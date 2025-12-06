# Flask/routes_indicators_france.py
"""
Routes Flask pour les indicateurs économiques FRANÇAIS
Utilise le connecteur unifié (Eurostat + INSEE + yFinance)
"""

from flask import Blueprint, jsonify, request, render_template
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def create_france_indicators_blueprint(db_manager):
    """Crée le blueprint pour les indicateurs français"""
    
    indicators_bp = Blueprint('indicators_france', __name__, url_prefix='/indicators/france')
    
    # Initialiser les connecteurs
    from .eurostat_connector import EurostatConnector
    from .insee_scraper import INSEEScraper
    from .yfinance_connector import YFinanceConnector
    from .gini_scraper import GINIScraper
    
    eurostat = EurostatConnector()
    insee = INSEEScraper()
    yfinance = YFinanceConnector()
    gini = GINIScraper()
    
    # === PAGE PRINCIPALE INDICATEURS FRANÇAIS ===
    @indicators_bp.route('/')
    def france_indicators_page():
        """Page principale des indicateurs français"""
        return render_template('indicators_france_dashboard.html')
    
    # === API DONNÉES EUROSTAT ===
    @indicators_bp.route('/api/eurostat')
    def get_eurostat_data():
        """Récupère les données Eurostat pour la France"""
        try:
            # Indicateurs par défaut
            default_ids = ['gdp', 'unemployment', 'hicp', 'trade_balance', 'gini']
            result = eurostat.get_multiple_indicators(default_ids)
            
            # Ajouter GINI spécifique
            try:
                gini_data = gini.get_gini_data()
                if gini_data.get('success'):
                    result['indicators']['gini'] = gini_data
            except Exception as e:
                logger.error(f"Erreur récupération GINI: {e}")
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"❌ Erreur get_eurostat_data: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # === API DONNÉES INSEE ===
    @indicators_bp.route('/api/insee')
    def get_insee_data():
        """Récupère les données INSEE par scraping"""
        try:
            result = insee.get_indicators()
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"❌ Erreur get_insee_data: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # === API MARCHÉS FINANCIERS FRANÇAIS ===
    @indicators_bp.route('/api/markets')
    def get_french_markets():
        """Récupère les indices boursiers français"""
        try:
            # Focus sur le CAC 40
            cac40_data = yfinance.get_index_data('^FCHI')
            
            result = {
                'success': True,
                'markets': {
                    '^FCHI': cac40_data
                },
                'timestamp': datetime.now().isoformat()
            }
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"❌ Erreur get_french_markets: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # === API DONNÉES HISTORIQUES ===
    @indicators_bp.route('/api/historical/<symbol>')
    def get_historical_data(symbol):
        """Données historiques d'un symbole"""
        try:
            period = request.args.get('period', '6mo')
            result = yfinance.get_historical_data(symbol, period)
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"❌ Erreur get_historical_data: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # === API DONNÉES COMPLÈTES ===
    @indicators_bp.route('/api/dashboard')
    def get_france_dashboard():
        """Récupère toutes les données du dashboard français"""
        try:
            # Eurostat
            eurostat_data = eurostat.get_multiple_indicators(['gdp', 'unemployment', 'hicp', 'trade_balance'])
            
            # INSEE
            insee_data = insee.get_indicators()
            
            # Marchés
            markets_data = yfinance.get_all_indices()
            
            # GINI
            gini_data = gini.get_gini_data()
            
            # Combiner toutes les données
            result = {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'sources': {
                    'eurostat': 'operational' if eurostat_data.get('success') else 'error',
                    'insee': 'operational' if insee_data.get('success') else 'error',
                    'markets': 'operational' if markets_data.get('success') else 'error',
                    'gini': 'operational' if gini_data.get('success') else 'error'
                },
                'indicators': {},
                'markets': markets_data if markets_data.get('success') else {},
                'summary': {
                    'total_indicators': 0,
                    'data_quality': 'limited'
                }
            }
            
            # Ajouter les indicateurs Eurostat
            if eurostat_data.get('success'):
                for key, indicator in eurostat_data['indicators'].items():
                    if indicator.get('success'):
                        result['indicators'][f'eurostat_{key}'] = {
                            'id': f'eurostat_{key}',
                            'name': indicator['indicator_name'],
                            'value': indicator['current_value'],
                            'unit': indicator['unit'],
                            'period': indicator['period'],
                            'change_percent': indicator['change_percent'],
                            'source': 'Eurostat (officiel)',
                            'category': indicator['category'],
                            'reliability': 'official',
                            'description': indicator['description']
                        }
            
            # Ajouter les indicateurs INSEE
            if insee_data.get('success'):
                for key, indicator in insee_data['indicators'].items():
                    result['indicators'][f'insee_{key}'] = {
                        'id': f'insee_{key}',
                        'name': indicator['name'],
                        'value': indicator['value'],
                        'unit': indicator['unit'],
                        'period': indicator['period'],
                        'change_percent': indicator.get('change_percent', 0),
                        'source': 'INSEE (scraping)',
                        'category': 'macro',
                        'reliability': 'scraped',
                        'description': f"Indicateur INSEE: {indicator['name']}"
                    }
            
            # Ajouter GINI
            if gini_data.get('success'):
                result['indicators']['eurostat_gini'] = {
                    'id': 'eurostat_gini',
                    'name': gini_data['name'],
                    'value': gini_data['value'],
                    'unit': gini_data['unit'],
                    'period': gini_data['period'],
                    'change_percent': gini_data['change_percent'],
                    'source': gini_data['source'],
                    'category': gini_data['category'],
                    'reliability': gini_data['reliability'],
                    'description': gini_data['description']
                }
            
            # Calculer le résumé
            total_indicators = len(result['indicators'])
            official_count = sum(1 for ind in result['indicators'].values() if ind['reliability'] == 'official')
            
            if total_indicators > 0:
                if official_count / total_indicators >= 0.7:
                    result['summary']['data_quality'] = 'excellent'
                elif official_count / total_indicators >= 0.5:
                    result['summary']['data_quality'] = 'good'
                else:
                    result['summary']['data_quality'] = 'acceptable'
            
            result['summary']['total_indicators'] = total_indicators
            
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"❌ Erreur get_france_dashboard: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # === RAFRAÎCHISSEMENT ===
    @indicators_bp.route('/api/refresh', methods=['POST'])
    def force_refresh():
        """Force le rafraîchissement des données françaises"""
        try:
            logger.info("🔄 Rafraîchissement forcé données françaises")
            
            # Rafraîchir INSEE
            try:
                insee.force_refresh()
            except Exception as e:
                logger.error(f"Erreur refresh INSEE: {e}")
            
            # Rafraîchir GINI
            try:
                gini.force_refresh()
            except Exception as e:
                logger.error(f"Erreur refresh GINI: {e}")
            
            # Retourner les nouvelles données
            return get_france_dashboard()
            
        except Exception as e:
            logger.error(f"❌ Erreur force_refresh: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    return indicators_bp
