"""
Routes API pour la gestion des profils de configuration.

Endpoints:
- GET    /api/geopol/profiles           - Liste tous les profils
- GET    /api/geopol/profiles/<name>    - Récupère un profil spécifique
- POST   /api/geopol/profiles           - Crée un nouveau profil
- PUT    /api/geopol/profiles/<name>    - Met à jour un profil
- DELETE /api/geopol/profiles/<name>    - Supprime un profil
- POST   /api/geopol/profiles/from-state - Crée un profil depuis l'état actuel
"""

from flask import Blueprint, request, jsonify
from typing import Optional
from pathlib import Path
from .config_manager import ConfigManager, ConfigProfile
from .config import BASE_DIR

# Blueprint pour les routes de configuration
config_bp = Blueprint('config', __name__, url_prefix='/api/geopol/profiles')

# Initialiser le gestionnaire de configuration avec un chemin de stockage
PROFILES_STORAGE_PATH = Path(BASE_DIR) / 'profiles'
config_manager = ConfigManager(storage_path=PROFILES_STORAGE_PATH)


@config_bp.route('', methods=['GET'])
def list_profiles():
    """
    Liste tous les profils disponibles (défaut + personnalisés).

    Returns:
        200: Liste des profils
        {
            "success": true,
            "profiles": {
                "default": {
                    "description": "...",
                    "type": "default",
                    "created_at": "...",
                    "updated_at": "..."
                },
                ...
            }
        }
    """
    try:
        profiles = config_manager.list_profiles()
        return jsonify({
            'success': True,
            'profiles': profiles,
            'count': len(profiles)
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@config_bp.route('/<string:name>', methods=['GET'])
def get_profile(name: str):
    """
    Récupère un profil spécifique par son nom.

    Args:
        name: Nom du profil

    Returns:
        200: Profil trouvé
        404: Profil non trouvé
    """
    try:
        profile = config_manager.get_profile(name)

        if profile is None:
            return jsonify({
                'success': False,
                'error': f'Profil "{name}" non trouvé'
            }), 404

        return jsonify({
            'success': True,
            'profile': profile.to_dict()
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@config_bp.route('', methods=['POST'])
def create_profile():
    """
    Crée un nouveau profil personnalisé.

    Body:
        {
            "name": "mon_profil",
            "description": "Description",
            "layers": {...},
            "entities": [...],
            "weather": {...},
            "earthquakes": {...},
            "theme": "light",
            ...
        }

    Returns:
        201: Profil créé
        400: Données invalides
        409: Profil déjà existant
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'Aucune donnée fournie'
            }), 400

        # Vérifier que le nom est fourni
        if 'name' not in data:
            return jsonify({
                'success': False,
                'error': 'Le nom du profil est requis'
            }), 400

        # Vérifier si le profil existe déjà
        existing_profile = config_manager.get_profile(data['name'])
        if existing_profile is not None:
            return jsonify({
                'success': False,
                'error': f'Un profil nommé "{data["name"]}" existe déjà'
            }), 409

        # Créer le profil
        profile = ConfigProfile.from_dict(data)

        # Valider le profil
        is_valid, error_msg = config_manager.validate_profile(profile)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': f'Profil invalide: {error_msg}'
            }), 400

        # Sauvegarder le profil
        success = config_manager.save_profile(profile)

        if not success:
            return jsonify({
                'success': False,
                'error': 'Échec de la sauvegarde du profil'
            }), 500

        return jsonify({
            'success': True,
            'message': f'Profil "{profile.name}" créé avec succès',
            'profile': profile.to_dict()
        }), 201

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@config_bp.route('/<string:name>', methods=['PUT'])
def update_profile(name: str):
    """
    Met à jour un profil existant.

    Args:
        name: Nom du profil à mettre à jour

    Body:
        {
            "description": "Nouvelle description",
            "layers": {...},
            ...
        }

    Returns:
        200: Profil mis à jour
        404: Profil non trouvé
        400: Données invalides
    """
    try:
        # Vérifier que le profil existe
        existing_profile = config_manager.get_profile(name)
        if existing_profile is None:
            return jsonify({
                'success': False,
                'error': f'Profil "{name}" non trouvé'
            }), 404

        # Vérifier qu'on ne modifie pas un profil par défaut
        if name in ConfigManager.DEFAULT_PROFILES:
            return jsonify({
                'success': False,
                'error': 'Les profils par défaut ne peuvent pas être modifiés. Créez un nouveau profil.'
            }), 403

        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Aucune donnée fournie'
            }), 400

        # Mettre à jour les champs fournis
        updated_data = existing_profile.to_dict()
        updated_data.update(data)
        updated_data['name'] = name  # S'assurer que le nom ne change pas

        # Créer le profil mis à jour
        updated_profile = ConfigProfile.from_dict(updated_data)

        # Valider le profil
        is_valid, error_msg = config_manager.validate_profile(updated_profile)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': f'Profil invalide: {error_msg}'
            }), 400

        # Sauvegarder avec overwrite=True
        success = config_manager.save_profile(updated_profile, overwrite=True)

        if not success:
            return jsonify({
                'success': False,
                'error': 'Échec de la mise à jour du profil'
            }), 500

        return jsonify({
            'success': True,
            'message': f'Profil "{name}" mis à jour avec succès',
            'profile': updated_profile.to_dict()
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@config_bp.route('/<string:name>', methods=['DELETE'])
def delete_profile(name: str):
    """
    Supprime un profil personnalisé.

    Args:
        name: Nom du profil à supprimer

    Returns:
        200: Profil supprimé
        403: Tentative de suppression d'un profil par défaut
        404: Profil non trouvé
    """
    try:
        # Vérifier qu'on ne supprime pas un profil par défaut
        if name in ConfigManager.DEFAULT_PROFILES:
            return jsonify({
                'success': False,
                'error': 'Les profils par défaut ne peuvent pas être supprimés'
            }), 403

        # Supprimer le profil
        success = config_manager.delete_profile(name)

        if not success:
            return jsonify({
                'success': False,
                'error': f'Profil "{name}" non trouvé'
            }), 404

        return jsonify({
            'success': True,
            'message': f'Profil "{name}" supprimé avec succès'
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@config_bp.route('/from-state', methods=['POST'])
def create_profile_from_state():
    """
    Crée un nouveau profil basé sur l'état actuel de la carte.

    Body:
        {
            "name": "mon_profil",
            "description": "Description",
            "current_state": {
                "layers": {
                    "geopolitical_entities": {
                        "enabled": true,
                        "opacity": 0.7,
                        ...
                    },
                    ...
                },
                "entities": ["GPE", "ORG"],
                "weather": {...},
                "earthquakes": {...},
                "theme": "dark",
                ...
            }
        }

    Returns:
        201: Profil créé
        400: Données invalides
        409: Profil déjà existant
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'Aucune donnée fournie'
            }), 400

        # Vérifier les champs requis
        required_fields = ['name', 'description', 'current_state']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Champ requis manquant: {field}'
                }), 400

        # Vérifier si le profil existe déjà
        existing_profile = config_manager.get_profile(data['name'])
        if existing_profile is not None:
            return jsonify({
                'success': False,
                'error': f'Un profil nommé "{data["name"]}" existe déjà'
            }), 409

        # Créer le profil depuis l'état actuel
        profile = config_manager.create_profile_from_current_state(
            name=data['name'],
            description=data['description'],
            current_state=data['current_state']
        )

        # Valider le profil
        is_valid, error_msg = config_manager.validate_profile(profile)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': f'Profil invalide: {error_msg}'
            }), 400

        # Sauvegarder le profil
        success = config_manager.save_profile(profile)

        if not success:
            return jsonify({
                'success': False,
                'error': 'Échec de la sauvegarde du profil'
            }), 500

        return jsonify({
            'success': True,
            'message': f'Profil "{profile.name}" créé depuis l\'état actuel',
            'profile': profile.to_dict()
        }), 201

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@config_bp.route('/validate', methods=['POST'])
def validate_profile():
    """
    Valide un profil sans le sauvegarder.

    Body:
        {
            "name": "test",
            "layers": {...},
            ...
        }

    Returns:
        200: Profil valide ou invalide avec détails
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({
                'success': False,
                'error': 'Aucune donnée fournie'
            }), 400

        # Créer le profil
        profile = ConfigProfile.from_dict(data)

        # Valider
        is_valid, error_msg = config_manager.validate_profile(profile)

        return jsonify({
            'success': True,
            'valid': is_valid,
            'error': error_msg,
            'profile': profile.to_dict()
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# Fonction pour enregistrer le blueprint
def register_config_routes(app):
    """Enregistre les routes de configuration dans l'application Flask."""
    app.register_blueprint(config_bp)
