# Flask/custom_tracking/routes.py - VERSION CORRIGÉE
"""
Routes pour le suivi personnalisé de valeurs financières avec alertes
"""

from flask import Blueprint, jsonify, request, render_template
from datetime import datetime, timedelta
import json
import logging
import yfinance as yf
import threading
import time

logger = logging.getLogger(__name__)

def create_custom_tracking_blueprint(db_manager):
    """Crée le blueprint pour le suivi personnalisé"""
    
    weak_bp = Blueprint('financial_tracking', __name__)
    
    # Variables pour les alertes en temps réel
    active_alerts = {}
    notification_list = []
    
    # ===============================================
    # FONCTIONS UTILITAIRES - DÉFINIES EN PREMIER
    # ===============================================
    
    def init_tracking_tables():
        """Initialise les tables de suivi"""
        conn = db_manager.get_connection()
        cur = conn.cursor()
        
        # Table des instruments suivis
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tracked_instruments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                description TEXT,
                alert_enabled BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table des alertes
        cur.execute("""
            CREATE TABLE IF NOT EXISTS price_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                instrument_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                condition TEXT NOT NULL,
                value REAL NOT NULL,
                threshold_percent REAL DEFAULT 5.0,
                timeframe_minutes INTEGER DEFAULT 60,
                active BOOLEAN DEFAULT 1,
                notification_type TEXT DEFAULT 'popup',
                last_triggered DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (instrument_id) REFERENCES tracked_instruments(id) ON DELETE CASCADE
            )
        """)
        
        # Table des notifications
        cur.execute("""
            CREATE TABLE IF NOT EXISTS price_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id INTEGER,
                instrument_id INTEGER,
                message TEXT NOT NULL,
                notification_type TEXT DEFAULT 'popup',
                severity TEXT DEFAULT 'info',
                read BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (alert_id) REFERENCES price_alerts(id) ON DELETE SET NULL,
                FOREIGN KEY (instrument_id) REFERENCES tracked_instruments(id) ON DELETE CASCADE
            )
        """)
        
        # Table des données historiques
        cur.execute("""
            CREATE TABLE IF NOT EXISTS instrument_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                instrument_id INTEGER NOT NULL,
                price REAL NOT NULL,
                change REAL,
                change_percent REAL,
                volume INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (instrument_id) REFERENCES tracked_instruments(id) ON DELETE CASCADE
            )
        """)
        
        # Index pour les performances
        cur.execute("CREATE INDEX IF NOT EXISTS idx_instruments_symbol ON tracked_instruments(symbol)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_alerts_instrument ON price_alerts(instrument_id)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_alerts_active ON price_alerts(active)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_notifications_read ON price_notifications(read, created_at)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_history_instrument_time ON instrument_history(instrument_id, timestamp)")
        
        conn.commit()
        conn.close()
        
        logger.info("✅ Tables de suivi personnalisé initialisées")
    
    def get_all_instruments():
        """Récupère tous les instruments suivis"""
        conn = db_manager.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM tracked_instruments ORDER BY created_at DESC")
        rows = cur.fetchall()
        conn.close()
        
        instruments = []
        for row in rows:
            instruments.append({
                'id': row[0],
                'symbol': row[1],
                'name': row[2],
                'type': row[3],
                'description': row[4],
                'alert_enabled': bool(row[5]),
                'created_at': row[6],
                'last_updated': row[7]
            })
        return instruments
    
    def get_instrument_by_symbol(symbol):
        """Récupère un instrument par son symbole"""
        conn = db_manager.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM tracked_instruments WHERE symbol = ?", (symbol,))
        row = cur.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'symbol': row[1],
                'name': row[2],
                'type': row[3],
                'description': row[4],
                'alert_enabled': bool(row[5]),
                'created_at': row[6],
                'last_updated': row[7]
            }
        return None
    
    def get_instrument_by_id(instrument_id):
        """Récupère un instrument par son ID"""
        conn = db_manager.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM tracked_instruments WHERE id = ?", (instrument_id,))
        row = cur.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'symbol': row[1],
                'name': row[2],
                'type': row[3],
                'description': row[4],
                'alert_enabled': bool(row[5]),
                'created_at': row[6],
                'last_updated': row[7]
            }
        return None
    
    def add_instrument_to_db(instrument_data):
        """Ajoute un instrument à la base de données"""
        conn = db_manager.get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO tracked_instruments (symbol, name, type, description, alert_enabled, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            instrument_data['symbol'],
            instrument_data['name'],
            instrument_data['type'],
            instrument_data.get('description', ''),
            instrument_data.get('alert_enabled', True),
            instrument_data.get('created_at', datetime.now().isoformat())
        ))
        instrument_id = cur.lastrowid
        conn.commit()
        conn.close()
        return instrument_id
    
    def delete_instrument_from_db(instrument_id):
        """Supprime un instrument"""
        conn = db_manager.get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM tracked_instruments WHERE id = ?", (instrument_id,))
        success = cur.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
    def get_alerts_for_instrument(instrument_id):
        """Récupère les alertes d'un instrument"""
        conn = db_manager.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM price_alerts WHERE instrument_id = ? ORDER BY created_at DESC", (instrument_id,))
        rows = cur.fetchall()
        conn.close()
        
        alerts = []
        for row in rows:
            alerts.append({
                'id': row[0],
                'instrument_id': row[1],
                'name': row[2],
                'condition': row[3],
                'value': row[4],
                'threshold_percent': row[5],
                'timeframe_minutes': row[6],
                'active': bool(row[7]),
                'notification_type': row[8],
                'last_triggered': row[9],
                'created_at': row[10]
            })
        return alerts
    
    def get_active_alerts_for_instrument(instrument_id):
        """Récupère les alertes actives d'un instrument"""
        conn = db_manager.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM price_alerts WHERE instrument_id = ? AND active = 1 ORDER BY created_at DESC", (instrument_id,))
        rows = cur.fetchall()
        conn.close()
        
        alerts = []
        for row in rows:
            alerts.append({
                'id': row[0],
                'instrument_id': row[1],
                'name': row[2],
                'condition': row[3],
                'value': row[4],
                'threshold_percent': row[5],
                'timeframe_minutes': row[6],
                'active': bool(row[7]),
                'notification_type': row[8],
                'last_triggered': row[9],
                'created_at': row[10]
            })
        return alerts
    
    def add_alert_to_db(alert_data):
        """Ajoute une alerte à la base de données"""
        conn = db_manager.get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO price_alerts (instrument_id, name, condition, value, threshold_percent, timeframe_minutes, active, notification_type, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            alert_data['instrument_id'],
            alert_data['name'],
            alert_data['condition'],
            alert_data['value'],
            alert_data.get('threshold_percent', 5.0),
            alert_data.get('timeframe_minutes', 60),
            alert_data.get('active', True),
            alert_data.get('notification_type', 'popup'),
            alert_data.get('created_at', datetime.now().isoformat())
        ))
        alert_id = cur.lastrowid
        conn.commit()
        conn.close()
        return alert_id
    
    def delete_alert_from_db(alert_id):
        """Supprime une alerte"""
        conn = db_manager.get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM price_alerts WHERE id = ?", (alert_id,))
        success = cur.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
    def get_instrument_data(symbol):
        """Récupère les données d'un instrument via yfinance"""
        try:
            ticker = yf.Ticker(symbol)
            
            # Données actuelles
            hist = ticker.history(period="2d")
            if len(hist) < 2:
                return None
            
            current_price = float(hist['Close'].iloc[-1])
            previous_price = float(hist['Close'].iloc[-2])
            change = current_price - previous_price
            change_percent = (change / previous_price) * 100
            
            # Informations générales
            info = ticker.info
            market_cap = info.get('marketCap')
            volume = info.get('volume')
            
            return {
                'current_price': round(current_price, 2),
                'previous_price': round(previous_price, 2),
                'change': round(change, 2),
                'change_percent': round(change_percent, 2),
                'volume': volume,
                'market_cap': market_cap,
                'currency': info.get('currency', 'USD'),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Erreur get_instrument_data pour {symbol}: {e}")
            return None
    
    def check_alert_condition(alert, data):
        """Vérifie si une condition d'alerte est remplie"""
        if alert['condition'] == 'above':
            return data['current_price'] > alert['value']
        elif alert['condition'] == 'below':
            return data['current_price'] < alert['value']
        elif alert['condition'] == 'change_up':
            return data['change_percent'] > alert['threshold_percent']
        elif alert['condition'] == 'change_down':
            return data['change_percent'] < -alert['threshold_percent']
        return False
    
    def create_notification(notification_data):
        """Crée une notification"""
        conn = db_manager.get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO price_notifications (alert_id, instrument_id, message, notification_type, severity, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            notification_data.get('alert_id'),
            notification_data.get('instrument_id'),
            notification_data['message'],
            notification_data.get('notification_type', 'popup'),
            notification_data.get('severity', 'info'),
            datetime.now().isoformat()
        ))
        notification_id = cur.lastrowid
        conn.commit()
        conn.close()
        
        # Ajouter à la liste en mémoire pour affichage immédiat
        notification_list.append({
            'id': notification_id,
            'message': notification_data['message'],
            'severity': notification_data.get('severity', 'info'),
            'read': False,
            'timestamp': datetime.now().isoformat()
        })
        
        return notification_id
    
    def get_recent_notifications(limit=50):
        """Récupère les notifications récentes"""
        conn = db_manager.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT n.*, i.symbol, i.name 
            FROM price_notifications n
            LEFT JOIN tracked_instruments i ON n.instrument_id = i.id
            ORDER BY n.created_at DESC
            LIMIT ?
        """, (limit,))
        rows = cur.fetchall()
        conn.close()
        
        notifications = []
        for row in rows:
            notifications.append({
                'id': row[0],
                'alert_id': row[1],
                'instrument_id': row[2],
                'message': row[3],
                'notification_type': row[4],
                'severity': row[5],
                'read': bool(row[6]),
                'created_at': row[7],
                'symbol': row[8],
                'instrument_name': row[9]
            })
        
        # Ajouter les notifications en mémoire (non encore persistées)
        for notif in notification_list[:10]:  # Limiter aux 10 plus récentes
            notifications.insert(0, notif)
        
        return notifications
    
    def mark_notification_as_read(notification_id):
        """Marque une notification comme lue"""
        conn = db_manager.get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE price_notifications SET read = 1 WHERE id = ?", (notification_id,))
        success = cur.rowcount > 0
        conn.commit()
        conn.close()
        return success
    
    def update_alert_last_triggered(alert_id):
        """Met à jour la date de dernier déclenchement d'une alerte"""
        conn = db_manager.get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE price_alerts SET last_triggered = ? WHERE id = ?", 
                   (datetime.now().isoformat(), alert_id))
        conn.commit()
        conn.close()
    
    def start_monitoring_instrument(instrument_id):
        """Démarre le monitoring d'un instrument"""
        if instrument_id not in active_alerts:
            active_alerts[instrument_id] = True
            logger.info(f"Monitoring démarré pour l'instrument {instrument_id}")
    
    def check_all_alerts():
        """Vérifie toutes les alertes actives"""
        triggered = []
        
        try:
            # Récupérer tous les instruments avec alertes actives
            conn = db_manager.get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT i.*, a.* 
                FROM tracked_instruments i
                JOIN price_alerts a ON i.id = a.instrument_id
                WHERE a.active = 1 AND i.alert_enabled = 1
            """)
            rows = cur.fetchall()
            conn.close()
            
            for row in rows:
                try:
                    instrument = {
                        'id': row[0],
                        'symbol': row[1],
                        'name': row[2]
                    }
                    
                    alert = {
                        'id': row[8],
                        'name': row[10],
                        'condition': row[11],
                        'value': row[12],
                        'threshold_percent': row[13],
                        'notification_type': row[16]
                    }
                    
                    # Récupérer les données actuelles
                    data = get_instrument_data(instrument['symbol'])
                    if not data:
                        continue
                    
                    # Vérifier la condition
                    is_triggered = check_alert_condition(alert, data)
                    
                    if is_triggered:
                        # Créer une notification
                        message = f"{instrument['name']} ({instrument['symbol']}): {alert['name']}"
                        
                        if alert['condition'] == 'above':
                            message += f" - Dépasse {alert['value']} (actuel: {data['current_price']})"
                        elif alert['condition'] == 'below':
                            message += f" - Descend sous {alert['value']} (actuel: {data['current_price']})"
                        elif alert['condition'] == 'change_up':
                            message += f" - Hausse de {data['change_percent']:.1f}% (> {alert['threshold_percent']}%)"
                        elif alert['condition'] == 'change_down':
                            message += f" - Baisse de {abs(data['change_percent']):.1f}% (> {alert['threshold_percent']}%)"
                        
                        # Enregistrer la notification
                        notification_id = create_notification({
                            'alert_id': alert['id'],
                            'instrument_id': instrument['id'],
                            'message': message,
                            'notification_type': alert['notification_type'],
                            'severity': 'warning'
                        })
                        
                        # Mettre à jour la date de déclenchement
                        update_alert_last_triggered(alert['id'])
                        
                        triggered.append({
                            'instrument': instrument['name'],
                            'symbol': instrument['symbol'],
                            'alert': alert['name'],
                            'message': message,
                            'notification_id': notification_id
                        })
                        
                except Exception as e:
                    logger.error(f"Erreur vérification alerte: {e}")
                    continue
            
            return triggered
            
        except Exception as e:
            logger.error(f"Erreur dans check_all_alerts: {e}")
            return []
    
    # Initialiser les tables maintenant (après leur définition)
    init_tracking_tables()
    
    # ===============================================
    # ROUTES API - APRÈS LES FONCTIONS UTILITAIRES
    # ===============================================
    
    @weak_bp.route('/api/custom-tracking/instruments')
    def get_tracked_instruments():
        """Récupère tous les instruments suivis"""
        try:
            instruments = get_all_instruments()
            return jsonify({
                'success': True,
                'instruments': instruments,
                'total': len(instruments)
            })
        except Exception as e:
            logger.error(f"Erreur get_tracked_instruments: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @weak_bp.route('/api/custom-tracking/instruments', methods=['POST'])
    def add_instrument():
        """Ajoute un nouvel instrument à suivre"""
        try:
            data = request.get_json()
            
            # Validation
            required_fields = ['symbol', 'name', 'type']
            for field in required_fields:
                if field not in data:
                    return jsonify({'success': False, 'error': f'Champ manquant: {field}'}), 400
            
            # Vérifier si l'instrument existe déjà
            existing = get_instrument_by_symbol(data['symbol'])
            if existing:
                return jsonify({'success': False, 'error': 'Instrument déjà suivi'}), 400
            
            # Ajouter l'instrument
            instrument_id = add_instrument_to_db({
                'symbol': data['symbol'].upper(),
                'name': data['name'],
                'type': data['type'],  # 'stock', 'index', 'currency', 'commodity', 'crypto'
                'description': data.get('description', ''),
                'alert_enabled': data.get('alert_enabled', True),
                'created_at': datetime.now().isoformat()
            })
            
            # Récupérer les données initiales
            initial_data = get_instrument_data(data['symbol'])
            
            return jsonify({
                'success': True,
                'instrument_id': instrument_id,
                'initial_data': initial_data
            })
        except Exception as e:
            logger.error(f"Erreur add_instrument: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @weak_bp.route('/api/custom-tracking/instruments/<int:instrument_id>', methods=['DELETE'])
    def delete_instrument(instrument_id):
        """Supprime un instrument"""
        try:
            success = delete_instrument_from_db(instrument_id)
            if success:
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error': 'Instrument non trouvé'}), 404
        except Exception as e:
            logger.error(f"Erreur delete_instrument: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @weak_bp.route('/api/custom-tracking/instruments/<int:instrument_id>/alerts')
    def get_instrument_alerts(instrument_id):
        """Récupère les alertes d'un instrument"""
        try:
            alerts = get_alerts_for_instrument(instrument_id)
            return jsonify({
                'success': True,
                'alerts': alerts,
                'instrument_id': instrument_id
            })
        except Exception as e:
            logger.error(f"Erreur get_instrument_alerts: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @weak_bp.route('/api/custom-tracking/alerts', methods=['POST'])
    def add_alert():
        """Ajoute une nouvelle alerte"""
        try:
            data = request.get_json()
            
            # Validation
            required_fields = ['instrument_id', 'name', 'condition', 'value']
            for field in required_fields:
                if field not in data:
                    return jsonify({'success': False, 'error': f'Champ manquant: {field}'}), 400
            
            # Vérifier que l'instrument existe
            instrument = get_instrument_by_id(data['instrument_id'])
            if not instrument:
                return jsonify({'success': False, 'error': 'Instrument non trouvé'}), 404
            
            # Ajouter l'alerte
            alert_id = add_alert_to_db({
                'instrument_id': data['instrument_id'],
                'name': data['name'],
                'condition': data['condition'],  # 'above', 'below', 'change_up', 'change_down'
                'value': float(data['value']),
                'threshold_percent': data.get('threshold_percent', 5.0),
                'timeframe_minutes': data.get('timeframe_minutes', 60),
                'active': data.get('active', True),
                'notification_type': data.get('notification_type', 'popup'),  # 'popup', 'email', 'both'
                'created_at': datetime.now().isoformat()
            })
            
            # Démarrer le monitoring si ce n'est pas déjà fait
            if data['instrument_id'] not in active_alerts:
                start_monitoring_instrument(data['instrument_id'])
            
            return jsonify({
                'success': True,
                'alert_id': alert_id
            })
        except Exception as e:
            logger.error(f"Erreur add_alert: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @weak_bp.route('/api/custom-tracking/alerts/<int:alert_id>', methods=['DELETE'])
    def delete_alert(alert_id):
        """Supprime une alerte"""
        try:
            success = delete_alert_from_db(alert_id)
            if success:
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error': 'Alerte non trouvée'}), 404
        except Exception as e:
            logger.error(f"Erreur delete_alert: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @weak_bp.route('/api/custom-tracking/notifications')
    def get_notifications():
        """Récupère les notifications récentes"""
        try:
            limit = request.args.get('limit', 50, type=int)
            notifications = get_recent_notifications(limit)
            unread_count = sum(1 for n in notifications if not n['read'])
            
            return jsonify({
                'success': True,
                'notifications': notifications,
                'unread_count': unread_count,
                'total': len(notifications)
            })
        except Exception as e:
            logger.error(f"Erreur get_notifications: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @weak_bp.route('/api/custom-tracking/notifications/<int:notification_id>/read', methods=['POST'])
    def mark_notification_read(notification_id):
        """Marque une notification comme lue"""
        try:
            success = mark_notification_as_read(notification_id)
            if success:
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error': 'Notification non trouvée'}), 404
        except Exception as e:
            logger.error(f"Erreur mark_notification_read: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @weak_bp.route('/api/custom-tracking/real-time-data')
    def get_real_time_data():
        """Récupère les données en temps réel pour tous les instruments suivis"""
        try:
            instruments = get_all_instruments()
            real_time_data = []
            
            for instrument in instruments:
                try:
                    data = get_instrument_data(instrument['symbol'])
                    if data:
                        real_time_data.append({
                            **instrument,
                            'current_data': data,
                            'alerts': get_active_alerts_for_instrument(instrument['id'])
                        })
                except Exception as e:
                    logger.error(f"Erreur pour {instrument['symbol']}: {e}")
                    continue
            
            return jsonify({
                'success': True,
                'data': real_time_data,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Erreur get_real_time_data: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @weak_bp.route('/api/custom-trading/check-alerts')
    def check_alerts_now():
        """Vérifie manuellement toutes les alertes"""
        try:
            triggered = check_all_alerts()
            return jsonify({
                'success': True,
                'triggered_alerts': triggered,
                'timestamp': datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Erreur check_alerts_now: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    # ===============================================
    # THREAD DE MONITORING
    # ===============================================
    
    def monitoring_thread():
        """Thread de monitoring continu"""
        while True:
            try:
                check_all_alerts()
                time.sleep(60)  # Vérifier toutes les minutes
            except Exception as e:
                logger.error(f"Erreur dans le thread de monitoring: {e}")
                time.sleep(30)
    
    # Démarrer le thread
    monitoring_thread_instance = threading.Thread(target=monitoring_thread, daemon=True)
    monitoring_thread_instance.start()
    logger.info("✅ Thread de monitoring démarré")
    
    return weak_bp