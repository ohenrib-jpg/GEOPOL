"""
Connecteur UN OCHA / HDX (Humanitarian Data Exchange)
API publique sans authentification requise
Source: https://data.humdata.org

Données disponibles:
- Crises humanitaires
- Conflits armés
- Déplacements de population
- Accès humanitaire
- Indicateurs de vulnérabilité
"""

import requests
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json

logger = logging.getLogger(__name__)

# Import du cache intelligent
try:
    from .security_cache import cached_connector_method
    CACHE_ENABLED = True
    logger.debug(f"[OCHA HDX] Cache intelligent activé")
except ImportError as e:
    CACHE_ENABLED = False
    cached_connector_method = lambda source: lambda func: func
    logger.warning(f"[OCHA HDX] Cache intelligent désactivé: {e}")


class OchaHdxConnector:
    """
    Connecteur pour l'API UN OCHA HDX
    Récupère données sur crises, conflits, humanitaire
    """

    BASE_URL = "https://data.humdata.org/api/3"
    SHOWCASE_URL = "https://data.humdata.org"

    # Configuration
    DEFAULT_TIMEOUT = 45
    MAX_RETRIES = 3

    def __init__(self, timeout: int = None, max_retries: int = None):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GEOPOL-Analytics/1.0 (+https://github.com/geopol)',
            'Accept': 'application/json'
        })
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        self.max_retries = max_retries or self.MAX_RETRIES
        self.circuit_breaker = {'failures': 0, 'last_failure': None, 'open': False}

    @cached_connector_method('ocha_hdx')
    def search_datasets(self, query: str = "crisis", limit: int = 20) -> Dict[str, Any]:
        """
        Recherche de datasets sur HDX
        """
        try:
            url = f"{self.BASE_URL}/action/package_search"
            params = {
                'q': query,
                'rows': limit,
                'sort': 'metadata_modified desc'
            }

            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()

            data = response.json()

            if not data.get('success'):
                logger.error("HDX API returned success=false")
                return {'success': False, 'datasets': []}

            result = data.get('result', {})
            datasets = []

            for package in result.get('results', []):
                dataset = {
                    'id': package.get('id'),
                    'name': package.get('name'),
                    'title': package.get('title'),
                    'notes': package.get('notes', '')[:500],  # Description
                    'organization': package.get('organization', {}).get('title'),
                    'dataset_date': package.get('dataset_date'),
                    'updated': package.get('metadata_modified'),
                    'tags': [tag.get('name') for tag in package.get('tags', [])],
                    'resources_count': len(package.get('resources', [])),
                    'url': f"{self.SHOWCASE_URL}/dataset/{package.get('name')}"
                }
                datasets.append(dataset)

            logger.info(f"[OK] HDX search: {len(datasets)} datasets found")

            return {
                'success': True,
                'count': result.get('count', 0),
                'datasets': datasets,
                'query': query,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"[ERROR] HDX search error: {e}")
            return {
                'success': False,
                'error': str(e),
                'datasets': []
            }

    @cached_connector_method('ocha_hdx')
    def get_crisis_data(self) -> Dict[str, Any]:
        """
        Récupère les données sur les crises en cours
        """
        try:
            # Rechercher datasets liés aux crises
            crisis_keywords = [
                'crisis', 'conflict', 'emergency', 'humanitarian',
                'displacement', 'refugees', 'violence'
            ]

            all_datasets = []

            for keyword in crisis_keywords[:3]:  # Limiter pour performance
                result = self.search_datasets(query=keyword, limit=10)
                if result.get('success'):
                    all_datasets.extend(result.get('datasets', []))

            # Dédupliquer par ID
            unique_datasets = {ds['id']: ds for ds in all_datasets}
            datasets = list(unique_datasets.values())

            # Analyser les tags pour extraire les pays affectés
            countries = set()
            crisis_types = set()

            for ds in datasets:
                tags = ds.get('tags', [])
                for tag in tags:
                    tag_lower = tag.lower()
                    # Détecter types de crises
                    if any(word in tag_lower for word in ['conflict', 'war', 'violence']):
                        crisis_types.add('armed_conflict')
                    elif any(word in tag_lower for word in ['displacement', 'refugees', 'idp']):
                        crisis_types.add('displacement')
                    elif any(word in tag_lower for word in ['food', 'famine', 'nutrition']):
                        crisis_types.add('food_security')
                    elif any(word in tag_lower for word in ['health', 'disease', 'covid']):
                        crisis_types.add('health')

            logger.info(f"[OK] Crisis data: {len(datasets)} datasets, {len(crisis_types)} crisis types")

            return {
                'success': True,
                'datasets_count': len(datasets),
                'crisis_types': list(crisis_types),
                'datasets': datasets[:20],  # Top 20
                'timestamp': datetime.now().isoformat(),
                'source': 'UN OCHA HDX'
            }

        except Exception as e:
            logger.error(f"[ERROR] Crisis data error: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_conflict_data(self) -> Dict[str, Any]:
        """
        Récupère les données sur les conflits armés
        """
        try:
            result = self.search_datasets(
                query='armed conflict OR violence OR war',
                limit=30
            )

            if not result.get('success'):
                return result

            datasets = result.get('datasets', [])

            # Analyser par région
            regions = {}
            for ds in datasets:
                org = ds.get('organization', 'Unknown')
                if org not in regions:
                    regions[org] = []
                regions[org].append(ds)

            logger.info(f"[OK] Conflict data: {len(datasets)} datasets, {len(regions)} regions")

            return {
                'success': True,
                'datasets_count': len(datasets),
                'regions': list(regions.keys()),
                'datasets': datasets,
                'by_region': regions,
                'timestamp': datetime.now().isoformat(),
                'source': 'UN OCHA HDX'
            }

        except Exception as e:
            logger.error(f"[ERROR] Conflict data error: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_displacement_data(self) -> Dict[str, Any]:
        """
        Récupère les données sur les déplacements de population
        """
        try:
            result = self.search_datasets(
                query='displacement OR refugees OR IDP OR migration',
                limit=30
            )

            if not result.get('success'):
                return result

            datasets = result.get('datasets', [])

            logger.info(f"[OK] Displacement data: {len(datasets)} datasets")

            return {
                'success': True,
                'datasets_count': len(datasets),
                'datasets': datasets,
                'timestamp': datetime.now().isoformat(),
                'source': 'UN OCHA HDX'
            }

        except Exception as e:
            logger.error(f"[ERROR] Displacement data error: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_humanitarian_access(self) -> Dict[str, Any]:
        """
        Récupère les données sur l'accès humanitaire
        """
        try:
            result = self.search_datasets(
                query='humanitarian access OR aid OR relief',
                limit=20
            )

            if not result.get('success'):
                return result

            datasets = result.get('datasets', [])

            logger.info(f"[OK] Humanitarian access data: {len(datasets)} datasets")

            return {
                'success': True,
                'datasets_count': len(datasets),
                'datasets': datasets,
                'timestamp': datetime.now().isoformat(),
                'source': 'UN OCHA HDX'
            }

        except Exception as e:
            logger.error(f"[ERROR] Humanitarian access error: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_country_data(self, country: str) -> Dict[str, Any]:
        """
        Récupère toutes les données pour un pays spécifique
        """
        try:
            # Rechercher datasets pour le pays
            result = self.search_datasets(
                query=f'groups:{country.lower()}',
                limit=50
            )

            if not result.get('success'):
                return result

            datasets = result.get('datasets', [])

            # Catégoriser par type
            categories = {
                'conflict': [],
                'displacement': [],
                'humanitarian': [],
                'health': [],
                'food_security': [],
                'other': []
            }

            for ds in datasets:
                tags = ' '.join(ds.get('tags', [])).lower()
                title = ds.get('title', '').lower()
                text = f"{tags} {title}"

                if any(word in text for word in ['conflict', 'violence', 'war']):
                    categories['conflict'].append(ds)
                elif any(word in text for word in ['displacement', 'refugees', 'idp']):
                    categories['displacement'].append(ds)
                elif any(word in text for word in ['humanitarian', 'aid', 'relief']):
                    categories['humanitarian'].append(ds)
                elif any(word in text for word in ['health', 'disease', 'covid']):
                    categories['health'].append(ds)
                elif any(word in text for word in ['food', 'nutrition', 'famine']):
                    categories['food_security'].append(ds)
                else:
                    categories['other'].append(ds)

            logger.info(f"[OK] Country data for {country}: {len(datasets)} datasets")

            return {
                'success': True,
                'country': country,
                'datasets_count': len(datasets),
                'categories': {k: len(v) for k, v in categories.items()},
                'datasets': datasets,
                'by_category': categories,
                'timestamp': datetime.now().isoformat(),
                'source': 'UN OCHA HDX'
            }

        except Exception as e:
            logger.error(f"[ERROR] Country data error for {country}: {e}")
            return {
                'success': False,
                'error': str(e),
                'country': country
            }

    @cached_connector_method('ocha_hdx')
    def get_summary(self) -> Dict[str, Any]:
        """
        Récupère un résumé global des crises et conflits actuels
        """
        try:
            crisis_data = self.get_crisis_data()
            conflict_data = self.get_conflict_data()
            displacement_data = self.get_displacement_data()

            summary = {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'source': 'UN OCHA HDX',
                'statistics': {
                    'total_crisis_datasets': crisis_data.get('datasets_count', 0),
                    'total_conflict_datasets': conflict_data.get('datasets_count', 0),
                    'total_displacement_datasets': displacement_data.get('datasets_count', 0),
                    'crisis_types': crisis_data.get('crisis_types', []),
                    'affected_regions': conflict_data.get('regions', [])
                },
                'latest_updates': []
            }

            # Combiner les dernières mises à jour
            all_datasets = []
            if crisis_data.get('success'):
                all_datasets.extend(crisis_data.get('datasets', []))
            if conflict_data.get('success'):
                all_datasets.extend(conflict_data.get('datasets', []))
            if displacement_data.get('success'):
                all_datasets.extend(displacement_data.get('datasets', []))

            # Trier par date de mise à jour
            all_datasets.sort(key=lambda x: x.get('updated', ''), reverse=True)

            # Top 10 dernières mises à jour
            summary['latest_updates'] = all_datasets[:10]

            logger.info("[OK] HDX summary generated")

            return summary

        except Exception as e:
            logger.error(f"[ERROR] Summary error: {e}")
            return {
                'success': False,
                'error': str(e)
            }


def get_ocha_hdx_connector() -> OchaHdxConnector:
    """Factory pour obtenir le connecteur"""
    return OchaHdxConnector()


__all__ = ['OchaHdxConnector', 'get_ocha_hdx_connector']
