"""
Enhancement de la base de données pour les réseaux sociaux
Ajout des tables manquantes pour système résilient et cartographie OSoME
"""

import sqlite3
import logging
import sys
from datetime import datetime

# Fix encoding pour Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'ignore')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'ignore')

logger = logging.getLogger(__name__)

class SocialDatabaseEnhancement:
    """Amélioration de la structure BD pour réseaux sociaux"""

    def __init__(self, db_path: str = "../rss_analyzer.db"):
        self.db_path = db_path

    def execute(self):
        """Exécute l'amélioration"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            print("=" * 70)
            print("[TOOL] ENHANCEMENT DATABASE - RÉSEAUX SOCIAUX")
            print("=" * 70)

            # Table des sources sociales (pour traçabilité)
            print("\n📦 Création table social_sources...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS social_sources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id TEXT UNIQUE NOT NULL,
                    source_type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    url TEXT,
                    description TEXT,

                    -- Configuration
                    enabled BOOLEAN DEFAULT 1,
                    fetch_interval INTEGER DEFAULT 3600,
                    config TEXT,

                    -- Statistiques
                    total_posts INTEGER DEFAULT 0,
                    last_fetch_at TIMESTAMP,
                    last_post_at TIMESTAMP,
                    fetch_errors INTEGER DEFAULT 0,

                    -- Métadonnées
                    category TEXT,
                    quality_score REAL DEFAULT 0.5,

                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("[OK] Table social_sources créée")

            # Table de propagation pour OSoME
            print("\n📦 Création table social_propagation...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS social_propagation (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    propagation_id TEXT UNIQUE NOT NULL,

                    -- Origine
                    origin_post_id TEXT,
                    origin_source TEXT,
                    origin_timestamp TIMESTAMP,
                    origin_author TEXT,

                    -- Contenu propagé
                    content_hash TEXT NOT NULL,
                    topic TEXT,
                    keywords TEXT,
                    content_excerpt TEXT,

                    -- Noeud de propagation (post qui propage)
                    node_post_id TEXT NOT NULL,
                    node_source TEXT NOT NULL,
                    node_timestamp TIMESTAMP NOT NULL,
                    node_author TEXT,

                    -- Métriques de propagation
                    hop_distance INTEGER DEFAULT 0,
                    propagation_speed_hours REAL,
                    engagement_score INTEGER DEFAULT 0,
                    sentiment_shift REAL,
                    virality_coefficient REAL,

                    -- Relations
                    parent_propagation_id TEXT,

                    -- Métadonnées
                    propagation_type TEXT,
                    detection_method TEXT,
                    confidence REAL,
                    metadata TEXT,

                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("[OK] Table social_propagation créée")

            # Table OSoME Networks (graphes de propagation)
            print("\n📦 Création table osome_networks...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS osome_networks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    network_id TEXT UNIQUE NOT NULL,

                    -- Identification
                    topic TEXT NOT NULL,
                    keywords TEXT,

                    -- Période d'analyse
                    start_date TIMESTAMP NOT NULL,
                    end_date TIMESTAMP NOT NULL,

                    -- Métriques réseau
                    node_count INTEGER DEFAULT 0,
                    edge_count INTEGER DEFAULT 0,
                    max_depth INTEGER DEFAULT 0,
                    avg_hop_time REAL,

                    -- Sources impliquées
                    sources TEXT,
                    primary_source TEXT,

                    -- Analyse
                    network_density REAL,
                    clustering_coefficient REAL,
                    central_nodes TEXT,
                    influencers TEXT,

                    -- Patterns détectés
                    propagation_pattern TEXT,
                    cascade_type TEXT,

                    -- Métadonnées
                    graph_data TEXT,
                    analysis_metadata TEXT,

                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("[OK] Table osome_networks créée")

            # Table de stockage des comparaisons enrichies
            print("\n📦 Création table social_rss_comparisons...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS social_rss_comparisons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    comparison_id TEXT UNIQUE NOT NULL,

                    -- Période
                    start_date TIMESTAMP NOT NULL,
                    end_date TIMESTAMP NOT NULL,
                    period_days INTEGER,

                    -- Thème analysé
                    topic TEXT,
                    keywords TEXT,

                    -- Métriques RSS (doxa médiatique)
                    rss_article_count INTEGER DEFAULT 0,
                    rss_sentiment_avg REAL,
                    rss_sentiment_std REAL,
                    rss_positive_pct REAL,
                    rss_negative_pct REAL,
                    rss_neutral_pct REAL,
                    rss_top_themes TEXT,

                    -- Métriques Social (inconscient populaire)
                    social_post_count INTEGER DEFAULT 0,
                    social_sentiment_avg REAL,
                    social_sentiment_std REAL,
                    social_positive_pct REAL,
                    social_negative_pct REAL,
                    social_neutral_pct REAL,
                    social_engagement_total INTEGER DEFAULT 0,
                    social_top_themes TEXT,

                    -- Analyse comparative (Facteur Z v2)
                    factor_z REAL,
                    factor_z_interpretation TEXT,
                    tension_level TEXT,
                    divergence_score REAL,
                    sentiment_gap REAL,
                    narrative_divergence TEXT,

                    -- Events détectés
                    events_count INTEGER DEFAULT 0,
                    events_data TEXT,
                    segments_count INTEGER DEFAULT 0,

                    -- Insights
                    key_differences TEXT,
                    recommendations TEXT,

                    -- Métadonnées
                    analysis_version TEXT,
                    analyzed_by TEXT,
                    metadata TEXT,

                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("[OK] Table social_rss_comparisons créée")

            # Index de performance
            print("\n[DATA] Création des index...")

            indexes = [
                ("idx_social_sources_type", "social_sources(source_type)"),
                ("idx_social_sources_enabled", "social_sources(enabled)"),

                ("idx_social_prop_origin", "social_propagation(origin_post_id)"),
                ("idx_social_prop_node", "social_propagation(node_post_id)"),
                ("idx_social_prop_hash", "social_propagation(content_hash)"),
                ("idx_social_prop_timestamp", "social_propagation(node_timestamp)"),
                ("idx_social_prop_topic", "social_propagation(topic)"),

                ("idx_osome_topic", "osome_networks(topic)"),
                ("idx_osome_dates", "osome_networks(start_date, end_date)"),

                ("idx_comp_topic", "social_rss_comparisons(topic)"),
                ("idx_comp_dates", "social_rss_comparisons(start_date, end_date)"),
                ("idx_comp_factor_z", "social_rss_comparisons(factor_z)"),
            ]

            for idx_name, idx_def in indexes:
                cursor.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {idx_def}")
                print(f"[OK] Index {idx_name}")

            # Insérer sources par défaut
            print("\n[NOTE] Insertion des sources par défaut...")
            default_sources = [
                ('reddit_worldnews', 'reddit', 'Reddit WorldNews',
                 'https://www.reddit.com/r/worldnews', 'Actualités mondiales', 'news',
                 '{"subreddit": "worldnews", "sort": "hot", "limit": 100}'),

                ('reddit_geopolitics', 'reddit', 'Reddit Geopolitics',
                 'https://www.reddit.com/r/geopolitics', 'Discussions géopolitiques', 'geopolitics',
                 '{"subreddit": "geopolitics", "sort": "hot", "limit": 100}'),

                ('youtube_news', 'youtube', 'YouTube News Comments',
                 'https://www.youtube.com', 'Commentaires actualités', 'news',
                 '{"max_comments": 100}'),

                ('nitter_geopolitics', 'nitter', 'Nitter Geopolitics',
                 'https://nitter.net', 'Tweets géopolitiques', 'geopolitics',
                 '{"query": "geopolitics OR diplomacy", "limit": 50}'),

                ('hackernews', 'hackernews', 'Hacker News',
                 'https://news.ycombinator.com', 'Tech & discussions', 'tech',
                 '{"limit": 50}'),
            ]

            for source in default_sources:
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO social_sources
                        (source_id, source_type, name, url, description, category, config)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, source)
                    print(f"[OK] Source {source[2]}")
                except Exception as e:
                    print(f"[WARN] Source {source[2]}: {e}")

            conn.commit()

            # Statistiques
            print("\n" + "=" * 70)
            print("[DATA] STATISTIQUES")
            print("=" * 70)

            tables = {
                'social_posts': 'Posts sociaux',
                'social_sources': 'Sources',
                'social_propagation': 'Propagations (OSoME)',
                'osome_networks': 'Réseaux OSoME',
                'social_rss_comparisons': 'Comparaisons RSS/Social'
            }

            for table, label in tables.items():
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"📦 {label}: {count} entrées")

            conn.close()

            print("\n" + "=" * 70)
            print("[OK] ENHANCEMENT TERMINÉ AVEC SUCCÈS")
            print("=" * 70)
            print("\n[NOTE] Structure complète:")
            print("   ✓ social_posts (existante)")
            print("   ✓ social_sources (tracking des sources)")
            print("   ✓ social_propagation (données pour OSoME)")
            print("   ✓ osome_networks (graphes de propagation)")
            print("   ✓ social_rss_comparisons (historique comparaisons)")

            return True

        except Exception as e:
            logger.error(f"[ERROR] Erreur enhancement: {e}")
            print(f"\n[ERROR] Erreur: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Point d'entrée"""
    enhancement = SocialDatabaseEnhancement()
    success = enhancement.execute()

    if success:
        print("\n[OK] Base de données améliorée!")
        print("[NOTE] Prochaines étapes:")
        print("   1. Améliorer la collecte Reddit avec persistance")
        print("   2. Améliorer la collecte YouTube avec persistance")
        print("   3. Développer le système de détection de propagation")
        print("   4. Créer l'interface OSoME")
    else:
        print("\n[ERROR] Enhancement échoué. Vérifier les logs.")

    return success


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
