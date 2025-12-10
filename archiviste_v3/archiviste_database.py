"""
Gestionnaire de base de données pour Archiviste v3.0
"""

import sqlite3
import json
import logging
import pickle
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import os
import sys

logger = logging.getLogger(__name__)

# Ajouter le chemin pour pouvoir importer HistoricalItem
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Importer HistoricalItem
try:
    from historical_item import HistoricalItem
    logger.info("✅ HistoricalItem importé dans archiviste_database")
except ImportError as e:
    logger.error(f"❌ Erreur import HistoricalItem dans archiviste_database: {e}")
    
    # Classe de secours
    class HistoricalItem:
        def __init__(self, archive_data):
            self.identifier = archive_data.get('identifier', '')
            self.title = archive_data.get('title', '')
            self.description = archive_data.get('description', '')
            self.date = archive_data.get('date', '')
            self.year = archive_data.get('year', 0)
            self.language = archive_data.get('language', '')
            self.creator = archive_data.get('creator', '')
            self.publisher = archive_data.get('publisher', '')
            self.subject = archive_data.get('subject', [])
            self.downloads = archive_data.get('downloads', 0)
            self.source_url = f"https://archive.org/details/{self.identifier}" if self.identifier else ''
            self.content = ''
            self.entities = []
            self.themes = []
            self.geopolitical_relevance = 0.0
            self.processed_at = None
        
        @classmethod
        def from_dict(cls, data):
            archive_data = {
                'identifier': data.get('identifier', ''),
                'title': data.get('title', ''),
                'description': data.get('description', ''),
                'date': data.get('date', ''),
                'year': data.get('year', 0),
                'language': data.get('language', ''),
                'creator': data.get('creator', ''),
                'publisher': data.get('publisher', ''),
                'subject': data.get('subject', []),
                'downloads': data.get('downloads', 0)
            }
            item = cls(archive_data)
            item.entities = data.get('entities', [])
            item.themes = data.get('themes', [])
            item.geopolitical_relevance = data.get('geopolitical_relevance', 0.0)
            return item
        
        def to_dict(self):
            return {
                'identifier': self.identifier,
                'title': self.title,
                'description': self.description,
                'date': self.date,
                'year': self.year,
                'language': self.language,
                'creator': self.creator,
                'publisher': self.publisher,
                'subject': self.subject,
                'downloads': self.downloads,
                'source_url': self.source_url,
                'content': self.content,
                'entities': self.entities,
                'themes': self.themes,
                'geopolitical_relevance': self.geopolitical_relevance,
                'processed_at': self.processed_at.isoformat() if self.processed_at else None
            }

class ArchivisteDatabase:
    """Base de données spécialisée pour l'Archiviste v3.0"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self._init_tables()
    
    def _init_tables(self):
        """Initialise les tables nécessaires pour Archiviste v3"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            # Table des items historiques
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS archiviste_v3_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    identifier TEXT UNIQUE NOT NULL,
                    title TEXT,
                    description TEXT,
                    date TEXT,
                    year INTEGER,
                    language TEXT,
                    creator TEXT,
                    publisher TEXT,
                    subject TEXT,
                    downloads INTEGER DEFAULT 0,
                    source_url TEXT,
                    content TEXT,
                    entities TEXT,
                    themes TEXT,
                    geopolitical_relevance REAL DEFAULT 0.0,
                    processed_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table des embeddings vectoriels
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS archiviste_v3_embeddings (
                    item_identifier TEXT PRIMARY KEY,
                    embedding_vector BLOB,
                    entities TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (item_identifier) REFERENCES archiviste_v3_items(identifier)
                )
            """)
            
            # Table des analyses de période
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS archiviste_v3_period_analyses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    period_key TEXT NOT NULL,
                    theme_id INTEGER NOT NULL,
                    total_items INTEGER DEFAULT 0,
                    items_analyzed INTEGER DEFAULT 0,
                    statistics TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (theme_id) REFERENCES themes(id)
                )
            """)
            
            # Table des analogies historiques
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS archiviste_v3_analogies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_text TEXT,
                    query_embedding BLOB,
                    item_identifier TEXT,
                    similarity_score REAL,
                    shared_entities TEXT,
                    summary TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (item_identifier) REFERENCES archiviste_v3_items(identifier)
                )
            """)
            
            # Index pour performances
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_archiviste_items_year ON archiviste_v3_items(year)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_archiviste_items_date ON archiviste_v3_items(date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_archiviste_embeddings ON archiviste_v3_embeddings(item_identifier)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_archiviste_period_key ON archiviste_v3_period_analyses(period_key)")
            
            conn.commit()
            logger.info("✅ Tables Archiviste v3 créées")
            
        except Exception as e:
            logger.error(f"❌ Erreur création tables Archiviste v3: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def save_historical_item(self, item: HistoricalItem) -> bool:
        """Sauvegarde un item historique"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            # Sauvegarder l'item principal
            cursor.execute("""
                INSERT OR REPLACE INTO archiviste_v3_items
                (identifier, title, description, date, year, language, creator, publisher,
                 subject, downloads, source_url, content, entities, themes, 
                 geopolitical_relevance, processed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item.identifier,
                item.title,
                item.description,
                item.date,
                item.year,
                item.language,
                item.creator,
                item.publisher,
                json.dumps(item.subject) if isinstance(item.subject, (list, dict)) else str(item.subject),
                item.downloads,
                item.source_url,
                item.content[:10000],  # Limiter la taille
                json.dumps(item.entities),
                json.dumps(item.themes),
                item.geopolitical_relevance,
                item.processed_at or datetime.now()
            ))
            
            # Sauvegarder l'embedding si disponible
            if hasattr(item, 'embedding') and item.embedding:
                cursor.execute("""
                    INSERT OR REPLACE INTO archiviste_v3_embeddings
                    (item_identifier, embedding_vector, entities)
                    VALUES (?, ?, ?)
                """, (
                    item.identifier,
                    pickle.dumps(item.embedding),
                    json.dumps(item.entities)
                ))
            
            conn.commit()
            logger.debug(f"✅ Item sauvegardé: {item.identifier}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde item {item.identifier}: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_historical_item(self, identifier: str) -> Optional[HistoricalItem]:
        """Récupère un item historique par son identifiant"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM archiviste_v3_items WHERE identifier = ?
            """, (identifier,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            # Construire les données de l'item
            columns = [description[0] for description in cursor.description]
            item_data = dict(zip(columns, row))
            
            # Convertir les champs JSON
            if item_data.get('subject'):
                try:
                    item_data['subject'] = json.loads(item_data['subject'])
                except:
                    item_data['subject'] = []
            
            if item_data.get('entities'):
                try:
                    item_data['entities'] = json.loads(item_data['entities'])
                except:
                    item_data['entities'] = []
            
            if item_data.get('themes'):
                try:
                    item_data['themes'] = json.loads(item_data['themes'])
                except:
                    item_data['themes'] = []
            
            # Créer l'instance HistoricalItem
            return HistoricalItem.from_dict(item_data)
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération item {identifier}: {e}")
            return None
        finally:
            conn.close()
    
    def get_theme_by_id(self, theme_id: int) -> Optional[Dict[str, Any]]:
        """Récupère un thème par son ID - VERSION CORRIGÉE"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
    
        try:
            cursor.execute("""
                SELECT id, name, keywords, color, description
                FROM themes
                WHERE id = ?
            """, (theme_id,))
        
            row = cursor.fetchone()
            if not row:
                return None
        
        # Gestion ROBUSTE des mots-clés
            keywords_raw = row[2]
            keywords = []
        
            if keywords_raw:
                try:
                # Essayer JSON d'abord
                    if isinstance(keywords_raw, str):
                        parsed = json.loads(keywords_raw)
                        if isinstance(parsed, list):
                            keywords = parsed
                        else:
                        # Si c'est une string simple
                            keywords = [k.strip() for k in str(keywords_raw).split(',') if k.strip()]
                    elif isinstance(keywords_raw, list):
                        keywords = keywords_raw
                    else:
                        keywords = [str(keywords_raw)]
                except:
                # Fallback: traitement comme texte
                    keywords_str = str(keywords_raw)
                    if ',' in keywords_str:
                        keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]
                    else:
                        keywords = [k.strip() for k in keywords_str.split('\n') if k.strip()]
        
            return {
                'id': row[0],
                'name': row[1],
                'keywords': keywords,
                'color': row[3] or '#6366f1',
                'description': row[4] or ''
            }
        
        except Exception as e:
            logger.error(f"❌ Erreur récupération thème {theme_id}: {e}")
            return None
        finally:
            conn.close()
  
    def find_similar_items(
        self, 
        query_embedding: List[float], 
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Trouve les items les plus similaires par embedding"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            # Récupérer tous les embeddings
            cursor.execute("""
                SELECT a.identifier, a.title, a.date, a.year, e.embedding_vector
                FROM archiviste_v3_items a
                JOIN archiviste_v3_embeddings e ON a.identifier = e.item_identifier
                WHERE e.embedding_vector IS NOT NULL
                LIMIT 500
            """)
            
            results = []
            for row in cursor.fetchall():
                try:
                    stored_embedding = pickle.loads(row[4])
                    
                    # Calculer la similarité cosinus
                    similarity = self._cosine_similarity(query_embedding, stored_embedding)
                    
                    if similarity > 0.3:  # Seuil minimal
                        results.append({
                            'identifier': row[0],
                            'title': row[1],
                            'date': row[2],
                            'year': row[3],
                            'similarity': similarity
                        })
                
                except Exception as e:
                    logger.debug(f"Erreur calcul similarité {row[0]}: {e}")
                    continue
            
            # Trier par similarité et limiter
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:limit]
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche items similaires: {e}")
            return []
        finally:
            conn.close()
    
    def find_historical_analogies(
        self,
        key_entities: List[str],
        query_embedding: List[float],
        threshold: float = 0.7,
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Trouve des analogies historiques basées sur les entités et embeddings"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            # Recherche par entités d'abord
            entity_matches = []
            for entity in key_entities[:3]:  # Limiter à 3 entités clés
                cursor.execute("""
                    SELECT identifier, title, date, year, entities
                    FROM archiviste_v3_items
                    WHERE content LIKE ? OR entities LIKE ?
                    LIMIT 50
                """, (f'%{entity}%', f'%{entity}%'))
                
                for row in cursor.fetchall():
                    try:
                        entities_data = []
                        if row[4]:
                            try:
                                entities_data = json.loads(row[4])
                            except:
                                pass
                        
                        item_entities = [e.get('text', '') if isinstance(e, dict) else str(e) for e in entities_data]
                        shared_entities = set(key_entities) & set(item_entities)
                        
                        if shared_entities:
                            entity_matches.append({
                                'identifier': row[0],
                                'title': row[1],
                                'date': row[2],
                                'year': row[3],
                                'shared_entities': list(shared_entities),
                                'entity_count': len(shared_entities)
                            })
                    except:
                        continue
            
            # Raffiner avec similarité vectorielle si disponible
            analogies = []
            for match in entity_matches[:20]:  # Limiter pour performances
                cursor.execute("""
                    SELECT embedding_vector FROM archiviste_v3_embeddings
                    WHERE item_identifier = ?
                """, (match['identifier'],))
                
                row = cursor.fetchone()
                if row:
                    try:
                        stored_embedding = pickle.loads(row[0])
                        similarity = self._cosine_similarity(query_embedding, stored_embedding)
                        
                        if similarity >= threshold:
                            analogies.append({
                                'identifier': match['identifier'],
                                'title': match['title'],
                                'date': match['date'],
                                'year': match['year'],
                                'shared_entities': match['shared_entities'],
                                'similarity': similarity,
                                'summary': self._generate_analogy_summary(match, similarity)
                            })
                    except:
                        continue
            
            # Trier par similarité
            analogies.sort(key=lambda x: x['similarity'], reverse=True)
            return analogies[:max_results]
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche analogies: {e}")
            return []
        finally:
            conn.close()
    
    def save_period_analysis(
        self, 
        period_key: str, 
        theme_id: int, 
        items: List[HistoricalItem],
        statistics: Dict[str, Any]
    ) -> int:
        """Sauvegarde une analyse de période"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO archiviste_v3_period_analyses
                (period_key, theme_id, total_items, items_analyzed, statistics)
                VALUES (?, ?, ?, ?, ?)
            """, (
                period_key,
                theme_id,
                len(items),
                len(items),
                json.dumps(statistics)
            ))
            
            analysis_id = cursor.lastrowid
            conn.commit()
            return analysis_id
            
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde analyse période: {e}")
            conn.rollback()
            return 0
        finally:
            conn.close()
    
    def get_period_analyses(
        self, 
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Récupère les analyses de période récentes"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT pa.id, pa.period_key, pa.theme_id, pa.items_analyzed,
                       pa.statistics, pa.created_at, t.name as theme_name
                FROM archiviste_v3_period_analyses pa
                JOIN themes t ON pa.theme_id = t.id
                ORDER BY pa.created_at DESC
                LIMIT ?
            """, (limit,))
            
            analyses = []
            for row in cursor.fetchall():
                try:
                    stats = json.loads(row[4]) if row[4] else {}
                except:
                    stats = {}
                
                analyses.append({
                    'id': row[0],
                    'period_key': row[1],
                    'theme_id': row[2],
                    'items_analyzed': row[3],
                    'statistics': stats,
                    'created_at': row[5],
                    'theme_name': row[6]
                })
            
            return analyses
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération analyses: {e}")
            return []
        finally:
            conn.close()
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calcule la similarité cosinus entre deux vecteurs"""
        import math
        
        if not vec1 or not vec2:
            return 0.0
        
        if len(vec1) != len(vec2):
            return 0.0
        
        try:
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            magnitude1 = math.sqrt(sum(a * a for a in vec1))
            magnitude2 = math.sqrt(sum(b * b for b in vec2))
            
            if magnitude1 == 0 or magnitude2 == 0:
                return 0.0
            
            return dot_product / (magnitude1 * magnitude2)
        except:
            return 0.0
    
    def _generate_analogy_summary(self, match: Dict[str, Any], similarity: float) -> str:
        """Génère un résumé pour une analogie"""
        entities_str = ', '.join(match['shared_entities'][:2])
        return f"Similaire par: {entities_str} ({similarity:.1%})"