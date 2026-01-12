"""
Routes API pour les alertes économiques
"""
from flask import Blueprint, jsonify, request, current_app
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Création du blueprint pour l'API
api_bp = Blueprint('economic_api_alerts', __name__)

# Variable globale pour stocker le service (sera injectée par le blueprint principal)
alert_service = None

def init_service(service):
    """Initialise le service d'alertes"""
    global alert_service
    alert_service = service

@api_bp.route('/alerts', methods=['GET'])
def get_alerts():
    """
    API: Récupère toutes les alertes
    GET /economic/api/alerts
    """
    try:
        if not alert_service:
            return jsonify({
                'success': False,
                'error': 'Service Alertes non initialisé'
            }), 500

        active_only = request.args.get('active_only', 'false').lower() == 'true'

        if active_only:
            alerts = alert_service.get_active_alerts()
        else:
            alerts = alert_service.get_all_alerts()

        return jsonify({
            'success': True,
            'data': [alert.to_dict() for alert in alerts],
            'count': len(alerts)
        })

    except Exception as e:
        logger.error(f"[API] Erreur récupération alertes: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/alerts/<int:alert_id>', methods=['GET'])
def get_alert(alert_id: int):
    """
    API: Récupère une alerte spécifique
    GET /economic/api/alerts/<id>
    """
    try:
        if not alert_service:
            return jsonify({
                'success': False,
                'error': 'Service Alertes non initialisé'
            }), 500

        alert = alert_service.get_alert(alert_id)
        if not alert:
            return jsonify({
                'success': False,
                'error': f'Alerte {alert_id} non trouvée'
            }), 404

        return jsonify({
            'success': True,
            'data': alert.to_dict()
        })

    except Exception as e:
        logger.error(f"[API] Erreur récupération alerte {alert_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/alerts', methods=['POST'])
def create_alert():
    """
    API: Crée une nouvelle alerte
    POST /economic/api/alerts
    """
    try:
        if not alert_service:
            return jsonify({
                'success': False,
                'error': 'Service Alertes non initialisé'
            }), 500

        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Données JSON requises'
            }), 400

        # Validation des champs requis
        required_fields = ['name', 'indicator_id', 'indicator_type', 'condition', 'threshold']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Champ requis manquant: {field}'
                }), 400

        # Création de l'objet alerte
        from ..models.alert import EconomicAlert
        alert = EconomicAlert(
            name=data['name'],
            description=data.get('description', ''),
            indicator_id=data['indicator_id'],
            indicator_type=data['indicator_type'],
            condition=data['condition'],
            threshold=float(data['threshold']),
            threshold_type=data.get('threshold_type', 'absolute'),
            active=data.get('active', True),
            user_id=data.get('user_id'),
            email_notification=data.get('email_notification', True),
            dashboard_notification=data.get('dashboard_notification', True)
        )

        alert_id = alert_service.create_alert(alert)

        return jsonify({
            'success': True,
            'alert_id': alert_id,
            'message': 'Alerte créée avec succès'
        }), 201

    except ValueError as e:
        logger.error(f"[API] Erreur validation données alerte: {e}")
        return jsonify({
            'success': False,
            'error': f'Erreur de validation: {str(e)}'
        }), 400
    except Exception as e:
        logger.error(f"[API] Erreur création alerte: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/alerts/<int:alert_id>', methods=['PUT'])
def update_alert(alert_id: int):
    """
    API: Met à jour une alerte existante
    PUT /economic/api/alerts/<id>
    """
    try:
        if not alert_service:
            return jsonify({
                'success': False,
                'error': 'Service Alertes non initialisé'
            }), 500

        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Données JSON requises'
            }), 400

        # Récupérer l'alerte existante
        existing_alert = alert_service.get_alert(alert_id)
        if not existing_alert:
            return jsonify({
                'success': False,
                'error': f'Alerte {alert_id} non trouvée'
            }), 404

        # Mettre à jour les champs
        for field in ['name', 'description', 'indicator_id', 'indicator_type',
                     'condition', 'threshold', 'threshold_type', 'active',
                     'user_id', 'email_notification', 'dashboard_notification']:
            if field in data:
                setattr(existing_alert, field, data[field])

        # Conversion numérique pour threshold
        if 'threshold' in data:
            existing_alert.threshold = float(data['threshold'])

        success = alert_service.update_alert(alert_id, existing_alert)
        if not success:
            return jsonify({
                'success': False,
                'error': 'Échec mise à jour alerte'
            }), 500

        return jsonify({
            'success': True,
            'message': 'Alerte mise à jour avec succès'
        })

    except ValueError as e:
        logger.error(f"[API] Erreur validation données alerte: {e}")
        return jsonify({
            'success': False,
            'error': f'Erreur de validation: {str(e)}'
        }), 400
    except Exception as e:
        logger.error(f"[API] Erreur mise à jour alerte {alert_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/alerts/<int:alert_id>', methods=['DELETE'])
def delete_alert(alert_id: int):
    """
    API: Supprime une alerte
    DELETE /economic/api/alerts/<id>
    """
    try:
        if not alert_service:
            return jsonify({
                'success': False,
                'error': 'Service Alertes non initialisé'
            }), 500

        success = alert_service.delete_alert(alert_id)
        if not success:
            return jsonify({
                'success': False,
                'error': f'Alerte {alert_id} non trouvée ou erreur suppression'
            }), 404

        return jsonify({
            'success': True,
            'message': 'Alerte supprimée avec succès'
        })

    except Exception as e:
        logger.error(f"[API] Erreur suppression alerte {alert_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/alerts/<int:alert_id>/toggle', methods=['POST'])
def toggle_alert(alert_id: int):
    """
    API: Active/désactive une alerte
    POST /economic/api/alerts/<id>/toggle
    """
    try:
        if not alert_service:
            return jsonify({
                'success': False,
                'error': 'Service Alertes non initialisé'
            }), 500

        data = request.get_json() or {}
        active = data.get('active')

        if active is None:
            return jsonify({
                'success': False,
                'error': 'Paramètre "active" requis (true/false)'
            }), 400

        success = alert_service.toggle_alert(alert_id, active)
        if not success:
            return jsonify({
                'success': False,
                'error': f'Alerte {alert_id} non trouvée'
            }), 404

        status = "activée" if active else "désactivée"
        return jsonify({
            'success': True,
            'message': f'Alerte {status} avec succès'
        })

    except Exception as e:
        logger.error(f"[API] Erreur changement état alerte {alert_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/alerts/triggered', methods=['GET'])
def get_triggered_alerts():
    """
    API: Récupère les alertes récemment déclenchées
    GET /economic/api/alerts/triggered
    """
    try:
        if not alert_service:
            return jsonify({
                'success': False,
                'error': 'Service Alertes non initialisé'
            }), 500

        hours = int(request.args.get('hours', 24))
        triggered = alert_service.get_recent_triggered_alerts(hours)

        return jsonify({
            'success': True,
            'data': [alert.to_dict() for alert in triggered],
            'count': len(triggered)
        })

    except ValueError:
        return jsonify({
            'success': False,
            'error': 'Paramètre "hours" doit être un nombre entier'
        }), 400
    except Exception as e:
        logger.error(f"[API] Erreur récupération alertes déclenchées: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/alerts/evaluate', methods=['POST'])
def evaluate_alert():
    """
    API: Évalue manuellement une alerte (pour tests)
    POST /economic/api/alerts/evaluate
    """
    try:
        if not alert_service:
            return jsonify({
                'success': False,
                'error': 'Service Alertes non initialisé'
            }), 500

        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Données JSON requises'
            }), 400

        # Validation
        required_fields = ['alert_id', 'current_value']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Champ requis manquant: {field}'
                }), 400

        alert_id = data['alert_id']
        current_value = float(data['current_value'])
        previous_value = float(data['previous_value']) if 'previous_value' in data else None

        # Récupérer l'alerte
        alert = alert_service.get_alert(alert_id)
        if not alert:
            return jsonify({
                'success': False,
                'error': f'Alerte {alert_id} non trouvée'
            }), 404

        # Évaluer
        should_trigger = alert_service.evaluate_alert(alert, current_value, previous_value)

        # Déclencher si nécessaire
        triggered_id = None
        if should_trigger and alert.active:
            triggered_id = alert_service.trigger_alert(alert, current_value, previous_value)

        return jsonify({
            'success': True,
            'should_trigger': should_trigger,
            'triggered': triggered_id is not None,
            'triggered_id': triggered_id,
            'alert_active': alert.active
        })

    except ValueError as e:
        logger.error(f"[API] Erreur validation données évaluation: {e}")
        return jsonify({
            'success': False,
            'error': f'Erreur de validation: {str(e)}'
        }), 400
    except Exception as e:
        logger.error(f"[API] Erreur évaluation alerte: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/alerts/stats', methods=['GET'])
def get_alert_stats():
    """
    API: Récupère les statistiques des alertes
    GET /economic/api/alerts/stats
    """
    try:
        if not alert_service:
            return jsonify({
                'success': False,
                'error': 'Service Alertes non initialisé'
            }), 500

        # Récupérer les données
        all_alerts = alert_service.get_all_alerts()
        active_alerts = alert_service.get_active_alerts()
        recent_triggered = alert_service.get_recent_triggered_alerts(hours=24)

        # Calculer les statistiques
        stats = {
            'total_alerts': len(all_alerts),
            'active_alerts': len(active_alerts),
            'inactive_alerts': len(all_alerts) - len(active_alerts),
            'triggered_last_24h': len(recent_triggered),
            'by_indicator_type': {},
            'by_condition': {}
        }

        # Statistiques par type d'indicateur
        for alert in all_alerts:
            indicator_type = alert.indicator_type
            stats['by_indicator_type'][indicator_type] = stats['by_indicator_type'].get(indicator_type, 0) + 1

        # Statistiques par condition
        for alert in all_alerts:
            condition = alert.condition
            stats['by_condition'][condition] = stats['by_condition'].get(condition, 0) + 1

        return jsonify({
            'success': True,
            'stats': stats
        })

    except Exception as e:
        logger.error(f"[API] Erreur récupération statistiques alertes: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500