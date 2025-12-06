# Flask/stock_routes.py
"""
Routes Flask pour la surveillance boursière avec yfinance
"""

from flask import Blueprint, jsonify, request
import logging
import yfinance as yf
from datetime import datetime, timedelta
import sqlite3
import os

logger = logging.getLogger(__name__)

stock_bp = Blueprint('stocks', __name__, url_prefix='/api/stocks')

def get_db_path_from_manager(db_manager):
    """Extrait le chemin de la base de données du db_manager"""
    # Vérifier différentes façons d'accéder au chemin
    if hasattr(db_manager, 'db_path'):
        return db_manager.db_path
    elif hasattr(db_manager, '_db_path'):
        return db_manager._db_path
    else:
        # Chemin par défaut
        instance_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'instance')
        return os.path.join(instance_dir, 'geopol.db')

def get_db_connection(db_manager):
    """Connexion à la base de données via db_manager"""
    db_path = get_db_path_from_manager(db_manager)
    
    # S'assurer que db_path n'est pas vide
    if not db_path:
        instance_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'instance')
        db_path = os.path.join(instance_dir, 'geopol.db')
    
    # S'assurer que le répertoire existe
    instance_dir = os.path.dirname(db_path)
    if instance_dir:  # Vérifier que le chemin n'est pas vide
        os.makedirs(instance_dir, exist_ok=True)
    else:
        # Utiliser un chemin par défaut
        instance_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'instance')
        os.makedirs(instance_dir, exist_ok=True)
        db_path = os.path.join(instance_dir, 'geopol.db')
    
    return sqlite3.connect(db_path)

def init_stock_table(db_manager):
    """Initialise la table de surveillance boursière"""
    try:
        conn = get_db_connection(db_manager)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_stock_monitors (
                symbol TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                active BOOLEAN DEFAULT 1
            )
        """)
        conn.commit()
        conn.close()
        logger.info("✅ Table user_stock_monitors initialisée")
    except Exception as e:
        logger.error(f"❌ Erreur initialisation table stock: {e}")

def register_stock_routes(app, db_manager):
    """Enregistre les routes de surveillance boursière"""
    
    # Configuration par défaut
    DEFAULT_INDICATORS = [
        {'symbol': 'SPY', 'name': 'S&P 500 ETF'},
        {'symbol': 'TLT', 'name': '20+ Year Treasury Bond ETF'},
        {'symbol': 'GLD', 'name': 'Gold ETF'}
    ]
    
    VIX_SYMBOL = '^VIX'
    
    @stock_bp.route('/config', methods=['GET'])
    def get_stock_config():
        """Récupère la configuration de surveillance boursière"""
        try:
            # Récupérer les indicateurs systémiques avec données actuelles
            system_indicators = []
            for indicator in DEFAULT_INDICATORS:
                try:
                    ticker = yf.Ticker(indicator['symbol'])
                    hist = ticker.history(period="2d")
                    if len(hist) >= 2:
                        current_price = hist['Close'].iloc[-1]
                        previous_price = hist['Close'].iloc[-2]
                        change = ((current_price - previous_price) / previous_price) * 100
                    else:
                        current_price = 0
                        change = 0
                    
                    system_indicators.append({
                        **indicator,
                        'current_price': float(current_price),
                        'current_change': float(change)
                    })
                except Exception as e:
                    logger.warning(f"Erreur récupération {indicator['symbol']}: {e}")
                    system_indicators.append({
                        **indicator,
                        'current_price': 0,
                        'current_change': 0
                    })
            
            # Récupérer les valeurs utilisateur
            conn = get_db_connection(db_manager)
            cur = conn.cursor()
            cur.execute("""
                SELECT symbol, name FROM user_stock_monitors 
                WHERE active = 1 ORDER BY created_at
            """)
            user_stocks = [{'symbol': row[0], 'name': row[1]} for row in cur.fetchall()]
            conn.close()
            
            return jsonify({
                'system_indicators': system_indicators,
                'user_stocks': user_stocks,
                'max_user_stocks': 5,
                'vix_symbol': VIX_SYMBOL
            })
            
        except Exception as e:
            logger.error(f"Erreur config boursière: {e}")
            return jsonify({'error': str(e)}), 500
    
    @stock_bp.route('/current', methods=['GET'])
    def get_current_stock_data():
        """Récupère les données boursières actuelles"""
        try:
            # Données des indicateurs systémiques
            system_data = []
            for indicator in DEFAULT_INDICATORS:
                try:
                    ticker = yf.Ticker(indicator['symbol'])
                    hist = ticker.history(period="2d")
                    if len(hist) >= 2:
                        price = float(hist['Close'].iloc[-1])
                        previous_price = float(hist['Close'].iloc[-2])
                        change = ((price - previous_price) / previous_price) * 100
                    else:
                        price = 0
                        change = 0
                    
                    system_data.append({
                        'symbol': indicator['symbol'],
                        'name': indicator['name'],
                        'price': price,
                        'change': change
                    })
                except Exception as e:
                    logger.warning(f"Erreur données {indicator['symbol']}: {e}")
                    system_data.append({
                        'symbol': indicator['symbol'],
                        'name': indicator['name'],
                        'price': 0,
                        'change': 0
                    })
            
            # Données VIX
            try:
                vix_ticker = yf.Ticker(VIX_SYMBOL)
                vix_hist = vix_ticker.history(period="1d")
                vix_value = float(vix_hist['Close'].iloc[-1]) if len(vix_hist) > 0 else 0
                
                # Classification du niveau de volatilité
                if vix_value > 30:
                    vix_level = 'high'
                    vix_desc = 'Volatilité élevée - marché stressé'
                elif vix_value > 20:
                    vix_level = 'medium'
                    vix_desc = 'Volatilité modérée'
                else:
                    vix_level = 'low'
                    vix_desc = 'Volatilité faible - marché calme'
                    
            except Exception as e:
                logger.warning(f"Erreur VIX: {e}")
                vix_value = 0
                vix_level = 'unknown'
                vix_desc = 'Données non disponibles'
            
            # Données utilisateur
            conn = get_db_connection(db_manager)
            cur = conn.cursor()
            cur.execute("""
                SELECT symbol, name FROM user_stock_monitors 
                WHERE active = 1 ORDER BY created_at
            """)
            user_symbols = [row[0] for row in cur.fetchall()]
            conn.close()
            
            user_data = []
            for symbol in user_symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(period="2d")
                    if len(hist) >= 2:
                        price = float(hist['Close'].iloc[-1])
                        previous_price = float(hist['Close'].iloc[-2])
                        change = ((price - previous_price) / previous_price) * 100
                        
                        # Récupérer le nom si disponible
                        info = ticker.info
                        name = info.get('longName', info.get('shortName', symbol))
                    else:
                        price = 0
                        change = 0
                        name = symbol
                    
                    user_data.append({
                        'symbol': symbol,
                        'name': name,
                        'price': price,
                        'change': change
                    })
                except Exception as e:
                    logger.warning(f"Erreur données utilisateur {symbol}: {e}")
                    user_data.append({
                        'symbol': symbol,
                        'name': symbol,
                        'price': 0,
                        'change': 0
                    })
            
            return jsonify({
                'timestamp': datetime.utcnow().isoformat(),
                'indicators': {
                    'system': system_data,
                    'vix': {
                        'symbol': VIX_SYMBOL,
                        'value': vix_value,
                        'level': vix_level,
                        'description': vix_desc
                    },
                    'user': user_data
                }
            })
            
        except Exception as e:
            logger.error(f"Erreur données boursières: {e}")
            return jsonify({'error': str(e)}), 500
    
    @stock_bp.route('/user-stocks', methods=['GET', 'POST'])
    def manage_user_stocks():
        """Gestion des valeurs boursières utilisateur"""
        try:
            if request.method == 'GET':
                conn = get_db_connection(db_manager)
                cur = conn.cursor()
                cur.execute("""
                    SELECT symbol, name, created_at FROM user_stock_monitors 
                    WHERE active = 1 ORDER BY created_at
                """)
                stocks = [{'symbol': row[0], 'name': row[1], 'created_at': row[2]} 
                         for row in cur.fetchall()]
                conn.close()
                
                return jsonify({'stocks': stocks})
            
            else:  # POST
                data = request.get_json()
                symbol = data.get('symbol', '').upper()
                name = data.get('name', '')
                
                if not symbol:
                    return jsonify({'error': 'Symbole requis'}), 400
                
                # Vérifier si le symbole existe
                try:
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    if not name:
                        name = info.get('longName', info.get('shortName', symbol))
                except Exception as e:
                    return jsonify({'error': f'Symbole invalide: {e}'}), 400
                
                # Vérifier la limite (5 valeurs max)
                conn = get_db_connection(db_manager)
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM user_stock_monitors WHERE active = 1")
                count = cur.fetchone()[0]
                
                if count >= 5:
                    conn.close()
                    return jsonify({'error': 'Limite de 5 valeurs atteinte'}), 400
                
                # Ajouter ou réactiver
                cur.execute("""
                    INSERT INTO user_stock_monitors (symbol, name)
                    VALUES (?, ?)
                    ON CONFLICT(symbol) DO UPDATE SET
                        active = 1,
                        name = excluded.name
                """, (symbol, name))
                
                conn.commit()
                conn.close()
                
                return jsonify({
                    'success': True,
                    'message': f'Valeur {symbol} ajoutée'
                })
                
        except Exception as e:
            logger.error(f"Erreur gestion valeurs utilisateur: {e}")
            return jsonify({'error': str(e)}), 500
    
    @stock_bp.route('/user-stocks/<symbol>', methods=['DELETE'])
    def remove_user_stock(symbol):
        """Supprime une valeur boursière utilisateur"""
        try:
            conn = get_db_connection(db_manager)
            cur = conn.cursor()
            cur.execute("""
                UPDATE user_stock_monitors 
                SET active = 0 
                WHERE symbol = ?
            """, (symbol.upper(),))
            
            if cur.rowcount == 0:
                conn.close()
                return jsonify({'error': 'Valeur non trouvée'}), 404
            
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True,
                'message': f'Valeur {symbol} supprimée'
            })
            
        except Exception as e:
            logger.error(f"Erreur suppression valeur {symbol}: {e}")
            return jsonify({'error': str(e)}), 500
    
    # Initialiser la table
    init_stock_table(db_manager)
    
    # Enregistrer le blueprint
    app.register_blueprint(stock_bp)
    
    logger.info("✅ Routes boursières enregistrées")
