# Flask/theme_manager.py - VERSION SIMPLIFIÉE ET CORRIGÉE

import json
import logging
from typing import List, Dict, Any
from .database import DatabaseManager

logger = logging.getLogger(__name__)

class ThemeManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def get_all_themes(self) -> List[Dict[str, Any]]:
        """Retourne tous les thèmes"""
        return self.db_manager.get_themes()
    
    def get_theme(self, theme_id: str) -> Dict[str, Any]:
        """Retourne un thème spécifique"""
        themes = self.db_manager.get_themes()
        for theme in themes:
            if theme['id'] == theme_id:
                return theme
        return None
    
    def create_theme(self, theme_id: str, name: str, keywords: List[str], 
                    color: str = '#6366f1', description: str = '') -> bool:
        """Crée un nouveau thème - VERSION SIMPLIFIÉE"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Vérifier si le thème existe déjà
            cursor.execute("SELECT id FROM themes WHERE id = ?", (theme_id,))
            if cursor.fetchone():
                logger.error(f"Thème {theme_id} existe déjà")
                conn.close()
                return False
            
            # Convertir les keywords en JSON
            if isinstance(keywords, str):
                # Si c'est une string, essayer de la parser
                try:
                    keywords_list = json.loads(keywords)
                except:
                    keywords_list = [k.strip() for k in keywords.split(',') if k.strip()]
            else:
                keywords_list = keywords
            
            # S'assurer que c'est une liste
            if not isinstance(keywords_list, list):
                keywords_list = [str(keywords_list)]
            
            # Valider qu'il y a au moins un mot-clé
            if not keywords_list:
                logger.error("Aucun mot-clé fourni")
                conn.close()
                return False
            
            # Convertir en JSON
            keywords_json = json.dumps(keywords_list, ensure_ascii=False)
            
            logger.info(f"Insertion thème: {theme_id}, keywords: {keywords_json}")
            
            # Insérer le thème
            cursor.execute("""
                INSERT INTO themes (id, name, keywords, color, description)
                VALUES (?, ?, ?, ?, ?)
            """, (
                theme_id,
                name,
                keywords_json,
                color,
                description
            ))
            
            conn.commit()
            conn.close()
            logger.info(f"✅ Thème créé: {theme_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur création thème {theme_id}: {e}")
            try:
                conn.close()
            except:
                pass
            return False
    
    def update_theme(self, theme_id: str, name: str = None, keywords: List[str] = None,
                    color: str = None, description: str = None) -> bool:
        """Met à jour un thème existant"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Vérifier si le thème existe
            cursor.execute("SELECT name, keywords, color, description FROM themes WHERE id = ?", (theme_id,))
            row = cursor.fetchone()
            
            if not row:
                logger.error(f"Thème {theme_id} non trouvé")
                conn.close()
                return False
            
            current_name, current_keywords, current_color, current_description = row
            
            # Préparer les nouvelles valeurs
            update_name = name if name is not None else current_name
            update_color = color if color is not None else current_color
            update_description = description if description is not None else current_description
            
            # Gestion des keywords
            if keywords is not None:
                if isinstance(keywords, str):
                    try:
                        update_keywords = json.loads(keywords)
                    except:
                        update_keywords = [k.strip() for k in keywords.split(',') if k.strip()]
                else:
                    update_keywords = keywords
                
                if not isinstance(update_keywords, list):
                    update_keywords = [str(update_keywords)]
                
                keywords_json = json.dumps(update_keywords, ensure_ascii=False)
            else:
                keywords_json = current_keywords
            
            # Mettre à jour
            cursor.execute("""
                UPDATE themes 
                SET name = ?, keywords = ?, color = ?, description = ?
                WHERE id = ?
            """, (
                update_name,
                keywords_json,
                update_color,
                update_description,
                theme_id
            ))
            
            conn.commit()
            conn.close()
            logger.info(f"✅ Thème mis à jour: {theme_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur mise à jour thème {theme_id}: {e}")
            try:
                conn.close()
            except:
                pass
            return False
    
    def delete_theme(self, theme_id: str) -> bool:
        """Supprime un thème"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Vérifier si le thème existe
            cursor.execute("SELECT id FROM themes WHERE id = ?", (theme_id,))
            if not cursor.fetchone():
                logger.error(f"Thème {theme_id} non trouvé")
                conn.close()
                return False
            
            # Supprimer les analyses associées
            cursor.execute("DELETE FROM theme_analyses WHERE theme_id = ?", (theme_id,))
            
            # Supprimer le thème
            cursor.execute("DELETE FROM themes WHERE id = ?", (theme_id,))
            
            conn.commit()
            conn.close()
            logger.info(f"✅ Thème supprimé: {theme_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur suppression thème {theme_id}: {e}")
            try:
                conn.close()
            except:
                pass
            return False