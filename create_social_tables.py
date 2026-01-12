#!/usr/bin/env python3
"""
Script pour créer les tables social_posts manquantes
"""

import sys
import logging
from database import DatabaseManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_social_tables():
    """Crée toutes les tables nécessaires pour les réseaux sociaux"""
    db = DatabaseManager()
    conn = db.get_connection()
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
        logger.info("[OK] Table social_posts créée")

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
        logger.info("[OK] Table social_posts_by_country créée")

        # Index pour améliorer les performances
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_social_country_date
            ON social_posts_by_country(country_code, pub_date DESC)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_social_country_relevance
            ON social_posts_by_country(country_code, relevance_score DESC)
        """)
        logger.info("[OK] Index créés")

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
        logger.info("[OK] Table sentiment_comparisons créée")

        conn.commit()
        logger.info("\n🎉 Toutes les tables sociales ont été créées avec succès!")

    except Exception as e:
        logger.error(f"[ERROR] Erreur création tables: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    logger.info("[TOOL] Création des tables réseaux sociaux...\n")
    create_social_tables()
