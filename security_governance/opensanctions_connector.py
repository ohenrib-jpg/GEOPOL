"""
Connecteur OpenSanctions - API de recherche et matching d'entités sanctionnées
https://www.opensanctions.org/docs/api/

Datasets disponibles:
- default: Dataset complet OpenSanctions
- sanctions: Toutes les listes de sanctions
- peps: Personnes politiquement exposées
- crime: Entités criminelles (mafias, trafiquants, etc.)
- us_ofac_sdn: Liste OFAC américaine
- eu_fsf: Sanctions européennes
- un_sc_sanctions: Sanctions ONU
- ru_rupep: PEPs russes
"""

import sys
if sys.platform == 'win32':
    import codecs
    if hasattr(sys.stdout, 'buffer') and not isinstance(sys.stdout, codecs.StreamWriter):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'ignore')
    if hasattr(sys.stderr, 'buffer') and not isinstance(sys.stderr, codecs.StreamWriter):
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'ignore')

import requests
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import os
from collections import defaultdict

logger = logging.getLogger(__name__)

# Import du cache intelligent
try:
    from .security_cache import cached_connector_method
    CACHE_ENABLED = True
    logger.debug("[OpenSanctions] Cache intelligent active")
except ImportError as e:
    logger.warning(f"[OpenSanctions] Cache non disponible: {e}")
    CACHE_ENABLED = False
    def cached_connector_method(*args, **kwargs):
        def decorator(func):
            return func
        return decorator


class OpenSanctionsConnector:
    """
    Connecteur pour l'API OpenSanctions
    Recherche et matching d'entités sanctionnées, PEPs, criminels
    """

    BASE_URL = "https://api.opensanctions.org"

    # Datasets disponibles
    DATASETS = {
        'default': 'Dataset complet OpenSanctions',
        'sanctions': 'Toutes les sanctions',
        'peps': 'Personnes politiquement exposees',
        'crime': 'Entites criminelles',
        'us_ofac_sdn': 'OFAC SDN (USA)',
        'eu_fsf': 'Sanctions UE',
        'un_sc_sanctions': 'Sanctions ONU',
        'ru_rupep': 'PEPs russes',
        'ua_nazk_sanctions': 'Sanctions Ukraine',
        'gb_hmt_sanctions': 'Sanctions UK',
        'ch_seco_sanctions': 'Sanctions Suisse',
        'interpol_red_notices': 'Interpol notices rouges'
    }

    # Schemas d'entites
    ENTITY_SCHEMAS = {
        'Person': 'Personne physique',
        'Company': 'Entreprise',
        'Organization': 'Organisation',
        'LegalEntity': 'Entite legale',
        'Vessel': 'Navire',
        'Aircraft': 'Aeronef',
        'CryptoWallet': 'Portefeuille crypto'
    }

    # Mapping pays -> code ISO
    COUNTRY_CODES = {
        'Russia': 'RU', 'China': 'CN', 'Iran': 'IR', 'North Korea': 'KP',
        'Syria': 'SY', 'Venezuela': 'VE', 'Belarus': 'BY', 'Myanmar': 'MM',
        'Afghanistan': 'AF', 'Cuba': 'CU', 'Libya': 'LY', 'Sudan': 'SD',
        'Iraq': 'IQ', 'Yemen': 'YE', 'Somalia': 'SO', 'Mali': 'ML',
        'France': 'FR', 'Germany': 'DE', 'Italy': 'IT', 'Spain': 'ES',
        'United States': 'US', 'United Kingdom': 'GB', 'Japan': 'JP'
    }

    def __init__(self, api_key: str = None):
        """
        Initialise le connecteur OpenSanctions

        Args:
            api_key: Cle API OpenSanctions (optionnelle pour usage limite)
        """
        self.api_key = api_key or os.getenv('OPENSANCTIONS_API_KEY')

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GEOPOL-Analytics/1.0',
            'Accept': 'application/json'
        })

        if self.api_key:
            self.session.headers['Authorization'] = f'ApiKey {self.api_key}'
            logger.info("[OK] OpenSanctions Connector initialise avec cle API")
        else:
            logger.warning("[WARN] OpenSanctions sans cle API (rate limit strict)")

        self.timeout = 30
        self._cache = {}
        self._cache_ttl = 3600  # 1 heure

    def _make_request(self, endpoint: str, method: str = 'GET',
                      params: Dict = None, json_data: Dict = None) -> Optional[Dict]:
        """
        Effectue une requete a l'API OpenSanctions
        """
        url = f"{self.BASE_URL}{endpoint}"

        try:
            logger.debug(f"[OpenSanctions] {method} {endpoint}")

            if method == 'GET':
                response = self.session.get(url, params=params, timeout=self.timeout)
            else:
                response = self.session.post(url, params=params, json=json_data, timeout=self.timeout)

            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                logger.warning("[OpenSanctions] Rate limit atteint - reessayer plus tard")
            else:
                logger.error(f"[OpenSanctions] HTTP error: {e}")
            return None
        except Exception as e:
            logger.error(f"[OpenSanctions] Erreur: {e}")
            return None

    @cached_connector_method(ttl_seconds=3600, cache_type='opensanctions')
    def get_catalog(self) -> Dict[str, Any]:
        """
        Recupere le catalogue des datasets disponibles
        """
        try:
            data = self._make_request('/catalog')
            if data:
                datasets = data.get('datasets', [])
                logger.info(f"[OK] OpenSanctions: {len(datasets)} datasets disponibles")
                return {
                    'success': True,
                    'datasets': datasets,
                    'count': len(datasets)
                }
            return {'success': False, 'error': 'Pas de reponse'}
        except Exception as e:
            logger.error(f"[OpenSanctions] Erreur catalog: {e}")
            return {'success': False, 'error': str(e)}

    @cached_connector_method(ttl_seconds=1800, cache_type='opensanctions')
    def search_entities(self, query: str, dataset: str = 'default',
                        schema: str = None, countries: List[str] = None,
                        limit: int = 50) -> Dict[str, Any]:
        """
        Recherche d'entites par texte

        Args:
            query: Terme de recherche
            dataset: Dataset a utiliser (default, sanctions, peps, crime, etc.)
            schema: Type d'entite (Person, Company, etc.)
            countries: Liste de codes pays ISO
            limit: Nombre max de resultats
        """
        try:
            params = {
                'q': query,
                'limit': min(limit, 500)
            }

            if schema:
                params['schema'] = schema
            if countries:
                params['countries'] = ','.join(countries)

            endpoint = f'/search/{dataset}'
            data = self._make_request(endpoint, params=params)

            if data:
                results = data.get('results', [])
                logger.info(f"[OK] OpenSanctions search '{query}': {len(results)} resultats")

                # Formater les resultats
                formatted = []
                for entity in results:
                    formatted.append(self._format_entity(entity))

                return {
                    'success': True,
                    'query': query,
                    'dataset': dataset,
                    'total': data.get('total', len(results)),
                    'results': formatted,
                    'facets': data.get('facets', {})
                }

            return {'success': False, 'error': 'Pas de reponse', 'results': []}

        except Exception as e:
            logger.error(f"[OpenSanctions] Erreur search: {e}")
            return {'success': False, 'error': str(e), 'results': []}

    def match_entity(self, name: str, dataset: str = 'default',
                     schema: str = 'Person', birth_date: str = None,
                     nationality: str = None, threshold: float = 0.7) -> Dict[str, Any]:
        """
        Matching d'entite avec score de similarite
        Utile pour le screening KYC/AML

        Args:
            name: Nom de l'entite
            dataset: Dataset (default, sanctions, peps, crime)
            schema: Type (Person, Company, Organization)
            birth_date: Date de naissance (YYYY-MM-DD)
            nationality: Code pays
            threshold: Seuil de matching (0.0-1.0)
        """
        try:
            # Construire la requete de matching
            query = {
                'schema': schema,
                'properties': {
                    'name': [name]
                }
            }

            if birth_date:
                query['properties']['birthDate'] = [birth_date]
            if nationality:
                query['properties']['nationality'] = [nationality]

            endpoint = f'/match/{dataset}'
            params = {
                'threshold': threshold,
                'limit': 10
            }

            data = self._make_request(endpoint, method='POST',
                                      params=params,
                                      json_data={'queries': {'q1': query}})

            if data and 'responses' in data:
                response = data['responses'].get('q1', {})
                results = response.get('results', [])

                logger.info(f"[OK] OpenSanctions match '{name}': {len(results)} correspondances")

                # Formater les resultats
                matches = []
                for match in results:
                    matches.append({
                        'score': match.get('score', 0),
                        'entity': self._format_entity(match)
                    })

                # Determiner si c'est un hit
                is_hit = len(matches) > 0 and matches[0]['score'] >= threshold

                return {
                    'success': True,
                    'query_name': name,
                    'dataset': dataset,
                    'is_hit': is_hit,
                    'match_count': len(matches),
                    'matches': matches,
                    'threshold': threshold
                }

            return {
                'success': True,
                'query_name': name,
                'is_hit': False,
                'match_count': 0,
                'matches': []
            }

        except Exception as e:
            logger.error(f"[OpenSanctions] Erreur match: {e}")
            return {'success': False, 'error': str(e), 'is_hit': False, 'matches': []}

    def get_entity(self, entity_id: str) -> Dict[str, Any]:
        """
        Recupere les details d'une entite specifique

        Args:
            entity_id: ID unique de l'entite
        """
        try:
            data = self._make_request(f'/entities/{entity_id}')

            if data:
                formatted = self._format_entity(data)
                logger.info(f"[OK] OpenSanctions entity {entity_id}")
                return {
                    'success': True,
                    'entity': formatted,
                    'raw': data
                }

            return {'success': False, 'error': 'Entite non trouvee'}

        except Exception as e:
            logger.error(f"[OpenSanctions] Erreur get_entity: {e}")
            return {'success': False, 'error': str(e)}

    @cached_connector_method(ttl_seconds=1800, cache_type='opensanctions')
    def get_crime_entities(self, countries: List[str] = None,
                           limit: int = 100) -> Dict[str, Any]:
        """
        Recupere les entites criminelles (mafias, cartels, trafiquants)

        Args:
            countries: Filtrer par pays (codes ISO)
            limit: Nombre max
        """
        try:
            params = {
                'limit': min(limit, 500)
            }

            if countries:
                params['countries'] = ','.join(countries)

            # Recherche dans le dataset crime
            data = self._make_request('/search/crime', params=params)

            if data:
                results = data.get('results', [])
                logger.info(f"[OK] OpenSanctions crime: {len(results)} entites")

                # Organiser par pays d'origine
                by_country = defaultdict(list)
                formatted = []

                for entity in results:
                    fmt = self._format_entity(entity)
                    formatted.append(fmt)

                    # Grouper par pays
                    for country in fmt.get('countries', []):
                        by_country[country].append(fmt)

                return {
                    'success': True,
                    'total': data.get('total', len(results)),
                    'entities': formatted,
                    'by_country': dict(by_country),
                    'dataset': 'crime'
                }

            return {'success': False, 'entities': [], 'error': 'Pas de reponse'}

        except Exception as e:
            logger.error(f"[OpenSanctions] Erreur crime: {e}")
            return {'success': False, 'error': str(e), 'entities': []}

    @cached_connector_method(ttl_seconds=1800, cache_type='opensanctions')
    def get_sanctions_by_country(self, country_code: str,
                                  limit: int = 100) -> Dict[str, Any]:
        """
        Recupere les entites sanctionnees pour un pays

        Args:
            country_code: Code ISO pays (RU, CN, IR, etc.)
            limit: Nombre max
        """
        try:
            params = {
                'countries': country_code,
                'limit': min(limit, 500)
            }

            data = self._make_request('/search/sanctions', params=params)

            if data:
                results = data.get('results', [])
                logger.info(f"[OK] OpenSanctions {country_code}: {len(results)} sanctionnes")

                # Formater et categoriser
                persons = []
                companies = []
                others = []

                for entity in results:
                    fmt = self._format_entity(entity)
                    schema = fmt.get('schema', '')

                    if schema == 'Person':
                        persons.append(fmt)
                    elif schema in ['Company', 'Organization', 'LegalEntity']:
                        companies.append(fmt)
                    else:
                        others.append(fmt)

                return {
                    'success': True,
                    'country': country_code,
                    'total': data.get('total', len(results)),
                    'persons': persons,
                    'companies': companies,
                    'others': others,
                    'summary': {
                        'persons_count': len(persons),
                        'companies_count': len(companies),
                        'others_count': len(others)
                    }
                }

            return {'success': False, 'error': 'Pas de reponse'}

        except Exception as e:
            logger.error(f"[OpenSanctions] Erreur sanctions country: {e}")
            return {'success': False, 'error': str(e)}

    @cached_connector_method(ttl_seconds=1800, cache_type='opensanctions')
    def get_peps_by_country(self, country_code: str,
                            limit: int = 100) -> Dict[str, Any]:
        """
        Recupere les Personnes Politiquement Exposees (PEPs) pour un pays

        Args:
            country_code: Code ISO pays
            limit: Nombre max
        """
        try:
            params = {
                'countries': country_code,
                'limit': min(limit, 500)
            }

            data = self._make_request('/search/peps', params=params)

            if data:
                results = data.get('results', [])
                logger.info(f"[OK] OpenSanctions PEPs {country_code}: {len(results)}")

                formatted = [self._format_entity(e) for e in results]

                # Categoriser par role/position
                by_position = defaultdict(list)
                for pep in formatted:
                    position = pep.get('position', 'Unknown')
                    by_position[position].append(pep)

                return {
                    'success': True,
                    'country': country_code,
                    'total': data.get('total', len(results)),
                    'peps': formatted,
                    'by_position': dict(by_position)
                }

            return {'success': False, 'error': 'Pas de reponse'}

        except Exception as e:
            logger.error(f"[OpenSanctions] Erreur PEPs: {e}")
            return {'success': False, 'error': str(e)}

    def get_sanctions_summary(self) -> Dict[str, Any]:
        """
        Resume global des sanctions disponibles
        """
        try:
            # Recuperer le catalogue
            catalog = self.get_catalog()

            if not catalog.get('success'):
                return catalog

            # Compter par dataset
            datasets = catalog.get('datasets', [])

            summary = {
                'success': True,
                'total_datasets': len(datasets),
                'datasets': [],
                'updated_at': datetime.now().isoformat()
            }

            # Extraire les infos de chaque dataset
            for ds in datasets:
                summary['datasets'].append({
                    'name': ds.get('name'),
                    'title': ds.get('title'),
                    'entity_count': ds.get('entity_count', 0),
                    'last_change': ds.get('last_change'),
                    'coverage': ds.get('coverage', {})
                })

            # Trier par nombre d'entites
            summary['datasets'].sort(key=lambda x: x.get('entity_count', 0), reverse=True)

            logger.info(f"[OK] OpenSanctions summary: {len(datasets)} datasets")
            return summary

        except Exception as e:
            logger.error(f"[OpenSanctions] Erreur summary: {e}")
            return {'success': False, 'error': str(e)}

    def _format_entity(self, entity: Dict) -> Dict[str, Any]:
        """
        Formate une entite OpenSanctions
        """
        props = entity.get('properties', {})

        # Extraire le nom principal
        names = props.get('name', [])
        name = names[0] if names else entity.get('caption', 'Unknown')

        # Extraire les alias
        aliases = props.get('alias', [])

        # Pays
        countries = props.get('country', [])
        nationalities = props.get('nationality', [])
        all_countries = list(set(countries + nationalities))

        # Topics (sanctions, pep, crime, etc.)
        topics = entity.get('topics', [])

        # Datasets sources
        datasets = entity.get('datasets', [])

        # Position (pour PEPs)
        positions = props.get('position', [])

        formatted = {
            'id': entity.get('id'),
            'schema': entity.get('schema'),
            'name': name,
            'caption': entity.get('caption'),
            'aliases': aliases,
            'countries': all_countries,
            'topics': topics,
            'datasets': datasets,
            'position': positions[0] if positions else None,
            'birth_date': props.get('birthDate', [None])[0],
            'death_date': props.get('deathDate', [None])[0],
            'gender': props.get('gender', [None])[0],
            'address': props.get('address', []),
            'notes': props.get('notes', []),
            'sanctions_programs': props.get('program', []),
            'first_seen': entity.get('first_seen'),
            'last_seen': entity.get('last_seen'),
            'last_change': entity.get('last_change')
        }

        # Score si disponible (pour matching)
        if 'score' in entity:
            formatted['match_score'] = entity['score']

        return formatted

    def verify_api_key(self) -> Dict[str, Any]:
        """
        Verifie si la cle API est valide
        """
        try:
            # Essayer une requete simple
            data = self._make_request('/healthz')

            return {
                'success': True,
                'api_key_configured': bool(self.api_key),
                'status': 'connected',
                'message': 'API OpenSanctions accessible'
            }
        except Exception as e:
            return {
                'success': False,
                'api_key_configured': bool(self.api_key),
                'error': str(e)
            }


def get_opensanctions_connector(api_key: str = None) -> OpenSanctionsConnector:
    """Factory pour obtenir le connecteur OpenSanctions"""
    return OpenSanctionsConnector(api_key=api_key)


__all__ = ['OpenSanctionsConnector', 'get_opensanctions_connector']
