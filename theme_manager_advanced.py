# Flask/theme_manager_advanced.py - VERSION COMPLÈTEMENT CORRIGÉE
import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from .database import DatabaseManager

logger = logging.getLogger(__name__)

class AdvancedThemeManager:
    """
    Gestionnaire de thèmes avancé avec support pour :
    - Mots-clés pondérés
    - Synonymes et variations
    - Contexte géopolitique
    - Statistiques détaillées
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self._init_advanced_tables()
    
    def _init_advanced_tables(self):
        """Initialise les tables avancées pour la gestion des thèmes"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        # Table pour les mots-clés pondérés
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS theme_keywords_weighted (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                theme_id TEXT NOT NULL,
                keyword TEXT NOT NULL,
                weight REAL DEFAULT 1.0,
                category TEXT DEFAULT 'primary',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (theme_id) REFERENCES themes(id) ON DELETE CASCADE,
                UNIQUE(theme_id, keyword)
            )
        """)
        
        # Table pour les synonymes
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS theme_synonyms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                theme_id TEXT NOT NULL,
                original_word TEXT NOT NULL,
                synonym TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (theme_id) REFERENCES themes(id) ON DELETE CASCADE
            )
        """)
        
        # Table pour le contexte géopolitique
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS theme_context (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                theme_id TEXT NOT NULL,
                context_type TEXT NOT NULL,
                context_value TEXT NOT NULL,
                metadata TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (theme_id) REFERENCES themes(id) ON DELETE CASCADE
            )
        """)
        
        # Table pour les statistiques d'apprentissage
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS theme_learning_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                theme_id TEXT NOT NULL,
                keyword TEXT NOT NULL,
                usage_count INTEGER DEFAULT 0,
                accuracy REAL DEFAULT 0.0,
                last_used DATETIME,
                FOREIGN KEY (theme_id) REFERENCES themes(id) ON DELETE CASCADE,
                UNIQUE(theme_id, keyword)
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info("✅ Tables avancées initialisées")
    
    def theme_exists(self, theme_id: str) -> bool:
        """Vérifie si un thème existe déjà"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM themes WHERE id = ?", (theme_id,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists
    
    def create_advanced_theme(self, theme_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée un thème avec configuration avancée - VERSION COMPLÈTEMENT CORRIGÉE
        """
        try:
            theme_id = theme_data.get('id', '').strip()
            
            # Validation des champs obligatoires
            if not theme_id:
                return {
                    'success': False,
                    'error': "L'ID du thème est requis"
                }
            
            if not theme_data.get('name', '').strip():
                return {
                    'success': False,
                    'error': "Le nom du thème est requis"
                }
            
            # Vérifier si le thème existe déjà
            if self.theme_exists(theme_id):
                return {
                    'success': False,
                    'error': f"Un thème avec l'ID '{theme_id}' existe déjà."
                }
            
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # 1. Préparer les mots-clés pour la table themes
            base_keywords = []
            if 'keywords' in theme_data:
                for kw in theme_data['keywords']:
                    if isinstance(kw, dict):
                        base_keywords.append(kw['word'])
                    else:
                        base_keywords.append(str(kw))
            
            # S'assurer qu'il y a au moins un mot-clé
            if not base_keywords:
                conn.close()
                return {
                    'success': False,
                    'error': 'Au moins un mot-clé est requis'
                }
            
            # 2. Créer le thème de base
            cursor.execute("""
                INSERT INTO themes (id, name, keywords, color, description)
                VALUES (?, ?, ?, ?, ?)
            """, (
                theme_id,
                theme_data['name'],
                json.dumps(base_keywords, ensure_ascii=False),
                theme_data.get('color', '#6366f1'),
                theme_data.get('description', '')
            ))
            
            # 3. Ajouter les mots-clés pondérés
            if 'keywords' in theme_data:
                for kw in theme_data['keywords']:
                    if isinstance(kw, dict):
                        cursor.execute("""
                            INSERT INTO theme_keywords_weighted 
                            (theme_id, keyword, weight, category)
                            VALUES (?, ?, ?, ?)
                        """, (
                            theme_id,
                            kw['word'],
                            kw.get('weight', 1.0),
                            kw.get('category', 'primary')
                        ))
            
            # 4. Ajouter les synonymes
            if 'synonyms' in theme_data:
                for original, syn_list in theme_data['synonyms'].items():
                    for synonym in syn_list:
                        cursor.execute("""
                            INSERT INTO theme_synonyms 
                            (theme_id, original_word, synonym)
                            VALUES (?, ?, ?)
                        """, (theme_id, original, synonym))
            
            # 5. Ajouter le contexte
            if 'context' in theme_data:
                for context_type, context_value in theme_data['context'].items():
                    cursor.execute("""
                        INSERT INTO theme_context 
                        (theme_id, context_type, context_value)
                        VALUES (?, ?, ?)
                    """, (
                        theme_id,
                        context_type,
                        json.dumps(context_value, ensure_ascii=False)
                    ))
            
            conn.commit()
            conn.close()
            logger.info(f"✅ Thème avancé créé: {theme_id}")
            
            return {
                'success': True,
                'message': f"Thème '{theme_data['name']}' créé avec succès !",
                'theme_id': theme_id
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur création thème avancé: {e}")
            return {
                'success': False,
                'error': f"Erreur lors de la création du thème: {str(e)}"
            }
    
    def get_theme_with_details(self, theme_id: str) -> Dict[str, Any]:
        """Récupère un thème avec toutes ses informations avancées"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        # Thème de base
        cursor.execute("""
            SELECT id, name, keywords, color, description, created_at
            FROM themes WHERE id = ?
        """, (theme_id,))
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            return {}
        
        theme = {
            'id': row[0],
            'name': row[1],
            'keywords': json.loads(row[2]) if row[2] else [],
            'color': row[3],
            'description': row[4],
            'created_at': row[5]
        }
        
        # Mots-clés pondérés
        cursor.execute("""
            SELECT keyword, weight, category
            FROM theme_keywords_weighted
            WHERE theme_id = ?
            ORDER BY weight DESC
        """, (theme_id,))
        
        theme['weighted_keywords'] = [
            {'word': row[0], 'weight': row[1], 'category': row[2]}
            for row in cursor.fetchall()
        ]
        
        # Synonymes
        cursor.execute("""
            SELECT original_word, GROUP_CONCAT(synonym, '|')
            FROM theme_synonyms
            WHERE theme_id = ?
            GROUP BY original_word
        """, (theme_id,))
        
        theme['synonyms'] = {
            row[0]: row[1].split('|') if row[1] else []
            for row in cursor.fetchall()
        }
        
        # Contexte
        cursor.execute("""
            SELECT context_type, context_value
            FROM theme_context
            WHERE theme_id = ?
        """, (theme_id,))
        
        theme['context'] = {
            row[0]: json.loads(row[1]) if row[1] else []
            for row in cursor.fetchall()
        }
        
        # Statistiques d'apprentissage
        cursor.execute("""
            SELECT keyword, usage_count, accuracy, last_used
            FROM theme_learning_stats
            WHERE theme_id = ?
            ORDER BY usage_count DESC
            LIMIT 10
        """, (theme_id,))
        
        theme['learning_stats'] = [
            {
                'keyword': row[0],
                'usage_count': row[1],
                'accuracy': row[2],
                'last_used': row[3]
            }
            for row in cursor.fetchall()
        ]
        
        conn.close()
        return theme
    
    def update_keyword_weight(self, theme_id: str, keyword: str, 
                            new_weight: float) -> bool:
        """Met à jour le poids d'un mot-clé"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE theme_keywords_weighted
                SET weight = ?
                WHERE theme_id = ? AND keyword = ?
            """, (new_weight, theme_id, keyword))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Erreur mise à jour poids: {e}")
            return False
    
    def add_synonym(self, theme_id: str, original_word: str, 
                   synonym: str) -> bool:
        """Ajoute un synonyme à un mot-clé"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO theme_synonyms (theme_id, original_word, synonym)
                VALUES (?, ?, ?)
            """, (theme_id, original_word, synonym))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"Erreur ajout synonyme: {e}")
            return False
    
    def record_keyword_usage(self, theme_id: str, keyword: str, 
                           was_accurate: bool) -> None:
        """Enregistre l'utilisation d'un mot-clé pour l'apprentissage"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Vérifier si le mot existe déjà
            cursor.execute("""
                SELECT usage_count, accuracy
                FROM theme_learning_stats
                WHERE theme_id = ? AND keyword = ?
            """, (theme_id, keyword))
            
            row = cursor.fetchone()
            
            if row:
                # Mettre à jour
                usage_count = row[0] + 1
                current_accuracy = row[1]
                new_accuracy = (current_accuracy * row[0] + (1.0 if was_accurate else 0.0)) / usage_count
                
                cursor.execute("""
                    UPDATE theme_learning_stats
                    SET usage_count = ?, accuracy = ?, last_used = ?
                    WHERE theme_id = ? AND keyword = ?
                """, (usage_count, new_accuracy, datetime.now(), theme_id, keyword))
            else:
                # Insérer
                cursor.execute("""
                    INSERT INTO theme_learning_stats
                    (theme_id, keyword, usage_count, accuracy, last_used)
                    VALUES (?, ?, 1, ?, ?)
                """, (theme_id, keyword, 1.0 if was_accurate else 0.0, datetime.now()))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Erreur enregistrement usage: {e}")
    
    def get_theme_statistics(self, theme_id: str) -> Dict[str, Any]:
        """Récupère des statistiques détaillées sur un thème"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # Nombre d'articles
        cursor.execute("""
            SELECT COUNT(DISTINCT article_id)
            FROM theme_analyses
            WHERE theme_id = ? AND confidence >= 0.3
        """, (theme_id,))
        stats['article_count'] = cursor.fetchone()[0]
        
        # Confiance moyenne
        cursor.execute("""
            SELECT AVG(confidence)
            FROM theme_analyses
            WHERE theme_id = ?
        """, (theme_id,))
        stats['avg_confidence'] = cursor.fetchone()[0] or 0.0
        
        # Distribution des sentiments
        cursor.execute("""
            SELECT a.sentiment_type, COUNT(*)
            FROM articles a
            JOIN theme_analyses ta ON a.id = ta.article_id
            WHERE ta.theme_id = ? AND ta.confidence >= 0.3
            GROUP BY a.sentiment_type
        """, (theme_id,))
        stats['sentiment_distribution'] = {
            row[0]: row[1] for row in cursor.fetchall()
        }
        
        # Mots-clés les plus performants
        cursor.execute("""
            SELECT keyword, usage_count, accuracy
            FROM theme_learning_stats
            WHERE theme_id = ?
            ORDER BY accuracy DESC, usage_count DESC
            LIMIT 5
        """, (theme_id,))
        stats['top_keywords'] = [
            {'keyword': row[0], 'usage': row[1], 'accuracy': row[2]}
            for row in cursor.fetchall()
        ]
        
        conn.close()
        return stats
    
    def suggest_new_keywords(self, theme_id: str, limit: int = 10) -> List[str]:
        """
        Suggère de nouveaux mots-clés basés sur les articles du thème
        """
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        # Récupérer le contenu des articles du thème
        cursor.execute("""
            SELECT a.title, a.content
            FROM articles a
            JOIN theme_analyses ta ON a.id = ta.article_id
            WHERE ta.theme_id = ? AND ta.confidence >= 0.5
            LIMIT 100
        """, (theme_id,))
        
        texts = [f"{row[0]} {row[1]}" for row in cursor.fetchall()]
        conn.close()
        
        if not texts:
            return []
        
        # Analyse simple de fréquence
        from collections import Counter
        import re
        
        all_words = []
        for text in texts:
            words = re.findall(r'\b[a-zàâäéèêëïîôùûüç]{4,}\b', text.lower())
            all_words.extend(words)
        
        # Mots courants à exclure
        stop_words = {'dans', 'pour', 'avec', 'plus', 'cette', 'sont', 
                     'être', 'fait', 'faire', 'tous', 'tout', 'très'}
        
        word_freq = Counter(w for w in all_words if w not in stop_words)
        
        return [word for word, _ in word_freq.most_common(limit)]
    
    def export_theme_config(self, theme_id: str) -> Dict[str, Any]:
        """Exporte la configuration complète d'un thème"""
        theme = self.get_theme_with_details(theme_id)
        
        return {
            'version': '1.0',
            'export_date': datetime.now().isoformat(),
            'theme': theme
        }
    
    def import_theme_config(self, config: Dict[str, Any]) -> bool:
        """Importe une configuration de thème"""
        try:
            theme_data = config.get('theme', {})
            result = self.create_advanced_theme(theme_data)
            return result['success']
        except Exception as e:
            logger.error(f"Erreur import thème: {e}")
            return False