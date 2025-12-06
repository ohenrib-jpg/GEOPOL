# Flask/database_migration_fix.py - VERSION CORRIGÉE
import sqlite3
import logging
import json

logger = logging.getLogger(__name__)

# Définir DEFAULT_THEMES localement pour éviter l'import
DEFAULT_THEMES = {
    "technologie": {
        "keywords": ["ai", "intelligence artificielle", "chatgpt", "machine learning", "python", "programmation", "développement", "software", "hardware", "robot", "blockchain", "cloud", "cybersécurité"],
        "color": "#3B82F6"
    },
    "politique": {
        "keywords": ["gouvernement", "élection", "président", "ministre", "parlement", "loi", "réforme", "politique", "député", "sénateur", "vote", "assemblée"],
        "color": "#EF4444"
    },
    "économie": {
        "keywords": ["économie", "inflation", "croissance", "banque", "finance", "bourse", "investissement", "entreprise", "marché", "chômage", "emploi", "crise"],
        "color": "#10B981"
    },
    "santé": {
        "keywords": ["santé", "médecine", "hôpital", "vaccin", "maladie", "médecin", "patient", "recherche", "traitement", "épidémie", "virus", "médical"],
        "color": "#8B5CF6"
    },
    "environnement": {
        "keywords": ["environnement", "climat", "écologie", "réchauffement", "pollution", "énergie", "durable", "biodiversité", "transition", "carbone", "renouvelable"],
        "color": "#22C55E"
    }
}

def safe_migration(db_path):
    """Migration sécurisée qui préserve les données existantes"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        print("🔍 Vérification de la structure de la base de données...")
        
        # ÉTAPE 1: Vérifier quelles tables existent
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]
        print(f"📋 Tables existantes: {existing_tables}")
        
        # Créer les tables essentielles d'abord
        _create_essential_tables(cursor, existing_tables)
        
        # Ajouter les colonnes avancées
        _add_advanced_columns(cursor, existing_tables)
        
        # AJOUT CRITIQUE : Ajouter les colonnes RoBERTa
        _add_roberta_columns(cursor, existing_tables)
        
        # Créer les index
        _create_indexes(cursor)
        
        # Peupler les thèmes
        _populate_default_themes(cursor)
        
        conn.commit()
        print("🎉 Migration complète terminée avec succès!")
        
        # Afficher un résumé
        _show_database_summary(cursor)
        
    except Exception as e:
        print(f"❌ Erreur lors de la migration: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def _create_essential_tables(cursor, existing_tables):
    """Crée les tables essentielles"""
    essential_tables = {
        'themes': """
            CREATE TABLE IF NOT EXISTS themes (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                keywords TEXT,
                color TEXT,
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """,
        'articles': """
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT,
                link TEXT UNIQUE,
                pub_date DATETIME,
                feed_url TEXT,
                sentiment_score REAL,
                sentiment_type TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """,
        'theme_analyses': """
            CREATE TABLE IF NOT EXISTS theme_analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER,
                theme_id TEXT,
                confidence REAL DEFAULT 0.5,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
                FOREIGN KEY (theme_id) REFERENCES themes(id) ON DELETE CASCADE
            )
        """
    }
    
    for table_name, create_sql in essential_tables.items():
        if table_name not in existing_tables:
            print(f"🔄 Création de la table {table_name}...")
            cursor.execute(create_sql)

def _add_advanced_columns(cursor, existing_tables):
    """Ajoute les colonnes avancées"""
    if 'articles' in existing_tables:
        cursor.execute("PRAGMA table_info(articles)")
        existing_columns = [column[1] for column in cursor.fetchall()]
        
        advanced_columns = [
            ('detailed_sentiment', 'TEXT'),
            ('confidence', 'REAL DEFAULT 0.5'),
            ('bayesian_confidence', 'REAL'),
            ('bayesian_evidence_count', 'INTEGER DEFAULT 0'),
            ('analyzed_at', 'DATETIME')
        ]
        
        for column_name, column_type in advanced_columns:
            if column_name not in existing_columns:
                print(f"🔄 Ajout de la colonne {column_name}...")
                try:
                    sql = f"ALTER TABLE articles ADD COLUMN {column_name} {column_type}"
                    cursor.execute(sql)
                except Exception as e:
                    print(f"⚠️ Impossible d'ajouter {column_name}: {e}")

def _add_roberta_columns(cursor, existing_tables):
    """AJOUT CRITIQUE : Colonnes pour RoBERTa"""
    if 'articles' in existing_tables:
        cursor.execute("PRAGMA table_info(articles)")
        existing_columns = [column[1] for column in cursor.fetchall()]
        
        # Colonnes CRITIQUES pour RoBERTa
        roberta_columns = [
            ('analysis_model', 'TEXT DEFAULT "traditional"'),
            ('sentiment_confidence', 'REAL DEFAULT 0.5'),
            ('roberta_score', 'REAL'),
            ('roberta_label', 'TEXT')
        ]
        
        print("🔧 Ajout des colonnes RoBERTa...")
        for column_name, column_type in roberta_columns:
            if column_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE articles ADD COLUMN {column_name} {column_type}")
                    print(f"✅ Colonne RoBERTa ajoutée: {column_name}")
                except Exception as e:
                    print(f"⚠️ Erreur sur {column_name}: {e}")
            else:
                print(f"✅ Colonne RoBERTa déjà présente: {column_name}")
        
        # Mettre à jour les articles existants avec le modèle par défaut
        try:
            cursor.execute("""
                UPDATE articles 
                SET analysis_model = 'traditional'
                WHERE analysis_model IS NULL
            """)
            print(f"✅ {cursor.rowcount} articles mis à jour avec le modèle par défaut")
        except Exception as e:
            print(f"⚠️ Erreur mise à jour articles: {e}")

def _create_indexes(cursor):
    """Crée les index de manière sécurisée"""
    print("🔄 Création des index...")
    
    # Index basiques (toujours sûrs)
    basic_indexes = [
        "CREATE INDEX IF NOT EXISTS idx_articles_pub_date ON articles(pub_date)",
        "CREATE INDEX IF NOT EXISTS idx_articles_feed_url ON articles(feed_url)",
        "CREATE INDEX IF NOT EXISTS idx_articles_sentiment ON articles(sentiment_type)",
        "CREATE INDEX IF NOT EXISTS idx_theme_analyses_article ON theme_analyses(article_id)",
        "CREATE INDEX IF NOT EXISTS idx_theme_analyses_theme ON theme_analyses(theme_id)"
    ]
    
    for index_sql in basic_indexes:
        try:
            cursor.execute(index_sql)
        except Exception as e:
            print(f"⚠️ Index basique ignoré: {e}")
    
    # Index avancés (peut échouer si colonnes manquantes)
    advanced_indexes = [
        "CREATE INDEX IF NOT EXISTS idx_articles_sentiment_score ON articles(sentiment_score)",
        "CREATE INDEX IF NOT EXISTS idx_articles_detailed_sentiment ON articles(detailed_sentiment)",
        "CREATE INDEX IF NOT EXISTS idx_articles_analyzed_at ON articles(analyzed_at)",
        "CREATE INDEX IF NOT EXISTS idx_articles_analysis_model ON articles(analysis_model)"
    ]
    
    for index_sql in advanced_indexes:
        try:
            cursor.execute(index_sql)
        except Exception as e:
            print(f"ℹ️ Index avancé ignoré (normal si colonne manquante): {e}")

def _populate_default_themes(cursor):
    """Ajoute les thèmes par défaut de manière sécurisée"""
    try:
        # Vérifier si des thèmes existent déjà
        cursor.execute("SELECT COUNT(*) FROM themes")
        theme_count = cursor.fetchone()[0]
        
        if theme_count == 0:
            print("🔄 Ajout des thèmes par défaut...")
            for theme_id, theme_data in DEFAULT_THEMES.items():
                # Nettoyer la couleur (enlever le # si présent)
                color = theme_data['color'].replace('#', '') if theme_data['color'] else '6366f1'
                
                cursor.execute(
                    "INSERT OR IGNORE INTO themes (id, name, keywords, color) VALUES (?, ?, ?, ?)",
                    (
                        theme_id,
                        theme_id.capitalize(),
                        json.dumps(theme_data['keywords'], ensure_ascii=False),
                        color
                    )
                )
            print("✅ Thèmes par défaut ajoutés")
        else:
            print(f"✅ Thèmes déjà présents: {theme_count}")
            
    except Exception as e:
        print(f"⚠️ Erreur lors de l'ajout des thèmes: {e}")

def _show_database_summary(cursor):
    """Affiche un résumé de la base de données"""
    try:
        cursor.execute("SELECT COUNT(*) FROM articles")
        article_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM theme_analyses")
        theme_analysis_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM themes")
        theme_count = cursor.fetchone()[0]
        
        # Vérifier les colonnes RoBERTa
        cursor.execute("PRAGMA table_info(articles)")
        columns = [col[1] for col in cursor.fetchall()]
        
        print(f"\n📊 RÉSUMÉ DE LA BASE DE DONNÉES:")
        print(f"   📰 Articles: {article_count}")
        print(f"   🏷️  Analyses de thèmes: {theme_analysis_count}")
        print(f"   📋 Thèmes: {theme_count}")
        print(f"   🔧 Colonnes articles: {len(columns)}")
        
        # Vérifier les colonnes critiques
        critical_columns = ['analysis_model', 'sentiment_confidence', 'roberta_score']
        for col in critical_columns:
            status = "✅ PRÉSENTE" if col in columns else "❌ MANQUANTE"
            print(f"   {status}: {col}")
        
    except Exception as e:
        print(f"📊 Impossible d'afficher le résumé: {e}")

        # Flask/AJOUT colonnes 4 fromages 
def _add_sentiment_columns(cursor, existing_tables):
    """Ajoute les colonnes pour les sentiments détaillés"""
    if 'articles' in existing_tables:
        cursor.execute("PRAGMA table_info(articles)")
        existing_columns = [column[1] for column in cursor.fetchall()]
        
        # Colonnes pour les 4 catégories RoBERTa
        new_columns = [
            ('detailed_sentiment', 'TEXT'),
            ('sentiment_confidence', 'REAL DEFAULT 0.5'),
            ('roberta_score', 'REAL'),
            ('roberta_label', 'TEXT'),
            ('analysis_model', 'TEXT DEFAULT "traditional"')
        ]
        
        for column_name, column_type in new_columns:
            if column_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE articles ADD COLUMN {column_name} {column_type}")
                    logger.info(f"  ➕ Colonne ajoutée: {column_name}")
                except Exception as e:
                    if "duplicate column" in str(e).lower():
                        logger.debug(f"  ⏭️  Colonne {column_name} existe déjà")
                    else:
                        raise
