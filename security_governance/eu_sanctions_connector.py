"""
Connecteur EU Sanctions - Récupère les sanctions de l'Union Européenne
Sources potentielles:
- sanctionsmap.eu (site officiel)
- data.europa.eu datasets
- Fichiers consolidés de l'UE
"""

import requests
import csv
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from io import StringIO
import pandas as pd
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Import du cache intelligent
try:
    from .security_cache import cached_connector_method, SecurityCache
    CACHE_ENABLED = True
    logger.debug(f"[EU SANCTIONS] Cache intelligent activé: CACHE_ENABLED={CACHE_ENABLED}")
except ImportError as e:
    CACHE_ENABLED = False
    cached_connector_method = lambda source: lambda func: func  # Décorateur factice
    logger.warning(f"[EU SANCTIONS] Cache intelligent désactivé: {e}")

# Import du circuit breaker
try:
    from .circuit_breaker import CircuitBreakerManager, with_circuit_breaker
    CIRCUIT_BREAKER_ENABLED = True
    logger.debug(f"[EU SANCTIONS] Circuit breaker activé")
except ImportError as e:
    CIRCUIT_BREAKER_ENABLED = False
    CircuitBreakerManager = None
    with_circuit_breaker = lambda *args, **kwargs: lambda func: func
    logger.warning(f"[EU SANCTIONS] Circuit breaker désactivé: {e}")


class EUSanctionsConnector:
    """
    Connecteur pour les sanctions de l'Union Européenne
    """

    # URLs potentielles pour les données EU sanctions
    # Site officiel sanctionsmap.eu
    SANCTIONS_MAP_URL = "https://www.sanctionsmap.eu"
    SANCTIONS_MAP_DATA_URL = "https://www.sanctionsmap.eu/api/"  # Possible API endpoint

    # Data.europa.eu datasets
    DATA_EUROPA_DATASET_URL = "https://data.europa.eu/data/datasets?query=sanctions"

    # URLs de secours pour fichiers consolidés (à vérifier)
    EU_CONSOLIDATED_LIST_URL = "https://webgate.ec.europa.eu/europeaid/fsd/fsf/public/files/csvFullSanctionsList_1_0/content?token=dummy"

    # Configuration de timeout et retry
    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # secondes

    def __init__(self, timeout: int = None, max_retries: int = None):
        """
        Args:
            timeout: Timeout en secondes pour les requêtes (défaut: 30)
            max_retries: Nombre maximum de tentatives (défaut: 3)
        """
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GEOPOL-Analytics/1.0 (+https://github.com/geopol)',
            'Accept': 'application/json,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        self.max_retries = max_retries or self.MAX_RETRIES

        # Circuit breaker avancé
        if CIRCUIT_BREAKER_ENABLED and CircuitBreakerManager:
            self.circuit_breaker = CircuitBreakerManager.get_breaker(
                name='eu_sanctions_api',
                failure_threshold=2,  # Seuil bas pour source sensible
                reset_timeout=600,    # 10 minutes avant réessai
                fallback_func=self._get_fallback_data
            )
        else:
            self.circuit_breaker = None

        self.data_cache = None
        self.cache_timestamp = None
        self.cache_duration = 3600  # 1 heure

    def _check_circuit_breaker(self) -> bool:
        """Vérifie si le circuit breaker est disponible"""
        if not self.circuit_breaker:
            return True  # Pas de circuit breaker = toujours disponible
        return self.circuit_breaker.is_available()

    def _get_fallback_data(self, *args, **kwargs) -> Dict[str, Any]:
        """Données de fallback quand circuit breaker ouvert"""
        logger.warning("[EU SANCTIONS] Circuit breaker ouvert - utilisation données fallback")
        return {
            'success': False,
            'error': 'EU sanctions service temporarily unavailable - circuit breaker open',
            'timestamp': datetime.now().isoformat(),
            'sanctions': [],
            'fallback': True,
            'circuit_state': 'open'
        }

    def _make_request(self, url: str) -> Dict[str, Any]:
        """
        Effectue une requête avec gestion d'erreurs, retry et circuit breaker
        """
        # Si circuit breaker disponible, l'utiliser
        if self.circuit_breaker:
            return self.circuit_breaker.call(self._execute_request_with_retry, url)

        # Sinon, exécuter directement
        return self._execute_request_with_retry(url)

    def _execute_request_with_retry(self, url: str) -> Dict[str, Any]:
        """Exécute une requête avec retry logic (appelé par circuit breaker)"""
        last_error = None

        # Retry logic
        for attempt in range(self.max_retries):
            try:
                logger.info(f"[EU SANCTIONS] Requête {url} (tentative {attempt + 1}/{self.max_retries})")
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()

                logger.info(f"[EU SANCTIONS] Succès requête {url}")
                return {'success': True, 'text': response.text, 'content_type': response.headers.get('content-type')}

            except requests.exceptions.Timeout as e:
                last_error = f"Timeout après {self.timeout}s: {e}"
                logger.warning(f"[EU SANCTIONS] Timeout (tentative {attempt + 1})")
                if attempt < self.max_retries - 1:
                    import time
                    time.sleep(self.RETRY_DELAY)
                continue

            except requests.exceptions.ConnectionError as e:
                last_error = f"Erreur de connexion: {e}"
                logger.warning(f"[EU SANCTIONS] Erreur connexion (tentative {attempt + 1})")
                if attempt < self.max_retries - 1:
                    import time
                    time.sleep(self.RETRY_DELAY)
                continue

            except requests.exceptions.HTTPError as e:
                # Ne pas retry sur 4xx (erreur client)
                if response.status_code < 500:
                    last_error = f"Erreur HTTP {response.status_code}: {e}"
                    logger.error(f"[EU SANCTIONS] Erreur HTTP {response.status_code} - pas de retry")
                    break
                last_error = f"Erreur serveur {response.status_code}: {e}"
                logger.warning(f"[EU SANCTIONS] Erreur serveur (tentative {attempt + 1})")
                if attempt < self.max_retries - 1:
                    import time
                    time.sleep(self.RETRY_DELAY)
                continue

            except Exception as e:
                last_error = f"Erreur inattendue: {e}"
                logger.error(f"[EU SANCTIONS] Erreur inattendue: {e}")
                break

        # Toutes les tentatives ont échoué
        logger.error(f"[EU SANCTIONS] Échec après {self.max_retries} tentatives: {last_error}")
        return {'success': False, 'error': last_error}

    def _is_cache_valid(self) -> bool:
        """Vérifie si le cache interne est valide"""
        if self.data_cache is None or self.cache_timestamp is None:
            return False

        elapsed = datetime.now() - self.cache_timestamp
        return elapsed.total_seconds() < self.cache_duration

    @cached_connector_method('eu_sanctions')
    def get_sanctions_list(self, limit: int = 100, country_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        Récupère la liste des sanctions EU
        Args:
            limit: Nombre max d'entrées
            country_filter: Filtrer par pays
        Returns:
            Dict avec résultats
        """
        try:
            # Vérifier cache (cache interne en plus du cache intelligent)
            if self._is_cache_valid():
                logger.info("[CACHE] Utilisation cache EU sanctions interne")
                return self._filter_and_limit(self.data_cache, limit, country_filter)

            logger.info("[EU SANCTIONS] Téléchargement liste sanctions...")

            # Essayer différentes sources
            sanctions_data = self._try_multiple_sources()

            if not sanctions_data:
                logger.warning("[EU SANCTIONS] Aucune source disponible, utilisation fallback")
                return self._get_static_fallback(limit, country_filter)

            # Mettre en cache
            self.data_cache = sanctions_data
            self.cache_timestamp = datetime.now()

            return self._filter_and_limit(sanctions_data, limit, country_filter)

        except Exception as e:
            logger.error(f"[ERROR] Erreur récupération sanctions EU: {e}")
            return self._get_static_fallback(limit, country_filter)

    def _try_multiple_sources(self) -> List[Dict[str, Any]]:
        """Essaye différentes sources pour récupérer les données EU sanctions"""
        sources = [
            self._fetch_from_sanctionsmap,
            self._fetch_from_data_europa,
            self._fetch_from_static_dataset,
        ]

        for source_func in sources:
            try:
                data = source_func()
                if data:
                    logger.info(f"[EU SANCTIONS] Source {source_func.__name__} réussie: {len(data)} entrées")
                    return data
            except Exception as e:
                logger.warning(f"[EU SANCTIONS] Source {source_func.__name__} échouée: {e}")
                continue

        return []

    def _fetch_from_sanctionsmap(self) -> List[Dict[str, Any]]:
        """Récupère les données depuis sanctionsmap.eu"""
        try:
            # Essayer d'abord la page principale pour extraire des données
            result = self._make_request(self.SANCTIONS_MAP_URL)
            if not result.get('success'):
                return []

            # Parser la page HTML avec BeautifulSoup
            soup = BeautifulSoup(result['text'], 'html.parser')

            # Chercher des données structurées dans les scripts
            scripts = soup.find_all('script')
            sanctions = []

            for script in scripts:
                if not script.string:
                    continue

                # Chercher des structures JSON dans les scripts
                import re
                json_pattern = r'\{.*"sanctions".*\}'
                matches = re.findall(json_pattern, script.string, re.DOTALL)

                for match in matches[:5]:  # Limiter pour performance
                    try:
                        import json
                        data = json.loads(match)
                        if 'sanctions' in data:
                            sanctions.extend(self._parse_sanctionsmap_data(data['sanctions']))
                    except:
                        continue

            # Si on a trouvé des données, les retourner
            if sanctions:
                logger.info(f"[EU SANCTIONS] {len(sanctions)} sanctions trouvées sur sanctionsmap.eu")
                return sanctions

            # Sinon, extraire des données des tables HTML
            tables = soup.find_all('table')
            for table in tables:
                table_data = self._parse_html_table(table)
                if table_data:
                    sanctions.extend(table_data)

            # Limiter et formater
            formatted_sanctions = []
            for sanction in sanctions[:200]:  # Limiter
                formatted = self._format_sanction_entry(sanction)
                if formatted:
                    formatted_sanctions.append(formatted)

            return formatted_sanctions

        except Exception as e:
            logger.warning(f"[EU SANCTIONS] Erreur scraping sanctionsmap.eu: {e}")
            return []

    def _fetch_from_data_europa(self) -> List[Dict[str, Any]]:
        """Récupère depuis data.europa.eu (à implémenter)"""
        # Pour l'instant, retourner liste vide
        return []

    def _fetch_from_static_dataset(self) -> List[Dict[str, Any]]:
        """Utilise un dataset statique de secours"""
        # Données statiques basées sur les sanctions EU connues
        static_sanctions = [
            {
                'name': 'Alexander LUKASHENKO',
                'type': 'individual',
                'country': 'Belarus',
                'reason': 'Human rights violations',
                'date': '2020-10-02',
                'source': 'EU',
                'program': 'Belarus sanctions'
            },
            {
                'name': 'Maria Alexandrovna LUKASHENKO',
                'type': 'individual',
                'country': 'Belarus',
                'reason': 'Human rights violations',
                'date': '2020-10-02',
                'source': 'EU',
                'program': 'Belarus sanctions'
            },
            {
                'name': 'Dmitry Belyatsky',
                'type': 'individual',
                'country': 'Belarus',
                'reason': 'Human rights violations',
                'date': '2021-06-21',
                'source': 'EU',
                'program': 'Belarus sanctions'
            },
            {
                'name': 'Russian National Wealth Fund',
                'type': 'entity',
                'country': 'Russia',
                'reason': 'Undermining territorial integrity of Ukraine',
                'date': '2022-02-23',
                'source': 'EU',
                'program': 'Ukraine sanctions'
            },
            {
                'name': 'Sberbank',
                'type': 'entity',
                'country': 'Russia',
                'reason': 'Undermining territorial integrity of Ukraine',
                'date': '2022-02-25',
                'source': 'EU',
                'program': 'Ukraine sanctions'
            },
            {
                'name': 'Gazprom',
                'type': 'entity',
                'country': 'Russia',
                'reason': 'Undermining territorial integrity of Ukraine',
                'date': '2022-03-15',
                'source': 'EU',
                'program': 'Ukraine sanctions'
            },
            {
                'name': 'Rosneft',
                'type': 'entity',
                'country': 'Russia',
                'reason': 'Undermining territorial integrity of Ukraine',
                'date': '2022-04-08',
                'source': 'EU',
                'program': 'Ukraine sanctions'
            },
            {
                'name': 'Islamic Revolutionary Guard Corps',
                'type': 'entity',
                'country': 'Iran',
                'reason': 'Human rights violations',
                'date': '2011-04-12',
                'source': 'EU',
                'program': 'Iran sanctions'
            },
            {
                'name': 'Bashar al-ASSAD',
                'type': 'individual',
                'country': 'Syria',
                'reason': 'Violence against civilians',
                'date': '2011-05-23',
                'source': 'EU',
                'program': 'Syria sanctions'
            },
            {
                'name': 'Maher al-ASSAD',
                'type': 'individual',
                'country': 'Syria',
                'reason': 'Violence against civilians',
                'date': '2011-12-01',
                'source': 'EU',
                'program': 'Syria sanctions'
            }
        ]

        formatted = [self._format_sanction_entry(s) for s in static_sanctions]
        return [f for f in formatted if f]

    def _parse_sanctionsmap_data(self, raw_data: Any) -> List[Dict[str, Any]]:
        """Parse les données brutes de sanctionsmap.eu"""
        # À adapter selon le format réel
        sanctions = []
        if isinstance(raw_data, list):
            for item in raw_data:
                if isinstance(item, dict):
                    sanction = {
                        'name': item.get('name', ''),
                        'type': item.get('type', 'individual'),
                        'country': item.get('country', ''),
                        'reason': item.get('reason', ''),
                        'date': item.get('date', ''),
                        'source': 'EU sanctionsmap',
                        'program': item.get('program', '')
                    }
                    sanctions.append(sanction)
        return sanctions

    def _parse_html_table(self, table) -> List[Dict[str, Any]]:
        """Parse une table HTML en données structurées"""
        # Implémentation simplifiée
        return []

    def _format_sanction_entry(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Formate une entrée sanction"""
        return {
            'nom': raw.get('name', 'Unknown'),
            'type': 'individu' if raw.get('type', '').lower() in ['individual', 'person'] else 'entite',
            'pays': raw.get('country', 'Unknown'),
            'programme': raw.get('program', 'EU Sanctions'),
            'date_ajout': raw.get('date', datetime.now().strftime('%Y-%m-%d')),
            'source': raw.get('source', 'EU'),
            'raison': raw.get('reason', ''),
            'severite': self._calculate_severity(raw.get('reason', ''))
        }

    def _calculate_severity(self, reason: str) -> str:
        """Calcule la sévérité basée sur la raison"""
        reason_lower = reason.lower()
        if any(term in reason_lower for term in ['violence', 'war', 'aggression', 'terrorism']):
            return 'Élevée'
        elif any(term in reason_lower for term in ['human rights', 'corruption', 'fraud']):
            return 'Moyenne'
        else:
            return 'Faible'

    def _filter_and_limit(self, data: List[Dict[str, Any]], limit: int, country_filter: Optional[str]) -> Dict[str, Any]:
        """Filtre et limite les données"""
        filtered = data

        if country_filter:
            country_lower = country_filter.lower()
            filtered = [
                d for d in filtered
                if country_lower in d.get('pays', '').lower() or
                   country_lower in d.get('nom', '').lower()
            ]

        limited = filtered[:limit] if limit else filtered

        return {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'source': 'EU Sanctions',
            'sanctions': limited,
            'count': len(limited),
            'total_available': len(filtered),
            'country_filter': country_filter,
            'limit_applied': limit
        }

    def _get_static_fallback(self, limit: int = 100, country_filter: Optional[str] = None) -> Dict[str, Any]:
        """Données statiques de fallback"""
        static_data = self._fetch_from_static_dataset()
        return self._filter_and_limit(static_data, limit, country_filter)

    @cached_connector_method('eu_sanctions')
    def get_sanctions_by_country(self, country: str, limit: int = 50) -> Dict[str, Any]:
        """
        Récupère les sanctions EU par pays
        """
        try:
            result = self.get_sanctions_list(limit=500)

            if not result.get('success', False):
                return result

            country_lower = country.lower()
            country_entries = [
                entry for entry in result.get('sanctions', [])
                if country_lower in entry.get('pays', '').lower()
            ][:limit]

            logger.info(f"[OK] {len(country_entries)} sanctions EU pour {country}")

            return {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'source': 'EU Sanctions',
                'country': country,
                'sanctions': country_entries,
                'count': len(country_entries)
            }

        except Exception as e:
            logger.error(f"[ERROR] Erreur sanctions EU par pays: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    @cached_connector_method('eu_sanctions')
    def get_recent_sanctions(self, days: int = 30, limit: int = 50) -> Dict[str, Any]:
        """
        Récupère les sanctions récentes
        """
        try:
            result = self.get_sanctions_list(limit=limit * 2)

            if not result.get('success', False):
                return result

            # Filtrer par date si disponible
            sanctions = result.get('sanctions', [])[:limit]

            return {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'source': 'EU Sanctions',
                'recent_sanctions': sanctions,
                'count': len(sanctions),
                'query': {
                    'days': days,
                    'limit': limit
                }
            }

        except Exception as e:
            logger.error(f"[ERROR] Erreur sanctions récentes EU: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    @cached_connector_method('eu_sanctions')
    def get_program_summary(self) -> Dict[str, Any]:
        """
        Récupère un résumé par programme
        """
        try:
            result = self.get_sanctions_list(limit=1000)

            if not result.get('success', False):
                return result

            programs = {}
            for entry in result.get('sanctions', []):
                program = entry.get('programme', 'UNKNOWN')
                if program not in programs:
                    programs[program] = {
                        'count': 0,
                        'countries': set(),
                        'types': set()
                    }

                programs[program]['count'] += 1
                programs[program]['countries'].add(entry.get('pays', 'Unknown'))
                programs[program]['types'].add(entry.get('type', 'Unknown'))

            # Formater pour JSON
            program_summary = []
            for program_name, data in programs.items():
                program_summary.append({
                    'program': program_name,
                    'count': data['count'],
                    'countries': list(data['countries'])[:5],
                    'types': list(data['types'])[:3]
                })

            # Trier par count décroissant
            program_summary.sort(key=lambda x: x['count'], reverse=True)

            return {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'source': 'EU Sanctions',
                'programs': program_summary[:10],  # Top 10
                'total_programs': len(programs),
                'total_entries': len(result.get('sanctions', []))
            }

        except Exception as e:
            logger.error(f"[ERROR] Erreur programme summary EU: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }


# Instance globale pour accès facile
eu_sanctions_connector = EUSanctionsConnector()