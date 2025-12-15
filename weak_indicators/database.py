# Flask/weak_indicators/database.py
"""Gestion de la base de données SQLite pour les indicateurs faibles"""

import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

class WeakIndicatorsDB:
    """Gestionnaire de base de données pour les indicateurs faibles"""
    
    def __init__(self, db_path: str = None):
        if db_path:
            self.db_path = Path(db_path)  # Convertir en Path object
        else:
            # Chemin par défaut
            base_dir = Path(__file__).parent.parent.parent
            self.db_path = base_dir / "data" / "weak_indicators.db"
            
        # Créer le dossier si nécessaire
        self.db_path.parent.mkdir(exist_ok=True)
        
        self.init_database()
    
    def get_connection(self):
        """Obtient une connexion à la base de données"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialise les tables de la base de données"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Table des avis de voyage
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS travel_advisories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    country_code TEXT NOT NULL,
                    country_name TEXT NOT NULL,
                    risk_level INTEGER NOT NULL,
                    source TEXT NOT NULL,
                    summary TEXT,
                    raw_data TEXT,
                    last_updated DATETIME NOT NULL,
                    expires_at DATETIME NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(country_code, source)
                )
            ''')
            
            # Table des instruments financiers
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS financial_instruments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    name TEXT NOT NULL,
                    current_price REAL NOT NULL,
                    change_percent REAL NOT NULL,
                    volume INTEGER,
                    timestamp DATETIME NOT NULL,
                    source TEXT NOT NULL,
                    category TEXT NOT NULL,
                    expires_at DATETIME NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, timestamp)
                )
            ''')
            
            # Table de l'activité SDR
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sdr_activities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    frequency_khz INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    activity_count INTEGER NOT NULL,
                    last_seen DATETIME NOT NULL,
                    is_anomaly BOOLEAN NOT NULL,
                    source TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Table des sources de scraping
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scraping_sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    url TEXT NOT NULL,
                    type TEXT NOT NULL,
                    enabled BOOLEAN DEFAULT 1,
                    last_scraped DATETIME,
                    success_rate REAL DEFAULT 0,
                    scraping_config TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Table des logs de scraping
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS scraping_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id INTEGER,
                    status TEXT NOT NULL,
                    message TEXT,
                    items_count INTEGER DEFAULT 0,
                    duration_seconds REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (source_id) REFERENCES scraping_sources(id)
                )
            ''')
            
            conn.commit()
            
            # Insérer les sources de scraping par défaut
            self._init_scraping_sources(cursor)
            
            logger.info(f"Base de données initialisée : {self.db_path}")
    
    def _init_scraping_sources(self, cursor):
        """Insère les sources de scraping par défaut"""
        sources = [
            {
                'name': 'UK Foreign Office',
                'url': 'https://www.gov.uk/foreign-travel-advice',
                'type': 'travel',
                'scraping_config': '{"method": "scrape_uk_gov"}'
            },
            {
                'name': 'US State Department',
                'url': 'https://travel.state.gov/content/travel/en/traveladvisories/traveladvisories.html',
                'type': 'travel',
                'scraping_config': '{"method": "scrape_us_state_gov"}'
            },
            {
                'name': 'Australia Smartraveller',
                'url': 'https://www.smartraveller.gov.au/destinations',
                'type': 'travel',
                'scraping_config': '{"method": "scrape_au_smartraveller"}'
            },
            {
                'name': 'France Diplomatie',
                'url': 'https://www.diplomatie.gouv.fr/fr/conseils-aux-voyageurs/',
                'type': 'travel',
                'scraping_config': '{"method": "scrape_fr_diplomatie"}'
            },
            {
                'name': 'Yahoo Finance',
                'url': 'https://finance.yahoo.com/',
                'type': 'financial',
                'scraping_config': '{"method": "yfinance"}'
            }
        ]
        
        for source in sources:
            cursor.execute('''
                INSERT OR IGNORE INTO scraping_sources (name, url, type, scraping_config)
                VALUES (?, ?, ?, ?)
            ''', (source['name'], source['url'], source['type'], source['scraping_config']))
    
    # --- Méthodes pour Travel Advisories ---
    
    def save_travel_advisory(self, advisory):
        """Sauvegarde un avis de voyage"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            expires_at = datetime.utcnow() + timedelta(hours=24)  # 24h de cache
            
            cursor.execute('''
                INSERT OR REPLACE INTO travel_advisories 
                (country_code, country_name, risk_level, source, summary, raw_data, last_updated, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                advisory.country_code,
                advisory.country_name,
                advisory.risk_level,
                advisory.source,
                advisory.summary,
                str(advisory.raw_data) if advisory.raw_data else None,
                advisory.last_updated,
                expires_at
            ))
            
            return cursor.lastrowid
    
    def get_travel_advisories(self, max_age_hours: int = 24, limit: int = 100):
        """Récupère les avis de voyage récents"""
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM travel_advisories 
                WHERE last_updated > ? AND expires_at > datetime('now')
                ORDER BY risk_level DESC, last_updated DESC
                LIMIT ?
            ''', (cutoff, limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    # --- Méthodes pour Financial Instruments ---
    
    def save_financial_instrument(self, instrument):
        """Sauvegarde un instrument financier"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            expires_at = datetime.utcnow() + timedelta(minutes=5)  # 5 min de cache
            
            cursor.execute('''
                INSERT INTO financial_instruments 
                (symbol, name, current_price, change_percent, volume, timestamp, source, category, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                instrument.symbol,
                instrument.name,
                instrument.current_price,
                instrument.change_percent,
                instrument.volume,
                instrument.timestamp,
                instrument.source,
                instrument.category,
                expires_at
            ))
            
            return cursor.lastrowid
    
    def get_financial_data(self, max_age_minutes: int = 10, limit: int = 50):
        """Récupère les données financières récentes"""
        cutoff = datetime.utcnow() - timedelta(minutes=max_age_minutes)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT f1.* FROM financial_instruments f1
                INNER JOIN (
                    SELECT symbol, MAX(timestamp) as max_timestamp
                    FROM financial_instruments
                    WHERE timestamp > ? AND expires_at > datetime('now')
                    GROUP BY symbol
                ) f2 ON f1.symbol = f2.symbol AND f1.timestamp = f2.max_timestamp
                ORDER BY f1.timestamp DESC
                LIMIT ?
            ''', (cutoff, limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    # --- Méthodes pour SDR Activities ---
    
    def save_sdr_activity(self, activity):
        """Sauvegarde une activité SDR"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO sdr_activities 
                (frequency_khz, name, activity_count, last_seen, is_anomaly, source)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                activity.frequency_khz,
                activity.name,
                activity.activity_count,
                activity.last_seen,
                1 if activity.is_anomaly else 0,
                activity.source
            ))
            
            return cursor.lastrowid
    
    def get_sdr_activities(self, max_age_hours: int = 1, limit: int = 50):
        """Récupère les activités SDR récentes"""
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM sdr_activities 
                WHERE last_seen > ?
                ORDER BY last_seen DESC
                LIMIT ?
            ''', (cutoff, limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    # --- Méthodes pour la gestion du scraping ---
    
    def log_scraping_result(self, source_id: int, status: str, message: str = None, 
                           items_count: int = 0, duration: float = 0):
        """Log un résultat de scraping"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO scraping_logs 
                (source_id, status, message, items_count, duration_seconds)
                VALUES (?, ?, ?, ?, ?)
            ''', (source_id, status, message, items_count, duration))
            
            # Mettre à jour la dernière date de scraping
            if status == 'success':
                cursor.execute('''
                    UPDATE scraping_sources 
                    SET last_scraped = datetime('now')
                    WHERE id = ?
                ''', (source_id,))
            
            conn.commit()
    
    def get_scraping_stats(self):
        """Récupère les statistiques de scraping"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    type,
                    COUNT(*) as total_sources,
                    SUM(CASE WHEN enabled = 1 THEN 1 ELSE 0 END) as enabled_sources,
                    COUNT(CASE WHEN last_scraped > datetime('now', '-1 hour') THEN 1 END) as recent_scrapes,
                    AVG(success_rate) as avg_success_rate
                FROM scraping_sources
                GROUP BY type
            ''')
            
            return [dict(row) for row in cursor.fetchall()]
    
    def cleanup_old_data(self):
        """Nettoie les anciennes données"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Supprimer les données expirées
            cursor.execute("DELETE FROM travel_advisories WHERE expires_at < datetime('now')")
            cursor.execute("DELETE FROM financial_instruments WHERE expires_at < datetime('now')")
            
            # Garder seulement 7 jours de logs
            cursor.execute("DELETE FROM scraping_logs WHERE created_at < datetime('now', '-7 days')")
            
            # Garder seulement 30 jours d'activités SDR
            cursor.execute("DELETE FROM sdr_activities WHERE created_at < datetime('now', '-30 days')")
            
            deleted = cursor.rowcount
            conn.commit()
            
            return deleted
