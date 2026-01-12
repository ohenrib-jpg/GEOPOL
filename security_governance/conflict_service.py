"""
ConflictService - Service unifié pour les données de conflits
Remplace ACLED par UCDP (gratuit, sans authentification)
Maintient la compatibilité avec le format attendu par le frontend
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)

# Import du connecteur UCDP
try:
    from .ucdp_connector import get_ucdp_connector, UCDPConnector
    UCDP_AVAILABLE = True
except ImportError as e:
    UCDP_AVAILABLE = False
    logger.warning(f"[ConflictService] UCDP non disponible: {e}")

# Fonction pour vider le cache UCDP
def _clear_ucdp_cache():
    """Vide le cache UCDP pour forcer un rechargement des données"""
    try:
        from .security_cache import SecurityCache
        if hasattr(SecurityCache, '_memory_cache'):
            keys_to_delete = [k for k in SecurityCache._memory_cache.keys() if 'ucdp' in k.lower()]
            for key in keys_to_delete:
                del SecurityCache._memory_cache[key]
                logger.info(f"[ConflictService] Cache UCDP vidé: {key[:50]}...")
    except Exception as e:
        logger.debug(f"[ConflictService] Pas de cache à vider: {e}")


class ConflictService:
    """
    Service unifié pour les données de conflits.
    Utilise UCDP comme source principale et adapte le format au format ACLED
    attendu par le frontend.
    """

    # Mapping des types UCDP vers des types plus lisibles (style ACLED)
    # Les clés peuvent être des strings ou des entiers selon le contexte
    EVENT_TYPE_MAPPING = {
        'State-based conflict': 'Battles',
        'Non-state conflict': 'Violence against civilians',
        'One-sided violence': 'Explosions/Remote violence',
        # Types UCDP bruts (string)
        '1': 'Battles',
        '2': 'Violence against civilians',
        '3': 'Explosions/Remote violence',
        # Types UCDP bruts (entier)
        1: 'Battles',
        2: 'Violence against civilians',
        3: 'Explosions/Remote violence'
    }

    def __init__(self):
        """Initialise le service avec les connecteurs disponibles"""
        self.ucdp = None

        if UCDP_AVAILABLE:
            try:
                # Vider le cache UCDP pour s'assurer d'avoir des données fraîches
                _clear_ucdp_cache()
                self.ucdp = get_ucdp_connector()
                logger.info("[ConflictService] UCDP connecteur initialisé")
            except Exception as e:
                logger.error(f"[ConflictService] Erreur init UCDP: {e}")

    def is_available(self) -> bool:
        """Vérifie si le service est disponible"""
        return self.ucdp is not None

    def get_security_summary(self, days: int = 7) -> Dict[str, Any]:
        """
        Retourne un résumé sécuritaire au format ACLED (compatible frontend).

        Format retourné:
        {
            'success': True,
            'period_days': days,
            'total_events': int,
            'total_fatalities': int,
            'by_type': [{'type': str, 'count': int}, ...],
            'top_countries': [{'country': str, 'count': int}, ...],
            'updated_at': ISO timestamp,
            'source': 'UCDP'
        }
        """
        if not self.ucdp:
            return {
                'success': False,
                'total_events': 0,
                'total_fatalities': 0,
                'by_type': [],
                'message': 'Service de conflits non disponible'
            }

        try:
            # Vider le cache UCDP avant chaque appel pour avoir des données fraîches
            _clear_ucdp_cache()

            # Récupérer les données UCDP
            logger.info(f"[ConflictService] Appel UCDP get_recent_conflicts(days={days})")
            result = self.ucdp.get_recent_conflicts(days=days, limit=500)
            logger.info(f"[ConflictService] UCDP result: success={result.get('success')}, total_events={result.get('total_events')}")

            if not result.get('success'):
                logger.warning(f"[ConflictService] UCDP erreur: {result.get('error')}")
                return self._get_fallback_summary(days)

            events = result.get('events', [])
            stats = result.get('statistics', {})
            logger.info(f"[ConflictService] Parsed: events={len(events)}, stats.total={stats.get('total')}")

            # Transformer by_type dict en liste (format ACLED)
            by_type_dict = stats.get('by_type', {})
            by_type_list = self._dict_to_type_list(by_type_dict)

            # Transformer by_country dict en liste
            by_country_dict = stats.get('by_country', {})
            top_countries = [
                {'country': k, 'count': v}
                for k, v in sorted(by_country_dict.items(), key=lambda x: x[1], reverse=True)[:10]
            ]

            return {
                'success': True,
                'period_days': days,
                'total_events': stats.get('total', len(events)),
                'total_fatalities': stats.get('total_fatalities', 0),
                'by_type': by_type_list,
                'top_countries': top_countries,
                'updated_at': datetime.now().isoformat(),
                'source': 'UCDP',
                'events_sample': events[:10]  # Échantillon pour debug
            }

        except Exception as e:
            logger.error(f"[ConflictService] Erreur get_security_summary: {e}")
            return self._get_fallback_summary(days)

    def get_hotspots(self, days: int = 7, min_events: int = 5) -> List[Dict[str, Any]]:
        """
        Identifie les zones de forte activité (hotspots).

        Format retourné (par hotspot):
        {
            'country': str,
            'location': str,
            'event_count': int,
            'total_fatalities': int,
            'severity': 'High' | 'Medium' | 'Low',
            'lat': float,
            'lon': float
        }
        """
        if not self.ucdp:
            return []

        try:
            result = self.ucdp.get_recent_conflicts(days=days, limit=1000)

            if not result.get('success'):
                return []

            events = result.get('events', [])

            # Agréger par pays/location
            hotspots_data = defaultdict(lambda: {
                'events': [],
                'fatalities': 0,
                'locations': set()
            })

            for event in events:
                country = event.get('country', 'Unknown')
                location = event.get('location', '')
                fatalities = event.get('fatalities', 0)

                hotspots_data[country]['events'].append(event)
                hotspots_data[country]['fatalities'] += fatalities
                if location:
                    hotspots_data[country]['locations'].add(location)

            # Filtrer et formater les hotspots
            hotspots = []
            for country, data in hotspots_data.items():
                event_count = len(data['events'])
                if event_count >= min_events:
                    # Calculer la sévérité
                    severity = 'High' if event_count >= 20 or data['fatalities'] >= 50 else \
                               'Medium' if event_count >= 10 or data['fatalities'] >= 20 else 'Low'

                    # Prendre les coordonnées du premier événement avec lat/lon
                    lat, lon = None, None
                    for evt in data['events']:
                        if evt.get('latitude') and evt.get('longitude'):
                            lat = evt['latitude']
                            lon = evt['longitude']
                            break

                    hotspots.append({
                        'country': country,
                        'location': ', '.join(list(data['locations'])[:3]),
                        'event_count': event_count,
                        'total_fatalities': data['fatalities'],
                        'severity': severity,
                        'lat': lat,
                        'lon': lon
                    })

            # Trier par nombre d'événements
            hotspots.sort(key=lambda x: x['event_count'], reverse=True)

            return hotspots[:20]  # Top 20

        except Exception as e:
            logger.error(f"[ConflictService] Erreur get_hotspots: {e}")
            return []

    def get_recent_events(self, days: int = 7, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retourne les événements récents au format ACLED.

        Format retourné (par événement):
        {
            'id': str,
            'event_type': str,
            'country': str,
            'location': str,
            'latitude': float,
            'longitude': float,
            'date': str (YYYY-MM-DD),
            'fatalities': int,
            'actors': dict or str,
            'source': str
        }
        """
        if not self.ucdp:
            return []

        try:
            result = self.ucdp.get_recent_conflicts(days=days, limit=limit)

            if not result.get('success'):
                return []

            events = result.get('events', [])

            # Adapter le format au format ACLED attendu
            formatted = []
            for event in events:
                formatted.append({
                    'id': f"ucdp_{event.get('id', '')}",
                    'event_type': self._map_event_type(event.get('event_type', '')),
                    'sub_event_type': event.get('event_type', ''),  # Type original
                    'country': event.get('country', ''),
                    'location': event.get('location', ''),
                    'latitude': event.get('latitude'),
                    'longitude': event.get('longitude'),
                    'date': event.get('date', '')[:10] if event.get('date') else '',
                    'fatalities': event.get('fatalities', 0),
                    'actors': {
                        'actor1': event.get('actors', '').split(' vs ')[0] if ' vs ' in str(event.get('actors', '')) else event.get('actors', ''),
                        'actor2': event.get('actors', '').split(' vs ')[1] if ' vs ' in str(event.get('actors', '')) else ''
                    },
                    'source': 'UCDP',
                    'timestamp': event.get('timestamp', datetime.now().isoformat())
                })

            return formatted

        except Exception as e:
            logger.error(f"[ConflictService] Erreur get_recent_events: {e}")
            return []

    def get_events_by_country(self, country_code: str, days: int = 30, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Retourne les événements pour un pays spécifique.
        Note: UCDP utilise des noms de pays, pas des codes ISO.
        """
        # Mapping codes ISO vers noms de pays (les plus courants)
        country_names = {
            'SYR': 'Syria', 'UKR': 'Ukraine', 'YEM': 'Yemen', 'AFG': 'Afghanistan',
            'IRQ': 'Iraq', 'SOM': 'Somalia', 'SDN': 'Sudan', 'ETH': 'Ethiopia',
            'NGA': 'Nigeria', 'MLI': 'Mali', 'BFA': 'Burkina Faso', 'NER': 'Niger',
            'COD': 'DR Congo', 'CAF': 'Central African Republic', 'MOZ': 'Mozambique',
            'MYA': 'Myanmar', 'PAK': 'Pakistan', 'IND': 'India', 'COL': 'Colombia',
            'MEX': 'Mexico', 'PHL': 'Philippines', 'THA': 'Thailand'
        }

        country_name = country_names.get(country_code.upper(), country_code)

        # Récupérer tous les événements et filtrer
        all_events = self.get_recent_events(days=days, limit=500)

        return [
            e for e in all_events
            if country_name.lower() in e.get('country', '').lower()
        ][:limit]

    def _dict_to_type_list(self, by_type_dict: Dict[str, int]) -> List[Dict[str, Any]]:
        """
        Convertit un dict {type: count} en liste [{type, count}]
        avec mapping des types UCDP vers types ACLED.
        """
        # Agréger par type mappé
        aggregated = defaultdict(int)
        for ucdp_type, count in by_type_dict.items():
            acled_type = self._map_event_type(ucdp_type)
            aggregated[acled_type] += count

        # Convertir en liste triée
        type_list = [
            {'type': t, 'count': c}
            for t, c in sorted(aggregated.items(), key=lambda x: x[1], reverse=True)
        ]

        return type_list

    def _map_event_type(self, ucdp_type: str) -> str:
        """Mappe un type UCDP vers un type ACLED-like"""
        return self.EVENT_TYPE_MAPPING.get(ucdp_type, ucdp_type)

    def _get_fallback_summary(self, days: int) -> Dict[str, Any]:
        """Retourne des données de fallback en cas d'erreur"""
        return {
            'success': True,
            'period_days': days,
            'total_events': 0,
            'total_fatalities': 0,
            'by_type': [
                {'type': 'Battles', 'count': 0},
                {'type': 'Violence against civilians', 'count': 0},
                {'type': 'Explosions/Remote violence', 'count': 0}
            ],
            'top_countries': [],
            'updated_at': datetime.now().isoformat(),
            'source': 'Fallback',
            'message': 'Données temporairement indisponibles'
        }


# Singleton
_conflict_service = None

def get_conflict_service() -> ConflictService:
    """Retourne l'instance singleton du ConflictService"""
    global _conflict_service
    if _conflict_service is None:
        _conflict_service = ConflictService()
    return _conflict_service


# Export pour compatibilité
__all__ = ['ConflictService', 'get_conflict_service']
