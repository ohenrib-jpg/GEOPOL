"""
Routes API pour les indicateurs economiques internationaux
"""
from flask import Blueprint, jsonify, request
import logging

logger = logging.getLogger(__name__)

# Creation du blueprint pour l'API internationale
api_bp = Blueprint('economic_api_international', __name__)

# Variable globale pour stocker le service (sera injectee par le blueprint principal)
international_service = None


def init_service(service):
    """Initialise le service International"""
    global international_service
    international_service = service


@api_bp.route('/international/available-indicators')
def get_available_indicators():
    """
    API: Liste des indicateurs internationaux disponibles pour configuration
    GET /economic/api/international/available-indicators
    """
    try:
        if not international_service:
            return jsonify({
                'success': False,
                'error': 'Service International non initialise'
            }), 500

        indicators = international_service.get_available_indicators()

        return jsonify({
            'success': True,
            'data': indicators,
            'count': len(indicators)
        })

    except Exception as e:
        logger.error(f"[API] Erreur available indicators international: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/international/categories')
def get_categories():
    """
    API: Liste des categories d'indicateurs
    GET /economic/api/international/categories
    """
    try:
        if not international_service:
            return jsonify({
                'success': False,
                'error': 'Service International non initialise'
            }), 500

        categories = international_service.get_categories()

        return jsonify({
            'success': True,
            'data': categories
        })

    except Exception as e:
        logger.error(f"[API] Erreur categories: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/international/category/<category_name>')
def get_indicators_by_category(category_name):
    """
    API: Indicateurs d'une categorie specifique
    GET /economic/api/international/category/<category_name>
    """
    try:
        force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'

        if not international_service:
            return jsonify({
                'success': False,
                'error': 'Service International non initialise'
            }), 500

        indicators_config = international_service.get_indicators_by_category(category_name)

        if not indicators_config:
            return jsonify({
                'success': False,
                'error': f'Categorie {category_name} non trouvee'
            }), 404

        # Recuperer les donnees pour chaque indicateur
        indicators_data = []
        for config in indicators_config:
            data = international_service.get_indicator_by_id(config['id'], force_refresh)
            if data:
                indicators_data.append(data)

        return jsonify({
            'success': True,
            'category': category_name,
            'data': indicators_data,
            'count': len(indicators_data)
        })

    except Exception as e:
        logger.error(f"[API] Erreur category {category_name}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/international/indicator/<indicator_id>')
def get_indicator_by_id(indicator_id):
    """
    API: Recupere un indicateur par son ID
    GET /economic/api/international/indicator/<indicator_id>
    """
    try:
        force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'

        if not international_service:
            return jsonify({
                'success': False,
                'error': 'Service International non initialise'
            }), 500

        data = international_service.get_indicator_by_id(indicator_id, force_refresh=force_refresh)

        if data:
            return jsonify({
                'success': True,
                'data': data
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Indicateur {indicator_id} non trouve'
            }), 404

    except Exception as e:
        logger.error(f"[API] Erreur indicator {indicator_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/international/selected-indicators', methods=['GET', 'POST'])
def get_selected_indicators():
    """
    API: Recupere les indicateurs selectionnes pour les widgets
    GET /economic/api/international/selected-indicators?ids=vix,dxy,brent
    POST /economic/api/international/selected-indicators {ids: ['vix', 'dxy', 'brent']}
    """
    try:
        force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'

        if not international_service:
            return jsonify({
                'success': False,
                'error': 'Service International non initialise'
            }), 500

        # Recuperer les IDs soit depuis query params soit depuis body
        if request.method == 'POST':
            data = request.get_json() or {}
            indicator_ids = data.get('ids', [])
        else:
            ids_param = request.args.get('ids', '')
            indicator_ids = [i.strip() for i in ids_param.split(',') if i.strip()]

        # Par defaut, retourner les indicateurs par defaut
        if not indicator_ids:
            indicator_ids = international_service.default_widgets

        indicators = international_service.get_selected_indicators(indicator_ids, force_refresh=force_refresh)

        return jsonify({
            'success': True,
            'data': indicators,
            'count': len(indicators),
            'requested': indicator_ids
        })

    except Exception as e:
        logger.error(f"[API] Erreur selected indicators: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/international/dashboard-summary')
def get_dashboard_summary():
    """
    API: Resume rapide pour le bandeau d'alerte
    GET /economic/api/international/dashboard-summary
    """
    try:
        force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'

        if not international_service:
            return jsonify({
                'success': False,
                'error': 'Service International non initialise'
            }), 500

        summary = international_service.get_dashboard_summary(force_refresh=force_refresh)

        return jsonify({
            'success': True,
            'data': summary
        })

    except Exception as e:
        logger.error(f"[API] Erreur dashboard summary: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/international/historical/<indicator_id>')
def get_historical_data(indicator_id):
    """
    API: Donnees historiques d'un indicateur pour le graphique
    GET /economic/api/international/historical/<indicator_id>?period=1m

    Periodes disponibles:
    - 1d: 1 jour
    - 7d: 7 jours
    - 1m: 1 mois
    - 3m: 3 mois
    - 6m: 6 mois
    - 1y: 1 an
    """
    try:
        period = request.args.get('period', '1m')

        # Valider la periode
        valid_periods = ['1d', '7d', '1m', '3m', '6m', '1y']
        if period not in valid_periods:
            return jsonify({
                'success': False,
                'error': f'Periode invalide. Valeurs acceptees: {", ".join(valid_periods)}'
            }), 400

        if not international_service:
            return jsonify({
                'success': False,
                'error': 'Service International non initialise'
            }), 500

        data = international_service.get_historical_data(indicator_id, period=period)

        return jsonify(data)

    except Exception as e:
        logger.error(f"[API] Erreur historical {indicator_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/international/all')
def get_all_indicators():
    """
    API: Recupere tous les indicateurs groupes par categorie
    GET /economic/api/international/all
    """
    try:
        force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'

        if not international_service:
            return jsonify({
                'success': False,
                'error': 'Service International non initialise'
            }), 500

        all_data = international_service.get_all_indicators(force_refresh=force_refresh)

        # Compter le total
        total = sum(len(indicators) for indicators in all_data.values())

        return jsonify({
            'success': True,
            'data': all_data,
            'categories': list(all_data.keys()),
            'total': total
        })

    except Exception as e:
        logger.error(f"[API] Erreur all indicators: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/international/clear-cache', methods=['POST'])
def clear_international_cache():
    """
    API: Vider le cache des indicateurs internationaux
    POST /economic/api/international/clear-cache
    POST /economic/api/international/clear-cache?key=intl_vix
    """
    try:
        if not international_service:
            return jsonify({
                'success': False,
                'error': 'Service International non initialise'
            }), 500

        cache_key = request.args.get('key', None)

        if cache_key:
            # Vider une entree specifique
            international_service.invalidate_cache(cache_key)
            return jsonify({
                'success': True,
                'message': f'Cache {cache_key} invalide'
            })
        else:
            # Vider tous les caches internationaux
            # Construire la liste des cles de cache
            cache_keys = []
            for indicators in international_service.indicators_config.values():
                for ind in indicators:
                    if ind.get('source') == 'yfinance':
                        cache_keys.append(f"intl_{ind['id']}")
                    elif ind.get('source') == 'fred':
                        cache_keys.append(f"intl_fred_{ind['id']}")

            for key in cache_keys:
                international_service.invalidate_cache(key)

            return jsonify({
                'success': True,
                'message': f'{len(cache_keys)} entrees de cache invalidees',
                'count': len(cache_keys)
            })

    except Exception as e:
        logger.error(f"[API] Erreur clear cache: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/international/refresh-all', methods=['POST'])
def refresh_all_international():
    """
    API: Forcer le rafraichissement de tous les indicateurs internationaux
    POST /economic/api/international/refresh-all
    """
    try:
        if not international_service:
            return jsonify({
                'success': False,
                'error': 'Service International non initialise'
            }), 500

        # Forcer le rafraichissement
        all_data = international_service.get_all_indicators(force_refresh=True)

        # Compter le total
        total = sum(len(indicators) for indicators in all_data.values())

        return jsonify({
            'success': True,
            'message': 'Indicateurs rafraichis',
            'total': total
        })

    except Exception as e:
        logger.error(f"[API] Erreur refresh all: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
