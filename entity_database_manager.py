# Flask/entity_database_manager.py - Gestion BDD pour entités géopolitiques
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from .database import DatabaseManager

logger = logging.getLogger(__name__)

class EntityDatabaseManager:
    """
    Gestionnaire de base de données pour les entités géopolitiques
    Stocke et analyse les entités extraites des articles
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self._init_tables()
    
    def _init_tables(self):
        """Crée les tables pour les entités géopolitiques"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        # Table principale des entités
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS geopolitical_entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_text TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                category TEXT NOT NULL,
                first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
                occurrence_count INTEGER DEFAULT 1,
                UNIQUE(entity_text, entity_type)
            )
        """)
        
        # Table de liaison article-entité
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS article_entities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER NOT NULL,
                entity_id INTEGER NOT NULL,
                position_start INTEGER,
                position_end INTEGER,
                context TEXT,
                extracted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
                FOREIGN KEY (entity_id) REFERENCES geopolitical_entities(id) ON DELETE CASCADE,
                UNIQUE(article_id, entity_id)
            )
        """)
        
        # Table des relations entre entités (co-occurrence)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entity_relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity1_id INTEGER NOT NULL,
                entity2_id INTEGER NOT NULL,
                relation_type TEXT DEFAULT 'co-occurrence',
                strength REAL DEFAULT 1.0,
                article_count INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (entity1_id) REFERENCES geopolitical_entities(id) ON DELETE CASCADE,
                FOREIGN KEY (entity2_id) REFERENCES geopolitical_entities(id) ON DELETE CASCADE,
                UNIQUE(entity1_id, entity2_id, relation_type)
            )
        """)
        
        # Table des statistiques temporelles
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS entity_temporal_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id INTEGER NOT NULL,
                date DATE NOT NULL,
                mention_count INTEGER DEFAULT 1,
                sentiment_avg REAL,
                FOREIGN KEY (entity_id) REFERENCES geopolitical_entities(id) ON DELETE CASCADE,
                UNIQUE(entity_id, date)
            )
        """)
        
        # Index pour performances
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entities_text ON geopolitical_entities(entity_text)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entities_type ON geopolitical_entities(entity_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entities_category ON geopolitical_entities(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_article_entities_article ON article_entities(article_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_article_entities_entity ON article_entities(entity_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_entity_relations_entities ON entity_relations(entity1_id, entity2_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_temporal_date ON entity_temporal_stats(date)")
        
        conn.commit()
        conn.close()
        logger.info("✅ Tables d'entités géopolitiques créées")
    
    def store_article_entities(self, article_id: int, entities: Dict[str, Any]) -> bool:
        """
        Stocke les entités extraites d'un article
        
        Args:
            article_id: ID de l'article
            entities: Dictionnaire d'entités (résultat de GeopoliticalEntityExtractor)
            
        Returns:
            True si succès
        """
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            entity_ids = []
            
            # Mapper catégories
            category_map = {
                'locations': 'location',
                'organizations': 'organization',
                'persons': 'person',
                'events': 'event',
                'groups': 'group'
            }
            
            # Traiter chaque catégorie
            for category_key, entity_list in entities.items():
                if category_key == 'all_entities':
                    continue
                
                category = category_map.get(category_key, 'other')
                
                for entity in entity_list:
                    entity_text = entity['text']
                    entity_type = entity['label']
                    
                    # Insérer ou mettre à jour l'entité
                    cursor.execute("""
                        INSERT INTO geopolitical_entities 
                        (entity_text, entity_type, category, last_seen, occurrence_count)
                        VALUES (?, ?, ?, CURRENT_TIMESTAMP, 1)
                        ON CONFLICT(entity_text, entity_type) DO UPDATE SET
                            last_seen = CURRENT_TIMESTAMP,
                            occurrence_count = occurrence_count + 1
                    """, (entity_text, entity_type, category))
                    
                    # Récupérer l'ID de l'entité
                    cursor.execute("""
                        SELECT id FROM geopolitical_entities
                        WHERE entity_text = ? AND entity_type = ?
                    """, (entity_text, entity_type))
                    
                    entity_id = cursor.fetchone()[0]
                    entity_ids.append(entity_id)
                    
                    # Lier à l'article
                    cursor.execute("""
                        INSERT OR IGNORE INTO article_entities
                        (article_id, entity_id, position_start, position_end, context)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        article_id,
                        entity_id,
                        entity.get('start', -1),
                        entity.get('end', -1),
                        entity.get('context', '')[:500]  # Limiter contexte
                    ))
            
            # Créer les relations (co-occurrence)
            self._create_relations(cursor, entity_ids, article_id)
            
            # Mettre à jour statistiques temporelles
            self._update_temporal_stats(cursor, entity_ids, article_id)
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ {len(entity_ids)} entités stockées pour article {article_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur stockage entités article {article_id}: {e}")
            return False
    
    def _create_relations(self, cursor, entity_ids: List[int], article_id: int):
        """Crée les relations de co-occurrence entre entités"""
        for i, entity1_id in enumerate(entity_ids):
            for entity2_id in entity_ids[i+1:]:
                # Toujours mettre le plus petit ID en premier
                if entity1_id > entity2_id:
                    entity1_id, entity2_id = entity2_id, entity1_id
                
                cursor.execute("""
                    INSERT INTO entity_relations
                    (entity1_id, entity2_id, article_count, updated_at)
                    VALUES (?, ?, 1, CURRENT_TIMESTAMP)
                    ON CONFLICT(entity1_id, entity2_id, relation_type) DO UPDATE SET
                        article_count = article_count + 1,
                        strength = strength + 0.1,
                        updated_at = CURRENT_TIMESTAMP
                """, (entity1_id, entity2_id))
    
    def _update_temporal_stats(self, cursor, entity_ids: List[int], article_id: int):
        """Met à jour les statistiques temporelles"""
        # Récupérer date et sentiment de l'article
        cursor.execute("""
            SELECT DATE(pub_date), sentiment_score
            FROM articles
            WHERE id = ?
        """, (article_id,))
        
        row = cursor.fetchone()
        if not row:
            return
        
        date, sentiment = row
        
        for entity_id in entity_ids:
            cursor.execute("""
                INSERT INTO entity_temporal_stats
                (entity_id, date, mention_count, sentiment_avg)
                VALUES (?, ?, 1, ?)
                ON CONFLICT(entity_id, date) DO UPDATE SET
                    mention_count = mention_count + 1,
                    sentiment_avg = ((sentiment_avg * (mention_count - 1)) + ?) / mention_count
            """, (entity_id, date, sentiment, sentiment))
    
    def get_entity_statistics(self, entity_text: str) -> Dict[str, Any]:
        """
        Récupère les statistiques d'une entité
        
        Args:
            entity_text: Texte de l'entité
            
        Returns:
            Statistiques complètes
        """
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        # Info de base
        cursor.execute("""
            SELECT id, entity_type, category, first_seen, last_seen, occurrence_count
            FROM geopolitical_entities
            WHERE entity_text = ?
        """, (entity_text,))
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            return {}
        
        entity_id, entity_type, category, first_seen, last_seen, occurrence = row
        
        # Nombre d'articles
        cursor.execute("""
            SELECT COUNT(DISTINCT article_id)
            FROM article_entities
            WHERE entity_id = ?
        """, (entity_id,))
        article_count = cursor.fetchone()[0]
        
        # Sentiment moyen
        cursor.execute("""
            SELECT AVG(a.sentiment_score)
            FROM articles a
            JOIN article_entities ae ON a.id = ae.article_id
            WHERE ae.entity_id = ?
        """, (entity_id,))
        avg_sentiment = cursor.fetchone()[0] or 0.0
        
        # Relations principales
        cursor.execute("""
            SELECT e.entity_text, e.category, er.strength, er.article_count
            FROM entity_relations er
            JOIN geopolitical_entities e ON (
                e.id = CASE WHEN er.entity1_id = ? THEN er.entity2_id ELSE er.entity1_id END
            )
            WHERE er.entity1_id = ? OR er.entity2_id = ?
            ORDER BY er.strength DESC
            LIMIT 10
        """, (entity_id, entity_id, entity_id))
        
        relations = [
            {
                'entity': row[0],
                'category': row[1],
                'strength': row[2],
                'article_count': row[3]
            }
            for row in cursor.fetchall()
        ]
        
        # Évolution temporelle (30 derniers jours)
        cursor.execute("""
            SELECT date, mention_count, sentiment_avg
            FROM entity_temporal_stats
            WHERE entity_id = ?
            ORDER BY date DESC
            LIMIT 30
        """, (entity_id,))
        
        temporal = [
            {'date': row[0], 'mentions': row[1], 'sentiment': row[2]}
            for row in cursor.fetchall()
        ]
        
        conn.close()
        
        return {
            'entity_text': entity_text,
            'entity_type': entity_type,
            'category': category,
            'first_seen': first_seen,
            'last_seen': last_seen,
            'occurrence_count': occurrence,
            'article_count': article_count,
            'avg_sentiment': avg_sentiment,
            'top_relations': relations,
            'temporal_evolution': temporal
        }
    
    def get_top_entities(self, category: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Récupère les entités les plus fréquentes
        
        Args:
            category: Catégorie à filtrer (location, organization, person, etc.)
            limit: Nombre de résultats
            
        Returns:
            Liste d'entités avec statistiques
        """
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT 
                e.entity_text,
                e.entity_type,
                e.category,
                e.occurrence_count,
                COUNT(DISTINCT ae.article_id) as article_count,
                AVG(a.sentiment_score) as avg_sentiment
            FROM geopolitical_entities e
            LEFT JOIN article_entities ae ON e.id = ae.entity_id
            LEFT JOIN articles a ON ae.article_id = a.id
        """
        
        params = []
        if category:
            query += " WHERE e.category = ?"
            params.append(category)
        
        query += """
            GROUP BY e.id
            ORDER BY e.occurrence_count DESC
            LIMIT ?
        """
        params.append(limit)
        
        cursor.execute(query, params)
        
        entities = [
            {
                'entity': row[0],
                'type': row[1],
                'category': row[2],
                'mentions': row[3],
                'articles': row[4],
                'avg_sentiment': row[5] or 0.0
            }
            for row in cursor.fetchall()
        ]
        
        conn.close()
        return entities
    
    def get_entity_network(self, min_strength: float = 1.0, limit: int = 100) -> Dict[str, Any]:
        """
        Récupère le réseau d'entités pour visualisation
        
        Args:
            min_strength: Force minimale des relations
            limit: Nombre maximal de nœuds
            
        Returns:
            Données de réseau (nodes, links)
        """
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        # Récupérer les entités principales
        cursor.execute("""
            SELECT id, entity_text, category, occurrence_count
            FROM geopolitical_entities
            ORDER BY occurrence_count DESC
            LIMIT ?
        """, (limit,))
        
        nodes = []
        entity_ids = set()
        
        for row in cursor.fetchall():
            entity_id, text, category, count = row
            entity_ids.add(entity_id)
            nodes.append({
                'id': entity_id,
                'label': text,
                'category': category,
                'size': count
            })
        
        # Récupérer les relations
        placeholders = ','.join('?' * len(entity_ids))
        cursor.execute(f"""
            SELECT entity1_id, entity2_id, strength, article_count
            FROM entity_relations
            WHERE (entity1_id IN ({placeholders}) AND entity2_id IN ({placeholders}))
                AND strength >= ?
            ORDER BY strength DESC
        """, list(entity_ids) + list(entity_ids) + [min_strength])
        
        links = [
            {
                'source': row[0],
                'target': row[1],
                'strength': row[2],
                'articles': row[3]
            }
            for row in cursor.fetchall()
        ]
        
        conn.close()
        
        return {
            'nodes': nodes,
            'links': links
        }
    
    def search_entities(self, search_term: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Recherche d'entités par texte
        
        Args:
            search_term: Terme de recherche
            category: Catégorie optionnelle
            
        Returns:
            Liste d'entités correspondantes
        """
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT entity_text, entity_type, category, occurrence_count
            FROM geopolitical_entities
            WHERE entity_text LIKE ?
        """
        params = [f"%{search_term}%"]
        
        if category:
            query += " AND category = ?"
            params.append(category)
        
        query += " ORDER BY occurrence_count DESC LIMIT 50"
        
        cursor.execute(query, params)
        
        results = [
            {
                'entity': row[0],
                'type': row[1],
                'category': row[2],
                'mentions': row[3]
            }
            for row in cursor.fetchall()
        ]
        
        conn.close()
        return results
