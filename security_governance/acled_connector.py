"""
Connecteur ACLED (Armed Conflict Location & Event Data)
API gratuite pour données de conflits, violences et manifestations

Documentation: https://apidocs.acleddata.com/
Inscription gratuite: https://developer.acleddata.com/

Types d'événements:
- Battles (combats)
- Explosions/Remote violence
- Violence against civilians
- Protests (manifestations)
- Riots (émeutes)
- Strategic developments
"""

import sys
if sys.platform == 'win32':
    import codecs
    # Vérifier si buffer existe avant de wrapper (éviter le double-wrapping)
    if hasattr(sys.stdout, 'buffer') and not isinstance(sys.stdout, codecs.StreamWriter):
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'ignore')
    if hasattr(sys.stderr, 'buffer') and not isinstance(sys.stderr, codecs.StreamWriter):
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'ignore')

import requests
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import os
from collections import defaultdict

logger = logging.getLogger(__name__)


class ACLEDConnector:
    """
    Connecteur pour l'API ACLED
    Récupère données de conflits et événements sécuritaires
    """

    BASE_URL = "https://acleddata.com/api/acled/read"
    AUTH_URL = "https://acleddata.com/oauth/token"

    # Types d'événements ACLED
    EVENT_TYPES = {
        'battles': 'Battles',
        'explosions': 'Explosions/Remote violence',
        'violence_civilians': 'Violence against civilians',
        'protests': 'Protests',
        'riots': 'Riots',
        'strategic': 'Strategic developments'
    }

    # Codes ISO pays (exemples - mappés aux noms ACLED)
    COUNTRY_MAPPING = {
        'SYR': 'Syria',
        'IRQ': 'Iraq',
        'AFG': 'Afghanistan',
        'YEM': 'Yemen',
        'LBY': 'Libya',
        'UKR': 'Ukraine',
        'RUS': 'Russia',
        'ISR': 'Israel',
        'PSE': 'Palestine',
        'MLI': 'Mali',
        'NGA': 'Nigeria',
        'SOM': 'Somalia',
        'SDN': 'Sudan',
        'COD': 'Democratic Republic of Congo',
        'ETH': 'Ethiopia',
        'BFA': 'Burkina Faso',
        'MMR': 'Myanmar'
    }

    def __init__(self, email: str = None, password: str = None, db_manager=None, api_key: str = None):
        """
        Initialise le connecteur ACLED

        Args:
            email: Email enregistré ACLED (ou via env ACLED_EMAIL ou DB)
            password: Mot de passe ACLED (ou via env ACLED_PASSWORD ou DB)
            db_manager: DatabaseManager pour récupérer clés depuis DB
            api_key: [DEPRECATED] Ancienne clé API (rétro-compatibilité)
        """
        # Essayer de récupérer depuis le manager de clés en priorité
        if db_manager and not email and not password:
            try:
                from ..api_keys_manager import get_api_keys_manager
                keys_manager = get_api_keys_manager(db_manager)
                credentials = keys_manager.get_api_key('acled')

                if credentials:
                    self.email = credentials.get('email')
                    self.password = credentials.get('password')
                    logger.info("[OK] ACLED credentials loaded from database")
                else:
                    # Fallback sur variables d'environnement
                    self.email = os.getenv('ACLED_EMAIL')
                    self.password = os.getenv('ACLED_PASSWORD')
                    logger.info("ℹ ACLED credentials from environment variables")
            except Exception as e:
                logger.warning(f"[WARN] Could not load ACLED from DB, using env: {e}")
                self.email = os.getenv('ACLED_EMAIL')
                self.password = os.getenv('ACLED_PASSWORD')
        else:
            # Utiliser les paramètres fournis ou env vars
            self.email = email or os.getenv('ACLED_EMAIL')
            self.password = password or os.getenv('ACLED_PASSWORD')

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GEOPOL-Analytics/1.0',
            'Accept': 'application/json'
        })

        # OAuth2 token management
        self._access_token = None
        self._token_expiry = None

        # Cache simple (pas de Redis pour l'instant)
        self._cache = {}
        self._cache_ttl = 3600  # 1 heure

    def _get_oauth_token(self) -> Optional[str]:
        """
        Obtient un access token OAuth2 depuis ACLED
        Le token est valide 24 heures

        Returns:
            Access token ou None
        """
        # Vérifier si on a déjà un token valide
        if self._access_token and self._token_expiry:
            if datetime.now() < self._token_expiry:
                logger.debug("[OK] Token ACLED encore valide")
                return self._access_token

        # Vérifier credentials
        if not self.email or not self.password:
            logger.error("[ERROR] ACLED credentials manquants (EMAIL et PASSWORD requis)")
            return None

        try:
            logger.info("🔐 Obtention token OAuth2 ACLED...")

            # Requête OAuth2
            data = {
                'username': self.email,
                'password': self.password,
                'grant_type': 'password',
                'client_id': 'acled'
            }

            response = requests.post(
                self.AUTH_URL,
                data=data,
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'application/json'
                },
                timeout=30
            )

            response.raise_for_status()
            token_data = response.json()
            logger.debug(f"[DEBUG] Token response: {token_data.keys()}")

            # Extraire token et expiry
            self._access_token = token_data.get('access_token')
            expires_in = token_data.get('expires_in', 86400)  # 24h par défaut

            # Calculer expiry (on retire 5 min pour sécurité)
            self._token_expiry = datetime.now() + timedelta(seconds=expires_in - 300)

            logger.info(f"[OK] Token ACLED obtenu (expire dans {expires_in}s)")
            return self._access_token

        except requests.exceptions.HTTPError as e:
            logger.error(f"[ERROR] HTTP error lors auth ACLED: {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"   Response: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"[ERROR] Erreur obtention token ACLED: {e}")
            return None

    def _make_request(self, params: Dict) -> Optional[Dict]:
        """
        Effectue une requête à l'API ACLED avec OAuth2

        Args:
            params: Paramètres de la requête

        Returns:
            Réponse JSON ou None
        """
        # Obtenir token OAuth2
        token = self._get_oauth_token()
        if not token:
            logger.error("[ERROR] Impossible d'obtenir token ACLED")
            return None

        # Ajouter le format JSON par défaut
        params['_format'] = 'json'

        try:
            logger.debug(f"📡 Requête ACLED: {params}")

            # Requête avec Bearer token (comme dans la documentation)
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            logger.debug(f"[DEBUG] Request headers: { {k: v[:20] + '...' if k == 'Authorization' and len(v) > 20 else v for k, v in headers.items()} }")
            logger.debug(f"[DEBUG] Request URL: {self.BASE_URL}")
            logger.debug(f"[DEBUG] Request params: {params}")

            response = self.session.get(
                self.BASE_URL,
                params=params,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            logger.debug(f"[DEBUG] ACLED response keys: {list(data.keys())}")

            # Vérifier succès selon la documentation (status == 200) ou champ success
            if data.get('status') == 200 or data.get('success'):
                count = data.get('count', 0)
                logger.debug(f"[OK] ACLED: {count} événements récupérés")
                return data
            else:
                error_msg = data.get('error') or data.get('message') or 'Unknown error'
                logger.error(f"[ERROR] ACLED error: {error_msg}")
                logger.debug(f"[DEBUG] Full response: {data}")
                return None

        except requests.exceptions.HTTPError as e:
            logger.error(f"[ERROR] HTTP error ACLED: {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"   Response: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"[ERROR] Erreur ACLED: {e}")
            return None

    def get_recent_events(self, days: int = 7, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Récupère les événements récents

        Args:
            days: Nombre de jours en arrière
            limit: Nombre max d'événements

        Returns:
            Liste d'événements
        """
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            end_date = datetime.now().strftime('%Y-%m-%d')

            params = {
                'event_date': f"{start_date}|{end_date}",
                'event_date_where': 'BETWEEN',
                'limit': limit
            }

            data = self._make_request(params)

            if not data or not data.get('data'):
                return []

            events = self._format_events(data['data'])

            logger.info(f"[OK] ACLED: {len(events)} événements récents récupérés")
            return events

        except Exception as e:
            logger.error(f"[ERROR] Erreur get_recent_events: {e}")
            return []

    def get_events_by_country(self, country_code: str, days: int = 30,
                              limit: int = 100) -> List[Dict[str, Any]]:
        """
        Récupère événements pour un pays

        Args:
            country_code: Code ISO pays (ex: 'SYR', 'UKR')
            days: Période en jours
            limit: Nombre max d'événements

        Returns:
            Liste d'événements
        """
        try:
            country_name = self.COUNTRY_MAPPING.get(country_code, country_code)

            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            end_date = datetime.now().strftime('%Y-%m-%d')

            params = {
                'country': country_name,
                'event_date': f"{start_date}|{end_date}",
                'event_date_where': 'BETWEEN',
                'limit': limit
            }

            data = self._make_request(params)

            if not data or not data.get('data'):
                return []

            events = self._format_events(data['data'])

            logger.info(f"[OK] ACLED {country_name}: {len(events)} événements")
            return events

        except Exception as e:
            logger.error(f"[ERROR] Erreur get_events_by_country: {e}")
            return []

    def get_conflicts(self, days: int = 7, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Récupère les conflits armés (Battles)

        Args:
            days: Période en jours
            limit: Nombre max d'événements

        Returns:
            Liste de conflits
        """
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            end_date = datetime.now().strftime('%Y-%m-%d')

            params = {
                'event_type': 'Battles',
                'event_date': f"{start_date}|{end_date}",
                'event_date_where': 'BETWEEN',
                'limit': limit
            }

            data = self._make_request(params)

            if not data or not data.get('data'):
                return []

            events = self._format_events(data['data'])

            logger.info(f"[OK] ACLED Conflicts: {len(events)} combats")
            return events

        except Exception as e:
            logger.error(f"[ERROR] Erreur get_conflicts: {e}")
            return []

    def get_terrorism_events(self, days: int = 7, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Récupère événements terroristes (Explosions/Remote violence)

        Args:
            days: Période en jours
            limit: Nombre max d'événements

        Returns:
            Liste d'événements terroristes
        """
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            end_date = datetime.now().strftime('%Y-%m-%d')

            params = {
                'event_type': 'Explosions/Remote violence',
                'event_date': f"{start_date}|{end_date}",
                'event_date_where': 'BETWEEN',
                'limit': limit
            }

            data = self._make_request(params)

            if not data or not data.get('data'):
                return []

            events = self._format_events(data['data'])

            logger.info(f"[OK] ACLED Terrorism: {len(events)} événements")
            return events

        except Exception as e:
            logger.error(f"[ERROR] Erreur get_terrorism_events: {e}")
            return []

    def get_protests(self, days: int = 7, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Récupère manifestations

        Args:
            days: Période en jours
            limit: Nombre max d'événements

        Returns:
            Liste de manifestations
        """
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            end_date = datetime.now().strftime('%Y-%m-%d')

            params = {
                'event_type': 'Protests',
                'event_date': f"{start_date}|{end_date}",
                'event_date_where': 'BETWEEN',
                'limit': limit
            }

            data = self._make_request(params)

            if not data or not data.get('data'):
                return []

            events = self._format_events(data['data'])

            logger.info(f"[OK] ACLED Protests: {len(events)} manifestations")
            return events

        except Exception as e:
            logger.error(f"[ERROR] Erreur get_protests: {e}")
            return []

    def get_violence_civilians(self, days: int = 7, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Récupère violences contre civils

        Args:
            days: Période en jours
            limit: Nombre max d'événements

        Returns:
            Liste de violences
        """
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            end_date = datetime.now().strftime('%Y-%m-%d')

            params = {
                'event_type': 'Violence against civilians',
                'event_date': f"{start_date}|{end_date}",
                'event_date_where': 'BETWEEN',
                'limit': limit
            }

            data = self._make_request(params)

            if not data or not data.get('data'):
                return []

            events = self._format_events(data['data'])

            logger.info(f"[OK] ACLED Violence: {len(events)} événements")
            return events

        except Exception as e:
            logger.error(f"[ERROR] Erreur get_violence_civilians: {e}")
            return []

    def get_security_summary(self, days: int = 7) -> Dict[str, Any]:
        """
        Résumé sécuritaire global

        Args:
            days: Période en jours

        Returns:
            Statistiques agrégées
        """
        try:
            logger.info(f"[SEARCH] Récupération résumé sécuritaire ACLED ({days} jours)...")

            # Récupérer tous les événements récents
            events = self.get_recent_events(days=days, limit=500)

            if not events:
                return {
                    'success': False,
                    'total_events': 0,
                    'message': 'Aucun événement récupéré'
                }

            # Agréger par type
            by_type = defaultdict(int)
            by_country = defaultdict(int)
            fatalities = 0

            for event in events:
                by_type[event['event_type']] += 1
                by_country[event['country']] += 1
                fatalities += event.get('fatalities', 0)

            # Top pays
            top_countries = sorted(
                [{'country': k, 'count': v} for k, v in by_country.items()],
                key=lambda x: x['count'],
                reverse=True
            )[:10]

            # Top types
            top_types = sorted(
                [{'type': k, 'count': v} for k, v in by_type.items()],
                key=lambda x: x['count'],
                reverse=True
            )

            summary = {
                'success': True,
                'period_days': days,
                'total_events': len(events),
                'total_fatalities': fatalities,
                'by_type': top_types,
                'top_countries': top_countries,
                'updated_at': datetime.now().isoformat()
            }

            logger.info(f"[OK] Résumé: {len(events)} événements, {fatalities} victimes")

            return summary

        except Exception as e:
            logger.error(f"[ERROR] Erreur get_security_summary: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_hotspots(self, days: int = 7, min_events: int = 5) -> List[Dict[str, Any]]:
        """
        Identifie les hotspots (zones de forte activité)

        Args:
            days: Période en jours
            min_events: Nombre min d'événements pour qualifier de hotspot

        Returns:
            Liste de hotspots
        """
        try:
            events = self.get_recent_events(days=days, limit=500)

            # Agréger par pays
            country_stats = defaultdict(lambda: {
                'events': 0,
                'fatalities': 0,
                'types': set()
            })

            for event in events:
                country = event['country']
                country_stats[country]['events'] += 1
                country_stats[country]['fatalities'] += event.get('fatalities', 0)
                country_stats[country]['types'].add(event['event_type'])

            # Filtrer et trier
            hotspots = []
            for country, stats in country_stats.items():
                if stats['events'] >= min_events:
                    hotspots.append({
                        'country': country,
                        'event_count': stats['events'],
                        'fatalities': stats['fatalities'],
                        'event_types': list(stats['types']),
                        'severity': 'high' if stats['fatalities'] > 50 else 'medium' if stats['fatalities'] > 10 else 'low'
                    })

            hotspots.sort(key=lambda x: x['event_count'], reverse=True)

            logger.info(f"[OK] {len(hotspots)} hotspots identifiés")

            return hotspots

        except Exception as e:
            logger.error(f"[ERROR] Erreur get_hotspots: {e}")
            return []

    def _format_events(self, raw_events: List[Dict]) -> List[Dict[str, Any]]:
        """
        Formate les événements ACLED au format GEOPOL

        Args:
            raw_events: Événements bruts ACLED

        Returns:
            Événements formatés
        """
        formatted = []

        for event in raw_events:
            try:
                formatted.append({
                    'id': f"acled_{event.get('data_id', '')}",
                    'event_type': event.get('event_type'),
                    'sub_event_type': event.get('sub_event_type'),
                    'country': event.get('country'),
                    'region': event.get('region'),
                    'location': event.get('location'),
                    'latitude': float(event.get('latitude', 0)),
                    'longitude': float(event.get('longitude', 0)),
                    'date': event.get('event_date'),
                    'fatalities': int(event.get('fatalities', 0)),
                    'actors': {
                        'actor1': event.get('actor1'),
                        'actor2': event.get('actor2'),
                        'assoc_actor_1': event.get('assoc_actor_1'),
                        'assoc_actor_2': event.get('assoc_actor_2')
                    },
                    'notes': event.get('notes', ''),
                    'source': event.get('source'),
                    'source_scale': event.get('source_scale'),
                    'timestamp': event.get('timestamp')
                })
            except Exception as e:
                logger.warning(f"[WARN] Erreur format événement: {e}")
                continue

        return formatted


def get_acled_connector(email: str = None, password: str = None, api_key: str = None) -> ACLEDConnector:
    """Factory pour obtenir le connecteur ACLED"""
    return ACLEDConnector(email=email, password=password, api_key=api_key)


__all__ = ['ACLEDConnector', 'get_acled_connector']
