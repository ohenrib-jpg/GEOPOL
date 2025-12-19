# Flask/social_database_migrations.py
"""
Migrations pour les tables des réseaux sociaux et stocks
"""

import logging
from .database import DatabaseManager

logger = logging.getLogger(__name__)

def create_social_tables(db_manager: DatabaseManager):
    """Crée toutes les tables nécessaires pour les réseaux sociaux"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    try:
        # Table des posts sociaux (legacy)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS social_posts (
                id TEXT PRIMARY KEY,
                title TEXT,
                content TEXT,
                link TEXT,
                pub_date DATETIME,
                source TEXT,
                source_type TEXT,
                author TEXT,
                sentiment_score REAL,
                sentiment_type TEXT,
                sentiment_confidence REAL,
                engagement TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table des posts sociaux par pays (nouveau système)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS social_posts_by_country (
                id TEXT PRIMARY KEY,
                country_code TEXT,
                country_name TEXT,
                language TEXT,
                title TEXT,
                content TEXT,
                link TEXT,
                pub_date DATETIME,
                author TEXT,
                sentiment_score REAL,
                sentiment_type TEXT,
                sentiment_confidence REAL,
                emotions TEXT,
                engagement TEXT,
                relevance_score REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Index pour améliorer les performances
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_social_country_date 
            ON social_posts_by_country(country_code, pub_date DESC)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_social_country_relevance 
            ON social_posts_by_country(country_code, relevance_score DESC)
        """)
        
        # Table des comparaisons RSS vs Social
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sentiment_comparisons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                rss_total INTEGER,
                rss_avg_sentiment REAL,
                social_total INTEGER,
                social_avg_sentiment REAL,
                divergence_absolute REAL,
                factor_z_value REAL,
                interpretation TEXT,
                recommendations TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table de monitoring des stocks (yFinance)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_monitoring (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT UNIQUE NOT NULL,
                name TEXT,
                current_price REAL,
                change_percent REAL,
                volume INTEGER,
                market_cap REAL,
                last_update DATETIME,
                is_active BOOLEAN DEFAULT 1,
                alert_threshold_high REAL,
                alert_threshold_low REAL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Ajouter quelques stocks par défaut
        default_stocks = [
            ('CAC40', 'CAC 40', 7500.00, 0.0, 1),
            ('^FCHI', 'CAC 40 Index', 7500.00, 0.0, 1),
            ('AAPL', 'Apple Inc.', 180.00, 0.0, 0),
            ('MSFT', 'Microsoft Corp.', 370.00, 0.0, 0)
        ]
        
        for symbol, name, price, change, active in default_stocks:
            cursor.execute("""
                INSERT OR IGNORE INTO stock_monitoring 
                (symbol, name, current_price, change_percent, is_active)
                VALUES (?, ?, ?, ?, ?)
            """, (symbol, name, price, change, active))
        
        conn.commit()
        logger.info("✅ Tables réseaux sociaux créées avec succès")
        
        # Afficher un résumé
        cursor.execute("SELECT COUNT(*) FROM social_posts")
        social_legacy_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM social_posts_by_country")
        social_country_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM sentiment_comparisons")
        comparisons_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM stock_monitoring")
        stocks_count = cursor.fetchone()[0]
        
        logger.info(f"📊 Résumé base de données sociale:")
        logger.info(f"   • Posts legacy: {social_legacy_count}")
        logger.info(f"   • Posts par pays: {social_country_count}")
        logger.info(f"   • Comparaisons: {comparisons_count}")
        logger.info(f"   • Stocks configurés: {stocks_count}")
        
    except Exception as e:
        logger.error(f"❌ Erreur création tables sociales: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def check_social_tables(db_manager: DatabaseManager) -> dict:
    """Vérifie l'état des tables sociales"""
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    tables_status = {}
    
    required_tables = [
        'social_posts',
        'social_posts_by_country',
        'sentiment_comparisons',
        'stock_monitoring'
    ]
    
    for table in required_tables:
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name=?
        """, (table,))
        
        tables_status[table] = cursor.fetchone() is not None
    
    conn.close()
    return tables_status

def run_social_migrations(db_manager: DatabaseManager):
    """Exécute toutes les migrations nécessaires"""
    logger.info("🔄 Vérification des tables réseaux sociaux...")
    
    status = check_social_tables(db_manager)
    
    missing_tables = [table for table, exists in status.items() if not exists]
    
    if missing_tables:
        logger.info(f"⚠️ Tables manquantes: {', '.join(missing_tables)}")
        logger.info("🔧 Création des tables...")
        create_social_tables(db_manager)
    else:
        logger.info("✅ Toutes les tables sociales existent")
    
    return status