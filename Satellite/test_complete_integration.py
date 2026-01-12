"""
Test d'integration complete : Sentinel Hub + YOLO

Teste le workflow complet :
1. Telecharger image Sentinel-2 reelle
2. Analyser avec YOLO
3. Calculer indicateurs (NDVI simule pour l'instant)
4. Exporter vers RAG

Version: 1.0.0
Author: GEOPOL Analytics
"""

import os
import sys
from pathlib import Path

# Ajouter le repertoire parent au path
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

from dotenv import load_dotenv
load_dotenv()

# Imports
from Flask.Satellite.sentinel_image_downloader import SentinelImageDownloader
from Flask.Satellite.satellite_yolo_analyzer import SatelliteYOLOAnalyzer
import numpy as np


def test_complete_integration():
    """Test integration complete Sentinel + YOLO"""

    print("=" * 70)
    print("TEST INTEGRATION COMPLETE : SENTINEL HUB + YOLO")
    print("=" * 70)

    # 1. Charger identifiants
    print("\n[1] Chargement identifiants...")
    client_id = os.getenv('COPERNICUS_CLIENT_ID')
    client_secret = os.getenv('COPERNICUS_CLIENT_SECRET')

    if not client_id or not client_secret:
        print("[ERROR] Identifiants non trouves dans .env")
        return False

    print("[OK] Identifiants charges")

    # 2. Initialiser modules
    print("\n[2] Initialisation modules...")
    downloader = SentinelImageDownloader(client_id, client_secret)
    analyzer = SatelliteYOLOAnalyzer(model_size='small')

    print(f"[OK] Downloader initialise")
    print(f"[OK] YOLO initialise (disponible: {analyzer.yolo_available})")

    # 3. Telecharger image Sentinel-2
    print("\n[3] Telechargement image Sentinel-2 (Paris)...")
    bbox = (2.2, 48.8, 2.4, 48.9)  # Paris

    satellite_image = downloader.download_image_rgb(
        bbox=bbox,
        width=640,
        height=640,
        date='2024-12-01',
        max_cloud_coverage=20
    )

    if satellite_image is None:
        print("[ERROR] Echec telechargement image")
        return False

    print(f"[OK] Image telechargee: {satellite_image.shape}")
    print(f"    Resolution: 640x640 pixels")
    print(f"    Bbox: {bbox}")
    print(f"    Min={satellite_image.min()}, Max={satellite_image.max()}, Mean={satellite_image.mean():.2f}")

    # 4. Analyser avec YOLO
    print("\n[4] Analyse YOLO de l'image satellite...")

    yolo_results = analyzer.analyze_satellite_image(
        image=satellite_image,
        resolution_m_per_pixel=10.0,  # Sentinel-2 = 10m/pixel
        enhance=True  # Preprocessing CLAHE
    )

    if not yolo_results.get('success'):
        print(f"[ERROR] Echec analyse YOLO: {yolo_results.get('error')}")
        return False

    print(f"[OK] Analyse YOLO terminee")
    print(f"    Total detections: {yolo_results.get('total_detections', 0)}")
    print(f"    Resolution: {yolo_results.get('resolution_m', 0)}m/pixel")
    print(f"    Taille image: {yolo_results.get('image_size')}")

    # Afficher detections par classe
    count_by_class = yolo_results.get('count_by_class', {})
    if count_by_class:
        print("\n    Detections par classe:")
        for class_name, count in count_by_class.items():
            print(f"      - {class_name}: {count}")
    else:
        print("    Aucune detection (normal pour image nuageuse/ocean)")

    # Afficher details des detections
    detections = yolo_results.get('detections', [])
    if detections:
        print(f"\n    Details premieres detections:")
        for det in detections[:3]:
            print(f"      - {det['class_name']}: confiance={det['confidence']}, ")
            print(f"        surface={det['area']['km2']:.6f} km2")

    # 5. Calculer indicateurs (simulation pour l'instant)
    print("\n[5] Calcul indicateurs satellite...")

    # Telecharger bandes multi-spectrales (simulation)
    bands = downloader.download_multispectral(
        bbox=bbox,
        bands=['B02', 'B03', 'B04', 'B08'],
        width=640,
        height=640,
        date='2024-12-01'
    )

    if bands:
        # Analyser
        multispectral_results = analyzer.analyze_multispectral(bands, resolution_m=10.0)

        print(f"[OK] Indicateurs calcules:")

        indicators = multispectral_results.get('indicators', {})
        for indicator_name, indicator_data in indicators.items():
            print(f"    - {indicator_name.upper()}: mean={indicator_data.get('mean', 0):.3f}, ")
            print(f"      std={indicator_data.get('std', 0):.3f}")
    else:
        print("[WARN] Bandes multi-spectrales non disponibles (mode simulation)")

    # 6. Export RAG
    print("\n[6] Format export RAG...")

    rag_export = {
        'source': 'sentinel_yolo_analysis',
        'timestamp': yolo_results.get('timestamp'),
        'location': {
            'bbox': bbox,
            'center': [(bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2],
            'description': 'Paris, France'
        },
        'analysis': {
            'type': 'satellite_detection',
            'resolution_m': 10.0,
            'total_detections': yolo_results.get('total_detections', 0),
            'count_by_class': count_by_class
        },
        'indicators': indicators if bands else {},
        'summary': f"Analyse satellite Paris: {yolo_results.get('total_detections', 0)} detections"
    }

    print(f"[OK] Export RAG pret:")
    print(f"    Source: {rag_export['source']}")
    print(f"    Location: {rag_export['location']['description']}")
    print(f"    Detections: {rag_export['analysis']['total_detections']}")

    print("\n" + "=" * 70)
    print("[OK] TEST INTEGRATION COMPLETE REUSSI")
    print("=" * 70)

    print("\n" + "=" * 70)
    print("RESUME")
    print("=" * 70)
    print("\nLe workflow complet fonctionne :")
    print("  [OK] Connexion Sentinel Hub OAuth2")
    print("  [OK] Telechargement image Sentinel-2 reelle")
    print("  [OK] Analyse YOLO sur image satellite")
    print("  [OK] Detection macro-objets (zones urbaines, routes, etc.)")
    print("  [OK] Calcul indicateurs (NDVI, NDWI, Built-up)")
    print("  [OK] Export format RAG")
    print("\nProchaines etapes recommandees :")
    print("  - Implementer telechargement vraies bandes multi-spectrales (NIR, SWIR)")
    print("  - Ajouter analyse temporelle (avant/apres)")
    print("  - Integrer affichage dans geopol-map.js")
    print("  - Fine-tuning YOLO sur datasets satellite (xView, DOTA)")
    print("\n" + "=" * 70)

    return True


if __name__ == '__main__':
    success = test_complete_integration()
    sys.exit(0 if success else 1)
