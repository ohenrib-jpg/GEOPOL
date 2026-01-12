# Flask/demographic_routes.py - VERSION CORRIGÉE
"""
Routes API pour le module démographique - VERSION CORRIGÉE
"""

from flask import Blueprint, jsonify, request, render_template
import logging
import time
import traceback

logger = logging.getLogger(__name__)


def create_demographic_blueprint(db_manager, demographic_service):
    """Crée le blueprint pour les routes démographiques"""
    
    # VÉRIFICATION CRITIQUE - mais NE PAS utiliser jsonify ici
    if db_manager is None:
        logger.error("[ERROR] db_manager est None")
        # Ne pas utiliser jsonify hors contexte
        return None
    
    if demographic_service is None:
        logger.error("[ERROR] demographic_service est None")
        return None
    
    try:
        bp = Blueprint('demographic', __name__, url_prefix='/demographic')
        logger.info("[OK] Blueprint démographique créé")
        
        # ============================================================
        # INTERFACE WEB
        # ============================================================
        
        @bp.route('/')
        def demographic_dashboard():
            """Page principale du module démographique"""
            try:
                return render_template('demographic_dashboard.html')
            except Exception as e:
                logger.error(f"Erreur chargement template: {e}")
                # Retourner HTML directement, pas jsonify
                return f'''
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Module Démographique - GEOPOL</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; padding: 20px; background: #f5f5f5; }}
                        .container {{ max-width: 800px; margin: 50px auto; text-align: center; }}
                        .card {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                        h1 {{ color: #3b82f6; }}
                        .api-link {{ display: block; margin: 10px 0; padding: 10px; background: #3b82f6; color: white; text-decoration: none; border-radius: 5px; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="card">
                            <h1>[DATA] Module Démographique</h1>
                            <p>Template non trouvé. L'API fonctionne :</p>
                            <a href="/demographic/api/test" class="api-link">Test API</a>
                            <a href="/demographic/api/debug" class="api-link">Debug Info</a>
                            <a href="/demographic/api/stats" class="api-link">Statistiques</a>
                        </div>
                    </div>
                </body>
                </html>
                ''', 200

        # ============================================================
        # API ENDPOINTS - TOUTES LES FONCTIONS SONT DANS LE CONTEXTE DU BLUEPRINT
        # ============================================================
        
        @bp.route('/api/test')
        def api_test():
            """Test endpoint - DANS LE CONTEXTE"""
            return jsonify({
                'success': True,
                'module': 'demographic',
                'version': '1.0',
                'timestamp': time.time()
            })

        @bp.route('/api/debug')
        def debug_info():
            """Debug endpoint - DANS LE CONTEXTE"""
            return jsonify({
                'success': True,
                'blueprint': 'demographic',
                'db_manager': 'present' if db_manager else 'missing',
                'service': 'present' if demographic_service else 'missing',
                'timestamp': time.time()
            })

        @bp.route('/api/stats')
        def get_stats():
            """Stats endpoint - DANS LE CONTEXTE"""
            try:
                countries = []
                indicators = []
                has_data = False

                try:
                    countries = demographic_service.get_available_countries()
                    indicators = demographic_service.get_available_indicators()
                    has_data = len(countries) > 0 or len(indicators) > 0
                except Exception as e:
                    logger.warning(f"Erreur récupération données: {e}")

                return jsonify({
                    'success': True,
                    'stats': {
                        'countries': len(countries),  # ← Corrigé pour correspondre au JS
                        'indicators': len(indicators),  # ← Corrigé pour correspondre au JS
                        'total_countries': len(countries),  # Gardé pour rétrocompatibilité
                        'total_indicators': len(indicators),  # Gardé pour rétrocompatibilité
                        'has_data': has_data,
                        'status': 'operational' if has_data else 'empty',
                        'message': 'Données disponibles' if has_data else 'Base de données vide - Collecte initiale nécessaire'
                    }
                })
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        @bp.route('/api/countries')
        def get_countries():
            """Countries endpoint - DANS LE CONTEXTE"""
            try:
                countries = demographic_service.get_available_countries()
                return jsonify({
                    'success': True,
                    'countries': countries,
                    'count': len(countries)
                })
            except Exception as e:
                logger.error(f"Erreur récupération pays: {e}")
                # Retourner une liste vide si erreur - pas de données fictives
                return jsonify({
                    'success': True,
                    'countries': [],
                    'count': 0,
                    'message': 'Aucun pays disponible. Lancez une collecte de données.'
                })

        @bp.route('/api/indicators')
        def get_indicators():
            """Indicators endpoint - DANS LE CONTEXTE"""
            try:
                indicators = demographic_service.get_available_indicators()
                return jsonify({
                    'success': True,
                    'indicators': indicators,
                    'count': len(indicators)
                })
            except Exception as e:
                logger.error(f"Erreur récupération indicateurs: {e}")
                # Retourner une liste vide si erreur - pas de données fictives
                return jsonify({
                    'success': True,
                    'indicators': [],
                    'count': 0,
                    'message': 'Aucun indicateur disponible. Lancez une collecte de données.'
                })

        @bp.route('/api/collect', methods=['POST'])
        def collect_data():
            """Collecte initiale de données démographiques"""
            try:
                data = request.get_json() if request.is_json else {}
                countries = data.get('countries', ['FR', 'DE', 'ES', 'IT', 'NL', 'BE', 'PT', 'PL'])

                logger.info(f"[MIGRATION] Collecte initiale pour: {countries}")

                collected_count = 0
                errors = []

                # Collecter les données de base depuis Eurostat
                basic_datasets = ['demo_pjan', 'nama_10_gdp', 'une_rt_a']  # Population, PIB, Chômage

                for dataset in basic_datasets:
                    try:
                        eurostat_data = demographic_service.fetch_eurostat_data(
                            dataset,
                            {'geo': countries}
                        )

                        if eurostat_data:
                            stored = demographic_service.store_indicators(eurostat_data)
                            collected_count += stored
                            logger.info(f"[OK] {dataset}: {stored} indicateurs stockés")
                    except Exception as e:
                        error_msg = f"{dataset}: {str(e)}"
                        errors.append(error_msg)
                        logger.error(f"[ERROR] Erreur collecte {dataset}: {e}")

                return jsonify({
                    'success': True,
                    'message': f'Collecte terminée: {collected_count} indicateurs collectés',
                    'countries': countries,
                    'collected': collected_count,
                    'datasets': basic_datasets,
                    'errors': errors if errors else None
                })

            except Exception as e:
                logger.error(f"[ERROR] Erreur collecte générale: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500

        # Routes de collecte individuelles - AVEC APPEL RÉEL DES APIs
        @bp.route('/api/collect/eurostat/<dataset>')
        def collect_eurostat(dataset):
            """Collecte réelle de données Eurostat"""
            try:
                logger.info(f"Collecte Eurostat: {dataset}")

                # Appeler réellement le service
                filters = request.args.to_dict() if request.args else None
                data = demographic_service.fetch_eurostat_data(dataset, filters)

                # Stocker en base
                stored = demographic_service.store_indicators(data) if data else 0

                return jsonify({
                    'success': True,
                    'source': 'eurostat',
                    'dataset': dataset,
                    'fetched': len(data),
                    'stored': stored,
                    'filters': filters
                })
            except Exception as e:
                logger.error(f"Erreur collecte Eurostat {dataset}: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @bp.route('/api/collect/worldbank/<indicator>')
        def collect_worldbank(indicator):
            """Collecte réelle de données World Bank"""
            try:
                logger.info(f"Collecte World Bank: {indicator}")

                # Récupérer les pays depuis les paramètres
                countries_param = request.args.get('countries', 'all')
                countries = countries_param.split(';') if countries_param != 'all' else None

                # Appeler réellement le service
                data = demographic_service.fetch_worldbank_data(indicator, countries)

                # Stocker en base
                stored = demographic_service.store_indicators(data) if data else 0

                return jsonify({
                    'success': True,
                    'source': 'worldbank',
                    'indicator': indicator,
                    'fetched': len(data),
                    'stored': stored,
                    'countries': countries or 'all'
                })
            except Exception as e:
                logger.error(f"Erreur collecte World Bank {indicator}: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @bp.route('/api/collect/ecb/<flow_ref>')
        def collect_ecb(flow_ref):
            """Collecte réelle de données BCE"""
            try:
                logger.info(f"Collecte BCE: {flow_ref}")

                # Récupérer la clé optionnelle
                key = request.args.get('key', None)

                # Appeler réellement le service
                data = demographic_service.fetch_ecb_data(flow_ref, key)

                # Stocker en base
                stored = demographic_service.store_indicators(data) if data else 0

                return jsonify({
                    'success': True,
                    'source': 'ecb',
                    'flow': flow_ref,
                    'key': key,
                    'fetched': len(data),
                    'stored': stored
                })
            except Exception as e:
                logger.error(f"Erreur collecte BCE {flow_ref}: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        # Routes de démo - DÉSACTIVÉE (utiliser les vraies sources de données)
        # @bp.route('/api/collect/demo')
        # def collect_demo():
        #     """Route de démonstration désactivée - utiliser les collectes réelles"""
        #     return jsonify({
        #         'success': False,
        #         'error': 'Les données de démonstration ont été désactivées. Utilisez la collecte rapide ou complète.'
        #     }), 404

        @bp.route('/api/collect/quick')
        def collect_quick():
            """Collecte rapide des indicateurs essentiels - APPEL RÉEL"""
            try:
                logger.info("Collecte rapide des indicateurs essentiels")

                # Récupérer les pays depuis les paramètres
                countries_param = request.args.get('countries', None)
                countries = countries_param.split(';') if countries_param else None

                # Appeler la méthode de collecte essentielle du service
                result = demographic_service.collect_essential_indicators(countries)

                return jsonify({
                    'success': result.get('success', True),
                    'message': 'Collecte rapide des indicateurs essentiels terminée',
                    'stats': result.get('stats', {}),
                    'total_indicators': result.get('indicators_count', 0)
                })
            except Exception as e:
                logger.error(f"Erreur collecte rapide: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @bp.route('/api/country/<country_code>')
        def get_country_data(country_code):
            """Récupère les vraies données d'un pays depuis la base"""
            try:
                year = request.args.get('year', None, type=int)

                # Récupérer les vraies données depuis le service
                data = demographic_service.get_country_data(country_code, year)

                # Si pas de données, retourner un ensemble minimal
                if not data:
                    data = {
                        'population': [],
                        'economy': [],
                        'social': [],
                        'health': [],
                        'education': []
                    }

                return jsonify({
                    'success': True,
                    'country_code': country_code,
                    'year': year or 'latest',
                    'data': data,
                    'indicators_count': sum(len(v) for v in data.values())
                })
            except Exception as e:
                logger.error(f"Erreur récupération données pays {country_code}: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        @bp.route('/api/indicator/<indicator_id>/comparison')
        def get_indicator_comparison(indicator_id):
            """Récupère les données de comparaison pour un indicateur donné"""
            try:
                # Récupérer les pays depuis les paramètres de requête
                countries_param = request.args.get('countries', '')
                if countries_param:
                    countries = countries_param.split(',')
                else:
                    # Par défaut, les 5 pays les plus peuplés d'Europe
                    countries = ['FR', 'DE', 'ES', 'IT', 'NL']

                # Récupérer l'année de début si fournie
                start_year = request.args.get('start_year', None, type=int)

                # Utiliser le service pour récupérer les données
                comparison_data = demographic_service.get_indicator_comparison(
                    indicator_id, countries, start_year
                )

                # comparison_data contient déjà indicator_id et indicator_name
                # Ajoutons les autres métadonnées
                response_data = {
                    'success': True,
                    **comparison_data,
                    'countries': countries,
                    'start_year': start_year
                }
                return jsonify(response_data)
            except Exception as e:
                logger.error(f"Erreur récupération comparaison indicateur {indicator_id}: {e}")
                return jsonify({'success': False, 'error': str(e)}), 500

        # Route sample-data désactivée - utiliser les vraies données
        # @bp.route('/api/sample-data')
        # def sample_data():
        #     """Route d'exemples désactivée - utiliser les vraies API"""
        #     return jsonify({
        #         'success': False,
        #         'error': 'Les données d\'exemple ont été désactivées. Utilisez les vraies sources de données.'
        #     }), 404

        @bp.route('/api/test-connectors')
        def test_connectors():
            """Test des 3 connecteurs de données"""
            try:
                results = {
                    'success': True,
                    'timestamp': time.time(),
                    'connectors': {}
                }

                # Test Eurostat
                logger.info("🧪 Test Eurostat...")
                try:
                    eurostat_data = demographic_service.fetch_eurostat_data('demo_pjan')
                    results['connectors']['eurostat'] = {
                        'status': 'success' if eurostat_data else 'no_data',
                        'records': len(eurostat_data),
                        'sample': eurostat_data[:3] if eurostat_data else []
                    }
                except Exception as e:
                    results['connectors']['eurostat'] = {
                        'status': 'error',
                        'error': str(e)
                    }

                # Test World Bank
                logger.info("🧪 Test World Bank...")
                try:
                    wb_data = demographic_service.fetch_worldbank_data('SP.POP.TOTL', ['FR', 'DE', 'ES'])
                    results['connectors']['worldbank'] = {
                        'status': 'success' if wb_data else 'no_data',
                        'records': len(wb_data),
                        'sample': wb_data[:3] if wb_data else []
                    }
                except Exception as e:
                    results['connectors']['worldbank'] = {
                        'status': 'error',
                        'error': str(e)
                    }

                # Test INSEE
                logger.info("🧪 Test INSEE...")
                try:
                    insee_data = demographic_service.fetch_insee_data()
                    results['connectors']['insee'] = {
                        'status': 'success' if insee_data else 'no_data',
                        'records': len(insee_data),
                        'sample': insee_data[:3] if insee_data else [],
                        'note': 'Fallback data may be used if scraping fails'
                    }
                except Exception as e:
                    results['connectors']['insee'] = {
                        'status': 'error',
                        'error': str(e)
                    }

                # Résumé
                total_records = sum(
                    c.get('records', 0) for c in results['connectors'].values()
                    if isinstance(c, dict)
                )
                results['summary'] = {
                    'total_records': total_records,
                    'connectors_working': sum(
                        1 for c in results['connectors'].values()
                        if isinstance(c, dict) and c.get('status') == 'success'
                    ),
                    'connectors_total': 3
                }

                return jsonify(results)

            except Exception as e:
                logger.error(f"Erreur test connecteurs: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e),
                    'traceback': traceback.format_exc()
                }), 500

        logger.info("[OK] Routes démographiques configurées")
        return bp
        
    except Exception as e:
        logger.error(f"[ERROR] Erreur création blueprint: {e}")
        # NE PAS utiliser jsonify ici !
        return None