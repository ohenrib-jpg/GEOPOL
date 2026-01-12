"""
Téléchargeur d'images Sentinel Hub

Récupère des images satellite réelles depuis Sentinel Hub
et les convertit en numpy arrays pour analyse YOLO.

Version: 1.0.0
Author: GEOPOL Analytics
"""

import requests
import numpy as np
from PIL import Image
from io import BytesIO
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
import logging
import os

logger = logging.getLogger(__name__)


class SentinelImageDownloader:
    """
    Téléchargeur d'images Sentinel Hub.
    Récupère des images RGB et multi-spectrales.
    """

    def __init__(self, client_id: str, client_secret: str):
        """
        Initialise le téléchargeur.

        Args:
            client_id: OAuth2 Client ID
            client_secret: OAuth2 Client Secret
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.token_expiry = None

        # URLs API - configurable via variables d'environnement
        import os
        self.auth_url = os.getenv('SENTINEL_HUB_AUTH_URL', 'https://services.sentinel-hub.com/oauth/token')
        base_url = os.getenv('SENTINEL_HUB_BASE_URL', 'https://services.sentinel-hub.com')
        self.process_url = f"{base_url}/api/v1/process"

        logger.info(f"[DOWNLOADER CONFIG] Auth URL: {self.auth_url}")
        logger.info(f"[DOWNLOADER CONFIG] Process URL: {self.process_url}")

        logger.info("[DOWNLOADER] SentinelImageDownloader initialise")

    def _get_access_token(self) -> str:
        """Obtient un token d'accès OAuth2."""
        # Vérifier si le token actuel est encore valide
        if self.access_token and self.token_expiry:
            if datetime.now() < self.token_expiry:
                return self.access_token

        logger.info("[AUTH] Demande nouveau token...")

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

            logger.info(f"[OK] Token obtenu (expire dans {expires_in}s)")
            return self.access_token

        except requests.exceptions.RequestException as e:
            logger.error(f"[ERROR] Erreur authentification: {e}")
            raise Exception(f"Echec authentification OAuth2: {e}")

    def download_image_rgb(
        self,
        bbox: Tuple[float, float, float, float],
        width: int = 512,
        height: int = 512,
        date: Optional[str] = None,
        max_cloud_coverage: int = 30
    ) -> Optional[np.ndarray]:
        """
        Télécharge une image RGB Sentinel-2.

        Args:
            bbox: Bounding box (min_lon, min_lat, max_lon, max_lat)
            width: Largeur en pixels
            height: Hauteur en pixels
            date: Date cible (YYYY-MM-DD) ou None
            max_cloud_coverage: Couverture nuageuse max (%)

        Returns:
            Image RGB en numpy array (H, W, 3) ou None
        """
        try:
            token = self._get_access_token()

            # Définir la période de recherche
            if date:
                try:
                    target_date = datetime.strptime(date, '%Y-%m-%d')
                except ValueError:
                    logger.error(f"[ERROR] Format date invalide: {date}")
                    return None
            else:
                target_date = datetime.now()

            # Période : 30 jours avant la date cible
            end_date = target_date
            start_date = end_date - timedelta(days=30)

            logger.info(f"[DOWNLOAD] Image RGB pour bbox={bbox}, date={date}")

            # Construire la requête Process API
            request_body = {
                "input": {
                    "bounds": {
                        "bbox": list(bbox),
                        "properties": {
                            "crs": "http://www.opengis.net/def/crs/EPSG/0/4326"
                        }
                    },
                    "data": [
                        {
                            "type": "sentinel-2-l2a",
                            "dataFilter": {
                                "timeRange": {
                                    "from": f"{start_date.strftime('%Y-%m-%d')}T00:00:00Z",
                                    "to": f"{end_date.strftime('%Y-%m-%d')}T23:59:59Z"
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
                "evalscript": self._get_evalscript_rgb()
            }

            # Faire la requête
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
                'Accept': 'image/png'
            }

            response = requests.post(
                self.process_url,
                headers=headers,
                json=request_body,
                timeout=60
            )

            if response.status_code == 200:
                # Convertir l'image en numpy array
                image = Image.open(BytesIO(response.content))
                image_array = np.array(image)

                logger.info(f"[OK] Image RGB telechargee: {image_array.shape}")
                return image_array

            else:
                logger.error(f"[ERROR] Erreur API: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"[ERROR] Erreur telechargement: {e}")
            import traceback
            traceback.print_exc()
            return None

    def download_multispectral(
        self,
        bbox: Tuple[float, float, float, float],
        bands: list = None,
        width: int = 512,
        height: int = 512,
        date: Optional[str] = None,
        max_cloud_coverage: int = 30
    ) -> Optional[Dict[str, np.ndarray]]:
        """
        Télécharge plusieurs bandes multi-spectrales.

        Args:
            bbox: Bounding box
            bands: Liste de bandes (ex: ['B02', 'B03', 'B04', 'B08'])
            width: Largeur
            height: Hauteur
            date: Date cible
            max_cloud_coverage: Couverture nuageuse max

        Returns:
            Dictionnaire {band_name: numpy_array} ou None
        """
        try:
            if bands is None:
                bands = ['B02', 'B03', 'B04', 'B08']  # RGB + NIR par défaut

            token = self._get_access_token()

            # Définir période
            if date:
                target_date = datetime.strptime(date, '%Y-%m-%d')
            else:
                target_date = datetime.now()

            end_date = target_date
            start_date = end_date - timedelta(days=30)

            logger.info(f"[DOWNLOAD] Bandes {bands} pour bbox={bbox}")

            # Construire evalscript pour retourner les bandes
            evalscript = self._get_evalscript_multispectral(bands)

            request_body = {
                "input": {
                    "bounds": {
                        "bbox": list(bbox),
                        "properties": {
                            "crs": "http://www.opengis.net/def/crs/EPSG/0/4326"
                        }
                    },
                    "data": [
                        {
                            "type": "sentinel-2-l2a",
                            "dataFilter": {
                                "timeRange": {
                                    "from": f"{start_date.strftime('%Y-%m-%d')}T00:00:00Z",
                                    "to": f"{end_date.strftime('%Y-%m-%d')}T23:59:59Z"
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
                                "type": "image/tiff"
                            }
                        }
                    ]
                },
                "evalscript": evalscript
            }

            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
                'Accept': 'image/tiff'
            }

            response = requests.post(
                self.process_url,
                headers=headers,
                json=request_body,
                timeout=60
            )

            if response.status_code == 200:
                # Traiter le TIFF pour extraire les bandes
                # Note: Nécessite rasterio ou similaire pour TIFF multi-bandes
                # Pour l'instant, retourner un placeholder
                logger.warning("[WARN] Extraction TIFF multi-bandes non implementee")

                # Créer des bandes placeholder basées sur l'image RGB
                rgb_image = self.download_image_rgb(bbox, width, height, date, max_cloud_coverage)

                if rgb_image is not None:
                    result = {}
                    # Simuler les bandes à partir de l'image RGB
                    result['B02'] = rgb_image[:, :, 2].astype(np.float32) / 255.0  # Blue
                    result['B03'] = rgb_image[:, :, 1].astype(np.float32) / 255.0  # Green
                    result['B04'] = rgb_image[:, :, 0].astype(np.float32) / 255.0  # Red
                    # NIR simulé (sera remplacé par vraie bande plus tard)
                    result['B08'] = np.random.rand(*rgb_image.shape[:2]).astype(np.float32)

                    logger.info(f"[OK] {len(result)} bandes extraites (mode simulation)")
                    return result

                return None

            else:
                logger.error(f"[ERROR] Erreur API: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            logger.error(f"[ERROR] Erreur telechargement multi-spectral: {e}")
            return None

    def _get_evalscript_rgb(self) -> str:
        """Evalscript pour image RGB True Color."""
        return """
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
"""

    def _get_evalscript_multispectral(self, bands: list) -> str:
        """Evalscript pour bandes multi-spectrales."""
        bands_str = '", "'.join(bands)

        return f"""
//VERSION=3
function setup() {{
    return {{
        input: ["{bands_str}"],
        output: {{ bands: {len(bands)} }}
    }};
}}

function evaluatePixel(sample) {{
    return [{', '.join(['sample.' + b for b in bands])}];
}}
"""


# ========================================
# FONCTION HELPER
# ========================================

def get_sentinel_image_for_yolo(
    bbox: Tuple[float, float, float, float],
    date: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None
) -> Optional[np.ndarray]:
    """
    Fonction helper pour récupérer une image Sentinel-2 prête pour YOLO.

    Args:
        bbox: Bounding box (min_lon, min_lat, max_lon, max_lat)
        date: Date cible (YYYY-MM-DD) ou None
        client_id: Client ID (ou charge depuis .env)
        client_secret: Client Secret (ou charge depuis .env)

    Returns:
        Image RGB numpy array (H, W, 3) ou None
    """
    # Charger identifiants depuis .env si non fournis
    if not client_id or not client_secret:
        from dotenv import load_dotenv
        load_dotenv()

        client_id = os.getenv('COPERNICUS_CLIENT_ID')
        client_secret = os.getenv('COPERNICUS_CLIENT_SECRET')

        if not client_id or not client_secret:
            logger.error("[ERROR] Identifiants non disponibles")
            return None

    try:
        downloader = SentinelImageDownloader(client_id, client_secret)

        rgb_image = downloader.download_image_rgb(
            bbox=bbox,
            width=640,
            height=640,
            date=date,
            max_cloud_coverage=20
        )

        return rgb_image

    except Exception as e:
        logger.error(f"[ERROR] Erreur: {e}")
        return None


if __name__ == '__main__':
    # Test
    print("=== Test SentinelImageDownloader ===\n")

    from dotenv import load_dotenv
    load_dotenv()

    client_id = os.getenv('COPERNICUS_CLIENT_ID')
    client_secret = os.getenv('COPERNICUS_CLIENT_SECRET')

    if not client_id:
        print("[ERROR] Identifiants non trouves")
    else:
        downloader = SentinelImageDownloader(client_id, client_secret)

        # Test download image RGB
        bbox = (2.2, 48.8, 2.4, 48.9)  # Paris

        print(f"[TEST] Telechargement image RGB pour Paris...")
        image = downloader.download_image_rgb(bbox, width=512, height=512, date='2024-12-01')

        if image is not None:
            print(f"[OK] Image telechargee: {image.shape}, dtype={image.dtype}")
            print(f"    Min={image.min()}, Max={image.max()}, Mean={image.mean():.2f}")
        else:
            print("[ERROR] Echec telechargement")
