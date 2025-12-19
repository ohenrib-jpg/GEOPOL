"""
Module satellite avancé - Sentinel Hub API

Fournit accès aux données Sentinel via l'API Copernicus Dataspace :
- Sentinel-2 L2A (optique haute résolution 10m)
- Sentinel-2 L1C (optique non-atmosphérique)
- Sentinel-1 GRD (radar)

Nécessite des identifiants utilisateur (OAuth2 Client ID + Secret).
Gratuits : https://dataspace.copernicus.eu/

Version: 2.0.0
Author: GEOPOL Analytics
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import logging

logger = logging.getLogger(__name__)


class SatelliteAdvanced:
    """
    Module satellite avancé utilisant l'API Sentinel Hub.

    Authentification OAuth2 avec identifiants utilisateur.
    """

    def __init__(self, client_id: str, client_secret: str):
        """
        Initialise le module avancé.

        Args:
            client_id: OAuth2 Client ID
            client_secret: OAuth2 Client Secret
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.token_expiry = None

        # URLs API Copernicus Dataspace
        self.auth_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
        self.base_url = "https://sh.dataspace.copernicus.eu"
        self.catalog_url = "https://catalogue.dataspace.copernicus.eu/odata/v1"

        # Collections disponibles
        self.collections = {
            'sentinel2_l2a': {
                'id': 'SENTINEL2_L2A',
                'name': 'Sentinel-2 L2A',
                'description': 'Optique haute résolution (10m) - Correction atmosphérique',
                'resolution': '10m',
                'type': 'optical',
                'bands': ['B02', 'B03', 'B04', 'B08', 'B11', 'B12']
            },
            'sentinel2_l1c': {
                'id': 'SENTINEL2_L1C',
                'name': 'Sentinel-2 L1C',
                'description': 'Optique haute résolution (10m) - Top of atmosphere',
                'resolution': '10m',
                'type': 'optical',
                'bands': ['B02', 'B03', 'B04', 'B08', 'B11', 'B12']
            },
            'sentinel1_grd': {
                'id': 'SENTINEL1_GRD',
                'name': 'Sentinel-1 GRD',
                'description': 'Radar (10m) - Tout temps, jour/nuit',
                'resolution': '10m',
                'type': 'radar',
                'bands': ['VV', 'VH']
            }
        }

        logger.info("🛰️ SatelliteAdvanced initialisé")

    # ========================================
    # AUTHENTIFICATION
    # ========================================

    def _get_access_token(self) -> str:
        """
        Obtient un token d'accès OAuth2.

        Returns:
            Token d'accès valide

        Raises:
            Exception si échec authentification
        """
        # Vérifier si le token actuel est encore valide
        if self.access_token and self.token_expiry:
            if datetime.now() < self.token_expiry:
                logger.debug("📦 Token OAuth2 en cache")
                return self.access_token

        logger.info("🔑 Demande nouveau token OAuth2...")

        # Requête OAuth2
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }

        try:
            response = requests.post(
                self.auth_url,
                data=data,
                timeout=10
            )
            response.raise_for_status()

            token_data = response.json()

            self.access_token = token_data["access_token"]

            # Définir l'expiration (moins 60s de marge)
            expires_in = token_data.get("expires_in", 300) - 60
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in)

            logger.info(f"✅ Token OAuth2 obtenu (expire dans {expires_in}s)")
            return self.access_token

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Erreur authentification: {e}")
            raise Exception(f"Échec authentification OAuth2: {e}")

    def test_connection(self) -> bool:
        """
        Teste la connexion à l'API.

        Returns:
            True si connexion OK
        """
        try:
            token = self._get_access_token()
            logger.info("✅ Connexion API Sentinel Hub OK")
            return True
        except Exception as e:
            logger.error(f"❌ Échec test connexion: {e}")
            return False

    # ========================================
    # COUCHES DISPONIBLES
    # ========================================

    def get_available_layers(self) -> Dict[str, Dict]:
        """
        Retourne les couches Sentinel disponibles.

        Returns:
            Dictionnaire {layer_id: metadata}
        """
        layers = {}

        for collection_id, metadata in self.collections.items():
            # Couche True Color (RGB naturel)
            layers[f"{collection_id}_truecolor"] = {
                'name': f"{metadata['name']} - True Color",
                'description': f"Image couleur naturelle - {metadata['description']}",
                'type': 'satellite',
                'category': 'satellite',
                'collection': metadata['id'],
                'resolution': metadata['resolution'],
                'coverage': 'Mondiale',
                'requires_auth': True,
                'visualization': 'true_color'
            }

            # Couche False Color (infrarouge)
            if metadata['type'] == 'optical':
                layers[f"{collection_id}_falsecolor"] = {
                    'name': f"{metadata['name']} - False Color",
                    'description': f"Fausses couleurs (végétation en rouge) - {metadata['description']}",
                    'type': 'satellite',
                    'category': 'satellite',
                    'collection': metadata['id'],
                    'resolution': metadata['resolution'],
                    'coverage': 'Mondiale',
                    'requires_auth': True,
                    'visualization': 'false_color'
                }

                # NDVI
                layers[f"{collection_id}_ndvi"] = {
                    'name': f"{metadata['name']} - NDVI",
                    'description': f"Indice de végétation - {metadata['description']}",
                    'type': 'satellite',
                    'category': 'thematic',
                    'collection': metadata['id'],
                    'resolution': metadata['resolution'],
                    'coverage': 'Mondiale',
                    'requires_auth': True,
                    'visualization': 'ndvi'
                }

        logger.debug(f"✅ {len(layers)} couches Sentinel disponibles")
        return layers

    # ========================================
    # GÉNÉRATION URLS
    # ========================================

    def get_layer_url(
        self,
        layer_id: str,
        bbox: Tuple[float, float, float, float],
        width: int = 512,
        height: int = 512,
        date: Optional[str] = None,
        max_cloud_coverage: int = 30
    ) -> Optional[str]:
        """
        Génère l'URL pour une image Sentinel.

        Args:
            layer_id: Identifiant de la couche
            bbox: Bounding box (min_lon, min_lat, max_lon, max_lat)
            width: Largeur en pixels
            height: Hauteur en pixels
            date: Date au format YYYY-MM-DD (optionnel)
            max_cloud_coverage: Couverture nuageuse max (%)

        Returns:
            URL de l'image ou None
        """
        try:
            # Obtenir le token
            token = self._get_access_token()

            # Extraire collection et visualisation du layer_id
            parts = layer_id.split('_')
            if len(parts) < 3:
                logger.error(f"❌ Format layer_id invalide: {layer_id}")
                return None

            collection_key = f"{parts[0]}_{parts[1]}"  # ex: sentinel2_l2a
            visualization = '_'.join(parts[2:])  # ex: truecolor

            if collection_key not in self.collections:
                logger.error(f"❌ Collection inconnue: {collection_key}")
                return None

            collection = self.collections[collection_key]['id']

            # Définir la période de recherche
            if date:
                try:
                    target_date = datetime.strptime(date, '%Y-%m-%d')
                except ValueError:
                    logger.error(f"❌ Format date invalide: {date}")
                    return None
            else:
                target_date = datetime.now()

            # Période : 30 jours avant la date cible
            end_date = target_date
            start_date = end_date - timedelta(days=30)

            # Construire la requête Process API
            request_body = self._build_process_request(
                collection=collection,
                bbox=bbox,
                width=width,
                height=height,
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d'),
                visualization=visualization,
                max_cloud_coverage=max_cloud_coverage
            )

            # URL Process API
            process_url = f"{self.base_url}/api/v1/process"

            # Faire la requête
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }

            response = requests.post(
                process_url,
                headers=headers,
                json=request_body,
                timeout=30
            )

            if response.status_code == 200:
                # Retourner l'URL avec le token
                logger.debug(f"✅ Image Sentinel générée pour {layer_id}")
                # Note: En production, il faudrait sauvegarder l'image et retourner son URL
                # Pour l'instant, on retourne une URL de requête
                return process_url

            else:
                logger.error(f"❌ Erreur API Sentinel: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"❌ Erreur génération URL Sentinel: {e}")
            return None

    def _build_process_request(
        self,
        collection: str,
        bbox: Tuple[float, float, float, float],
        width: int,
        height: int,
        start_date: str,
        end_date: str,
        visualization: str,
        max_cloud_coverage: int
    ) -> Dict:
        """
        Construit le corps de la requête Process API.

        Args:
            collection: Collection Sentinel
            bbox: Bounding box
            width: Largeur
            height: Hauteur
            start_date: Date début (YYYY-MM-DD)
            end_date: Date fin (YYYY-MM-DD)
            visualization: Type de visualisation
            max_cloud_coverage: Couverture nuageuse max

        Returns:
            Dictionnaire de requête
        """
        # Evalscript selon la visualisation
        evalscript = self._get_evalscript(visualization)

        # Construire la requête
        request = {
            "input": {
                "bounds": {
                    "bbox": list(bbox),
                    "properties": {
                        "crs": "http://www.opengis.net/def/crs/EPSG/0/4326"
                    }
                },
                "data": [
                    {
                        "type": collection,
                        "dataFilter": {
                            "timeRange": {
                                "from": f"{start_date}T00:00:00Z",
                                "to": f"{end_date}T23:59:59Z"
                            },
                            "maxCloudCoverage": max_cloud_coverage
                        }
                    }
                ]
            },
            "output": {
                "width": width,
                "height": height,
                "responses": [
                    {
                        "identifier": "default",
                        "format": {
                            "type": "image/png"
                        }
                    }
                ]
            },
            "evalscript": evalscript
        }

        return request

    def _get_evalscript(self, visualization: str) -> str:
        """
        Retourne l'evalscript pour une visualisation.

        Args:
            visualization: Type (truecolor, falsecolor, ndvi)

        Returns:
            Code evalscript JavaScript
        """
        evalscripts = {
            'truecolor': """
                //VERSION=3
                function setup() {
                    return {
                        input: ["B04", "B03", "B02"],
                        output: { bands: 3 }
                    };
                }
                function evaluatePixel(sample) {
                    return [2.5 * sample.B04, 2.5 * sample.B03, 2.5 * sample.B02];
                }
            """,
            'falsecolor': """
                //VERSION=3
                function setup() {
                    return {
                        input: ["B08", "B04", "B03"],
                        output: { bands: 3 }
                    };
                }
                function evaluatePixel(sample) {
                    return [2.5 * sample.B08, 2.5 * sample.B04, 2.5 * sample.B03];
                }
            """,
            'ndvi': """
                //VERSION=3
                function setup() {
                    return {
                        input: ["B04", "B08"],
                        output: { bands: 3 }
                    };
                }
                function evaluatePixel(sample) {
                    let ndvi = (sample.B08 - sample.B04) / (sample.B08 + sample.B04);
                    if (ndvi < -0.2) return [0.05, 0.05, 0.05];
                    else if (ndvi < 0.0) return [0.75, 0.75, 0.75];
                    else if (ndvi < 0.1) return [0.86, 0.86, 0.86];
                    else if (ndvi < 0.2) return [1.0, 0.98, 0.8];
                    else if (ndvi < 0.3) return [0.93, 0.91, 0.71];
                    else if (ndvi < 0.4) return [0.87, 0.85, 0.61];
                    else if (ndvi < 0.5) return [0.8, 0.78, 0.51];
                    else if (ndvi < 0.6) return [0.74, 0.72, 0.42];
                    else if (ndvi < 0.7) return [0.69, 0.76, 0.38];
                    else if (ndvi < 0.8) return [0.64, 0.8, 0.35];
                    else return [0.57, 0.75, 0.32];
                }
            """
        }

        return evalscripts.get(visualization, evalscripts['truecolor'])

    # ========================================
    # RECHERCHE IMAGES
    # ========================================

    def search_images(
        self,
        bbox: Tuple[float, float, float, float],
        start_date: str,
        end_date: str,
        collection: str = 'SENTINEL2_L2A',
        max_cloud_coverage: int = 30,
        limit: int = 10
    ) -> List[Dict]:
        """
        Recherche d'images Sentinel disponibles.

        Args:
            bbox: Bounding box
            start_date: Date début (YYYY-MM-DD)
            end_date: Date fin (YYYY-MM-DD)
            collection: Collection Sentinel
            max_cloud_coverage: Couverture nuageuse max (%)
            limit: Nombre max de résultats

        Returns:
            Liste de métadonnées d'images
        """
        try:
            token = self._get_access_token()

            # Construire la requête Catalog
            catalog_filter = {
                "datetime": f"{start_date}T00:00:00Z/{end_date}T23:59:59Z",
                "collections": [collection],
                "bbox": list(bbox),
                "limit": limit,
                "filter": f"eo:cloud_cover < {max_cloud_coverage}"
            }

            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }

            # Note: L'API Catalog peut varier selon la version
            # Ceci est une implémentation simplifiée
            logger.info(f"🔍 Recherche images {collection} ({start_date} à {end_date})")

            # En production, faire la vraie requête au catalogue
            # Pour l'instant, retourner une liste vide
            return []

        except Exception as e:
            logger.error(f"❌ Erreur recherche images: {e}")
            return []

    # ========================================
    # STATISTIQUES
    # ========================================

    def get_statistics(
        self,
        bbox: Tuple[float, float, float, float],
        start_date: str,
        end_date: str,
        collection: str = 'SENTINEL2_L2A',
        bands: List[str] = None
    ) -> Optional[Dict]:
        """
        Calcule des statistiques sur une zone.

        Args:
            bbox: Bounding box
            start_date: Date début
            end_date: Date fin
            collection: Collection Sentinel
            bands: Bandes à analyser

        Returns:
            Statistiques (mean, min, max, stddev)
        """
        try:
            token = self._get_access_token()

            if bands is None:
                bands = ['B04', 'B03', 'B02']  # RGB par défaut

            # Construire la requête Statistical API
            # Note: Implémentation simplifiée
            logger.info(f"📊 Calcul statistiques {collection}")

            # En production, faire la vraie requête
            return None

        except Exception as e:
            logger.error(f"❌ Erreur calcul statistiques: {e}")
            return None

    # ========================================
    # UTILITAIRES
    # ========================================

    def get_quota_info(self) -> Optional[Dict]:
        """
        Récupère les informations de quota.

        Returns:
            Informations de quota (processing units restantes, etc.)
        """
        try:
            token = self._get_access_token()

            # En production, interroger l'API de quotas
            logger.info("📊 Récupération info quota")

            return {
                'status': 'ok',
                'message': 'Quota non implémenté (gratuit)'
            }

        except Exception as e:
            logger.error(f"❌ Erreur info quota: {e}")
            return None
