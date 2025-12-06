# Flask/archiviste_database.py
import sqlite3
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class ArchivisteDatabase:
    """Gestionnaire de base de données avancé pour l'Archiviste"""
    
    def __init__(self, db_manager):  # ← db_manager est l'objet DatabaseManager
        self.db_manager = db_manager  # ← Stocker l'objet directement
        self._init_tables()  # ✅ Cette méthode doit exister
    
    def _init_tables(self):  # ✅ Méthode ajoutée
        """Initialise les tables avancées pour l'Archiviste"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            # Table des items Archive.org avec métadonnées enrichies
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS archiviste_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    identifier TEXT UNIQUE NOT NULL,
                    title TEXT,
                    date TEXT,
                    year INTEGER,
                    collection TEXT,
                    description TEXT,
                    language TEXT,
                    creator TEXT,
                    publisher TEXT,
                    subject TEXT,
                    mediatype TEXT,
                    downloads INTEGER DEFAULT 0,
                    full_text TEXT,
                    text_quality_score INTEGER DEFAULT 0,
                    geopolitical_relevance_score INTEGER DEFAULT 0,
                    themes_detected TEXT,
                    sentiment_score REAL DEFAULT 0.0,
                    entities_extracted TEXT,
                    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_analyzed_at DATETIME,
                    analysis_version INTEGER DEFAULT 1
                )
            """)
            
            # Table des analyses par période avec agrégations avancées
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS archiviste_period_analyses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    period_key TEXT NOT NULL,
                    period_name TEXT,
                    theme_id INTEGER,
                    total_items INTEGER DEFAULT 0,
                    items_analyzed INTEGER DEFAULT 0,
                    sentiment_evolution TEXT,
                    theme_evolution TEXT,
                    dominant_narratives TEXT,
                    geopolitical_shifts TEXT,
                    key_events TEXT,
                    confidence_score REAL DEFAULT 0.0,
                    analysis_summary TEXT,
                    raw_data TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table de mapping thèmes-items (liaison avec les thèmes utilisateur)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS archiviste_theme_mappings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_identifier TEXT NOT NULL,
                    theme_id INTEGER NOT NULL,
                    theme_name TEXT NOT NULL,
                    relevance_score REAL DEFAULT 0.0,
                    confidence REAL DEFAULT 0.0,
                    matched_keywords TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (item_identifier) REFERENCES archiviste_items(identifier)
                )
            """)
            
            # Index pour performances
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_archiviste_items_year ON archiviste_items(year)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_archiviste_items_theme ON archiviste_items(themes_detected)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_archiviste_mappings_theme ON archiviste_theme_mappings(theme_id)")
            
            conn.commit()
            logger.info("✅ Tables Archiviste avancées initialisées")
            
        except Exception as e:
            logger.error(f"❌ Erreur init tables Archiviste: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def get_connection(self):
        """Retourne une connexion à la base de données"""
        return self.db_manager.get_connection()
    
    def get_user_themes_with_keywords(self) -> List[Dict[str, Any]]:
        """Récupère les thèmes définis par l'utilisateur via ThemeManager"""
        try:
            # Importer ici pour éviter les imports circulaires
            try:
                from .theme_manager import ThemeManager
            except ImportError:
                from Flask.theme_manager import ThemeManager
            
            # Utiliser le DatabaseManager existant
            theme_manager = ThemeManager(self.db_manager)
            
            # Récupérer tous les thèmes
            themes = theme_manager.get_all_themes()
            
            formatted_themes = []
            for theme in themes:
                # Formater les mots-clés
                keywords = []
                if isinstance(theme.get('keywords'), str):
                    try:
                        keywords = json.loads(theme['keywords'])
                    except:
                        keywords = [k.strip() for k in theme['keywords'].split(',') if k.strip()]
                elif isinstance(theme.get('keywords'), list):
                    keywords = theme['keywords']
                
                formatted_theme = {
                    'id': theme['id'],
                    'name': theme['name'],
                    'keywords': keywords,
                    'description': theme.get('description', ''),
                    'color': theme.get('color', '#6366f1'),
                    'category': 'general'  # Valeur par défaut
                }
                
                formatted_themes.append(formatted_theme)
            
            logger.info(f"✅ {len(formatted_themes)} thèmes chargés via ThemeManager")
            return formatted_themes
            
        except Exception as e:
            logger.error(f"❌ Erreur get_user_themes via ThemeManager: {e}")
            # Fallback: essayer la méthode directe
            return self._get_themes_directly()
    
    def _get_themes_directly(self) -> List[Dict[str, Any]]:
        """Méthode de fallback pour récupérer les thèmes directement depuis la base"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Vérifier si la table themes existe
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='themes'
            """)
            
            if not cursor.fetchone():
                logger.warning("⚠️ Table 'themes' n'existe pas")
                return []
            
            # Vérifier si la colonne 'active' existe
            cursor.execute("PRAGMA table_info(themes)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'active' in columns:
                cursor.execute("""
                    SELECT id, name, keywords, description, color
                    FROM themes
                    WHERE active = 1 OR active IS NULL
                    ORDER BY name
                """)
            else:
                # Si la colonne active n'existe pas, récupérer tous les thèmes
                cursor.execute("""
                    SELECT id, name, keywords, description, color
                    FROM themes
                    ORDER BY name
                """)
            
            themes = []
            for row in cursor.fetchall():
                keywords = []
                if row[2]:  # keywords column
                    try:
                        keywords = json.loads(row[2])
                    except:
                        keywords = [k.strip() for k in str(row[2]).split(',') if k.strip()]
                
                themes.append({
                    'id': row[0],
                    'name': row[1],
                    'keywords': keywords,
                    'description': row[3] or '',
                    'color': row[4] or '#6366f1',
                    'category': 'general'
                })
            
            logger.info(f"✅ {len(themes)} thèmes chargés directement depuis la base")
            return themes
            
        except Exception as e:
            logger.error(f"❌ Erreur _get_themes_directly: {e}")
            return []
        finally:
            conn.close()
    
    def save_archiviste_item(self, item_data: Dict[str, Any], full_text: str = "") -> bool:
        """Sauvegarde un item Archive.org avec métadonnées enrichies"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Préparer les données
            subject_json = json.dumps(item_data.get('subject', []))
            collection_json = json.dumps(item_data.get('collection', []))
            
            cursor.execute("""
                INSERT OR REPLACE INTO archiviste_items 
                (identifier, title, date, year, collection, description, 
                 language, creator, publisher, subject, mediatype, downloads, full_text)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item_data.get('identifier', ''),
                item_data.get('title', ''),
                item_data.get('date', ''),
                item_data.get('year', 0),
                collection_json,
                item_data.get('description', ''),
                item_data.get('language', ''),
                item_data.get('creator', ''),
                item_data.get('publisher', ''),
                subject_json,
                item_data.get('mediatype', ''),
                item_data.get('downloads', 0),
                full_text
            ))
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde item Archiviste: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def map_item_to_themes(self, item_identifier: str, text_content: str) -> List[Dict[str, Any]]:
        """Associe un item Archive.org aux thèmes utilisateur"""
        themes = self.get_user_themes_with_keywords()
        mappings = []
        
        for theme in themes:
            relevance_score = self._calculate_theme_relevance(text_content, theme['keywords'])
            
            if relevance_score > 0.1:  # Seuil minimal de pertinence
                mappings.append({
                    'item_identifier': item_identifier,
                    'theme_id': theme['id'],
                    'theme_name': theme['name'],
                    'relevance_score': relevance_score,
                    'confidence': min(relevance_score * 1.5, 1.0),
                    'matched_keywords': json.dumps(self._find_matching_keywords(text_content, theme['keywords']))
                })
        
        # Sauvegarder les mappings
        self._save_theme_mappings(mappings)
        return mappings
    
    def _calculate_theme_relevance(self, text: str, keywords: List[str]) -> float:
        """Calcule la pertinence d'un texte par rapport à des mots-clés de thème"""
        if not text or not keywords:
            return 0.0
        
        text_lower = text.lower()
        matches = 0
        
        for keyword in keywords:
            if keyword.lower() in text_lower:
                matches += 1
        
        return matches / len(keywords) if keywords else 0.0
    
    def _find_matching_keywords(self, text: str, keywords: List[str]) -> List[str]:
        """Trouve les mots-clés correspondants dans le texte"""
        text_lower = text.lower()
        matched = []
        
        for keyword in keywords:
            if keyword.lower() in text_lower:
                matched.append(keyword)
        
        return matched
    
    def _save_theme_mappings(self, mappings: List[Dict[str, Any]]):
        """Sauvegarde les associations thèmes-items"""
        if not mappings:
            return
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            for mapping in mappings:
                cursor.execute("""
                    INSERT OR REPLACE INTO archiviste_theme_mappings
                    (item_identifier, theme_id, theme_name, relevance_score, confidence, matched_keywords)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    mapping['item_identifier'],
                    mapping['theme_id'],
                    mapping['theme_name'],
                    mapping['relevance_score'],
                    mapping['confidence'],
                    mapping['matched_keywords']
                ))
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde mappings: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def get_items_by_theme(self, theme_id: int, limit: int = 50) -> List[Dict[str, Any]]:
        """Récupère les items Archive.org associés à un thème spécifique"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT ai.*, atm.relevance_score, atm.confidence
                FROM archiviste_items ai
                JOIN archiviste_theme_mappings atm ON ai.identifier = atm.item_identifier
                WHERE atm.theme_id = ?
                ORDER BY atm.relevance_score DESC, ai.downloads DESC
                LIMIT ?
            """, (theme_id, limit))
            
            items = []
            columns = [description[0] for description in cursor.description]
            
            for row in cursor.fetchall():
                item = dict(zip(columns, row))
                # Convertir les champs JSON
                if item.get('collection'):
                    try:
                        item['collection'] = json.loads(item['collection'])
                    except:
                        item['collection'] = []
                if item.get('subject'):
                    try:
                        item['subject'] = json.loads(item['subject'])
                    except:
                        item['subject'] = []
                items.append(item)
            
            return items
            
        except Exception as e:
            logger.error(f"❌ Erreur get_items_by_theme: {e}")
            return []
        finally:
            conn.close()
