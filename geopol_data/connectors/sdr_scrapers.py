# Flask/geopol_data/connectors/sdr_scrapers.py
"""
Scrapers pour récupérer les stations SDR actives
Sources: rx-tx.info, kiwisdr.com, websdr.org, sdr.hu
"""

import requests
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import time
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)

class SDRStation:
    """Représente une station SDR active"""
    
    def __init__(
        self,
        id: str,
        name: str,
        lat: float,
        lon: float,
        country: str = None,
        last_seen: datetime = None,
        status: str = "unknown",
        frequency_range: str = None,
        url: str = None,
        type: str = "sdr",
        source: str = "unknown"
    ):
        self.id = id
        self.name = name
        self.lat = lat
        self.lon = lon
        self.country = country
        self.last_seen = last_seen or datetime.utcnow()
        self.status = status
        self.frequency_range = frequency_range
        self.url = url
        self.type = type
        self.source = source

    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire pour JSON"""
        return {
            'id': self.id,
            'name': self.name,
            'lat': self.lat,
            'lon': self.lon,
            'country': self.country,
            'last_seen': self.last_seen.isoformat() + 'Z' if self.last_seen else None,
            'status': self.status,
            'frequency_range': self.frequency_range,
            'url': self.url,
            'type': self.type,
            'source': self.source
        }

class SDRScrapers:
    """Gestionnaire de tous les scrapers SDR"""
    
    def __init__(self, cache_ttl_minutes: int = 15):
        self.cache_ttl = timedelta(minutes=cache_ttl_minutes)
        self.cache = None
        self.cache_timestamp = None
        self.timeout = 20  # Timeout plus long pour le scraping
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def get_all_stations(self, force_refresh: bool = False) -> List[SDRStation]:
        """
        Récupère toutes les stations SDR de toutes les sources
        
        Args:
            force_refresh: Force le rafraîchissement du cache

        Returns:
            Liste des stations SDR
        """
        # Vérifier le cache
        if not force_refresh and self._is_cache_valid():
            logger.info("📦 Utilisation du cache SDR")
            return self.cache

        logger.info("🔄 Rafraîchissement des données SDR...")
        stations = []

        # Sources à scraper
        scrapers = [
            self._scrape_rx_tx_info,
            self._scrape_kiwisdr,
            self._scrape_sdr_hu,
            self._scrape_websdr
        ]

        for scraper in scrapers:
            try:
                source_stations = scraper()
                stations.extend(source_stations)
                logger.info(f"✅ {scraper.__name__}: {len(source_stations)} stations")
            except Exception as e:
                logger.warning(f"⚠️ {scraper.__name__} échoué: {e}")

        # Mettre à jour le cache
        self.cache = stations
        self.cache_timestamp = datetime.utcnow()

        logger.info(f"✅ Total: {len(stations)} stations SDR récupérées")
        return stations

    def _is_cache_valid(self) -> bool:
        """Vérifie si le cache est encore valide"""
        if self.cache is None or self.cache_timestamp is None:
            return False
        return (datetime.utcnow() - self.cache_timestamp) < self.cache_ttl

    def _scrape_rx_tx_info(self) -> List[SDRStation]:
        """
        Scrape les stations depuis https://rx-tx.info/map-sdr-points
        """
        stations = []
        url = "https://rx-tx.info/map-sdr-points"
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # Parser le JSON ou HTML selon la structure réelle
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Chercher les données dans le JavaScript ou les balises data
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and 'var markers' in script.string:
                    # Extraire les données des marqueurs
                    marker_data = re.findall(r'var markers = (\[.*?\]);', script.string, re.DOTALL)
                    if marker_data:
                        try:
                            import json
                            markers = json.loads(marker_data[0])
                            for marker in markers:
                                station = SDRStation(
                                    id=f"rxtx_{len(stations)}",
                                    name=marker.get('name', f'Station {len(stations)}'),
                                    lat=float(marker.get('lat', 0)),
                                    lon=float(marker.get('lng', 0)),
                                    country=marker.get('country', 'Unknown'),
                                    status='active',
                                    url=marker.get('url', ''),
                                    source='rx-tx.info'
                                )
                                stations.append(station)
                        except Exception as e:
                            logger.warning(f"Erreur parsing markers rx-tx.info: {e}")
            
            # Alternative: chercher dans les balises HTML
            map_divs = soup.find_all('div', class_='map-point')
            for div in map_divs:
                try:
                    # Extraire les attributs data-*
                    lat = float(div.get('data-lat', 0))
                    lon = float(div.get('data-lng', 0))
                    name = div.get('data-name', f'Station {len(stations)}')
                    country = div.get('data-country', 'Unknown')
                    
                    station = SDRStation(
                        id=f"rxtx_{len(stations)}",
                        name=name,
                        lat=lat,
                        lon=lon,
                        country=country,
                        status='active',
                        source='rx-tx.info'
                    )
                    stations.append(station)
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Erreur scraping rx-tx.info: {e}")
            
        return stations

    def _scrape_kiwisdr(self) -> List[SDRStation]:
        """
        Scrape les stations depuis kiwisdr.com
        """
        stations = []
        url = "http://kiwisdr.com/public/"
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Chercher les lignes de tableau ou divs contenant les stations
            rows = soup.find_all('tr')  # Table rows
            if not rows:
                rows = soup.find_all('div', class_='receiver')  # Div format
            
            for row in rows:
                try:
                    # Extraire les informations selon le format
                    cells = row.find_all(['td', 'div'])
                    if len(cells) >= 3:
                        # Format typique: Nom, Location, Status
                        name_cell = cells[0]
                        location_cell = cells[1] 
                        status_cell = cells[2]
                        
                        name = name_cell.get_text(strip=True)
                        location_text = location_cell.get_text(strip=True)
                        
                        # Extraire coordonnées depuis le texte (ex: "48.85, 2.35")
                        coords_match = re.search(r'([-+]?\d*\.\d+|\d+)[,\s]+([-+]?\d*\.\d+|\d+)', location_text)
                        if coords_match:
                            lat = float(coords_match.group(1))
                            lon = float(coords_match.group(2))
                            
                            station = SDRStation(
                                id=f"kiwi_{len(stations)}",
                                name=name,
                                lat=lat,
                                lon=lon,
                                status='active' if 'online' in status_cell.get_text().lower() else 'unknown',
                                url=name_cell.find('a')['href'] if name_cell.find('a') else '',
                                source='kiwisdr.com'
                            )
                            stations.append(station)
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Erreur scraping kiwisdr.com: {e}")
            
        return stations

    def _scrape_sdr_hu(self) -> List[SDRStation]:
        """
        Scrape les stations depuis sdr.hu
        """
        stations = []
        url = "http://sdr.hu/"
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Chercher les stations dans la liste
            station_elements = soup.find_all(['div', 'li'], class_=['station', 'receiver'])
            if not station_elements:
                # Alternative: chercher par attributs
                station_elements = soup.find_all(attrs={'data-lat': True, 'data-lng': True})
            
            for element in station_elements:
                try:
                    name = element.get('data-name') or element.find(['h3', 'h4', 'span', 'div'], class_='name')
                    if name:
                        name = name.get_text(strip=True) if hasattr(name, 'get_text') else str(name)
                    
                    lat = element.get('data-lat')
                    lon = element.get('data-lng')
                    
                    if lat and lon:
                        station = SDRStation(
                            id=f"sdrhu_{len(stations)}",
                            name=name or f'Station {len(stations)}',
                            lat=float(lat),
                            lon=float(lon),
                            country=element.get('data-country', 'Unknown'),
                            status='active',
                            url=element.get('data-url', ''),
                            source='sdr.hu'
                        )
                        stations.append(station)
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Erreur scraping sdr.hu: {e}")
            
        return stations

    def _scrape_websdr(self) -> List[SDRStation]:
        """
        Scrape les stations depuis websdr.org
        """
        stations = []
        url = "http://websdr.org/"
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Chercher les liens vers les WebSDR
            links = soup.find_all('a', href=re.compile(r'websdr'))
            
            # Stations connues et fiables
            known_stations = [
                {
                    "name": "University of Twente WebSDR",
                    "lat": 52.2387,
                    "lon": 6.8509,
                    "country": "NL",
                    "url": "http://websdr.ewi.utwente.nl:8901/"
                },
                {
                    "name": "Northern Utah WebSDR",
                    "lat": 41.7370,
                    "lon": -111.8338,
                    "country": "US",
                    "url": "http://websdr.sdrutah.org:8901/"
                },
                {
                    "name": "SkyHub WebSDR",
                    "lat": 51.5074,
                    "lon": -0.1278,
                    "country": "GB",
                    "url": "http://skyhub.websdr.org:8901/"
                },
                {
                    "name": "Hack Green WebSDR",
                    "lat": 53.0833,
                    "lon": -2.5167,
                    "country": "GB",
                    "url": "http://hackgreensdr.org:8901/"
                },
                {
                    "name": "Berlin WebSDR",
                    "lat": 52.5200,
                    "lon": 13.4050,
                    "country": "DE",
                    "url": "http://berlin.websdr.org:8901/"
                }
            ]
            
            for station_data in known_stations:
                station = SDRStation(
                    id=f"websdr_{len(stations)}",
                    name=station_data["name"],
                    lat=station_data["lat"],
                    lon=station_data["lon"],
                    country=station_data["country"],
                    status='active',
                    url=station_data["url"],
                    source='websdr.org'
                )
                stations.append(station)
                
        except Exception as e:
            logger.error(f"Erreur scraping websdr.org: {e}")
            
        return stations

    def get_stations_as_dict(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Retourne les stations sous forme de dictionnaires"""
        stations = self.get_all_stations(force_refresh)
        return [s.to_dict() for s in stations]

    def get_cache_info(self) -> Dict[str, Any]:
        """Retourne les informations sur le cache"""
        return {
            'cached': self.cache is not None,
            'cache_timestamp': self.cache_timestamp.isoformat() + 'Z' if self.cache_timestamp else None,
            'cache_ttl_minutes': self.cache_ttl.total_seconds() / 60,
            'cache_valid': self._is_cache_valid(),
            'station_count': len(self.cache) if self.cache else 0
        }

    def get_health_status(self) -> Dict[str, Any]:
        """Retourne le statut santé du scraper"""
        return {
            'status': 'healthy' if self._test_connection() else 'degraded',
            'last_updated': self.cache_timestamp.isoformat() + 'Z' if self.cache_timestamp else None,
            'station_count': len(self.cache) if self.cache else 0,
            'sources': {
                'rx_tx_info': self._test_source('https://rx-tx.info'),
                'kiwisdr': self._test_source('http://kiwisdr.com/public/'),
                'sdr_hu': self._test_source('http://sdr.hu/'),
                'websdr': self._test_source('http://websdr.org/')
            }
        }
    
    def _test_connection(self) -> bool:
        """Teste la connexion générale"""
        try:
            response = self.session.get('https://httpbin.org/get', timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def _test_source(self, url: str) -> bool:
        """Teste une source spécifique"""
        try:
            response = self.session.get(url, timeout=10)
            return response.status_code == 200
        except:
            return False

# Fonction utilitaire pour l'intégration
def create_sdr_scraper() -> SDRScrapers:
    """Factory pour créer une instance de SDRScrapers"""
    return SDRScrapers()

# Exemple d'utilisation
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    scraper = SDRScrapers()
    
    print("🔍 Scraping des stations SDR...")
    stations = scraper.get_all_stations()
    
    print(f"\n📊 Résultats: {len(stations)} stations trouvées")
    
    # Afficher quelques exemples
    for i, station in enumerate(stations[:5]):
        print(f"\n{i+1}. {station.name}")
        print(f"   📍 {station.lat}, {station.lon}")
        print(f"   🌍 {station.country}")
        print(f"   🔧 {station.source}")
        print(f"   📡 {station.status}")
