"""
Module satellite avancé - Copernicus Dataspace API

Fournit accès aux données Sentinel via l'API Copernicus Dataspace :
- Sentinel-2 L2A (optique haute résolution 10m)
- Sentinel-2 L1C (optique non-atmosphérique)
- Sentinel-1 GRD (radar)

Nécessite des identifiants utilisateur (OAuth2 Client ID + Secret).
Gratuits : https://dataspace.copernicus.eu/

Version: 2.0.1 - CORRIGE
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
    Module satellite avancé utilisant l'API Copernicus Dataspace.

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

        # URLs API - Support multiple providers: Copernicus Dataspace, Sentinel Hub/Planet Insight
        import os
        # Try Sentinel Hub/Planet Insight variables first
        sentinel_auth_url = os.getenv('SENTINEL_HUB_AUTH_URL')
        sentinel_base_url = os.getenv('SENTINEL_HUB_BASE_URL')

        if sentinel_auth_url and sentinel_base_url:
            # Using Sentinel Hub/Planet Insight
            self.auth_url = sentinel_auth_url
            self.catalog_url = f"{sentinel_base_url}/catalog/api/v1/products"
            self.download_url = f"{sentinel_base_url}/api/v1/process"
            self.provider = 'sentinel_hub'
            logger.info(f"[CONFIG] Using Sentinel Hub/Planet Insight: {sentinel_base_url}")
        else:
            # Fallback to Copernicus Dataspace
            self.auth_url = os.getenv('COPERNICUS_AUTH_URL', 'https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token')
            self.catalog_url = os.getenv('COPERNICUS_CATALOG_URL', 'https://catalogue.dataspace.copernicus.eu/resto/api/collections/Sentinel2/search.json')
            self.download_url = os.getenv('COPERNICUS_DOWNLOAD_URL', 'https://zipper.dataspace.copernicus.eu/odata/v1/Products')
            self.provider = 'copernicus'
            logger.info(f"[CONFIG] Using Copernicus Dataspace (fallback)")

        logger.info(f"[CONFIG] Auth URL: {self.auth_url}")
        logger.info(f"[CONFIG] Catalog URL: {self.catalog_url}")
        logger.info(f"[CONFIG] Provider: {self.provider}")

        # Collections disponibles
        self.collections = {
            'sentinel2_l2a': {
                'id': 'Sentinel2',
                'name': 'Sentinel-2 L2A',
                'description': 'Optique haute résolution (10m) - Correction atmosphérique',
                'resolution': '10m',
                'type': 'optical',
                'bands': ['B02', 'B03', 'B04', 'B08', 'B11', 'B12']
            },
            'sentinel2_l1c': {
                'id': 'Sentinel2',
                'name': 'Sentinel-2 L1C',
                'description': 'Optique haute résolution (10m) - Top of atmosphere',
                'resolution': '10m',
                'type': 'optical',
                'bands': ['B02', 'B03', 'B04', 'B08', 'B11', 'B12']
            },
            'sentinel1_grd': {
                'id': 'Sentinel1',
                'name': 'Sentinel-1 GRD',
                'description': 'Radar (10m) - Tout temps, jour/nuit',
                'resolution': '10m',
                'type': 'radar',
                'bands': ['VV', 'VH']
            }
        }

        logger.info("[SATELLITE] SatelliteAdvanced initialisé")

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
                logger.debug("[CACHE] Token OAuth2 en cache")
                return self.access_token

        logger.info("[AUTH] Demande nouveau token OAuth2...")

        # Requête OAuth2 CORRIGEE pour Copernicus
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        try:
            response = requests.post(
                self.auth_url,
                data=data,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()

            token_data = response.json()

            self.access_token = token_data["access_token"]

            # Définir l'expiration (moins 60s de marge)
            expires_in = token_data.get("expires_in", 300) - 60
            self.token_expiry = datetime.now() + timedelta(seconds=expires_in)

            logger.info(f"[OK] Token OAuth2 obtenu (expire dans {expires_in}s)")
            return self.access_token

        except requests.exceptions.RequestException as e:
            logger.error(f"[ERROR] Erreur authentification: {e}")
            raise Exception(f"Échec authentification OAuth2: {e}")

    def test_connection(self) -> bool:
        """
        Teste la connexion à l'API.

        Returns:
            True si connexion OK
        """
        try:
            token = self._get_access_token()
            logger.info("[OK] Connexion API Copernicus Dataspace OK")
            return True
        except Exception as e:
            logger.error(f"[ERROR] Échec test connexion: {e}")
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

        logger.debug(f"[OK] {len(layers)} couches Sentinel disponibles")
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
                logger.error(f"[ERROR] Format layer_id invalide: {layer_id}")
                return None

            collection_key = f"{parts[0]}_{parts[1]}"  # ex: sentinel2_l2a
            visualization = '_'.join(parts[2:])  # ex: truecolor

            if collection_key not in self.collections:
                logger.error(f"[ERROR] Collection inconnue: {collection_key}")
                return None

            # Pour Copernicus, on retourne une URL de téléchargement
            # ou on indique qu'il faut utiliser l'API de recherche
            logger.debug(f"[OK] Couche avancée {layer_id} prête (token valide)")
            return f"advanced_layer://{layer_id}"

        except Exception as e:
            logger.error(f"[ERROR] Erreur génération URL Sentinel: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

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
        collection: str = 'Sentinel2',
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

            logger.info(f"[SEARCH] Recherche images {collection} ({start_date} à {end_date})")

            # Construire la requête pour Copernicus
            params = {
                'box': f'{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}',
                'startDate': f'{start_date}T00:00:00Z',
                'completionDate': f'{end_date}T23:59:59Z',
                'cloudCover': f'[0,{max_cloud_coverage}]',
                'maxRecords': limit,
                'processingLevel': 'S2MSI2A' if collection == 'Sentinel2' else None
            }

            headers = {
                'Authorization': f'Bearer {token}'
            }

            response = requests.get(
                self.catalog_url,
                params=params,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            features = data.get('features', [])

            results = []
            for feature in features:
                props = feature.get('properties', {})

                result = {
                    'id': props.get('productIdentifier'),
                    'title': props.get('title'),
                    'date': props.get('startDate'),
                    'cloud_cover': props.get('cloudCover'),
                    'product_type': props.get('processingLevel'),
                    'platform': props.get('platform'),
                    'geometry': feature.get('geometry'),
                    'download_link': props.get('services', {}).get('download', {}).get('url')
                }
                results.append(result)

            logger.info(f"[OK] {len(results)} images trouvées")
            return results

        except Exception as e:
            logger.error(f"[ERROR] Erreur recherche images: {e}")
            return []

    # ========================================
    # STATISTIQUES
    # ========================================

    def get_statistics(
        self,
        bbox: Tuple[float, float, float, float],
        start_date: str,
        end_date: str,
        collection: str = 'Sentinel2',
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

            # Pour l'instant, retourner une structure de base
            logger.info(f"[STATS] Calcul statistiques {collection}")

            return {
                'status': 'ok',
                'message': 'Fonctionnalité à implémenter',
                'bands': bands
            }

        except Exception as e:
            logger.error(f"[ERROR] Erreur calcul statistiques: {e}")
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

            logger.info("[STATS] Récupération info quota")

            return {
                'status': 'ok',
                'message': 'Quota non implémenté (gratuit)'
            }

        except Exception as e:
            logger.error(f"[ERROR] Erreur info quota: {e}")
            return None
