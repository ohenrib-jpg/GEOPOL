# Flask/routes_indicators.py
"""
Routes Flask pour le dashboard économique INTERNATIONAL
Sources : yFinance, Banque Mondiale, OpenSanctions, BRICS
"""

from flask import Blueprint, jsonify, request, render_template
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def create_indicators_blueprint(db_manager):
    """Crée le blueprint des indicateurs économiques internationaux"""
    
    indicators_bp = Blueprint('indicators_intl', __name__, url_prefix='/indicators')
    
    # Initialiser les connecteurs
    try:
        from .yfinance_connector import YFinanceConnector
        yfinance = YFinanceConnector()
    except Exception as e:
        logger.error(f"Erreur initialisation yFinance: {e}")
        yfinance = None
    
    # === PAGE PRINCIPALE ===
    @indicators_bp.route('/')
    def indicators_page():
        """Page principale du dashboard international"""
        return render_template('indicators_international_dashboard.html')
    
    # === API INDICES BOURSIERS ===
    @indicators_bp.route('/api/indices')
    def get_financial_indices():
        """Récupère les indices boursiers internationaux"""
        try:
            if yfinance:
                result = yfinance.get_all_indices()
                return jsonify(result)
            else:
                return jsonify({
                    'success': False,
                    'error': 'yFinance non disponible'
                }), 500
                
        except Exception as e:
            logger.error(f"❌ Erreur get_financial_indices: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @indicators_bp.route('/api/historical/<symbol>')
    def get_historical_data(symbol):
        """Données historiques d'un indice"""
        try:
            if yfinance:
                period = request.args.get('period', '6mo')
                result = yfinance.get_historical_data(symbol, period)
                return jsonify(result)
            else:
                return jsonify({
                    'success': False,
                    'error': 'yFinance non disponible'
                }), 500
                
        except Exception as e:
            logger.error(f"❌ Erreur get_historical_data: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # === API DONNÉES MACROÉCONOMIQUES ===
    @indicators_bp.route('/api/macro')
    def get_macro_data():
        """Récupère les données macroéconomiques internationales"""
        try:
            # Données de démonstration pour l'instant
            result = {
                'success': True,
                'data': {
                    'world_gdp_growth': {
                        'value': 3.1,
                        'unit': '%',
                        'period': '2024',
                        'source': 'Banque Mondiale (simulation)'
                    },
                    'world_inflation': {
                        'value': 5.2,
                        'unit': '%',
                        'period': '2024',
                        'source': 'FMI (simulation)'
                    },
                    'world_trade_volume': {
                        'value': 1.8,
                        'unit': '%',
                        'period': '2024',
                        'source': 'OMC (simulation)'
                    }
                },
                'timestamp': datetime.now().isoformat(),
                'note': 'Données de démonstration - Module en développement'
            }
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"❌ Erreur get_macro_data: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # === API SANCTIONS INTERNATIONALES ===
    @indicators_bp.route('/api/sanctions')
    def get_sanctions_data():
        """Récupère les données de sanctions internationales"""
        try:
            # Données de démonstration pour l'instant
            result = {
                'success': True,
                'sanctions': {
                    'active_sanctions': 1247,
                    'new_this_month': 23,
                    'countries_affected': 45,
                    'sectors_targeted': ['Énergie', 'Technologie', 'Finance', 'Transport']
                },
                'timestamp': datetime.now().isoformat(),
                'source': 'OpenSanctions (simulation)',
                'note': 'Données de démonstration - Module en développement'
            }
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"❌ Erreur get_sanctions_data: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # === API ÉCONOMIES ÉMERGENTES (BRICS) ===
    @indicators_bp.route('/api/brics')
    def get_brics_data():
        """Récupère les données des économies émergentes BRICS"""
        try:
            # Données de démonstration pour l'instant
            result = {
                'success': True,
                'brics_countries': {
                    'Brazil': {
                        'gdp_growth': 2.8,
                        'inflation': 4.1,
                        'currency': 'BRL'
                    },
                    'Russia': {
                        'gdp_growth': 3.5,
                        'inflation': 7.2,
                        'currency': 'RUB'
                    },
                    'India': {
                        'gdp_growth': 6.5,
                        'inflation': 5.1,
                        'currency': 'INR'
                    },
                    'China': {
                        'gdp_growth': 5.2,
                        'inflation': 0.3,
                        'currency': 'CNY'
                    },
                    'South_Africa': {
                        'gdp_growth': 0.9,
                        'inflation': 4.8,
                        'currency': 'ZAR'
                    }
                },
                'timestamp': datetime.now().isoformat(),
                'note': 'Données de démonstration - Module en développement'
            }
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"❌ Erreur get_brics_data: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # === API DASHBOARD COMPLET ===
    @indicators_bp.route('/api/dashboard')
    def get_international_dashboard():
        """Récupère toutes les données du dashboard international"""
        try:
            dashboard_data = {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'modules': {
                    'markets': 'active' if yfinance else 'inactive',
                    'macro': 'development',
                    'sanctions': 'development',
                    'brics': 'development'
                }
            }
            
            # Indices boursiers
            if yfinance:
                markets = yfinance.get_all_indices()
                if markets.get('success'):
                    dashboard_data['markets'] = markets['indices']
            
            # Données macro
            try:
                macro_response = get_macro_data()
                if hasattr(macro_response, 'json'):
                    macro_data = macro_response.json
                    if macro_data.get('success'):
                        dashboard_data['macro_data'] = macro_data['data']
            except:
                pass
            
            # Sanctions
            try:
                sanctions_response = get_sanctions_data()
                if hasattr(sanctions_response, 'json'):
                    sanctions_data = sanctions_response.json
                    if sanctions_data.get('success'):
                        dashboard_data['sanctions'] = sanctions_data['sanctions']
            except:
                pass
            
            # BRICS
            try:
                brics_response = get_brics_data()
                if hasattr(brics_response, 'json'):
                    brics_data = brics_response.json
                    if brics_data.get('success'):
                        dashboard_data['brics'] = brics_data['brics_countries']
            except:
                pass
            
            return jsonify(dashboard_data)
            
        except Exception as e:
            logger.error(f"❌ Erreur get_international_dashboard: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # === STATUT ===
    @indicators_bp.route('/api/status')
    def get_status():
        """Statut du système international"""
        return jsonify({
            'success': True,
            'system_status': 'operational',
            'data_sources': {
                'yfinance': 'available' if yfinance else 'unavailable',
                'world_bank': 'development',
                'open_sanctions': 'development',
                'brics_data': 'development'
            },
            'timestamp': datetime.now().isoformat(),
            'note': 'Dashboard international - Sources variées'
        })
    
    return indicators_bp
