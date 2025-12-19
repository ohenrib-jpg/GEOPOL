# Flask/geopol_data/connectors/earthquake_usgs.py
"""
Connecteur pour l'API USGS Earthquake
Récupération des données sismiques en temps réel
Documentation: https://earthquake.usgs.gov/earthquakes/feed/v1.0/geojson.php
"""

import requests
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

class USGSConfig:
    """Configuration USGS Earthquake API"""

    # URL de base (API query pour filtrage avancé)
    BASE_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"

    # URL feeds pré-filtrés (plus rapides)
    FEEDS = {
        'significant_month': 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_month.geojson',
        'all_hour': 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson',
        'all_day': 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson',
        'all_week': 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_week.geojson',
        '2.5_day': 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson',
        '4.5_week': 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_week.geojson',
    }

    # Timeout requêtes
    TIMEOUT = 15

    # Cache TTL (en minutes)
    CACHE_TTL_MINUTES = 5  # Données sismiques changent rapidement

# ============================================================================
# MODÈLES DE DONNÉES
# ============================================================================

@dataclass
class Earthquake:
    """Données d'un séisme"""
    id: str
    magnitude: float
    place: str
    time: datetime
    latitude: float
    longitude: float
    depth: float  # Profondeur en km
    url: str
    tsunami: bool = False
    status: str = "automatic"
    type: str = "earthquake"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'magnitude': self.magnitude,
            'place': self.place,
            'time': self.time.isoformat() if self.time else None,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'depth': self.depth,
            'url': self.url,
            'tsunami': self.tsunami,
            'status': self.status,
            'type': self.type
        }

    def get_magnitude_category(self) -> str:
        """Retourne la catégorie de magnitude"""
        if self.magnitude < 3.0:
            return 'MINOR'  # Mineur
        elif self.magnitude < 5.0:
            return 'LIGHT'  # Léger
        elif self.magnitude < 6.0:
            return 'MODERATE'  # Modéré
        elif self.magnitude < 7.0:
            return 'STRONG'  # Fort
        elif self.magnitude < 8.0:
            return 'MAJOR'  # Majeur
        else:
            return 'GREAT'  # Catastrophique

    def get_depth_category(self) -> str:
        """Retourne la catégorie de profondeur"""
        if self.depth < 70:
            return 'SHALLOW'  # Peu profond (plus destructeur)
        elif self.depth < 300:
            return 'INTERMEDIATE'  # Intermédiaire
        else:
            return 'DEEP'  # Profond

# ============================================================================
# CLASSE PRINCIPALE : USGS EARTHQUAKE CONNECTOR
# ============================================================================

class USGSEarthquakeConnector:
    """
    Connecteur pour l'API USGS Earthquake
    Gère les requêtes de données sismiques en temps réel
    """

    def __init__(self):
        self.base_url = USGSConfig.BASE_URL
        self.feeds = USGSConfig.FEEDS
        self.timeout = USGSConfig.TIMEOUT

        # Session HTTP réutilisable
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GEOPOL-Analytics/1.0',
            'Accept': 'application/json'
        })

        # Cache simple en mémoire
        self._cache = {}
        self._cache_ttl = timedelta(minutes=USGSConfig.CACHE_TTL_MINUTES)

        logger.info("USGSEarthquakeConnector initialisé")

    # ========================================================================
    # MÉTHODE PRINCIPALE : Fetch Earthquakes
    # ========================================================================

    def fetch_earthquakes(self,
                         min_magnitude: float = 4.5,
                         time_period: str = 'week',
                         max_results: int = 100) -> List[Earthquake]:
        """
        Récupère les séismes selon des critères

        Args:
            min_magnitude: Magnitude minimale (1.0 à 10.0)
            time_period: Période ('hour', 'day', 'week', 'month')
            max_results: Nombre maximum de résultats

        Returns:
            Liste d'objets Earthquake
        """
        # Vérifier le cache
        cache_key = f"eq_{min_magnitude}_{time_period}_{max_results}"
        cached = self._get_from_cache(cache_key)
        if cached:
            logger.debug(f"✓ Cache hit séismes: {cache_key}")
            return cached

        logger.info(f"Requête USGS: magnitude ≥ {min_magnitude}, période: {time_period}")

        # Calculer la date de début selon la période
        now = datetime.utcnow()
        if time_period == 'hour':
            start_time = now - timedelta(hours=1)
        elif time_period == 'day':
            start_time = now - timedelta(days=1)
        elif time_period == 'week':
            start_time = now - timedelta(weeks=1)
        elif time_period == 'month':
            start_time = now - timedelta(days=30)
        else:
            start_time = now - timedelta(weeks=1)  # Par défaut: semaine

        # Paramètres de la requête
        params = {
            'format': 'geojson',
            'starttime': start_time.strftime('%Y-%m-%d'),
            'minmagnitude': min_magnitude,
            'limit': max_results,
            'orderby': 'time-asc'
        }

        try:
            response = self.session.get(
                self.base_url,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()

            # Parser la réponse GeoJSON
            earthquakes = self._parse_geojson_response(data)

            # Mettre en cache
            self._put_in_cache(cache_key, earthquakes)

            logger.info(f"✅ {len(earthquakes)} séismes récupérés (mag ≥ {min_magnitude})")
            return earthquakes

        except requests.Timeout:
            logger.error(f"⏱️ Timeout USGS")
            return []
        except requests.RequestException as e:
            logger.error(f"❌ Erreur réseau USGS: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ Erreur inattendue USGS: {e}")
            return []

    def fetch_earthquakes_by_feed(self, feed_name: str) -> List[Earthquake]:
        """
        Récupère les séismes depuis un feed pré-filtré (plus rapide)

        Args:
            feed_name: Nom du feed ('all_day', '4.5_week', etc.)

        Returns:
            Liste d'objets Earthquake
        """
        if feed_name not in self.feeds:
            logger.error(f"Feed inconnu: {feed_name}")
            return []

        # Vérifier le cache
        cache_key = f"feed_{feed_name}"
        cached = self._get_from_cache(cache_key)
        if cached:
            logger.debug(f"✓ Cache hit feed: {feed_name}")
            return cached

        logger.info(f"Requête USGS feed: {feed_name}")

        try:
            response = self.session.get(
                self.feeds[feed_name],
                timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()

            # Parser la réponse GeoJSON
            earthquakes = self._parse_geojson_response(data)

            # Mettre en cache
            self._put_in_cache(cache_key, earthquakes)

            logger.info(f"✅ {len(earthquakes)} séismes récupérés (feed: {feed_name})")
            return earthquakes

        except Exception as e:
            logger.error(f"❌ Erreur feed {feed_name}: {e}")
            return []

    # ========================================================================
    # MÉTHODES PRIVÉES : Parsing
    # ========================================================================

    def _parse_geojson_response(self, data: Dict[str, Any]) -> List[Earthquake]:
        """Parse la réponse GeoJSON USGS"""
        earthquakes = []

        try:
            features = data.get('features', [])

            for feature in features:
                try:
                    props = feature.get('properties', {})
                    geom = feature.get('geometry', {})
                    coords = geom.get('coordinates', [])

                    if len(coords) < 3:
                        continue

                    # Créer l'objet Earthquake
                    earthquake = Earthquake(
                        id=feature.get('id', ''),
                        magnitude=props.get('mag', 0.0),
                        place=props.get('place', 'Unknown location'),
                        time=datetime.utcfromtimestamp(props.get('time', 0) / 1000),
                        longitude=coords[0],
                        latitude=coords[1],
                        depth=coords[2] if len(coords) > 2 else 0.0,
                        url=props.get('url', ''),
                        tsunami=props.get('tsunami', 0) == 1,
                        status=props.get('status', 'automatic'),
                        type=props.get('type', 'earthquake')
                    )

                    earthquakes.append(earthquake)

                except Exception as e:
                    logger.warning(f"Erreur parsing séisme: {e}")
                    continue

            return earthquakes

        except Exception as e:
            logger.error(f"Erreur parsing GeoJSON: {e}")
            return []

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
        logger.info(f"Cache USGS vidé: {count} entrées")

    # ========================================================================
    # MÉTHODES UTILITAIRES
    # ========================================================================

    def test_connection(self) -> bool:
        """Teste la connexion à l'API USGS"""
        try:
            logger.info("Test connexion USGS...")

            # Récupérer les séismes de la dernière heure
            earthquakes = self.fetch_earthquakes_by_feed('all_hour')

            if earthquakes is not None:
                logger.info(f"✅ Connexion USGS OK ({len(earthquakes)} séismes dernière heure)")
                return True
            else:
                logger.error("❌ Réponse USGS invalide")
                return False

        except Exception as e:
            logger.error(f"❌ Connexion USGS échouée: {e}")
            return False

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
    print("TEST USGS EARTHQUAKE CONNECTOR")
    print("=" * 70)

    connector = USGSEarthquakeConnector()

    # Test 1: Connexion
    print("\n1. Test connexion...")
    if connector.test_connection():
        print("✅ API accessible")
    else:
        print("❌ API inaccessible")
        exit(1)

    # Test 2: Séismes magnitude 4.5+ dernière semaine
    print("\n2. Séismes magnitude ≥ 4.5 (dernière semaine)...")
    earthquakes = connector.fetch_earthquakes(min_magnitude=4.5, time_period='week', max_results=20)

    print(f"\nNombre de séismes: {len(earthquakes)}\n")

    for eq in earthquakes[:5]:  # Afficher les 5 premiers
        print(f"Magnitude {eq.magnitude} - {eq.place}")
        print(f"  • Date: {eq.time.strftime('%Y-%m-%d %H:%M UTC')}")
        print(f"  • Position: {eq.latitude}, {eq.longitude}")
        print(f"  • Profondeur: {eq.depth} km ({eq.get_depth_category()})")
        print(f"  • Catégorie: {eq.get_magnitude_category()}")
        print(f"  • Tsunami: {'Oui' if eq.tsunami else 'Non'}")
        print(f"  • URL: {eq.url}")
        print()

    print("=" * 70)
    print("TESTS TERMINÉS")
    print("=" * 70)
