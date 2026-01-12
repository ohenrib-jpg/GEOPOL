"""
Analyseur YOLO optimisé pour imagerie satellite
Détection macro-objets : zones urbaines, industrielles, routes, etc.

Version: 1.0.0
Author: GEOPOL Analytics
"""

import numpy as np
import cv2
import os
from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class SatelliteYOLOAnalyzer:
    """
    YOLO optimisé pour l'imagerie satellite.
    Détecte des macro-objets (zones, pas objets individuels).
    """

    def __init__(self, model_size: str = "small"):
        """
        Initialise l'analyseur YOLO.

        Args:
            model_size: 'nano', 'small', 'medium', 'large' (small = bon compromis)
        """
        self.model_size = model_size
        self.model = None
        self.yolo_available = self._init_yolo()

        # Classes pour détection satellite (macro-niveau)
        self.satellite_classes = {
            0: 'urban_area',         # Zone urbaine
            1: 'industrial_zone',    # Zone industrielle
            2: 'road_network',       # Réseau routier
            3: 'agricultural_field', # Champ agricole
            4: 'water_body',         # Plan d'eau
            5: 'forest_area',        # Zone forestière
            6: 'commercial_area',    # Zone commerciale
            7: 'construction_site',  # Chantier
            8: 'port_facility',      # Installation portuaire
            9: 'parking_area'        # Zone de parking
        }

        logger.info(f"[SEARCH] SatelliteYOLOAnalyzer initialisé (model={model_size}, available={self.yolo_available})")

    def _init_yolo(self) -> bool:
        """Initialise YOLOv8 si disponible."""
        try:
            from ultralytics import YOLO

            # Charger modèle selon taille
            model_files = {
                'nano': 'yolov8n.pt',
                'small': 'yolov8s.pt',
                'medium': 'yolov8m.pt',
                'large': 'yolov8l.pt'
            }

            model_file_name = model_files.get(self.model_size, 'yolov8s.pt')
            # Essayer plusieurs chemins possibles
            possible_paths = [
                model_file_name,  # Chemin relatif depuis le répertoire de travail
                os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', model_file_name),  # Racine du projet
                os.path.join(os.getcwd(), model_file_name)  # Répertoire de travail actuel
            ]

            model_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    model_path = path
                    break

            if model_path is None:
                logger.warning(f"[WARN] Fichier modèle {model_file_name} non trouvé. Utilisation du chemin par défaut.")
                model_path = model_file_name

            self.model = YOLO(model_path)

            # Optimisations pour satellite
            self.model.overrides['conf'] = 0.25      # Seuil confiance
            self.model.overrides['iou'] = 0.45       # IOU
            self.model.overrides['imgsz'] = 1280     # Taille image
            self.model.overrides['augment'] = True   # Augmentation

            logger.info(f"[OK] YOLO {model_file} chargé")
            return True

        except ImportError:
            logger.warning("[WARN] ultralytics non installé - YOLO désactivé (pip install ultralytics)")
            return False
        except Exception as e:
            logger.error(f"[ERROR] Erreur chargement YOLO: {e}")
            return False

    def analyze_satellite_image(self,
                               image: np.ndarray,
                               resolution_m_per_pixel: float = 10.0,
                               enhance: bool = True) -> Dict[str, Any]:
        """
        Analyse une image satellite avec YOLO.

        Args:
            image: Image satellite (RGB ou multi-bande)
            resolution_m_per_pixel: Résolution en mètres/pixel (Sentinel-2 = 10m)
            enhance: Appliquer prétraitement

        Returns:
            Résultats d'analyse avec détections et statistiques
        """

        if not self.yolo_available:
            return self._fallback_analysis(image, resolution_m_per_pixel)

        # Prétraitement
        if enhance:
            processed = self._preprocess_satellite(image)
        else:
            processed = image

        # Détection YOLO
        try:
            results = self.model(processed, verbose=False)
            detections = self._parse_yolo_results(results[0], resolution_m_per_pixel)

            return {
                'success': True,
                'detections': detections,
                'count_by_class': self._count_by_class(detections),
                'total_detections': len(detections),
                'resolution_m': resolution_m_per_pixel,
                'image_size': image.shape[:2],
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"[ERROR] Erreur analyse YOLO: {e}")
            return {'success': False, 'error': str(e)}

    def _preprocess_satellite(self, image: np.ndarray) -> np.ndarray:
        """
        Prétraitement optimisé pour imagerie satellite.
        Applique CLAHE pour améliorer le contraste.
        """

        # Convertir en RGB si nécessaire
        if len(image.shape) == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)

        # CLAHE pour améliorer contraste
        try:
            lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
            l, a, b = cv2.split(lab)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            lab = cv2.merge([l, a, b])
            enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
            return enhanced
        except:
            return image

    def _parse_yolo_results(self,
                           results,
                           resolution_m: float) -> List[Dict[str, Any]]:
        """Parse résultats YOLO en format structuré."""

        detections = []

        if not hasattr(results, 'boxes'):
            return detections

        boxes = results.boxes

        for i in range(len(boxes)):
            box = boxes[i]

            # Coordonnées
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()

            # Classe et confiance
            class_id = int(box.cls[0].cpu().numpy())
            confidence = float(box.conf[0].cpu().numpy())

            # Surface en pixels et m²
            width_px = x2 - x1
            height_px = y2 - y1
            area_px = width_px * height_px
            area_m2 = area_px * (resolution_m ** 2)
            area_km2 = area_m2 / 1_000_000

            detection = {
                'class_id': class_id,
                'class_name': self.satellite_classes.get(class_id, 'unknown'),
                'confidence': round(confidence, 3),
                'bbox': {
                    'x1': int(x1), 'y1': int(y1),
                    'x2': int(x2), 'y2': int(y2),
                    'width_px': int(width_px),
                    'height_px': int(height_px)
                },
                'area': {
                    'pixels': int(area_px),
                    'm2': round(area_m2, 2),
                    'km2': round(area_km2, 6)
                }
            }

            detections.append(detection)

        return detections

    def _count_by_class(self, detections: List[Dict]) -> Dict[str, int]:
        """Compte détections par classe."""
        counts = {}
        for det in detections:
            class_name = det['class_name']
            counts[class_name] = counts.get(class_name, 0) + 1
        return counts

    def _fallback_analysis(self,
                          image: np.ndarray,
                          resolution_m: float) -> Dict[str, Any]:
        """
        Analyse fallback sans YOLO (basique).
        Détecte zones par seuillage de couleur simple.
        """

        logger.info("[WARN] Mode fallback (YOLO indisponible)")

        # Analyse basique par couleur
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY) if len(image.shape) == 3 else image

        # Seuillages simples
        _, urban_mask = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)
        _, water_mask = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY_INV)

        urban_pct = (urban_mask > 0).sum() / urban_mask.size * 100
        water_pct = (water_mask > 0).sum() / water_mask.size * 100

        return {
            'success': True,
            'mode': 'fallback',
            'detections': [],
            'basic_analysis': {
                'urban_coverage_%': round(urban_pct, 2),
                'water_coverage_%': round(water_pct, 2)
            },
            'warning': 'YOLO indisponible - analyse basique seulement'
        }

    def calculate_ndvi(self, nir: np.ndarray, red: np.ndarray) -> np.ndarray:
        """
        Calcule NDVI (Normalized Difference Vegetation Index).
        NDVI = (NIR - Red) / (NIR + Red)

        Valeurs:
        - (-1 à 0) : Eau, sol nu
        - (0 à 0.2) : Végétation clairsemée
        - (0.2 à 0.5) : Végétation modérée
        - (0.5 à 1) : Végétation dense
        """

        nir = nir.astype(float)
        red = red.astype(float)

        # Éviter division par zéro
        denominator = nir + red
        denominator[denominator == 0] = 0.0001

        ndvi = (nir - red) / denominator

        return np.clip(ndvi, -1, 1)

    def calculate_ndwi(self, green: np.ndarray, nir: np.ndarray) -> np.ndarray:
        """
        Calcule NDWI (Normalized Difference Water Index).
        NDWI = (Green - NIR) / (Green + NIR)

        Valeurs positives = eau
        """

        green = green.astype(float)
        nir = nir.astype(float)

        denominator = green + nir
        denominator[denominator == 0] = 0.0001

        ndwi = (green - nir) / denominator

        return np.clip(ndwi, -1, 1)

    def calculate_built_up_index(self,
                                swir: np.ndarray,
                                nir: np.ndarray) -> np.ndarray:
        """
        Calcule Built-up Index (urbanisation).
        BUI = (SWIR - NIR) / (SWIR + NIR)

        Valeurs élevées = zones urbanisées
        """

        swir = swir.astype(float)
        nir = nir.astype(float)

        denominator = swir + nir
        denominator[denominator == 0] = 0.0001

        bui = (swir - nir) / denominator

        return np.clip(bui, -1, 1)

    def analyze_multispectral(self,
                             bands: Dict[str, np.ndarray],
                             resolution_m: float = 10.0) -> Dict[str, Any]:
        """
        Analyse multi-spectrale complète.

        Args:
            bands: Dict avec bandes {'red': array, 'green': array, 'blue': array,
                                    'nir': array, 'swir': array (optionnel)}
            resolution_m: Résolution

        Returns:
            Résultats avec indicateurs calculés
        """

        results = {
            'success': True,
            'indicators': {},
            'statistics': {},
            'timestamp': datetime.now().isoformat()
        }

        # NDVI (si NIR et Red disponibles)
        if 'nir' in bands and 'red' in bands:
            ndvi = self.calculate_ndvi(bands['nir'], bands['red'])
            results['indicators']['ndvi'] = {
                'mean': float(ndvi.mean()),
                'std': float(ndvi.std()),
                'min': float(ndvi.min()),
                'max': float(ndvi.max()),
                'description': 'Indice végétation'
            }

        # NDWI (si Green et NIR disponibles)
        if 'green' in bands and 'nir' in bands:
            ndwi = self.calculate_ndwi(bands['green'], bands['nir'])
            results['indicators']['ndwi'] = {
                'mean': float(ndwi.mean()),
                'std': float(ndwi.std()),
                'description': 'Indice eau'
            }

        # Built-up Index (si SWIR et NIR disponibles)
        if 'swir' in bands and 'nir' in bands:
            bui = self.calculate_built_up_index(bands['swir'], bands['nir'])
            results['indicators']['built_up'] = {
                'mean': float(bui.mean()),
                'std': float(bui.std()),
                'description': 'Indice urbanisation'
            }

        # Créer RGB pour YOLO
        if all(k in bands for k in ['red', 'green', 'blue']):
            rgb = np.stack([bands['red'], bands['green'], bands['blue']], axis=-1)
            rgb = (rgb * 255).astype(np.uint8) if rgb.max() <= 1 else rgb.astype(np.uint8)

            # Analyse YOLO
            yolo_results = self.analyze_satellite_image(rgb, resolution_m)
            results['yolo_detections'] = yolo_results

        return results


# Fonction helper pour tests rapides
def quick_test():
    """Test rapide de l'analyseur."""

    print("=== Test SatelliteYOLOAnalyzer ===\n")

    analyzer = SatelliteYOLOAnalyzer(model_size='small')

    # Image test
    test_image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)

    results = analyzer.analyze_satellite_image(test_image, resolution_m_per_pixel=10.0)

    print(f"Succès: {results.get('success')}")
    print(f"Détections: {results.get('total_detections', 0)}")
    print(f"YOLO disponible: {analyzer.yolo_available}")

    if results.get('count_by_class'):
        print("\nDétections par classe:")
        for cls, count in results['count_by_class'].items():
            print(f"  - {cls}: {count}")


if __name__ == '__main__':
    quick_test()
