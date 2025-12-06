import logging
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta
import statistics
from collections import defaultdict

logger = logging.getLogger(__name__)


class BatchSentimentAnalyzer:
    """
    Analyseur de sentiment par lots avec cohérence via corroboration
    Principe : Les articles similaires doivent avoir des sentiments cohérents
    """
    
    def __init__(self, sentiment_analyzer, corroboration_engine, bayesian_analyzer):
        self.sentiment_analyzer = sentiment_analyzer
        self.corroboration_engine = corroboration_engine
        self.bayesian_analyzer = bayesian_analyzer
        
        # Configuration
        self.similarity_threshold = 0.70  # Seuil pour considérer articles comme similaires
        self.min_cluster_size = 2  # Minimum d'articles pour former un cluster
        self.max_deviation = 0.3  # Déviation max acceptable dans un cluster
        
    def analyze_batch_with_coherence(self, articles: List[Dict], 
                                     db_manager) -> Dict[str, Any]:
        """
        Analyse un lot d'articles avec garantie de cohérence
        
        Étapes :
        1. Analyse individuelle initiale
        2. Identification des clusters d'articles similaires
        3. Harmonisation des sentiments dans chaque cluster
        4. Application de l'analyse bayésienne
        5. Sauvegarde avec métriques de cohérence
        """
        logger.info(f"🔄 Démarrage analyse batch de {len(articles)} articles")
        
        results = {
            'total_articles': len(articles),
            'analyzed': 0,
            'clusters_found': 0,
            'harmonized': 0,
            'confidence_improved': 0,
            'sentiment_changes': 0,
            'errors': []
        }
        
        # ÉTAPE 1 : Analyse initiale de tous les articles
        logger.info("📊 Étape 1/5 : Analyse initiale...")
        analyzed_articles = self._initial_analysis(articles)
        results['analyzed'] = len(analyzed_articles)
        
        # ÉTAPE 2 : Identification des clusters
        logger.info("🔍 Étape 2/5 : Identification des clusters...")
        clusters = self._identify_clusters(analyzed_articles)
        results['clusters_found'] = len(clusters)
        
        # ÉTAPE 3 : Harmonisation par cluster
        logger.info("⚖️ Étape 3/5 : Harmonisation des clusters...")
        harmonization_stats = self._harmonize_clusters(clusters, analyzed_articles)
        results['harmonized'] = harmonization_stats['harmonized']
        results['sentiment_changes'] = harmonization_stats['changes']
        
        # ÉTAPE 4 : Application bayésienne
        logger.info("🧮 Étape 4/5 : Analyse bayésienne...")
        bayesian_stats = self._apply_bayesian_refinement(analyzed_articles, db_manager)
        results['confidence_improved'] = bayesian_stats['improved']
        
        # ÉTAPE 5 : Sauvegarde
        logger.info("💾 Étape 5/5 : Sauvegarde...")
        save_stats = self._save_batch_results(analyzed_articles, db_manager)
        
        logger.info(f"✅ Analyse batch terminée : {results['analyzed']} articles, "
                   f"{results['clusters_found']} clusters, "
                   f"{results['harmonized']} harmonisés")
        
        return results
    
    def _initial_analysis(self, articles: List[Dict]) -> List[Dict]:
        """
        Analyse initiale de chaque article individuellement
        """
        analyzed = []
        
        for article in articles:
            try:
                # Analyse de sentiment
                sentiment_result = self.sentiment_analyzer.analyze_article(
                    article.get('title', ''),
                    article.get('content', '')
                )
                
                # Enrichir l'article avec les résultats
                article['sentiment_analysis'] = {
                    'score': sentiment_result['score'],
                    'type': sentiment_result['type'],
                    'confidence': sentiment_result['confidence'],
                    'model': sentiment_result['model'],
                    'raw_score': sentiment_result.get('raw_score', sentiment_result['score']),
                    'initial': True  # Marqueur pour savoir si c'est l'analyse initiale
                }
                
                analyzed.append(article)
                
            except Exception as e:
                logger.error(f"Erreur analyse article {article.get('id')}: {e}")
                continue
        
        logger.info(f"✅ {len(analyzed)}/{len(articles)} articles analysés avec succès")
        return analyzed
    
    def _identify_clusters(self, articles: List[Dict]) -> List[List[int]]:
        """
        Identifie les clusters d'articles similaires
        Utilise le moteur de corroboration
        """
        clusters = []
        processed = set()
        
        for i, article in enumerate(articles):
            article_id = article.get('id')
            
            if article_id in processed:
                continue
            
            # Trouver les articles similaires
            similar = self.corroboration_engine.find_corroborations(
                article,
                articles,
                threshold=self.similarity_threshold,
                top_n=20
            )
            
            if len(similar) >= self.min_cluster_size - 1:  # -1 car on ne compte pas l'article lui-même
                # Créer un cluster
                cluster_ids = [article_id] + [s['id'] for s in similar]
                clusters.append(cluster_ids)
                processed.update(cluster_ids)
                
                logger.debug(f"📦 Cluster trouvé : {len(cluster_ids)} articles similaires "
                           f"(article principal: {article_id})")
        
        logger.info(f"🔍 {len(clusters)} clusters identifiés sur {len(articles)} articles")
        return clusters
    
    def _harmonize_clusters(self, clusters: List[List[int]], 
                           articles: List[Dict]) -> Dict[str, int]:
        """
        Harmonise les sentiments au sein de chaque cluster
        Stratégie : utiliser la médiane pondérée par la confiance
        """
        stats = {'harmonized': 0, 'changes': 0}
        
        # Créer un index pour accès rapide
        article_index = {a.get('id'): a for a in articles}
        
        for cluster_ids in clusters:
            # Récupérer les articles du cluster
            cluster_articles = [article_index[aid] for aid in cluster_ids if aid in article_index]
            
            if len(cluster_articles) < self.min_cluster_size:
                continue
            
            # Calculer le sentiment consensus
            consensus = self._calculate_cluster_consensus(cluster_articles)
            
            # Vérifier la cohérence actuelle
            current_scores = [a['sentiment_analysis']['score'] for a in cluster_articles]
            current_deviation = statistics.stdev(current_scores) if len(current_scores) > 1 else 0
            
            # Si la déviation est trop grande, harmoniser
            if current_deviation > self.max_deviation:
                logger.debug(f"⚠️ Cluster incohérent détecté (σ={current_deviation:.3f}), harmonisation...")
                
                for article in cluster_articles:
                    old_score = article['sentiment_analysis']['score']
                    old_type = article['sentiment_analysis']['type']
                    
                    # Appliquer le consensus avec pondération
                    # 60% consensus, 40% analyse originale (pour préserver les nuances)
                    harmonized_score = (consensus['score'] * 0.6) + (old_score * 0.4)
                    
                    # Recatégoriser
                    new_type = self._categorize_harmonized_sentiment(
                        harmonized_score,
                        consensus['confidence']
                    )
                    
                    # Mettre à jour
                    article['sentiment_analysis']['score'] = harmonized_score
                    article['sentiment_analysis']['type'] = new_type
                    article['sentiment_analysis']['harmonized'] = True
                    article['sentiment_analysis']['cluster_size'] = len(cluster_articles)
                    article['sentiment_analysis']['original_score'] = old_score
                    article['sentiment_analysis']['deviation_reduced'] = current_deviation
                    
                    stats['harmonized'] += 1
                    
                    if new_type != old_type:
                        stats['changes'] += 1
                        logger.debug(f"  📝 Article {article.get('id')}: {old_type} → {new_type} "
                                   f"(score: {old_score:.3f} → {harmonized_score:.3f})")
        
        return stats
    
    def _calculate_cluster_consensus(self, cluster_articles: List[Dict]) -> Dict[str, float]:
        """
        Calcule le sentiment consensus d'un cluster
        Utilise la médiane pondérée par la confiance
        """
        # Extraire scores et confidences
        weighted_scores = []
        
        for article in cluster_articles:
            score = article['sentiment_analysis']['score']
            confidence = article['sentiment_analysis']['confidence']
            
            # Ajouter le score autant de fois que sa confiance (arrondie)
            weight = max(1, int(confidence * 10))
            weighted_scores.extend([score] * weight)
        
        # Calculer la médiane pondérée
        consensus_score = statistics.median(weighted_scores)
        
        # Calculer la confiance du consensus (inversement proportionnel à la dispersion)
        score_variance = statistics.variance(weighted_scores) if len(weighted_scores) > 1 else 0
        consensus_confidence = max(0.5, 1.0 - (score_variance * 2))
        
        return {
            'score': consensus_score,
            'confidence': min(0.95, consensus_confidence),
            'sample_size': len(cluster_articles)
        }
    
    def _categorize_harmonized_sentiment(self, score: float, confidence: float) -> str:
        """
        Catégorise un sentiment harmonisé
        Utilise les mêmes seuils que sentiment_analyzer mais avec prudence accrue
        """
        # Seuils (identiques au sentiment_analyzer amélioré)
        thresholds = {
            'positive': 0.25,
            'neutral_positive': 0.08,
            'neutral_negative': -0.08,
            'negative': -0.25
        }
        
        # Si confiance faible, préférer neutre
        if confidence < 0.4:
            return 'neutral_positive' if score >= 0 else 'neutral_negative'
        
        if score >= thresholds['positive']:
            return 'positive'
        elif score >= thresholds['neutral_positive']:
            return 'neutral_positive'
        elif score >= thresholds['neutral_negative']:
            return 'neutral_negative'
        else:
            return 'negative'
    
    def _apply_bayesian_refinement(self, articles: List[Dict], 
                                   db_manager) -> Dict[str, int]:
        """
        Applique l'analyse bayésienne pour raffiner les scores
        """
        stats = {'improved': 0, 'errors': 0}
        
        for article in articles:
            try:
                # Récupérer les corroborations depuis la DB
                corroboration_data = self._get_corroboration_from_db(
                    article.get('id'),
                    db_manager
                )
                
                # Préparer les données pour l'analyse bayésienne
                article_data = {
                    'sentiment_score': article['sentiment_analysis']['score'],
                    'sentiment_confidence': article['sentiment_analysis']['confidence'],
                    'sentiment_type': article['sentiment_analysis']['type'],
                    'pub_date': article.get('pub_date'),
                    'themes': article.get('themes', [])
                }
                
                # Analyse bayésienne
                bayesian_result = self.bayesian_analyzer.analyze_article_sentiment(
                    article_data,
                    corroboration_data
                )
                
                # Vérifier si la confiance s'est améliorée
                old_confidence = article['sentiment_analysis']['confidence']
                new_confidence = bayesian_result['bayesian_confidence']
                
                if new_confidence > old_confidence:
                    stats['improved'] += 1
                
                # Enrichir l'article
                article['sentiment_analysis']['bayesian_score'] = bayesian_result['bayesian_score']
                article['sentiment_analysis']['bayesian_confidence'] = new_confidence
                article['sentiment_analysis']['evidence_count'] = bayesian_result['evidence_count']
                
                # Utiliser le score bayésien comme score final
                article['sentiment_analysis']['final_score'] = bayesian_result['bayesian_score']
                article['sentiment_analysis']['final_type'] = bayesian_result['sentiment_type']
                
            except Exception as e:
                logger.error(f"Erreur bayésienne article {article.get('id')}: {e}")
                stats['errors'] += 1
                # En cas d'erreur, garder l'analyse harmonisée
                article['sentiment_analysis']['final_score'] = article['sentiment_analysis']['score']
                article['sentiment_analysis']['final_type'] = article['sentiment_analysis']['type']
        
        return stats
    
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
    
    def _save_batch_results(self, articles: List[Dict], db_manager) -> Dict[str, int]:
        """
        Sauvegarde les résultats de l'analyse batch
        """
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        stats = {'saved': 0, 'errors': 0}
        
        try:
            for article in articles:
                try:
                    analysis = article['sentiment_analysis']
                    
                    cursor.execute("""
                        UPDATE articles
                        SET sentiment_score = ?,
                            sentiment_type = ?,
                            sentiment_confidence = ?,
                            bayesian_confidence = ?,
                            bayesian_evidence_count = ?,
                            harmonized = ?,
                            cluster_size = ?,
                            analysis_metadata = ?
                        WHERE id = ?
                    """, (
                        analysis.get('final_score', analysis['score']),
                        analysis.get('final_type', analysis['type']),
                        analysis['confidence'],
                        analysis.get('bayesian_confidence', analysis['confidence']),
                        analysis.get('evidence_count', 0),
                        1 if analysis.get('harmonized', False) else 0,
                        analysis.get('cluster_size', 1),
                        str({
                            'initial_score': analysis.get('original_score', analysis['score']),
                            'harmonized': analysis.get('harmonized', False),
                            'model': analysis['model'],
                            'deviation_reduced': analysis.get('deviation_reduced', 0)
                        }),
                        article.get('id')
                    ))
                    
                    stats['saved'] += 1
                    
                except Exception as e:
                    logger.error(f"Erreur sauvegarde article {article.get('id')}: {e}")
                    stats['errors'] += 1
            
            conn.commit()
            logger.info(f"💾 {stats['saved']}/{len(articles)} articles sauvegardés")
            
        except Exception as e:
            logger.error(f"Erreur globale sauvegarde: {e}")
            conn.rollback()
        finally:
            conn.close()
        
        return stats
    
    def analyze_recent_articles(self, db_manager, days: int = 7) -> Dict[str, Any]:
        """
        Analyse les articles récents (helper method)
        
        Args:
            db_manager: Gestionnaire de base de données
            days: Nombre de jours à analyser
            
        Returns:
            Résultats de l'analyse
        """
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            # Récupérer les articles récents
            cursor.execute("""
                SELECT id, title, content, pub_date, feed_url, sentiment_score, sentiment_type
                FROM articles
                WHERE pub_date >= datetime('now', '-' || ? || ' days')
                ORDER BY pub_date DESC
            """, (days,))
            
            articles = []
            for row in cursor.fetchall():
                articles.append({
                    'id': row[0],
                    'title': row[1],
                    'content': row[2],
                    'pub_date': row[3],
                    'feed_url': row[4],
                    'sentiment_score': row[5],
                    'sentiment_type': row[6]
                })
            
            logger.info(f"📰 {len(articles)} articles récents trouvés ({days} derniers jours)")
            
            # Lancer l'analyse batch
            if articles:
                return self.analyze_batch_with_coherence(articles, db_manager)
            else:
                return {'error': 'Aucun article à analyser'}
            
        finally:
            conn.close()
    
    def get_cluster_report(self, db_manager) -> Dict[str, Any]:
        """
        Génère un rapport sur les clusters détectés
        """
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            # Articles harmonisés
            cursor.execute("""
                SELECT COUNT(*) 
                FROM articles 
                WHERE harmonized = 1
            """)
            harmonized_count = cursor.fetchone()[0]
            
            # Distribution par taille de cluster
            cursor.execute("""
                SELECT cluster_size, COUNT(*) as count
                FROM articles
                WHERE cluster_size > 1
                GROUP BY cluster_size
                ORDER BY cluster_size DESC
            """)
            
            cluster_distribution = {}
            for row in cursor.fetchall():
                cluster_distribution[row[0]] = row[1]
            
            return {
                'harmonized_articles': harmonized_count,
                'cluster_distribution': cluster_distribution,
                'total_clustered': sum(cluster_distribution.values())
            }
            
        finally:
            conn.close()


# Fonction d'intégration pour l'utilisation dans Flask
def create_batch_analyzer(sentiment_analyzer, corroboration_engine, bayesian_analyzer):
    """
    Factory function pour créer une instance configurée
    """
    return BatchSentimentAnalyzer(
        sentiment_analyzer,
        corroboration_engine,
        bayesian_analyzer
    )