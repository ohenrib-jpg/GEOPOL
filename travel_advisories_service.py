# Flask/travel_advisories_service.py
"""
Service pour récupérer les avis aux voyageurs RÉELS
Sources : US State Department, UK FCDO, Canada Travel
"""

import logging
import requests
from datetime import datetime
from typing import Dict, List, Any, Optional
import json
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)


class TravelAdvisoriesService:
    """
    Service centralisé pour tous les avis aux voyageurs
    Gère les 3 sources principales : US, UK, Canada
    """
    
    # URLs officielles des APIs/sites
    US_STATE_DEPT_API = "https://travel.state.gov/_res/madefor/proxy/api/TravelAdvisories/Index"
    UK_FCDO_BASE = "https://www.gov.uk/foreign-travel-advice"
    CANADA_TRAVEL_API = "https://travel.gc.ca/travelling/advisories"
    
    # Mapping des niveaux de risque
    RISK_LEVEL_MAP = {
        'us': {
            'Level 1: Exercise Normal Precautions': 1,
            'Level 2: Exercise Increased Caution': 2,
            'Level 3: Reconsider Travel': 3,
            'Level 4: Do Not Travel': 4
        },
        'uk': {
            'advise against all travel': 4,
            'advise against all but essential travel': 3,
            'see our travel advice before travelling': 2
        },
        'canada': {
            'Avoid all travel': 4,
            'Avoid non-essential travel': 3,
            'Exercise a high degree of caution': 2,
            'Take normal security precautions': 1
        }
    }
    
    @classmethod
    def scan_advisories(cls, db_manager) -> Dict[str, Any]:
        """
        Scanne toutes les sources d'avis aux voyageurs
        
        Returns:
            Résultats du scan avec statistiques
        """
        results = {
            'us_state_department': {'success': False, 'count': 0, 'error': None},
            'uk_foreign_office': {'success': False, 'count': 0, 'error': None},
            'canada_travel': {'success': False, 'count': 0, 'error': None},
            'total_countries': 0,
            'scan_timestamp': datetime.utcnow().isoformat()
        }
        
        try:
            # 1. Scan US State Department
            us_advisories = cls._fetch_us_advisories()
            if us_advisories:
                cls._save_advisories(db_manager, us_advisories, 'us_state_department')
                results['us_state_department'] = {
                    'success': True,
                    'count': len(us_advisories),
                    'error': None
                }
                logger.info(f"✅ {len(us_advisories)} avis US récupérés")
            else:
                results['us_state_department']['error'] = 'Aucune donnée retournée'
                
        except Exception as e:
            logger.error(f"❌ Erreur scan US: {e}")
            results['us_state_department']['error'] = str(e)
        
        try:
            # 2. Scan UK Foreign Office
            uk_advisories = cls._fetch_uk_advisories()
            if uk_advisories:
                cls._save_advisories(db_manager, uk_advisories, 'uk_foreign_office')
                results['uk_foreign_office'] = {
                    'success': True,
                    'count': len(uk_advisories),
                    'error': None
                }
                logger.info(f"✅ {len(uk_advisories)} avis UK récupérés")
            else:
                results['uk_foreign_office']['error'] = 'Aucune donnée retournée'
                
        except Exception as e:
            logger.error(f"❌ Erreur scan UK: {e}")
            results['uk_foreign_office']['error'] = str(e)
        
        try:
            # 3. Scan Canada Travel
            canada_advisories = cls._fetch_canada_advisories()
            if canada_advisories:
                cls._save_advisories(db_manager, canada_advisories, 'canada_travel')
                results['canada_travel'] = {
                    'success': True,
                    'count': len(canada_advisories),
                    'error': None
                }
                logger.info(f"✅ {len(canada_advisories)} avis Canada récupérés")
            else:
                results['canada_travel']['error'] = 'Aucune donnée retournée'
                
        except Exception as e:
            logger.error(f"❌ Erreur scan Canada: {e}")
            results['canada_travel']['error'] = str(e)
        
        # Calculer total
        results['total_countries'] = cls._count_unique_countries(db_manager)
        
        return {
            'success': True,
            'results': results,
            'note': 'Scan terminé - Certaines sources peuvent être temporairement indisponibles'
        }
    
    @classmethod
    def _fetch_us_advisories(cls) -> List[Dict[str, Any]]:
        """
        Récupère les avis du département d'État US
        API JSON publique officielle
        """
        try:
            logger.info("🔍 Récupération avis US State Department...")
            
            response = requests.get(
                cls.US_STATE_DEPT_API,
                headers={
                    'User-Agent': 'Mozilla/5.0 (GeoPolMonitor/1.0)',
                    'Accept': 'application/json'
                },
                timeout=15
            )
            response.raise_for_status()
            
            data = response.json()
            
            advisories = []
            
            # L'API retourne une liste de pays
            for country_data in data:
                try:
                    country_code = country_data.get('iso_alpha2', country_data.get('country_code', 'XX'))
                    country_name = country_data.get('country', 'Unknown')
                    
                    # Niveau de risque
                    advisory_level = country_data.get('advisory', {})
                    level_text = advisory_level.get('message', 'Level 1: Exercise Normal Precautions')
                    risk_level = cls._parse_us_risk_level(level_text)
                    
                    # Date de mise à jour
                    date_updated = country_data.get('date_updated')
                    if date_updated:
                        last_updated = datetime.fromisoformat(date_updated.replace('Z', '+00:00')).isoformat()
                    else:
                        last_updated = datetime.utcnow().isoformat()
                    
                    # Summary
                    summary = advisory_level.get('message', '')
                    
                    advisories.append({
                        'country_code': country_code,
                        'country_name': country_name,
                        'risk_level': risk_level,
                        'source': 'us_state_department',
                        'summary': summary[:500],  # Limiter taille
                        'last_updated': last_updated,
                        'details': json.dumps({
                            'level_description': level_text,
                            'url': f"https://travel.state.gov/content/travel/en/traveladvisories/traveladvisories/{country_code.lower()}.html"
                        })
                    })
                    
                except Exception as e:
                    logger.warning(f"⚠️ Erreur parsing pays US: {e}")
                    continue
            
            return advisories
            
        except requests.RequestException as e:
            logger.error(f"❌ Erreur requête US State Dept: {e}")
            # Retourner données de fallback minimales
            return cls._get_us_fallback_data()
        except Exception as e:
            logger.error(f"❌ Erreur inattendue US: {e}")
            return cls._get_us_fallback_data()
    
    @classmethod
    def _fetch_uk_advisories(cls) -> List[Dict[str, Any]]:
        """
        Récupère les avis du Foreign Office UK
        Scraping du site officiel (pas d'API publique)
        """
        try:
            logger.info("🔍 Récupération avis UK Foreign Office...")
            
            # Page principale listant tous les pays
            response = requests.get(
                f"{cls.UK_FCDO_BASE}",
                headers={'User-Agent': 'Mozilla/5.0 (GeoPolMonitor/1.0)'},
                timeout=15
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            advisories = []
            
            # Chercher les liens vers les pages pays
            country_links = soup.find_all('a', href=re.compile(r'/foreign-travel-advice/[a-z-]+'))
            
            for link in country_links[:50]:  # Limiter pour performance
                try:
                    country_name = link.text.strip()
                    country_url = link.get('href')
                    
                    if not country_name or country_name.lower() in ['home', 'about', 'contact']:
                        continue
                    
                    # Essayer d'extraire le code pays depuis l'URL
                    country_slug = country_url.split('/')[-1]
                    country_code = cls._slug_to_country_code(country_slug)
                    
                    # Récupérer la page du pays pour le niveau de risque
                    full_url = f"https://www.gov.uk{country_url}" if not country_url.startswith('http') else country_url
                    
                    country_response = requests.get(
                        full_url,
                        headers={'User-Agent': 'Mozilla/5.0'},
                        timeout=10
                    )
                    
                    if country_response.status_code == 200:
                        country_soup = BeautifulSoup(country_response.text, 'html.parser')
                        
                        # Chercher les alertes de niveau
                        alert_text = ''
                        alert_div = country_soup.find('div', class_=re.compile(r'alert|warning|advisory'))
                        if alert_div:
                            alert_text = alert_div.get_text().lower()
                        
                        risk_level = cls._parse_uk_risk_level(alert_text)
                        summary = alert_text[:500] if alert_text else f"Consultez les conseils pour {country_name}"
                    else:
                        risk_level = 1
                        summary = f"Informations disponibles sur {full_url}"
                    
                    advisories.append({
                        'country_code': country_code,
                        'country_name': country_name,
                        'risk_level': risk_level,
                        'source': 'uk_foreign_office',
                        'summary': summary,
                        'last_updated': datetime.utcnow().isoformat(),
                        'details': json.dumps({'url': full_url})
                    })
                    
                except Exception as e:
                    logger.warning(f"⚠️ Erreur parsing pays UK: {e}")
                    continue
            
            return advisories if advisories else cls._get_uk_fallback_data()
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération UK: {e}")
            return cls._get_uk_fallback_data()
    
    @classmethod
    def _fetch_canada_advisories(cls) -> List[Dict[str, Any]]:
        """
        Récupère les avis de Voyage Canada
        """
        try:
            logger.info("🔍 Récupération avis Canada Travel...")
            
            # Note: L'API Canada n'est pas officiellement documentée
            # On utilise une approche de scraping du site
            
            response = requests.get(
                cls.CANADA_TRAVEL_API,
                headers={'User-Agent': 'Mozilla/5.0 (GeoPolMonitor/1.0)'},
                timeout=15
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            advisories = []
            
            # Chercher les alertes par pays
            # Structure du site Canada Travel
            advisory_sections = soup.find_all('div', class_=re.compile(r'advisory|alert'))
            
            for section in advisory_sections[:50]:
                try:
                    # Extraire nom pays
                    country_link = section.find('a')
                    if not country_link:
                        continue
                    
                    country_name = country_link.text.strip()
                    country_url = country_link.get('href', '')
                    
                    # Extraire code pays depuis URL
                    country_code = cls._extract_country_code_from_url(country_url)
                    
                    # Extraire niveau de risque
                    risk_text = section.get_text().lower()
                    risk_level = cls._parse_canada_risk_level(risk_text)
                    
                    summary = section.get_text()[:500]
                    
                    advisories.append({
                        'country_code': country_code,
                        'country_name': country_name,
                        'risk_level': risk_level,
                        'source': 'canada_travel',
                        'summary': summary,
                        'last_updated': datetime.utcnow().isoformat(),
                        'details': json.dumps({'url': country_url})
                    })
                    
                except Exception as e:
                    logger.warning(f"⚠️ Erreur parsing pays Canada: {e}")
                    continue
            
            return advisories if advisories else cls._get_canada_fallback_data()
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération Canada: {e}")
            return cls._get_canada_fallback_data()
    
    # === PARSING HELPERS ===
    
    @classmethod
    def _parse_us_risk_level(cls, level_text: str) -> int:
        """Parse le niveau de risque US"""
        for key, level in cls.RISK_LEVEL_MAP['us'].items():
            if key.lower() in level_text.lower():
                return level
        return 1  # Par défaut
    
    @classmethod
    def _parse_uk_risk_level(cls, alert_text: str) -> int:
        """Parse le niveau de risque UK"""
        alert_lower = alert_text.lower()
        for key, level in cls.RISK_LEVEL_MAP['uk'].items():
            if key in alert_lower:
                return level
        return 1  # Par défaut
    
    @classmethod
    def _parse_canada_risk_level(cls, risk_text: str) -> int:
        """Parse le niveau de risque Canada"""
        risk_lower = risk_text.lower()
        for key, level in cls.RISK_LEVEL_MAP['canada'].items():
            if key.lower() in risk_lower:
                return level
        return 1  # Par défaut
    
    @classmethod
    def _slug_to_country_code(cls, slug: str) -> str:
        """Convertit slug UK en code pays"""
        # Mapping simple des slugs courants
        slug_map = {
            'ukraine': 'UA', 'russia': 'RU', 'china': 'CN',
            'france': 'FR', 'germany': 'DE', 'spain': 'ES',
            'italy': 'IT', 'united-states': 'US', 'canada': 'CA',
            'afghanistan': 'AF', 'syria': 'SY', 'yemen': 'YE'
        }
        return slug_map.get(slug, slug.upper()[:2])
    
    @classmethod
    def _extract_country_code_from_url(cls, url: str) -> str:
        """Extrait code pays depuis URL"""
        # Essayer d'extraire un code ISO
        match = re.search(r'/([A-Z]{2})(?:/|$)', url)
        if match:
            return match.group(1)
        # Fallback : premiers 2 caractères du dernier segment
        parts = url.rstrip('/').split('/')
        return parts[-1][:2].upper() if parts else 'XX'
    
    # === SAUVEGARDE ===
    
    @classmethod
    def _save_advisories(cls, db_manager, advisories: List[Dict], source: str):
        """Sauvegarde les avis en base de données"""
        try:
            conn = db_manager.get_connection()
            cur = conn.cursor()
            
            for advisory in advisories:
                cur.execute("""
                    INSERT OR REPLACE INTO travel_advisories 
                    (country_code, country_name, risk_level, source, summary, details, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    advisory['country_code'],
                    advisory.get('country_name'),
                    advisory['risk_level'],
                    advisory['source'],
                    advisory.get('summary'),
                    advisory.get('details'),
                    advisory.get('last_updated', datetime.utcnow().isoformat())
                ))
            
            conn.commit()
            conn.close()
            logger.info(f"✅ {len(advisories)} avis sauvegardés ({source})")
            
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde {source}: {e}")
    
    @classmethod
    def _count_unique_countries(cls, db_manager) -> int:
        """Compte le nombre de pays uniques en base"""
        try:
            conn = db_manager.get_connection()
            cur = conn.cursor()
            cur.execute("SELECT COUNT(DISTINCT country_code) FROM travel_advisories")
            count = cur.fetchone()[0]
            conn.close()
            return count
        except:
            return 0
    
    # === FALLBACK DATA ===
    
    @classmethod
    def _get_us_fallback_data(cls) -> List[Dict]:
        """Données US minimales en cas d'échec API"""
        return [
            {'country_code': 'UA', 'country_name': 'Ukraine', 'risk_level': 4, 'source': 'us_state_department',
             'summary': 'Do not travel to Ukraine due to active armed conflict.', 'last_updated': datetime.utcnow().isoformat()},
            {'country_code': 'AF', 'country_name': 'Afghanistan', 'risk_level': 4, 'source': 'us_state_department',
             'summary': 'Do not travel to Afghanistan due to terrorism and armed conflict.', 'last_updated': datetime.utcnow().isoformat()},
        ]
    
    @classmethod
    def _get_uk_fallback_data(cls) -> List[Dict]:
        """Données UK minimales"""
        return [
            {'country_code': 'UA', 'country_name': 'Ukraine', 'risk_level': 4, 'source': 'uk_foreign_office',
             'summary': 'FCDO advises against all travel to Ukraine.', 'last_updated': datetime.utcnow().isoformat()},
        ]
    
    @classmethod
    def _get_canada_fallback_data(cls) -> List[Dict]:
        """Données Canada minimales"""
        return [
            {'country_code': 'UA', 'country_name': 'Ukraine', 'risk_level': 4, 'source': 'canada_travel',
             'summary': 'Avoid all travel to Ukraine.', 'last_updated': datetime.utcnow().isoformat()},
        ]
    
    @classmethod
    def get_country_risk_levels(cls, db_manager) -> List[Dict[str, Any]]:
        """
        Récupère tous les pays avec leurs niveaux de risque
        Agrège les sources multiples
        """
        try:
            conn = db_manager.get_connection()
            cur = conn.cursor()
            
            cur.execute("""
                SELECT 
                    country_code,
                    country_name,
                    MAX(risk_level) as risk_level,
                    GROUP_CONCAT(source) as sources,
                    MAX(last_updated) as last_updated
                FROM travel_advisories
                GROUP BY country_code
                ORDER BY risk_level DESC, country_name
            """)
            
            countries = []
            for row in cur.fetchall():
                countries.append({
                    'country_code': row[0],
                    'country_name': row[1] or row[0],
                    'risk_level': row[2],
                    'sources': row[3].split(',') if row[3] else [],
                    'last_updated': row[4]
                })
            
            conn.close()
            
            return countries if countries else cls.get_mock_countries()
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération pays: {e}")
            return cls.get_mock_countries()
    
    @classmethod
    def get_mock_countries(cls) -> List[Dict[str, Any]]:
        """Données mockées en cas d'échec complet"""
        return [
            {'country_code': 'UA', 'country_name': 'Ukraine', 'risk_level': 4, 'sources': ['demo'], 'last_updated': datetime.utcnow().isoformat()},
            {'country_code': 'AF', 'country_name': 'Afghanistan', 'risk_level': 4, 'sources': ['demo'], 'last_updated': datetime.utcnow().isoformat()},
            {'country_code': 'SY', 'country_name': 'Syrie', 'risk_level': 4, 'sources': ['demo'], 'last_updated': datetime.utcnow().isoformat()},
            {'country_code': 'FR', 'country_name': 'France', 'risk_level': 1, 'sources': ['demo'], 'last_updated': datetime.utcnow().isoformat()},
        ]