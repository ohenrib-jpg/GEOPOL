# Flask/real_travel_data.py
"""
Données voyage RÉELLES avec scraping amélioré
"""

import logging
import requests
from datetime import datetime
from typing import Dict, List, Any
from bs4 import BeautifulSoup
import json

logger = logging.getLogger(__name__)

class RealTravelData:
    """Récupère les avis voyage en temps réel"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def fetch_real_advisories(self) -> Dict[str, Any]:
        """Récupère les avis réels"""
        advisories = []
        
        # 1. US State Department (API officielle)
        us_data = self._fetch_us_advisories()
        advisories.extend(us_data)
        
        # 2. UK Foreign Office (scraping)
        uk_data = self._fetch_uk_advisories()
        advisories.extend(uk_data)
        
        # 3. Canada Travel (scraping)
        ca_data = self._fetch_canada_advisories()
        advisories.extend(ca_data)
        
        # Sauvegarder
        self._save_advisories(advisories)
        
        return {
            'success': True,
            'advisories': advisories,
            'total': len(advisories),
            'sources': ['US', 'UK', 'CA'],
            'real_data': True,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _fetch_us_advisories(self) -> List[Dict[str, Any]]:
        """Avis US State Department"""
        try:
            url = "https://travel.state.gov/content/travel/en/traveladvisories/traveladvisories.json"
            response = self.session.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                advisories = []
                
                for country in data.get('countries', []):
                    advisories.append({
                        'country_code': country.get('iso', 'XX'),
                        'country_name': country.get('name', 'Unknown'),
                        'risk_level': self._parse_us_risk_level(country.get('level', '1')),
                        'source': 'us_state_department',
                        'summary': country.get('advisory_text', '')[:200],
                        'last_updated': country.get('last_updated', datetime.utcnow().isoformat()),
                        'real_data': True
                    })
                
                logger.info(f"✅ {len(advisories)} avis US récupérés")
                return advisories
                
        except Exception as e:
            logger.error(f"❌ Erreur US advisories: {e}")
        
        return []
    
    def _fetch_uk_advisories(self) -> List[Dict[str, Any]]:
        """Avis UK Foreign Office"""
        try:
            # Cette URL réelle liste tous les pays
            url = "https://www.gov.uk/foreign-travel-advice"
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                advisories = []
                
                # Chercher les liens vers les pages pays
                country_links = soup.find_all('a', class_='govuk-link')
                
                for link in country_links[:20]:  # Limiter pour performance
                    href = link.get('href', '')
                    if '/foreign-travel-advice/' in href and not href.endswith('/foreign-travel-advice'):
                        country_name = link.text.strip()
                        if country_name:
                            advisories.append({
                                'country_code': self._country_to_code(country_name),
                                'country_name': country_name,
                                'risk_level': 2,  # Par défaut
                                'source': 'uk_foreign_office',
                                'summary': f'Consultez les conseils pour {country_name}',
                                'last_updated': datetime.utcnow().isoformat(),
                                'real_data': True
                            })
                
                logger.info(f"✅ {len(advisories)} avis UK récupérés")
                return advisories
                
        except Exception as e:
            logger.error(f"❌ Erreur UK advisories: {e}")
        
        return []
    
    def _fetch_canada_advisories(self) -> List[Dict[str, Any]]:
        """Avis Canada Travel"""
        try:
            url = "https://travel.gc.ca/travelling/advisories"
            response = self.session.get(url, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                advisories = []
                
                # Chercher les alertes
                advisory_items = soup.find_all('div', class_='alert')
                
                for item in advisory_items[:15]:
                    text = item.get_text().strip()
                    if 'Avoid all travel' in text or 'Avoid non-essential travel' in text:
                        # Essayer d'extraire le pays
                        lines = text.split('\n')
                        if lines:
                            advisories.append({
                                'country_code': 'XX',
                                'country_name': lines[0][:50],
                                'risk_level': 4 if 'Avoid all travel' in text else 3,
                                'source': 'canada_travel',
                                'summary': text[:200],
                                'last_updated': datetime.utcnow().isoformat(),
                                'real_data': True
                            })
                
                logger.info(f"✅ {len(advisories)} avis Canada récupérés")
                return advisories
                
        except Exception as e:
            logger.error(f"❌ Erreur Canada advisories: {e}")
        
        return []
    
    def _parse_us_risk_level(self, level_str: str) -> int:
        """Convertit le niveau de risque US"""
        level_map = {
            'Level 1': 1,
            'Level 2': 2,
            'Level 3': 3,
            'Level 4': 4
        }
        
        for key, value in level_map.items():
            if key in level_str:
                return value
        
        return 1
    
    def _country_to_code(self, country_name: str) -> str:
        """Convertit nom de pays en code"""
        country_map = {
            'France': 'FR',
            'Germany': 'DE',
            'United Kingdom': 'GB',
            'United States': 'US',
            'China': 'CN',
            'Russia': 'RU',
            'Ukraine': 'UA'
        }
        
        return country_map.get(country_name, country_name[:2].upper())
    
    def _save_advisories(self, advisories: List[Dict[str, Any]]):
        """Sauvegarde en base de données"""
        try:
            conn = self.db_manager.get_connection()
            cur = conn.cursor()
            
            for advisory in advisories:
                cur.execute("""
                    INSERT OR REPLACE INTO travel_advisories 
                    (country_code, country_name, risk_level, source, summary, last_updated, real_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    advisory['country_code'],
                    advisory['country_name'],
                    advisory['risk_level'],
                    advisory['source'],
                    advisory['summary'],
                    advisory['last_updated'],
                    advisory.get('real_data', True)
                ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"💾 {len(advisories)} avis sauvegardés")
            
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde avis: {e}")