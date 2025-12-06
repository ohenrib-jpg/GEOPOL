# Flask/corroboration_engine.py
"""
Moteur de corroboration d'articles - Version optimisée Flask pure
Sans dépendances lourdes obligatoires
"""

import logging
import re
import difflib
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Tentative d'import des bibliothèques optionnelles
HAVE_RAPIDFUZZ = False
try:
    from rapidfuzz import fuzz
    HAVE_RAPIDFUZZ = True
except ImportError:
    logger.info("rapidfuzz non disponible - utilisation de difflib")

HAVE_SKLEARN = False
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    HAVE_SKLEARN = True
except ImportError:
    logger.info("sklearn non disponible - utilisation de similarité textuelle basique")


class CorroborationEngine:
    """
    Moteur de recherche d'articles corroborants
    Fonctionne avec ou sans bibliothèques ML
    """
    
    def __init__(self):
        self.tfidf = None
        self.window_days = 7  # Fenêtre temporelle par défaut
        
        if HAVE_SKLEARN:
            try:
                self.tfidf = TfidfVectorizer(
                    max_features=2000,
                    ngram_range=(1, 2),
                    min_df=1
                )
                logger.info("✅ TF-IDF initialisé")
            except Exception as e:
                logger.warning(f"Erreur init TF-IDF: {e}")
    
    def _normalize_text(self, text: str) -> str:
        """Normalise un texte pour la comparaison"""
        if not text:
            return ""
        text = str(text).lower().strip()
        text = re.sub(r'\s+', ' ', text)
        return text
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """
        Calcule la similarité entre deux textes
        Utilise rapidfuzz si disponible, sinon difflib
        """
        text1 = self._normalize_text(text1)
        text2 = self._normalize_text(text2)
        
        if not text1 or not text2:
            return 0.0
        
        if HAVE_RAPIDFUZZ:
            try:
                return fuzz.token_sort_ratio(text1, text2) / 100.0
            except Exception:
                pass
        
        # Fallback sur difflib
        return difflib.SequenceMatcher(None, text1, text2).ratio()
    
    def _semantic_similarity(self, target: str, candidates: List[str]) -> List[float]:
        """
        Calcule la similarité sémantique
        Utilise TF-IDF si disponible, sinon similarité textuelle
        """
        if HAVE_SKLEARN and self.tfidf:
            try:
                vectors = self.tfidf.fit_transform([target] + candidates)
                similarities = cosine_similarity(vectors[0:1], vectors[1:]).flatten()
                return similarities.tolist()
            except Exception as e:
                logger.debug(f"Erreur TF-IDF: {e}")
        
        # Fallback sur similarité textuelle
        return [self._text_similarity(target, cand) for cand in candidates]
    
    def _temporal_proximity(self, date1: datetime, date2: datetime) -> float:
        """
        Calcule la proximité temporelle (0-1)
        Plus les dates sont proches, plus le score est élevé
        """
        if not date1 or not date2:
            return 0.0
        
        try:
            delta_days = abs((date1 - date2).days)
            
            # Décroissance exponentielle
            if delta_days == 0:
                return 1.0
            elif delta_days <= 1:
                return 0.9
            elif delta_days <= 3:
                return 0.7
            elif delta_days <= 7:
                return 0.5
            elif delta_days <= 14:
                return 0.3
            else:
                return 0.1
        except Exception as e:
            logger.debug(f"Erreur calcul temporel: {e}")
            return 0.0
    
    def _parse_date(self, date_value) -> Optional[datetime]:
        """Parse une date depuis différents formats"""
        if isinstance(date_value, datetime):
            return date_value
        
        if isinstance(date_value, str):
            try:
                # Essayer ISO format
                return datetime.fromisoformat(date_value.replace('Z', '+00:00'))
            except Exception:
                # Essayer d'autres formats
                for fmt in [
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%d",
                    "%a, %d %b %Y %H:%M:%S %z"
                ]:
                    try:
                        return datetime.strptime(date_value, fmt)
                    except Exception:
                        continue
        
        return None
    
    def _theme_similarity(self, themes1: List[str], themes2: List[str]) -> float:
        """Calcule la similarité entre deux ensembles de thèmes (Jaccard)"""
        if not themes1 or not themes2:
            return 0.0
        
        set1 = set(themes1)
        set2 = set(themes2)
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    def _source_similarity(self, source1: str, source2: str) -> float:
        """Vérifie si deux sources sont identiques"""
        if not source1 or not source2:
            return 0.0
        
        return 1.0 if source1.lower() == source2.lower() else 0.0
    
    def compute_similarity(self, article: Dict, candidate: Dict) -> float:
        """
        Calcule le score de similarité global entre deux articles
        Combine plusieurs facteurs : contenu, thèmes, source, temps
        """
        scores = []
        weights = []
        
        # 1. Similarité de contenu (titre + résumé/contenu)
        target_text = f"{article.get('title', '')} {article.get('content', '')[:500]}"
        cand_text = f"{candidate.get('title', '')} {candidate.get('content', '')[:500]}"
        
        content_sim = self._text_similarity(target_text, cand_text)
        scores.append(content_sim)
        weights.append(0.5)  # Poids le plus important
        
        # 2. Similarité de titre seul
        title_sim = self._text_similarity(
            article.get('title', ''),
            candidate.get('title', '')
        )
        scores.append(title_sim)
        weights.append(0.2)
        
        # 3. Similarité thématique
        article_themes = article.get('themes', [])
        if isinstance(article_themes, list) and len(article_themes) > 0:
            # Gérer le cas où themes est une liste de dicts ou de strings
            if isinstance(article_themes[0], dict):
                article_themes = [t.get('id') or t.get('name') for t in article_themes]
        
        cand_themes = candidate.get('themes', [])
        if isinstance(cand_themes, list) and len(cand_themes) > 0:
            if isinstance(cand_themes[0], dict):
                cand_themes = [t.get('id') or t.get('name') for t in cand_themes]
        
        theme_sim = self._theme_similarity(article_themes, cand_themes)
        scores.append(theme_sim)
        weights.append(0.15)
        
        # 4. Proximité temporelle
        date1 = self._parse_date(article.get('pub_date') or article.get('date'))
        date2 = self._parse_date(candidate.get('pub_date') or candidate.get('date'))
        
        if date1 and date2:
            temporal_sim = self._temporal_proximity(date1, date2)
            scores.append(temporal_sim)
            weights.append(0.1)
        
        # 5. Similarité de source
        source_sim = self._source_similarity(
            article.get('feed_url', ''),
            candidate.get('feed_url', '')
        )
        scores.append(source_sim)
        weights.append(0.05)
        
        # Moyenne pondérée
        total_weight = sum(weights)
        if total_weight > 0:
            weighted_score = sum(s * w for s, w in zip(scores, weights)) / total_weight
            return round(weighted_score, 4)
        
        return 0.0
    
    def find_corroborations(self, article: Dict, candidates: List[Dict],
                          threshold: float = 0.65, top_n: int = 10) -> List[Dict]:
        """
        Trouve les articles corroborants pour un article donné
        
        Args:
            article: Article de référence
            candidates: Liste d'articles candidats
            threshold: Seuil minimal de similarité (0.65 par défaut)
            top_n: Nombre maximal de résultats
            
        Returns:
            Liste d'articles similaires avec leur score
        """
        if not candidates:
            logger.debug("Aucun candidat pour corroboration")
            return []
        
        article_id = article.get('id')
        results = []
        
        logger.info(f"🔍 Recherche de corroboration pour article {article_id} parmi {len(candidates)} candidats")
        
        for candidate in candidates:
            # Éviter de comparer avec soi-même
            if candidate.get('id') == article_id:
                continue
            
            # Calcul de similarité
            similarity = self.compute_similarity(article, candidate)
            
            if similarity >= threshold:
                results.append({
                    'id': candidate.get('id'),
                    'title': candidate.get('title'),
                    'source': candidate.get('feed_url', 'Unknown'),
                    'similarity': similarity,
                    'pub_date': candidate.get('pub_date'),
                    'sentiment_type': candidate.get('sentiment_type'),
                    'sentiment_score': candidate.get('sentiment_score')
                })
        
        # Trier par similarité décroissante
        results.sort(key=lambda x: x['similarity'], reverse=True)
        
        # Limiter le nombre de résultats
        results = results[:top_n]
        
        logger.info(f"✅ {len(results)} articles corroborants trouvés (seuil: {threshold})")
        
        return results
    
    def batch_process_articles(self, articles: List[Dict], 
                              recent_articles: List[Dict],
                              db_manager) -> Dict[str, int]:
        """
        Traite un lot d'articles pour trouver leurs corroborations
        
        Args:
            articles: Articles à analyser
            recent_articles: Pool d'articles récents pour comparaison
            db_manager: Gestionnaire de base de données
            
        Returns:
            Statistiques du traitement
        """
        stats = {
            'processed': 0,
            'corroborations_found': 0,
            'errors': 0
        }
        
        for article in articles:
            try:
                # Trouver les corroborations
                corroborations = self.find_corroborations(
                    article,
                    recent_articles,
                    threshold=0.65,
                    top_n=10
                )
                
                # Sauvegarder dans la base
                if corroborations:
                    self._save_corroborations(
                        article.get('id'),
                        corroborations,
                        db_manager
                    )
                    stats['corroborations_found'] += len(corroborations)
                
                stats['processed'] += 1
                
            except Exception as e:
                logger.error(f"Erreur traitement article {article.get('id')}: {e}")
                stats['errors'] += 1
        
        return stats
    
    def _save_corroborations(self, article_id: int, 
                           corroborations: List[Dict],
                           db_manager):
        """Sauvegarde les corroborations dans la base de données"""
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            # Supprimer les anciennes corroborations
            cursor.execute("""
                DELETE FROM article_corroborations 
                WHERE article_id = ?
            """, (article_id,))
            
            # Insérer les nouvelles
            for corr in corroborations:
                cursor.execute("""
                    INSERT INTO article_corroborations 
                    (article_id, similar_article_id, similarity_score, created_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    article_id,
                    corr['id'],
                    corr['similarity']
                ))
            
            conn.commit()
            logger.debug(f"💾 {len(corroborations)} corroborations sauvegardées pour article {article_id}")
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde corroborations: {e}")
            conn.rollback()
        finally:
            conn.close()
