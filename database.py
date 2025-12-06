import sqlite3
import logging
import os
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = "rss_analyzer.db"):
        self.db_path = db_path
        self._init_db()

    def get_connection(self) -> sqlite3.Connection:
        """Retourne une connexion à la base de données"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Initialise la base de données avec les tables nécessaires"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Table des articles - CORRIGÉE AVEC TOUTES LES COLONNES
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    content TEXT,
                    link TEXT UNIQUE,
                    pub_date TIMESTAMP,
                    sentiment_type TEXT,
                    sentiment_score REAL,
                    detailed_sentiment TEXT,
                    roberta_score REAL,
                    analysis_model TEXT,
                    feed_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sentiment_confidence REAL DEFAULT 0.5,
                    bayesian_confidence REAL,
                    bayesian_evidence_count INTEGER DEFAULT 0,
                    analyzed_at TIMESTAMP
                )
            """)

            # Table des thèmes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS themes (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    keywords TEXT,
                    color TEXT DEFAULT '#6366f1',
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Table d'analyse des thèmes
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

            # Index pour améliorer les performances
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_date ON articles(pub_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_sentiment ON articles(sentiment_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_detailed_sentiment ON articles(detailed_sentiment)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_analysis_model ON articles(analysis_model)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_theme_analyses_confidence ON theme_analyses(confidence)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_theme_analyses_article ON theme_analyses(article_id)")

            conn.commit()
            conn.close()
            logger.info("✅ Base de données initialisée avec succès")

        except Exception as e:
            logger.error(f"❌ Erreur initialisation base de données: {e}")
            raise

    def execute_query(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Exécute une requête SELECT et retourne les résultats"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()
            conn.close()
            return results
        except Exception as e:
            logger.error(f"Erreur exécution requête: {e}")
            raise

    def execute_update(self, query: str, params: tuple = ()) -> bool:
        """Exécute une requête UPDATE/INSERT/DELETE"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Erreur exécution mise à jour: {e}")
            return False

    def get_article_count(self) -> int:
        """Retourne le nombre total d'articles"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM articles")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            logger.error(f"Erreur comptage articles: {e}")
            return 0

    # AJOUT DE LA MÉTHODE MANQUANTE
    def get_themes(self) -> List[Dict[str, Any]]:
        """Retourne tous les thèmes"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, keywords, color, description, created_at 
                FROM themes 
                ORDER BY name
            """)
            
            themes = []
            for row in cursor.fetchall():
                theme = {
                    'id': row[0],
                    'name': row[1],
                    'keywords': [],
                    'color': row[3],
                    'description': row[4],
                    'created_at': row[5]
                }
                
                # Parser les keywords JSON
                try:
                    import json
                    theme['keywords'] = json.loads(row[2]) if row[2] else []
                except:
                    theme['keywords'] = row[2].split(',') if row[2] else []
                
                themes.append(theme)
            
            conn.close()
            return themes
        except Exception as e:
            logger.error(f"Erreur récupération thèmes: {e}")
            return []
