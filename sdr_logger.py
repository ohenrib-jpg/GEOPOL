# Flask/sdr_logger.py
"""
Logger spécialisé pour le module SDR
"""

import logging
import json
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from datetime import datetime
import os


def setup_sdr_logger(log_dir: str = "logs"):
    """Configure le logger SDR"""
    
    # Créer le dossier de logs
    os.makedirs(log_dir, exist_ok=True)
    
    # Créer le logger
    logger = logging.getLogger('sdr_spectrum')
    logger.setLevel(logging.DEBUG)
    logger.propagate = False  # Éviter la double journalisation
    
    # Formateur détaillé
    formatter = logging.Formatter(
        '%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - '
        '[%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler fichier avec rotation par taille
    file_handler = RotatingFileHandler(
        filename=os.path.join(log_dir, 'sdr_spectrum.log'),
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=10,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Handler erreurs séparé
    error_handler = TimedRotatingFileHandler(
        filename=os.path.join(log_dir, 'sdr_errors.log'),
        when='midnight',
        interval=1,
        backupCount=30,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.WARNING)
    error_handler.setFormatter(formatter)
    
    # Handler console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    
    # Ajouter les handlers
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)
    logger.addHandler(console_handler)
    
    return logger


class SDRMetricsLogger:
    """Logger pour les métriques SDR"""
    
    def __init__(self, db_manager, log_dir="logs"):
        self.db_manager = db_manager
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        self.metrics_file = os.path.join(log_dir, 'sdr_metrics.json')
        self._init_metrics_db()
    
    def _init_metrics_db(self):
        """Initialise la table des métriques"""
        try:
            conn = self.db_manager.get_connection()
            cur = conn.cursor()
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sdr_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_type TEXT NOT NULL,
                    value REAL,
                    metadata TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Index pour les requêtes
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_metrics_type_time 
                ON sdr_metrics(metric_type, timestamp DESC)
            """)
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"❌ Erreur init métriques: {e}")
    
    def log_scan_metric(self, frequency_khz: int, success: bool, 
                       response_time: float, servers_used: int):
        """Log une métrique de scan"""
        try:
            conn = self.db_manager.get_connection()
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO sdr_metrics (metric_type, value, metadata)
                VALUES (?, ?, ?)
            """, (
                'scan',
                response_time,
                json.dumps({
                    'frequency_khz': frequency_khz,
                    'success': success,
                    'servers_used': servers_used
                })
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"❌ Erreur log métrique: {e}")
    
    def log_server_metric(self, server_url: str, status: str, response_time: float):
        """Log une métrique de serveur"""
        try:
            conn = self.db_manager.get_connection()
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO sdr_metrics (metric_type, value, metadata)
                VALUES (?, ?, ?)
            """, (
                'server',
                response_time,
                json.dumps({
                    'server': server_url,
                    'status': status
                })
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"❌ Erreur log serveur: {e}")
    
    def get_daily_stats(self, days: int = 7) -> Dict[str, Any]:
        """Récupère les statistiques quotidiennes"""
        try:
            conn = self.db_manager.get_connection()
            cur = conn.cursor()
            
            # Scans par jour
            cur.execute("""
                SELECT 
                    DATE(timestamp) as day,
                    COUNT(*) as total_scans,
                    AVG(value) as avg_response_time,
                    SUM(CASE WHEN json_extract(metadata, '$.success') = 1 THEN 1 ELSE 0 END) as successful_scans
                FROM sdr_metrics
                WHERE metric_type = 'scan'
                AND timestamp > datetime('now', '-? days')
                GROUP BY DATE(timestamp)
                ORDER BY day DESC
            """, (days,))
            
            daily_stats = []
            for row in cur.fetchall():
                daily_stats.append({
                    'date': row[0],
                    'total_scans': row[1],
                    'avg_response_time': float(row[2]) if row[2] else 0,
                    'success_rate': row[3] / row[1] if row[1] > 0 else 0
                })
            
            # Serveurs les plus utilisés
            cur.execute("""
                SELECT 
                    json_extract(metadata, '$.server') as server,
                    COUNT(*) as requests,
                    AVG(value) as avg_response_time
                FROM sdr_metrics
                WHERE metric_type = 'server'
                AND timestamp > datetime('now', '-7 days')
                GROUP BY server
                ORDER BY requests DESC
                LIMIT 10
            """)
            
            top_servers = []
            for row in cur.fetchall():
                top_servers.append({
                    'server': row[0],
                    'requests': row[1],
                    'avg_response_time': float(row[2]) if row[2] else 0
                })
            
            conn.close()
            
            return {
                'daily_stats': daily_stats,
                'top_servers': top_servers,
                'period_days': days
            }
            
        except Exception as e:
            print(f"❌ Erreur stats quotidiennes: {e}")
            return {'error': str(e)}