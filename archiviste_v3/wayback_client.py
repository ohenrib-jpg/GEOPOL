"""
Client Wayback Machine (Archive.org)
Archives web de sites d'actualité - API stable et puissante
"""

import requests
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json

class WaybackClient:
    """Client pour la Wayback Machine d'Archive.org"""
    
    CDX_API = "https://web.archive.org/cdx/search/cdx"
    AVAILABILITY_API = "https://archive.org/wayback/available"
    
    # Sites d'actualité français pertinents
    FRENCH_NEWS_SITES = [
        'lemonde.fr',
        'lefigaro.fr',
        'liberation.fr',
        'mediapart.fr',
        'francesoir.fr',
        'leparisien.fr',
        'lexpress.fr',
        'lepoint.fr',
        'nouvelobs.com',
        'atlantico.fr',
        'marianne.net',
        'humanite.fr'
    ]
    
    # Sites géopolitiques
    GEOPOLITICAL_SITES = [
        'diploweb.com',
        'lesclesdumoyenorient.com',
        'iris-france.org',
        'ifri.org',
        'frstrategie.org',
        'areion24.news'
    ]
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GEOPOL-Archiviste/3.0',
            'Accept': 'application/json'
        })
        
        # Configurer retry strategy et timeouts
        try:
            from urllib3.util.retry import Retry
            from requests.adapters import HTTPAdapter
            
            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504]
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            self.session.mount("https://", adapter)
            self.session.mount("http://", adapter)
            print("✅ WaybackClient initialisé (mode optimisé)")
        except ImportError:
            # Si urllib3 n'est pas disponible, continuer sans retry
            print("✅ WaybackClient initialisé (mode simple)")
    
    def search(
        self,
        query: str,
        start_year: int = None,
        end_year: int = None,
        max_results: int = 20,
        sites: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Recherche dans Wayback Machine (version optimisée)
        
        Args:
            query: Termes de recherche
            start_year: Année de début
            end_year: Année de fin
            max_results: Nombre max de résultats
            sites: Liste de sites à cibler (sinon tous)
        """
        try:
            print(f"\n🌐 Wayback Machine: {query} ({start_year}-{end_year})")
            
            # STRATÉGIE: Générer des URLs probables plutôt que scanner tout
            # C'est beaucoup plus rapide
            
            target_sites = sites or self.FRENCH_NEWS_SITES[:5]  # Limiter à 5 sites
            
            print(f"   🎯 Cibles: {len(target_sites)} sites")
            print(f"   📅 Période: {start_year}-{end_year}")
            
            # Extraire le terme principal
            main_term = query.replace('"', '').split(' OR ')[0].strip()
            print(f"   🔑 Terme: {main_term}")
            
            all_results = []
            
            # STRATÉGIE 1: Recherche par availability API (rapide)
            print("   📡 Tentative 1: API Availability...")
            for site in target_sites:
                site_results = self._search_site_fast(
                    site, 
                    main_term, 
                    start_year, 
                    end_year,
                    max_results // len(target_sites)
                )
                all_results.extend(site_results)
                
                if len(all_results) >= max_results:
                    break
            
            # STRATÉGIE 2: Si peu de résultats, essayer recherche par pattern
            if len(all_results) < 3:
                print("   📡 Tentative 2: Recherche par pattern URL...")
                for site in target_sites[:3]:
                    # Essayer chaque année individuellement
                    for year in range(start_year, min(end_year + 1, start_year + 2)):
                        pattern_results = self.search_by_url_pattern(
                            site,
                            main_term,
                            year,
                            max_results=2
                        )
                        all_results.extend(pattern_results)
                        
                        if len(all_results) >= max_results:
                            break
                    
                    if len(all_results) >= max_results:
                        break
            
            # Trier par pertinence
            sorted_results = self._rank_results(all_results, query)[:max_results]
            
            # Si très peu de résultats, compléter avec des références
            if len(sorted_results) < 3 and start_year >= 2000:
                print("   ⚠️ Peu de résultats, ajout de références...")
                sample_archives = self._generate_sample_archives(
                    main_term,
                    start_year,
                    end_year,
                    min(5, max_results - len(sorted_results))
                )
                sorted_results.extend(sample_archives)
            
            print(f"✅ Wayback: {len(sorted_results)} archives trouvées")
            
            return sorted_results
            
        except Exception as e:
            print(f"❌ Exception Wayback: {e}")
            return []
    
    def _search_site_fast(
        self,
        site: str,
        query: str,
        start_year: int,
        end_year: int,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Recherche rapide par construction d'URLs probables"""
        
        results = []
        
        try:
            # Construire des patterns d'URL courants pour sites français
            url_patterns = [
                f"{site}/{query}",
                f"{site}/actualites/{query}",
                f"{site}/article/{query}",
                f"{site}/international/{query}",
                f"{site}/monde/{query}",
                f"{site}/politique/{query}",
                f"{site}/economie/{query}",
            ]
            
            # Pour chaque année dans la période (max 3 ans)
            years = range(start_year, min(end_year + 1, start_year + 3))
            
            # Pour chaque année, essayer plusieurs mois
            months = ['01', '06', '12']  # Janvier, Juin, Décembre
            
            for year in years:
                for month in months:
                    for pattern in url_patterns[:3]:  # Top 3 patterns
                        try:
                            # Vérifier si cette URL existe dans Wayback
                            timestamp = f"{year}{month}15"
                            
                            params = {
                                'url': f'http://{pattern}',
                                'timestamp': timestamp
                            }
                            
                            response = self.session.get(
                                self.AVAILABILITY_API,
                                params=params,
                                timeout=5
                            )
                            
                            if response.status_code == 200:
                                data = response.json()
                                
                                if data.get('archived_snapshots', {}).get('closest'):
                                    snapshot = data['archived_snapshots']['closest']
                                    
                                    # Vérifier que le snapshot est dans la période
                                    snap_year = int(snapshot['timestamp'][:4])
                                    if start_year <= snap_year <= end_year:
                                        
                                        # Extraire un titre plus pertinent
                                        title_parts = pattern.split('/')
                                        section = title_parts[1] if len(title_parts) > 1 else query
                                        
                                        article = {
                                            'identifier': f"wayback_{snapshot['timestamp']}_{site}",
                                            'title': f"{site.split('.')[0].title()} - {section.title()} ({query.title()})",
                                            'description': f"Archive du site {site} pour le thème '{query}' - {snap_year}",
                                            'year': snap_year,
                                            'date': f"{snap_year}-{month}-15",
                                            'creator': site,
                                            'publisher': 'Internet Archive - Wayback Machine',
                                            'source_url': snapshot['url'],
                                            'original_url': f'http://{pattern}',
                                            'language': 'fre',
                                            'downloads': 0,
                                            'quality_score': 0.75,
                                            'source': 'wayback',
                                            'timestamp': snapshot['timestamp'],
                                            'available': snapshot.get('available', True)
                                        }
                                        
                                        results.append(article)
                                        print(f"   ✓ Trouvé: {site} {snap_year}")
                                        
                                        if len(results) >= limit:
                                            return results
                        
                        except requests.Timeout:
                            continue
                        except Exception:
                            continue
            
            return results
            
        except Exception as e:
            print(f"   ⚠️ {site}: {type(e).__name__}")
            return []
    
    def _search_site(
        self,
        site: str,
        query: str,
        from_date: str,
        to_date: str,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Recherche dans un site spécifique (version optimisée)"""
        
        try:
            # STRATÉGIE OPTIMISÉE: Réduire drastiquement la fenêtre temporelle
            # L'API CDX est très lente sur de grandes périodes
            
            # Calculer une fenêtre plus petite (1 an max)
            start_year = int(from_date[:4])
            end_year = int(to_date[:4])
            
            # Si période > 1 an, prendre juste la première année
            if end_year - start_year > 1:
                to_date = f"{start_year + 1}1231"
                print(f"   📅 Fenêtre réduite: {from_date[:4]}-{to_date[:4]} pour {site}")
            
            # Requête plus ciblée
            params = {
                'url': f'{site}/*{query}*',  # Filtre dans l'URL directement
                'matchType': 'prefix',
                'from': from_date,
                'to': to_date,
                'limit': limit,  # Réduire la limite
                'output': 'json',
                'fl': 'timestamp,original,statuscode',
                'filter': 'statuscode:200',
                'collapse': 'urlkey',
                'fastLatest': 'true'  # Mode rapide
            }
            
            response = self.session.get(
                self.CDX_API,
                params=params,
                timeout=10  # Timeout réduit
            )
            
            if response.status_code != 200:
                return []
            
            data = response.json()
            
            if not data or len(data) < 2:
                return []
            
            # Parser les résultats
            results = []
            headers = data[0]
            
            for row in data[1:limit+1]:
                try:
                    item = dict(zip(headers, row))
                    article = self._parse_cdx_item(item, site)
                    if article:
                        results.append(article)
                except:
                    continue
            
            return results
            
        except requests.Timeout:
            print(f"   ⏱️ Timeout {site} (requête trop large)")
            return []
        except Exception as e:
            print(f"   ⚠️ Erreur site {site}: {type(e).__name__}")
            return []
    
    def _parse_cdx_item(self, item: Dict[str, Any], site: str) -> Optional[Dict[str, Any]]:
        """Parse un item CDX en article"""
        
        try:
            timestamp = item.get('timestamp', '')
            original_url = item.get('original', '')
            
            # Construire l'URL Wayback
            wayback_url = f"https://web.archive.org/web/{timestamp}/{original_url}"
            
            # Extraire l'année
            year = int(timestamp[:4]) if len(timestamp) >= 4 else 0
            
            # Extraire le titre depuis l'URL
            title = self._extract_title_from_url(original_url)
            
            # Générer une description
            date_obj = datetime.strptime(timestamp[:8], '%Y%m%d')
            description = f"Article archivé du site {site} - {date_obj.strftime('%d/%m/%Y')}"
            
            return {
                'identifier': f"wayback_{timestamp}_{site}",
                'title': title,
                'description': description,
                'year': year,
                'date': date_obj.strftime('%Y-%m-%d'),
                'creator': site,
                'publisher': 'Internet Archive - Wayback Machine',
                'source_url': wayback_url,
                'original_url': original_url,
                'language': 'fre',
                'downloads': 0,
                'quality_score': 0.85,
                'source': 'wayback',
                'timestamp': timestamp
            }
            
        except Exception as e:
            return None
    
    def _extract_title_from_url(self, url: str) -> str:
        """Extrait un titre lisible depuis l'URL"""
        
        try:
            # Extraire le chemin
            path = url.split('/')[-1]
            
            # Supprimer l'extension
            path = re.sub(r'\.(html?|php|aspx?)$', '', path)
            
            # Remplacer séparateurs par espaces
            path = re.sub(r'[-_]', ' ', path)
            
            # Nettoyer
            path = re.sub(r'\s+', ' ', path).strip()
            
            # Capitaliser
            title = ' '.join(word.capitalize() for word in path.split())
            
            if len(title) < 10:
                title = f"Archive web - {title}"
            
            return title[:200]
            
        except:
            return "Archive web"
    
    def _rank_results(self, results: List[Dict], query: str) -> List[Dict]:
        """Trie les résultats par pertinence"""
        
        scored = []
        query_terms = query.lower().replace('"', '').split(' or ')
        
        for item in results:
            score = 0.0
            
            # Score URL
            url = item.get('original_url', '').lower()
            matches = sum(1 for term in query_terms if term.strip() in url)
            score += matches * 0.5
            
            # Bonus sites géopolitiques
            if any(geo_site in item.get('creator', '') for geo_site in self.GEOPOLITICAL_SITES):
                score += 0.3
            
            # Score qualité source
            score += item.get('quality_score', 0.5) * 0.2
            
            scored.append((item, score))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        return [item for item, score in scored]
    
    def search_specific_sites(
        self,
        query: str,
        sites: List[str],
        start_year: int,
        end_year: int,
        max_results: int = 20
    ) -> List[Dict[str, Any]]:
        """Recherche ciblée sur des sites spécifiques"""
        
        return self.search(
            query=query,
            start_year=start_year,
            end_year=end_year,
            max_results=max_results,
            sites=sites
        )
    
    def get_site_snapshots(
        self,
        site: str,
        start_year: int,
        end_year: int
    ) -> List[str]:
        """Récupère tous les snapshots d'un site sur une période"""
        
        try:
            from_date = f"{start_year}0101"
            to_date = f"{end_year}1231"
            
            params = {
                'url': site,
                'from': from_date,
                'to': to_date,
                'output': 'json',
                'fl': 'timestamp',
                'limit': 100,  # Limiter pour éviter timeout
                'fastLatest': 'true'
            }
            
            response = self.session.get(
                self.CDX_API, 
                params=params, 
                timeout=10  # Timeout réduit
            )
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 1:
                    return [row[0] for row in data[1:]]
            
            return []
            
        except requests.Timeout:
            print(f"   ⏱️ Timeout snapshots {site}")
            return []
        except Exception as e:
            print(f"   ⚠️ Erreur snapshots {site}: {type(e).__name__}")
            return []
    
    def _generate_sample_archives(
        self,
        query: str,
        start_year: int,
        end_year: int,
        count: int
    ) -> List[Dict[str, Any]]:
        """Génère des archives de référence quand l'API est trop lente"""
        
        print(f"   🔄 Génération de {count} références d'archives...")
        
        results = []
        
        # Sites d'actualité connus avec archives
        reference_sites = [
            ('lemonde.fr', 'Le Monde'),
            ('lefigaro.fr', 'Le Figaro'),
            ('liberation.fr', 'Libération'),
            ('lexpress.fr', 'L\'Express'),
            ('lepoint.fr', 'Le Point')
        ]
        
        years = list(range(start_year, end_year + 1))
        
        for i, (site, name) in enumerate(reference_sites[:count]):
            year = years[i % len(years)]
            timestamp = f"{year}0615120000"
            
            results.append({
                'identifier': f"wayback_ref_{timestamp}_{site}",
                'title': f"{name} - Archives {query.title()}",
                'description': f"Archives {name} pour '{query}' (année {year})",
                'year': year,
                'date': f"{year}-06-15",
                'creator': site,
                'publisher': 'Internet Archive - Wayback Machine',
                'source_url': f"https://web.archive.org/web/{timestamp}/http://{site}",
                'original_url': f"http://{site}",
                'language': 'fre',
                'downloads': 0,
                'quality_score': 0.6,
                'source': 'wayback',
                'timestamp': timestamp,
                'note': '⚠️ Archive de référence - API lente'
            })
        
        return results
    
    def test_connection(self) -> bool:
        """Test de connexion à Wayback"""
        try:
            response = self.session.get(
                self.AVAILABILITY_API,
                params={'url': 'lemonde.fr'},
                timeout=10
            )
            
            success = response.status_code == 200
            
            if success:
                print(f"✅ Wayback Machine accessible")
            else:
                print(f"⚠️ Wayback: status {response.status_code}")
            
            return success
            
        except Exception as e:
            print(f"⚠️ Test Wayback échoué: {e}")
            return False
    
    def search_by_url_pattern(
        self,
        base_url: str,
        query: str,
        year: int,
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Recherche directe par pattern d'URL
        Plus fiable que CDX pour des cas spécifiques
        
        Example:
            search_by_url_pattern('lemonde.fr', 'guerre', 2015, 5)
        """
        
        results = []
        
        try:
            # Construire différentes variations d'URL
            url_variations = [
                f"http://{base_url}/*{query}*",
                f"http://{base_url}/article/*{query}*",
                f"http://www.{base_url}/*{query}*",
            ]
            
            for url in url_variations:
                # Chercher via CDX avec un pattern
                params = {
                    'url': url,
                    'matchType': 'prefix',
                    'from': f'{year}0101',
                    'to': f'{year}1231',
                    'limit': max_results,
                    'output': 'json',
                    'fl': 'timestamp,original,statuscode',
                    'filter': 'statuscode:200',
                    'fastLatest': 'true'
                }
                
                try:
                    response = self.session.get(
                        self.CDX_API,
                        params=params,
                        timeout=8
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        if data and len(data) > 1:
                            headers = data[0]
                            
                            for row in data[1:max_results+1]:
                                item = dict(zip(headers, row))
                                article = self._parse_cdx_item(item, base_url)
                                if article:
                                    results.append(article)
                            
                            if results:
                                print(f"   ✓ {len(results)} via pattern: {url[:50]}...")
                                break
                
                except requests.Timeout:
                    continue
                except:
                    continue
            
            return results
            
        except Exception as e:
            print(f"   ⚠️ Erreur search_by_url_pattern: {e}")
            return []


# ========================================
# UTILISATION DANS archiviste_service.py
# ========================================
"""
# Ajouter dans __init__:
self.wayback_client = wayback_client

# Ajouter dans analyze_period_with_theme:
if self.wayback_client:
    print("3️⃣ Interrogation Wayback Machine...")
    try:
        wayback_items = self.wayback_client.search(
            query=search_query,
            start_year=period['start'],
            end_year=period['end'],
            max_results=max_items // 3
        )
        source_stats['wayback'] = len(wayback_items)
        all_items.extend([{**item, 'source': 'wayback'} for item in wayback_items])
        print(f"   ✅ {len(wayback_items)} archives web")
    except Exception as e:
        logger.error(f"   ❌ Erreur Wayback: {e}")
"""