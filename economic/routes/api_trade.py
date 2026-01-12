"""
API REST pour les données de balances commerciales (COMTRADE)
"""
from flask import Blueprint, request, jsonify, current_app
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Création du blueprint
api_bp = Blueprint('trade_api', __name__)

# Variable globale pour le service (sera injectée)
trade_service = None

def init_trade_api(service):
    """Initialise l'API avec le service trade"""
    global trade_service
    trade_service = service
    logger.info("[TRADE API] API trade initialisée")

@api_bp.route('/trade/country/<country_code>')
def get_country_trade_balance(country_code):
    """
    API: Balance commerciale d'un pays
    GET /economic/api/trade/country/<country_code>?year=2024
    """
    try:
        year = request.args.get('year', type=int)

        if not trade_service:
            return jsonify({
                'success': False,
                'error': 'Service Trade non initialisé'
            }), 500

        data = trade_service.get_country_trade_balance(country_code.upper(), year)

        if data.get('success'):
            return jsonify(data)
        else:
            return jsonify(data), 400

    except Exception as e:
        logger.error(f"[TRADE API] Erreur country {country_code}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/trade/flows')
def get_trade_flows():
    """
    API: Flux commerciaux entre deux pays
    GET /economic/api/trade/flows?reporter=FR&partner=DE&year=2024
    """
    try:
        reporter = request.args.get('reporter', '')
        partner = request.args.get('partner', '')
        year = request.args.get('year', type=int)

        if not reporter or not partner:
            return jsonify({
                'success': False,
                'error': 'Paramètres reporter et partner requis'
            }), 400

        if not trade_service:
            return jsonify({
                'success': False,
                'error': 'Service Trade non initialisé'
            }), 500

        data = trade_service.get_trade_flows(reporter.upper(), partner.upper(), year)

        if data.get('success'):
            return jsonify(data)
        else:
            return jsonify(data), 400

    except Exception as e:
        logger.error(f"[TRADE API] Erreur flows {reporter}-{partner}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/trade/product/<product_category>')
def get_product_trade(product_category):
    """
    API: Données commerciales par catégorie de produit
    GET /economic/api/trade/product/<product_category>?country=FR&year=2024
    """
    try:
        country = request.args.get('country', '')
        year = request.args.get('year', type=int)

        if not country:
            return jsonify({
                'success': False,
                'error': 'Paramètre country requis'
            }), 400

        if not trade_service:
            return jsonify({
                'success': False,
                'error': 'Service Trade non initialisé'
            }), 500

        data = trade_service.get_product_trade(product_category, country.upper(), year)

        if data.get('success'):
            return jsonify(data)
        else:
            return jsonify(data), 400

    except Exception as e:
        logger.error(f"[TRADE API] Erreur product {product_category}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/trade/all-countries')
def get_all_countries_trade():
    """
    API: Balances commerciales de tous les pays prioritaires
    GET /economic/api/trade/all-countries?year=2024
    """
    try:
        year = request.args.get('year', type=int)

        if not trade_service:
            return jsonify({
                'success': False,
                'error': 'Service Trade non initialisé'
            }), 500

        data = trade_service.get_all_countries_trade(year)

        if data.get('success'):
            return jsonify(data)
        else:
            return jsonify(data), 400

    except Exception as e:
        logger.error(f"[TRADE API] Erreur all-countries: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/trade/alerts')
def get_trade_alerts():
    """
    API: Alertes commerciales (déficits/excédents significatifs)
    GET /economic/api/trade/alerts?threshold=5.0
    """
    try:
        threshold = request.args.get('threshold', type=float, default=5.0)

        if not trade_service:
            return jsonify({
                'success': False,
                'error': 'Service Trade non initialisé'
            }), 500

        data = trade_service.get_trade_alerts(threshold)

        if data.get('success'):
            return jsonify(data)
        else:
            return jsonify(data), 400

    except Exception as e:
        logger.error(f"[TRADE API] Erreur alerts: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/trade/historical/<country_code>')
def get_historical_trade_data(country_code):
    """
    API: Données historiques de balance commerciale
    GET /economic/api/trade/historical/<country_code>?years=10
    """
    try:
        years = request.args.get('years', type=int, default=10)

        if not trade_service:
            return jsonify({
                'success': False,
                'error': 'Service Trade non initialisé'
            }), 500

        data = trade_service.get_historical_trade_data(country_code.upper(), years)

        if data.get('success'):
            return jsonify(data)
        else:
            return jsonify(data), 400

    except Exception as e:
        logger.error(f"[TRADE API] Erreur historical {country_code}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/trade/available-countries')
def get_available_countries():
    """
    API: Liste des pays disponibles pour l'analyse commerciale
    GET /economic/api/trade/available-countries
    """
    try:
        if not trade_service:
            return jsonify({
                'success': False,
                'error': 'Service Trade non initialisé'
            }), 500

        countries = trade_service.PRIORITY_COUNTRIES

        return jsonify({
            'success': True,
            'countries': countries,
            'count': len(countries),
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"[TRADE API] Erreur available-countries: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/trade/available-products')
def get_available_products():
    """
    API: Liste des catégories de produits disponibles
    GET /economic/api/trade/available-products
    """
    try:
        if not trade_service:
            return jsonify({
                'success': False,
                'error': 'Service Trade non initialisé'
            }), 500

        products = [
            {
                'id': category_id,
                'name': config['name'],
                'codes': config['codes']
            }
            for category_id, config in trade_service.PRODUCT_CATEGORIES.items()
        ]

        return jsonify({
            'success': True,
            'products': products,
            'count': len(products),
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"[TRADE API] Erreur available-products: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500