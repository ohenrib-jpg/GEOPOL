import feedparser
import logging
from datetime import datetime
from typing import List, Dict, Any
from .database import DatabaseManager
from .sentiment_analyzer import SentimentAnalyzer
from .theme_analyzer import ThemeAnalyzer

logger = logging.getLogger(__name__)

class RSSManager:
    def __init__(self, db_manager: DatabaseManager, sentiment_analyzer=None):
        self.db_manager = db_manager
        self.sentiment_analyzer = sentiment_analyzer
        self.theme_analyzer = ThemeAnalyzer(db_manager)  # Ajout de theme_analyzer
        print(f"📡 RSSManager initialisé avec analyseur: {type(sentiment_analyzer).__name__ if sentiment_analyzer else 'Aucun'}")

    def analyze_article_sentiment(self, title: str, content: str) -> Dict[str, Any]:
        """Analyse le sentiment avec RoBERTa en priorité"""
        if self.sentiment_analyzer:
            try:
                # Utiliser RoBERTa
                result = self.sentiment_analyzer.analyze_sentiment_with_score(f"{title} {content}")
                print(f"🔮 Analyse RoBERTa: {result['type']} (score: {result['score']})")
                return result
            except Exception as e:
                print(f"⚠️ Erreur RoBERTa, fallback traditionnel: {e}")
        
        # Fallback traditionnel
        fallback_analyzer = SentimentAnalyzer()
        result = fallback_analyzer.analyze_sentiment(f"{title} {content}")
        print(f"📊 Analyse traditionnelle: {result['type']}")
        return result

    def save_article(self, article_data: Dict[str, Any], feed_url: str) -> int:
        """Sauvegarde un article avec analyse de sentiment"""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            # Analyser le sentiment
            sentiment_result = self.analyze_article_sentiment(
                article_data.get('title', ''), 
                article_data.get('content', '')
            )
            
            # Insérer l'article
            cursor.execute("""
                INSERT OR IGNORE INTO articles 
                (title, content, link, pub_date, feed_url, 
                 sentiment_score, sentiment_type, detailed_sentiment,
                 sentiment_confidence, analysis_model, roberta_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                article_data.get('title'),
                article_data.get('content'),
                article_data.get('link'),
                article_data.get('pub_date'),
                feed_url,
                sentiment_result.get('score', 0),
                sentiment_result.get('type', 'neutral'),
                sentiment_result.get('type'),  # detailed_sentiment
                sentiment_result.get('confidence', 0.5),
                sentiment_result.get('model', 'traditional'),
                sentiment_result.get('score', 0)  # roberta_score
            ))
            
            article_id = cursor.lastrowid
            conn.commit()
            
            print(f"💾 Article sauvegardé (ID: {article_id}) avec modèle: {sentiment_result.get('model')}")
            return article_id
            
        except Exception as e:
            print(f"❌ Erreur sauvegarde article: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    
    def update_feeds(self, feed_urls: List[str]) -> Dict[str, Any]:
        """Met à jour tous les flux RSS"""
        results = {
            'total_articles': 0,
            'new_articles': 0,
            'errors': []
        }
        
        for feed_url in feed_urls:
            try:
                articles = self.parse_feed(feed_url)
                results['total_articles'] += len(articles)
                
                for article in articles:
                    article_id = self.process_article(article, feed_url)  # Passer feed_url
                    if article_id > 0:
                        results['new_articles'] += 1
                        
            except Exception as e:
                error_msg = f"Erreur flux {feed_url}: {e}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
        
        return results

    def parse_feed(self, feed_url: str) -> List[Dict[str, Any]]:
        """Parse un flux RSS et retourne les articles"""
        try:
            feed = feedparser.parse(feed_url)
            articles = []
            
            for entry in feed.entries:
                article = {
                    'title': getattr(entry, 'title', ''),
                    'content': getattr(entry, 'summary', '') or getattr(entry, 'content', [{'value': ''}])[0].get('value', ''),
                    'link': getattr(entry, 'link', ''),
                    'pub_date': getattr(entry, 'published_parsed', None)
                }
                
                # Convertir la date
                if article['pub_date']:
                    try:
                        article['pub_date'] = datetime.fromtimestamp(
                            datetime(*article['pub_date'][:6]).timestamp()
                        )
                    except:
                        article['pub_date'] = datetime.now()
                else:
                    article['pub_date'] = datetime.now()
                
                articles.append(article)
            
            return articles
            
        except Exception as e:
            logger.error(f"Erreur parsing flux {feed_url}: {e}")
            return []

    def process_article(self, article_data: Dict[str, Any], feed_url: str) -> int:
        """Traite un article individuel"""
        try:
            # Ajouter feed_url aux données de l'article
            article_data['feed_url'] = feed_url
            
            # Sauvegarder l'article
            article_id = self.save_article(article_data, feed_url)
            
            if article_id:
                # Analyser les thèmes
                theme_scores = self.theme_analyzer.analyze_article(
                    article_data.get('content', ''), 
                    article_data.get('title', '')
                )
                
                # Sauvegarder l'analyse des thèmes
                if theme_scores:
                    self.theme_analyzer.save_theme_analysis(article_id, theme_scores)
                
                return article_id
            
            return 0
            
        except Exception as e:
            logger.error(f"Erreur traitement article: {e}")
            return 0
