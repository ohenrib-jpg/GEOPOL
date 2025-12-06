# Flask/alerts_routes.py
"""
Routes pour le système d'alertes
"""

from flask import Blueprint, jsonify, request
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

alerts_bp = Blueprint('alerts', __name__)

def register_alerts_routes(app, db_manager):
    """Enregistre les routes d'alertes"""
    
    @alerts_bp.route('/api/alerts')
    def get_alerts():
        """Retourne toutes les alertes"""
        try:
            # Données simulées pour le moment
            alerts = [
                {
                    "id": 1,
                    "type": "info",
                    "message": "Système RTL-SDR opérationnel",
                    "timestamp": datetime.utcnow().isoformat(),
                    "read": False
                },
                {
                    "id": 2, 
                    "type": "warning",
                    "message": "Activité élevée détectée sur 14300 kHz",
                    "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                    "read": True
                }
            ]
            
            return jsonify({
                "success": True,
                "alerts": alerts,
                "total": len(alerts)
            })
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @alerts_bp.route('/api/alerts/triggered')
    def get_triggered_alerts():
        """Alertes déclenchées récemment"""
        try:
            hours = request.args.get('hours', 24, type=int)
            
            # Données simulées
            triggered_alerts = [
                {
                    "id": 1,
                    "frequency_khz": 14300,
                    "alert_type": "high_activity",
                    "triggered_at": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
                    "severity": "medium",
                    "description": "Activité anormalement élevée"
                }
            ]
            
            return jsonify({
                "success": True,
                "alerts": triggered_alerts,
                "timeframe_hours": hours
            })
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    # Enregistrer le blueprint
    app.register_blueprint(alerts_bp, url_prefix='/alerts')
    logger.info("✅ Routes alertes enregistrées")