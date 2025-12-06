# Flask/database_fix.py
import sqlite3
import logging

logger = logging.getLogger(__name__)

def fix_database_structure(db_path="rss_analyzer.db"):
    """Corrige la structure de la base de données"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("🔧 Correction de la structure de la base de données...")
        
        # Vérifier si la table themes existe avec les bonnes colonnes
        cursor.execute("PRAGMA table_info(themes)")
        theme_columns = [col[1] for col in cursor.fetchall()]
        
        if 'description' not in theme_columns:
            print("➕ Ajout de la colonne description à la table themes")
            cursor.execute("ALTER TABLE themes ADD COLUMN description TEXT")
        
        # Vérifier la table articles
        cursor.execute("PRAGMA table_info(articles)")
        article_columns = [col[1] for col in cursor.fetchall()]
        
        missing_columns = []
        for col in ['detailed_sentiment', 'roberta_score', 'analysis_model', 'sentiment_confidence']:
            if col not in article_columns:
                missing_columns.append(col)
        
        if missing_columns:
            print(f"➕ Ajout des colonnes manquantes: {missing_columns}")
            for col in missing_columns:
                if col == 'detailed_sentiment':
                    cursor.execute("ALTER TABLE articles ADD COLUMN detailed_sentiment TEXT")
                elif col == 'roberta_score':
                    cursor.execute("ALTER TABLE articles ADD COLUMN roberta_score REAL")
                elif col == 'analysis_model':
                    cursor.execute("ALTER TABLE articles ADD COLUMN analysis_model TEXT DEFAULT 'traditional'")
                elif col == 'sentiment_confidence':
                    cursor.execute("ALTER TABLE articles ADD COLUMN sentiment_confidence REAL DEFAULT 0.5")
        
        # Créer la table theme_analyses si elle n'existe pas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS theme_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER,
                theme_id TEXT,
                confidence REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (article_id) REFERENCES articles (id),
                FOREIGN KEY (theme_id) REFERENCES themes (id)
            )
        """)
        
        conn.commit()
        print("✅ Structure de la base de données corrigée")
        
    except Exception as e:
        print(f"❌ Erreur lors de la correction: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_database_structure()
