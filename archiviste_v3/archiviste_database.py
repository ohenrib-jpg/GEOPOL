"""
Base de données pour Archiviste v3.0 - VERSION ENRICHIE
Ajout: stockage embeddings, requêtes vectorielles optimisées
"""

import sqlite3
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ArchivisteDatabase:
    """Base de données enrichie avec support vectoriel"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self._init_tables()
        self._check_and_fix_columns()
    
    def _init_tables(self):
        """Initialise les tables avec toutes les colonnes nécessaires"""
        conn = None
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Table des items avec support embedding
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS archiviste_v3_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    identifier TEXT UNIQUE,
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
                    period_key TEXT,
                    theme_id INTEGER,
                    search_query TEXT,
                    is_french BOOLEAN DEFAULT 1,
                    
                    -- Analyse NLP
                    entities TEXT,
                    embedding TEXT,
                    geopolitical_relevance REAL DEFAULT 0.0,
                    
                    processed_at DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table des sessions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS archiviste_v3_search_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    period_key TEXT,
                    theme_id INTEGER,
                    search_query TEXT,
                    total_items_found INTEGER DEFAULT 0,
                    new_items_added INTEGER DEFAULT 0,
                    cached_items_used INTEGER DEFAULT 0,
                    search_duration REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Index optimisés
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_period_theme ON archiviste_v3_items(period_key, theme_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_year ON archiviste_v3_items(year)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_identifier ON archiviste_v3_items(identifier)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_items_relevance ON archiviste_v3_items(geopolitical_relevance)")
            
            conn.commit()
            logger.info("✅ Tables Archiviste créées/réinitialisées")
            
        except Exception as e:
            logger.error(f"❌ Erreur création tables: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except:
                    pass
    
    def _check_and_fix_columns(self):
        """Vérifie et ajoute les colonnes manquantes"""
        conn = None
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Colonnes nécessaires
            required_columns = [
                ('period_key', 'TEXT'),
                ('theme_id', 'INTEGER'),
                ('search_query', 'TEXT'),
                ('is_french', 'BOOLEAN DEFAULT 1'),
                ('processed_at', 'DATETIME'),
                ('entities', 'TEXT'),
                ('embedding', 'TEXT'),
                ('geopolitical_relevance', 'REAL DEFAULT 0.0')
            ]
            
            # Vérifier chaque colonne
            cursor.execute("PRAGMA table_info(archiviste_v3_items)")
            existing_columns = [row[1] for row in cursor.fetchall()]
            
            for column_name, column_type in required_columns:
                if column_name not in existing_columns:
                    logger.warning(f"⚠️ Colonne {column_name} manquante, ajout...")
                    try:
                        cursor.execute(f"ALTER TABLE archiviste_v3_items ADD COLUMN {column_name} {column_type}")
                        logger.info(f"✅ Colonne {column_name} ajoutée")
                    except Exception as e:
                        logger.error(f"❌ Erreur ajout colonne {column_name}: {e}")
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"❌ Erreur vérification colonnes: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except:
                    pass
    
    def get_cached_items(self, period_key: str, theme_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Récupère les items en cache"""
        conn = None
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT identifier, title, description, date, year, 
                       publisher, downloads, source_url, subject,
                       entities, geopolitical_relevance
                FROM archiviste_v3_items 
                WHERE period_key = ? AND theme_id = ?
                ORDER BY geopolitical_relevance DESC, downloads DESC
                LIMIT ?
            """
            
            cursor.execute(query, (period_key, theme_id, limit))
            
            items = []
            for row in cursor.fetchall():
                try:
                    item = {
                        'identifier': row[0] or '',
                        'title': row[1] or '',
                        'description': row[2] or '',
                        'date': row[3] or '',
                        'year': row[4] or 0,
                        'publisher': row[5] or '',
                        'downloads': row[6] or 0,
                        'source_url': row[7] or '',
                        'subject': json.loads(row[8]) if row[8] else [],
                        'entities': json.loads(row[9]) if row[9] else [],
                        'geopolitical_relevance': row[10] or 0.0
                    }
                    items.append(item)
                except Exception as e:
                    logger.debug(f"⚠️ Erreur formatage item: {e}")
                    continue
            
            logger.debug(f"📂 {len(items)} items en cache pour {period_key}/{theme_id}")
            return items
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération cache: {e}")
            return []
        finally:
            if conn:
                try:
                    conn.close()
                except:
                    pass
    
    def save_items_batch(
        self, 
        items: List[Dict[str, Any]], 
        period_key: str, 
        theme_id: int, 
        search_query: str
    ) -> int:
        """Sauvegarde des items avec données NLP"""
        if not items:
            return 0
        
        conn = None
        new_count = 0
        
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            for item in items:
                try:
                    identifier = item.get('identifier', '')
                    if not identifier:
                        continue
                    
                    # Vérifier si existe
                    cursor.execute(
                        "SELECT id FROM archiviste_v3_items WHERE identifier = ?",
                        (identifier,)
                    )
                    
                    if not cursor.fetchone():
                        # Préparer les données
                        title = item.get('title', '')[:500]
                        description = item.get('description', '')[:2000]
                        date = item.get('date', '')
                        year = item.get('year', 0)
                        publisher = item.get('publisher', '')[:200]
                        downloads = item.get('downloads', 0)
                        source_url = item.get('source_url', '')
                        subject = json.dumps(item.get('subject', []))
                        
                        # Données NLP
                        entities = json.dumps(item.get('entities', []))
                        embedding = json.dumps(item.get('embedding', [])) if item.get('embedding') else None
                        geopolitical_relevance = item.get('geopolitical_relevance', 0.0)
                        processed_at = item.get('processed_at')
                        
                        # Insérer
                        cursor.execute("""
                            INSERT INTO archiviste_v3_items 
                            (identifier, title, description, date, year, 
                             publisher, downloads, source_url, subject,
                             period_key, theme_id, search_query, is_french,
                             entities, embedding, geopolitical_relevance, processed_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            identifier, title, description, date, year,
                            publisher, downloads, source_url, subject,
                            period_key, theme_id, search_query[:500], 1,
                            entities, embedding, geopolitical_relevance, processed_at
                        ))
                        new_count += 1
                        
                except Exception as e:
                    logger.debug(f"⚠️ Erreur sauvegarde item {item.get('identifier', 'unknown')}: {e}")
                    continue
            
            conn.commit()
            logger.info(f"💾 {new_count} nouveaux items sauvegardés")
            return new_count
            
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde batch: {e}")
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
            return 0
        finally:
            if conn:
                try:
                    conn.close()
                except:
                    pass
    
    def get_all_items_with_content(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Récupère tous les items avec leur contenu pour recherche vectorielle"""
        conn = None
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT identifier, title, description, year, source_url,
                       entities, geopolitical_relevance, period_key
                FROM archiviste_v3_items
                ORDER BY created_at DESC
                LIMIT ?
            """
            
            cursor.execute(query, (limit,))
            
            items = []
            for row in cursor.fetchall():
                items.append({
                    'identifier': row[0],
                    'title': row[1],
                    'description': row[2],
                    'year': row[3],
                    'source_url': row[4],
                    'entities': json.loads(row[5]) if row[5] else [],
                    'geopolitical_relevance': row[6] or 0.0,
                    'period_key': row[7]
                })
            
            return items
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération items: {e}")
            return []
        finally:
            if conn:
                try:
                    conn.close()
                except:
                    pass
    
    def save_search_session(
        self, 
        period_key: str, 
        theme_id: int, 
        search_query: str,
        total_found: int, 
        new_added: int, 
        cached_used: int, 
        duration: float
    ) -> int:
        """Sauvegarde une session de recherche"""
        conn = None
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO archiviste_v3_search_sessions 
                (period_key, theme_id, search_query, total_items_found, 
                 new_items_added, cached_items_used, search_duration)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                period_key,
                theme_id,
                search_query[:500],
                total_found,
                new_added,
                cached_used,
                duration
            ))
            
            conn.commit()
            session_id = cursor.lastrowid
            logger.debug(f"📝 Session sauvegardée: {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde session: {e}")
            return 0
        finally:
            if conn:
                try:
                    conn.close()
                except:
                    pass
    
    def get_search_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Historique des recherches"""
        conn = None
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, period_key, theme_id, total_items_found,
                       new_items_added, cached_items_used, search_duration,
                       created_at
                FROM archiviste_v3_search_sessions
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            
            history = []
            for row in cursor.fetchall():
                history.append({
                    'id': row[0],
                    'period_key': row[1],
                    'theme_id': row[2],
                    'items_analyzed': row[3],
                    'new_added': row[4],
                    'cached_used': row[5],
                    'duration': row[6],
                    'created_at': row[7]
                })
            
            return history
            
        except Exception as e:
            logger.error(f"❌ Erreur historique: {e}")
            return []
        finally:
            if conn:
                try:
                    conn.close()
                except:
                    pass
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Statistiques du cache"""
        conn = None
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            stats = {}
            
            # Total items
            cursor.execute("SELECT COUNT(*) FROM archiviste_v3_items")
            stats['total_items'] = cursor.fetchone()[0]
            
            # Items avec embeddings
            cursor.execute("SELECT COUNT(*) FROM archiviste_v3_items WHERE embedding IS NOT NULL")
            stats['items_with_embeddings'] = cursor.fetchone()[0]
            
            # Total sessions
            cursor.execute("SELECT COUNT(*) FROM archiviste_v3_search_sessions")
            stats['total_searches'] = cursor.fetchone()[0]
            
            # Items par période
            cursor.execute("""
                SELECT period_key, COUNT(*) 
                FROM archiviste_v3_items 
                WHERE period_key IS NOT NULL
                GROUP BY period_key
            """)
            stats['items_by_period'] = dict(cursor.fetchall())
            
            # Pertinence moyenne
            cursor.execute("SELECT AVG(geopolitical_relevance) FROM archiviste_v3_items")
            avg_rel = cursor.fetchone()[0]
            stats['avg_relevance'] = round(avg_rel, 3) if avg_rel else 0.0
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Erreur stats cache: {e}")
            return {}
        finally:
            if conn:
                try:
                    conn.close()
                except:
                    pass
    
    def clear_old_cache(self, days: int = 30):
        """Supprime les entrées de cache anciennes"""
        conn = None
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            cursor.execute("""
                DELETE FROM archiviste_v3_items 
                WHERE created_at < ?
            """, (cutoff_date.isoformat(),))
            
            deleted = cursor.rowcount
            conn.commit()
            
            logger.info(f"🗑️ {deleted} entrées anciennes supprimées")
            return deleted
            
        except Exception as e:
            logger.error(f"❌ Erreur clear cache: {e}")
            return 0
        finally:
            if conn:
                try:
                    conn.close()
                except:
                    pass
    
    def reset_database(self):
        """Réinitialise complètement la base"""
        conn = None
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("DROP TABLE IF EXISTS archiviste_v3_items")
            cursor.execute("DROP TABLE IF EXISTS archiviste_v3_search_sessions")
            
            conn.commit()
            logger.info("🗑️ Base Archiviste réinitialisée")
            
            # Recréer les tables
            self._init_tables()
            
        except Exception as e:
            logger.error(f"❌ Erreur réinitialisation: {e}")
        finally:
            if conn:
                try:
                    conn.close()
                except:
                    pass