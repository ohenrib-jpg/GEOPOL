# Flask/social_comparator.py
"""
Module de comparaison des sentiments RSS vs Réseaux Sociaux
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from .database import DatabaseManager

logger = logging.getLogger(__name__)

class SocialComparator:
    """
    Comparateur de sentiments entre médias traditionnels et réseaux sociaux
    Calcule le "Facteur Z" de dissonance médiatique
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        
    def compare_rss_vs_social(self, days: int = 1) -> Dict[str, Any]:
        """
        Compare les sentiments entre articles RSS et posts sociaux
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Récupérer les articles RSS
            rss_articles = self._get_rss_articles(cutoff_date)
            
            # Récupérer les posts sociaux
            social_posts = self._get_social_posts(cutoff_date)
            
            logger.info(f"📊 Comparaison: {len(rss_articles)} RSS vs {len(social_posts)} social")
            
            if not rss_articles or not social_posts:
                return {
                    'success': False,
                    'error': 'Données insuffisantes pour la comparaison',
                    'rss_count': len(rss_articles),
                    'social_count': len(social_posts)
                }
            
            # Analyser les distributions
            rss_analysis = self._analyze_sentiment_distribution(rss_articles, 'rss')
            social_analysis = self._analyze_sentiment_distribution(social_posts, 'social')
            
            # Calculer la divergence
            divergence = self._calculate_divergence(rss_analysis, social_analysis)
            
            # Calculer le Facteur Z
            factor_z = self._calculate_factor_z(rss_analysis, social_analysis)
            
            # Générer les recommandations
            recommendations = self._generate_recommendations(divergence, factor_z)
            
            comparison_result = {
                'timestamp': datetime.now(),
                'rss_analysis': rss_analysis,
                'social_analysis': social_analysis,
                'divergence': divergence,
                'factor_z': factor_z,
                'recommendations': recommendations
            }
            
            # Sauvegarder la comparaison
            self._save_comparison(comparison_result)
            
            logger.info(f"✅ Comparaison terminée: Facteur Z = {factor_z['value']:.3f}")
            
            return {
                'success': True,
                'comparison': comparison_result,
                'summary': {
                    'rss_sentiment': rss_analysis['average'],
                    'social_sentiment': social_analysis['average'],
                    'divergence': divergence['absolute'],
                    'factor_z': factor_z['value'],
                    'interpretation': factor_z['interpretation']
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur compare_rss_vs_social: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_rss_articles(self, cutoff_date: datetime) -> List[Dict[str, Any]]:
        """Récupère les articles RSS récents"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, title, content, sentiment_score, sentiment_type
            FROM articles
            WHERE pub_date >= ?
            ORDER BY pub_date DESC
            LIMIT 500
        """, (cutoff_date,))
        
        articles = []
        for row in cursor.fetchall():
            articles.append({
                'id': row[0],
                'title': row[1],
                'content': row[2],
                'sentiment_score': row[3],
                'sentiment_type': row[4]
            })
        
        conn.close()
        return articles
    
    def _get_social_posts(self, cutoff_date: datetime) -> List[Dict[str, Any]]:
        """Récupère les posts sociaux récents"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, title, content, sentiment_score, sentiment_type
            FROM social_posts
            WHERE pub_date >= ?
            ORDER BY pub_date DESC
            LIMIT 500
        """, (cutoff_date,))
        
        posts = []
        for row in cursor.fetchall():
            posts.append({
                'id': row[0],
                'title': row[1],
                'content': row[2],
                'sentiment_score': row[3],
                'sentiment_type': row[4]
            })
        
        conn.close()
        return posts
    
    def _analyze_sentiment_distribution(self, items: List[Dict[str, Any]], item_type: str) -> Dict[str, Any]:
        """
        Analyse la distribution des sentiments
        """
        distribution = {
            'positive': 0,
            'neutral': 0,
            'negative': 0,
            'total': 0,
            'scores': []
        }
        
        total_score = 0
        total_weighted_score = 0
        
        for item in items:
            score = float(item.get('sentiment_score', 0))
            sentiment_type = item.get('sentiment_type', 'neutral')
            
            distribution['scores'].append(score)
            total_score += score
            
            # Pondération par confiance si disponible
            confidence = float(item.get('sentiment_confidence', 1))
            total_weighted_score += score * confidence
            
            # Classification
            if sentiment_type == 'positive' or score > 0.1:
                distribution['positive'] += 1
            elif sentiment_type == 'negative' or score < -0.1:
                distribution['negative'] += 1
            else:
                distribution['neutral'] += 1
            
            distribution['total'] += 1
        
        # Calculs statistiques
        avg_score = total_score / distribution['total'] if distribution['total'] > 0 else 0
        weighted_avg = total_weighted_score / distribution['total'] if distribution['total'] > 0 else 0
        
        # Variance et écart-type
        variance = 0
        if distribution['total'] > 1:
            for score in distribution['scores']:
                variance += (score - avg_score) ** 2
            variance /= (distribution['total'] - 1)
        
        std_dev = variance ** 0.5
        
        return {
            'type': item_type,
            'total': distribution['total'],
            'distribution': {
                'positive': distribution['positive'],
                'neutral': distribution['neutral'],
                'negative': distribution['negative'],
                'positive_percent': (distribution['positive'] / distribution['total'] * 100) if distribution['total'] > 0 else 0,
                'neutral_percent': (distribution['neutral'] / distribution['total'] * 100) if distribution['total'] > 0 else 0,
                'negative_percent': (distribution['negative'] / distribution['total'] * 100) if distribution['total'] > 0 else 0
            },
            'average': round(avg_score, 4),
            'weighted_average': round(weighted_avg, 4),
            'variance': round(variance, 4),
            'std_dev': round(std_dev, 4),
            'min_score': min(distribution['scores']) if distribution['scores'] else 0,
            'max_score': max(distribution['scores']) if distribution['scores'] else 0
        }
    
    def _calculate_divergence(self, rss_analysis: Dict, social_analysis: Dict) -> Dict[str, Any]:
        """
        Calcule la divergence entre les distributions
        """
        # Différence absolue des moyennes
        mean_diff = abs(rss_analysis['average'] - social_analysis['average'])
        
        # Différence relative en pourcentage
        relative_diff = 0
        if rss_analysis['average'] != 0:
            relative_diff = abs((social_analysis['average'] - rss_analysis['average']) / rss_analysis['average'] * 100)
        
        # Classification de la divergence
        if mean_diff > 2.0:
            level = 'high'
        elif mean_diff > 1.0:
            level = 'medium'
        else:
            level = 'low'
        
        return {
            'absolute': round(mean_diff, 4),
            'relative': round(relative_diff, 2),
            'level': level,
            'rss_average': rss_analysis['average'],
            'social_average': social_analysis['average']
        }
    
    def _calculate_factor_z(self, rss_analysis: Dict, social_analysis: Dict) -> Dict[str, Any]:
        """
        Calcule le Facteur Z (Z-score) de dissonance médiatique
        """
        # Différence des moyennes
        mean_diff = abs(rss_analysis['average'] - social_analysis['average'])
        
        # Variance poolée
        n1 = rss_analysis['total']
        n2 = social_analysis['total']
        pooled_variance = ((rss_analysis['variance'] * n1) + (social_analysis['variance'] * n2)) / (n1 + n2)
        
        # Erreur standard
        standard_error = (pooled_variance / n1 + pooled_variance / n2) ** 0.5
        
        # Z-score
        z_score = mean_diff / standard_error if standard_error > 0 else 0
        
        # Interprétation
        abs_z = abs(z_score)
        if abs_z > 2.5:
            interpretation = 'Dissonance majeure'
            confidence = 'very_high'
        elif abs_z > 1.5:
            interpretation = 'Dissonance modérée'
            confidence = 'high'
        elif abs_z > 0.5:
            interpretation = 'Légère dissonance'
            confidence = 'medium'
        else:
            interpretation = 'Validation populaire'
            confidence = 'low'
        
        return {
            'value': round(z_score, 4),
            'absolute_value': round(abs_z, 4),
            'interpretation': interpretation,
            'confidence': confidence,
            'mean_difference': round(mean_diff, 4),
            'standard_error': round(standard_error, 4),
            'pooled_variance': round(pooled_variance, 4)
        }
    
    def _generate_recommendations(self, divergence: Dict, factor_z: Dict) -> List[Dict[str, Any]]:
        """
        Génère des recommandations basées sur l'analyse
        """
        recommendations = []
        
        if factor_z['absolute_value'] > 2.5:
            recommendations.append({
                'level': 'critical',
                'message': 'Divergence majeure détectée entre médias et réseaux sociaux',
                'action': 'Analyser les causes de la dissonance et vérifier les sources'
            })
        
        if divergence['level'] == 'high':
            recommendations.append({
                'level': 'warning',
                'message': 'Écart significatif dans les sentiments exprimés',
                'action': 'Comparer les thèmes abordés par chaque source'
            })
        
        if factor_z['absolute_value'] < 0.5:
            recommendations.append({
                'level': 'success',
                'message': 'Convergence des opinions médiatiques et populaires',
                'action': 'Consensus général sur les sujets traités'
            })
        
        if not recommendations:
            recommendations.append({
                'level': 'info',
                'message': 'Divergence modérée observée',
                'action': 'Surveillance continue recommandée'
            })
        
        return recommendations
    
    def _save_comparison(self, comparison: Dict[str, Any]):
        """
        Sauvegarde la comparaison dans la base
        """
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sentiment_comparisons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME,
                    rss_total INTEGER,
                    rss_avg_sentiment REAL,
                    social_total INTEGER,
                    social_avg_sentiment REAL,
                    divergence_absolute REAL,
                    factor_z_value REAL,
                    interpretation TEXT,
                    recommendations TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                INSERT INTO sentiment_comparisons 
                (timestamp, rss_total, rss_avg_sentiment, social_total, social_avg_sentiment,
                 divergence_absolute, factor_z_value, interpretation, recommendations)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                comparison['timestamp'],
                comparison['rss_analysis']['total'],
                comparison['rss_analysis']['average'],
                comparison['social_analysis']['total'],
                comparison['social_analysis']['average'],
                comparison['divergence']['absolute'],
                comparison['factor_z']['value'],
                comparison['factor_z']['interpretation'],
                str(comparison['recommendations'])
            ))
            
            conn.commit()
            logger.debug("💾 Comparison saved")
            
        except Exception as e:
            logger.error(f"Error saving comparison: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def get_comparison_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Récupère l'historique des comparaisons
        """
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT timestamp, rss_total, social_total, factor_z_value, interpretation
            FROM sentiment_comparisons
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        history = []
        for row in cursor.fetchall():
            history.append({
                'timestamp': row[0],
                'rss_count': row[1],
                'social_count': row[2],
                'factor_z': row[3],
                'interpretation': row[4]
            })
        
        conn.close()
        return history

# Instance globale
_social_comparator = None

def get_social_comparator(db_manager: DatabaseManager) -> SocialComparator:
    """Retourne l'instance singleton du comparateur"""
    global _social_comparator
    if _social_comparator is None:
        _social_comparator = SocialComparator(db_manager)
    return _social_comparator
