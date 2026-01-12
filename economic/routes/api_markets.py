"""
Routes API pour les marches financiers
"""
from flask import Blueprint, jsonify, request
import logging

logger = logging.getLogger(__name__)

# Creation du blueprint pour l'API markets
api_bp = Blueprint('economic_api_markets', __name__)

# Variable globale pour stocker le service
market_service = None

def init_service(service):
    """Initialise le service Market"""
    global market_service
    market_service = service

@api_bp.route('/markets/indices')
def get_all_indices():
    """
    API: Recupere tous les indices internationaux
    GET /economic/api/markets/indices
    """
    try:
        force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'

        if not market_service:
            return jsonify({
                'success': False,
                'error': 'Service Market non initialise'
            }), 500

        indices = market_service.get_all_indices(force_refresh=force_refresh)

        return jsonify({
            'success': True,
            'data': indices,
            'count': len(indices)
        })

    except Exception as e:
        logger.error(f"[API] Erreur indices: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/markets/indices/<region>')
def get_indices_by_region(region):
    """
    API: Recupere les indices d'une region
    GET /economic/api/markets/indices/<region>
    """
    try:
        force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'

        if not market_service:
            return jsonify({'success': False, 'error': 'Service non initialise'}), 500

        indices = market_service.get_indices_by_region(region, force_refresh=force_refresh)

        return jsonify({
            'success': True,
            'region': region,
            'data': indices,
            'count': len(indices)
        })

    except Exception as e:
        logger.error(f"[API] Erreur indices region {region}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/markets/summary')
def get_market_summary():
    """
    API: Recupere un resume des marches mondiaux
    GET /economic/api/markets/summary
    """
    try:
        force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'

        if not market_service:
            return jsonify({'success': False, 'error': 'Service non initialise'}), 500

        summary = market_service.get_market_summary(force_refresh=force_refresh)

        return jsonify({
            'success': True,
            'data': summary
        })

    except Exception as e:
        logger.error(f"[API] Erreur summary: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
