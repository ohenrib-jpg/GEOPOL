# Flask/geopol_data/sdr_routes.py
"""
Routes API pour l'intégration SDR dans GEOPOL
"""

from flask import Blueprint, jsonify, request, current_app
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

logger = logging.getLogger(__name__)

def create_sdr_api_blueprint(db_manager, sdr_analyzer, sdr_service):
    """Crée le blueprint API pour SDR"""
    
    bp = Blueprint('sdr_api', __name__, url_prefix='/api/sdr')
    
    @bp.route('/health', methods=['GET'])
    def get_sdr_health():
        """Récupère la santé SDR globale"""
        try:
            if not sdr_analyzer:
                return jsonify({
                    'success': False,
                    'error': 'Analyzer SDR non initialisé',
                    'timestamp': datetime.utcnow().isoformat()
                }), 503
            
            # Générer les métriques (simulées pour l'exemple)
            scan_data = current_app.config.get('SDR_SCAN_DATA', [])
            metrics = sdr_analyzer.process_scan_data(scan_data)
            
            return jsonify({
                'success': True,
                'metrics': {k: v.to_dict() for k, v in metrics.items()},
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"❌ Erreur health SDR: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @bp.route('/geojson', methods=['GET'])
    def get_sdr_geojson():
        """Récupère le GeoJSON pour Leaflet"""
        try:
            if not sdr_analyzer:
                return jsonify({
                    'type': 'FeatureCollection',
                    'features': [],
                    'timestamp': datetime.utcnow().isoformat()
                })
            
            geojson = sdr_analyzer.get_geojson_overlay()
            geojson['timestamp'] = datetime.utcnow().isoformat()
            
            return jsonify(geojson)
            
        except Exception as e:
            logger.error(f"❌ Erreur GeoJSON SDR: {e}")
            return jsonify({
                'type': 'FeatureCollection',
                'features': [],
                'error': str(e)
            }), 500
    
    @bp.route('/zone/<zone_id>', methods=['GET'])
    def get_zone_metrics(zone_id: str):
        """Récupère les métriques d'une zone spécifique"""
        try:
            hours = request.args.get('hours', 24, type=int)
            
            # Récupérer l'historique
            conn = db_manager.get_connection()
            cur = conn.cursor()
            
            cur.execute("""
                SELECT * FROM sdr_health_metrics
                WHERE zone_id = ? AND timestamp > datetime('now', '-? hours')
                ORDER BY timestamp DESC
            """, (zone_id, hours))
            
            metrics = []
            for row in cur.fetchall():
                metrics.append({
                    'timestamp': row[13],
                    'total_activity': row[3],
                    'frequency_coverage': row[4],
                    'anomaly_score': row[7],
                    'geopolitical_risk': row[10],
                    'communication_health': row[11],
                    'health_status': row[12]
                })
            
            conn.close()
            
            return jsonify({
                'success': True,
                'zone_id': zone_id,
                'metrics': metrics,
                'period_hours': hours,
                'count': len(metrics)
            })
            
        except Exception as e:
            logger.error(f"❌ Erreur métriques zone {zone_id}: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @bp.route('/timeline/<zone_id>', methods=['GET'])
    def get_zone_timeline(zone_id: str):
        """Récupère la timeline d'une zone"""
        try:
            hours = request.args.get('hours', 24, type=int)
            
            from .overlays.sdr_overlay import SDRTimeline
            timeline = SDRTimeline(db_manager)
            data = timeline.get_zone_timeline(zone_id, hours)
            
            return jsonify({
                'success': 'error' not in data,
                'data': data,
                'zone_id': zone_id
            })
            
        except Exception as e:
            logger.error(f"❌ Erreur timeline {zone_id}: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @bp.route('/compare', methods=['GET'])
    def compare_zones():
        """Compare deux zones"""
        try:
            zone1 = request.args.get('zone1', 'NATO')
            zone2 = request.args.get('zone2', 'BRICS')
            hours = request.args.get('hours', 24, type=int)
            
            from .overlays.sdr_overlay import SDRTimeline
            timeline = SDRTimeline(db_manager)
            data = timeline.get_comparison_data(zone1, zone2, hours)
            
            return jsonify({
                'success': True,
                'comparison': data,
                'zones': [zone1, zone2]
            })
            
        except Exception as e:
            logger.error(f"❌ Erreur comparaison: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @bp.route('/correlate', methods=['POST'])
    def correlate_with_entities():
        """Corrèle avec les entités spaCy"""
        try:
            data = request.get_json()
            if not data or 'entities' not in data:
                return jsonify({
                    'success': False,
                    'error': 'Données entités manquantes'
                }), 400
            
            if not sdr_analyzer:
                return jsonify({
                    'success': False,
                    'error': 'Analyzer SDR non disponible'
                }), 503
            
            correlations = sdr_analyzer.correlate_with_ner_entities(data['entities'])
            
            return jsonify({
                'success': True,
                'correlations': correlations,
                'entities_provided': {
                    'locations': len(data['entities'].get('locations', [])),
                    'organizations': len(data['entities'].get('organizations', [])),
                    'persons': len(data['entities'].get('persons', []))
                }
            })
            
        except Exception as e:
            logger.error(f"❌ Erreur corrélation: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @bp.route('/scan', methods=['POST'])
    def trigger_scan():
        """Déclenche un scan SDR"""
        try:
            if not sdr_service:
                return jsonify({
                    'success': False,
                    'error': 'Service SDR non disponible',
                    'real_data': False
                }), 503
            
            # Lancer un scan
            import asyncio
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Scanner les fréquences critiques
            scan_results = loop.run_until_complete(sdr_service.scan_critical_frequencies())
            loop.close()
            
            # Traiter les résultats
            processed_scans = []
            for category, results in scan_results.get('results', {}).items():
                for result in results:
                    processed_scans.append({
                        'frequency_khz': result.get('frequency_khz', 0),
                        'power_db': result.get('analysis', {}).get('power_db', -100),
                        'bandwidth_khz': 5,
                        'timestamp': result.get('timestamp', datetime.utcnow().isoformat()),
                        'category': category
                    })
            
            # Mettre à jour les métriques
            if processed_scans and sdr_analyzer:
                metrics = sdr_analyzer.process_scan_data(processed_scans)
                
                return jsonify({
                    'success': True,
                    'scan_results': scan_results,
                    'sdr_metrics': {k: v.to_dict() for k, v in metrics.items()},
                    'real_data': True,
                    'scans_processed': len(processed_scans)
                })
            else:
                return jsonify({
                    'success': True,
                    'scan_results': scan_results,
                    'sdr_metrics': {},
                    'real_data': True,
                    'warning': 'Aucune donnée à traiter'
                })
                
        except Exception as e:
            logger.error(f"❌ Erreur scan SDR: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @bp.route('/anomalies', methods=['GET'])
    def get_recent_anomalies():
        """Récupère les anomalies récentes"""
        try:
            hours = request.args.get('hours', 24, type=int)
            limit = request.args.get('limit', 20, type=int)
            
            conn = db_manager.get_connection()
            cur = conn.cursor()
            
            cur.execute("""
                SELECT * FROM sdr_anomalies
                WHERE timestamp > datetime('now', '-? hours')
                ORDER BY timestamp DESC
                LIMIT ?
            """, (hours, limit))
            
            anomalies = []
            for row in cur.fetchall():
                anomalies.append({
                    'id': row[0],
                    'zone_id': row[1],
                    'type': row[2],
                    'severity': row[3],
                    'description': row[4],
                    'confidence': row[5],
                    'timestamp': row[6]
                })
            
            conn.close()
            
            return jsonify({
                'success': True,
                'anomalies': anomalies,
                'count': len(anomalies),
                'period_hours': hours
            })
            
        except Exception as e:
            logger.error(f"❌ Erreur anomalies: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    return bp