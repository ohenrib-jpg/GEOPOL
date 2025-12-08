# Flask/sdr_spectrum_routes.py - VERSION CORRIGÉE

from flask import Blueprint, jsonify, request, current_app
import logging
import time

logger = logging.getLogger(__name__)

def create_sdr_spectrum_blueprint(db_manager, sdr_service):
    """Crée le blueprint pour les routes SDR"""
    
    sdr_bp = Blueprint('sdr_spectrum', __name__, url_prefix='/api/sdr')
    
    @sdr_bp.route('/dashboard', methods=['GET'])
    def get_dashboard():
        """Données du dashboard SDR"""
        try:
            if hasattr(sdr_service, 'get_dashboard_data'):
                data = sdr_service.get_dashboard_data()
                return jsonify(data)
            else:
                return jsonify({
                    'success': True,
                    'stats': {
                        'total_frequencies': 8,
                        'anomalies_count': 0,
                        'active_servers': 0,
                        'total_scans': 0
                    },
                    'recent_scans': [],
                    'anomalies': [],
                    'real_data': current_app.config.get('REAL_MODE', False)
                })
        except Exception as e:
            logger.error(f"❌ Erreur dashboard: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @sdr_bp.route('/scan', methods=['POST'])
    def scan_frequency():
        """Scanne une fréquence spécifique"""
        try:
            data = request.get_json()
            frequency = data.get('frequency')
            
            if not frequency:
                return jsonify({
                    'success': False,
                    'error': 'Fréquence requise'
                }), 400
            
            if hasattr(sdr_service, 'scan_frequency'):
                result = sdr_service.scan_frequency(frequency, 'custom')
            else:
                # Mode simulation
                import numpy as np
                result = {
                    'success': True,
                    'frequency_khz': frequency,
                    'peak_count': np.random.randint(1, 20),
                    'power_db': round(-70 + np.random.rand() * 30, 2),
                    'signal_present': True,
                    'anomaly_detected': np.random.rand() > 0.8,
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
    def scan_all_bands():
        """Scanne toutes les bandes géopolitiques"""
        try:
            if hasattr(sdr_service, 'scan_all_geopolitical_frequencies'):
                results = sdr_service.scan_all_geopolitical_frequencies()
            else:
                results = {
                    'success': True,
                    'results': {},
                    'stats': {
                        'total_scans': 8,
                        'anomalies_detected': 0,
                        'active_servers': 0
                    },
                    'timestamp': time.time()
                }
            return jsonify(results)
        except Exception as e:
            logger.error(f"❌ Erreur scan all: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @sdr_bp.route('/servers', methods=['GET'])
    def get_servers():
        """Liste des serveurs WebSDR actifs"""
        try:
            if hasattr(sdr_service, 'discover_active_servers'):
                servers = sdr_service.discover_active_servers()
            else:
                servers = []
            return jsonify({
                'success': True,
                'servers': servers,
                'count': len(servers)
            })
        except Exception as e:
            logger.error(f"❌ Erreur serveurs: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @sdr_bp.route('/test-spectrum', methods=['GET'])
    def test_spectrum():
        """Spectre de test pour Plotly"""
        try:
            if hasattr(sdr_service, 'get_test_spectrum'):
                spectrum = sdr_service.get_test_spectrum()
            else:
                import numpy as np
                frequencies = np.linspace(0, 30, 1000)
                powers = -90 + 20 * np.random.rand(1000)
                # Ajouter quelques pics
                peaks_idx = np.random.choice(1000, 5, replace=False)
                powers[peaks_idx] += 30
                
                spectrum = {
                    'success': True,
                    'frequencies_mhz': frequencies.tolist(),
                    'powers': powers.tolist()
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
            return jsonify({
                'success': True,
                'status': 'online',
                'active_servers': len(sdr_service.active_servers) if hasattr(sdr_service, 'active_servers') else 0,
                'service': 'SDR Spectrum Analysis',
                'real_mode': current_app.config.get('REAL_MODE', False)
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
                        'name': server['name'],
                        'url': server['url'],
                        'status': 'active' if status else 'inactive',
                        'type': server.get('type', 'unknown')
                    })
            
            return jsonify({
                'success': True,
                'servers': servers,
                'real_mode': current_app.config.get('REAL_MODE', False)
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    return sdr_bp