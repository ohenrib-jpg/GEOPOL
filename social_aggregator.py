# Flask/social_aggregator.py
"""
Module d'agrégation de flux de réseaux sociaux
Version améliorée avec gestion robuste des instances Nitter
"""

import requests
import logging
import re
import json
import random
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from Flask.database import DatabaseManager
from Flask.sentiment_analyzer import SentimentAnalyzer

# Configuration des instances Nitter
NITTER_INSTANCES = [
    'https://nitter.net',
    'https://nitter.it', 
    'https://nitter.privacydev.net',
    'https://nitter.poast.org',
    'https://nitter.tiekoetter.com',
    'https://nitter.fdn.fr',
    'https://nitter.nixnet.services',
    'https://nitter.1d4.us',
    'https://nitter.kavin.rocks',
    'https://nitter.unixfox.eu'
]

SCRAPING_CONFIG = {
    'timeout': 15,
    'max_retries': 3,
    'retry_delay': 2,
    'rate_limit_delay': 1,
    'user_agents': [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    ]
}

logger = logging.getLogger(__name__)

class SocialAggregator:
    """
    Agrégateur de flux de réseaux sociaux avec gestion robuste des instances Nitter
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.sentiment_analyzer = SentimentAnalyzer()
        
        # Gestion avancée des instances
        self.nitter_instances = NITTER_INSTANCES.copy()
        self.instance_stats = {instance: {'success': 0, 'errors': 0, 'last_used': None} for instance in self.nitter_instances}
        self.blacklisted_instances = set()
        
        # Configuration
        self.scraping_config = SCRAPING_CONFIG
        
        # Sources par défaut
        self.default_sources = [
            {
                'id': 'nitter_emotions',
                'name': 'Nitter - Émotions',
                'type': 'nitter',
                'enabled': True,
                'config': {
                    'query': 'anger OR sadness OR happiness OR fear OR joy OR "social media" OR "public opinion" -filter:replies',
                    'limit': 30,
                    'include_rts': False,
                    'include_replies': False
                }
            },
            {
                'id': 'nitter_geopolitics',
                'name': 'Nitter - Géopolitique',
                'type': 'nitter',
                'enabled': True,
                'config': {
                    'query': 'geopolitics OR diplomacy OR "world news" OR international OR "foreign policy" OR war OR conflict -filter:replies',
                    'limit': 30,
                    'include_rts': False,
                    'include_replies': False
                }
            },
            {
                'id': 'reddit_worldnews',
                'name': 'Reddit - WorldNews',
                'type': 'reddit',
                'enabled': True,
                'config': {
                    'url': 'https://www.reddit.com/r/worldnews',
                    'limit': 50,
                    'sort': 'hot'
                }
            }
        ]
        
        # Thèmes émotionnels
        self.emotion_themes = {
            'anger': ['colère', 'rage', 'fureur', 'indignation', 'anger', 'mad', 'furious'],
            'sadness': ['tristesse', 'peine', 'détresse', 'sad', 'sorrow', 'grief', 'depression'],
            'joy': ['joie', 'bonheur', 'contentement', 'joy', 'happiness', 'celebration', 'happy'],
            'fear': ['peur', 'crainte', 'appréhension', 'fear', 'worry', 'anxiety', 'concern'],
            'surprise': ['surprise', 'étonnement', 'stupéfaction', 'surprise', 'shock', 'amazement']
        }
        
        logger.info(f"🔄 SocialAggregator initialisé avec {len(self.nitter_instances)} instances Nitter")
    
    def _get_best_instance(self) -> str:
        """Retourne la meilleure instance disponible"""
        available_instances = [inst for inst in self.nitter_instances if inst not in self.blacklisted_instances]
        
        if not available_instances:
            # Réinitialiser les blacklists si toutes sont bloquées
            self.blacklisted_instances.clear()
            available_instances = self.nitter_instances.copy()
            logger.warning("🔄 Réinitialisation de toutes les instances Nitter")
        
        # Choisir une instance aléatoire parmi les disponibles
        return random.choice(available_instances)
    
    def _test_instance_health(self, instance: str) -> bool:
        """Teste la santé d'une instance Nitter"""
        try:
            test_url = f"{instance}/search?f=tweets&q=test&limit=1"
            headers = self._get_headers()
            
            response = requests.get(test_url, headers=headers, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            logger.debug(f"❌ Instance {instance} en échec: {e}")
            return False
    
    def _get_headers(self) -> Dict[str, str]:
        """Retourne des headers réalistes avec rotation d'User-Agent"""
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        headers['User-Agent'] = random.choice(self.scraping_config['user_agents'])
        return headers
    
    def _fetch_from_nitter_robust(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Récupération robuste avec fallback sur multiple instances
        """
        max_retries = self.scraping_config['max_retries']
        posts = []
        
        for attempt in range(max_retries):
            instance = self._get_best_instance()
            logger.info(f"🔍 Tentative {attempt + 1} avec {instance}")
            
            try:
                posts = self._nitter_request(instance, source)
                
                if posts:
                    # Succès - mettre à jour les stats
                    self.instance_stats[instance]['success'] += 1
                    self.instance_stats[instance]['last_used'] = datetime.now()
                    logger.info(f"✅ Succès avec {instance}: {len(posts)} posts")
                    break
                else:
                    # Aucun post trouvé mais pas d'erreur
                    logger.warning(f"⚠️ Aucun post trouvé avec {instance}")
                    
            except Exception as e:
                # Erreur - blacklist temporairement l'instance
                self.instance_stats[instance]['errors'] += 1
                self.blacklisted_instances.add(instance)
                logger.warning(f"🚫 Instance {instance} blacklistée: {e}")
                
                if attempt < max_retries - 1:
                    # Attente progressive
                    delay = self.scraping_config['retry_delay'] * (attempt + 1)
                    logger.info(f"⏳ Attente de {delay}s avant prochaine tentative...")
                    time.sleep(delay)
                else:
                    logger.error(f"❌ Échec après {max_retries} tentatives")
        
        # Respecter la rate limit
        time.sleep(self.scraping_config['rate_limit_delay'])
        
        return posts
    
    def _nitter_request(self, instance: str, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Effectue la requête vers Nitter"""
        config = source.get('config', {})
        
        # Construction de l'URL
        url = f"{instance}/search"
        params = {
            'f': 'tweets',
            'q': config.get('query', 'geopolitics'),
            'limit': min(config.get('limit', 30), 50)  # Limiter pour éviter le blocage
        }
        
        # Paramètres optionnels
        if config.get('lang'):
            params['lang'] = config['lang']
        if config.get('since'):
            params['since'] = config['since']
        
        logger.debug(f"🌐 Requête Nitter: {url} avec params: {params}")
        
        headers = self._get_headers()
        response = requests.get(url, params=params, headers=headers, timeout=self.scraping_config['timeout'])
        response.raise_for_status()
        
        # Vérifier si on est bloqué (captcha, page d'erreur)
        if any(indicator in response.text.lower() for indicator in ['captcha', 'error', 'blocked', 'rate limit']):
            raise Exception("Instance bloquée ou avec CAPTCHA")
        
        return self._parse_nitter_html(response.text, source, instance)
    
    def _parse_nitter_html(self, html: str, source: Dict[str, Any], instance: str) -> List[Dict[str, Any]]:
        """Parse le HTML de Nitter"""
        soup = BeautifulSoup(html, 'html.parser')
        posts = []
        
        # Chercher les tweets dans différents sélecteurs possibles
        tweet_selectors = [
            '.main-tweet', '.tweet', '[data-testid="tweet"]', 
            '.timeline-item', '.main-timeline .tweet'
        ]
        
        tweets_found = False
        for selector in tweet_selectors:
            tweets = soup.select(selector)
            if tweets:
                tweets_found = True
                logger.info(f"Found {len(tweets)} tweets with selector: {selector}")
                break
        
        if not tweets_found:
            logger.warning("⚠️ No tweets found in Nitter response")
            return []
        
        for i, tweet in enumerate(tweets[:30]):  # Limite à 30 tweets
            try:
                post = self._extract_tweet_data(tweet, source, i, instance)
                if post:
                    posts.append(post)
            except Exception as e:
                logger.debug(f"Error parsing tweet {i}: {e}")
                continue
        
        return posts
    
    def _extract_tweet_data(self, tweet_element, source: Dict[str, Any], index: int, instance: str) -> Optional[Dict[str, Any]]:
        """Extrait les données d'un tweet"""
        try:
            # Titre/Contenu
            content_selectors = [
                '.tweet-content', '.tweet-text', '.main-tweet .tweet-content',
                '[data-testid="tweetText"]', '.timeline-item .tweet-content'
            ]
            
            content = ""
            for selector in content_selectors:
                element = tweet_element.select_one(selector)
                if element:
                    content = element.get_text(strip=True)
                    break
            
            if not content:
                return None
            
            # Date
            date_selectors = [
                '.tweet-date a', '.tweet-date', 'time', '.tweet-published'
            ]
            
            pub_date = datetime.now()
            for selector in date_selectors:
                element = tweet_element.select_one(selector)
                if element:
                    date_text = element.get('datetime') or element.get('title') or element.get_text(strip=True)
                    if date_text:
                        try:
                            pub_date = self._parse_date(date_text)
                            break
                        except:
                            continue
            
            # Auteur
            author_selectors = [
                '.tweet-header .username', '.tweet-header .display-name',
                '[data-testid="User-Name"]', '.tweet .username'
            ]
            
            author = "unknown"
            for selector in author_selectors:
                element = tweet_element.select_one(selector)
                if element:
                    author = element.get_text(strip=True)
                    break
            
            # URL du tweet
            link_selectors = ['.tweet-date a', 'a[href*="/status/"]']
            link = ""
            for selector in link_selectors:
                element = tweet_element.select_one(selector)
                if element:
                    href = element.get('href', '')
                    if href:
                        link = f"{instance}{href}" if not href.startswith('http') else href
                        break
            
            # Métriques d'engagement
            engagement = self._extract_engagement(tweet_element)
            
            return {
                'id': link or f"nitter_{int(pub_date.timestamp())}_{index}",
                'title': content[:100] + '...' if len(content) > 100 else content,
                'content': content,
                'link': link,
                'pub_date': pub_date,
                'source': source['name'],
                'source_type': 'nitter',
                'author': author,
                'engagement': engagement
            }
            
        except Exception as e:
            logger.debug(f"Error extracting tweet data: {e}")
            return None
    
    def _parse_date(self, date_text: str) -> datetime:
        """Parse différentes formats de dates"""
        if not date_text:
            return datetime.now()
        
        try:
            # Format ISO
            if 'T' in date_text or 'Z' in date_text:
                return datetime.fromisoformat(date_text.replace('Z', '+00:00'))
            
            # Format Twitter standard
            if '+' in date_text:
                return datetime.strptime(date_text, '%a %b %d %H:%M:%S %z %Y')
            
            # Format relatif (ex: "2 hours ago")
            if 'hour' in date_text.lower():
                hours = int(re.search(r'\d+', date_text).group())
                return datetime.now() - timedelta(hours=hours)
            elif 'minute' in date_text.lower():
                minutes = int(re.search(r'\d+', date_text).group())
                return datetime.now() - timedelta(minutes=minutes)
            elif 'day' in date_text.lower():
                days = int(re.search(r'\d+', date_text).group())
                return datetime.now() - timedelta(days=days)
            
            return datetime.now()
            
        except Exception:
            return datetime.now()
    
    def _extract_engagement(self, tweet_element) -> Dict[str, Any]:
        """Extrait les métriques d'engagement"""
        engagement = {'likes': 0, 'retweets': 0, 'comments': 0}
        
        # Compter les icônes/emojis
        tweet_text = tweet_element.get_text()
        engagement['likes'] = len(re.findall(r'❤️|👍|like', tweet_text, re.IGNORECASE))
        engagement['retweets'] = len(re.findall(r'🔁|↻|RT', tweet_text, re.IGNORECASE))
        engagement['comments'] = len(re.findall(r'💬|comment', tweet_text, re.IGNORECASE))
        
        return engagement
    
    def _fetch_from_reddit(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Récupère des données depuis Reddit
        """
        try:
            config = source.get('config', {})
            url = config.get('url', 'https://www.reddit.com/r/worldnews')
            limit = config.get('limit', 50)
            sort = config.get('sort', 'hot')
            
            reddit_url = f"{url}/{sort}.json?limit={limit}"
            headers = {
                'User-Agent': 'GEOPOLIS/1.0 (+https://github.com/geopolis)'
            }
            
            response = requests.get(reddit_url, headers=headers, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            posts = []
            
            for child in data.get('data', {}).get('children', []):
                post_data = child.get('data', {})
                
                post = {
                    'id': f"reddit_{post_data.get('id', '')}",
                    'title': post_data.get('title', ''),
                    'content': post_data.get('selftext', post_data.get('title', '')),
                    'link': f"https://www.reddit.com{post_data.get('permalink', '')}",
                    'pub_date': datetime.fromtimestamp(post_data.get('created_utc', 0)),
                    'source': source['name'],
                    'source_type': 'reddit',
                    'author': post_data.get('author', 'unknown'),
                    'engagement': {
                        'upvotes': post_data.get('ups', 0),
                        'comments': post_data.get('num_comments', 0),
                        'ratio': post_data.get('upvote_ratio', 0)
                    }
                }
                posts.append(post)
            
            logger.info(f"✅ Reddit fetch success: {len(posts)} posts")
            return posts
            
        except Exception as e:
            logger.error(f"❌ Reddit fetch error: {e}")
            return []
    
    def get_top_emotion_themes(self, days: int = 1) -> List[Dict[str, Any]]:
        """
        Identifie les 5 thèmes émotionnels les plus discussés
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Récupérer tous les posts récents
        all_posts = self.fetch_recent_posts(cutoff_date)
        
        if not all_posts:
            return []
        
        # Analyser les émotions
        emotion_scores = {}
        
        for emotion, keywords in self.emotion_themes.items():
            score = 0
            matched_posts = 0
            
            for post in all_posts:
                text = f"{post['title']} {post['content']}".lower()
                
                # Compter les correspondances
                for keyword in keywords:
                    score += text.count(keyword.lower())
                
                if any(keyword.lower() in text for keyword in keywords):
                    matched_posts += 1
            
            # Score pondéré par le nombre de posts et l'engagement
            total_engagement = sum(
                post['engagement'].get('likes', 0) + 
                post['engagement'].get('retweets', 0) + 
                post['engagement'].get('comments', 0)
                for post in all_posts
                if any(keyword.lower() in f"{post['title']} {post['content']}".lower() 
                       for keyword in keywords)
            )
            
            emotion_scores[emotion] = {
                'score': score,
                'posts_count': matched_posts,
                'total_engagement': total_engagement,
                'final_score': score * (1 + total_engagement / 100)  # Pondération par engagement
            }
        
        # Trier par score final et prendre les 5 premiers
        top_themes = sorted(
            emotion_scores.items(),
            key=lambda x: x[1]['final_score'],
            reverse=True
        )[:5]
        
        return [
            {
                'theme': theme,
                'score': data['score'],
                'posts_count': data['posts_count'],
                'total_engagement': data['total_engagement'],
                'final_score': data['final_score']
            }
            for theme, data in top_themes
        ]
    
    def fetch_recent_posts(self, cutoff_date: datetime) -> List[Dict[str, Any]]:
        """
        Récupère tous les posts récents depuis les sources activées
        """
        all_posts = []
        sources = self.default_sources
        
        for source in sources:
            if not source.get('enabled', True):
                continue
                
            logger.info(f"📡 Fetching from {source['name']} ({source['type']})")
            
            try:
                if source['type'] == 'nitter':
                    posts = self._fetch_from_nitter_robust(source)
                elif source['type'] == 'reddit':
                    posts = self._fetch_from_reddit(source)
                else:
                    logger.warning(f"Unknown source type: {source['type']}")
                    posts = []
                
                # Filtrer par date
                recent_posts = [
                    post for post in posts
                    if post['pub_date'] >= cutoff_date
                ]
                
                all_posts.extend(recent_posts)
                logger.info(f"✅ {source['name']}: {len(recent_posts)} recent posts")
                
            except Exception as e:
                logger.error(f"❌ Error fetching from {source['name']}: {e}")
        
        # Trier par date décroissante
        all_posts.sort(key=lambda x: x['pub_date'], reverse=True)
        
        logger.info(f"📊 Total recent posts: {len(all_posts)}")
        return all_posts
    
    def analyze_social_sentiment(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyse le sentiment des posts sociaux
        """
        posts_with_sentiment = []
        
        for post in posts:
            try:
                # Analyser le sentiment
                sentiment_result = self.sentiment_analyzer.analyze_sentiment(
                    f"{post['title']} {post['content']}"
                )
                
                # Enrichir le post
                enriched_post = {
                    **post,
                    'sentiment_score': sentiment_result['score'],
                    'sentiment_type': sentiment_result['type'],
                    'sentiment_confidence': sentiment_result['confidence']
                }
                
                posts_with_sentiment.append(enriched_post)
                
            except Exception as e:
                logger.debug(f"Error analyzing sentiment for post {post.get('id', 'unknown')}: {e}")
                # Ajouter le post sans analyse de sentiment
                posts_with_sentiment.append({
                    **post,
                    'sentiment_score': 0.0,
                    'sentiment_type': 'neutral',
                    'sentiment_confidence': 0.0
                })
        
        return posts_with_sentiment
    
    def save_social_posts(self, posts: List[Dict[str, Any]]) -> int:
        """
        Sauvegarde les posts sociaux dans la base de données
        """
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            # Créer la table si elle n'existe pas
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS social_posts (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    content TEXT,
                    link TEXT,
                    pub_date DATETIME,
                    source TEXT,
                    source_type TEXT,
                    author TEXT,
                    sentiment_score REAL,
                    sentiment_type TEXT,
                    sentiment_confidence REAL,
                    engagement TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            saved_count = 0
            
            for post in posts:
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO social_posts 
                        (id, title, content, link, pub_date, source, source_type, 
                         author, sentiment_score, sentiment_type, sentiment_confidence, engagement)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        post['id'],
                        post['title'],
                        post['content'],
                        post['link'],
                        post['pub_date'],
                        post['source'],
                        post['source_type'],
                        post['author'],
                        post.get('sentiment_score', 0.0),
                        post.get('sentiment_type', 'neutral'),
                        post.get('sentiment_confidence', 0.0),
                        json.dumps(post.get('engagement', {}), ensure_ascii=False)
                    ))
                    saved_count += 1
                    
                except Exception as e:
                    logger.debug(f"Error saving post {post.get('id', 'unknown')}: {e}")
                    continue
            
            conn.commit()
            logger.info(f"💾 Saved {saved_count} social posts")
            return saved_count
            
        except Exception as e:
            logger.error(f"Error saving social posts: {e}")
            conn.rollback()
            return 0
        finally:
            conn.close()
    
    def get_social_statistics(self, days: int = 7) -> Dict[str, Any]:
        """
        Récupère les statistiques des posts sociaux
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            # Statistiques générales
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_posts,
                    AVG(sentiment_score) as avg_sentiment,
                    COUNT(CASE WHEN sentiment_type = 'positive' THEN 1 END) as positive_count,
                    COUNT(CASE WHEN sentiment_type = 'negative' THEN 1 END) as negative_count,
                    COUNT(CASE WHEN sentiment_type = 'neutral' THEN 1 END) as neutral_count
                FROM social_posts
                WHERE pub_date >= ?
            """, (cutoff_date,))
            
            row = cursor.fetchone()
            total_posts = row[0] if row else 0
            
            # Distribution par source
            cursor.execute("""
                SELECT source, source_type, COUNT(*) as count
                FROM social_posts
                WHERE pub_date >= ?
                GROUP BY source, source_type
                ORDER BY count DESC
            """, (cutoff_date,))
            
            source_stats = [{'source': row[0], 'type': row[1], 'count': row[2]} for row in cursor.fetchall()]
            
            # Posts par jour
            cursor.execute("""
                SELECT DATE(pub_date) as date, COUNT(*) as count
                FROM social_posts
                WHERE pub_date >= ?
                GROUP BY DATE(pub_date)
                ORDER BY date
            """, (cutoff_date,))
            
            daily_stats = [{'date': row[0], 'count': row[1]} for row in cursor.fetchall()]
            
            return {
                'total_posts': total_posts,
                'average_sentiment': row[1] if row else 0.0,
                'sentiment_distribution': {
                    'positive': row[2] if row else 0,
                    'negative': row[3] if row else 0,
                    'neutral': row[4] if row else 0
                },
                'source_distribution': source_stats,
                'daily_stats': daily_stats,
                'period_days': days
            }
            
        except Exception as e:
            logger.error(f"Error getting social statistics: {e}")
            return {}
        finally:
            conn.close()

    # NOUVELLES MÉTHODES DE GESTION DES INSTANCES
    def get_instance_status(self) -> Dict[str, Any]:
        """Retourne le statut de toutes les instances"""
        status = {}
        for instance in self.nitter_instances:
            stats = self.instance_stats.get(instance, {'success': 0, 'errors': 0})
            status[instance] = {
                'success': stats['success'],
                'errors': stats['errors'],
                'blacklisted': instance in self.blacklisted_instances,
                'health': self._test_instance_health(instance) if instance not in self.blacklisted_instances else False,
                'last_used': stats.get('last_used')
            }
        return status
    
    def reset_blacklist(self):
        """Réinitialise la blacklist des instances"""
        self.blacklisted_instances.clear()
        logger.info("🔄 Blacklist des instances réinitialisée")
    
    def add_custom_instance(self, instance_url: str):
        """Ajoute une instance Nitter personnalisée"""
        if instance_url not in self.nitter_instances:
            self.nitter_instances.append(instance_url)
            self.instance_stats[instance_url] = {'success': 0, 'errors': 0, 'last_used': None}
            logger.info(f"➕ Instance personnalisée ajoutée: {instance_url}")
    
    def remove_instance(self, instance_url: str):
        """Supprime une instance"""
        if instance_url in self.nitter_instances:
            self.nitter_instances.remove(instance_url)
            self.instance_stats.pop(instance_url, None)
            self.blacklisted_instances.discard(instance_url)
            logger.info(f"➖ Instance supprimée: {instance_url}")

# Instance globale
_social_aggregator = None

def get_social_aggregator(db_manager: DatabaseManager) -> SocialAggregator:
    """Retourne l'instance singleton du social aggregator"""
    global _social_aggregator
    if _social_aggregator is None:
        _social_aggregator = SocialAggregator(db_manager)
    return _social_aggregator