"""
Connecteur Global Incident - Multi-sources
Sources utilisees:
- GDELT (Global Database of Events, Language, and Tone) - API gratuite
- Global Incident Map (embed)
- ACLED (via le connecteur dedié si disponible)

Donnees disponibles:
- Terrorisme
- Conflits armes
- Protestations
- Tensions internationales
- Evenements geopolitiques
"""

import requests
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json
from collections import defaultdict

logger = logging.getLogger(__name__)

# Import du cache intelligent
try:
    from .security_cache import cached_connector_method
    CACHE_ENABLED = True
except ImportError:
    CACHE_ENABLED = False
    def cached_connector_method(*args, **kwargs):
        def decorator(func):
            return func
        return decorator


class GlobalIncidentConnector:
    """
    Connecteur multi-sources pour incidents globaux
    Utilise GDELT API pour des donnees reelles
    """

    # GDELT API endpoints
    GDELT_DOC_API = "https://api.gdeltproject.org/api/v2/doc/doc"
    GDELT_GEO_API = "https://api.gdeltproject.org/api/v2/geo/geo"
    GDELT_TV_API = "https://api.gdeltproject.org/api/v2/tv/tv"

    # Themes GDELT pertinents pour la securite
    SECURITY_THEMES = {
        'terrorism': ['TERROR', 'SUICIDE_ATTACK', 'BOMB', 'ATTACK', 'EXTREMISM'],
        'conflict': ['WAR', 'MILITARY', 'REBEL', 'ARMED_CONFLICT', 'VIOLENCE'],
        'protest': ['PROTEST', 'RIOT', 'DEMONSTRATION', 'CIVIL_UNREST'],
        'cyber': ['CYBER_ATTACK', 'HACKING', 'RANSOMWARE', 'DATA_BREACH'],
        'political': ['POLITICAL_TURMOIL', 'COUP', 'ELECTION_FRAUD', 'GOVERNMENT']
    }

    # Mapping CAMEO codes -> categories
    CAMEO_CATEGORIES = {
        '14': 'protest',       # Protestations
        '15': 'force',         # Usage de la force
        '17': 'coerce',        # Coercition
        '18': 'assault',       # Attaques
        '19': 'fight',         # Combats
        '20': 'unconventional' # Violence non-conventionnelle (terrorisme)
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GEOPOL-Analytics/1.0',
            'Accept': 'application/json'
        })
        self.timeout = 30

    @cached_connector_method(ttl_seconds=1800, cache_type='gdelt')
    def get_recent_incidents(self, days: int = 7, limit: int = 100) -> Dict[str, Any]:
        """
        Recupere les incidents recents via GDELT API
        """
        try:
            # Recherche multi-themes
            all_incidents = []

            # Recuperer les incidents de securite via GDELT Doc API
            for category, themes in self.SECURITY_THEMES.items():
                try:
                    incidents = self._fetch_gdelt_articles(
                        query=' OR '.join(themes),
                        days=days,
                        limit=limit // len(self.SECURITY_THEMES)
                    )
                    for inc in incidents:
                        inc['category'] = category
                    all_incidents.extend(incidents)
                except Exception as e:
                    logger.warning(f"[WARN] GDELT {category}: {e}")

            # Trier par date
            all_incidents.sort(key=lambda x: x.get('date', ''), reverse=True)

            # Limiter
            all_incidents = all_incidents[:limit]

            # Statistiques
            by_category = defaultdict(int)
            by_country = defaultdict(int)
            for inc in all_incidents:
                by_category[inc.get('category', 'unknown')] += 1
                for country in inc.get('countries', []):
                    by_country[country] += 1

            logger.info(f"[OK] GDELT: {len(all_incidents)} incidents recuperes")

            return {
                'success': True,
                'incidents_count': len(all_incidents),
                'incidents': all_incidents,
                'period_days': days,
                'by_category': dict(by_category),
                'by_country': dict(sorted(by_country.items(), key=lambda x: x[1], reverse=True)[:20]),
                'timestamp': datetime.now().isoformat(),
                'source': 'GDELT Project API'
            }

        except Exception as e:
            logger.error(f"[ERROR] Error getting incidents: {e}")
            return {
                'success': False,
                'error': str(e),
                'incidents': []
            }

    def _fetch_gdelt_articles(self, query: str, days: int = 7, limit: int = 50) -> List[Dict]:
        """
        Recupere des articles GDELT via l'API Doc
        """
        try:
            # Calculer les dates
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            params = {
                'query': query,
                'mode': 'artlist',
                'maxrecords': min(limit, 250),
                'format': 'json',
                'startdatetime': start_date.strftime('%Y%m%d%H%M%S'),
                'enddatetime': end_date.strftime('%Y%m%d%H%M%S'),
                'sort': 'datedesc'
            }

            response = self.session.get(
                self.GDELT_DOC_API,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()

            data = response.json()
            articles = data.get('articles', [])

            # Formater les resultats
            incidents = []
            for article in articles:
                incidents.append({
                    'id': article.get('url', '')[:50],
                    'title': article.get('title', ''),
                    'url': article.get('url', ''),
                    'source': article.get('domain', ''),
                    'date': article.get('seendate', ''),
                    'language': article.get('language', ''),
                    'countries': self._extract_countries(article),
                    'tone': article.get('tone', 0),
                    'image': article.get('socialimage', '')
                })

            return incidents

        except Exception as e:
            logger.warning(f"[WARN] GDELT fetch error: {e}")
            return []

    def _extract_countries(self, article: Dict) -> List[str]:
        """Extrait les pays d'un article GDELT"""
        countries = []
        # GDELT utilise des codes FIPS/ISO dans sourcecountry
        if article.get('sourcecountry'):
            countries.append(article['sourcecountry'])
        return countries

    @cached_connector_method(ttl_seconds=1800, cache_type='gdelt')
    def get_terrorism_data(self, days: int = 30, limit: int = 50) -> Dict[str, Any]:
        """
        Recupere les donnees sur les actes terroristes via GDELT
        """
        try:
            # Themes terrorisme
            themes = self.SECURITY_THEMES['terrorism']
            incidents = self._fetch_gdelt_articles(
                query=' OR '.join(themes),
                days=days,
                limit=limit
            )

            # Calculer statistiques
            by_country = defaultdict(int)
            for inc in incidents:
                for country in inc.get('countries', []):
                    by_country[country] += 1

            # Calculer la moyenne du tone (sentiment)
            avg_tone = 0
            if incidents:
                tones = [inc.get('tone', 0) for inc in incidents if inc.get('tone')]
                if tones:
                    avg_tone = sum(tones) / len(tones)

            data = {
                'success': True,
                'data_type': 'terrorism',
                'timestamp': datetime.now().isoformat(),
                'source': 'GDELT Project API',
                'statistics': {
                    'total_incidents': len(incidents),
                    'period_days': days,
                    'affected_countries': list(by_country.keys()),
                    'top_countries': sorted(by_country.items(), key=lambda x: x[1], reverse=True)[:10],
                    'average_tone': round(avg_tone, 2)
                },
                'recent_incidents': incidents[:20],
                'map_embed': {
                    'url': 'https://www.globalincidentmap.com/home.php',
                    'description': 'Global Terrorism Incident Map'
                }
            }

            logger.info(f"[OK] Terrorism: {len(incidents)} articles")
            return data

        except Exception as e:
            logger.error(f"[ERROR] Terrorism data error: {e}")
            return {'success': False, 'error': str(e)}

    @cached_connector_method(ttl_seconds=1800, cache_type='gdelt')
    def get_cyber_attacks(self, days: int = 30, limit: int = 50) -> Dict[str, Any]:
        """
        Recupere les donnees sur les cyberattaques via GDELT
        """
        try:
            # Themes cyber
            themes = self.SECURITY_THEMES['cyber']
            incidents = self._fetch_gdelt_articles(
                query=' OR '.join(themes),
                days=days,
                limit=limit
            )

            # Statistiques
            by_country = defaultdict(int)
            for inc in incidents:
                for country in inc.get('countries', []):
                    by_country[country] += 1

            data = {
                'success': True,
                'data_type': 'cyber_attacks',
                'timestamp': datetime.now().isoformat(),
                'source': 'GDELT Project API',
                'statistics': {
                    'total_incidents': len(incidents),
                    'period_days': days,
                    'affected_countries': list(by_country.keys()),
                    'top_countries': sorted(by_country.items(), key=lambda x: x[1], reverse=True)[:10]
                },
                'recent_attacks': incidents[:20]
            }

            logger.info(f"[OK] Cyber attacks: {len(incidents)} articles")
            return data

        except Exception as e:
            logger.error(f"[ERROR] Cyber attacks data error: {e}")
            return {'success': False, 'error': str(e)}

    @cached_connector_method(ttl_seconds=1800, cache_type='gdelt')
    def get_political_tensions(self, days: int = 30, limit: int = 50) -> Dict[str, Any]:
        """
        Recupere les donnees sur les tensions politiques via GDELT
        """
        try:
            # Themes politiques
            themes = self.SECURITY_THEMES['political'] + self.SECURITY_THEMES['protest']
            incidents = self._fetch_gdelt_articles(
                query=' OR '.join(themes),
                days=days,
                limit=limit
            )

            # Statistiques par pays
            by_country = defaultdict(int)
            for inc in incidents:
                for country in inc.get('countries', []):
                    by_country[country] += 1

            # Identifier les hotspots
            hotspots = sorted(by_country.items(), key=lambda x: x[1], reverse=True)[:10]

            data = {
                'success': True,
                'data_type': 'political_tensions',
                'timestamp': datetime.now().isoformat(),
                'source': 'GDELT Project API',
                'statistics': {
                    'total_incidents': len(incidents),
                    'period_days': days,
                    'countries_affected': len(by_country)
                },
                'hotspots': [{'country': c, 'count': n} for c, n in hotspots],
                'recent_incidents': incidents[:20],
                'global_tension_index': min(10, len(incidents) / 10)  # Indice simplifie
            }

            logger.info(f"[OK] Political tensions: {len(incidents)} articles")
            return data

        except Exception as e:
            logger.error(f"[ERROR] Political tensions error: {e}")
            return {'success': False, 'error': str(e)}

    def get_security_summary(self, days: int = 7) -> Dict[str, Any]:
        """
        Resume global de la situation securitaire
        """
        try:
            terrorism = self.get_terrorism_data(days=days)
            cyber = self.get_cyber_attacks(days=days)
            tensions = self.get_political_tensions(days=days)

            # Calculer totaux
            total_incidents = 0
            countries_set = set()

            if terrorism.get('success'):
                total_incidents += terrorism.get('statistics', {}).get('total_incidents', 0)
                countries_set.update(terrorism.get('statistics', {}).get('affected_countries', []))

            if cyber.get('success'):
                total_incidents += cyber.get('statistics', {}).get('total_incidents', 0)
                countries_set.update(cyber.get('statistics', {}).get('affected_countries', []))

            if tensions.get('success'):
                total_incidents += tensions.get('statistics', {}).get('total_incidents', 0)

            # Determiner niveau de menace
            threat_level = 'low'
            if total_incidents > 50:
                threat_level = 'medium'
            if total_incidents > 100:
                threat_level = 'high'
            if total_incidents > 200:
                threat_level = 'critical'

            summary = {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'period_days': days,
                'global_security_status': {
                    'overall_threat_level': threat_level,
                    'terrorism_threat': 'high' if terrorism.get('statistics', {}).get('total_incidents', 0) > 20 else 'medium',
                    'cyber_threat': 'high' if cyber.get('statistics', {}).get('total_incidents', 0) > 20 else 'medium',
                    'political_stability': 'low' if tensions.get('statistics', {}).get('total_incidents', 0) > 30 else 'medium'
                },
                'statistics': {
                    'total_incidents_tracked': total_incidents,
                    'countries_affected': len(countries_set),
                    'terrorism_incidents': terrorism.get('statistics', {}).get('total_incidents', 0),
                    'cyber_incidents': cyber.get('statistics', {}).get('total_incidents', 0),
                    'political_incidents': tensions.get('statistics', {}).get('total_incidents', 0)
                },
                'data_sources': [
                    'GDELT Project API',
                    'Open Source Intelligence (OSINT)'
                ],
                'terrorism': terrorism if terrorism.get('success') else None,
                'cyber_attacks': cyber if cyber.get('success') else None,
                'political_tensions': tensions if tensions.get('success') else None,
                'maps': {
                    'global_incidents': 'https://www.globalincidentmap.com/',
                    'terrorism': 'https://www.globalincidentmap.com/home.php'
                }
            }

            logger.info(f"[OK] Security summary: {total_incidents} incidents totaux")
            return summary

        except Exception as e:
            logger.error(f"[ERROR] Security summary error: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_map_embed_info(self) -> Dict[str, Any]:
        """
        Retourne les informations pour embed des cartes
        """
        return {
            'success': True,
            'maps': [
                {
                    'name': 'Global Terrorism',
                    'url': 'https://www.globalincidentmap.com/home.php',
                    'description': 'Real-time terrorism incident tracking',
                    'type': 'terrorism'
                },
                {
                    'name': 'Global Incidents',
                    'url': 'https://www.globalincidentmap.com/',
                    'description': 'Comprehensive security incident tracking',
                    'type': 'general'
                }
            ],
            'note': 'These maps provide visual representation of global security incidents',
            'usage': 'Can be embedded in iframe for real-time visualization'
        }


def get_global_incident_connector() -> GlobalIncidentConnector:
    """Factory pour obtenir le connecteur"""
    return GlobalIncidentConnector()


__all__ = ['GlobalIncidentConnector', 'get_global_incident_connector']
