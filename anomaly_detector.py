# Flask/anomaly_detector.py
"""
Module de détection d'anomalies et d'écarts dans les données géopolitiques
"""

import logging
import numpy as np
from typing import List, Dict, Any
from datetime import datetime, timedelta
from scipy import stats
from .database import DatabaseManager

logger = logging.getLogger(__name__)

class AnomalyDetector:
    """
    Détecteur d'anomalies pour identifier les écarts significatifs dans les données
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def detect_sentiment_anomalies(self, days: int = 7, threshold: float = 2.0) -> List[Dict[str, Any]]:
        """
        Détecte les anomalies de sentiment sur une période donnée
        Utilise la méthode statistique des z-scores
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Récupérer les données de sentiment
            cursor.execute("""
                SELECT sentiment_score, pub_date
                FROM articles
                WHERE pub_date >= ?
                ORDER BY pub_date
            """, (cutoff_date,))
            
            scores = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            if len(scores) < 10:
                return []
            
            # Calcul des statistiques de base
            mean_score = np.mean(scores)
            std_score = np.std(scores)
            
            if std_score == 0:
                return []
            
            # Calcul des z-scores
            z_scores = [(score - mean_score) / std_score for score in scores]
            
            # Identifier les anomalies (|z-score| > threshold)
            anomalies = []
            for i, (score, z_score) in enumerate(zip(scores, z_scores)):
                if abs(z_score) > threshold:
                    anomalies.append({
                        'score': score,
                        'z_score': z_score,
                        'is_positive_anomaly': z_score > threshold,
                        'is_negative_anomaly': z_score < -threshold,
                        'confidence': min(1.0, abs(z_score) / (threshold * 2))
                    })
            
            logger.info(f"🔍 {len(anomalies)} anomalies de sentiment détectées sur {len(scores)} articles")
            return anomalies
            
        except Exception as e:
            logger.error(f"Erreur détection anomalies sentiment: {e}")
            return []
    
    def detect_theme_anomalies(self, theme_id: str, days: int = 7) -> Dict[str, Any]:
        """
        Détecte les anomalies dans l'apparition d'un thème
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Compter les articles par jour pour ce thème
            cursor.execute("""
                SELECT DATE(a.pub_date) as date, COUNT(*) as count
                FROM articles a
                JOIN theme_analyses ta ON a.id = ta.article_id
                WHERE ta.theme_id = ? AND a.pub_date >= ?
                GROUP BY DATE(a.pub_date)
                ORDER BY date
            """, (theme_id, cutoff_date))
            
            daily_counts = [(row[0], row[1]) for row in cursor.fetchall()]
            conn.close()
            
            if len(daily_counts) < 3:
                return {'anomaly_detected': False, 'message': 'Données insuffisantes'}
            
            counts = [count for _, count in daily_counts]
            mean_count = np.mean(counts)
            std_count = np.std(counts)
            
            if std_count == 0:
                return {'anomaly_detected': False, 'message': 'Variance nulle'}
            
            # Détecter les pics significatifs (2 écarts-types au-dessus de la moyenne)
            significant_peaks = []
            for date, count in daily_counts:
                if count > mean_count + 2 * std_count:
                    significant_peaks.append({
                        'date': date,
                        'count': count,
                        'z_score': (count - mean_count) / std_count,
                        'increase_factor': count / max(1, mean_count)
                    })
            
            return {
                'anomaly_detected': len(significant_peaks) > 0,
                'mean_daily_count': mean_count,
                'std_daily_count': std_count,
                'significant_peaks': significant_peaks,
                'total_peaks': len(significant_peaks)
            }
            
        except Exception as e:
            logger.error(f"Erreur détection anomalies thème {theme_id}: {e}")
            return {'anomaly_detected': False, 'error': str(e)}
    
    def detect_correlation_anomalies(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Détecte les anomalies dans les corrélations entre thèmes et sentiments
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # Récupérer les données thème-sentiment
            cursor.execute("""
                SELECT t.id, t.name, AVG(a.sentiment_score) as avg_sentiment, COUNT(*) as article_count
                FROM themes t
                JOIN theme_analyses ta ON t.id = ta.theme_id
                JOIN articles a ON ta.article_id = a.id
                WHERE a.pub_date >= ? AND ta.confidence >= 0.1
                GROUP BY t.id, t.name
                HAVING COUNT(*) >= 5
            """, (cutoff_date,))
            
            theme_data = cursor.fetchall()
            conn.close()
            
            if len(theme_data) < 2:
                return []
            
            # Calculer les corrélations
            theme_names = [row[1] for row in theme_data]
            sentiment_scores = [row[2] for row in theme_data]
            article_counts = [row[3] for row in theme_data]
            
            # Corrélation entre sentiment et fréquence
            if len(sentiment_scores) > 1 and len(article_counts) > 1:
                correlation, p_value = stats.pearsonr(sentiment_scores, article_counts)
                
                return [{
                    'type': 'sentiment_frequency_correlation',
                    'correlation': correlation,
                    'p_value': p_value,
                    'is_significant': p_value < 0.05,
                    'strength': 'strong' if abs(correlation) > 0.7 else 'moderate' if abs(correlation) > 0.3 else 'weak',
                    'interpretation': self._interpret_correlation(correlation)
                }]
            
            return []
            
        except Exception as e:
            logger.error(f"Erreur détection anomalies corrélation: {e}")
            return []
    
    def _interpret_correlation(self, correlation: float) -> str:
        """Interprète la signification d'une corrélation"""
        if correlation > 0.7:
            return "Corrélation positive forte: les thèmes les plus fréquents ont tendance à être plus positifs"
        elif correlation > 0.3:
            return "Corrélation positive modérée"
        elif correlation < -0.7:
            return "Corrélation négative forte: les thèmes les plus fréquents ont tendance à être plus négatifs"
        elif correlation < -0.3:
            return "Corrélation négative modérée"
        else:
            return "Corrélation faible ou inexistante"
    
    def get_comprehensive_anomaly_report(self, days: int = 7) -> Dict[str, Any]:
        """
        Génère un rapport complet des anomalies détectées
        """
        report = {
            'timestamp': datetime.now(),
            'period_days': days,
            'sentiment_anomalies': self.detect_sentiment_anomalies(days),
            'theme_anomalies': {},
            'correlation_anomalies': self.detect_correlation_anomalies(days)
        }
        
        # Analyser les anomalies pour chaque thème
        themes = self.db_manager.get_themes()
        for theme in themes:
            theme_anomaly = self.detect_theme_anomalies(theme['id'], days)
            if theme_anomaly.get('anomaly_detected', False) or theme_anomaly.get('total_peaks', 0) > 0:
                report['theme_anomalies'][theme['id']] = theme_anomaly
        
        return report
