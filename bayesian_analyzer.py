# Flask/bayesian_analyzer.py
"""
Module d'analyse bayésienne pour renforcer l'analyse de sentiment
Intégration directe sans pont JavaScript
"""

import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class BayesianSentimentAnalyzer:
    """
    Analyseur bayésien pour fusion des évidences de sentiment
    """
    
    def __init__(self):
        self.default_prior = 0.5  # Prior neutre
        
    def bayesian_update(self, prior: float, likelihood: float, 
                       evidence_weight: float = 1.0) -> Dict[str, float]:
        """
        Mise à jour bayésienne : P(H|E) = P(E|H) * P(H) / P(E)
        
        Args:
            prior: Probabilité a priori (0-1)
            likelihood: Vraisemblance de l'évidence (0-1)
            evidence_weight: Poids de confiance (0-1)
            
        Returns:
            Dict avec 'posterior' et 'confidence'
        """
        # Normalisation
        prior = max(0.01, min(0.99, prior))
        likelihood = max(0.01, min(0.99, likelihood))
        evidence_weight = max(0.0, min(1.0, evidence_weight))
        
        # Calcul bayésien
        likelihood_not = 1.0 - likelihood
        numerator = likelihood * prior
        denominator = (likelihood * prior) + (likelihood_not * (1 - prior))
        
        posterior = numerator / denominator if denominator != 0 else prior
        
        # Application du poids
        posterior = prior + (posterior - prior) * evidence_weight
        
        # Calcul de confiance
        confidence = abs(posterior - prior) * evidence_weight
        confidence = min(0.95, max(0.1, confidence))
        
        return {
            'posterior': round(posterior, 4),
            'confidence': round(confidence, 4)
        }
    
    def fusion_multiple_evidences(self, evidences: List[Dict]) -> Dict[str, float]:
        """
        Fusion de plusieurs évidences par mise à jour séquentielle
        
        Args:
            evidences: Liste de dict avec 'type', 'value', 'confidence'
            
        Returns:
            Dict avec 'posterior' et 'confidence' finales
        """
        if not evidences:
            return {'posterior': self.default_prior, 'confidence': 0.0}
        
        current_posterior = self.default_prior
        cumulative_confidence = 0.0
        
        for evidence in evidences:
            value = evidence.get('value', 0.5)
            confidence = evidence.get('confidence', 0.5)
            
            result = self.bayesian_update(
                prior=current_posterior,
                likelihood=value,
                evidence_weight=confidence
            )
            
            current_posterior = result['posterior']
            cumulative_confidence += result['confidence'] * confidence
        
        avg_confidence = cumulative_confidence / len(evidences) if evidences else 0.0
        
        return {
            'posterior': round(current_posterior, 4),
            'confidence': round(min(0.95, avg_confidence), 4),
            'evidence_count': len(evidences)
        }
    
    def analyze_article_sentiment(self, article_data: Dict[str, Any], 
                                  corroboration_data: List[Dict] = None) -> Dict[str, Any]:
        """
        Analyse le sentiment d'un article avec fusion bayésienne
        
        Args:
            article_data: Données de l'article avec sentiment initial
            corroboration_data: Articles similaires pour contexte
            
        Returns:
            Analyse enrichie avec score bayésien
        """
        evidences = []
        
        # 1. Évidence principale : sentiment TextBlob/VADER
        initial_sentiment = article_data.get('sentiment_score', 0.0)
        initial_confidence = article_data.get('sentiment_confidence', 0.5)
        
        # Normaliser le sentiment (-1,1) vers (0,1)
        normalized_sentiment = (initial_sentiment + 1) / 2
        
        evidences.append({
            'type': 'initial_analysis',
            'value': normalized_sentiment,
            'confidence': initial_confidence
        })
        
        # 2. Évidence de corroboration (si disponible)
        if corroboration_data:
            similar_sentiments = []
            for corr in corroboration_data:
                if corr.get('sentiment_score') is not None:
                    # Pondérer par la similarité
                    similarity = corr.get('similarity', 0.5)
                    sent = (corr['sentiment_score'] + 1) / 2
                    similar_sentiments.append((sent, similarity))
            
            if similar_sentiments:
                # Moyenne pondérée des sentiments similaires
                weighted_avg = sum(s * w for s, w in similar_sentiments) / sum(w for _, w in similar_sentiments)
                avg_similarity = sum(w for _, w in similar_sentiments) / len(similar_sentiments)
                
                evidences.append({
                    'type': 'corroboration',
                    'value': weighted_avg,
                    'confidence': avg_similarity * 0.8  # Réduction pour prudence
                })
        
        # 3. Évidence temporelle (récence de l'article)
        pub_date = article_data.get('pub_date')
        if pub_date:
            try:
                if isinstance(pub_date, str):
                    pub_date = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                days_old = (datetime.now(pub_date.tzinfo or None) - pub_date).days
                
                # Les articles récents ont plus de poids
                recency_confidence = max(0.3, 1.0 - (days_old / 30))
                
                evidences.append({
                    'type': 'temporal',
                    'value': normalized_sentiment,  # Renforce le sentiment initial
                    'confidence': recency_confidence * 0.6
                })
            except Exception as e:
                logger.debug(f"Erreur parsing date: {e}")
        
        # 4. Évidence thématique (cohérence avec le thème)
        themes = article_data.get('themes', [])
        if themes:
            # Si l'article a plusieurs thèmes détectés avec confiance
            theme_confidence = sum(t.get('confidence', 0) for t in themes) / len(themes) if themes else 0
            
            evidences.append({
                'type': 'thematic',
                'value': normalized_sentiment,
                'confidence': theme_confidence * 0.5
            })
        
        # Fusion bayésienne
        result = self.fusion_multiple_evidences(evidences)
        
        # Conversion du posterior vers échelle de sentiment (-1, 1)
        bayesian_sentiment = (result['posterior'] * 2) - 1
        
        # Détermination du type de sentiment avec le score bayésien
        if bayesian_sentiment > 0.1:
            sentiment_type = 'positive'
        elif bayesian_sentiment < -0.1:
            sentiment_type = 'negative'
        else:
            sentiment_type = 'neutral'
        
        return {
            'original_score': initial_sentiment,
            'bayesian_score': round(bayesian_sentiment, 4),
            'bayesian_confidence': result['confidence'],
            'sentiment_type': sentiment_type,
            'evidence_count': result['evidence_count'],
            'evidences_used': [e['type'] for e in evidences]
        }
    
    def batch_analyze_articles(self, articles: List[Dict], 
                               db_manager) -> Dict[str, Any]:
        """
        Analyse en batch plusieurs articles
        
        Args:
            articles: Liste d'articles à analyser
            db_manager: Gestionnaire de base de données
            
        Returns:
            Résultats de l'analyse batch
        """
        results = {
            'analyzed': 0,
            'updated': 0,
            'errors': []
        }
        
        for article in articles:
            try:
                # Récupérer les données de corroboration depuis la DB
                corroboration_data = self._get_corroboration_from_db(
                    article.get('id'), 
                    db_manager
                )
                
                # Analyse bayésienne
                analysis = self.analyze_article_sentiment(
                    article, 
                    corroboration_data
                )
                
                # Mise à jour dans la base
                self._save_bayesian_analysis(
                    article.get('id'),
                    analysis,
                    db_manager
                )
                
                results['analyzed'] += 1
                
                # Vérifier si le sentiment a changé
                if analysis['sentiment_type'] != article.get('sentiment_type'):
                    results['updated'] += 1
                    
            except Exception as e:
                logger.error(f"Erreur analyse article {article.get('id')}: {e}")
                results['errors'].append(str(e))
        
        return results
    
    def _get_corroboration_from_db(self, article_id: int, db_manager) -> List[Dict]:
        """Récupère les données de corroboration depuis la base"""
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT c.similar_article_id, c.similarity_score,
                       a.sentiment_score, a.sentiment_type
                FROM article_corroborations c
                JOIN articles a ON c.similar_article_id = a.id
                WHERE c.article_id = ? AND c.similarity_score >= 0.65
                ORDER BY c.similarity_score DESC
                LIMIT 10
            """, (article_id,))
            
            corroborations = []
            for row in cursor.fetchall():
                corroborations.append({
                    'similar_article_id': row[0],
                    'similarity': row[1],
                    'sentiment_score': row[2],
                    'sentiment_type': row[3]
                })
            
            return corroborations
        finally:
            conn.close()
    
    def _save_bayesian_analysis(self, article_id: int, analysis: Dict, db_manager):
        """Sauvegarde l'analyse bayésienne dans la base"""
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE articles
                SET sentiment_score = ?,
                    sentiment_type = ?,
                    bayesian_confidence = ?,
                    bayesian_evidence_count = ?
                WHERE id = ?
            """, (
                analysis['bayesian_score'],
                analysis['sentiment_type'],
                analysis['bayesian_confidence'],
                analysis['evidence_count'],
                article_id
            ))
            
            conn.commit()
            logger.info(f"✅ Analyse bayésienne sauvegardée pour article {article_id}")
        except Exception as e:
            logger.error(f"Erreur sauvegarde: {e}")
            conn.rollback()
        finally:
            conn.close()
