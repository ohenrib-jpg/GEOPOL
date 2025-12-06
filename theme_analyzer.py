# Flask/theme_analyzer.py - VERSION AMÉLIORÉE

import re
import logging
from typing import List, Dict, Any
from .database import DatabaseManager

logger = logging.getLogger(__name__)

class ThemeAnalyzer:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.themes_cache = None
    
    def _get_themes_with_keywords(self) -> Dict[str, Dict[str, Any]]:
        """Récupère les thèmes avec leurs mots-clés (avec cache)"""
        if self.themes_cache is None:
            themes_data = self.db_manager.get_themes()
            self.themes_cache = {
                theme['id']: {
                    'name': theme['name'],
                    'keywords': [kw.lower() for kw in theme['keywords']],
                    'color': theme['color']
                }
                for theme in themes_data
            }
            logger.info(f"📚 {len(self.themes_cache)} thèmes chargés en cache")
        return self.themes_cache
    
    def clear_cache(self):
        """Vide le cache des thèmes (utile après modification)"""
        self.themes_cache = None
        logger.info("🔄 Cache des thèmes vidé")
    
    def analyze_article(self, article_text: str, article_title: str = "") -> Dict[str, float]:
        """
        Analyse un article et retourne les thèmes détectés avec leur score de confiance
        """
        if not article_text:
            return {}
        
        # Combine titre et contenu pour l'analyse
        full_text = f"{article_title} {article_text}".lower()
        themes_data = self._get_themes_with_keywords()
        results = {}
        
        for theme_id, theme_info in themes_data.items():
            score = 0
            matches_found = 0
            total_keywords = len(theme_info['keywords'])
            
            if total_keywords == 0:
                continue
            
            for keyword in theme_info['keywords']:
                # Recherche de mots entiers avec regex
                pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
                matches = len(re.findall(pattern, full_text))
                
                if matches > 0:
                    matches_found += 1
                    # Score avec pondération selon le nombre d'occurrences
                    score += min(matches * 0.3, 1.0)
            
            # Calcul du score normalisé
            if score > 0:
                # Moyenne entre le score d'occurrences et le ratio de mots-clés trouvés
                keyword_ratio = matches_found / total_keywords
                normalized_score = (score + keyword_ratio) / 2
                
                # Limiter à 1.0 maximum
                results[theme_id] = min(normalized_score, 1.0)
                
                logger.debug(f"Thème '{theme_id}': {matches_found}/{total_keywords} mots-clés, score={normalized_score:.2f}")
        
        if results:
            logger.info(f"✅ {len(results)} thème(s) détecté(s) dans l'article")
        else:
            logger.debug("⚠️ Aucun thème détecté dans l'article")
        
        return results
    
    def save_theme_analysis(self, article_id: int, theme_scores: Dict[str, float]):
        """Sauvegarde l'analyse des thèmes pour un article"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            # Supprime les analyses précédentes pour cet article
            cursor.execute("DELETE FROM theme_analyses WHERE article_id = ?", (article_id,))
            
            # Insère les nouvelles analyses
            saved_count = 0
            for theme_id, confidence in theme_scores.items():
                if confidence >= 0.1:  # Seuil minimal de confiance (réduit de 0.3 à 0.1)
                    cursor.execute("""
                        INSERT INTO theme_analyses (article_id, theme_id, confidence)
                        VALUES (?, ?, ?)
                    """, (article_id, theme_id, confidence))
                    saved_count += 1
            
            conn.commit()
            logger.info(f"💾 {saved_count} analyse(s) de thème sauvegardée(s) pour l'article {article_id}")
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde analyse thèmes: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def reanalyze_all_articles(self):
        """Ré-analyse tous les articles existants avec les thèmes actuels"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            # Vider le cache pour avoir les thèmes à jour
            self.clear_cache()
            
            # Récupérer tous les articles
            cursor.execute("SELECT id, title, content FROM articles")
            articles = cursor.fetchall()
            
            logger.info(f"🔄 Ré-analyse de {len(articles)} articles...")
            
            for article_id, title, content in articles:
                theme_scores = self.analyze_article(content, title)
                if theme_scores:
                    self.save_theme_analysis(article_id, theme_scores)
            
            conn.close()
            logger.info(f"✅ Ré-analyse terminée pour {len(articles)} articles")
            
        except Exception as e:
            logger.error(f"Erreur ré-analyse articles: {e}")
            conn.close()
    
    def get_articles_by_theme(self, theme_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Récupère les articles pour un thème donné"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT a.id, a.title, a.content, a.link, a.pub_date, a.sentiment_type, ta.confidence
            FROM articles a
            JOIN theme_analyses ta ON a.id = ta.article_id
            WHERE ta.theme_id = ? AND ta.confidence >= 0.2
            ORDER BY ta.confidence DESC, a.pub_date DESC
            LIMIT ?
        """, (theme_id, limit))
        
        articles = []
        for row in cursor.fetchall():
            articles.append({
                'id': row[0],
                'title': row[1],
                'content': row[2],
                'link': row[3],
                'pub_date': row[4],
                'sentiment': row[5],
                'confidence': row[6]
            })
        
        conn.close()
        logger.info(f"📰 {len(articles)} article(s) trouvé(s) pour le thème '{theme_id}'")
        return articles
    
    def get_theme_statistics(self) -> Dict[str, int]:
        """Retourne le nombre d'articles par thème"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT theme_id, COUNT(DISTINCT article_id) as count
            FROM theme_analyses
            WHERE confidence >= 0.2
            GROUP BY theme_id
        """)
        
        stats = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        
        logger.info(f"📊 Statistiques: {len(stats)} thèmes avec articles")
        return stats