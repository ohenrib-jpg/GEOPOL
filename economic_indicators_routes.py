# Flask/economic_indicators_routes.py
"""
Routes Flask pour le module Indicateurs Économiques Internationaux
"""

from flask import jsonify, request, render_template
import logging

logger = logging.getLogger(__name__)


def register_economic_routes(app, db_manager):
    """Enregistre toutes les routes du module économique"""
    
    from .economic_indicators import EconomicIndicatorsManager
    
    # Initialiser le manager
    eco_manager = EconomicIndicatorsManager(db_manager)
    app.config['ECO_MANAGER'] = eco_manager
    
    logger.info("📊 Enregistrement des routes économiques...")
    
    # ==========================================
    # PAGE PRINCIPALE
    # ==========================================
    
    @app.route('/indicators')
    def indicators_page():
        """Page principale des indicateurs économiques"""
        try:
            return render_template('economic_indicators.html')
        except:
            # Fallback: utiliser le fichier static
            return app.send_static_file('economic_indicators.html')
    
    # ==========================================
    # INDICATEURS FINANCIERS (YFINANCE)
    # ==========================================
    
    @app.route('/api/economic/financial/fetch', methods=['POST'])
    def fetch_financial():
        """Récupère des données financières"""
        try:
            data = request.get_json()
            symbols = data.get('symbols', [])
            period = data.get('period', '1mo')
            
            if not symbols:
                return jsonify({'success': False, 'error': 'Symboles manquants'}), 400
            
            results = eco_manager.fetch_financial_data(symbols, period)
            
            return jsonify({
                'success': True,
                'data': results,
                'count': len(results)
            })
            
        except Exception as e:
            logger.error(f"❌ Erreur fetch_financial: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/economic/financial/latest')
    def get_latest_financial():
        """Récupère les derniers indicateurs financiers"""
        try:
            limit = request.args.get('limit', 50, type=int)
            data = eco_manager.get_latest_financial_indicators(limit)
            
            return jsonify({
                'success': True,
                'data': data,
                'count': len(data)
            })
            
        except Exception as e:
            logger.error(f"❌ Erreur get_latest_financial: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/economic/indices')
    def get_major_indices():
        """Récupère les principaux indices boursiers"""
        try:
            data = eco_manager.get_major_indices()
            
            return jsonify({
                'success': True,
                'data': data,
                'timestamp': app.config.get('LAST_UPDATE', '')
            })
            
        except Exception as e:
            logger.error(f"❌ Erreur get_major_indices: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/economic/commodities')
    def get_commodities():
        """Récupère les prix des matières premières"""
        try:
            data = eco_manager.get_commodities()
            
            return jsonify({
                'success': True,
                'data': data
            })
            
        except Exception as e:
            logger.error(f"❌ Erreur get_commodities: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/economic/currencies')
    def get_currencies():
        """Récupère les taux de change"""
        try:
            data = eco_manager.get_currencies()
            
            return jsonify({
                'success': True,
                'data': data
            })
            
        except Exception as e:
            logger.error(f"❌ Erreur get_currencies: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    # ==========================================
    # BANQUE MONDIALE
    # ==========================================
    
    @app.route('/api/economic/worldbank/fetch', methods=['POST'])
    def fetch_worldbank():
        """Récupère des données Banque Mondiale"""
        try:
            data = request.get_json()
            countries = data.get('countries', [])
            indicator = data.get('indicator', 'NY.GDP.MKTP.CD')
            years = data.get('years', 5)
            
            if not countries:
                return jsonify({'success': False, 'error': 'Pays manquants'}), 400
            
            results = eco_manager.fetch_world_bank_data(countries, indicator, years)
            
            return jsonify({
                'success': True,
                'data': results,
                'indicator': indicator
            })
            
        except Exception as e:
            logger.error(f"❌ Erreur fetch_worldbank: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/economic/worldbank/country/<country_code>')
    def get_wb_by_country(country_code):
        """Récupère les indicateurs d'un pays"""
        try:
            limit = request.args.get('limit', 20, type=int)
            data = eco_manager.get_wb_indicators_by_country(country_code, limit)
            
            return jsonify({
                'success': True,
                'country': country_code,
                'data': data,
                'count': len(data)
            })
            
        except Exception as e:
            logger.error(f"❌ Erreur get_wb_by_country: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/economic/brics')
    def get_brics():
        """Récupère les indicateurs des pays BRICS"""
        try:
            data = eco_manager.get_brics_indicators()
            
            return jsonify({
                'success': True,
                'data': data
            })
            
        except Exception as e:
            logger.error(f"❌ Erreur get_brics: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    # ==========================================
    # SANCTIONS INTERNATIONALES
    # ==========================================
    
    @app.route('/api/economic/sanctions/fetch', methods=['POST'])
    def fetch_sanctions():
        """Récupère les données de sanctions"""
        try:
            data = request.get_json() or {}
            countries = data.get('countries')
            
            results = eco_manager.fetch_sanctions_data(countries)
            
            return jsonify({
                'success': True,
                'data': results
            })
            
        except Exception as e:
            logger.error(f"❌ Erreur fetch_sanctions: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/economic/sanctions/summary')
    def get_sanctions_summary():
        """Récupère un résumé des sanctions"""
        try:
            data = eco_manager.get_sanctions_summary()
            
            return jsonify({
                'success': True,
                'data': data
            })
            
        except Exception as e:
            logger.error(f"❌ Erreur get_sanctions_summary: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    # ==========================================
    # SÉRIES TEMPORELLES
    # ==========================================
    
    @app.route('/api/economic/timeseries/<indicator_key>')
    def get_timeseries(indicator_key):
        """Récupère une série temporelle"""
        try:
            indicator_type = request.args.get('type', 'price')
            days = request.args.get('days', 30, type=int)
            
            data = eco_manager.get_time_series(indicator_key, indicator_type, days)
            
            return jsonify({
                'success': True,
                'indicator': indicator_key,
                'type': indicator_type,
                'data': data,
                'count': len(data)
            })
            
        except Exception as e:
            logger.error(f"❌ Erreur get_timeseries: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/economic/timeseries/save', methods=['POST'])
    def save_timeseries():
        """Sauvegarde un point de série temporelle"""
        try:
            data = request.get_json()
            
            eco_manager.save_time_series(
                indicator_key=data['indicator_key'],
                indicator_type=data['indicator_type'],
                date=data['date'],
                value=data['value'],
                metadata=data.get('metadata')
            )
            
            return jsonify({
                'success': True,
                'message': 'Point sauvegardé'
            })
            
        except Exception as e:
            logger.error(f"❌ Erreur save_timeseries: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    # ==========================================
    # DASHBOARD COMPLET
    # ==========================================
    
    @app.route('/api/economic/dashboard')
    def get_economic_dashboard():
        """Récupère toutes les données pour le dashboard"""
        try:
            # Récupérer toutes les données principales
            indices = eco_manager.get_major_indices()
            commodities = eco_manager.get_commodities()
            currencies = eco_manager.get_currencies()
            sanctions = eco_manager.get_sanctions_summary()
            
            return jsonify({
                'success': True,
                'data': {
                    'indices': indices,
                    'commodities': commodities,
                    'currencies': currencies,
                    'sanctions': sanctions
                }
            })
            
        except Exception as e:
            logger.error(f"❌ Erreur get_economic_dashboard: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    logger.info("✅ Routes économiques enregistrées")
