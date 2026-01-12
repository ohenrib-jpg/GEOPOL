"""
API REST pour les données cryptomonnaies
"""
from flask import Blueprint, request, jsonify, current_app
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Création du blueprint
api_bp = Blueprint('crypto_api', __name__)

# Variable globale pour le service (sera injectée)
crypto_service = None

def init_crypto_api(service):
    """Initialise l'API avec le service crypto"""
    global crypto_service
    crypto_service = service
    logger.info("[CRYPTO API] API crypto initialisée")

@api_bp.route('/crypto/<crypto_id>')
def get_crypto_data(crypto_id):
    """
    API: Données d'une cryptomonnaie
    GET /economic/api/crypto/<crypto_id>
    """
    try:
        if not crypto_service:
            return jsonify({
                'success': False,
                'error': 'Service Crypto non initialisé'
            }), 500

        data = crypto_service.get_crypto_data(crypto_id.lower())

        if data.get('success'):
            return jsonify(data)
        else:
            return jsonify(data), 400

    except Exception as e:
        logger.error(f"[CRYPTO API] Erreur crypto {crypto_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/crypto')
def get_all_cryptos():
    """
    API: Toutes les cryptomonnaies surveillées
    GET /economic/api/crypto?limit=3
    """
    try:
        limit = request.args.get('limit', type=int, default=3)

        if not crypto_service:
            return jsonify({
                'success': False,
                'error': 'Service Crypto non initialisé'
            }), 500

        data = crypto_service.get_all_cryptos(limit)

        if data.get('success'):
            return jsonify(data)
        else:
            return jsonify(data), 400

    except Exception as e:
        logger.error(f"[CRYPTO API] Erreur toutes cryptos: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/crypto/historical/<crypto_id>')
def get_crypto_historical_data(crypto_id):
    """
    API: Données historiques d'une cryptomonnaie
    GET /economic/api/crypto/historical/<crypto_id>?period=1m
    """
    try:
        period = request.args.get('period', '1m')

        if not crypto_service:
            return jsonify({
                'success': False,
                'error': 'Service Crypto non initialisé'
            }), 500

        data = crypto_service.get_crypto_historical_data(crypto_id.lower(), period)

        if data.get('success'):
            return jsonify(data)
        else:
            return jsonify(data), 400

    except Exception as e:
        logger.error(f"[CRYPTO API] Erreur historique {crypto_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/crypto/market-overview')
def get_crypto_market_overview():
    """
    API: Vue d'ensemble du marché des cryptomonnaies
    GET /economic/api/crypto/market-overview
    """
    try:
        if not crypto_service:
            return jsonify({
                'success': False,
                'error': 'Service Crypto non initialisé'
            }), 500

        data = crypto_service.get_crypto_market_overview()

        if data.get('success'):
            return jsonify(data)
        else:
            return jsonify(data), 400

    except Exception as e:
        logger.error(f"[CRYPTO API] Erreur market overview: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/crypto/news')
def get_crypto_news():
    """
    API: Actualités cryptomonnaies
    GET /economic/api/crypto/news?limit=5
    """
    try:
        limit = request.args.get('limit', type=int, default=5)

        if not crypto_service:
            return jsonify({
                'success': False,
                'error': 'Service Crypto non initialisé'
            }), 500

        data = crypto_service.get_crypto_news(limit)

        if data.get('success'):
            return jsonify(data)
        else:
            return jsonify(data), 400

    except Exception as e:
        logger.error(f"[CRYPTO API] Erreur news: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/crypto/available')
def get_available_cryptos():
    """
    API: Liste des cryptomonnaies disponibles
    GET /economic/api/crypto/available
    """
    try:
        if not crypto_service:
            return jsonify({
                'success': False,
                'error': 'Service Crypto non initialisé'
            }), 500

        cryptos = crypto_service.TRACKED_CRYPTOS

        return jsonify({
            'success': True,
            'cryptos': cryptos,
            'count': len(cryptos),
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"[CRYPTO API] Erreur available cryptos: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/crypto/validate-limit')
def validate_crypto_limit():
    """
    API: Vérifie la limite de cryptomonnaies surveillées
    GET /economic/api/crypto/validate-limit?current_count=2
    """
    try:
        current_count = request.args.get('current_count', type=int, default=0)

        if not crypto_service:
            return jsonify({
                'success': False,
                'error': 'Service Crypto non initialisé'
            }), 500

        data = crypto_service.validate_crypto_limit(current_count)

        if data.get('success'):
            return jsonify(data)
        else:
            return jsonify(data), 400

    except Exception as e:
        logger.error(f"[CRYPTO API] Erreur validate limit: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500