import sqlite3
import logging
import os
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = None):
        """
        Initialise le gestionnaire de base de données

        Args:
            db_path: Chemin vers la base de données. Si None, utilise instance/rss_analyzer.db
        """
        if db_path is None:
            # Déterminer le chemin du répertoire instance
            # Si on est dans Flask/, instance est dans ../instance/
            # Si on est à la racine, instance est dans ./instance/
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)  # Remonter d'un niveau depuis Flask/
            instance_dir = os.path.join(project_root, 'instance')

            # Créer le répertoire instance s'il n'existe pas
            os.makedirs(instance_dir, exist_ok=True)

            db_path = os.path.join(instance_dir, 'rss_analyzer.db')
            logger.info(f"[DB] Base de données RSS: {db_path}")

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
                    analyzed_at TIMESTAMP,
                    harmonized INTEGER DEFAULT 0,
                    cluster_size INTEGER DEFAULT 1,
                    analysis_metadata TEXT
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
                    active INTEGER DEFAULT 1,
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

            # Table des flux RSS configurables
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rss_feeds (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    category TEXT DEFAULT 'general',
                    quality TEXT DEFAULT 'medium',
                    language TEXT DEFAULT 'fr',
                    enabled BOOLEAN DEFAULT 1,
                    is_default BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # ========================================================================
            # TABLES OSoME - AJOUTÉES POUR LA PROPAGATION ET L'ANALYSE DE RÉSEAUX
            # ========================================================================

            # Table des propagations sociales
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS social_propagation (
                    propagation_id TEXT PRIMARY KEY,
                    origin_post_id TEXT NOT NULL,
                    origin_source TEXT,
                    origin_timestamp DATETIME,
                    node_post_id TEXT NOT NULL,
                    node_source TEXT,
                    node_timestamp DATETIME,
                    node_author TEXT,
                    hop_distance INTEGER,
                    propagation_speed_hours REAL,
                    engagement_score REAL,
                    virality_coefficient REAL,
                    sentiment_shift REAL,
                    confidence REAL
                )
            """)

            # Table des réseaux OSoME
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS osome_networks (
                    network_id TEXT PRIMARY KEY,
                    topic TEXT,
                    start_date DATETIME,
                    end_date DATETIME,
                    node_count INTEGER,
                    edge_count INTEGER,
                    max_depth INTEGER,
                    avg_hop_time REAL,
                    network_density REAL,
                    propagation_pattern TEXT,
                    cascade_type TEXT,
                    graph_data TEXT,
                    analysis_metadata TEXT,
                    created_at DATETIME
                )
            """)

            # Index pour améliorer les performances
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_date ON articles(pub_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_sentiment ON articles(sentiment_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_detailed_sentiment ON articles(detailed_sentiment)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_analysis_model ON articles(analysis_model)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_theme_analyses_confidence ON theme_analyses(confidence)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_theme_analyses_article ON theme_analyses(article_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rss_feeds_enabled ON rss_feeds(enabled)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rss_feeds_category ON rss_feeds(category)")
            
            # Index pour les tables OSoME
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_social_propagation_timestamp ON social_propagation(node_timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_social_propagation_origin ON social_propagation(origin_post_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_social_propagation_node ON social_propagation(node_post_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_osome_networks_topic ON osome_networks(topic)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_osome_networks_created ON osome_networks(created_at)")

            conn.commit()
            conn.close()
            logger.info("[OK] Base de données initialisée avec succès")

            # Migrer les flux par défaut si la table est vide
            self.migrate_default_feeds_if_empty()

        except Exception as e:
            logger.error(f"[ERROR] Erreur initialisation base de données: {e}")
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

    # ========================================================================
    # MÉTHODES POUR LES TABLES OSoME
    # ========================================================================

    def get_propagation_count(self) -> int:
        """Retourne le nombre total de propagations"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM social_propagation")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            logger.error(f"Erreur comptage propagations: {e}")
            return 0

    def get_network_count(self) -> int:
        """Retourne le nombre total de réseaux OSoME"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM osome_networks")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            logger.error(f"Erreur comptage réseaux: {e}")
            return 0

    # ========================================================================
    # MÉTHODES CRUD POUR LES FLUX RSS (EXISTANTES)
    # ========================================================================

    def get_rss_feeds(self, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """
        Récupère tous les flux RSS configurés

        Args:
            enabled_only: Si True, ne retourne que les flux activés

        Returns:
            Liste des flux RSS
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            if enabled_only:
                cursor.execute("""
                    SELECT id, url, name, category, quality, language, enabled, is_default, created_at, updated_at
                    FROM rss_feeds
                    WHERE enabled = 1
                    ORDER BY is_default DESC, name ASC
                """)
            else:
                cursor.execute("""
                    SELECT id, url, name, category, quality, language, enabled, is_default, created_at, updated_at
                    FROM rss_feeds
                    ORDER BY is_default DESC, name ASC
                """)

            feeds = []
            for row in cursor.fetchall():
                feeds.append({
                    'id': row[0],
                    'url': row[1],
                    'name': row[2],
                    'category': row[3],
                    'quality': row[4],
                    'language': row[5],
                    'enabled': bool(row[6]),
                    'is_default': bool(row[7]),
                    'created_at': row[8],
                    'updated_at': row[9]
                })

            conn.close()
            return feeds
        except Exception as e:
            logger.error(f"[ERROR] Erreur récupération flux RSS: {e}")
            return []

    def add_rss_feed(self, url: str, name: str, category: str = 'general',
                     quality: str = 'medium', language: str = 'fr',
                     is_default: bool = False) -> Optional[int]:
        """
        Ajoute un nouveau flux RSS

        Returns:
            ID du flux créé ou None en cas d'erreur
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO rss_feeds (url, name, category, quality, language, is_default)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (url, name, category, quality, language, 1 if is_default else 0))

            feed_id = cursor.lastrowid
            conn.commit()
            conn.close()

            logger.info(f"[OK] Flux RSS ajouté: {name} ({url})")
            return feed_id
        except sqlite3.IntegrityError:
            logger.warning(f"[WARN] Flux RSS déjà existant: {url}")
            return None
        except Exception as e:
            logger.error(f"[ERROR] Erreur ajout flux RSS: {e}")
            return None

    def update_rss_feed(self, feed_id: int, **kwargs) -> bool:
        """
        Met à jour un flux RSS

        Args:
            feed_id: ID du flux
            **kwargs: Champs à mettre à jour (name, category, quality, language, enabled)

        Returns:
            True si succès
        """
        try:
            allowed_fields = ['url', 'name', 'category', 'quality', 'language', 'enabled']
            updates = []
            values = []

            for field, value in kwargs.items():
                if field in allowed_fields:
                    updates.append(f"{field} = ?")
                    values.append(value)

            if not updates:
                return False

            # Ajouter updated_at
            updates.append("updated_at = CURRENT_TIMESTAMP")
            values.append(feed_id)

            query = f"UPDATE rss_feeds SET {', '.join(updates)} WHERE id = ?"

            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, tuple(values))
            conn.commit()
            conn.close()

            logger.info(f"[OK] Flux RSS mis à jour: ID {feed_id}")
            return True
        except Exception as e:
            logger.error(f"[ERROR] Erreur mise à jour flux RSS: {e}")
            return False

    def delete_rss_feed(self, feed_id: int) -> bool:
        """
        Supprime un flux RSS

        Args:
            feed_id: ID du flux à supprimer

        Returns:
            True si succès
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM rss_feeds WHERE id = ?", (feed_id,))
            conn.commit()
            conn.close()

            logger.info(f"[OK] Flux RSS supprimé: ID {feed_id}")
            return True
        except Exception as e:
            logger.error(f"[ERROR] Erreur suppression flux RSS: {e}")
            return False

    def reset_rss_feeds_to_default(self) -> bool:
        """
        Réinitialise les flux RSS aux valeurs par défaut depuis FEEDS_CATALOG

        Returns:
            True si succès
        """
        try:
            # Importer le catalogue par défaut
            from .rss_aggregator import RSSAggregator

            conn = self.get_connection()
            cursor = conn.cursor()

            # Supprimer tous les flux existants
            cursor.execute("DELETE FROM rss_feeds")

            # Insérer les flux par défaut
            aggregator = RSSAggregator()
            for feed_key, feed_data in aggregator.FEEDS_CATALOG.items():
                cursor.execute("""
                    INSERT INTO rss_feeds (url, name, category, quality, language, is_default)
                    VALUES (?, ?, ?, ?, ?, 1)
                """, (
                    feed_data['url'],
                    feed_data['name'],
                    feed_data.get('category', 'general'),
                    feed_data.get('quality', 'medium'),
                    feed_data.get('language', 'en')
                ))

            conn.commit()
            conn.close()

            logger.info(f"[OK] Flux RSS réinitialisés aux valeurs par défaut")
            return True
        except Exception as e:
            logger.error(f"[ERROR] Erreur réinitialisation flux RSS: {e}")
            return False

    def migrate_default_feeds_if_empty(self) -> None:
        """
        Migre les flux par défaut depuis FEEDS_CATALOG si la table est vide
        (Appelée automatiquement à l'initialisation)
        """
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Vérifier si la table est vide
            cursor.execute("SELECT COUNT(*) FROM rss_feeds")
            count = cursor.fetchone()[0]
            conn.close()

            if count == 0:
                logger.info("📦 Table rss_feeds vide, migration des flux par défaut...")
                self.reset_rss_feeds_to_default()
        except Exception as e:
            logger.error(f"[ERROR] Erreur migration flux par défaut: {e}")
