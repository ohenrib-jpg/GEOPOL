# Flask/social_manager.py - Gestionnaire social minimal pour résoudre l'erreur 503

import logging
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class MinimalSocialManager:
    """Gestionnaire social minimal pour fournir des données de base"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.countries = ['france', 'usa', 'uk', 'germany', 'china', 'russia']
    
    def get_social_statistics(self, days=1):
        """Retourne des statistiques sociales de base"""
        try:
            # Données simulées pour le ticker
            return {
                'success': True,
                'statistics': {
                    'total_posts': 150,
                    'average_sentiment': 0.15,
                    'sentiment_distribution': {
                        'positive': 45,
                        'negative': 35,
                        'neutral': 70
                    }
                },
                'method': 'minimal'
            }
        except Exception as e:
            logger.error(f"Erreur statistiques sociales: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def fetch_recent_posts(self, days=1):
        """Récupère des posts récents (simulés)"""
        try:
            # Posts simulés pour la démonstration
            simulated_posts = [
                {
                    'content': 'Discussion sur les politiques économiques actuelles',
                    'sentiment': 'neutral',
                    'engagement': 25,
                    'country': 'france'
                },
                {
                    'content': 'Nouvelles mesures environnementales bien accueillies',
                    'sentiment': 'positive', 
                    'engagement': 42,
                    'country': 'france'
                }
            ]
            
            return {
                'success': True,
                'posts': simulated_posts,
                'count': len(simulated_posts),
                'saved_count': 0,
                'method': 'minimal'
            }
        except Exception as e:
            logger.error(f"Erreur fetch posts: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_top_emotion_themes(self, days=1):
        """Thèmes émotionnels simulés"""
        return {
            'success': True,
            'themes': [
                {'theme': 'économie', 'score': 85, 'posts_count': 23},
                {'theme': 'environnement', 'score': 72, 'posts_count': 18},
                {'theme': 'politique', 'score': 68, 'posts_count': 15}
            ],
            'method': 'minimal'
        }

class SocialComparator:
    """Comparateur social minimal"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def compare_rss_vs_social(self, days=1):
        """Comparaison simulée RSS vs Social"""
        return {
            'success': True,
            'factor_z': 1.2,
            'rss_sentiment': 0.18,
            'social_sentiment': 0.15,
            'discrepancy': 0.03,
            'message': 'Données simulées - Service en développement'
        }
    
    def get_comparison_history(self, limit=20):
        """Historique de comparaison simulé"""
        return {
            'success': True,
            'history': [
                {
                    'date': datetime.now().isoformat(),
                    'factor_z': 1.2,
                    'rss_count': 45,
                    'social_count': 38
                }
            ]
        }