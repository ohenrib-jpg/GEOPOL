"""
Client optimisé pour Archive.org avec filtrage presse
"""

import requests
import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class ArchiveOrgClient:
    """Client spécialisé pour Archive.org avec focus sur la presse"""
    
    BASE_URL = "https://archive.org/advancedsearch.php"
    METADATA_URL = "https://archive.org/metadata"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GEOPOL-Archiviste/3.0 (Educational Research)',
            'Accept': 'application/json'
        })
        
        # Rate limiting
        self.last_request = 0
        self.min_interval = 2.0  # 2 secondes minimum
        
        # Collections presse prioritaires
        self.press_collections = [
            'news', 'newspapers', 'journals', 'magazines',
            'lemonde', 'figaro', 'liberation', 'humanite',
            'timesofindia', 'guardian', 'nytimes'
        ]
    
    def _throttle(self):
        """Applique le rate limiting"""
        elapsed = time.time() - self.last_request
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request = time.time()
    
    def search_press_articles(
        self, 
        query: str, 
        start_year: int = None, 
        end_year: int = None,
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Recherche uniquement des articles de presse
        
        Args:
            query: Termes de recherche
            start_year: Année de début
            end_year: Année de fin
            max_results: Nombre max de résultats
            
        Returns:
            List[Dict]: Articles de presse trouvés
        """
        try:
            self._throttle()
            
            # Construction de la query optimisée pour la presse
            search_query = self._build_press_query(query, start_year, end_year)
            
            params = {
                'q': search_query,
                'fl[]': [
                    'identifier', 'title', 'description', 'date', 'year',
                    'creator', 'publisher', 'subject', 'language',
                    'source', 'mediatype', 'downloads'
                ],
                'rows': max_results,
                'output': 'json',
                'page': 1,
                'sort[]': ['date desc', 'downloads desc']
            }
            
            logger.info(f"🔍 Recherche Archive.org: {query[:50]}...")
            
            response = self.session.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            docs = data.get('response', {}).get('docs', [])
            
            # Filtrage presse strict
            press_items = [doc for doc in docs if self._is_press_item(doc)]
            
            logger.info(f"✅ {len(press_items)} articles de presse trouvés")
            return press_items
            
        except Exception as e:
            logger.error(f"❌ Erreur recherche Archive.org: {e}")
            return []
    
    def _build_press_query(self, query: str, start_year: int = None, end_year: int = None) -> str:
        """Construit une query optimisée pour la presse"""
        # Base query avec collections presse
        collections_str = ' OR '.join([f'collection:{col}' for col in self.press_collections[:5]])
        base_query = f'({collections_str}) AND mediatype:texts'
        
        # Ajouter la recherche utilisateur
        if query:
            search_terms = ' OR '.join([f'title:"{term}"' for term in query.split()[:3]])
            base_query += f' AND ({search_terms})'
        
        # Filtrage par date
        if start_year and end_year:
            base_query += f' AND year:[{start_year} TO {end_year}]'
        
        # Filtrage langue
        base_query += ' AND language:(fre OR eng)'
        
        return base_query
    
    def _is_press_item(self, item: Dict[str, Any]) -> bool:
        """Vérifie si c'est bien un article de presse"""
        # Vérifier le mediatype
        mediatype = item.get('mediatype', '').lower()
        if mediatype not in ['texts', 'news']:
            return False
        
        # Vérifier les sujets
        subjects = item.get('subject', [])
        if isinstance(subjects, str):
            subjects = [subjects]
        
        press_keywords = ['news', 'journal', 'newspaper', 'magazine', 'press', 'article']
        has_press_subject = any(
            any(keyword in str(subject).lower() for keyword in press_keywords)
            for subject in subjects
        )
        
        return has_press_subject
    
    def get_item_metadata(self, identifier: str) -> Optional[Dict[str, Any]]:
        """Récupère les métadonnées complètes d'un item"""
        try:
            self._throttle()
            url = f"{self.METADATA_URL}/{identifier}"
            response = self.session.get(url, timeout=20)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"❌ Erreur métadonnées {identifier}: {e}")
            return None
    
    def extract_content(self, item: Dict[str, Any]) -> str:
        """Extrait le contenu textuel d'un item"""
        text_parts = []
        
        # Titre
        if item.get('title'):
            text_parts.append(str(item['title']))
        
        # Description (souvent riche)
        if item.get('description'):
            desc = item['description']
            if isinstance(desc, list):
                text_parts.extend([str(d) for d in desc])
            else:
                text_parts.append(str(desc))
        
        # Sujets
        if item.get('subject'):
            subjects = item['subject']
            if isinstance(subjects, list):
                text_parts.extend([str(s) for s in subjects])
            else:
                text_parts.append(str(subjects))
        
        # Éditeur/créateur
        if item.get('publisher'):
            text_parts.append(str(item['publisher']))
        if item.get('creator'):
            text_parts.append(str(item['creator']))
        
        return ' '.join(text_parts)
