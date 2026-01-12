"""
Routes API pour les données UN OCHA HDX
Source principale de données conflits/humanitaires
"""

from flask import Blueprint, jsonify, request
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Blueprint
hdx_bp = Blueprint('hdx', __name__, url_prefix='/api/hdx')

# Connecteurs (seront initialisés par la factory)
hdx_primary_connector = None
hdx_basic_connector = None


def init_hdx_routes(app):
    """Initialise les routes HDX"""
    global hdx_primary_connector, hdx_basic_connector

    try:
        from .hdx_primary_connector import get_hdx_primary_connector
        from .ocha_hdx_connector import get_ocha_hdx_connector

        hdx_primary_connector = get_hdx_primary_connector()
        hdx_basic_connector = get_ocha_hdx_connector()

        app.register_blueprint(hdx_bp)
        logger.info("[OK] Routes HDX initialisées")

    except Exception as e:
        logger.error(f"[ERROR] Erreur initialisation routes HDX: {e}")
        raise


# ============================================================================
# ROUTES DE DONNÉES HDX
# ============================================================================

@hdx_bp.route('/health', methods=['GET'])
def health_check():
    """Health check du module HDX"""
    try:
        return jsonify({
            'success': True,
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'connectors': {
                'primary': hdx_primary_connector is not None,
                'basic': hdx_basic_connector is not None
            }
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 500


@hdx_bp.route('/summary', methods=['GET'])
def get_summary():
    """Récupère un résumé global des crises et conflits"""
    try:
        use_primary = request.args.get('primary', 'true').lower() == 'true'

        if use_primary and hdx_primary_connector:
            result = hdx_primary_connector.get_summary()
        elif hdx_basic_connector:
            result = hdx_basic_connector.get_summary()
        else:
            return jsonify({
                'success': False,
                'error': 'HDX connectors not initialized'
            }), 500

        return jsonify(result), 200 if result.get('success') else 400

    except Exception as e:
        logger.error(f"[ERROR] Erreur get_summary: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@hdx_bp.route('/conflict-events', methods=['GET'])
def get_conflict_events():
    """Récupère les événements de conflit récents (similaire ACLED)"""
    try:
        days = int(request.args.get('days', '30'))
        limit = int(request.args.get('limit', '100'))

        if not hdx_primary_connector:
            return jsonify({
                'success': False,
                'error': 'HDX primary connector not initialized'
            }), 500

        result = hdx_primary_connector.get_conflict_events(days=days, limit=limit)

        return jsonify(result), 200 if result.get('success') else 400

    except Exception as e:
        logger.error(f"[ERROR] Erreur get_conflict_events: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@hdx_bp.route('/crisis-indicators', methods=['GET'])
def get_crisis_indicators():
    """Récupère des indicateurs de crise pour un pays ou globalement"""
    try:
        country = request.args.get('country')
        use_primary = request.args.get('primary', 'true').lower() == 'true'

        if use_primary and hdx_primary_connector:
            result = hdx_primary_connector.get_crisis_indicators(country=country)
        elif hdx_basic_connector:
            # Fallback sur le connecteur de base
            if country:
                result = hdx_basic_connector.get_country_data(country)
            else:
                result = hdx_basic_connector.get_summary()
        else:
            return jsonify({
                'success': False,
                'error': 'HDX connectors not initialized'
            }), 500

        return jsonify(result), 200 if result.get('success') else 400

    except Exception as e:
        logger.error(f"[ERROR] Erreur get_crisis_indicators: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@hdx_bp.route('/priority-regions', methods=['GET'])
def get_priority_regions():
    """Récupère le statut des régions prioritaires"""
    try:
        if not hdx_primary_connector:
            return jsonify({
                'success': False,
                'error': 'HDX primary connector not initialized'
            }), 500

        result = hdx_primary_connector.get_priority_regions_status()

        return jsonify(result), 200 if result.get('success') else 400

    except Exception as e:
        logger.error(f"[ERROR] Erreur get_priority_regions: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@hdx_bp.route('/humanitarian-access', methods=['GET'])
def get_humanitarian_access():
    """Récupère les données d'accès humanitaire"""
    try:
        use_primary = request.args.get('primary', 'true').lower() == 'true'

        if use_primary and hdx_primary_connector:
            result = hdx_primary_connector.get_humanitarian_access_map()
        elif hdx_basic_connector:
            result = hdx_basic_connector.get_humanitarian_access()
        else:
            return jsonify({
                'success': False,
                'error': 'HDX connectors not initialized'
            }), 500

        return jsonify(result), 200 if result.get('success') else 400

    except Exception as e:
        logger.error(f"[ERROR] Erreur get_humanitarian_access: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@hdx_bp.route('/daily-briefing', methods=['GET'])
def get_daily_briefing():
    """Génère un briefing quotidien des crises mondiales"""
    try:
        if not hdx_primary_connector:
            return jsonify({
                'success': False,
                'error': 'HDX primary connector not initialized'
            }), 500

        result = hdx_primary_connector.get_daily_briefing()

        return jsonify(result), 200 if result.get('success') else 400

    except Exception as e:
        logger.error(f"[ERROR] Erreur get_daily_briefing: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@hdx_bp.route('/datasets/search', methods=['GET'])
def search_datasets():
    """Recherche de datasets HDX"""
    try:
        query = request.args.get('query', 'crisis')
        limit = int(request.args.get('limit', '20'))

        if not hdx_basic_connector:
            return jsonify({
                'success': False,
                'error': 'HDX basic connector not initialized'
            }), 500

        result = hdx_basic_connector.search_datasets(query=query, limit=limit)

        return jsonify(result), 200 if result.get('success') else 400

    except Exception as e:
        logger.error(f"[ERROR] Erreur search_datasets: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@hdx_bp.route('/country/<country_name>', methods=['GET'])
def get_country_data(country_name: str):
    """Récupère toutes les données pour un pays spécifique"""
    try:
        use_primary = request.args.get('primary', 'true').lower() == 'true'

        if use_primary and hdx_primary_connector:
            # Utiliser les indicateurs avancés
            result = hdx_primary_connector.get_crisis_indicators(country=country_name)
        elif hdx_basic_connector:
            result = hdx_basic_connector.get_country_data(country_name)
        else:
            return jsonify({
                'success': False,
                'error': 'HDX connectors not initialized'
            }), 500

        return jsonify(result), 200 if result.get('success') else 400

    except Exception as e:
        logger.error(f"[ERROR] Erreur get_country_data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@hdx_bp.route('/compare/acled', methods=['GET'])
def compare_with_acled():
    """
    Compare les données HDX avec ACLED (si configuré)
    Retourne des métriques de couverture
    """
    try:
        # Cette route nécessite ACLED configuré
        # Pour l'instant, retourne des informations basiques
        return jsonify({
            'success': True,
            'comparison': {
                'hdx_coverage': 'global',
                'acled_coverage': 'specific_conflicts',
                'hdx_auth_required': False,
                'acled_auth_required': True,
                'recommendation': 'Use HDX as primary source with ACLED as supplement'
            },
            'timestamp': datetime.now().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"[ERROR] Erreur compare_with_acled: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# ROUTES ADMIN / DIAGNOSTIC
# ============================================================================

@hdx_bp.route('/diagnostic', methods=['GET'])
def diagnostic():
    """Diagnostic complet du système HDX"""
    try:
        diagnostic_info = {
            'timestamp': datetime.now().isoformat(),
            'connectors': {
                'primary_initialized': hdx_primary_connector is not None,
                'basic_initialized': hdx_basic_connector is not None
            },
            'endpoints': [
                '/api/hdx/health',
                '/api/hdx/summary',
                '/api/hdx/conflict-events',
                '/api/hdx/crisis-indicators',
                '/api/hdx/priority-regions',
                '/api/hdx/humanitarian-access',
                '/api/hdx/daily-briefing',
                '/api/hdx/datasets/search',
                '/api/hdx/country/<country>',
                '/api/hdx/compare/acled'
            ],
            'status': 'operational' if hdx_primary_connector or hdx_basic_connector else 'inactive'
        }

        # Test de connexion basique
        if hdx_basic_connector:
            try:
                test_result = hdx_basic_connector.search_datasets(query='test', limit=1)
                diagnostic_info['connectivity_test'] = {
                    'success': test_result.get('success', False),
                    'datasets_found': test_result.get('count', 0)
                }
            except Exception as e:
                diagnostic_info['connectivity_test'] = {
                    'success': False,
                    'error': str(e)
                }

        return jsonify({
            'success': True,
            'diagnostic': diagnostic_info
        }), 200

    except Exception as e:
        logger.error(f"[ERROR] Erreur diagnostic: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


__all__ = ['hdx_bp', 'init_hdx_routes']