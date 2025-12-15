# Flask/alerts_system_routes.py
from flask import Blueprint, jsonify, request, render_template
import sqlite3, os
from datetime import datetime, timedelta
import json
import logging

alerts_system_bp = Blueprint('alerts_system', __name__, url_prefix='/api')
logger = logging.getLogger(__name__)

# === GESTION DES ALERTES ===

@alerts_system_bp.route('/alerts')
def alerts_system_alerts():
    """Récupère toutes les alertes configurées"""
    try:
        alerts = get_alerts_from_db()
        return jsonify(alerts)
    except Exception as e:
        logger.error(f"Erreur récupération alertes: {e}")
        return jsonify({"error": str(e)}), 500

@alerts_system_bp.route('/alerts', methods=['POST'])
def create_alert():
    """Crée une nouvelle alerte"""
    try:
        data = request.get_json()
        
        alert_data = {
            'name': data.get('name', '').strip(),
            'description': data.get('description', '').strip(),
            'keywords': data.get('keywords', []),
            'threshold_count': int(data.get('threshold_count', 5)),
            'threshold_time_hours': int(data.get('threshold_time_hours', 24)),
            'sensitivity': data.get('sensitivity', 'medium'),
            'categories': data.get('categories', []),
            'active': True
        }
        
        if not alert_data['name'] or not alert_data['keywords']:
            return jsonify({"error": "Nom et mots-clés requis"}), 400
        
        alert_id = save_alert_to_db(alert_data)
        return jsonify({"success": True, "id": alert_id})
        
    except Exception as e:
        logger.error(f"Erreur création alerte: {e}")
        return jsonify({"error": str(e)}), 500

@alerts_system_bp.route('/alerts/<int:alert_id>', methods=['PUT'])
def update_alert(alert_id):
    """Met à jour une alerte"""
    try:
        data = request.get_json()
        alert_data = {
            'name': data.get('name', '').strip(),
            'description': data.get('description', '').strip(),
            'keywords': data.get('keywords', []),
            'threshold_count': int(data.get('threshold_count', 5)),
            'threshold_time_hours': int(data.get('threshold_time_hours', 24)),
            'sensitivity': data.get('sensitivity', 'medium'),
            'categories': data.get('categories', []),
            'active': data.get('active', True)
        }
        
        if not alert_data['name'] or not alert_data['keywords']:
            return jsonify({"error": "Nom et mots-clés requis"}), 400
        
        success = update_alert_in_db(alert_id, alert_data)
        if success:
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Alerte non trouvée"}), 404
            
    except Exception as e:
        logger.error(f"Erreur mise à jour alerte: {e}")
        return jsonify({"error": str(e)}), 500

@alerts_system_bp.route('/alerts/<int:alert_id>', methods=['DELETE'])
def delete_alert(alert_id):
    """Supprime une alerte"""
    try:
        success = delete_alert_from_db(alert_id)
        if success:
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Alerte non trouvée"}), 404
    except Exception as e:
        logger.error(f"Erreur suppression alerte: {e}")
        return jsonify({"error": str(e)}), 500

@alerts_system_bp.route('/alerts/<int:alert_id>/toggle', methods=['POST'])
def toggle_alert(alert_id):
    """Active/désactive une alerte"""
    try:
        data = request.get_json()
        active = data.get('active', True)
        success = toggle_alert_in_db(alert_id, active)
        if success:
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Alerte non trouvée"}), 404
    except Exception as e:
        logger.error(f"Erreur toggle alerte: {e}")
        return jsonify({"error": str(e)}), 500

# === DÉTECTION D'ANOMALIES ===

@alerts_system_bp.route('/alerts')
def get_alerts():
    """Récupère toutes les alertes configurées"""
    try:
        alerts = get_alerts_from_db()
        return jsonify(alerts)
    except Exception as e:
        logger.error(f"Erreur récupération alertes: {e}")
        return jsonify({
            "alerts": [],
            "total": 0,
            "last_updated": datetime.utcnow().isoformat()
        })

@alerts_system_bp.route('/alerts/triggered')
def alerts_system_triggered_alerts():
    """Récupère les alertes déclenchées récemment"""
    try:
        hours = int(request.args.get('hours', 24))
        triggered_alerts = get_recently_triggered_alerts(hours)
        return jsonify(triggered_alerts)
    except Exception as e:
        logger.error(f"Erreur récupération alertes déclenchées: {e}")
        return jsonify({
            "triggered_alerts": [],
            "timeframe_hours": hours,
            "total": 0
        })

# === FONCTIONS UTILITAIRES ===

def get_db_connection():
    """Connexion à la base de données"""
    instance_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'instance')
    os.makedirs(instance_dir, exist_ok=True)
    db_path = os.path.join(instance_dir, 'geopol.db')
    return sqlite3.connect(db_path)

def init_alerts_tables():
    """Initialise les tables d'alertes"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Table des alertes
    cur.execute("""
        CREATE TABLE IF NOT EXISTS alert_configurations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            keywords TEXT NOT NULL, -- JSON array
            threshold_count INTEGER DEFAULT 5,
            threshold_time_hours INTEGER DEFAULT 24,
            sensitivity TEXT DEFAULT 'medium', -- low, medium, high
            categories TEXT DEFAULT '[]', -- JSON array
            active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Table des alertes déclenchées
    cur.execute("""
        CREATE TABLE IF NOT EXISTS triggered_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_id INTEGER,
            article_count INTEGER,
            time_window_hours INTEGER,
            keywords_found TEXT, -- JSON array
            article_samples TEXT, -- JSON array with article IDs
            severity TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(alert_id) REFERENCES alert_configurations(id)
        )
    """)
    
    # Index pour les performances
    cur.execute("CREATE INDEX IF NOT EXISTS idx_alerts_active ON alert_configurations(active)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_triggered_alerts_time ON triggered_alerts(created_at)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_triggered_alerts_alert ON triggered_alerts(alert_id)")
    
    conn.commit()
    conn.close()

def get_alerts_from_db():
    """Récupère toutes les alertes"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM alert_configurations ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    
    alerts = []
    for row in rows:
        alerts.append({
            'id': row[0],
            'name': row[1],
            'description': row[2],
            'keywords': json.loads(row[3]) if row[3] else [],
            'threshold_count': row[4],
            'threshold_time_hours': row[5],
            'sensitivity': row[6],
            'categories': json.loads(row[7]) if row[7] else [],
            'active': bool(row[8]),
            'created_at': row[9],
            'updated_at': row[10]
        })
    
    return alerts

def get_active_alerts_from_db():
    """Récupère les alertes actives"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM alert_configurations WHERE active = 1 ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    
    alerts = []
    for row in rows:
        alerts.append({
            'id': row[0],
            'name': row[1],
            'description': row[2],
            'keywords': json.loads(row[3]) if row[3] else [],
            'threshold_count': row[4],
            'threshold_time_hours': row[5],
            'sensitivity': row[6],
            'categories': json.loads(row[7]) if row[7] else [],
            'active': bool(row[8])
        })
    
    return alerts

def save_alert_to_db(alert_data):
    """Sauvegarde une nouvelle alerte"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO alert_configurations (name, description, keywords, threshold_count, 
                                        threshold_time_hours, sensitivity, categories)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        alert_data['name'],
        alert_data['description'],
        json.dumps(alert_data['keywords']),
        alert_data['threshold_count'],
        alert_data['threshold_time_hours'],
        alert_data['sensitivity'],
        json.dumps(alert_data['categories'])
    ))
    alert_id = cur.lastrowid
    conn.commit()
    conn.close()
    return alert_id

def update_alert_in_db(alert_id, alert_data):
    """Met à jour une alerte"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE alert_configurations 
        SET name = ?, description = ?, keywords = ?, threshold_count = ?, 
            threshold_time_hours = ?, sensitivity = ?, categories = ?, active = ?, 
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (
        alert_data['name'],
        alert_data['description'],
        json.dumps(alert_data['keywords']),
        alert_data['threshold_count'],
        alert_data['threshold_time_hours'],
        alert_data['sensitivity'],
        json.dumps(alert_data['categories']),
        alert_data['active'],
        alert_id
    ))
    success = cur.rowcount > 0
    conn.commit()
    conn.close()
    return success

def delete_alert_from_db(alert_id):
    """Supprime une alerte"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM alert_configurations WHERE id = ?", (alert_id,))
    success = cur.rowcount > 0
    conn.commit()
    conn.close()
    return success

def toggle_alert_in_db(alert_id, active):
    """Active/désactive une alerte"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE alert_configurations SET active = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (active, alert_id))
    success = cur.rowcount > 0
    conn.commit()
    conn.close()
    return success

def get_recent_articles(hours=48):
    """Récupère les articles récents"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
    cur.execute("""
        SELECT id, title, content, pub_date, sentiment_type, feed_url
        FROM articles 
        WHERE pub_date >= ?
        ORDER BY pub_date DESC
    """, (since,))
    
    rows = cur.fetchall()
    conn.close()
    
    articles = []
    for row in rows:
        articles.append({
            'id': row[0],
            'title': row[1] or '',
            'content': row[2] or '',
            'pub_date': row[3],
            'sentiment': row[4] or 'neutral',
            'source': row[5] or ''
        })
    
    return articles

def analyze_alert_against_articles(alert, articles):
    """Analyse une alerte contre les articles"""
    keywords = [kw.lower().strip() for kw in alert['keywords']]
    time_window = alert['threshold_time_hours']
    threshold = alert['threshold_count']
    
    # Analyser par tranches de temps
    now = datetime.utcnow()
    recent_matches = []
    keyword_counts = {kw: 0 for kw in keywords}
    
    for article in articles:
        article_date = datetime.fromisoformat(article['pub_date'].replace('Z', '+00:00'))
        hours_diff = (now - article_date).total_seconds() / 3600
        
        if hours_diff <= time_window:
            text = (article['title'] + ' ' + article['content']).lower()
            found_keywords = []
            
            for keyword in keywords:
                if keyword in text:
                    keyword_counts[keyword] += 1
                    found_keywords.append(keyword)
            
            if found_keywords:
                recent_matches.append({
                    'article': article,
                    'found_keywords': found_keywords,
                    'hours_ago': hours_diff
                })
    
    total_matches = len(recent_matches)
    top_keywords = sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Déterminer si l'alerte est déclenchée
    triggered = total_matches >= threshold
    
    # Calculer la sévérité
    if total_matches >= threshold * 2:
        severity = 'high'
    elif total_matches >= threshold * 1.5:
        severity = 'medium'
    else:
        severity = 'low'
    
    return {
        'alert_id': alert['id'],
        'alert_name': alert['name'],
        'triggered': triggered,
        'article_count': total_matches,
        'threshold': threshold,
        'time_window_hours': time_window,
        'keyword_counts': dict(top_keywords),
        'severity': severity,
        'matches': recent_matches[:5]  # Limiter aux 5 plus récents
    }

def log_triggered_alert(alert, analysis_result):
    """Enregistre une alerte déclenchée"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Récupérer les IDs des articles pour référence
    article_ids = [match['article']['id'] for match in analysis_result['matches']]
    
    cur.execute("""
        INSERT INTO triggered_alerts (alert_id, article_count, time_window_hours, 
                                    keywords_found, article_samples, severity)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        alert['id'],
        analysis_result['article_count'],
        analysis_result['time_window_hours'],
        json.dumps(analysis_result['keyword_counts']),
        json.dumps(article_ids),
        analysis_result['severity']
    ))
    
    conn.commit()
    conn.close()

def get_recently_triggered_alerts(hours=24):
    """Récupère les alertes déclenchées récemment"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
    cur.execute("""
        SELECT ta.*, ac.name as alert_name, ac.description as alert_description
        FROM triggered_alerts ta
        JOIN alert_configurations ac ON ta.alert_id = ac.id
        WHERE ta.created_at >= ?
        ORDER BY ta.created_at DESC
        LIMIT 50
    """, (since,))
    
    rows = cur.fetchall()
    conn.close()
    
    triggered_alerts = []
    for row in rows:
        triggered_alerts.append({
            'id': row[0],
            'alert_id': row[1],
            'alert_name': row[8],
            'alert_description': row[9],
            'article_count': row[2],
            'time_window_hours': row[3],
            'keyword_counts': json.loads(row[4]) if row[4] else {},
            'article_samples': json.loads(row[5]) if row[5] else [],
            'severity': row[6],
            'created_at': row[7]
        })
    
    return triggered_alerts

# Initialisation au chargement du module
init_alerts_tables()