# Flask/sdr_spectrum_routes.py - VERSION CORRIGÉE AVEC RATE LIMITING
"""
Routes API pour le module SDR Spectrum Analyzer
"""

from flask import Blueprint, jsonify, request, current_app
import logging
import time
from datetime import datetime
from functools import wraps

logger = logging.getLogger(__name__)

def create_sdr_spectrum_blueprint(db_manager, sdr_service):
    """Crée le blueprint pour les routes SDR"""
    
    sdr_bp = Blueprint('sdr_spectrum', __name__, url_prefix='/api/sdr')
    
    # Rate limiting simple
    request_timestamps = {}
    
    def rate_limit(max_per_minute=30):
        """Decorator de rate limiting basique"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                client_ip = request.remote_addr
                now = time.time()
                
                # Nettoyer les anciennes requêtes
                if client_ip in request_timestamps:
                    request_timestamps[client_ip] = [
                        ts for ts in request_timestamps[client_ip]
                        if now - ts < 60  # 60 secondes
                    ]
                else:
                    request_timestamps[client_ip] = []
                
                # Vérifier la limite
                if len(request_timestamps[client_ip]) >= max_per_minute:
                    return jsonify({
                        'success': False,
                        'error': 'Rate limit exceeded',
                        'retry_after': 60
                    }), 429
                
                # Ajouter la requête
                request_timestamps[client_ip].append(now)
                
                return f(*args, **kwargs)
            return decorated_function
        return decorator
    
    @sdr_bp.route('/dashboard', methods=['GET'])
    @rate_limit(max_per_minute=10)
    def get_dashboard():
        """Données du dashboard SDR"""
        try:
            if hasattr(sdr_service, 'get_dashboard_data'):
                data = sdr_service.get_dashboard_data()
                return jsonify(data)
            else:
                # Fallback simulation
                return jsonify({
                    'success': True,
                    'stats': {
                        'total_frequencies': 8,
                        'anomalies_count': 0,
                        'active_servers': 0,
                        'total_scans': 0,
                        'real_data_ratio': 0.0
                    },
                    'frequencies': [],
                    'recent_scans': [],
                    'anomalies': [],
                    'real_data': current_app.config.get('REAL_MODE', False),
                    'timestamp': datetime.utcnow().isoformat()
                })
        except Exception as e:
            logger.error(f"❌ Erreur dashboard: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @sdr_bp.route('/scan', methods=['POST'])
    @rate_limit(max_per_minute=5)
    def scan_frequency():
        """Scanne une fréquence spécifique"""
        try:
            data = request.get_json(silent=True) or {}
            frequency = data.get('frequency')
            
            if not frequency or not isinstance(frequency, (int, float)):
                return jsonify({'success': False, 'error': 'Fréquence invalide'}), 400
        
            if frequency <= 0 or frequency > 30000:  # kHz max
                return jsonify({'success': False, 'error': 'Fréquence hors limites (1-30000 kHz)'}), 400

            if not frequency:
                return jsonify({
                    'success': False,
                    'error': 'Fréquence requise',
                    'example': {'frequency': 4625, 'bandwidth': 5}
                }), 400
            
            try:
                frequency = int(frequency)
            except ValueError:
                return jsonify({
                    'success': False,
                    'error': 'Fréquence doit être un nombre'
                }), 400
            
            # Validation des limites
            if frequency <= 0 or frequency > 30000:
                return jsonify({
                    'success': False,
                    'error': 'Fréquence hors limites (1-30000 kHz)'
                }), 400
            
            # Catégorie optionnelle
            category = data.get('category', 'custom')
            bandwidth = data.get('bandwidth', 5)
            
            logger.info(f"🎯 Scan demandé: {frequency} kHz ({category})")
            
            if hasattr(sdr_service, 'scan_frequency'):
                result = sdr_service.scan_frequency(frequency, category)
            else:
                # Mode simulation
                import random
                result = {
                    'success': True,
                    'frequency_khz': frequency,
                    'peak_count': random.randint(1, 20),
                    'power_db': round(-70 + random.random() * 30, 2),
                    'signal_present': True,
                    'anomaly_detected': random.random() > 0.8,
                    'servers_used': 0,
                    'real_data': False,
                    'timestamp': time.time()
                }
            
            return jsonify({
                'success': True,
                'results': result
            })
            
        except Exception as e:
            logger.error(f"❌ Erreur scan: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @sdr_bp.route('/scan-all', methods=['POST'])
    @rate_limit(max_per_minute=2)
    def scan_all_bands():
        """Scanne toutes les bandes géopolitiques"""
        try:
            logger.info("🔍 Scan complet demandé")
            
            if hasattr(sdr_service, 'scan_all_geopolitical_frequencies'):
                results = sdr_service.scan_all_geopolitical_frequencies()
            else:
                # Simulation
                results = {
                    'success': True,
                    'results': {},
                    'stats': {
                        'total_scans': 8,
                        'anomalies_detected': 0,
                        'active_servers': 0,
                        'real_data_ratio': 0.0
                    },
                    'timestamp': time.time(),
                    'real_data': False
                }
            
            return jsonify(results)
        except Exception as e:
            logger.error(f"❌ Erreur scan all: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @sdr_bp.route('/servers', methods=['GET'])
    @rate_limit(max_per_minute=20)
    def get_servers():
        """Liste des serveurs WebSDR actifs"""
        try:
            servers = []
            real_data = False
            
            if hasattr(sdr_service, 'discover_active_servers'):
                servers = sdr_service.discover_active_servers()
                real_data = current_app.config.get('REAL_MODE', False)
            elif hasattr(sdr_service, 'active_servers'):
                servers = sdr_service.active_servers
            
            # Formater pour le frontend
            formatted_servers = []
            for server in servers:
                formatted_servers.append({
                    'name': server.get('name', 'Unknown'),
                    'url': server.get('url', ''),
                    'type': server.get('type', 'unknown'),
                    'location': server.get('location', 'Unknown'),
                    'status': server.get('status', 'unknown'),
                    'last_check': server.get('last_check')
                })
            
            return jsonify({
                'success': True,
                'servers': formatted_servers,
                'count': len(formatted_servers),
                'real_data': real_data
            })
        except Exception as e:
            logger.error(f"❌ Erreur serveurs: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @sdr_bp.route('/test-spectrum', methods=['GET'])
    @rate_limit(max_per_minute=30)
    def test_spectrum():
        """Spectre de test pour Plotly"""
        try:
            if hasattr(sdr_service, 'get_test_spectrum'):
                spectrum = sdr_service.get_test_spectrum()
            else:
                # Génération de fallback
                import numpy as np
                frequencies = np.linspace(0, 30, 1000)
                powers = -90 + 20 * np.random.rand(1000)
                
                # Ajouter quelques pics
                peaks_idx = np.random.choice(1000, 5, replace=False)
                powers[peaks_idx] += 30
                
                spectrum = {
                    'success': True,
                    'frequencies_mhz': frequencies.tolist(),
                    'powers': powers.tolist(),
                    'timestamp': datetime.utcnow().isoformat()
                }
            
            return jsonify(spectrum)
        except Exception as e:
            logger.error(f"❌ Erreur test spectrum: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @sdr_bp.route('/status', methods=['GET'])
    def get_status():
        """Statut du service SDR"""
        try:
            active_servers = 0
            if hasattr(sdr_service, 'active_servers'):
                active_servers = len(sdr_service.active_servers)
            elif hasattr(sdr_service, 'discover_active_servers'):
                servers = sdr_service.discover_active_servers()
                active_servers = len(servers)
            
            return jsonify({
                'success': True,
                'status': 'online',
                'active_servers': active_servers,
                'service': 'SDR Spectrum Analysis',
                'real_mode': current_app.config.get('REAL_MODE', False),
                'endpoints': {
                    'dashboard': '/api/sdr/dashboard',
                    'scan': '/api/sdr/scan',
                    'servers': '/api/sdr/servers',
                    'test_spectrum': '/api/sdr/test-spectrum'
                },
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @sdr_bp.route('/debug-servers', methods=['GET'])
    def debug_servers():
        """Debug des serveurs WebSDR"""
        try:
            servers = []
            
            if hasattr(sdr_service, 'WEBSDR_SERVERS'):
                for server in sdr_service.WEBSDR_SERVERS:
                    status = False
                    if hasattr(sdr_service, 'test_websdr_server'):
                        status = sdr_service.test_websdr_server(server)
                    
                    servers.append({
                        'name': server.get('name', 'Unknown'),
                        'url': server.get('url', ''),
                        'status': 'active' if status else 'inactive',
                        'type': server.get('type', 'unknown'),
                        'location': server.get('location', 'Unknown')
                    })
            elif hasattr(sdr_service, 'active_servers'):
                for server in sdr_service.active_servers:
                    servers.append({
                        'name': server.get('name', 'Unknown'),
                        'url': server.get('url', ''),
                        'status': server.get('status', 'unknown'),
                        'type': server.get('type', 'unknown'),
                        'location': server.get('location', 'Unknown')
                    })
            
            return jsonify({
                'success': True,
                'servers': servers,
                'real_mode': current_app.config.get('REAL_MODE', False),
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @sdr_bp.route('/frequency/<int:freq_khz>', methods=['GET'])
    @rate_limit(max_per_minute=10)
    def get_frequency_data(freq_khz):
        """Données historiques pour une fréquence"""
        try:
            # Validation
            if freq_khz <= 0 or freq_khz > 30000:
                return jsonify({
                    'success': False,
                    'error': 'Fréquence invalide (1-30000 kHz)'
                }), 400
            
            conn = db_manager.get_connection()
            cur = conn.cursor()
            
            # Derniers scans
            cur.execute("""
                SELECT 
                    peak_count, power_db, anomaly_detected, real_data, timestamp
                FROM sdr_spectrum_scans
                WHERE frequency_khz = ?
                ORDER BY timestamp DESC
                LIMIT 50
            """, (freq_khz,))
            
            scans = []
            for row in cur.fetchall():
                scans.append({
                    'peak_count': row[0],
                    'power_db': float(row[1]) if row[1] else -100.0,
                    'anomaly': bool(row[2]),
                    'real_data': bool(row[3]),
                    'timestamp': row[4]
                })
            
            # Statistiques
            cur.execute("""
                SELECT 
                    AVG(peak_count) as avg_peaks,
                    MIN(peak_count) as min_peaks,
                    MAX(peak_count) as max_peaks,
                    AVG(power_db) as avg_power,
                    COUNT(*) as total_scans,
                    SUM(CASE WHEN anomaly_detected = 1 THEN 1 ELSE 0 END) as anomalies
                FROM sdr_spectrum_scans
                WHERE frequency_khz = ?
                AND timestamp > datetime('now', '-7 days')
            """, (freq_khz,))
            
            stats_row = cur.fetchone()
            
            conn.close()
            
            stats = {}
            if stats_row and stats_row[0] is not None:
                stats = {
                    'avg_peaks': float(stats_row[0]) if stats_row[0] else 0,
                    'min_peaks': stats_row[1] if stats_row[1] else 0,
                    'max_peaks': stats_row[2] if stats_row[2] else 0,
                    'avg_power': float(stats_row[3]) if stats_row[3] else -100.0,
                    'total_scans': stats_row[4] if stats_row[4] else 0,
                    'anomalies': stats_row[5] if stats_row[5] else 0
                }
            
            return jsonify({
                'success': True,
                'frequency_khz': freq_khz,
                'scans': scans,
                'stats': stats,
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"❌ Erreur fréquence {freq_khz}: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @sdr_bp.route('/health', methods=['GET'])
    def health_check():
        """Health check du service SDR"""
        try:
            # Tester le service
            test_results = {
                'database': 'ok',
                'service': 'unknown',
                'real_mode': current_app.config.get('REAL_MODE', False)
            }
            
            # Test BDD
            try:
                conn = db_manager.get_connection()
                cur = conn.cursor()
                cur.execute("SELECT 1")
                conn.close()
                test_results['database'] = 'ok'
            except Exception as e:
                test_results['database'] = f'error: {str(e)[:50]}'
            
            # Test service
            if hasattr(sdr_service, 'discover_active_servers'):
                try:
                    servers = sdr_service.discover_active_servers()
                    test_results['service'] = f'ok ({len(servers)} serveurs)'
                    test_results['active_servers'] = len(servers)
                except Exception as e:
                    test_results['service'] = f'error: {str(e)[:50]}'
            
            return jsonify({
                'success': True,
                'status': 'healthy',
                'tests': test_results,
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'status': 'unhealthy',
                'error': str(e)
            }), 500

    @sdr_bp.route('/geojson', methods=['GET'])
    def get_sdr_geojson():
        """Retourne le GeoJSON SDR pour la carte"""
        try:
            # Importer et créer l'analyseur
            from Flask.geopol_data.sdr_analyzer import SDRAnalyzer
            
            analyzer = SDRAnalyzer(db_manager)
            geojson = analyzer.get_geojson_overlay()
            
            return jsonify(geojson)
            
        except ImportError as e:
            logger.error(f"Import SDRAnalyzer failed: {e}")
            return jsonify({
                'type': 'FeatureCollection',
                'features': [],
                'error': 'SDRAnalyzer not available',
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            logger.error(f"GeoJSON error: {e}")
            return jsonify({
                'type': 'FeatureCollection',
                'features': [],
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
    
    @sdr_bp.route('/scan/<int:freq_khz>', methods=['GET'])
    def scan_frequency_api(freq_khz):
        """Scanne une fréquence spécifique"""
        try:
            # Validation
            if freq_khz <= 0 or freq_khz > 30000:
                return jsonify({
                    'success': False,
                    'error': 'Fréquence hors limites (1-30000 kHz)',
                    'frequency_khz': freq_khz
                }), 400
            
            # Scanner
            result = sdr_service.scan_frequency(freq_khz)
            
            # Formater la réponse
            response = {
                'success': True,
                'scan': result,
                'request': {
                    'frequency_khz': freq_khz,
                    'frequency_mhz': freq_khz / 1000.0
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Si c'est une simulation, l'indiquer
            if not result.get('real_data', False):
                response['mode'] = 'simulation'
            
            return jsonify(response)
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e),
                'frequency_khz': freq_khz,
                'timestamp': datetime.utcnow().isoformat()
            }), 500
    
    @sdr_bp.route('/scan', methods=['GET'])
    def scan_default():
        """Scan une fréquence par défaut (6000 kHz = BBC)"""
        return scan_frequency_api(6000)
    
    @sdr_bp.route('/zones', methods=['GET'])
    def get_sdr_zones():
        """Liste des zones SDR surveillées"""
        try:
            from Flask.geopol_data.sdr_analyzer import SDRAnalyzer
            
            analyzer = SDRAnalyzer(db_manager)
            
            zones = []
            for zone_id, zone_info in analyzer.zones.items():
                zones.append({
                    'id': zone_id,
                    'name': zone_info.get('name', zone_id),
                    'center': zone_info.get('center', [0, 0]),
                    'description': f'Zone de surveillance {zone_info.get("name", zone_id)}'
                })
            
            return jsonify({
                'success': True,
                'zones': zones,
                'count': len(zones),
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e),
                'zones': [],
                'timestamp': datetime.utcnow().isoformat()
            })
    
    @sdr_bp.route('/analyze', methods=['POST'])
    def analyze_sdr_data():
        """Analyse des données SDR (pour intégration future)"""
        try:
            data = request.get_json() or {}
            scan_data = data.get('scans', [])
            
            from Flask.geopol_data.sdr_analyzer import SDRAnalyzer
            analyzer = SDRAnalyzer(db_manager)
            
            metrics = analyzer.process_scan_data(scan_data)
            
            return jsonify({
                'success': True,
                'metrics': metrics,
                'scans_processed': len(scan_data),
                'zones_analyzed': len(metrics),
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }), 500
    
    return sdr_bp
    
    return sdr_bp