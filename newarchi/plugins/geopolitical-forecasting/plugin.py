"""
Plugin: Media Sentiment Analysis
Description: Analyse des sentiments médiatiques via scraping RSS et analyse émotionnelle
"""

import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging
import re
from collections import Counter

logger = logging.getLogger(__name__)

class Plugin:
    """Classe principale du plugin"""
    
    def __init__(self, settings):
        """Initialisation"""
        self.name = "media-sentiment-analysis"
        self.settings = settings
    
    def run(self, payload=None):
        """Point d'entrée principal"""
        if payload is None:
            payload = {}
        
        try:
            # VOTRE LOGIQUE ICI
            results = self._analyze_media_sentiment(payload)
            
            return {
                'status': 'success',
                'plugin': self.name,
                'timestamp': self._get_timestamp(),
                'data': results['data'],
                'metrics': results['metrics'],
                'message': 'Analyse médiatique terminée'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'plugin': self.name,
                'timestamp': self._get_timestamp(),
                'data': [],
                'metrics': {},
                'message': f'Erreur: {str(e)}'
            }
    
    def _analyze_media_sentiment(self, payload):
        """Logique d'analyse des sentiments médiatiques"""
        keywords = payload.get('keywords', ['conflict', 'economy', 'politics', 'security'])
        sources = payload.get('sources', ['bbc', 'reuters', 'npr'])
        
        # Collecte des articles
        articles = self._collect_articles(sources, keywords)
        
        # Analyse des sentiments
        analyzed_articles = self._analyze_articles(articles)
        
        # Détection de tendances
        trends = self._detect_trends(analyzed_articles)
        
        data = []
        for article in analyzed_articles[:15]:  # Limiter aux 15 premiers
            data.append({
                'source': article['source'],
                'titre': article['title'],
                'date_publication': article['published'],
                'sentiment_global': article['sentiment_label'],
                'score_sentiment': article['sentiment_score'],
                'emotion_dominante': article['dominant_emotion'],
                'mots_cles_trouves': ', '.join(article['keywords_found']),
                'urgence_detectee': article['urgency_detected']
            })
        
        metrics = {
            'articles_analyses': len(analyzed_articles),
            'sentiment_moyen': self._calculate_average_sentiment(analyzed_articles),
            'emotion_predominante': self._get_predominant_emotion(analyzed_articles),
            'couverture_geographique': len(set([a.get('region', 'Global') for a in analyzed_articles])),
            'alertes_mediatiques': len([a for a in analyzed_articles if a['urgency_detected']])
        }
        
        return {'data': data, 'metrics': metrics}
    
    def _collect_articles(self, sources, keywords):
        """Collecte les articles des sources RSS"""
        articles = []
        
        rss_feeds = {
            'bbc': 'http://feeds.bbci.co.uk/news/world/rss.xml',
            'reuters': 'https://rss.reuters.com/reuters/worldNews',
            'npr': 'https://feeds.npr.org/1001/rss.xml',
            'cnn': 'http://rss.cnn.com/rss/edition.rss'
        }
        
        for source in sources:
            if source in rss_feeds:
                try:
                    feed = feedparser.parse(rss_feeds[source])
                    
                    for entry in feed.entries[:10]:  # 10 articles par source
                        if self._matches_keywords(entry, keywords):
                            articles.append({
                                'source': source,
                                'title': entry.title,
                                'link': entry.link,
                                'published': self._parse_date(entry),
                                'summary': entry.get('summary', ''),
                                'content': self._extract_content(entry)
                            })
                            
                except Exception as e:
                    logger.warning(f"Error parsing {source}: {e}")
        
        return articles
    
    def _analyze_articles(self, articles):
        """Analyse les sentiments et émotions des articles"""
        analyzed_articles = []
        
        for article in articles:
            text = f"{article['title']} {article['content']}"
            
            # Analyse de sentiment
            sentiment_score = self._analyze_sentiment(text)
            
            # Analyse des 5 émotions
            emotions = self._analyze_emotions(text)
            
            # Détection d'urgence
            urgency_detected = self._detect_urgency(text)
            
            # Extraction mots-clés
            keywords_found = self._extract_keywords(text, article.get('keywords', []))
            
            analyzed_articles.append({
                **article,
                'sentiment_score': sentiment_score,
                'sentiment_label': self._get_sentiment_label(sentiment_score),
                'emotions': emotions,
                'dominant_emotion': max(emotions.items(), key=lambda x: x[1])[0],
                'urgency_detected': urgency_detected,
                'keywords_found': keywords_found,
                'region': self._extract_region(text)
            })
        
        return analyzed_articles
    
    def _analyze_sentiment(self, text):
        """Analyse le sentiment du texte (-1 à 1)"""
        # Algorithme de sentiment simplifié
        positive_words = ['peace', 'agreement', 'cooperation', 'progress', 'success', 'hope']
        negative_words = ['war', 'conflict', 'crisis', 'violence', 'attack', 'tension']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        total = positive_count + negative_count
        if total == 0:
            return 0
        
        return (positive_count - negative_count) / total
    
    def _analyze_emotions(self, text):
        """Analyse les 5 émotions principales"""
        text_lower = text.lower()
        
        emotion_keywords = {
            'peur': ['crisis', 'danger', 'attack', 'threat', 'emergency', 'risk', 'conflict'],
            'colère': ['anger', 'frustration', 'protest', 'violence', 'hostility', 'sanctions'],
            'tristesse': ['tragedy', 'victims', 'death', 'destruction', 'suffering', 'loss'],
            'joie': ['peace', 'agreement', 'cooperation', 'success', 'progress', 'hope'],
            'neutralité': ['report', 'analysis', 'statement', 'meeting', 'negotiations']
        }
        
        emotions = {}
        for emotion, keywords in emotion_keywords.items():
            count = sum(1 for keyword in keywords if keyword in text_lower)
            emotions[emotion] = min(1.0, count / len(keywords) * 2)
        
        return emotions
    
    def _detect_urgency(self, text):
        """Détecte l'urgence dans le texte"""
        urgency_indicators = ['urgent', 'crisis', 'immediate', 'critical', 'alert', 'breaking']
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in urgency_indicators)
    
    def _extract_keywords(self, text, keywords):
        """Extrait les mots-clés trouvés"""
        text_lower = text.lower()
        return [kw for kw in keywords if kw.lower() in text_lower]
    
    def _extract_region(self, text):
        """Extrait la région mentionnée"""
        regions = {
            'Europe': ['europe', 'eu', 'nato', 'brussels', 'berlin', 'paris'],
            'Asia': ['asia', 'china', 'japan', 'india', 'korea', 'taiwan'],
            'Middle East': ['middle east', 'israel', 'palestine', 'iran', 'saudi', 'syria'],
            'Africa': ['africa', 'nigeria', 'kenya', 'egypt', 'south africa'],
            'Americas': ['usa', 'us', 'america', 'canada', 'brazil', 'mexico']
        }
        
        text_lower = text.lower()
        for region, keywords in regions.items():
            if any(keyword in text_lower for keyword in keywords):
                return region
        
        return 'Global'
    
    def _get_sentiment_label(self, score):
        """Convertit le score en label de sentiment"""
        if score > 0.3:
            return "Positif"
        elif score > 0.1:
            return "Légèrement positif"
        elif score < -0.3:
            return "Négatif"
        elif score < -0.1:
            return "Légèrement négatif"
        else:
            return "Neutre"
    
    def _detect_trends(self, analyzed_articles):
        """Détecte les tendances médiatiques"""
        if not analyzed_articles:
            return []
        
        emotion_counts = Counter([a['dominant_emotion'] for a in analyzed_articles])
        region_counts = Counter([a['region'] for a in analyzed_articles])
        
        trends = []
        
        # Tendance émotionnelle
        dominant_emotion, count = emotion_counts.most_common(1)[0]
        if count > len(analyzed_articles) * 0.3:  # 30% des articles
            trends.append(f"Dominance de {dominant_emotion}")
        
        # Tendance géographique
        dominant_region, region_count = region_counts.most_common(1)[0]
        if region_count > len(analyzed_articles) * 0.4:  # 40% des articles
            trends.append(f"Focus sur {dominant_region}")
        
        return trends
    
    def _calculate_average_sentiment(self, analyzed_articles):
        """Calcule le sentiment moyen"""
        if not analyzed_articles:
            return 0
        return sum([a['sentiment_score'] for a in analyzed_articles]) / len(analyzed_articles)
    
    def _get_predominant_emotion(self, analyzed_articles):
        """Trouve l'émotion prédominante"""
        if not analyzed_articles:
            return "Neutre"
        
        emotion_counts = Counter([a['dominant_emotion'] for a in analyzed_articles])
        return emotion_counts.most_common(1)[0][0]
    
    def _matches_keywords(self, entry, keywords):
        """Vérifie si l'article correspond aux mots-clés"""
        text = f"{entry.title} {entry.get('summary', '')}".lower()
        return any(keyword.lower() in text for keyword in keywords)
    
    def _parse_date(self, entry):
        """Parse la date de l'article"""
        try:
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                return datetime(*entry.published_parsed[:6]).isoformat()
        except:
            pass
        return datetime.now().isoformat()
    
    def _extract_content(self, entry):
        """Extrait le contenu complet de l'article"""
        try:
            if hasattr(entry, 'link'):
                response = requests.get(entry.link, timeout=10)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extraire le texte des paragraphes
                paragraphs = soup.find_all('p')
                content = ' '.join([p.get_text() for p in paragraphs[:5]])
                return content[:1000]  # Limiter la taille
        except:
            pass
        
        return entry.get('summary', '')[:500]
    
    def _get_timestamp(self):
        """Retourne timestamp ISO"""
        return datetime.now().isoformat()
    
    def get_info(self):
        """Informations du plugin"""
        return {
            'name': self.name,
            'capabilities': ['analyse_sentiments', 'detection_emotions', 'veille_mediatique'],
            'required_keys': []  # Aucune clé requise
        }