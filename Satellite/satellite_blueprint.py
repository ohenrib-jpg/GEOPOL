from flask import Blueprint, request, jsonify, current_app, session
from .satellite_manager import SatelliteManager
from datetime import datetime, timedelta

# Création du blueprint
satellite_bp = Blueprint('satellite', __name__, url_prefix='/api/satellite')

# Initialisation du gestionnaire
satellite_manager = SatelliteManager()

@satellite_bp.route('/layers', methods=['GET'])
def get_available_layers():
    """Récupère les couches satellite disponibles."""
    try:
        layers = satellite_manager.get_available_layers()
        return jsonify({
            "status": "success",
            "layers": layers
        })
    except Exception as e:
        current_app.logger.error(f"Erreur récupération couches: {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500

@satellite_bp.route('/dates', methods=['POST'])
def get_available_dates():
    """Récupère les dates disponibles pour une zone donnée."""
    try:
        data = request.get_json()
        bbox = data.get('bbox')
        
        if not bbox:
            return jsonify({"status": "error", "error": "bbox manquante"}), 400
        
        # Pour le mode avancé, on peut spécifier une période
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        dates = satellite_manager.get_available_dates(bbox, start_date, end_date)
        
        return jsonify({
            "status": "success",
            "dates": dates
        })
    except Exception as e:
        current_app.logger.error(f"Erreur récupération dates: {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500

@satellite_bp.route('/layer-url', methods=['POST'])
def get_layer_url():
    """Récupère l'URL d'une couche satellite."""
    try:
        data = request.get_json()
        layer_id = data.get('layer_id')
        date = data.get('date')
        
        if not layer_id:
            return jsonify({"status": "error", "error": "layer_id manquante"}), 400
        
        url = satellite_manager.get_layer_url(layer_id, date)
        
        if not url:
            return jsonify({"status": "error", "error": "Couche non trouvée"}), 404
        
        return jsonify({
            "status": "success",
            "url": url,
            "layer_id": layer_id
        })
    except Exception as e:
        current_app.logger.error(f"Erreur récupération URL couche: {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500

@satellite_bp.route('/metadata', methods=['GET'])
def get_metadata():
    """Récupère les informations de métadonnées."""
    try:
        metadata = satellite_manager.get_metadata_info()
        return jsonify({
            "status": "success",
            "metadata": metadata
        })
    except Exception as e:
        current_app.logger.error(f"Erreur récupération métadonnées: {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500

@satellite_bp.route('/credentials', methods=['POST'])
def set_credentials():
    """Définit les identifiants utilisateur."""
    try:
        data = request.get_json()
        client_id = data.get('client_id')
        client_secret = data.get('client_secret')
        
        if not client_id or not client_secret:
            return jsonify({"status": "error", "error": "Identifiants manquants"}), 400
        
        satellite_manager.set_user_credentials(client_id, client_secret)
        
        return jsonify({
            "status": "success",
            "message": "Identifiants enregistrés"
        })
    except Exception as e:
        current_app.logger.error(f"Erreur définition identifiants: {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500

@satellite_bp.route('/credentials', methods=['DELETE'])
def clear_credentials():
    """Efface les identifiants utilisateur."""
    try:
        satellite_manager.clear_user_credentials()
        
        return jsonify({
            "status": "success",
            "message": "Identifiants effacés"
        })
    except Exception as e:
        current_app.logger.error(f"Erreur effacement identifiants: {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500

@satellite_bp.route('/credentials/status', methods=['GET'])
def get_credentials_status():
    """Récupère l'état des identifiants utilisateur."""
    try:
        status = satellite_manager.get_current_credentials_status()
        return jsonify({
            "status": "success",
            "credentials_status": status
        })
    except Exception as e:
        current_app.logger.error(f"Erreur état identifiants: {str(e)}")
        return jsonify({"status": "error", "error": str(e)}), 500

# Fonction d'initialisation à appeler dans app_factory.py
def init_satellite_blueprint(app):
    """Initialise le blueprint satellite avec l'application."""
    with app.app_context():
        # Réinitialiser le gestionnaire pour s'assurer qu'il utilise la session courante
        global satellite_manager
        satellite_manager = SatelliteManager()
    
    app.register_blueprint(satellite_bp)