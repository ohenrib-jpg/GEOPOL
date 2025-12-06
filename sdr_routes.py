# Flask/sdr_routes.py
"""
Routes API pour le système SDR RÉEL
"""

from flask import Blueprint, jsonify, request
import logging
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

sdr_bp = Blueprint('sdr', __name__)

def register_sdr_routes(app, db_manager, sdr_service):
    """Enregistre les routes SDR"""
    
    @sdr_bp.route('/api/sdr/scan', methods=['GET', 'POST'])
    async def scan_frequencies():
        """Lance un scan complet des fréquences"""
        try:
            if not sdr_service:
                return jsonify({
                    'success': False,
                    'error': 'Service SDR non disponible. Activez le mode RÉEL.',
                    'real_data': False
                }), 503
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(sdr_service.scan_critical_frequencies())
            loop.close()
            
            return jsonify(results)
            
        except Exception as e:
            logger.error(f"❌ Erreur scan SDR: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @sdr_bp.route('/api/sdr/frequency/<int:frequency>', methods=['GET'])
    async def scan_specific_frequency(frequency):
        """Scan une fréquence spécifique"""
        try:
            if not sdr_service:
                return jsonify({
                    'success': False,
                    'error': 'Service SDR non disponible',
                    'real_data': False
                }), 503
            
            bandwidth = request.args.get('bandwidth', 5, type=int)
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(sdr_service.scan_frequency(frequency, bandwidth))
            loop.close()
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"❌ Erreur scan fréquence {frequency}: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @sdr_bp.route('/api/sdr/servers', methods=['GET'])
    async def get_servers():
        """Liste les serveurs SDR actifs"""
        try:
            if not sdr_service:
                return jsonify({
                    'success': True,
                    'servers': [],
                    'message': 'Service SDR non disponible - Mode simulation',
                    'real_data': False
                })
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            servers = loop.run_until_complete(sdr_service.discover_active_servers())
            loop.close()
            
            return jsonify({
                'success': True,
                'servers': servers,
                'count': len(servers),
                'real_data': True
            })
            
        except Exception as e:
            logger.error(f"❌ Erreur serveurs SDR: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @sdr_bp.route('/api/sdr/status', methods=['GET'])
    def get_status():
        """Statut du service SDR"""
        return jsonify({
            'success': True,
            'service_available': sdr_service is not None,
            'active_servers': len(sdr_service.active_servers) if sdr_service else 0,
            'mode': 'REAL' if sdr_service else 'SIMULATION',
            'timestamp': datetime.utcnow().isoformat()
        })
    
    # Enregistrer le blueprint
    app.register_blueprint(sdr_bp, url_prefix='')
    logger.info("✅ Routes SDR RÉEL enregistrées")