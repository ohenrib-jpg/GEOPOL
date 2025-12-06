# Flask/init_weak_indicators_db.py
"""
Script d'initialisation de la base de données pour les indicateurs faibles
À exécuter une seule fois ou après modifications du schéma
"""

import sqlite3
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_weak_indicators_database(db_path: str = None):
    """
    Initialise toutes les tables nécessaires pour les indicateurs faibles
    
    Args:
        db_path: Chemin vers la base de données (défaut: instance/geopol.db)
    """
    
    if db_path is None:
        # Déterminer le chemin par défaut
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        instance_dir = os.path.join(base_dir, 'instance')
        os.makedirs(instance_dir, exist_ok=True)
        db_path = os.path.join(instance_dir, 'geopol.db')
    
    logger.info(f"📂 Initialisation base de données: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        # Lire le schéma SQL
        schema_path = os.path.join(os.path.dirname(__file__), 'weak_indicators_schema.sql')
        
        if os.path.exists(schema_path):
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
            
            # Exécuter le schéma
            cur.executescript(schema_sql)
            logger.info("✅ Schéma SQL exécuté depuis fichier")
        else:
            # Exécuter le schéma inline si fichier absent
            logger.warning("⚠️ Fichier schema.sql non trouvé, utilisation schéma inline")
            execute_inline_schema(cur)
        
        conn.commit()
        
        # Vérifier les tables créées
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cur.fetchall()]
        
        logger.info(f"✅ {len(tables)} tables créées/vérifiées")
        logger.info(f"📋 Tables: {', '.join(tables)}")
        
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur initialisation DB: {e}")
        return False


def execute_inline_schema(cur):
    """
    Exécute le schéma SQL directement (fallback)
    """
    
    # Tables Avis aux Voyageurs
    cur.execute("""
        CREATE TABLE IF NOT EXISTS travel_advisories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country_code TEXT NOT NULL,
            country_name TEXT,
            risk_level INTEGER NOT NULL DEFAULT 1,
            source TEXT NOT NULL,
            summary TEXT,
            details TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(country_code, source)
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS travel_advisories_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country_code TEXT NOT NULL,
            source TEXT NOT NULL,
            previous_risk_level INTEGER,
            new_risk_level INTEGER,
            changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tables KiwiSDR
    cur.execute("""
        CREATE TABLE IF NOT EXISTS kiwisdr_servers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT NOT NULL UNIQUE,
            location TEXT,
            users INTEGER DEFAULT 0,
            users_max INTEGER DEFAULT 4,
            status TEXT DEFAULT 'online',
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS kiwisdr_monitored_frequencies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            frequency_khz INTEGER NOT NULL UNIQUE,
            name TEXT NOT NULL,
            description TEXT,
            category TEXT,
            active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS kiwisdr_frequency_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            frequency_id INTEGER NOT NULL,
            date DATE NOT NULL,
            emission_count INTEGER DEFAULT 0,
            peak_strength REAL DEFAULT 0.0,
            observation_duration INTEGER DEFAULT 0,
            notes TEXT,
            observer TEXT DEFAULT 'user',
            FOREIGN KEY(frequency_id) REFERENCES kiwisdr_monitored_frequencies(id),
            UNIQUE(frequency_id, date)
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS kiwisdr_server_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_servers INTEGER NOT NULL,
            online_servers INTEGER NOT NULL,
            full_servers INTEGER NOT NULL,
            snapshot_data TEXT
        )
    """)
    
    # Tables Stocks
    cur.execute("""
        CREATE TABLE IF NOT EXISTS stock_data_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            name TEXT,
            asset_type TEXT,
            current_price REAL,
            change_percent REAL,
            change_direction TEXT,
            country TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_json TEXT,
            UNIQUE(symbol)
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS stock_price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            date DATE NOT NULL,
            close_price REAL,
            volume BIGINT,
            UNIQUE(symbol, date)
        )
    """)
    
    # Tables SDR Streams
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sdr_streams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            url TEXT,
            frequency_khz INTEGER DEFAULT 0,
            type TEXT DEFAULT 'rtlsdr',
            description TEXT,
            active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sdr_daily_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            stream_id INTEGER NOT NULL,
            date DATE NOT NULL,
            activity_count INTEGER DEFAULT 0,
            FOREIGN KEY(stream_id) REFERENCES sdr_streams(id),
            UNIQUE(stream_id, date)
        )
    """)
    
    # Tables Monitoring
    cur.execute("""
        CREATE TABLE IF NOT EXISTS weak_indicators_monitoring (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            monitoring_id TEXT UNIQUE,
            frequency_khz INTEGER NOT NULL,
            emissions_count INTEGER DEFAULT 0,
            activity_level TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            analysis_data TEXT
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS weak_indicators_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            frequency_khz INTEGER NOT NULL,
            pattern_type TEXT,
            confidence REAL,
            detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            details TEXT
        )
    """)
    
    # Index
    cur.execute("CREATE INDEX IF NOT EXISTS idx_travel_country ON travel_advisories(country_code)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_travel_risk ON travel_advisories(risk_level)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_freq_activity_date ON kiwisdr_frequency_activity(date)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_stock_symbol ON stock_data_cache(symbol)")
    
    logger.info("✅ Schéma inline exécuté")


def populate_initial_data(db_path: str = None):
    """
    Remplit la base avec des données initiales
    """
    if db_path is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(base_dir, 'instance', 'geopol.db')
    
    logger.info("📝 Ajout données initiales...")
    
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        
        # Insérer presets fréquences géopolitiques
        geopolitical_freqs = [
            (2182, 'Maritime MF Détresse', 'Fréquence de détresse maritime 2182 kHz', 'maritime'),
            (4625, 'UVB-76 "The Buzzer"', 'Station mystérieuse russe', 'military'),
            (5732, 'Communications Diplomatiques HF', 'Bande HF diplomatique', 'diplomatic'),
            (6998, 'Militaire OTAN', 'Fréquence militaire OTAN standard', 'military'),
            (8992, 'Communications Gouvernementales', 'Bande HF gouvernementale', 'government'),
            (11175, 'US Military HFGCS', 'High Frequency Global Communications System', 'military'),
            (13670, 'Voice of America', 'Radio internationale américaine', 'broadcast'),
            (14313, 'Maritime Mobile Service', 'Service mobile maritime international', 'maritime'),
            (15300, 'Radio France International', 'Radio internationale française', 'broadcast'),
            (121500, 'Aviation Urgence', 'Fréquence d\'urgence aviation civile (121.5 MHz)', 'aviation')
        ]
        
        count = 0
        for freq_khz, name, desc, cat in geopolitical_freqs:
            try:
                cur.execute("""
                    INSERT OR IGNORE INTO kiwisdr_monitored_frequencies 
                    (frequency_khz, name, description, category, active)
                    VALUES (?, ?, ?, ?, 1)
                """, (freq_khz, name, desc, cat))
                if cur.rowcount > 0:
                    count += 1
            except Exception as e:
                logger.warning(f"⚠️ Erreur insertion fréquence {name}: {e}")
        
        logger.info(f"✅ {count} fréquences géopolitiques ajoutées")
        
        # Insérer quelques symboles boursiers de base
        stock_symbols = [
            ('^GSPC', 'S&P 500', 'index', 'USA'),
            ('^FTSE', 'FTSE 100', 'index', 'UK'),
            ('^GDAXI', 'DAX Performance', 'index', 'Germany'),
            ('^FCHI', 'CAC 40', 'index', 'France'),
            ('CL=F', 'Oil Crude', 'commodity', 'Global'),
            ('GC=F', 'Gold', 'commodity', 'Global'),
            ('BTC-USD', 'Bitcoin', 'crypto', 'Global')
        ]
        
        stock_count = 0
        for symbol, name, asset_type, country in stock_symbols:
            try:
                cur.execute("""
                    INSERT OR IGNORE INTO stock_data_cache 
                    (symbol, name, asset_type, country, current_price, change_percent, change_direction)
                    VALUES (?, ?, ?, ?, 0, 0, 'stable')
                """, (symbol, name, asset_type, country))
                if cur.rowcount > 0:
                    stock_count += 1
            except Exception as e:
                logger.warning(f"⚠️ Erreur insertion stock {symbol}: {e}")
        
        logger.info(f"✅ {stock_count} symboles boursiers ajoutés")
        
        conn.commit()
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur ajout données initiales: {e}")
        return False


if __name__ == "__main__":
    """
    Exécution directe du script
    """
    print("🚀 Initialisation base de données Indicateurs Faibles")
    print("=" * 60)
    
    # Initialiser le schéma
    success = init_weak_indicators_database()
    
    if success:
        print("\n✅ Schéma créé avec succès")
        
        # Ajouter données initiales
        print("\n📝 Ajout des données initiales...")
        populate_initial_data()
        
        print("\n🎉 Initialisation terminée avec succès!")
        print("\n📋 Prochaines étapes:")
        print("   1. Vérifiez que toutes les tables sont créées")
        print("   2. Lancez un scan des avis aux voyageurs")
        print("   3. Récupérez les serveurs KiwiSDR actifs")
        print("   4. Testez les données boursières avec yfinance")
    else:
        print("\n❌ Erreur lors de l'initialisation")
        print("   Vérifiez les logs pour plus de détails")
