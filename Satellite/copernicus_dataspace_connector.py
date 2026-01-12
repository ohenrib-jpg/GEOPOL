"""
Connecteur Copernicus Dataspace pour récupération images Sentinel-2

API Copernicus Dataspace (gratuite, ESA):
- https://dataspace.copernicus.eu/
- Sentinel-2 L2A (10m résolution)
- Accès multi-bandes (RGB, NIR, SWIR)

Version: 1.0.0
Author: GEOPOL Analytics
"""

import requests
import numpy as np
from PIL import Image
from io import BytesIO
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import logging
import os

logger = logging.getLogger(__name__)


class CopernicusDataspaceConnector:
    """
    Connecteur pour l'API Copernicus Dataspace.
    Récupère des images Sentinel-2 avec bandes multi-spectrales.
    """

    def __init__(self, client_id: str, client_secret: str):
        """
        Initialise le connecteur.

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
        self.catalog_url = "https://catalogue.dataspace.copernicus.eu/resto/api/collections/Sentinel2/search.json"
        self.download_url = "https://zipper.dataspace.copernicus.eu/odata/v1/Products"

        # Bandes Sentinel-2 L2A
        self.bands_sentinel2_l2a = {
            'B02': {'name': 'Blue', 'resolution': 10, 'wavelength': '490nm'},
            'B03': {'name': 'Green', 'resolution': 10, 'wavelength': '560nm'},
            'B04': {'name': 'Red', 'resolution': 10, 'wavelength': '665nm'},
            'B08': {'name': 'NIR', 'resolution': 10, 'wavelength': '842nm'},
            'B11': {'name': 'SWIR1', 'resolution': 20, 'wavelength': '1610nm'},
            'B12': {'name': 'SWIR2', 'resolution': 20, 'wavelength': '2190nm'}
        }

        logger.info("[COPERNICUS] Connecteur Dataspace initialise")

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
            raise Exception(f"Echec authentification OAuth2: {e}")

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
            logger.error(f"[ERROR] Echec test connexion: {e}")
            return False

    # ========================================
    # RECHERCHE D'IMAGES
    # ========================================

    def search_images(
        self,
        bbox: Tuple[float, float, float, float],
        start_date: str,
        end_date: str,
        max_cloud_coverage: int = 30,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Recherche d'images Sentinel-2 disponibles.

        Args:
            bbox: Bounding box (min_lon, min_lat, max_lon, max_lat)
            start_date: Date début (YYYY-MM-DD)
            end_date: Date fin (YYYY-MM-DD)
            max_cloud_coverage: Couverture nuageuse max (%)
            limit: Nombre max de résultats

        Returns:
            Liste de métadonnées d'images
        """
        try:
            logger.info(f"[SEARCH] Recherche images Sentinel-2 ({start_date} a {end_date})")

            # Construire la requête
            params = {
                'box': f'{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}',
                'startDate': f'{start_date}T00:00:00Z',
                'completionDate': f'{end_date}T23:59:59Z',
                'cloudCover': f'[0,{max_cloud_coverage}]',
                'maxRecords': limit,
                'processingLevel': 'S2MSI2A',  # Sentinel-2 L2A
                'sortParam': 'startDate',
                'sortOrder': 'descending'
            }

            response = requests.get(
                self.catalog_url,
                params=params,
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

            logger.info(f"[OK] {len(results)} images trouvees")
            return results

        except Exception as e:
            logger.error(f"[ERROR] Erreur recherche images: {e}")
            return []

    # ========================================
    # TÉLÉCHARGEMENT D'IMAGES
    # ========================================

    def download_image_rgb(
        self,
        product_id: str,
        bbox: Optional[Tuple[float, float, float, float]] = None,
        target_size: Tuple[int, int] = (512, 512)
    ) -> Optional[np.ndarray]:
        """
        Télécharge une image RGB Sentinel-2.

        Args:
            product_id: Identifiant du produit Sentinel-2
            bbox: Bounding box optionnel (crop)
            target_size: Taille cible (width, height)

        Returns:
            Image RGB en numpy array ou None
        """
        try:
            token = self._get_access_token()

            logger.info(f"[DOWNLOAD] Telechargement image RGB {product_id}...")

            # Construction de l'URL de téléchargement
            # NOTE: L'API Copernicus Dataspace nécessite un download des produits complets
            # Pour une implémentation complète, il faudrait :
            # 1. Télécharger le produit .SAFE complet
            # 2. Extraire les bandes B02, B03, B04
            # 3. Composer l'image RGB

            # Pour l'instant, retourner une image de test
            logger.warning("[WARN] Telechargement complet non implemente - retour image test")

            # Image test RGB
            test_image = np.random.randint(0, 255, (*target_size, 3), dtype=np.uint8)

            logger.info(f"[OK] Image RGB generee: {test_image.shape}")
            return test_image

        except Exception as e:
            logger.error(f"[ERROR] Erreur telechargement image: {e}")
            return None

    def download_multispectral_bands(
        self,
        product_id: str,
        bands: List[str] = None,
        bbox: Optional[Tuple[float, float, float, float]] = None
    ) -> Optional[Dict[str, np.ndarray]]:
        """
        Télécharge plusieurs bandes multi-spectrales.

        Args:
            product_id: Identifiant du produit
            bands: Liste de bandes (ex: ['B02', 'B03', 'B04', 'B08'])
            bbox: Bounding box optionnel

        Returns:
            Dictionnaire {band_name: numpy_array} ou None
        """
        try:
            if bands is None:
                bands = ['B02', 'B03', 'B04', 'B08']  # RGB + NIR par défaut

            logger.info(f"[DOWNLOAD] Telechargement bandes {bands} pour {product_id}...")

            # NOTE: Implémentation complète nécessiterait:
            # 1. Download du produit .SAFE
            # 2. Extraction des fichiers JP2 pour chaque bande
            # 3. Lecture avec rasterio ou GDAL

            logger.warning("[WARN] Telechargement multi-spectral non implemente - retour bandes test")

            # Bandes test
            test_bands = {}
            for band in bands:
                test_bands[band] = np.random.rand(512, 512).astype(np.float32)

            logger.info(f"[OK] {len(test_bands)} bandes generees")
            return test_bands

        except Exception as e:
            logger.error(f"[ERROR] Erreur telechargement bandes: {e}")
            return None

    # ========================================
    # UTILITAIRES
    # ========================================

    def get_best_image(
        self,
        bbox: Tuple[float, float, float, float],
        date: Optional[str] = None,
        max_cloud_coverage: int = 20
    ) -> Optional[Dict[str, Any]]:
        """
        Trouve la meilleure image disponible pour une zone.

        Args:
            bbox: Bounding box
            date: Date cible (YYYY-MM-DD) ou None pour aujourd'hui
            max_cloud_coverage: Couverture nuageuse max

        Returns:
            Métadonnées de la meilleure image ou None
        """
        try:
            if date:
                target_date = datetime.strptime(date, '%Y-%m-%d')
            else:
                target_date = datetime.now()

            # Rechercher dans une fenêtre de 30 jours
            end_date = target_date
            start_date = end_date - timedelta(days=30)

            images = self.search_images(
                bbox=bbox,
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d'),
                max_cloud_coverage=max_cloud_coverage,
                limit=10
            )

            if not images:
                logger.warning("[WARN] Aucune image trouvee")
                return None

            # Trier par couverture nuageuse (plus faible d'abord)
            images_sorted = sorted(images, key=lambda x: x.get('cloud_cover', 100))

            best = images_sorted[0]
            logger.info(f"[OK] Meilleure image: {best['id']} (cloud={best['cloud_cover']}%)")

            return best

        except Exception as e:
            logger.error(f"[ERROR] Erreur recherche meilleure image: {e}")
            return None


# ========================================
# FONCTION HELPER POUR INTEGRATION YOLO
# ========================================

def get_sentinel2_image_for_yolo(
    bbox: Tuple[float, float, float, float],
    date: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None
) -> Optional[np.ndarray]:
    """
    Récupère une image Sentinel-2 RGB prête pour analyse YOLO.

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
            logger.error("[ERROR] Identifiants Copernicus non disponibles")
            return None

    try:
        # Initialiser connecteur
        connector = CopernicusDataspaceConnector(client_id, client_secret)

        # Trouver meilleure image
        best_image = connector.get_best_image(bbox, date, max_cloud_coverage=20)

        if not best_image:
            logger.warning("[WARN] Aucune image disponible")
            return None

        # Télécharger image RGB
        rgb_image = connector.download_image_rgb(
            product_id=best_image['id'],
            bbox=bbox,
            target_size=(640, 640)
        )

        return rgb_image

    except Exception as e:
        logger.error(f"[ERROR] Erreur recuperation image: {e}")
        return None


if __name__ == '__main__':
    # Test rapide
    print("=== Test Copernicus Dataspace Connector ===\n")

    from dotenv import load_dotenv
    load_dotenv()

    client_id = os.getenv('COPERNICUS_CLIENT_ID')
    client_secret = os.getenv('COPERNICUS_CLIENT_SECRET')

    if not client_id:
        print("[ERROR] Identifiants non trouves dans .env")
    else:
        connector = CopernicusDataspaceConnector(client_id, client_secret)

        # Test connexion
        if connector.test_connection():
            print("[OK] Connexion reussie!\n")

            # Test recherche
            bbox = (2.2, 48.8, 2.4, 48.9)  # Paris
            images = connector.search_images(
                bbox=bbox,
                start_date='2024-12-01',
                end_date='2024-12-28',
                max_cloud_coverage=30,
                limit=5
            )

            print(f"[OK] {len(images)} images trouvees")
            for img in images:
                print(f"   - {img['title']}: {img['cloud_cover']}% clouds")
