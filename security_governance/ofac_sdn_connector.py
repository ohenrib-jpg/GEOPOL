"""
Connecteur OFAC SDN (Specially Designated Nationals)
Source: https://www.treasury.gov/ofac/downloads/sdn.csv
Fichier CSV public mis à jour régulièrement
Aucune authentification requise

Format du fichier CSV:
- Name, Type, Program, List, Score, etc.
"""

import requests
import csv
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from io import StringIO
import pandas as pd

logger = logging.getLogger(__name__)

# Import du cache intelligent
try:
    from .security_cache import cached_connector_method, SecurityCache
    CACHE_ENABLED = True
    logger.debug(f"[OFAC] Cache intelligent activé: CACHE_ENABLED={CACHE_ENABLED}")
except ImportError as e:
    CACHE_ENABLED = False
    cached_connector_method = lambda source: lambda func: func  # Décorateur factice
    logger.warning(f"[OFAC] Cache intelligent désactivé: {e}")

# Import du circuit breaker
try:
    from .circuit_breaker import CircuitBreakerManager, with_circuit_breaker
    CIRCUIT_BREAKER_ENABLED = True
    logger.debug(f"[OFAC] Circuit breaker activé")
except ImportError as e:
    CIRCUIT_BREAKER_ENABLED = False
    CircuitBreakerManager = None
    with_circuit_breaker = lambda *args, **kwargs: lambda func: func
    logger.warning(f"[OFAC] Circuit breaker désactivé: {e}")


class OFACSDNConnector:
    """
    Connecteur pour la liste SDN d'OFAC (US Treasury)
    Récupère les sanctions américaines
    """

    # URLs OFAC SDN - Multiples sources pour résilience
    # Note: Le format CSV d'OFAC a des colonnes spécifiques
    SDN_CSV_URL = "https://www.treasury.gov/ofac/downloads/sdn.csv"
    SDN_PIPE_URL = "https://www.treasury.gov/ofac/downloads/sdnlist.txt"  # Format pipe-delimited
    CONSOLIDATED_LIST_URL = "https://www.treasury.gov/ofac/downloads/consolidated/consolidated.csv"

    # Colonnes du fichier SDN.CSV (format officiel OFAC)
    SDN_COLUMNS = [
        'ent_num', 'sdn_name', 'sdn_type', 'program', 'title',
        'call_sign', 'vess_type', 'tonnage', 'grt', 'vess_flag',
        'vess_owner', 'remarks'
    ]

    # Configuration de timeout et retry
    DEFAULT_TIMEOUT = 60  # Plus long pour téléchargement CSV
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # secondes

    def __init__(self, timeout: int = None, max_retries: int = None):
        """
        Args:
            timeout: Timeout en secondes pour les requêtes (défaut: 60)
            max_retries: Nombre maximum de tentatives (défaut: 3)
        """
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GEOPOL-Analytics/1.0 (+https://github.com/geopol)',
            'Accept': 'text/csv,application/json'
        })
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        self.max_retries = max_retries or self.MAX_RETRIES

        # Circuit breaker avancé
        if CIRCUIT_BREAKER_ENABLED and CircuitBreakerManager:
            self.circuit_breaker = CircuitBreakerManager.get_breaker(
                name='ofac_sdn_api',
                failure_threshold=2,  # Seuil bas pour OFAC (source sensible)
                reset_timeout=900,    # 15 minutes avant réessai
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
        logger.warning("[OFAC] Circuit breaker ouvert - utilisation données fallback")
        return {
            'success': False,
            'error': 'OFAC service temporarily unavailable - circuit breaker open',
            'timestamp': datetime.now().isoformat(),
            'sdn_entries': [],
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
                logger.info(f"[OFAC] Requête {url} (tentative {attempt + 1}/{self.max_retries})")
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()

                logger.info(f"[OFAC] Succès requête {url}")
                return {'success': True, 'text': response.text}

            except requests.exceptions.Timeout as e:
                last_error = f"Timeout après {self.timeout}s: {e}"
                logger.warning(f"[OFAC] Timeout (tentative {attempt + 1})")
                if attempt < self.max_retries - 1:
                    import time
                    time.sleep(self.RETRY_DELAY)
                continue

            except requests.exceptions.ConnectionError as e:
                last_error = f"Erreur de connexion: {e}"
                logger.warning(f"[OFAC] Erreur connexion (tentative {attempt + 1})")
                if attempt < self.max_retries - 1:
                    import time
                    time.sleep(self.RETRY_DELAY)
                continue

            except requests.exceptions.HTTPError as e:
                # Ne pas retry sur 4xx (erreur client)
                if response.status_code < 500:
                    last_error = f"Erreur HTTP {response.status_code}: {e}"
                    logger.error(f"[OFAC] Erreur HTTP {response.status_code} - pas de retry")
                    break
                last_error = f"Erreur serveur {response.status_code}: {e}"
                logger.warning(f"[OFAC] Erreur serveur (tentative {attempt + 1})")
                if attempt < self.max_retries - 1:
                    import time
                    time.sleep(self.RETRY_DELAY)
                continue

            except Exception as e:
                last_error = f"Erreur inattendue: {e}"
                logger.error(f"[OFAC] Erreur inattendue: {e}")
                break

        # Toutes les tentatives ont échoué
        logger.error(f"[OFAC] Échec après {self.max_retries} tentatives: {last_error}")
        return {'success': False, 'error': last_error}

    @cached_connector_method('ofac_sdn')
    def get_sdn_list(self, limit: int = 100, program_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        Récupère la liste SDN
        Args:
            limit: Nombre max d'entrées
            program_filter: Filtrer par programme (ex: 'UKRAINE-EO14024')
        Returns:
            Dict avec résultats
        """
        try:
            # Vérifier cache (cache interne en plus du cache intelligent)
            if self._is_cache_valid():
                logger.info("[CACHE] Utilisation cache SDN interne")
                return self._filter_and_limit(self.data_cache, limit, program_filter)

            logger.info("[OFAC] Téléchargement liste SDN...")

            # Utiliser la méthode avec retry et circuit breaker
            result = self._make_request(self.SDN_CSV_URL)

            if not result.get('success'):
                return {
                    'success': False,
                    'error': result.get('error', 'Unknown error'),
                    'timestamp': datetime.now().isoformat(),
                    'sdn_entries': []
                }

            # Lire CSV avec pandas pour gérer les problèmes d'encodage
            csv_data = StringIO(result['text'])

            # Le fichier SDN.csv d'OFAC n'a PAS d'en-tête
            # Format: colonnes fixes définies dans SDN_COLUMNS
            try:
                # Essayer d'abord sans en-tête avec les colonnes définies
                df = pd.read_csv(
                    csv_data,
                    delimiter=',',
                    quotechar='"',
                    encoding='utf-8',
                    names=self.SDN_COLUMNS,
                    header=None,
                    on_bad_lines='skip'
                )
            except Exception as e1:
                logger.warning(f"[OFAC] Parsing UTF-8 échoué: {e1}, essai latin-1...")
                csv_data.seek(0)
                try:
                    df = pd.read_csv(
                        csv_data,
                        delimiter=',',
                        quotechar='"',
                        encoding='latin-1',
                        names=self.SDN_COLUMNS,
                        header=None,
                        on_bad_lines='skip'
                    )
                except Exception as e2:
                    logger.warning(f"[OFAC] Parsing latin-1 échoué: {e2}, essai avec en-tête auto...")
                    csv_data.seek(0)
                    # Dernier recours: laisser pandas détecter
                    df = pd.read_csv(csv_data, encoding='latin-1', on_bad_lines='skip')

            logger.info(f"[OK] Liste SDN chargée: {len(df)} entrées, colonnes: {list(df.columns)[:5]}...")

            # Formater les données
            sdn_entries = self._format_sdn_entries(df)

            # Mettre en cache
            self.data_cache = sdn_entries
            self.cache_timestamp = datetime.now()

            return self._filter_and_limit(sdn_entries, limit, program_filter)

        except requests.exceptions.RequestException as e:
            logger.error(f"[ERROR] Erreur téléchargement SDN: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'sdn_entries': []
            }
        except Exception as e:
            logger.error(f"[ERROR] Erreur traitement SDN: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'sdn_entries': []
            }

    @cached_connector_method('ofac_sdn')
    def get_recent_sanctions(self, days: int = 30, limit: int = 50) -> Dict[str, Any]:
        """
        Récupère les sanctions récentes (si date disponible)
        Note: Le fichier SDN ne contient pas de date d'ajout, donc on retourne toutes
        """
        try:
            result = self.get_sdn_list(limit=limit * 2)

            if not result.get('success', False):
                return result

            # Dans le cas où on n'a pas de date, on retourne les premières entrées
            sdn_entries = result.get('sdn_entries', [])[:limit]

            return {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'source': 'OFAC SDN List',
                'recent_sanctions': sdn_entries,
                'count': len(sdn_entries),
                'query': {
                    'days': days,
                    'limit': limit
                }
            }

        except Exception as e:
            logger.error(f"[ERROR] Erreur récent sanctions: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    @cached_connector_method('ofac_sdn')
    def get_sanctions_by_country(self, country: str, limit: int = 50) -> Dict[str, Any]:
        """
        Récupère les sanctions par pays
        """
        try:
            result = self.get_sdn_list(limit=500)  # Plus pour filtrer

            if not result.get('success', False):
                return result

            country_lower = country.lower()
            country_entries = [
                entry for entry in result.get('sdn_entries', [])
                if country_lower in entry.get('addresses', '').lower() or
                   country_lower in entry.get('countries', '').lower()
            ][:limit]

            logger.info(f"[OK] {len(country_entries)} sanctions OFAC pour {country}")

            return {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'source': 'OFAC SDN List',
                'country': country,
                'sanctions': country_entries,
                'count': len(country_entries)
            }

        except Exception as e:
            logger.error(f"[ERROR] Erreur sanctions par pays: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    @cached_connector_method('ofac_sdn')
    def get_program_summary(self) -> Dict[str, Any]:
        """
        Récupère un résumé par programme
        """
        try:
            result = self.get_sdn_list(limit=1000)

            if not result.get('success', False):
                return result

            programs = {}
            for entry in result.get('sdn_entries', []):
                program = entry.get('program', 'UNKNOWN')
                if program not in programs:
                    programs[program] = {
                        'count': 0,
                        'types': set(),
                        'countries': set()
                    }

                programs[program]['count'] += 1
                programs[program]['types'].add(entry.get('type', 'Unknown'))

                # Extraire pays des adresses
                addresses = entry.get('addresses', '')
                if addresses:
                    # Recherche simple de noms de pays
                    common_countries = ['RUSSIA', 'CHINA', 'IRAN', 'NORTH KOREA', 'SYRIA', 'VENEZUELA', 'CUBA']
                    for country in common_countries:
                        if country in addresses.upper():
                            programs[program]['countries'].add(country.title())

            # Formater pour JSON
            program_summary = []
            for program_name, data in programs.items():
                program_summary.append({
                    'program': program_name,
                    'count': data['count'],
                    'types': list(data['types'])[:5],
                    'countries': list(data['countries'])[:5]
                })

            # Trier par count décroissant
            program_summary.sort(key=lambda x: x['count'], reverse=True)

            return {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'source': 'OFAC SDN List',
                'programs': program_summary[:10],  # Top 10
                'total_programs': len(programs),
                'total_entries': len(result.get('sdn_entries', []))
            }

        except Exception as e:
            logger.error(f"[ERROR] Erreur programme summary: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def _format_sdn_entries(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Formate les entrées SDN au format GEOPOL"""
        entries = []

        # Mapping des colonnes possibles (format OFAC vs format générique)
        column_mapping = {
            'name': ['sdn_name', 'Name', 'name', 0],  # Index 0 si pas de nom de colonne
            'type': ['sdn_type', 'Type', 'type', 2],
            'program': ['program', 'Program', 3],
            'remarks': ['remarks', 'Remarks', 11],
            'title': ['title', 'Title', 4]
        }

        def get_value(row, field):
            """Récupère une valeur en essayant différentes colonnes"""
            for col in column_mapping.get(field, [field]):
                if isinstance(col, int):
                    # Index numérique
                    try:
                        val = row.iloc[col] if col < len(row) else None
                        if pd.notna(val):
                            return str(val).strip()
                    except:
                        continue
                elif col in row.index:
                    val = row.get(col)
                    if pd.notna(val):
                        return str(val).strip()
            return ''

        for _, row in df.iterrows():
            try:
                # Extraire données basiques avec mapping flexible
                name = get_value(row, 'name')
                entry_type = get_value(row, 'type')
                program = get_value(row, 'program')
                remarks = get_value(row, 'remarks')

                # Ignorer les lignes sans nom
                if not name or name == 'nan':
                    continue

                # Pas d'adresse dans le fichier SDN.csv principal
                # Les adresses sont dans un fichier séparé (add.csv)
                addresses = remarks  # Les remarques contiennent parfois des adresses

                # Liste (pas de colonne spécifique, utiliser 'SDN')
                sdn_list = 'SDN'

                # Déterminer si c'est un individu ou une entité
                if any(title in name.upper() for title in ['MR.', 'MRS.', 'DR.', 'PROF.', 'SHEIKH', 'PRINCE']):
                    target_type = 'Individu'
                elif any(term in entry_type.upper() for term in ['COMPANY', 'CORPORATION', 'BANK', 'ORGANIZATION', 'ENTITY']):
                    target_type = 'Entité'
                else:
                    target_type = 'Individu'  # Par défaut

                # Extraire pays potentiels des adresses
                countries = self._extract_countries_from_address(addresses)

                entry = {
                    'name': name,
                    'type': target_type,
                    'program': program,
                    'list': sdn_list,
                    'addresses': addresses,
                    'remarks': remarks,
                    'countries': ', '.join(countries),
                    'source': 'OFAC SDN',
                    'severity': self._determine_severity(program),
                    'timestamp': datetime.now().isoformat(),
                    'raw_type': entry_type
                }
                entries.append(entry)

            except Exception as e:
                logger.warning(f"[WARN] Erreur format SDN: {e}")
                continue

        return entries

    def _extract_countries_from_address(self, addresses: str) -> List[str]:
        """Extrait les noms de pays des adresses"""
        if not addresses:
            return []

        # Liste de pays communs
        country_keywords = [
            'RUSSIA', 'CHINA', 'IRAN', 'NORTH KOREA', 'SYRIA',
            'VENEZUELA', 'CUBA', 'SUDAN', 'BELARUS', 'MYANMAR',
            'AFGHANISTAN', 'YEMEN', 'LIBYA', 'SOMALIA', 'IRAQ'
        ]

        found_countries = []
        addresses_upper = addresses.upper()

        for country in country_keywords:
            if country in addresses_upper:
                # Formater joliment
                if country == 'NORTH KOREA':
                    found_countries.append('Corée du Nord')
                elif country == 'RUSSIA':
                    found_countries.append('Russie')
                elif country == 'CHINA':
                    found_countries.append('Chine')
                elif country == 'IRAN':
                    found_countries.append('Iran')
                elif country == 'SYRIA':
                    found_countries.append('Syrie')
                elif country == 'VENEZUELA':
                    found_countries.append('Venezuela')
                elif country == 'CUBA':
                    found_countries.append('Cuba')
                elif country == 'SUDAN':
                    found_countries.append('Soudan')
                elif country == 'BELARUS':
                    found_countries.append('Biélorussie')
                elif country == 'MYANMAR':
                    found_countries.append('Myanmar')
                else:
                    found_countries.append(country.title())

        return list(set(found_countries))[:3]  # Limiter à 3 pays

    def _determine_severity(self, program: str) -> str:
        """Détermine la sévérité basée sur le programme"""
        if not program:
            return 'Medium'

        program_upper = program.upper()

        # Programmes critiques
        critical_programs = ['CYBER2', 'NPWMD', 'IFSR', 'FTO', 'SDGT']
        # Programmes élevés
        high_programs = ['UKRAINE', 'RUSSIA', 'IRAN', 'SYRIA', 'NORTH KOREA']

        if any(critical in program_upper for critical in critical_programs):
            return 'Critical'
        elif any(high in program_upper for high in high_programs):
            return 'High'
        else:
            return 'Medium'

    def _is_cache_valid(self) -> bool:
        """Vérifie si le cache est valide"""
        if self.data_cache is None or self.cache_timestamp is None:
            return False

        age = (datetime.now() - self.cache_timestamp).total_seconds()
        return age < self.cache_duration

    def _filter_and_limit(self, entries: List[Dict], limit: int, program_filter: Optional[str]) -> Dict[str, Any]:
        """Filtre et limite les entrées"""
        if program_filter:
            filtered = [e for e in entries if program_filter.upper() in e.get('program', '').upper()]
        else:
            filtered = entries

        limited = filtered[:limit]

        return {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'source': 'OFAC SDN List',
            'sdn_entries': limited,
            'count': len(limited),
            'total_available': len(entries),
            'program_filter': program_filter
        }


    def get_circuit_breaker_stats(self) -> Optional[Dict[str, Any]]:
        """Retourne les statistiques du circuit breaker"""
        if self.circuit_breaker:
            return self.circuit_breaker.get_stats()
        return None

    def reset_circuit_breaker(self):
        """Réinitialise le circuit breaker"""
        if self.circuit_breaker:
            self.circuit_breaker.reset()
            logger.info("[OFAC] Circuit breaker réinitialisé")


def get_ofac_sdn_connector() -> OFACSDNConnector:
    """Factory pour obtenir le connecteur OFAC SDN"""
    return OFACSDNConnector()


def get_circuit_breaker_stats() -> Dict[str, Any]:
    """Retourne les statistiques de tous les circuit breakers"""
    try:
        if CIRCUIT_BREAKER_ENABLED and CircuitBreakerManager:
            return CircuitBreakerManager.get_all_stats()
    except Exception as e:
        logger.error(f"Erreur récupération stats circuit breaker: {e}")

    return {}


__all__ = ['OFACSDNConnector', 'get_ofac_sdn_connector', 'get_circuit_breaker_stats']