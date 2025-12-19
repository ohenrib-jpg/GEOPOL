# routes_indicators.py - VERSION AVEC FACTORY FUNCTION POUR L'USINE
from flask import Blueprint, render_template, jsonify, request
import requests
import json
import os
from datetime import datetime, timedelta

def create_indicators_blueprint(db_manager=None):
    """Factory function pour créer le blueprint des indicateurs internationaux ET dashboard"""
    
    indicators_bp = Blueprint('indicators', __name__, url_prefix='/indicators')
    
    # ====================
    # ROUTES DE PAGES
    # ====================

    # 1. DASHBOARD UNIFIÉ (NOUVEAU - VERSION FINALE)
    @indicators_bp.route('/dashboard')
    def indicators_dashboard():
        return render_template('economic_dashboard_unified.html')

    # 2. Redirection pour l'ancienne route principale vers le dashboard unifié
    @indicators_bp.route('/')
    def indicators_main():
        # Rediriger vers le dashboard unifié
        from flask import redirect, url_for
        return redirect(url_for('indicators.indicators_dashboard'))

    # 3. INDICATEURS INTERNATIONAUX (CONSERVÉ pour compatibilité)
    @indicators_bp.route('/international')
    def indicators_international():
        # Rediriger vers le dashboard unifié avec onglet international
        from flask import redirect, url_for
        return redirect(url_for('indicators.indicators_dashboard') + '#international')
    
    # ====================
    # ROUTES API
    # ====================
    
    @indicators_bp.route('/api/indices')
    def get_all_indices():
        """Liste de tous les indices disponibles"""
        indices = {
            'categories': [
                {
                    'id': 'france',
                    'name': 'Indicateurs Français',
                    'indices': [
                        {'id': 'inflation_fr', 'name': 'Taux d\'inflation', 'source': 'INSEE'},
                        {'id': 'pib_fr', 'name': 'PIB trimestriel', 'source': 'INSEE'},
                        {'id': 'chomage_fr', 'name': 'Taux de chômage', 'source': 'DARES'}
                    ]
                },
                {
                    'id': 'international',
                    'name': 'Indicateurs Internationaux',
                    'indices': [
                        {'id': 'pib_mondial', 'name': 'PIB mondial', 'source': 'FMI'},
                        {'id': 'commerce_int', 'name': 'Commerce international', 'source': 'OMC'}
                    ]
                },
                {
                    'id': 'eurostat',
                    'name': 'Données Eurostat',
                    'indices': [
                        {'id': 'tps00003', 'name': 'Taux de chômage (EU)', 'dataset': 'tps00003'},
                        {'id': 'nama_10_gdp', 'name': 'PIB trimestriel (EU)', 'dataset': 'nama_10_gdp'},
                        {'id': 'prc_hicp_midx', 'name': 'Inflation HICP (EU)', 'dataset': 'prc_hicp_midx'}
                    ]
                }
            ]
        }
        return jsonify(indices)
    
    @indicators_bp.route('/api/dashboard')
    def get_dashboard_data():
        """Données pour le dashboard unifié - VERSION CORRIGÉE"""
        try:
            # ⚠️ AJOUTER les indicateurs manquants
            dashboard_data = {
                'status': 'success',
                'indicators': {
                    'tps00003': {
                        'name': 'Taux de chômage (EU)',
                        'value': 6.5,
                        'unit': '%',
                        'change_percent': -0.2,
                        'period': 'Nov 2024',
                        'source': 'Eurostat',
                        'reliability': 'official',
                        'category': 'employment',
                        'description': 'Taux de chômage harmonisé UE'
                    },
                        'nama_10_gdp': {
                        'name': 'PIB trimestriel (EU)',
                        'value': 0.3,
                        'unit': '%',
                        'change_percent': 0.1,
                        'period': 'Q3 2024',
                        'source': 'Eurostat',
                        'reliability': 'official',
                        'category': 'macro',
                        'description': 'Croissance du PIB zone euro'
                    },
                    'prc_hicp_midx': {
                        'name': 'Inflation HICP (EU)',
                        'value': 2.4,
                        'unit': '%',
                        'change_percent': -0.1,
                        'period': 'Nov 2024',
                        'source': 'Eurostat',
                        'reliability': 'official',
                        'category': 'prices',
                        'description': 'Inflation harmonisée zone euro'
                    },
                    'insee_inflation': {
                        'name': 'Inflation France',
                        'value': 2.1,
                        'unit': '%',
                        'change_percent': -0.3,
                        'period': 'Nov 2024',
                        'source': 'INSEE',
                        'reliability': 'official',
                        'category': 'prices',
                        'description': 'Inflation annuelle France'
                   },
                        'insee_pib': {
                        'name': 'PIB France',
                        'value': 0.2,
                        'unit': '%',
                        'change_percent': 0.0,
                        'period': 'Q3 2024',
                        'source': 'INSEE',
                        'reliability': 'official',
                        'category': 'macro',
                        'description': 'Croissance du PIB français'
                    },
                    'insee_chomage': {
                        'name': 'Chômage France',
                        'value': 7.4,
                        'unit': '%',
                        'change_percent': -0.1,
                        'period': 'Q3 2024',
                        'source': 'DARES',
                        'reliability': 'official',
                        'category': 'employment',
                        'description': 'Taux de chômage France'
                    }
                },
                'summary': {
                    'data_quality': 'good',
                    'france': {
                        'count': 3,
                        'last_update': datetime.now().isoformat(),
                        'selected': ['insee_inflation', 'insee_pib', 'insee_chomage']
                    },
                    'international': {
                        'count': 2,
                        'last_update': datetime.now().isoformat(),
                        'selected': ['pib_mondial', 'commerce_int']
                    },
                    'eurostat': {
                        'count': 3,
                        'last_update': datetime.now().isoformat(),
                        'selected': ['tps00003', 'nama_10_gdp', 'prc_hicp_midx']
                    }
                },
                'sources_status': {
                    'INSEE': 'operational',
                    'Eurostat': 'operational',
                    'BCE': 'operational',
                    'DARES': 'operational'
                },
                    'quick_stats': [
                    {'label': 'Indices actifs', 'value': 8, 'change': '+2', 'trend': 'up'},
                    {'label': 'Données chargées', 'value': 1245, 'change': '+45', 'trend': 'up'},
                    {'label': 'Mises à jour/jour', 'value': 12, 'change': '0', 'trend': 'stable'},
                    {'label': 'Sources actives', 'value': 4, 'change': '+1', 'trend': 'up'}
                ],
                'recent_updates': [
                    {'id': 'tps00003', 'name': 'Taux de chômage EU', 'updated': 'Il y a 2 heures', 'value': '6.5%'},
                    {'id': 'insee_inflation', 'name': 'Inflation France', 'updated': 'Il y a 1 jour', 'value': '2.1%'},
                    {'id': 'nama_10_gdp', 'name': 'PIB trimestriel (EU)', 'updated': 'Il y a 3 jours', 'value': '+0.3%'}
                ]
            }
        
            return jsonify(dashboard_data)
        
        except Exception as e:
            print(f"❌ Erreur dans /api/dashboard: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @indicators_bp.route('/api/settings', methods=['GET', 'POST'])
    def indicator_settings():
        """Gestion des paramètres"""
        if request.method == 'GET':
            return jsonify({
                'refresh_interval': 300,
                'default_view': 'chart',
                'eurostat_enabled': True,
                'notifications': True
            })
        else:
            data = request.json
            print("Paramètres reçus:", data)
            return jsonify({'status': 'success', 'message': 'Paramètres sauvegardés'})
    
    @indicators_bp.route('/api/eurostat/<dataset_code>')
    def get_eurostat_data(dataset_code):
        """Récupération données Eurostat"""
        try:
            url = f"https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/{dataset_code}?format=JSON&lang=FR"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return jsonify({
                    'dataset': dataset_code,
                    'values': data.get('value', {}),
                    'dimensions': data.get('dimension', {}),
                    'metadata': {'source': 'Eurostat'}
                })
            return jsonify({'error': f'Erreur {response.status_code}'}), 500
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    @indicators_bp.route('/api/selected-indices', methods=['GET', 'POST'])
    def manage_selected_indices():
        """Gestion des indices sélectionnés"""
        if request.method == 'GET':
            return jsonify({
                'france': ['inflation_fr', 'chomage_fr'],
                'international': ['pib_mondial'],
                'eurostat': ['tps00003', 'nama_10_gdp']
            })
        else:
            data = request.json
            print("Indices sélectionnés:", data)
            return jsonify({'status': 'success', 'message': 'Sauvegardé'})
    
    @indicators_bp.route('/api/test-indicator/<indicator_id>')
    def test_indicator(indicator_id):
        """Test d'un indicateur"""
        test_data = {
            'tps00003': {'value': 6.5, 'unit': '%', 'name': 'Taux de chômage (EU)'},
            'nama_10_gdp': {'value': 0.3, 'unit': '%', 'name': 'PIB trimestriel (EU)'},
            'inflation_fr': {'value': 2.1, 'unit': '%', 'name': 'Inflation France'},
            'pib_mondial': {'value': 3.2, 'unit': '%', 'name': 'PIB mondial'}
        }
        return jsonify(test_data.get(indicator_id, {'error': 'Non trouvé'}))

    # ======================================================================
    # NOUVELLES ROUTES POUR LE DASHBOARD UNIFIÉ
    # ======================================================================

    @indicators_bp.route('/api/quotes', methods=['POST'])
    def get_multiple_quotes():
        """Récupère les prix de plusieurs indices boursiers"""
        try:
            import yfinance as yf
            from datetime import datetime

            data = request.json
            symbols = data.get('symbols', [])

            if not symbols:
                return jsonify({
                    'success': False,
                    'error': 'Liste de symboles requise'
                }), 400

            quotes = []

            for symbol in symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    hist = ticker.history(period='5d')

                    if not hist.empty:
                        current_price = hist['Close'].iloc[-1]
                        previous_price = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
                        change = current_price - previous_price
                        change_percent = (change / previous_price) * 100 if previous_price > 0 else 0

                        quotes.append({
                            'symbol': symbol,
                            'name': info.get('shortName', symbol),
                            'price': float(current_price),
                            'change': float(change),
                            'changePercent': float(change_percent)
                        })

                except Exception as e:
                    print(f"⚠️ Erreur {symbol}: {e}")
                    quotes.append({
                        'symbol': symbol,
                        'name': symbol,
                        'price': 0,
                        'change': 0,
                        'changePercent': 0,
                        'error': str(e)
                    })

            return jsonify({
                'success': True,
                'quotes': quotes,
                'count': len(quotes)
            }), 200

        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @indicators_bp.route('/api/chart', methods=['GET'])
    def get_chart_data():
        """Récupère les données pour un graphique d'indice"""
        try:
            import yfinance as yf
            from datetime import datetime

            symbol = request.args.get('symbol')
            period = request.args.get('period', '6mo')

            if not symbol:
                return jsonify({
                    'success': False,
                    'error': 'Symbole requis'
                }), 400

            ticker = yf.Ticker(symbol)
            info = ticker.info
            hist = ticker.history(period=period)

            if hist.empty:
                return jsonify({
                    'success': False,
                    'error': f'Aucune donnée pour {symbol}'
                }), 404

            # Préparer les données pour Chart.js
            dates = [d.strftime('%Y-%m-%d') for d in hist.index]
            prices = hist['Close'].tolist()

            current_price = hist['Close'].iloc[-1]
            first_price = hist['Close'].iloc[0]
            change = current_price - first_price
            change_percent = (change / first_price) * 100 if first_price > 0 else 0

            return jsonify({
                'success': True,
                'symbol': symbol,
                'name': info.get('shortName', symbol),
                'dates': dates,
                'prices': prices,
                'current': float(current_price),
                'change': float(change_percent),
                'timestamp': datetime.utcnow().isoformat()
            }), 200

        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    return indicators_bp

# Pour la compatibilité avec l'ancien code si import direct
# (Optionnel - gardez si d'autres fichiers importent directement le blueprint)
indicators_bp = create_indicators_blueprint()