# Flask/hackernews_source.py
"""
Hacker News API Source - Discussions tech/policy de qualité
API publique JSON - Pas d'authentification
"""

import requests
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class HackerNewsSource:
    """
    Source Hacker News via API publique Firebase
    https://github.com/HackerNews/API
    """

    BASE_URL = "https://hacker-news.firebaseio.com/v0"

    # Mots-clés géopolitiques pour filtrage
    GEOPOLITICS_KEYWORDS = [
        'geopolit', 'diplomacy', 'foreign policy', 'international',
        'war', 'conflict', 'china', 'russia', 'ukraine', 'taiwan',
        'middle east', 'nato', 'sanctions', 'trade war', 'strategic',
        'military', 'defense', 'security', 'intelligence', 'cyber war'
    ]

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Geopol-Analytics-HN/1.0'
        })

    def fetch(self, query: Optional[str] = None, limit: int = 30,
              story_type: str = 'top') -> List[Dict[str, Any]]:
        """
        Récupère stories depuis Hacker News

        Args:
            query: Mot-clé de filtrage (optionnel)
            limit: Nombre maximum de stories
            story_type: Type de stories ('top', 'best', 'new')

        Returns:
            Liste de posts
        """
        logger.info(f"📰 Récupération Hacker News ({story_type}, limit={limit})")

        try:
            # Récupérer IDs des stories
            story_ids = self._get_story_ids(story_type)

            posts = []
            fetched = 0

            for story_id in story_ids:
                if fetched >= limit * 3:  # Fetch plus pour compenser le filtrage
                    break

                try:
                    story = self._get_story(story_id)

                    if not story:
                        continue

                    # Filtrer par query ou géopolitique
                    if not self._is_relevant(story, query):
                        continue

                    post = self._convert_to_post(story)
                    posts.append(post)
                    fetched += 1

                except Exception as e:
                    logger.debug(f"Erreur récupération story {story_id}: {e}")
                    continue

            logger.info(f"[OK] Hacker News: {len(posts)} stories récupérées")
            return posts[:limit]

        except Exception as e:
            logger.error(f"[ERROR] Erreur Hacker News: {e}")
            return []

    def _get_story_ids(self, story_type: str) -> List[int]:
        """
        Récupère les IDs des stories

        Args:
            story_type: Type de stories

        Returns:
            Liste d'IDs
        """
        endpoints = {
            'top': f"{self.BASE_URL}/topstories.json",
            'best': f"{self.BASE_URL}/beststories.json",
            'new': f"{self.BASE_URL}/newstories.json"
        }

        url = endpoints.get(story_type, endpoints['top'])

        response = self.session.get(url, timeout=10)
        response.raise_for_status()

        return response.json()

    def _get_story(self, story_id: int) -> Optional[Dict[str, Any]]:
        """
        Récupère les détails d'une story

        Args:
            story_id: ID de la story

        Returns:
            Données de la story
        """
        url = f"{self.BASE_URL}/item/{story_id}.json"

        response = self.session.get(url, timeout=10)
        response.raise_for_status()

        story = response.json()

        # Filtrer les stories nulles ou non-story
        if not story or story.get('type') != 'story':
            return None

        return story

    def _is_relevant(self, story: Dict, query: Optional[str]) -> bool:
        """
        Vérifie si une story est pertinente

        Args:
            story: Données de la story
            query: Requête de recherche (optionnel)

        Returns:
            True si pertinent
        """
        title = story.get('title', '').lower()
        text = story.get('text', '').lower()
        url = story.get('url', '').lower()

        searchable = f"{title} {text} {url}"

        # Si query fournie, filtrer dessus
        if query:
            return query.lower() in searchable

        # Sinon, filtrer sur mots-clés géopolitiques
        return any(keyword in searchable for keyword in self.GEOPOLITICS_KEYWORDS)

    def _convert_to_post(self, story: Dict) -> Dict[str, Any]:
        """
        Convertit une story HN en format post standard

        Args:
            story: Story Hacker News

        Returns:
            Post formaté
        """
        story_id = story.get('id')
        title = story.get('title', 'No title')
        url = story.get('url', f"https://news.ycombinator.com/item?id={story_id}")
        text = story.get('text', '')

        # Nettoyer HTML si présent
        if '<' in text:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(text, 'html.parser')
            text = soup.get_text(strip=True)

        score = story.get('score', 0)
        descendants = story.get('descendants', 0)  # Nombre de comments
        author = story.get('by', 'unknown')
        timestamp = story.get('time', 0)

        pub_date = datetime.fromtimestamp(timestamp) if timestamp else datetime.now()

        return {
            'id': f"hn_{story_id}",
            'title': title,
            'content': text or title,  # Utiliser title si pas de texte
            'link': url,
            'pub_date': pub_date,
            'source': 'Hacker News',
            'source_type': 'hackernews',
            'author': author,
            'engagement': {
                'score': score,
                'comments': descendants,
                'upvotes': score  # Score HN = upvotes
            }
        }

    def get_comments(self, story_id: int, max_depth: int = 1) -> List[Dict[str, Any]]:
        """
        Récupère les commentaires d'une story

        Args:
            story_id: ID de la story
            max_depth: Profondeur maximale de récursion

        Returns:
            Liste de commentaires
        """
        story = self._get_story(story_id)

        if not story:
            return []

        kid_ids = story.get('kids', [])
        comments = []

        for kid_id in kid_ids[:50]:  # Limiter à 50 top comments
            try:
                comment = self._get_comment(kid_id, depth=0, max_depth=max_depth)
                if comment:
                    comments.append(comment)
            except:
                continue

        return comments

    def _get_comment(self, comment_id: int, depth: int, max_depth: int) -> Optional[Dict[str, Any]]:
        """
        Récupère un commentaire (récursif si max_depth > 0)

        Args:
            comment_id: ID du commentaire
            depth: Profondeur actuelle
            max_depth: Profondeur maximale

        Returns:
            Commentaire formaté
        """
        if depth > max_depth:
            return None

        url = f"{self.BASE_URL}/item/{comment_id}.json"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            comment_data = response.json()

            if not comment_data or comment_data.get('deleted') or comment_data.get('dead'):
                return None

            text = comment_data.get('text', '')

            # Nettoyer HTML
            if '<' in text:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(text, 'html.parser')
                text = soup.get_text(strip=True)

            comment = {
                'id': comment_id,
                'author': comment_data.get('by', 'unknown'),
                'text': text,
                'time': datetime.fromtimestamp(comment_data.get('time', 0)),
                'replies': []
            }

            # Récupérer replies si depth < max_depth
            if depth < max_depth and comment_data.get('kids'):
                for kid_id in comment_data['kids'][:10]:  # Max 10 replies
                    try:
                        reply = self._get_comment(kid_id, depth + 1, max_depth)
                        if reply:
                            comment['replies'].append(reply)
                    except:
                        continue

            return comment

        except:
            return None


# Export
__all__ = ['HackerNewsSource']
