# Flask/social_aggregator_improved.py
"""
Agrégateur social amélioré avec ciblage géographique et linguistique
Version optimisée pour analyse par pays
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
from collections import Counter
from .database import DatabaseManager
from .sentiment_analyzer import SentimentAnalyzer

logger = logging.getLogger(__name__)

# Configuration des pays surveillés
MONITORED_COUNTRIES = {
    'france': {
        'name': 'France',
        'language': 'fr',
        'keywords': ['france', 'français', 'paris', 'macron'],
        'hashtags': ['#France', '#Paris', '#Politique'],
        'exclusions': []
    },
    'usa': {
        'name': 'États-Unis',
        'language': 'en',
        'keywords': ['usa', 'america', 'us politics', 'washington'],
        'hashtags': ['#USA', '#Politics', '#America'],
        'exclusions': []
    },
    'uk': {
        'name': 'Royaume-Uni',
        'language': 'en',
        'keywords': ['uk', 'britain', 'british', 'london'],
        'hashtags': ['#UK', '#Britain', '#London'],
        'exclusions': []
    },
    'germany': {
        'name': 'Allemagne',
        'language': 'de',
        'keywords': ['deutschland', 'germany', 'berlin'],
        'hashtags': ['#Deutschland', '#Germany'],
        'exclusions': []
    },
    'china': {
        'name': 'Chine',
        'language': 'zh',
        'keywords': ['china', '中国', 'beijing'],
        'hashtags': ['#China', '#中国'],
        'exclusions': []
    },
    'russia': {
        'name': 'Russie',
        'language': 'ru',
        'keywords': ['russia', 'россия', 'moscow'],
        'hashtags': ['#Russia', '#Россия'],
        'exclusions': []
    }
}

# Thèmes émotionnels prioritaires
EMOTION_THEMES = {
    'anger': {
        'fr': ['colère', 'rage', 'furieux', 'indigné', 'révolte'],
        'en': ['anger', 'rage', 'furious', 'outrage', 'mad'],
        'de': ['wut', 'zorn', 'ärger', 'empörung'],
        'ru': ['гнев', 'ярость', 'злость'],
        'zh': ['愤怒', '生气', '暴怒']
    },
    'fear': {
        'fr': ['peur', 'crainte', 'anxiété', 'inquiétude', 'angoisse'],
        'en': ['fear', 'anxiety', 'worry', 'concern', 'scared'],
        'de': ['angst', 'furcht', 'sorge', 'bedenken'],
        'ru': ['страх', 'боязнь', 'тревога'],
        'zh': ['恐惧', '害怕', '担心']
    },
    'joy': {
        'fr': ['joie', 'bonheur', 'heureux', 'célébration'],
        'en': ['joy', 'happiness', 'happy', 'celebration', 'delight'],
        'de': ['freude', 'glück', 'fröhlich'],
        'ru': ['радость', 'счастье', 'веселье'],
        'zh': ['快乐', '高兴', '幸福']
    },
    'sadness': {
        'fr': ['tristesse', 'peine', 'chagrin', 'dépression'],
        'en': ['sadness', 'sad', 'sorrow', 'grief', 'depression'],
        'de': ['traurigkeit', 'trauer', 'kummer'],
        'ru': ['грусть', 'печаль', 'тоска'],
        'zh': ['悲伤', '难过', '忧伤']
    }
}

# Instances Nitter (réduites aux plus fiables)
NITTER_INSTANCES = [
    'https://nitter.net',
    'https://nitter.privacydev.net',
    'https://nitter.poast.org',
    'https://nitter.fdn.fr'
]

class ImprovedSocialAggregator:
    """
    Agrégateur social amélioré avec ciblage géographique
    """
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.sentiment_analyzer = SentimentAnalyzer()
        
        # Gestion des instances
        self.nitter_instances = NITTER_INSTANCES.copy()
        self.blacklisted_instances = set()
        self.instance_stats = {inst: {'success': 0, 'errors': 0} for inst in self.nitter_instances}
        
        # Cache pour éviter les doublons
        self.processed_ids = set()
        
        logger.info(f"🌍 ImprovedSocialAggregator initialisé avec {len(MONITORED_COUNTRIES)} pays surveillés")
    
    def fetch_posts_by_country(self, country_code: str, days: int = 1, limit: int = 50) -> Dict[str, Any]:
        """
        Récupère les posts pour un pays spécifique
        
        Args:
            country_code: Code du pays (ex: 'france', 'usa')
            days: Nombre de jours à analyser
            limit: Limite de posts par pays
        
        Returns:
            Dictionnaire avec posts et statistiques
        """
        if country_code not in MONITORED_COUNTRIES:
            logger.error(f"❌ Pays non surveillé: {country_code}")
            return {'success': False, 'error': 'Pays non surveillé'}
        
        country_config = MONITORED_COUNTRIES[country_code]
        logger.info(f"🌍 Récupération posts pour {country_config['name']}")
        
        # Construire la requête optimisée
        posts = self._fetch_targeted_posts(country_config, days, limit)
        
        if not posts:
            return {
                'success': True,
                'country': country_config['name'],
                'posts': [],
                'count': 0
            }
        
        # Analyser les émotions et sentiments
        analyzed_posts = self._analyze_posts_emotions(posts, country_config)
        
        # Calculer les statistiques
        stats = self._calculate_country_stats(analyzed_posts, country_config)
        
        # Sauvegarder en base
        saved_count = self._save_country_posts(analyzed_posts, country_code)
        
        return {
            'success': True,
            'country': country_config['name'],
            'country_code': country_code,
            'posts': analyzed_posts[:20],  # Retourner seulement les 20 premiers
            'count': len(analyzed_posts),
            'saved_count': saved_count,
            'statistics': stats
        }
    
    def _fetch_targeted_posts(self, country_config: Dict, days: int, limit: int) -> List[Dict[str, Any]]:
        """
        Récupération ciblée avec requêtes optimisées par pays
        """
        posts = []
        instance = self._get_best_instance()
        
        if not instance:
            logger.error("❌ Aucune instance Nitter disponible")
            return []
        
        # Construire la requête Nitter optimisée
        query_parts = []
        
        # Ajouter les mots-clés principaux
        keywords = country_config['keywords'][:3]  # Limiter à 3 mots-clés max
        query_parts.append(f"({' OR '.join(keywords)})")
        
        # Ajouter la langue
        lang_filter = f"lang:{country_config['language']}"
        
        # Ajouter filtre temporel
        since_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        # Construire l'URL
        query = ' '.join(query_parts)
        url = f"{instance}/search"
        
        params = {
            'f': 'tweets',
            'q': f"{query} {lang_filter} since:{since_date} -filter:replies",
            'limit': min(limit, 50)  # Limiter pour éviter le blocage
        }
        
        logger.info(f"🔍 Requête: {query} (langue: {country_config['language']})")
        
        try:
            headers = self._get_headers()
            response = requests.get(url, params=params, headers=headers, timeout=15)
            response.raise_for_status()
            
            # Vérifier si bloqué
            if any(indicator in response.text.lower() for indicator in ['captcha', 'error', 'blocked']):
                logger.warning(f"⚠️ Instance {instance} potentiellement bloquée")
                self.blacklisted_instances.add(instance)
                return []
            
            posts = self._parse_nitter_response(response.text, country_config)
            
            # Mettre à jour les stats
            self.instance_stats[instance]['success'] += 1
            logger.info(f"✅ {len(posts)} posts récupérés pour {country_config['name']}")
            
            # Rate limiting
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération posts {country_config['name']}: {e}")
            self.instance_stats[instance]['errors'] += 1
            self.blacklisted_instances.add(instance)
        
        return posts
    
    def _parse_nitter_response(self, html: str, country_config: Dict) -> List[Dict[str, Any]]:
        """
        Parse les résultats Nitter avec filtrage intelligent
        """
        soup = BeautifulSoup(html, 'html.parser')
        posts = []
        
        # Sélecteurs possibles
        tweet_selectors = ['.main-tweet', '.tweet', '.timeline-item']
        
        tweets = []
        for selector in tweet_selectors:
            tweets = soup.select(selector)
            if tweets:
                break
        
        if not tweets:
            logger.warning("⚠️ Aucun tweet trouvé dans la réponse")
            return []
        
        for tweet_elem in tweets[:50]:  # Limiter à 50 max
            try:
                post = self._extract_post_data(tweet_elem, country_config)
                
                if post and self._is_relevant_post(post, country_config):
                    # Vérifier que ce n'est pas un doublon
                    post_id = post.get('id', '')
                    if post_id not in self.processed_ids:
                        posts.append(post)
                        self.processed_ids.add(post_id)
                        
            except Exception as e:
                logger.debug(f"Erreur extraction post: {e}")
                continue
        
        return posts
    
    def _extract_post_data(self, tweet_elem, country_config: Dict) -> Optional[Dict[str, Any]]:
        """
        Extrait les données d'un post avec métadonnées enrichies
        """
        try:
            # Contenu
            content_selectors = ['.tweet-content', '.tweet-text', '[data-testid="tweetText"]']
            content = ""
            for selector in content_selectors:
                elem = tweet_elem.select_one(selector)
                if elem:
                    content = elem.get_text(strip=True)
                    break
            
            if not content or len(content) < 10:
                return None
            
            # Date
            pub_date = datetime.now()
            date_elem = tweet_elem.select_one('.tweet-date a, time')
            if date_elem:
                date_text = date_elem.get('datetime') or date_elem.get('title')
                if date_text:
                    pub_date = self._parse_date(date_text)
            
            # Auteur
            author = "unknown"
            author_elem = tweet_elem.select_one('.username, .display-name')
            if author_elem:
                author = author_elem.get_text(strip=True)
            
            # URL
            link = ""
            link_elem = tweet_elem.select_one('a[href*="/status/"]')
            if link_elem:
                link = link_elem.get('href', '')
            
            # Engagement (métrique importante pour le tri)
            engagement = self._extract_engagement_metrics(tweet_elem)
            
            return {
                'id': f"{country_config['language']}_{hash(content)}_{int(pub_date.timestamp())}",
                'title': content[:100] + '...' if len(content) > 100 else content,
                'content': content,
                'link': link,
                'pub_date': pub_date,
                'author': author,
                'country': country_config['name'],
                'language': country_config['language'],
                'engagement': engagement,
                'relevance_score': 0  # Sera calculé après
            }
            
        except Exception as e:
            logger.debug(f"Erreur extraction: {e}")
            return None
    
    def _extract_engagement_metrics(self, tweet_elem) -> Dict[str, int]:
        """
        Extrait les métriques d'engagement (approximatives)
        """
        engagement = {
            'likes': 0,
            'retweets': 0,
            'comments': 0,
            'total_score': 0
        }
        
        # Chercher les statistiques dans le HTML
        stats_elem = tweet_elem.select('.tweet-stats span, .icon-container')
        
        for stat in stats_elem:
            text = stat.get_text(strip=True)
            numbers = re.findall(r'\d+', text)
            if numbers:
                value = int(numbers[0])
                
                # Identifier le type de métrique
                if 'comment' in text.lower() or '💬' in text:
                    engagement['comments'] = value
                elif 'retweet' in text.lower() or '🔁' in text:
                    engagement['retweets'] = value
                elif 'like' in text.lower() or '❤️' in text:
                    engagement['likes'] = value
        
        # Calculer un score total pondéré
        engagement['total_score'] = (
            engagement['likes'] * 1 +
            engagement['retweets'] * 3 +  # Les retweets comptent plus
            engagement['comments'] * 2
        )
        
        return engagement
    
    def _is_relevant_post(self, post: Dict, country_config: Dict) -> bool:
        """
        Filtre de pertinence du post
        """
        content_lower = post['content'].lower()
        
        # Vérifier présence de mots-clés du pays
        has_keyword = any(kw.lower() in content_lower for kw in country_config['keywords'])
        
        # Vérifier présence de hashtags pertinents (optionnel)
        has_hashtag = any(ht.lower() in content_lower for ht in country_config['hashtags'])
        
        # Vérifier exclusions
        has_exclusion = any(ex.lower() in content_lower for ex in country_config.get('exclusions', []))
        
        # Post pertinent si: (keyword OU hashtag) ET PAS d'exclusion
        is_relevant = (has_keyword or has_hashtag) and not has_exclusion
        
        # Bonus: vérifier si c'est un post à fort engagement
        has_engagement = post['engagement']['total_score'] > 10
        
        return is_relevant or has_engagement
    
    def _analyze_posts_emotions(self, posts: List[Dict], country_config: Dict) -> List[Dict]:
        """
        Analyse les émotions et sentiments des posts
        """
        language = country_config['language']
        analyzed_posts = []
        
        for post in posts:
            try:
                # Analyse de sentiment (RoBERTa)
                sentiment_result = self.sentiment_analyzer.analyze_sentiment(post['content'])
                
                # Détection d'émotions
                detected_emotions = self._detect_emotions(post['content'], language)
                
                # Calcul du score de pertinence final
                relevance_score = self._calculate_relevance_score(
                    post, 
                    detected_emotions, 
                    sentiment_result
                )
                
                analyzed_post = {
                    **post,
                    'sentiment_score': sentiment_result['score'],
                    'sentiment_type': sentiment_result['type'],
                    'sentiment_confidence': sentiment_result['confidence'],
                    'emotions': detected_emotions,
                    'relevance_score': relevance_score
                }
                
                analyzed_posts.append(analyzed_post)
                
            except Exception as e:
                logger.debug(f"Erreur analyse post: {e}")
                analyzed_posts.append({
                    **post,
                    'sentiment_score': 0.0,
                    'sentiment_type': 'neutral',
                    'emotions': {},
                    'relevance_score': 0
                })
        
        # Trier par score de pertinence décroissant
        analyzed_posts.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return analyzed_posts
    
    def _detect_emotions(self, text: str, language: str) -> Dict[str, int]:
        """
        Détecte les émotions présentes dans le texte
        """
        text_lower = text.lower()
        emotions_detected = {}
        
        for emotion, translations in EMOTION_THEMES.items():
            if language not in translations:
                continue
            
            keywords = translations[language]
            count = sum(text_lower.count(kw.lower()) for kw in keywords)
            
            if count > 0:
                emotions_detected[emotion] = count
        
        return emotions_detected
    
    def _calculate_relevance_score(self, post: Dict, emotions: Dict, sentiment: Dict) -> float:
        """
        Calcule un score de pertinence composite
        """
        score = 0.0
        
        # Score d'engagement (normalisé)
        engagement_score = min(post['engagement']['total_score'] / 100, 10)
        score += engagement_score * 3  # Poids x3
        
        # Score émotionnel
        emotion_score = sum(emotions.values()) * 2
        score += emotion_score
        
        # Score de sentiment (intensité)
        sentiment_intensity = abs(sentiment['score'])
        score += sentiment_intensity * 5
        
        # Bonus pour sentiment fort
        if sentiment_intensity > 0.5:
            score += 5
        
        # Bonus pour émotions multiples
        if len(emotions) > 1:
            score += 3
        
        return round(score, 2)
    
    def _calculate_country_stats(self, posts: List[Dict], country_config: Dict) -> Dict[str, Any]:
        """
        Calcule les statistiques pour un pays
        """
        if not posts:
            return {}
        
        # Distribution des sentiments
        sentiments = [p['sentiment_type'] for p in posts]
        sentiment_counts = Counter(sentiments)
        
        # Émotions dominantes
        all_emotions = []
        for post in posts:
            all_emotions.extend(post.get('emotions', {}).keys())
        emotion_counts = Counter(all_emotions)
        
        # Score moyen de sentiment
        avg_sentiment = sum(p['sentiment_score'] for p in posts) / len(posts)
        
        # Top posts (par engagement)
        top_posts = sorted(posts, key=lambda x: x['engagement']['total_score'], reverse=True)[:5]
        
        return {
            'total_posts': len(posts),
            'sentiment_distribution': {
                'positive': sentiment_counts.get('positive', 0),
                'negative': sentiment_counts.get('negative', 0),
                'neutral_positive': sentiment_counts.get('neutral_positive', 0),
                'neutral_negative': sentiment_counts.get('neutral_negative', 0)
            },
            'average_sentiment': round(avg_sentiment, 3),
            'dominant_emotions': dict(emotion_counts.most_common(5)),
            'top_posts': [
                {
                    'content': p['title'],
                    'engagement': p['engagement']['total_score'],
                    'sentiment': p['sentiment_type']
                }
                for p in top_posts
            ],
            'engagement_stats': {
                'total_likes': sum(p['engagement']['likes'] for p in posts),
                'total_retweets': sum(p['engagement']['retweets'] for p in posts),
                'total_comments': sum(p['engagement']['comments'] for p in posts)
            }
        }
    
    def _save_country_posts(self, posts: List[Dict], country_code: str) -> int:
        """
        Sauvegarde les posts avec métadonnées pays
        """
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS social_posts_by_country (
                    id TEXT PRIMARY KEY,
                    country_code TEXT,
                    country_name TEXT,
                    language TEXT,
                    title TEXT,
                    content TEXT,
                    link TEXT,
                    pub_date DATETIME,
                    author TEXT,
                    sentiment_score REAL,
                    sentiment_type TEXT,
                    sentiment_confidence REAL,
                    emotions TEXT,
                    engagement TEXT,
                    relevance_score REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            saved_count = 0
            
            for post in posts:
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO social_posts_by_country
                        (id, country_code, country_name, language, title, content, link,
                         pub_date, author, sentiment_score, sentiment_type, sentiment_confidence,
                         emotions, engagement, relevance_score)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        post['id'],
                        country_code,
                        post['country'],
                        post['language'],
                        post['title'],
                        post['content'],
                        post['link'],
                        post['pub_date'],
                        post['author'],
                        post['sentiment_score'],
                        post['sentiment_type'],
                        post['sentiment_confidence'],
                        json.dumps(post.get('emotions', {})),
                        json.dumps(post['engagement']),
                        post['relevance_score']
                    ))
                    saved_count += 1
                except Exception as e:
                    logger.debug(f"Erreur sauvegarde post: {e}")
            
            conn.commit()
            logger.info(f"💾 {saved_count} posts sauvegardés pour {country_code}")
            return saved_count
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde: {e}")
            conn.rollback()
            return 0
        finally:
            conn.close()
    
    def fetch_all_countries(self, days: int = 1, limit_per_country: int = 30) -> Dict[str, Any]:
        """
        Récupère les posts pour tous les pays surveillés
        """
        results = {}
        total_posts = 0
        
        for country_code in MONITORED_COUNTRIES.keys():
            logger.info(f"🌍 Traitement de {country_code}...")
            
            result = self.fetch_posts_by_country(country_code, days, limit_per_country)
            
            if result['success']:
                results[country_code] = result
                total_posts += result['count']
            
            # Pause entre pays pour éviter le rate limiting
            time.sleep(3)
        
        logger.info(f"✅ Récupération terminée: {total_posts} posts pour {len(results)} pays")
        
        return {
            'success': True,
            'countries': results,
            'total_posts': total_posts,
            'countries_analyzed': len(results)
        }
    
    def get_country_comparison(self, days: int = 7) -> Dict[str, Any]:
        """
        Compare les tendances émotionnelles entre pays
        """
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        cutoff_date = datetime.now() - timedelta(days=days)
        
        cursor.execute("""
            SELECT 
                country_code,
                country_name,
                AVG(sentiment_score) as avg_sentiment,
                COUNT(*) as post_count,
                AVG(relevance_score) as avg_relevance
            FROM social_posts_by_country
            WHERE pub_date >= ?
            GROUP BY country_code, country_name
            ORDER BY avg_sentiment DESC
        """, (cutoff_date,))
        
        countries_data = []
        for row in cursor.fetchall():
            countries_data.append({
                'country_code': row[0],
                'country': row[1],
                'avg_sentiment': round(row[2], 3),
                'post_count': row[3],
                'avg_relevance': round(row[4], 2)
            })
        
        conn.close()
        
        return {
            'success': True,
            'countries': countries_data,
            'period_days': days
        }
    
    # Méthodes utilitaires
    def _get_best_instance(self) -> Optional[str]:
        """Retourne la meilleure instance disponible"""
        available = [inst for inst in self.nitter_instances if inst not in self.blacklisted_instances]
        
        if not available:
            self.blacklisted_instances.clear()
            available = self.nitter_instances.copy()
            logger.warning("🔄 Reset blacklist instances")
        
        return random.choice(available) if available else None
    
    def _get_headers(self) -> Dict[str, str]:
        """Headers HTTP réalistes"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        ]
        
        return {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive'
        }
    
    def _parse_date(self, date_text: str) -> datetime:
        """Parse différents formats de dates"""
        try:
            if 'T' in date_text or 'Z' in date_text:
                return datetime.fromisoformat(date_text.replace('Z', '+00:00'))
            return datetime.now()
        except:
            return datetime.now()

# Instance globale
_improved_aggregator = None

def get_improved_aggregator(db_manager: DatabaseManager) -> ImprovedSocialAggregator:
    """Retourne l'instance singleton"""
    global _improved_aggregator
    if _improved_aggregator is None:
        _improved_aggregator = ImprovedSocialAggregator(db_manager)
    return _improved_aggregator