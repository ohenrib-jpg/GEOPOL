# Flask/geopol_data/alerts_routes.py
"""
Routes pour le système d'alertes géopolitiques
"""

from flask import Blueprint, jsonify, request
from .alerts import GeopolAlert, GeopolAlertsService
import logging

logger = logging.getLogger(__name__)

def create_alerts_blueprint(db_manager, data_service, alerts_service) -> Blueprint:
    bp = Blueprint('geopol_alerts', __name__, url_prefix='/api/geopol/alerts')

    @bp.route('', methods=['GET'])
    def get_alerts():
        """Récupère toutes les alertes"""
        try:
            alerts = alerts_service.get_all_alerts()
            return jsonify({
                'success': True,
                'alerts': [alert.to_dict() for alert in alerts]
            })
        except Exception as e:
            logger.error(f"Erreur get_alerts: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @bp.route('', methods=['POST'])
    def create_alert():
        """Crée une nouvelle alerte"""
        try:
            data = request.get_json()
            alert = GeopolAlert(
                name=data['name'],
                description=data.get('description', ''),
                country_code=data['country_code'].upper(),
                indicator=data['indicator'],
                condition=data['condition'],
                threshold=float(data['threshold']),
                active=data.get('active', True)
            )
            alert_id = alerts_service.create_alert(alert)
            return jsonify({'success': True, 'id': alert_id})
        except Exception as e:
            logger.error(f"Erreur create_alert: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @bp.route('/<int:alert_id>', methods=['PUT'])
    def update_alert(alert_id):
        """Met à jour une alerte"""
        try:
            data = request.get_json()
            alert = GeopolAlert(
                id=alert_id,
                name=data['name'],
                description=data.get('description', ''),
                country_code=data['country_code'].upper(),
                indicator=data['indicator'],
                condition=data['condition'],
                threshold=float(data['threshold']),
                active=data.get('active', True)
            )
            success = alerts_service.update_alert(alert_id, alert)
            if success:
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error': 'Alerte non trouvée'}), 404
        except Exception as e:
            logger.error(f"Erreur update_alert: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @bp.route('/<int:alert_id>', methods=['DELETE'])
    def delete_alert(alert_id):
        """Supprime une alerte"""
        try:
            success = alerts_service.delete_alert(alert_id)
            if success:
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error': 'Alerte non trouvée'}), 404
        except Exception as e:
            logger.error(f"Erreur delete_alert: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @bp.route('/<int:alert_id>/toggle', methods=['POST'])
    def toggle_alert(alert_id):
        """Active/désactive une alerte"""
        try:
            data = request.get_json()
            active = data.get('active', True)
            success = alerts_service.toggle_alert(alert_id, active)
            if success:
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error': 'Alerte non trouvée'}), 404
        except Exception as e:
            logger.error(f"Erreur toggle_alert: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    @bp.route('/triggered')
    def get_triggered_alerts():
        """Récupère les alertes récemment déclenchées"""
        try:
            hours = int(request.args.get('hours', 24))
            triggered = alerts_service.get_recently_triggered(hours)
            return jsonify({
                'success': True,
                'alerts': triggered,
                'timeframe_hours': hours
            })
        except Exception as e:
            logger.error(f"Erreur get_triggered_alerts: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

    return bp
