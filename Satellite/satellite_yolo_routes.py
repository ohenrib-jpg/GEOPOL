"""
Routes YOLO pour analyse satellite
Endpoints pour détection et analyse d'images satellite

Version: 1.0.0
Author: GEOPOL Analytics
"""

from flask import jsonify, request
from typing import Dict, Any
import logging
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)


def add_yolo_routes(bp):
    """
    Ajoute les routes YOLO au blueprint satellite.

    Args:
        bp: Blueprint Flask
    """

    @bp.route('/api/yolo/analyze', methods=['POST'])
    def yolo_analyze_area():
        """
        Analyse une zone avec YOLO + indicateurs satellite.

        Body:
            {
                "bbox": [min_lon, min_lat, max_lon, max_lat],
                "layers": ["rgb", "ndvi", "ndwi"] (optionnel),
                "resolution_m": 10.0,
                "use_yolo": true,
                "image_url": "https://..." (optionnel - pour test)
            }

        Returns:
            {
                "success": true,
                "yolo_detections": {...},
                "indicators": {...},
                "rag_data": {...}
            }
        """
        try:
            from .satellite_yolo_analyzer import SatelliteYOLOAnalyzer

            data = request.get_json()
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'Body JSON requis',
                    'example': {
                        'bbox': [2.2, 48.8, 2.4, 48.9],
                        'layers': ['rgb', 'ndvi'],
                        'resolution_m': 10.0,
                        'use_yolo': True
                    }
                }), 400

            bbox = data.get('bbox')
            if not bbox or len(bbox) != 4:
                return jsonify({
                    'success': False,
                    'error': 'bbox requis: [min_lon, min_lat, max_lon, max_lat]'
                }), 400

            layers = data.get('layers', ['rgb'])
            resolution_m = data.get('resolution_m', 10.0)
            use_yolo = data.get('use_yolo', True)

            # Initialiser analyseur
            analyzer = SatelliteYOLOAnalyzer(model_size='small')

            # Pour MVP: image test (à remplacer par vraie API Sentinel-2)
            test_image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
            logger.warning("[WARN] Mode test - image aléatoire (TODO: intégrer API Sentinel-2/Copernicus)")

            # Analyse
            results = {
                'success': True,
                'bbox': bbox,
                'resolution_m': resolution_m,
                'timestamp': datetime.now().isoformat(),
                'mode': 'test'
            }

            if use_yolo:
                yolo_results = analyzer.analyze_satellite_image(
                    test_image,
                    resolution_m_per_pixel=resolution_m
                )
                results['yolo_detections'] = yolo_results

            # Indicateurs (TODO: vraies bandes NIR/SWIR)
            if 'ndvi' in layers or 'ndwi' in layers or 'built_up' in layers:
                results['indicators'] = {
                    'message': 'Indicateurs nécessitent bandes multi-spectrales (NIR, SWIR)',
                    'todo': 'Intégrer API Copernicus Sentinel-2 pour bandes réelles',
                    'available_with_real_data': ['ndvi', 'ndwi', 'built_up_index', 'burn_index']
                }

            # Export RAG
            results['rag_data'] = _format_for_rag(results, bbox)

            return jsonify(results)

        except ImportError as e:
            logger.error(f"[ERROR] Import error: {e}")
            return jsonify({
                'success': False,
                'error': 'Module YOLO non disponible',
                'install': 'pip install ultralytics opencv-python numpy'
            }), 500

        except Exception as e:
            logger.error(f"[ERROR] Erreur analyse YOLO: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/api/yolo/status', methods=['GET'])
    def yolo_status():
        """
        Vérifie si YOLO est disponible.

        Returns:
            {
                "success": true,
                "yolo_available": true,
                "model_size": "small",
                "classes": [...]
            }
        """
        try:
            from .satellite_yolo_analyzer import SatelliteYOLOAnalyzer

            analyzer = SatelliteYOLOAnalyzer(model_size='small')

            return jsonify({
                'success': True,
                'yolo_available': analyzer.yolo_available,
                'model_size': analyzer.model_size,
                'classes_count': len(analyzer.satellite_classes),
                'classes': list(analyzer.satellite_classes.values()),
                'description': 'YOLO optimisé pour imagerie satellite (macro-détection)'
            })

        except ImportError:
            return jsonify({
                'success': True,
                'yolo_available': False,
                'error': 'ultralytics non installé',
                'install': 'pip install ultralytics'
            })

        except Exception as e:
            logger.error(f"[ERROR] Erreur status YOLO: {e}")
            return jsonify({
                'success': False,
                'yolo_available': False,
                'error': str(e)
            }), 500

    @bp.route('/api/yolo/indicators/calculate', methods=['POST'])
    def calculate_indicators():
        """
        Calcule indicateurs satellite (NDVI, NDWI, Built-up Index).

        Body:
            {
                "bands": {
                    "red": [...],
                    "green": [...],
                    "blue": [...],
                    "nir": [...],
                    "swir": [...] (optionnel)
                },
                "resolution_m": 10.0
            }

        Returns:
            {
                "success": true,
                "indicators": {
                    "ndvi": {...},
                    "ndwi": {...},
                    "built_up": {...}
                }
            }
        """
        try:
            from .satellite_yolo_analyzer import SatelliteYOLOAnalyzer

            data = request.get_json()
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'Body JSON requis'
                }), 400

            bands = data.get('bands')
            if not bands:
                return jsonify({
                    'success': False,
                    'error': 'bands requis (dict avec red, green, blue, nir, swir)'
                }), 400

            resolution_m = data.get('resolution_m', 10.0)

            # Convertir bandes en numpy arrays
            bands_np = {}
            for band_name, band_data in bands.items():
                bands_np[band_name] = np.array(band_data, dtype=np.float32)

            # Analyser
            analyzer = SatelliteYOLOAnalyzer()
            results = analyzer.analyze_multispectral(bands_np, resolution_m)

            return jsonify(results)

        except Exception as e:
            logger.error(f"[ERROR] Erreur calcul indicateurs: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @bp.route('/api/yolo/compare', methods=['POST'])
    def compare_temporal():
        """
        Compare 2 images satellite (avant/après).

        Body:
            {
                "bbox": [min_lon, min_lat, max_lon, max_lat],
                "date_before": "2024-01-01",
                "date_after": "2024-06-01",
                "analysis_type": "disaster|urban_growth|deforestation"
            }

        Returns:
            {
                "success": true,
                "changes_detected": {...},
                "severity": "low|medium|high",
                "rag_data": {...}
            }
        """
        try:
            data = request.get_json()
            if not data:
                return jsonify({
                    'success': False,
                    'error': 'Body JSON requis'
                }), 400

            bbox = data.get('bbox')
            date_before = data.get('date_before')
            date_after = data.get('date_after')
            analysis_type = data.get('analysis_type', 'general')

            if not all([bbox, date_before, date_after]):
                return jsonify({
                    'success': False,
                    'error': 'bbox, date_before et date_after requis'
                }), 400

            # TODO: Implémenter vraie comparaison temporelle
            # Pour l'instant, retourner structure de base

            results = {
                'success': True,
                'mode': 'placeholder',
                'bbox': bbox,
                'dates': {
                    'before': date_before,
                    'after': date_after
                },
                'analysis_type': analysis_type,
                'changes_detected': {
                    'message': 'Comparaison temporelle à implémenter avec vraies images Sentinel-2',
                    'todo': 'Récupérer images via API Copernicus, calculer différences NDVI/NDWI/Built-up'
                },
                'severity': 'unknown',
                'timestamp': datetime.now().isoformat()
            }

            return jsonify(results)

        except Exception as e:
            logger.error(f"[ERROR] Erreur comparaison temporelle: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    logger.info("[OK] Routes YOLO ajoutées au blueprint Satellite")


def _format_for_rag(results: dict, bbox: list) -> Dict[str, Any]:
    """
    Formate les résultats pour export RAG.

    Args:
        results: Résultats d'analyse
        bbox: Bounding box

    Returns:
        Données structurées pour RAG
    """
    return {
        'source': 'satellite_yolo_analysis',
        'timestamp': results.get('timestamp'),
        'location': {
            'bbox': bbox,
            'center': [
                (bbox[0] + bbox[2]) / 2,
                (bbox[1] + bbox[3]) / 2
            ],
            'area_description': f"Zone: {bbox[0]:.4f},{bbox[1]:.4f} à {bbox[2]:.4f},{bbox[3]:.4f}"
        },
        'analysis': {
            'type': 'satellite_detection',
            'resolution_m': results.get('resolution_m'),
            'mode': results.get('mode', 'production')
        },
        'detections_summary': {
            'total': results.get('yolo_detections', {}).get('total_detections', 0),
            'by_class': results.get('yolo_detections', {}).get('count_by_class', {}),
            'detections': results.get('yolo_detections', {}).get('detections', [])
        },
        'indicators': results.get('indicators', {}),
        'context_for_rag': _generate_rag_context(results, bbox)
    }


def _generate_rag_context(results: dict, bbox: list) -> str:
    """Génère description textuelle pour RAG."""

    detections = results.get('yolo_detections', {})
    total = detections.get('total_detections', 0)
    by_class = detections.get('count_by_class', {})

    if total == 0:
        return f"Satellite analysis of area {bbox} - No significant features detected (test mode)"

    context_parts = [
        f"Satellite analysis of area {bbox}:",
        f"Total detections: {total}"
    ]

    if by_class:
        context_parts.append("Detected features:")
        for cls, count in by_class.items():
            context_parts.append(f"  - {cls}: {count}")

    return " ".join(context_parts)
