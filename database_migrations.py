# Flask/database_migrations.py
"""
Migrations de base de données pour ajouter les fonctionnalités avancées
"""

import logging
from typing import Optional
from .database import DatabaseManager

logger = logging.getLogger(__name__)


class DatabaseMigrations:
    """Gestionnaire de migrations de la base de données"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def run_all_migrations(self):
        """Exécute toutes les migrations nécessaires"""
        logger.info("🔄 Démarrage des migrations...")
        
        migrations = [
            ("01_add_bayesian_columns", self._add_bayesian_columns),
            ("02_create_corroboration_table", self._create_corroboration_table),
            ("03_add_indices", self._add_performance_indices),
        ]
        
        for name, migration_func in migrations:
            try:
                if self._should_run_migration(name):
                    logger.info(f"▶️  Exécution migration: {name}")
                    migration_func()
                    self._mark_migration_complete(name)
                    logger.info(f"✅ Migration {name} terminée")
                else:
                    logger.debug(f"⏭️  Migration {name} déjà appliquée")
            except Exception as e:
                logger.error(f"❌ Erreur migration {name}: {e}")
                raise
        
        logger.info("✅ Toutes les migrations terminées")
    
    def _should_run_migration(self, migration_name: str) -> bool:
        """Vérifie si une migration doit être exécutée"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            # Créer la table des migrations si elle n'existe pas
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS migrations (
                    name TEXT PRIMARY KEY,
                    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Vérifier si la migration a déjà été appliquée
            cursor.execute(
                "SELECT name FROM migrations WHERE name = ?",
                (migration_name,)
            )
            
            result = cursor.fetchone()
            return result is None
            
        finally:
            conn.close()
    
    def _mark_migration_complete(self, migration_name: str):
        """Marque une migration comme complétée"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "INSERT INTO migrations (name) VALUES (?)",
                (migration_name,)
            )
            conn.commit()
        finally:
            conn.close()
    
    def _add_bayesian_columns(self):
        """Ajoute les colonnes pour l'analyse bayésienne"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            # Ajouter les colonnes si elles n'existent pas
            columns_to_add = [
                ("bayesian_confidence", "REAL DEFAULT 0.0"),
                ("bayesian_evidence_count", "INTEGER DEFAULT 0"),
                ("original_sentiment_score", "REAL"),
                ("analyzed_at", "DATETIME"),  # Date de l'analyse
            ]
            
            for column_name, column_type in columns_to_add:
                try:
                    cursor.execute(f"""
                        ALTER TABLE articles 
                        ADD COLUMN {column_name} {column_type}
                    """)
                    logger.info(f"  ➕ Colonne ajoutée: {column_name}")
                except Exception as e:
                    if "duplicate column" in str(e).lower():
                        logger.debug(f"  ⏭️  Colonne {column_name} existe déjà")
                    else:
                        raise
            
            conn.commit()
            
        finally:
            conn.close()
    
    def _create_corroboration_table(self):
        """Crée la table des corroborations d'articles"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS article_corroborations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article_id INTEGER NOT NULL,
                    similar_article_id INTEGER NOT NULL,
                    similarity_score REAL NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
                    FOREIGN KEY (similar_article_id) REFERENCES articles(id) ON DELETE CASCADE,
                    UNIQUE(article_id, similar_article_id)
                )
            """)
            
            logger.info("  ➕ Table article_corroborations créée")
            conn.commit()
            
        finally:
            conn.close()
    
    def _add_performance_indices(self):
        """Ajoute des index pour améliorer les performances"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            indices = [
                ("idx_corr_article", "article_corroborations", "article_id"),
                ("idx_corr_similar", "article_corroborations", "similar_article_id"),
                ("idx_corr_score", "article_corroborations", "similarity_score"),
                ("idx_articles_sentiment", "articles", "sentiment_type"),
                ("idx_articles_bayesian_conf", "articles", "bayesian_confidence"),
            ]
            
            for idx_name, table_name, column_name in indices:
                try:
                    cursor.execute(f"""
                        CREATE INDEX IF NOT EXISTS {idx_name} 
                        ON {table_name}({column_name})
                    """)
                    logger.info(f"  ➕ Index créé: {idx_name}")
                except Exception as e:
                    if "already exists" in str(e).lower():
                        logger.debug(f"  ⏭️  Index {idx_name} existe déjà")
                    else:
                        raise
            
            conn.commit()
            
        finally:
            conn.close()
    
    def get_migration_status(self) -> dict:
        """Retourne le statut des migrations"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT name, applied_at 
                FROM migrations 
                ORDER BY applied_at
            """)
            
            migrations = []
            for row in cursor.fetchall():
                migrations.append({
                    'name': row[0],
                    'applied_at': row[1]
                })
            
            return {
                'total': len(migrations),
                'migrations': migrations
            }
            
        except Exception:
            return {'total': 0, 'migrations': []}
        finally:
            conn.close()


def run_migrations(db_manager: DatabaseManager):
    """Point d'entrée pour exécuter les migrations"""
    migrator = DatabaseMigrations(db_manager)
    migrator.run_all_migrations()
