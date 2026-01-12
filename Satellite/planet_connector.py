"""
Planet API Connector - Accès aux données Planet

Fournit accès à l'API Planet (anciennement Planet Labs) :
- PlanetScope (3m de résolution, quotidien)
- SkySat (50cm de résolution)
- RapidEye (5m)

Documentation: https://developers.planet.com/docs/apis/

Organisation: 798194 (Evaluation Program)
Créé: 2025-12-27

Version: 1.0.0
Author: GEOPOL Analytics
"""

import os
import requests
import logging
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class PlanetConnector:
    """
    Connecteur Planet API.

    Utilise l'authentification par API Key (pas OAuth2).
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialise le connecteur Planet.

        Args:
            api_key: Clé API Planet (ou charge depuis PLANET_API_KEY)
        """
        self.api_key = api_key or os.getenv('PLANET_API_KEY')
        self.base_url = os.getenv('PLANET_BASE_URL', 'https://api.planet.com')

        # URLs API
        self.data_api_url = f"{self.base_url}/data/v1"
        self.basemaps_url = f"{self.base_url}/basemaps/v1"
        self.orders_url = f"{self.base_url}/compute/ops/orders/v2"

        # Collections disponibles
        self.item_types = {
            'PSScene': {
                'name': 'PlanetScope Scene',
                'description': 'Imagerie quotidienne 3m de résolution',
                'resolution': '3m',
                'revisit': 'Quotidien'
            },
            'SkySatScene': {
                'name': 'SkySat Scene',
                'description': 'Imagerie très haute résolution 50cm',
                'resolution': '50cm',
                'revisit': 'Sur demande'
            },
            'SkySatCollect': {
                'name': 'SkySat Collect',
                'description': 'Collection SkySat consolidée',
                'resolution': '50cm',
                'revisit': 'Sur demande'
            },
            'REOrthoTile': {
                'name': 'RapidEye Ortho Tile',
                'description': 'Imagerie RapidEye 5m',
                'resolution': '5m',
                'revisit': '5.5 jours'
            }
        }

        if self.api_key:
            logger.info(f"[PLANET] Connecteur initialisé (API Key présente)")
        else:
            logger.warning("[PLANET] API Key non configurée")

    def is_configured(self) -> bool:
        """Vérifie si Planet est configuré."""
        return bool(self.api_key)

    def test_connection(self) -> bool:
        """
        Teste la connexion à l'API Planet.

        Returns:
            True si connexion OK
        """
        if not self.api_key:
            logger.warning("[PLANET] API Key non configurée")
            return False

        try:
            response = requests.get(
                f"{self.data_api_url}/item-types",
                auth=(self.api_key, ''),
                timeout=10
            )

            if response.status_code == 200:
                logger.info("[PLANET] Connexion OK")
                return True
            elif response.status_code == 401:
                logger.error("[PLANET] API Key invalide")
                return False
            else:
                logger.error(f"[PLANET] Erreur {response.status_code}")
                return False

        except requests.RequestException as e:
            logger.error(f"[PLANET] Erreur connexion: {e}")
            return False

    def get_available_layers(self) -> Dict[str, Dict]:
        """
        Retourne les couches Planet disponibles.

        Returns:
            Dictionnaire {layer_id: metadata}
        """
        if not self.api_key:
            return {}

        layers = {}

        for item_type, metadata in self.item_types.items():
            layer_id = f"planet_{item_type.lower()}"

            layers[layer_id] = {
                'name': metadata['name'],
                'description': metadata['description'],
                'type': 'satellite',
                'category': 'satellite',
                'provider': 'Planet',
                'resolution': metadata['resolution'],
                'revisit': metadata['revisit'],
                'coverage': 'Mondiale',
                'requires_auth': True,
                'item_type': item_type
            }

        logger.debug(f"[PLANET] {len(layers)} couches disponibles")
        return layers

    def search_images(
        self,
        bbox: Tuple[float, float, float, float],
        start_date: str,
        end_date: str,
        item_type: str = 'PSScene',
        max_cloud_cover: float = 0.3,
        limit: int = 10
    ) -> List[Dict]:
        """
        Recherche d'images Planet.

        Args:
            bbox: Bounding box (min_lon, min_lat, max_lon, max_lat)
            start_date: Date début (YYYY-MM-DD)
            end_date: Date fin (YYYY-MM-DD)
            item_type: Type d'item Planet
            max_cloud_cover: Couverture nuageuse max (0-1)
            limit: Nombre max de résultats

        Returns:
            Liste de métadonnées d'images
        """
        if not self.api_key:
            logger.error("[PLANET] API Key requise")
            return []

        try:
            # Construire le filtre géographique
            geo_filter = {
                "type": "GeometryFilter",
                "field_name": "geometry",
                "config": {
                    "type": "Polygon",
                    "coordinates": [[
                        [bbox[0], bbox[1]],
                        [bbox[2], bbox[1]],
                        [bbox[2], bbox[3]],
                        [bbox[0], bbox[3]],
                        [bbox[0], bbox[1]]
                    ]]
                }
            }

            # Filtre de date
            date_filter = {
                "type": "DateRangeFilter",
                "field_name": "acquired",
                "config": {
                    "gte": f"{start_date}T00:00:00.000Z",
                    "lte": f"{end_date}T23:59:59.999Z"
                }
            }

            # Filtre de couverture nuageuse
            cloud_filter = {
                "type": "RangeFilter",
                "field_name": "cloud_cover",
                "config": {
                    "lte": max_cloud_cover
                }
            }

            # Combiner les filtres
            combined_filter = {
                "type": "AndFilter",
                "config": [geo_filter, date_filter, cloud_filter]
            }

            # Requête de recherche
            search_request = {
                "item_types": [item_type],
                "filter": combined_filter
            }

            response = requests.post(
                f"{self.data_api_url}/quick-search",
                auth=(self.api_key, ''),
                json=search_request,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            features = data.get('features', [])[:limit]

            results = []
            for feature in features:
                props = feature.get('properties', {})

                result = {
                    'id': feature.get('id'),
                    'item_type': props.get('item_type'),
                    'acquired': props.get('acquired'),
                    'cloud_cover': props.get('cloud_cover'),
                    'sun_elevation': props.get('sun_elevation'),
                    'pixel_resolution': props.get('pixel_resolution'),
                    'geometry': feature.get('geometry'),
                    'provider': 'Planet',
                    '_links': feature.get('_links', {})
                }
                results.append(result)

            logger.info(f"[PLANET] {len(results)} images trouvées")
            return results

        except requests.RequestException as e:
            logger.error(f"[PLANET] Erreur recherche: {e}")
            return []

    def get_thumbnail_url(self, item_id: str, item_type: str = 'PSScene') -> Optional[str]:
        """
        Génère l'URL de la miniature d'une image.

        Args:
            item_id: ID de l'item
            item_type: Type d'item

        Returns:
            URL de la miniature
        """
        if not self.api_key:
            return None

        return f"{self.data_api_url}/item-types/{item_type}/items/{item_id}/thumb"

    def get_quota_info(self) -> Optional[Dict]:
        """
        Récupère les informations de quota.

        Returns:
            Informations de quota
        """
        if not self.api_key:
            return None

        try:
            response = requests.get(
                f"{self.base_url}/auth/v1/experimental/public/my/subscriptions",
                auth=(self.api_key, ''),
                timeout=10
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {'status': 'error', 'code': response.status_code}

        except requests.RequestException as e:
            logger.error(f"[PLANET] Erreur quota: {e}")
            return None


# Singleton global
_planet_connector = None


def get_planet_connector() -> PlanetConnector:
    """
    Factory pour le connecteur Planet.

    Returns:
        Instance de PlanetConnector
    """
    global _planet_connector

    if _planet_connector is None:
        _planet_connector = PlanetConnector()

    return _planet_connector
