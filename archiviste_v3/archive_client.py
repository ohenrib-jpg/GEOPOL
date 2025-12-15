"""
Client Archive.org - Version corrigée
"""

import requests
import re
from typing import List, Dict, Any, Optional

class ArchiveOrgClient:
    """Client Archive.org simplifié et robuste"""
    
    BASE_URL = "https://archive.org/advancedsearch.php"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GEOPOL-Archive/1.0',
            'Accept': 'application/json',
        })
        print("✅ ArchiveOrgClient initialisé")
    
    def search_french_press(self, query: str, start_year: int = None, 
                           end_year: int = None, max_results: int = 30) -> List[Dict[str, Any]]:
        """Recherche simple dans Archive.org"""
        try:
            print(f"🔍 Archive.org: '{query}' {start_year}-{end_year}")
            
            # Nettoyer la requête
            if ' OR ' in query and ' AND ' not in query:
                # Garder la structure OR telle quelle
                search_query = f'({query})'
            else:
                safe_query = query.replace('"', '\\"')
                search_query = f'"{safe_query}"'
            
            # Construire requête complète
            query_parts = [search_query, 'language:fre', 'mediatype:texts']
            
            if start_year and end_year:
                query_parts.append(f'year:[{start_year} TO {end_year}]')
            
            final_query = ' AND '.join(query_parts)
            print(f"📤 Requête Archive.org: {final_query}")
            
            params = {
                'q': final_query,
                'fl[]': ['identifier', 'title', 'description', 'year', 
                        'publisher', 'downloads', 'mediatype', 'language'],
                'rows': max_results * 2,
                'output': 'json',
                'sort[]': ['downloads desc']
            }
            
            # Appel API
            response = self.session.get(self.BASE_URL, params=params, timeout=30)
            
            print(f"📡 Statut Archive.org: {response.status_code}")
            
            if response.status_code != 200:
                print(f"❌ Erreur Archive.org HTTP: {response.status_code}")
                return []
            
            data = response.json()
            docs = data.get('response', {}).get('docs', [])
            
            print(f"📊 Archive.org: {len(docs)} documents bruts")
            
            # Convertir les résultats
            articles = []
            for doc in docs[:max_results]:
                article = self._convert_document(doc)
                if article:
                    articles.append(article)
            
            print(f"✅ Archive.org: {len(articles)} articles convertis")
            return articles
            
        except Exception as e:
            print(f"❌ Exception Archive.org: {e}")
            return []
    
    def _convert_document(self, doc: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Convertit un document Archive.org"""
        try:
            identifier = doc.get('identifier', '')
            if not identifier:
                return None
            
            # Titre
            title = doc.get('title', '')
            if isinstance(title, list):
                title = ' '.join(title)
            
            # Description
            description = doc.get('description', '')
            if isinstance(description, list):
                description = ' '.join(description)
            
            # Année
            year = doc.get('year', 0)
            
            # Publisher
            publisher = doc.get('publisher', '')
            if isinstance(publisher, list):
                publisher = publisher[0] if publisher else ''
            
            # Vérifier langue
            language = doc.get('language', '')
            if isinstance(language, list):
                language = ' '.join(language)
            
            if 'fre' not in str(language).lower() and 'fra' not in str(language).lower():
                return None
            
            return {
                'identifier': identifier,
                'title': str(title).strip()[:300],
                'description': str(description).strip()[:500],
                'year': int(year) if year else 0,
                'publisher': str(publisher).strip()[:100],
                'downloads': doc.get('downloads', 0),
                'source_url': f"https://archive.org/details/{identifier}",
                'quality_score': self._calculate_quality(doc)
            }
            
        except Exception as e:
            print(f"⚠️ Erreur conversion document: {e}")
            return None
    
    def _calculate_quality(self, doc: Dict[str, Any]) -> float:
        """Calcule un score de qualité"""
        score = 0.5
        
        # Téléchargements
        downloads = doc.get('downloads', 0)
        if downloads > 1000:
            score += 0.3
        elif downloads > 100:
            score += 0.2
        elif downloads > 10:
            score += 0.1
        
        return min(score, 1.0)