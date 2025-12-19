# Flask/routes_stocks_portfolio.py
"""
Routes Flask pour le suivi boursier personnalisé
Gestion des portfolios sectoriels personnalisés (max 4 secteurs, 5 valeurs/secteur)
"""

from flask import Blueprint, jsonify, request
import logging
import yfinance as yf
from datetime import datetime
import json

logger = logging.getLogger(__name__)


def create_stocks_portfolio_blueprint(db_manager):
    """Crée le blueprint pour le suivi boursier personnalisé"""

    stocks_bp = Blueprint('stocks_portfolio', __name__, url_prefix='/api/stocks')

    # =========================================================================
    # INDICATEURS FIXES (VIX, Or, Pétrole, Uranium)
    # =========================================================================

    @stocks_bp.route('/fixed-indicators', methods=['GET'])
    def get_fixed_indicators():
        """Récupère les 4 indicateurs fixes: VIX, Or, Pétrole, Uranium"""
        try:
            # Symboles des indicateurs fixes
            symbols = {
                'vix': '^VIX',           # Volatilité
                'gold': 'GC=F',          # Or (Gold Futures)
                'oil': 'CL=F',           # Pétrole WTI (Crude Oil Futures)
                'uranium': 'URA'         # ETF Uranium
            }

            result = {}

            for key, symbol in symbols.items():
                try:
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    hist = ticker.history(period='5d')

                    if not hist.empty:
                        current_price = hist['Close'].iloc[-1]
                        previous_price = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
                        change_percent = ((current_price - previous_price) / previous_price) * 100 if previous_price > 0 else 0

                        result[key] = {
                            'symbol': symbol,
                            'name': info.get('shortName', symbol),
                            'price': float(current_price),
                            'change': float(current_price - previous_price),
                            'changePercent': float(change_percent),
                            'timestamp': datetime.utcnow().isoformat()
                        }
                    else:
                        result[key] = None

                except Exception as e:
                    logger.warning(f"⚠️ Erreur récupération {symbol}: {e}")
                    result[key] = None

            return jsonify({
                'success': True,
                **result
            }), 200

        except Exception as e:
            logger.error(f"❌ Erreur indicateurs fixes: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    # =========================================================================
    # GESTION DES SECTEURS PERSONNALISÉS
    # =========================================================================

    @stocks_bp.route('/portfolios/sectors', methods=['GET'])
    def get_sectors():
        """Liste tous les secteurs configurés par l'utilisateur"""
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()

            cursor.execute('''
                SELECT id, sector_name, sector_order, stock_symbols, created_at, updated_at
                FROM user_stock_portfolios
                ORDER BY sector_order ASC
            ''')

            rows = cursor.fetchall()
            conn.close()

            sectors = []
            for row in rows:
                sectors.append({
                    'id': row[0],
                    'sector_name': row[1],
                    'sector_order': row[2],
                    'stock_symbols': row[3],
                    'created_at': row[4],
                    'updated_at': row[5]
                })

            return jsonify({
                'success': True,
                'sectors': sectors,
                'count': len(sectors)
            }), 200

        except Exception as e:
            logger.error(f"❌ Erreur récupération secteurs: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @stocks_bp.route('/portfolios/sectors', methods=['POST'])
    def create_sector():
        """Crée un nouveau secteur (max 4)"""
        try:
            data = request.json
            sector_name = data.get('sector_name')
            stock_symbols = data.get('stock_symbols')  # JSON string

            if not sector_name:
                return jsonify({
                    'success': False,
                    'error': 'Le nom du secteur est requis'
                }), 400

            # Vérifier le nombre de secteurs existants
            conn = db_manager.get_connection()
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*) FROM user_stock_portfolios')
            count = cursor.fetchone()[0]

            if count >= 4:
                conn.close()
                return jsonify({
                    'success': False,
                    'error': 'Maximum 4 secteurs autorisés'
                }), 400

            # Déterminer l'ordre du nouveau secteur
            cursor.execute('SELECT COALESCE(MAX(sector_order), 0) FROM user_stock_portfolios')
            max_order = cursor.fetchone()[0]
            new_order = max_order + 1

            # Insérer le nouveau secteur
            now = datetime.utcnow().isoformat()

            cursor.execute('''
                INSERT INTO user_stock_portfolios
                (user_id, sector_name, sector_order, stock_symbols, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (1, sector_name, new_order, stock_symbols, now, now))

            conn.commit()
            sector_id = cursor.lastrowid
            conn.close()

            logger.info(f"✅ Secteur créé: {sector_name} (ID: {sector_id})")

            return jsonify({
                'success': True,
                'sector_id': sector_id,
                'message': 'Secteur créé avec succès'
            }), 201

        except Exception as e:
            logger.error(f"❌ Erreur création secteur: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @stocks_bp.route('/portfolios/sectors/<int:sector_id>', methods=['PUT'])
    def update_sector(sector_id):
        """Met à jour un secteur existant"""
        try:
            data = request.json
            sector_name = data.get('sector_name')
            stock_symbols = data.get('stock_symbols')

            if not sector_name:
                return jsonify({
                    'success': False,
                    'error': 'Le nom du secteur est requis'
                }), 400

            conn = db_manager.get_connection()
            cursor = conn.cursor()

            now = datetime.utcnow().isoformat()

            cursor.execute('''
                UPDATE user_stock_portfolios
                SET sector_name = ?, stock_symbols = ?, updated_at = ?
                WHERE id = ?
            ''', (sector_name, stock_symbols, now, sector_id))

            conn.commit()
            conn.close()

            logger.info(f"✅ Secteur mis à jour: {sector_name} (ID: {sector_id})")

            return jsonify({
                'success': True,
                'message': 'Secteur mis à jour avec succès'
            }), 200

        except Exception as e:
            logger.error(f"❌ Erreur mise à jour secteur: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @stocks_bp.route('/portfolios/sectors/<int:sector_id>', methods=['DELETE'])
    def delete_sector(sector_id):
        """Supprime un secteur"""
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()

            cursor.execute('DELETE FROM user_stock_portfolios WHERE id = ?', (sector_id,))

            conn.commit()
            conn.close()

            logger.info(f"✅ Secteur supprimé (ID: {sector_id})")

            return jsonify({
                'success': True,
                'message': 'Secteur supprimé avec succès'
            }), 200

        except Exception as e:
            logger.error(f"❌ Erreur suppression secteur: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    # =========================================================================
    # DONNÉES BOURSIÈRES (yFinance)
    # =========================================================================

    @stocks_bp.route('/quote/<symbol>', methods=['GET'])
    def get_quote(symbol):
        """Récupère le prix d'une valeur boursière"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            hist = ticker.history(period='5d')

            if hist.empty:
                return jsonify({
                    'success': False,
                    'error': f'Aucune donnée pour {symbol}'
                }), 404

            current_price = hist['Close'].iloc[-1]
            previous_price = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
            change = current_price - previous_price
            change_percent = (change / previous_price) * 100 if previous_price > 0 else 0

            return jsonify({
                'success': True,
                'symbol': symbol.upper(),
                'name': info.get('shortName', symbol),
                'price': float(current_price),
                'change': float(change),
                'changePercent': float(change_percent),
                'volume': int(info.get('volume', 0)),
                'marketCap': info.get('marketCap'),
                'timestamp': datetime.utcnow().isoformat()
            }), 200

        except Exception as e:
            logger.error(f"❌ Erreur quote {symbol}: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @stocks_bp.route('/quotes/multiple', methods=['POST'])
    def get_multiple_quotes():
        """Récupère les prix de plusieurs valeurs"""
        try:
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
                            'symbol': symbol.upper(),
                            'name': info.get('shortName', symbol),
                            'price': float(current_price),
                            'change': float(change),
                            'changePercent': float(change_percent),
                            'volume': int(info.get('volume', 0))
                        })

                except Exception as e:
                    logger.warning(f"⚠️ Erreur {symbol}: {e}")
                    quotes.append({
                        'symbol': symbol.upper(),
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
            logger.error(f"❌ Erreur quotes multiples: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    # =========================================================================
    # ALERTES BOURSIÈRES (Intégration avec système d'alertes existant)
    # =========================================================================

    @stocks_bp.route('/alerts', methods=['GET'])
    def get_stock_alerts():
        """Liste toutes les alertes boursières actives"""
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()

            # Requête pour récupérer les alertes de type 'stock'
            # (nécessite que la table alerts ait été étendue avec alert_type et stock_symbol)
            cursor.execute('''
                SELECT id, stock_symbol, condition, threshold, active, created_at
                FROM stock_alerts
                ORDER BY created_at DESC
            ''')

            rows = cursor.fetchall()
            conn.close()

            alerts = []
            for row in rows:
                alerts.append({
                    'id': row[0],
                    'stock_symbol': row[1],
                    'condition': row[2],
                    'threshold': row[3],
                    'active': bool(row[4]),
                    'created_at': row[5]
                })

            return jsonify({
                'success': True,
                'alerts': alerts,
                'count': len(alerts)
            }), 200

        except Exception as e:
            logger.error(f"❌ Erreur récupération alertes: {e}")
            # Si la table n'existe pas encore, retourner une liste vide
            return jsonify({
                'success': True,
                'alerts': [],
                'count': 0
            }), 200

    @stocks_bp.route('/alerts', methods=['POST'])
    def create_stock_alert():
        """Crée une nouvelle alerte boursière"""
        try:
            data = request.json
            stock_symbol = data.get('stock_symbol')
            condition = data.get('condition')  # 'above', 'below', 'change_percent'
            threshold = data.get('threshold')

            if not all([stock_symbol, condition, threshold]):
                return jsonify({
                    'success': False,
                    'error': 'stock_symbol, condition et threshold requis'
                }), 400

            conn = db_manager.get_connection()
            cursor = conn.cursor()

            now = datetime.utcnow().isoformat()

            cursor.execute('''
                INSERT INTO stock_alerts
                (stock_symbol, condition, threshold, active, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (stock_symbol.upper(), condition, threshold, 1, now))

            conn.commit()
            alert_id = cursor.lastrowid
            conn.close()

            logger.info(f"✅ Alerte créée: {stock_symbol} {condition} {threshold}")

            return jsonify({
                'success': True,
                'alert_id': alert_id,
                'message': 'Alerte créée avec succès'
            }), 201

        except Exception as e:
            logger.error(f"❌ Erreur création alerte: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @stocks_bp.route('/alerts/<int:alert_id>', methods=['DELETE'])
    def delete_stock_alert(alert_id):
        """Supprime une alerte boursière"""
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()

            cursor.execute('DELETE FROM stock_alerts WHERE id = ?', (alert_id,))

            conn.commit()
            conn.close()

            logger.info(f"✅ Alerte supprimée (ID: {alert_id})")

            return jsonify({
                'success': True,
                'message': 'Alerte supprimée avec succès'
            }), 200

        except Exception as e:
            logger.error(f"❌ Erreur suppression alerte: {e}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    # =========================================================================
    # HEALTH CHECK
    # =========================================================================

    @stocks_bp.route('/health', methods=['GET'])
    def health_check():
        """Vérification de l'état du service"""
        return jsonify({
            'success': True,
            'service': 'Stocks Portfolio API',
            'status': 'operational',
            'features': [
                'Fixed Indicators (VIX, Gold, Oil, Uranium)',
                'Custom Sectors (max 4)',
                'Stock Quotes (yFinance)',
                'Stock Alerts Integration'
            ]
        }), 200

    return stocks_bp
