"""
Routes API pour les commodites strategiques
"""
from flask import Blueprint, jsonify, request
import logging

logger = logging.getLogger(__name__)

# Creation du blueprint pour l'API commodites
api_bp = Blueprint('economic_api_commodities', __name__)

# Variable globale pour stocker le service
commodity_service = None

def init_service(service):
    """Initialise le service Commodity"""
    global commodity_service
    commodity_service = service

@api_bp.route('/commodities')
def get_all_commodities():
    """
    API: Recupere toutes les commodites strategiques
    GET /economic/api/commodities
    """
    try:
        force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'

        if not commodity_service:
            return jsonify({
                'success': False,
                'error': 'Service Commodity non initialise'
            }), 500

        commodities = commodity_service.get_all_commodities(force_refresh=force_refresh)

        return jsonify({
            'success': True,
            'data': commodities,
            'count': len(commodities),
            'categories': {
                'metaux_precieux': len([c for c in commodities if c.get('category') == 'metaux_precieux']),
                'energie': len([c for c in commodities if c.get('category') == 'energie']),
                'metaux_industriels': len([c for c in commodities if c.get('category') == 'metaux_industriels']),
                'etf_strategique': len([c for c in commodities if c.get('category') == 'etf_strategique'])
            }
        })

    except Exception as e:
        logger.error(f"[API] Erreur commodites: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/commodities/precious-metals')
def get_precious_metals():
    """
    API: Recupere les metaux precieux
    GET /economic/api/commodities/precious-metals
    """
    try:
        force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'

        if not commodity_service:
            return jsonify({'success': False, 'error': 'Service non initialise'}), 500

        metals = commodity_service.get_precious_metals(force_refresh=force_refresh)

        return jsonify({
            'success': True,
            'data': metals,
            'count': len(metals)
        })

    except Exception as e:
        logger.error(f"[API] Erreur metaux precieux: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/commodities/energy')
def get_energy_commodities():
    """
    API: Recupere les commodites energetiques
    GET /economic/api/commodities/energy
    """
    try:
        force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'

        if not commodity_service:
            return jsonify({'success': False, 'error': 'Service non initialise'}), 500

        energy = commodity_service.get_energy_commodities(force_refresh=force_refresh)

        return jsonify({
            'success': True,
            'data': energy,
            'count': len(energy)
        })

    except Exception as e:
        logger.error(f"[API] Erreur energie: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/commodities/agricultural')
def get_agricultural_commodities():
    """
    API: Recupere les commodites agricoles (Alpha Vantage uniquement)
    GET /economic/api/commodities/agricultural
    """
    try:
        force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'

        if not commodity_service:
            return jsonify({'success': False, 'error': 'Service non initialise'}), 500

        agricultural = commodity_service.get_agricultural_commodities(force_refresh=force_refresh)

        return jsonify({
            'success': True,
            'data': agricultural,
            'count': len(agricultural),
            'note': 'Donnees Alpha Vantage - Mise a jour mensuelle'
        })

    except Exception as e:
        logger.error(f"[API] Erreur agricole: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
