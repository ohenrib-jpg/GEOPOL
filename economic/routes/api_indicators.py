"""
Routes API pour les indicateurs economiques
"""
from flask import Blueprint, jsonify, request, current_app
import logging

logger = logging.getLogger(__name__)

# Creation du blueprint pour l'API
api_bp = Blueprint('economic_api_indicators', __name__)

# Variable globale pour stocker le service (sera injectee par le blueprint principal)
france_service = None

def init_service(service):
    """Initialise le service France"""
    global france_service
    france_service = service

@api_bp.route('/indicators/france')
def get_france_indicators():
    """
    API: Recupere les indicateurs francais
    GET /economic/api/indicators/france
    """
    try:
        force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'

        if not france_service:
            return jsonify({
                'success': False,
                'error': 'Service France non initialise'
            }), 500

        indicators = france_service.get_france_indicators(force_refresh=force_refresh)

        return jsonify({
            'success': True,
            'data': indicators,
            'count': len(indicators),
            'timestamp': indicators[0].get('last_updated') if indicators else None
        })

    except Exception as e:
        logger.error(f"[API] Erreur indicateurs France: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/indicators/international')
def get_international_indicators():
    """
    API: Recupere les indicateurs internationaux
    GET /economic/api/indicators/international
    """
    try:
        # TODO: Implementer avec international_service
        return jsonify({
            'success': True,
            'data': [],
            'message': 'En cours de developpement'
        })

    except Exception as e:
        logger.error(f"[API] Erreur indicateurs internationaux: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/indicators/summary')
def get_indicators_summary():
    """
    API: Recupere un resume de tous les indicateurs
    GET /economic/api/indicators/summary
    """
    try:
        force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'

        summary = {
            'france': [],
            'international': [],
            'timestamp': None
        }

        if france_service:
            summary['france'] = france_service.get_france_indicators(force_refresh=force_refresh)

        return jsonify({
            'success': True,
            'data': summary
        })

    except Exception as e:
        logger.error(f"[API] Erreur summary: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/health')
def health_check():
    """
    API: Health check du module economique
    GET /economic/api/health
    """
    try:
        status = {
            'module': 'economic',
            'status': 'healthy',
            'services': {
                'france_service': france_service is not None
            }
        }

        return jsonify(status)

    except Exception as e:
        logger.error(f"[API] Erreur health check: {e}")
        return jsonify({
            'module': 'economic',
            'status': 'unhealthy',
            'error': str(e)
        }), 500

@api_bp.route('/stats')
def get_stats():
    """
    API: Statistiques du cache
    GET /economic/api/stats
    """
    try:
        if not france_service:
            return jsonify({
                'success': False,
                'error': 'Service non initialise'
            }), 500

        stats = france_service.get_cache_stats()

        return jsonify({
            'success': True,
            'data': stats
        })

    except Exception as e:
        logger.error(f"[API] Erreur stats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================
# ROUTES API FRANCE - WIDGETS ET CAC40
# ============================================================

@api_bp.route('/france/available-indicators')
def get_available_indicators():
    """
    API: Liste des indicateurs France disponibles pour configuration
    GET /economic/api/france/available-indicators
    """
    try:
        if not france_service:
            return jsonify({
                'success': False,
                'error': 'Service France non initialise'
            }), 500

        indicators = france_service.get_available_indicators()

        return jsonify({
            'success': True,
            'data': indicators,
            'count': len(indicators)
        })

    except Exception as e:
        logger.error(f"[API] Erreur available indicators: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/france/indicator/<indicator_id>')
def get_indicator_by_id(indicator_id):
    """
    API: Recupere un indicateur par son ID
    GET /economic/api/france/indicator/<indicator_id>
    """
    try:
        force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'

        if not france_service:
            return jsonify({
                'success': False,
                'error': 'Service France non initialise'
            }), 500

        data = france_service.get_indicator_by_id(indicator_id, force_refresh=force_refresh)

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


@api_bp.route('/france/selected-indicators', methods=['GET', 'POST'])
def get_selected_indicators():
    """
    API: Recupere les indicateurs selectionnes pour les widgets
    GET /economic/api/france/selected-indicators?ids=cac40,pib,inflation
    POST /economic/api/france/selected-indicators {ids: ['cac40', 'pib', 'inflation']}
    """
    try:
        force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'

        if not france_service:
            return jsonify({
                'success': False,
                'error': 'Service France non initialise'
            }), 500

        # Recuperer les IDs soit depuis query params soit depuis body
        if request.method == 'POST':
            data = request.get_json() or {}
            indicator_ids = data.get('ids', [])
        else:
            ids_param = request.args.get('ids', '')
            indicator_ids = [i.strip() for i in ids_param.split(',') if i.strip()]

        # Par defaut, retourner les 4 indicateurs principaux
        if not indicator_ids:
            indicator_ids = ['cac40', 'pib', 'inflation', 'chomage']

        indicators = france_service.get_selected_indicators(indicator_ids, force_refresh=force_refresh)

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


@api_bp.route('/france/cac40/historical')
def get_cac40_historical():
    """
    API: Donnees historiques du CAC40 pour le graphique
    GET /economic/api/france/cac40/historical?period=1d

    Periodes disponibles:
    - realtime: Donnees intraday
    - 1d: 1 jour
    - 2d: 2 jours
    - 3d: 3 jours
    - 7d: 7 jours (1 semaine)
    - 1m: 1 mois
    """
    try:
        period = request.args.get('period', '1d')

        # Valider la periode
        valid_periods = ['realtime', '1d', '2d', '3d', '7d', '1m']
        if period not in valid_periods:
            return jsonify({
                'success': False,
                'error': f'Periode invalide. Valeurs acceptees: {", ".join(valid_periods)}'
            }), 400

        if not france_service:
            return jsonify({
                'success': False,
                'error': 'Service France non initialise'
            }), 500

        data = france_service.get_cac40_historical(period=period)

        return jsonify(data)

    except Exception as e:
        logger.error(f"[API] Erreur CAC40 historical: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/france/cac40/current')
def get_cac40_current():
    """
    API: Valeur actuelle du CAC40
    GET /economic/api/france/cac40/current
    """
    try:
        force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'

        if not france_service:
            return jsonify({
                'success': False,
                'error': 'Service France non initialise'
            }), 500

        data = france_service.get_cac40(force_refresh=force_refresh)

        if data:
            return jsonify({
                'success': True,
                'data': data
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Impossible de recuperer le CAC40'
            }), 500

    except Exception as e:
        logger.error(f"[API] Erreur CAC40 current: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/france/clear-cache', methods=['POST'])
def clear_france_cache():
    """
    API: Vider le cache des indicateurs France
    POST /economic/api/france/clear-cache
    POST /economic/api/france/clear-cache?key=france_unemployment
    """
    try:
        if not france_service:
            return jsonify({
                'success': False,
                'error': 'Service France non initialise'
            }), 500

        cache_key = request.args.get('key', None)

        if cache_key:
            # Vider une entree specifique
            france_service.invalidate_cache(cache_key)
            return jsonify({
                'success': True,
                'message': f'Cache {cache_key} invalide'
            })
        else:
            # Vider tous les caches France
            cache_keys = [
                'france_cac40',
                'france_gdp',
                'france_inflation',
                'france_unemployment',
                'france_trade_balance',
                'france_eurusd'
            ]
            for key in cache_keys:
                france_service.invalidate_cache(key)

            return jsonify({
                'success': True,
                'message': f'{len(cache_keys)} entrees de cache invalidees',
                'keys': cache_keys
            })

    except Exception as e:
        logger.error(f"[API] Erreur clear cache: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/france/refresh-all', methods=['POST'])
def refresh_all_france():
    """
    API: Forcer le rafraichissement de tous les indicateurs France
    POST /economic/api/france/refresh-all
    """
    try:
        if not france_service:
            return jsonify({
                'success': False,
                'error': 'Service France non initialise'
            }), 500

        # Forcer le rafraichissement
        indicators = france_service.get_france_indicators(force_refresh=True)

        return jsonify({
            'success': True,
            'message': 'Indicateurs rafraichis',
            'count': len(indicators),
            'data': indicators
        })

    except Exception as e:
        logger.error(f"[API] Erreur refresh all: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/debug/cache')
def debug_cache():
    """
    API Debug: Voir le contenu du cache economique
    GET /economic/api/debug/cache
    GET /economic/api/debug/cache?key=france_unemployment
    """
    try:
        if not france_service:
            return jsonify({
                'success': False,
                'error': 'Service France non initialise'
            }), 500

        cache_key = request.args.get('key', None)

        conn = france_service.db_manager.get_connection()
        cursor = conn.cursor()

        if cache_key:
            # Une entree specifique
            cursor.execute("""
                SELECT cache_key, data_source, data_type, data_value,
                       timestamp, expiry_datetime, is_fresh
                FROM economic_cache
                WHERE cache_key = ?
            """, (cache_key,))
        else:
            # Toutes les entrees
            cursor.execute("""
                SELECT cache_key, data_source, data_type, data_value,
                       timestamp, expiry_datetime, is_fresh
                FROM economic_cache
                ORDER BY timestamp DESC
                LIMIT 50
            """)

        rows = cursor.fetchall()
        conn.close()

        entries = []
        for row in rows:
            try:
                import json
                data_parsed = json.loads(row[3])
            except:
                data_parsed = row[3]

            entries.append({
                'cache_key': row[0],
                'data_source': row[1],
                'data_type': row[2],
                'data': data_parsed,
                'timestamp': row[4],
                'expiry_datetime': row[5],
                'is_fresh': bool(row[6])
            })

        return jsonify({
            'success': True,
            'count': len(entries),
            'entries': entries
        })

    except Exception as e:
        logger.error(f"[API] Erreur debug cache: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/debug/eurostat-test')
def debug_eurostat_test():
    """
    API Debug: Tester directement le connecteur Eurostat
    GET /economic/api/debug/eurostat-test?indicator=unemployment
    """
    try:
        indicator_id = request.args.get('indicator', 'unemployment')

        if not france_service or not france_service.eurostat:
            return jsonify({
                'success': False,
                'error': 'Connecteur Eurostat non disponible'
            }), 500

        # Appel direct au connecteur Eurostat
        result = france_service.eurostat.get_indicator(indicator_id, force_refresh=True)

        return jsonify({
            'success': True,
            'indicator': indicator_id,
            'raw_result': result
        })

    except Exception as e:
        logger.error(f"[API] Erreur test Eurostat: {e}")
        import traceback
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500
