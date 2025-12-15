# Flask/geopol_data/connectors/open_meteo.py
"""
Connecteur pour l'API Open-Meteo
Récupération des données météorologiques et de qualité de l'air
Documentation: https://open-meteo.com/en/docs
"""

import requests
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

class OpenMeteoConfig:
    """Configuration Open-Meteo API"""
    
    # URLs de base (pas de clé API nécessaire)
    WEATHER_URL = "https://api.open-meteo.com/v1/forecast"
    AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
    
    # Timeout requêtes (API gratuite peut être lente)
    TIMEOUT = 15
    
    # Paramètres météo par défaut
    DEFAULT_WEATHER_PARAMS = [
        'temperature_2m',
        'precipitation',
        'windspeed_10m',
        'cloudcover',
        'surface_pressure'
    ]
    
    # Paramètres qualité de l'air
    DEFAULT_AIR_PARAMS = [
        'pm10',
        'pm2_5',
        'carbon_monoxide',
        'nitrogen_dioxide',
        'ozone'
    ]
    
    # Cache TTL (en heures)
    CACHE_TTL_HOURS = 6  # Données météo changent rapidement

# ============================================================================
# MODÈLES DE DONNÉES
# ============================================================================

@dataclass
class WeatherData:
    """Données météorologiques d'un point"""
    latitude: float
    longitude: float
    temperature: Optional[float] = None
    precipitation: Optional[float] = None
    wind_speed: Optional[float] = None
    cloud_cover: Optional[float] = None
    pressure: Optional[float] = None
    timestamp: datetime = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'latitude': self.latitude,
            'longitude': self.longitude,
            'temperature': self.temperature,
            'precipitation': self.precipitation,
            'wind_speed': self.wind_speed,
            'cloud_cover': self.cloud_cover,
            'pressure': self.pressure,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

@dataclass
class AirQualityData:
    """Données de qualité de l'air"""
    latitude: float
    longitude: float
    pm10: Optional[float] = None
    pm2_5: Optional[float] = None
    carbon_monoxide: Optional[float] = None
    nitrogen_dioxide: Optional[float] = None
    ozone: Optional[float] = None
    aqi: Optional[int] = None  # Air Quality Index calculé
    timestamp: datetime = None
    
    def calculate_aqi(self) -> int:
        """
        Calcule un AQI simplifié (0-500)
        Basé sur PM2.5 (principal indicateur)
        """
        if self.pm2_5 is None:
            return None
        
        # Table de conversion PM2.5 → AQI (EPA)
        if self.pm2_5 <= 12.0:
            return int((50 / 12.0) * self.pm2_5)
        elif self.pm2_5 <= 35.4:
            return int(50 + ((100 - 50) / (35.4 - 12.1)) * (self.pm2_5 - 12.1))
        elif self.pm2_5 <= 55.4:
            return int(100 + ((150 - 100) / (55.4 - 35.5)) * (self.pm2_5 - 35.5))
        elif self.pm2_5 <= 150.4:
            return int(150 + ((200 - 150) / (150.4 - 55.5)) * (self.pm2_5 - 55.5))
        elif self.pm2_5 <= 250.4:
            return int(200 + ((300 - 200) / (250.4 - 150.5)) * (self.pm2_5 - 150.5))
        else:
            return min(500, int(300 + ((500 - 300) / (500.4 - 250.5)) * (self.pm2_5 - 250.5)))
    
    def get_aqi_level(self) -> str:
        """Retourne le niveau de qualité de l'air (Good, Moderate, etc.)"""
        aqi = self.aqi or self.calculate_aqi()
        if aqi is None:
            return 'UNKNOWN'
        elif aqi <= 50:
            return 'GOOD'
        elif aqi <= 100:
            return 'MODERATE'
        elif aqi <= 150:
            return 'UNHEALTHY_SENSITIVE'
        elif aqi <= 200:
            return 'UNHEALTHY'
        elif aqi <= 300:
            return 'VERY_UNHEALTHY'
        else:
            return 'HAZARDOUS'
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'latitude': self.latitude,
            'longitude': self.longitude,
            'pm10': self.pm10,
            'pm2_5': self.pm2_5,
            'carbon_monoxide': self.carbon_monoxide,
            'nitrogen_dioxide': self.nitrogen_dioxide,
            'ozone': self.ozone,
            'aqi': self.aqi or self.calculate_aqi(),
            'aqi_level': self.get_aqi_level(),
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

# ============================================================================
# CLASSE PRINCIPALE : OPEN-METEO CONNECTOR
# ============================================================================

class OpenMeteoConnector:
    """
    Connecteur pour l'API Open-Meteo
    Gère les requêtes météo et qualité de l'air
    """
    
    def __init__(self):
        self.weather_url = OpenMeteoConfig.WEATHER_URL
        self.air_quality_url = OpenMeteoConfig.AIR_QUALITY_URL
        self.timeout = OpenMeteoConfig.TIMEOUT
        
        # Session HTTP réutilisable
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GEOPOL-Analytics/1.0',
            'Accept': 'application/json'
        })
        
        # Cache simple en mémoire
        self._cache = {}
        self._cache_ttl = timedelta(hours=OpenMeteoConfig.CACHE_TTL_HOURS)
        
        logger.info("OpenMeteoConnector initialisé")
    
    # ========================================================================
    # MÉTHODE PRINCIPALE : Fetch Weather
    # ========================================================================
    
    def fetch_weather(self, latitude: float, longitude: float) -> Optional[WeatherData]:
        """
        Récupère les données météorologiques pour des coordonnées GPS
        
        Args:
            latitude: Latitude (ex: 48.8566 pour Paris)
            longitude: Longitude (ex: 2.3522 pour Paris)
        
        Returns:
            WeatherData ou None si erreur
        
        Example:
            >>> connector = OpenMeteoConnector()
            >>> weather = connector.fetch_weather(48.8566, 2.3522)
            >>> print(f"Température: {weather.temperature}°C")
        """
        # Vérifier le cache
        cache_key = f"weather_{latitude}_{longitude}"
        cached = self._get_from_cache(cache_key)
        if cached:
            logger.debug(f"✓ Cache hit météo: {latitude}, {longitude}")
            return cached
        
        logger.info(f"Requête météo Open-Meteo: {latitude}, {longitude}")
        
        # Paramètres de la requête
        params = {
            'latitude': latitude,
            'longitude': longitude,
            'current': ','.join(OpenMeteoConfig.DEFAULT_WEATHER_PARAMS),
            'timezone': 'auto'
        }
        
        try:
            response = self.session.get(
                self.weather_url,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Parser la réponse
            weather = self._parse_weather_response(data, latitude, longitude)
            
            if weather:
                # Mettre en cache
                self._put_in_cache(cache_key, weather)
                logger.info(f"✅ Météo récupérée: {weather.temperature}°C")
                return weather
            else:
                logger.warning("⚠️ Réponse météo invalide")
                return None
                
        except requests.Timeout:
            logger.error(f"⏱️ Timeout météo pour {latitude}, {longitude}")
            return None
        except requests.RequestException as e:
            logger.error(f"❌ Erreur réseau météo: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Erreur inattendue météo: {e}")
            return None
    
    # ========================================================================
    # MÉTHODE : Fetch Air Quality
    # ========================================================================
    
    def fetch_air_quality(self, latitude: float, longitude: float) -> Optional[AirQualityData]:
        """
        Récupère les données de qualité de l'air
        
        Args:
            latitude: Latitude
            longitude: Longitude
        
        Returns:
            AirQualityData ou None si erreur
        """
        # Vérifier le cache
        cache_key = f"air_{latitude}_{longitude}"
        cached = self._get_from_cache(cache_key)
        if cached:
            logger.debug(f"✓ Cache hit qualité air: {latitude}, {longitude}")
            return cached
        
        logger.info(f"Requête qualité air Open-Meteo: {latitude}, {longitude}")
        
        params = {
            'latitude': latitude,
            'longitude': longitude,
            'current': ','.join(OpenMeteoConfig.DEFAULT_AIR_PARAMS),
            'timezone': 'auto'
        }
        
        try:
            response = self.session.get(
                self.air_quality_url,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Parser la réponse
            air_quality = self._parse_air_quality_response(data, latitude, longitude)
            
            if air_quality:
                # Calculer l'AQI
                air_quality.aqi = air_quality.calculate_aqi()
                
                # Mettre en cache
                self._put_in_cache(cache_key, air_quality)
                logger.info(f"✅ Qualité air récupérée: PM2.5={air_quality.pm2_5}, AQI={air_quality.aqi}")
                return air_quality
            else:
                logger.warning("⚠️ Réponse qualité air invalide")
                return None
                
        except requests.Timeout:
            logger.error(f"⏱️ Timeout qualité air pour {latitude}, {longitude}")
            return None
        except requests.RequestException as e:
            logger.error(f"❌ Erreur réseau qualité air: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Erreur inattendue qualité air: {e}")
            return None
    
    # ========================================================================
    # MÉTHODES PRIVÉES : Parsing
    # ========================================================================
    
    def _parse_weather_response(self, data: Dict[str, Any], 
                                latitude: float, longitude: float) -> Optional[WeatherData]:
        """Parse la réponse JSON Open-Meteo (météo)"""
        try:
            current = data.get('current', {})
            
            weather = WeatherData(
                latitude=latitude,
                longitude=longitude,
                temperature=current.get('temperature_2m'),
                precipitation=current.get('precipitation'),
                wind_speed=current.get('windspeed_10m'),
                cloud_cover=current.get('cloudcover'),
                pressure=current.get('surface_pressure'),
                timestamp=datetime.utcnow()
            )
            
            return weather
            
        except Exception as e:
            logger.error(f"Erreur parsing météo: {e}")
            return None
    
    def _parse_air_quality_response(self, data: Dict[str, Any],
                                   latitude: float, longitude: float) -> Optional[AirQualityData]:
        """Parse la réponse JSON Open-Meteo (qualité air)"""
        try:
            current = data.get('current', {})
            
            air_quality = AirQualityData(
                latitude=latitude,
                longitude=longitude,
                pm10=current.get('pm10'),
                pm2_5=current.get('pm2_5'),
                carbon_monoxide=current.get('carbon_monoxide'),
                nitrogen_dioxide=current.get('nitrogen_dioxide'),
                ozone=current.get('ozone'),
                timestamp=datetime.utcnow()
            )
            
            return air_quality
            
        except Exception as e:
            logger.error(f"Erreur parsing qualité air: {e}")
            return None
    
    # ========================================================================
    # MÉTHODES PRIVÉES : Cache
    # ========================================================================
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Récupère depuis le cache si valide"""
        if key not in self._cache:
            return None
        
        data, cached_at = self._cache[key]
        
        # Vérifier si expiré
        if datetime.utcnow() - cached_at > self._cache_ttl:
            del self._cache[key]
            return None
        
        return data
    
    def _put_in_cache(self, key: str, data: Any):
        """Met en cache"""
        self._cache[key] = (data, datetime.utcnow())
    
    def clear_cache(self):
        """Vide le cache"""
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"Cache Open-Meteo vidé: {count} entrées")
    
    # ========================================================================
    # MÉTHODES UTILITAIRES
    # ========================================================================
    
    def test_connection(self) -> bool:
        """Teste la connexion à l'API Open-Meteo"""
        try:
            logger.info("Test connexion Open-Meteo...")
            
            # Test simple sur Paris
            weather = self.fetch_weather(48.8566, 2.3522)
            
            if weather and weather.temperature is not None:
                logger.info(f"✅ Connexion Open-Meteo OK (Paris: {weather.temperature}°C)")
                return True
            else:
                logger.error("❌ Réponse Open-Meteo invalide")
                return False
                
        except Exception as e:
            logger.error(f"❌ Connexion Open-Meteo échouée: {e}")
            return False
    
    def fetch_complete_data(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Récupère météo + qualité air en une seule fois
        
        Returns:
            Dict avec weather et air_quality
        """
        return {
            'weather': self.fetch_weather(latitude, longitude),
            'air_quality': self.fetch_air_quality(latitude, longitude),
            'timestamp': datetime.utcnow().isoformat()
        }

# ============================================================================
# FONCTION HELPER
# ============================================================================

def get_weather_for_country(country_code: str) -> Optional[Dict[str, Any]]:
    """
    Récupère la météo pour la capitale d'un pays
    Utilise CAPITALS_GPS depuis constants.py
    
    Args:
        country_code: Code ISO du pays (ex: 'FR')
    
    Returns:
        Dict avec météo et qualité air
    """
    try:
        from ..constants import CAPITALS_GPS
        
        # Récupérer les coordonnées
        coords = CAPITALS_GPS.get(country_code)
        if not coords:
            logger.warning(f"Coordonnées inconnues pour {country_code}")
            return None
        
        latitude, longitude = coords
        
        # Récupérer les données
        connector = OpenMeteoConnector()
        return connector.fetch_complete_data(latitude, longitude)
        
    except Exception as e:
        logger.error(f"Erreur météo pays {country_code}: {e}")
        return None

# ============================================================================
# EXEMPLE D'UTILISATION
# ============================================================================

if __name__ == '__main__':
    import json
    
    # Configuration logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 70)
    print("TEST OPEN-METEO CONNECTOR")
    print("=" * 70)
    
    connector = OpenMeteoConnector()
    
    # Test 1: Connexion
    print("\n1. Test connexion...")
    if connector.test_connection():
        print("✅ API accessible")
    else:
        print("❌ API inaccessible")
        exit(1)
    
    # Test 2: Météo Paris
    print("\n2. Météo Paris...")
    weather = connector.fetch_weather(48.8566, 2.3522)
    if weather:
        print(json.dumps(weather.to_dict(), indent=2, ensure_ascii=False))
    
    # Test 3: Qualité air Paris
    print("\n3. Qualité air Paris...")
    air = connector.fetch_air_quality(48.8566, 2.3522)
    if air:
        print(json.dumps(air.to_dict(), indent=2, ensure_ascii=False))
    
    # Test 4: Données complètes
    print("\n4. Données complètes (météo + air)...")
    complete = connector.fetch_complete_data(48.8566, 2.3522)
    print(f"Température: {complete['weather'].temperature}°C")
    print(f"AQI: {complete['air_quality'].aqi} ({complete['air_quality'].get_aqi_level()})")
    
    print("\n" + "=" * 70)
    print("TESTS TERMINÉS")
    print("=" * 70)
