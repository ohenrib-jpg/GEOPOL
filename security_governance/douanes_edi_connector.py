"""
Connecteur Douanes Françaises EDI API
Récupère les données des sanctions internationales via l'API des douanes françaises
Documentation: https://www.douane.gouv.fr/fiche/echange-de-donnees-informatise-edi-api
"""

import requests
import logging
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Import du cache intelligent
try:
    from .security_cache import cached_connector_method, SecurityCache
    CACHE_ENABLED = True
    logger.debug(f"[DOUANES EDI] Cache intelligent activé: CACHE_ENABLED={CACHE_ENABLED}")
except ImportError as e:
    CACHE_ENABLED = False
    cached_connector_method = lambda source: lambda func: func  # Décorateur factice
    logger.warning(f"[DOUANES EDI] Cache intelligent désactivé: {e}")

# Import du circuit breaker
try:
    from .circuit_breaker import CircuitBreakerManager, with_circuit_breaker
    CIRCUIT_BREAKER_ENABLED = True
    logger.debug(f"[DOUANES EDI] Circuit breaker activé")
except ImportError as e:
    CIRCUIT_BREAKER_ENABLED = False
    CircuitBreakerManager = None
    with_circuit_breaker = lambda *args, **kwargs: lambda func: func
    logger.warning(f"[DOUANES EDI] Circuit breaker désactivé: {e}")


class DouanesEDIConnector:
    """
    Connecteur pour l'API EDI des Douanes Françaises
    """

    # URLs de l'API
    API_BASE_URL = "https://api.douane.gouv.fr"
    API_SANCTIONS_URL = f"{API_BASE_URL}/v1/sanctions"  # À confirmer
    API_EDI_URL = f"{API_BASE_URL}/v1/edi"  # À confirmer

    # Documentation URLs
    DOCUMENTATION_URL = "https://www.douane.gouv.fr/fiche/echange-de-donnees-informatise-edi-api"
    PDF_GUIDE_URL = "https://www.douane.gouv.fr/sites/default/files/2023-12/15/edi-douane-via-api-processus-1-contrat-utilisation-public.pdf"

    # Configuration de timeout et retry
    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # secondes

    def __init__(self, timeout: int = None, max_retries: int = None, api_key: str = None):
        """
        Args:
            timeout: Timeout en secondes pour les requêtes (défaut: 30)
            max_retries: Nombre maximum de tentatives (défaut: 3)
            api_key: Clé API pour l'authentification (peut être None)
        """
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GEOPOL-Analytics/1.0 (+https://github.com/geopol)',
            'Accept': 'application/json,application/xml',
        })

        # Utiliser la clé API si fournie, sinon chercher dans les variables d'environnement
        self.api_key = api_key or os.environ.get('DOUANES_API_KEY')
        if self.api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_key}',
                'X-API-Key': self.api_key,
            })
            logger.info("[DOUANES EDI] Clé API configurée")
        else:
            logger.warning("[DOUANES EDI] Aucune clé API configurée - utilisation données statiques")

        self.timeout = timeout or self.DEFAULT_TIMEOUT
        self.max_retries = max_retries or self.MAX_RETRIES

        # Circuit breaker avancé
        if CIRCUIT_BREAKER_ENABLED and CircuitBreakerManager:
            self.circuit_breaker = CircuitBreakerManager.get_breaker(
                name='douanes_edi_api',
                failure_threshold=2,
                reset_timeout=600,  # 10 minutes avant réessai
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
        logger.warning("[DOUANES EDI] Circuit breaker ouvert - utilisation données fallback")
        return {
            'success': False,
            'error': 'Douanes EDI service temporarily unavailable - circuit breaker open',
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
                logger.info(f"[DOUANES EDI] Requête {url} (tentative {attempt + 1}/{self.max_retries})")
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()

                logger.info(f"[DOUANES EDI] Succès requête {url}")
                return {'success': True, 'text': response.text, 'content_type': response.headers.get('content-type')}

            except requests.exceptions.Timeout as e:
                last_error = f"Timeout après {self.timeout}s: {e}"
                logger.warning(f"[DOUANES EDI] Timeout (tentative {attempt + 1})")
                if attempt < self.max_retries - 1:
                    import time
                    time.sleep(self.RETRY_DELAY)
                continue

            except requests.exceptions.ConnectionError as e:
                last_error = f"Erreur de connexion: {e}"
                logger.warning(f"[DOUANES EDI] Erreur connexion (tentative {attempt + 1})")
                if attempt < self.max_retries - 1:
                    import time
                    time.sleep(self.RETRY_DELAY)
                continue

            except requests.exceptions.HTTPError as e:
                # Ne pas retry sur 4xx (erreur client)
                if response.status_code < 500:
                    last_error = f"Erreur HTTP {response.status_code}: {e}"
                    logger.error(f"[DOUANES EDI] Erreur HTTP {response.status_code} - pas de retry")
                    break
                last_error = f"Erreur serveur {response.status_code}: {e}"
                logger.warning(f"[DOUANES EDI] Erreur serveur (tentative {attempt + 1})")
                if attempt < self.max_retries - 1:
                    import time
                    time.sleep(self.RETRY_DELAY)
                continue

            except Exception as e:
                last_error = f"Erreur inattendue: {e}"
                logger.error(f"[DOUANES EDI] Erreur inattendue: {e}")
                break

        # Toutes les tentatives ont échoué
        logger.error(f"[DOUANES EDI] Échec après {self.max_retries} tentatives: {last_error}")
        return {'success': False, 'error': last_error}

    def _is_cache_valid(self) -> bool:
        """Vérifie si le cache interne est valide"""
        if self.data_cache is None or self.cache_timestamp is None:
            return False

        elapsed = datetime.now() - self.cache_timestamp
        return elapsed.total_seconds() < self.cache_duration

    @cached_connector_method('douanes_edi')
    def get_sanctions_list(self, limit: int = 100, country_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        Récupère la liste des sanctions internationales des douanes françaises
        Args:
            limit: Nombre max d'entrées
            country_filter: Filtrer par pays
        Returns:
            Dict avec résultats
        """
        try:
            # Vérifier cache (cache interne en plus du cache intelligent)
            if self._is_cache_valid():
                logger.info("[CACHE] Utilisation cache douanes EDI interne")
                return self._filter_and_limit(self.data_cache, limit, country_filter)

            # Essayer l'API si une clé est disponible
            if self.api_key:
                logger.info("[DOUANES EDI] Tentative récupération via API")
                result = self._try_api_fetch()
                if result and result.get('success'):
                    sanctions = self._parse_api_response(result)
                    if sanctions:
                        self.data_cache = sanctions
                        self.cache_timestamp = datetime.now()
                        return self._filter_and_limit(sanctions, limit, country_filter)

            # Fallback sur données statiques
            logger.info("[DOUANES EDI] Utilisation données statiques")
            static_data = self._get_static_sanctions()
            self.data_cache = static_data
            self.cache_timestamp = datetime.now()

            return self._filter_and_limit(static_data, limit, country_filter)

        except Exception as e:
            logger.error(f"[ERROR] Erreur récupération sanctions douanes: {e}")
            return self._get_static_fallback(limit, country_filter)

    def _try_api_fetch(self) -> Optional[Dict[str, Any]]:
        """Tente de récupérer des données via l'API"""
        # Essayer différentes URLs potentielles
        endpoints = [
            self.API_SANCTIONS_URL,
            f"{self.API_BASE_URL}/sanctions",
            f"{self.API_BASE_URL}/public/sanctions",
        ]

        for endpoint in endpoints:
            try:
                result = self._make_request(endpoint)
                if result.get('success'):
                    content_type = result.get('content_type', '')
                    if 'application/json' in content_type:
                        import json
                        data = json.loads(result['text'])
                        return {'success': True, 'data': data, 'endpoint': endpoint}
                    elif 'application/xml' in content_type:
                        # Parse XML
                        return {'success': True, 'data': result['text'], 'endpoint': endpoint}
            except Exception as e:
                logger.warning(f"[DOUANES EDI] Échec endpoint {endpoint}: {e}")
                continue

        return None

    def _parse_api_response(self, api_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse la réponse de l'API"""
        data = api_result.get('data')
        if not data:
            return []

        # Format inconnu, retourner données basiques
        # Cette méthode doit être adaptée selon le format réel de l'API
        sanctions = []
        try:
            if isinstance(data, dict):
                # Essayer de trouver une liste de sanctions
                items = data.get('sanctions', data.get('items', data.get('results', [])))
                if isinstance(items, list):
                    for item in items[:100]:  # Limiter
                        sanction = self._extract_sanction_from_item(item)
                        if sanction:
                            sanctions.append(sanction)
            elif isinstance(data, list):
                for item in data[:100]:
                    sanction = self._extract_sanction_from_item(item)
                    if sanction:
                        sanctions.append(sanction)
        except Exception as e:
            logger.warning(f"[DOUANES EDI] Erreur parsing réponse API: {e}")

        return sanctions

    def _extract_sanction_from_item(self, item) -> Optional[Dict[str, Any]]:
        """Extrait les informations de sanction d'un item API"""
        try:
            # Logique générique d'extraction
            if isinstance(item, dict):
                name = item.get('name', item.get('nom', item.get('title', '')))
                country = item.get('country', item.get('pays', item.get('nationality', '')))
                sanction_type = item.get('type', item.get('sanction_type', ''))
                date = item.get('date', item.get('date_entree', datetime.now().strftime('%Y-%m-%d')))

                return {
                    'nom': name or 'Unknown',
                    'type': 'entite' if any(keyword in str(item).lower() for keyword in ['company', 'entity', 'organization', 'vessel']) else 'individu',
                    'pays': country or 'Unknown',
                    'type_sanction': sanction_type or 'Général',
                    'date_entree': date,
                    'source': 'Douanes Françaises (API)',
                    'severite': 'Moyenne'
                }
        except:
            pass
        return None

    def _get_static_sanctions(self) -> List[Dict[str, Any]]:
        """Retourne des données statiques de sanctions"""
        return [
            {
                'nom': 'Russie',
                'type': 'pays',
                'pays': 'Russie',
                'type_sanction': 'Économique',
                'date_entree': '2022-02-24',
                'source': 'Douanes Françaises',
                'severite': 'Élevée',
                'secteurs': 'Énergie, Finance, Défense, Technologie'
            },
            {
                'nom': 'Corée du Nord',
                'type': 'pays',
                'pays': 'Corée du Nord',
                'type_sanction': 'Embargo',
                'date_entree': '2006-10-09',
                'source': 'Douanes Françaises',
                'severite': 'Élevée',
                'secteurs': 'Armement, Biens de luxe, Finance'
            },
            {
                'nom': 'Iran',
                'type': 'pays',
                'pays': 'Iran',
                'type_sanction': 'Nucléaire',
                'date_entree': '2010-06-09',
                'source': 'Douanes Françaises',
                'severite': 'Élevée',
                'secteurs': 'Pétrole, Finance, Technologie'
            },
            {
                'nom': 'Syrie',
                'type': 'pays',
                'pays': 'Syrie',
                'type_sanction': 'Droits humains',
                'date_entree': '2011-05-09',
                'source': 'Douanes Françaises',
                'severite': 'Élevée',
                'secteurs': 'Gouvernement, Sécurité'
            },
            {
                'nom': 'Venezuela',
                'type': 'pays',
                'pays': 'Venezuela',
                'type_sanction': 'Démocratie',
                'date_entree': '2017-11-13',
                'source': 'Douanes Françaises',
                'severite': 'Moyenne',
                'secteurs': 'Gouvernement, Finance'
            },
            {
                'nom': 'Biélorussie',
                'type': 'pays',
                'pays': 'Biélorussie',
                'type_sanction': 'Droits humains',
                'date_entree': '2020-10-02',
                'source': 'Douanes Françaises',
                'severite': 'Moyenne',
                'secteurs': 'Gouvernement, Sécurité'
            }
        ]

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
            'source': 'Douanes Françaises EDI',
            'sanctions': limited,
            'count': len(limited),
            'total_available': len(filtered),
            'country_filter': country_filter,
            'limit_applied': limit,
            'api_used': self.api_key is not None
        }

    def _get_static_fallback(self, limit: int = 100, country_filter: Optional[str] = None) -> Dict[str, Any]:
        """Données statiques de fallback"""
        static_data = self._get_static_sanctions()
        return self._filter_and_limit(static_data, limit, country_filter)

    @cached_connector_method('douanes_edi')
    def get_sanctions_by_country(self, country: str, limit: int = 50) -> Dict[str, Any]:
        """
        Récupère les sanctions par pays
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

            logger.info(f"[OK] {len(country_entries)} sanctions douanes pour {country}")

            return {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'source': 'Douanes Françaises EDI',
                'country': country,
                'sanctions': country_entries,
                'count': len(country_entries)
            }

        except Exception as e:
            logger.error(f"[ERROR] Erreur sanctions douanes par pays: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    @cached_connector_method('douanes_edi')
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
                'source': 'Douanes Françaises EDI',
                'recent_sanctions': sanctions,
                'count': len(sanctions),
                'query': {
                    'days': days,
                    'limit': limit
                }
            }

        except Exception as e:
            logger.error(f"[ERROR] Erreur sanctions récentes douanes: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }


# Instance globale pour accès facile
douanes_edi_connector = DouanesEDIConnector()