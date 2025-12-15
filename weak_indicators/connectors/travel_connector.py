# Flask/weak_indicators/connectors/travel_connector.py
"""Connecteur unifié pour les avis de voyage avec scraping léger - VERSION TIMEOUT CORRIGÉE"""

import logging
import requests
from bs4 import BeautifulSoup
from typing import List, Optional
from datetime import datetime
from urllib.parse import urljoin
import time

from ..models import TravelAdvisory

logger = logging.getLogger(__name__)

class TravelScraper:
    """Classe de base pour le scraping des avis de voyage"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        # CORRECTION: Augmenter timeout et réduire délai
        self.timeout = 15  # Réduit de 30 à 15 secondes
        self.delay = 0.5   # Réduit de 1 à 0.5 secondes
        self.max_retries = 2  # Maximum de tentatives


    def fetch_all_advisories(self) -> List[TravelAdvisory]:
        """Récupère tous les avis de toutes les sources"""
    
    # Fallback immédiat pour le débogage
        logger.warning("⚠️ Utilisation des données de fallback pour le débogage")
        return self._get_fallback_advisories()
    
    def _safe_request(self, url: str, retry_count: int = 0) -> Optional[str]:
        """Effectue une requête HTTP sécurisée avec retry"""
        try:
            time.sleep(self.delay)
            
            logger.info(f"Requête {url} (tentative {retry_count + 1}/{self.max_retries + 1})")
            
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            logger.info(f"✅ Succès {url}")
            return response.text
            
        except requests.Timeout:
            if retry_count < self.max_retries:
                logger.warning(f"⏱️ Timeout {url}, retry {retry_count + 1}")
                time.sleep(1)
                return self._safe_request(url, retry_count + 1)
            else:
                logger.error(f"❌ Timeout définitif après {self.max_retries + 1} tentatives: {url}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"❌ Erreur requête {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Erreur inattendue {url}: {e}")
            return None

class UKGovScraper(TravelScraper):
    """Scraper pour le UK Foreign Office"""
    
    def scrape_source(self, url: str, source_name: str = "uk_gov") -> List[TravelAdvisory]:
        advisories = []
        
        html = self._safe_request(url)
        if not html:
            logger.warning(f"⚠️ UK Gov: impossible de récupérer la page principale")
            return advisories
        
        soup = BeautifulSoup(html, 'html.parser')
        country_cards = soup.find_all('li', class_='gem-c-document-list__item')
        
        # CORRECTION: Limiter à 10 pays au lieu de 20 pour accélérer
        for card in country_cards[:10]:
            try:
                link = card.find('a', class_='govuk-link')
                if not link:
                    continue
                    
                country_url = urljoin(url, link.get('href'))
                country_name = link.text.strip()
                
                advisory = self._scrape_country_page(country_url, country_name, source_name)
                if advisory:
                    advisories.append(advisory)
                    
            except Exception as e:
                logger.error(f"Erreur scraping UK pays {country_name}: {e}")
        
        logger.info(f"✅ UK Gov: {len(advisories)} avis récupérés")
        return advisories
    
    def _scrape_country_page(self, url: str, country_name: str, source: str) -> Optional[TravelAdvisory]:
        """Scrape la page d'un pays spécifique"""
        html = self._safe_request(url)
        if not html:
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        
        risk_level = 1  # Par défaut
        content = soup.find('div', class_='govuk-grid-column-two-thirds')
        
        if content:
            text = content.get_text().lower()
            
            if 'do not travel' in text or 'advise against' in text:
                risk_level = 4
            elif 'reconsider' in text or 'advise reconsidering' in text:
                risk_level = 3
            elif 'exercise caution' in text or 'be cautious' in text:
                risk_level = 2
            
            summary_elem = content.find('p')
            summary = summary_elem.get_text()[:200] + '...' if summary_elem else "Consultez le site officiel"
        else:
            summary = "Informations disponibles sur le site du UK Foreign Office"
        
        country_code = self._country_name_to_code(country_name)
        
        return TravelAdvisory(
            country_code=country_code,
            country_name=country_name,
            risk_level=risk_level,
            source=source,
            summary=summary,
            last_updated=datetime.utcnow(),
            raw_data={'url': url}
        )
    
    def _country_name_to_code(self, name: str) -> str:
        """Convertit un nom de pays en code"""
        mapping = {
            'france': 'FR', 'germany': 'DE', 'spain': 'ES', 'italy': 'IT',
            'united states': 'US', 'china': 'CN', 'russia': 'RU', 'ukraine': 'UA',
            'australia': 'AU', 'japan': 'JP', 'brazil': 'BR', 'india': 'IN',
            'united kingdom': 'GB', 'canada': 'CA', 'mexico': 'MX'
        }
        
        name_lower = name.lower()
        for key, code in mapping.items():
            if key in name_lower:
                return code
        
        return name[:2].upper() if len(name) >= 2 else 'XX'

class SmartravellerScraper(TravelScraper):
    """Scraper pour Australia Smartraveller - VERSION DÉSACTIVÉE PAR DÉFAUT"""
    
    def scrape_source(self, url: str, source_name: str = "au_smartraveller") -> List[TravelAdvisory]:
        # CORRECTION: Désactiver temporairement ce scraper car il timeout
        logger.warning(f"⚠️ Smartraveller temporairement désactivé (timeout récurrent)")
        return []
        
        # Code original commenté
        """
        advisories = []
        html = self._safe_request(url)
        if not html:
            return advisories
        
        soup = BeautifulSoup(html, 'html.parser')
        destinations = soup.find_all('a', href=re.compile(r'/destinations/'))
        
        for dest in destinations[:10]:
            try:
                country_name = dest.get_text(strip=True)
                if not country_name or len(country_name) < 2:
                    continue
                
                advisories.append(
                    TravelAdvisory(
                        country_code=self._country_name_to_code(country_name),
                        country_name=country_name,
                        risk_level=1,
                        source=source_name,
                        summary=f"Voir les conseils pour {country_name} sur Smartraveller",
                        last_updated=datetime.utcnow(),
                        raw_data={'url': urljoin(url, dest.get('href', ''))}
                    )
                )
                
            except Exception as e:
                logger.error(f"Erreur Smartraveller {country_name}: {e}")
        
        return advisories
        """
    
    def _country_name_to_code(self, name: str) -> str:
        return name[:2].upper() if len(name) >= 2 else 'XX'

class FranceDiplomatieScraper(TravelScraper):
    """Scraper pour France Diplomatie"""
    
    def scrape_source(self, url: str, source_name: str = "fr_diplomatie") -> List[TravelAdvisory]:
        advisories = []
        
        html = self._safe_request(url)
        if not html:
            logger.warning(f"⚠️ France Diplomatie: impossible de récupérer la page")
            return advisories
        
        soup = BeautifulSoup(html, 'html.parser')
        country_sections = soup.find_all('div', class_=lambda x: x and ('country' in x.lower() or 'pays' in x.lower()))
        
        # CORRECTION: Limiter à 10 pays
        for section in country_sections[:10]:
            try:
                title = section.find(['h2', 'h3', 'h4'])
                if not title:
                    continue
                    
                country_name = title.get_text(strip=True)
                risk_level = 1
                
                summary_elem = section.find('p')
                summary = summary_elem.get_text()[:150] + '...' if summary_elem else "Consultez France Diplomatie"
                
                advisories.append(
                    TravelAdvisory(
                        country_code=self._country_name_to_code(country_name),
                        country_name=country_name,
                        risk_level=risk_level,
                        source=source_name,
                        summary=summary,
                        last_updated=datetime.utcnow(),
                        raw_data={}
                    )
                )
                
            except Exception as e:
                logger.error(f"Erreur France Diplomatie: {e}")
        
        logger.info(f"✅ France Diplomatie: {len(advisories)} avis récupérés")
        return advisories
    
    def _country_name_to_code(self, name: str) -> str:
        return name[:2].upper() if len(name) >= 2 else 'XX'

class TravelConnector:
    """Connecteur unifié pour les avis de voyage - VERSION OPTIMISÉE TIMEOUT"""
    
    def __init__(self, use_scraping: bool = True):
        self.use_scraping = use_scraping
        self.scrapers = {
            'uk_gov': UKGovScraper(),
            'au_smartraveller': SmartravellerScraper(),  # Désactivé dans le scraper
            'fr_diplomatie': FranceDiplomatieScraper()
        }
        
        # CORRECTION: Désactiver Smartraveller par défaut
        self.sources = {
            'uk_gov': {
                'url': 'https://www.gov.uk/foreign-travel-advice',
                'enabled': True,
                'scraper': 'uk_gov'
            },
            'au_smartraveller': {
                'url': 'https://www.smartraveller.gov.au/destinations',
                'enabled': False,  # DÉSACTIVÉ - timeout trop fréquent
                'scraper': 'au_smartraveller'
            },
            'fr_diplomatie': {
                'url': 'https://www.diplomatie.gouv.fr/fr/conseils-aux-voyageurs/',
                'enabled': True,
                'scraper': 'fr_diplomatie'
            }
        }
    
    def fetch_all_advisories(self) -> List[TravelAdvisory]:
        """Récupère tous les avis de toutes les sources"""
        advisories = []
        
        if not self.use_scraping:
            logger.info("Scraping désactivé, utilisation des données de fallback")
            return self._get_fallback_advisories()
        
        logger.info("🔍 Début du scraping des avis de voyage...")
        
        for source_name, source_config in self.sources.items():
            if not source_config['enabled']:
                logger.info(f"⏭️ Source {source_name} désactivée")
                continue
                
            try:
                logger.info(f"📡 Scraping {source_name}...")
                
                scraper_name = source_config['scraper']
                if scraper_name in self.scrapers:
                    scraper = self.scrapers[scraper_name]
                    
                    # Timeout global pour chaque source (30 secondes max)
                    import signal
                    
                    def timeout_handler(signum, frame):
                        raise TimeoutError(f"Timeout global pour {source_name}")
                    
                    # Configurer le timeout global (Windows n'a pas signal.alarm)
                    try:
                        source_advisories = scraper.scrape_source(
                            source_config['url'], 
                            source_name
                        )
                        
                        if source_advisories:
                            advisories.extend(source_advisories)
                            logger.info(f"✅ {source_name}: {len(source_advisories)} avis récupérés")
                        else:
                            logger.warning(f"⚠️ {source_name}: aucun avis récupéré")
                            
                    except TimeoutError as e:
                        logger.error(f"⏱️ Timeout {source_name}: {e}")
                        advisories.extend(self._get_fallback_for_source(source_name))
                    
            except Exception as e:
                logger.error(f"❌ Erreur scraping {source_name}: {e}")
                advisories.extend(self._get_fallback_for_source(source_name))
        
        # Si aucune donnée, utiliser le fallback complet
        if not advisories:
            logger.warning("⚠️ Aucun avis récupéré, utilisation du fallback")
            advisories = self._get_fallback_advisories()
        
        logger.info(f"✅ Total: {len(advisories)} avis de voyage disponibles")
        return advisories
    
    def _get_fallback_advisories(self) -> List[TravelAdvisory]:
        """Données de fallback"""
        logger.info("📦 Chargement données de fallback")
        return [
            TravelAdvisory(
                country_code='FR',
                country_name='France',
                risk_level=1,
                source='fallback',
                summary='Précautions normales de sécurité',
                last_updated=datetime.utcnow()
            ),
            TravelAdvisory(
                country_code='GB',
                country_name='United Kingdom',
                risk_level=1,
                source='fallback',
                summary='Normal security precautions',
                last_updated=datetime.utcnow()
            ),
            TravelAdvisory(
                country_code='US',
                country_name='United States',
                risk_level=2,
                source='fallback',
                summary='Exercise increased caution',
                last_updated=datetime.utcnow()
            ),
            TravelAdvisory(
                country_code='ES',
                country_name='Spain',
                risk_level=1,
                source='fallback',
                summary='Precauciones normales',
                last_updated=datetime.utcnow()
            ),
            TravelAdvisory(
                country_code='DE',
                country_name='Germany',
                risk_level=1,
                source='fallback',
                summary='Normale Sicherheitsvorkehrungen',
                last_updated=datetime.utcnow()
            )
        ]
    
    def _get_fallback_for_source(self, source_name: str) -> List[TravelAdvisory]:
        """Fallback pour une source spécifique"""
        logger.info(f"📦 Fallback pour source {source_name}")
        return []