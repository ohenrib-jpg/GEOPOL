"""
Routes API pour la surveillance personnalisee (watchlist)
"""
from flask import Blueprint, jsonify, request
import logging

logger = logging.getLogger(__name__)

# Creation du blueprint pour l'API watchlist
api_bp = Blueprint('economic_api_watchlist', __name__)

# Variable globale pour stocker le service
watchlist_service = None

def init_service(service):
    """Initialise le service Watchlist"""
    global watchlist_service
    watchlist_service = service

@api_bp.route('/watchlist', methods=['GET'])
def get_watchlist():
    """
    API: Recupere la watchlist
    GET /economic/api/watchlist?type=index|etf&with_prices=true
    """
    try:
        if not watchlist_service:
            return jsonify({
                'success': False,
                'error': 'Service Watchlist non initialise'
            }), 500

        watchlist_type = request.args.get('type')  # index, etf, ou None pour tous
        with_prices = request.args.get('with_prices', 'true').lower() == 'true'
        force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'

        if with_prices:
            watchlist = watchlist_service.get_watchlist_with_prices(
                watchlist_type=watchlist_type,
                force_refresh=force_refresh
            )
        else:
            watchlist = watchlist_service.get_watchlist(watchlist_type=watchlist_type)

        return jsonify({
            'success': True,
            'data': watchlist,
            'count': len(watchlist)
        })

    except Exception as e:
        logger.error(f"[API] Erreur get watchlist: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/watchlist', methods=['POST'])
def add_to_watchlist():
    """
    API: Ajoute un element a la watchlist
    POST /economic/api/watchlist
    Body: {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "watchlist_type": "etf",
        "data_source": "yfinance"
    }
    """
    try:
        if not watchlist_service:
            return jsonify({'success': False, 'error': 'Service non initialise'}), 500

        data = request.get_json()

        if not data:
            return jsonify({'success': False, 'error': 'Donnees manquantes'}), 400

        symbol = data.get('symbol')
        name = data.get('name')
        watchlist_type = data.get('watchlist_type')
        data_source = data.get('data_source', 'yfinance')

        if not all([symbol, name, watchlist_type]):
            return jsonify({
                'success': False,
                'error': 'Parametres manquants: symbol, name, watchlist_type requis'
            }), 400

        result = watchlist_service.add_to_watchlist(
            symbol=symbol,
            name=name,
            watchlist_type=watchlist_type,
            data_source=data_source
        )

        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code

    except Exception as e:
        logger.error(f"[API] Erreur add watchlist: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/watchlist/<int:item_id>', methods=['DELETE'])
def remove_from_watchlist(item_id):
    """
    API: Retire un element de la watchlist
    DELETE /economic/api/watchlist/<item_id>
    """
    try:
        if not watchlist_service:
            return jsonify({'success': False, 'error': 'Service non initialise'}), 500

        result = watchlist_service.remove_from_watchlist(item_id)

        status_code = 200 if result['success'] else 404
        return jsonify(result), status_code

    except Exception as e:
        logger.error(f"[API] Erreur delete watchlist: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/watchlist/order', methods=['PUT'])
def update_watchlist_order():
    """
    API: Met a jour l'ordre d'affichage
    PUT /economic/api/watchlist/order
    Body: [
        {"id": 1, "order": 0},
        {"id": 2, "order": 1}
    ]
    """
    try:
        if not watchlist_service:
            return jsonify({'success': False, 'error': 'Service non initialise'}), 500

        data = request.get_json()

        if not data or not isinstance(data, list):
            return jsonify({'success': False, 'error': 'Format invalide'}), 400

        result = watchlist_service.update_display_order(data)

        return jsonify(result)

    except Exception as e:
        logger.error(f"[API] Erreur update order: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/watchlist/stats', methods=['GET'])
def get_watchlist_stats():
    """
    API: Recupere les statistiques de la watchlist
    GET /economic/api/watchlist/stats
    """
    try:
        if not watchlist_service:
            return jsonify({'success': False, 'error': 'Service non initialise'}), 500

        stats = watchlist_service.get_watchlist_stats()

        return jsonify({
            'success': True,
            'data': stats
        })

    except Exception as e:
        logger.error(f"[API] Erreur stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
