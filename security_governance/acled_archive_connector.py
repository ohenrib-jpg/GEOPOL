"""
Connecteur ACLED Archives - Données publiques gratuites
Source: https://acleddata.com/resources/general-public/
Documentation: https://acleddata.com/acleddata-site-content/uploads/2022/11/ACLED-Codebook-2022.pdf
"""

import pandas as pd
import requests
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import os
from io import StringIO

logger = logging.getLogger(__name__)

class ACLEDArchiveConnector:
    """
    Connecteur pour les archives publiques ACLED
    Données gratuites sans authentification
    """

    # URLs des archives publiques (2023-2024)
    ARCHIVE_URLS = {
        '2024': 'https://acleddata.com/special-projects/reduced-acled-dataset-for-2024/',
        '2023': 'https://acleddata.com/special-projects/reduced-acled-dataset-for-2023/',
        '2022': 'https://acleddata.com/special-projects/reduced-acled-dataset-for-2022/',
        '2021': 'https://acleddata.com/special-projects/reduced-acled-dataset-for-2021/',
        '2020': 'https://acleddata.com/special-projects/reduced-acled-dataset-for-2020/'
    }

    # URLs directes des CSV (à vérifier et mettre à jour)
    CSV_URLS = {
        '2024': 'https://api.acleddata.com/acled/read.csv?limit=0&terms=accept',
        '2023': 'https://api.acleddata.com/acled/read.csv?year=2023&limit=0&terms=accept',
        '2022': 'https://api.acleddata.com/acled/read.csv?year=2022&limit=0&terms=accept'
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GEOPOL-Analytics/1.0 (Public Archive Access)',
            'Accept': 'text/csv,application/json'
        })
        self.data_cache = {}

    def get_archive_data(self, year: str = '2023', limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Récupère les données d'archive pour une année donnée
        
        Args:
            year: Année (ex: '2023', '2022')
            limit: Nombre max d'événements
            
        Returns:
            Liste d'événements formatés
        """
        try:
            # Vérifier cache
            cache_key = f"{year}_{limit}"
            if cache_key in self.data_cache:
                logger.info(f"[CACHE] Données ACLED {year} récupérées du cache")
                return self.data_cache[cache_key][:limit]

            # URL de l'archive
            url = self.CSV_URLS.get(year)
            if not url:
                logger.warning(f"[WARN] Année {year} non supportée")
                return []

            logger.info(f"[DOWNLOAD] Téléchargement données ACLED {year}...")
            
            # Télécharger CSV
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            # Parser CSV
            csv_data = StringIO(response.text)
            df = pd.read_csv(csv_data, low_memory=False)

            # Formater les données
            events = self._format_events(df, limit)
            
            # Cacher les données
            self.data_cache[cache_key] = events
            
            logger.info(f"[OK] {len(events)} événements ACLED {year} récupérés")
            return events

        except Exception as e:
            logger.error(f"[ERROR] Erreur récupération ACLED {year}: {e}")
            logger.info(f"[DEMO] Utilisation données de démonstration pour ACLED {year}")
            # Retourner des événements de démonstration
            demo_events = self._get_demo_events(year, limit)
            return demo_events

    def get_recent_events(self, days: int = 7, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Récupère les événements récents (dernière année disponible)
        """
        try:
            # Utiliser la dernière année disponible dans les archives
            # Trier les années disponibles en ordre décroissant
            available_years = sorted(self.CSV_URLS.keys(), reverse=True)

            all_events = []
            for recent_year in available_years:
                all_events = self.get_archive_data(recent_year, limit * 2)
                if all_events:
                    break

            # Filtrer par date récente
            cutoff_date = datetime.now() - timedelta(days=days)
            recent_events = []
            
            for event in all_events:
                try:
                    event_date = datetime.strptime(event['date'], '%Y-%m-%d')
                    if event_date >= cutoff_date:
                        recent_events.append(event)
                except:
                    continue
                
                if len(recent_events) >= limit:
                    break

            logger.info(f"[OK] {len(recent_events)} événements récents ACLED")
            return recent_events[:limit]

        except Exception as e:
            logger.error(f"[ERROR] Erreur get_recent_events: {e}")
            return []

    def get_events_by_country(self, country_code: str, days: int = 30, 
                             limit: int = 100) -> List[Dict[str, Any]]:
        """
        Récupère événements pour un pays spécifique
        """
        try:
            country_name = self._get_country_name(country_code)
            recent_year = str(datetime.now().year)
            
            all_events = self.get_archive_data(recent_year, limit * 3)
            country_events = [
                event for event in all_events 
                if event.get('country', '').lower() == country_name.lower()
            ][:limit]

            logger.info(f"[OK] {len(country_events)} événements ACLED pour {country_name}")
            return country_events

        except Exception as e:
            logger.error(f"[ERROR] Erreur get_events_by_country: {e}")
            return []

    def get_security_summary(self, days: int = 7) -> Dict[str, Any]:
        """
        Résumé sécuritaire global
        """
        try:
            events = self.get_recent_events(days=days, limit=500)
            
            if not events:
                return {
                    'success': False,
                    'message': 'Aucun événement trouvé'
                }

            # Agréger par type
            by_type = {}
            by_country = {}
            fatalities = 0

            for event in events:
                # Compter par type
                event_type = event.get('event_type', 'Unknown')
                by_type[event_type] = by_type.get(event_type, 0) + 1
                
                # Compter par pays
                country = event.get('country', 'Unknown')
                by_country[country] = by_country.get(country, 0) + 1
                
                # Total victimes
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

            logger.info(f"[OK] Résumé ACLED: {len(events)} événements")
            return summary

        except Exception as e:
            logger.error(f"[ERROR] Erreur get_security_summary: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_conflicts(self, days: int = 7, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Récupère les conflits armés (Battles)
        """
        events = self.get_recent_events(days=days, limit=limit * 2)
        battles = [
            event for event in events 
            if event.get('event_type') == 'Battles'
        ][:limit]
        
        logger.info(f"[OK] {len(battles)} conflits armés ACLED")
        return battles

    def get_terrorism_events(self, days: int = 7, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Récupère événements terroristes
        """
        events = self.get_recent_events(days=days, limit=limit * 2)
        terrorism = [
            event for event in events
            if event.get('event_type') in ['Explosions/Remote violence', 'Violence against civilians']
        ][:limit]

        logger.info(f"[OK] {len(terrorism)} événements terroristes ACLED")
        return terrorism

    def get_protests(self, days: int = 7, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Récupère les manifestations
        """
        events = self.get_recent_events(days=days, limit=limit * 2)
        protests = [
            event for event in events
            if event.get('event_type') in ['Protests', 'Riots']
        ][:limit]

        logger.info(f"[OK] {len(protests)} manifestations ACLED")
        return protests

    def get_violence_civilians(self, days: int = 7, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Récupère les violences contre civils
        """
        events = self.get_recent_events(days=days, limit=limit * 2)
        violence = [
            event for event in events
            if event.get('event_type') == 'Violence against civilians'
        ][:limit]

        logger.info(f"[OK] {len(violence)} violences contre civils ACLED")
        return violence

    def get_hotspots(self, days: int = 7, min_events: int = 5) -> List[Dict[str, Any]]:
        """
        Identifie les zones à forte activité sécuritaire
        """
        events = self.get_recent_events(days=days, limit=500)

        # Agréger par localisation
        location_counts = {}
        for event in events:
            loc_key = f"{event.get('country', 'Unknown')}:{event.get('location', 'Unknown')}"
            if loc_key not in location_counts:
                location_counts[loc_key] = {
                    'country': event.get('country', 'Unknown'),
                    'location': event.get('location', 'Unknown'),
                    'latitude': event.get('latitude', 0),
                    'longitude': event.get('longitude', 0),
                    'event_count': 0,
                    'total_fatalities': 0,
                    'event_types': set()
                }

            location_counts[loc_key]['event_count'] += 1
            location_counts[loc_key]['total_fatalities'] += event.get('fatalities', 0)
            location_counts[loc_key]['event_types'].add(event.get('event_type', 'Unknown'))

        # Filtrer par min_events et formater
        hotspots = [
            {
                'country': data['country'],
                'location': data['location'],
                'latitude': data['latitude'],
                'longitude': data['longitude'],
                'event_count': data['event_count'],
                'total_fatalities': data['total_fatalities'],
                'event_types': list(data['event_types']),
                'severity': 'High' if data['event_count'] >= min_events * 2 else 'Medium'
            }
            for loc_key, data in location_counts.items()
            if data['event_count'] >= min_events
        ]

        # Trier par nombre d'événements
        hotspots.sort(key=lambda x: x['event_count'], reverse=True)

        logger.info(f"[OK] {len(hotspots)} zones chaudes ACLED")
        return hotspots

    def _format_events(self, df: pd.DataFrame, limit: int) -> List[Dict[str, Any]]:
        """
        Formate les événements ACLED au format GEOPOL
        """
        formatted = []
        
        # Colonnes ACLED standard
        required_columns = [
            'data_id', 'event_type', 'sub_event_type', 'country', 'region',
            'location', 'latitude', 'longitude', 'event_date', 'fatalities',
            'actor1', 'actor2', 'notes', 'source'
        ]
        
        # Vérifier colonnes disponibles
        available_columns = [col for col in required_columns if col in df.columns]
        
        for _, row in df.head(limit).iterrows():
            try:
                event = {
                    'id': f"acled_{row.get('data_id', '')}",
                    'event_type': row.get('event_type', 'Unknown'),
                    'sub_event_type': row.get('sub_event_type', ''),
                    'country': row.get('country', 'Unknown'),
                    'region': row.get('region', ''),
                    'location': row.get('location', ''),
                    'latitude': float(row.get('latitude', 0)),
                    'longitude': float(row.get('longitude', 0)),
                    'date': row.get('event_date', ''),
                    'fatalities': int(row.get('fatalities', 0)),
                    'actors': {
                        'actor1': row.get('actor1', ''),
                        'actor2': row.get('actor2', ''),
                    },
                    'notes': row.get('notes', ''),
                    'source': row.get('source', 'ACLED Public Archive'),
                    'timestamp': datetime.now().isoformat()
                }
                formatted.append(event)
            except Exception as e:
                logger.warning(f"[WARN] Erreur format événement: {e}")
                continue

        return formatted

    def _get_country_name(self, country_code: str) -> str:
        """
        Convertit code ISO en nom de pays
        """
        country_mapping = {
            'SYR': 'Syria', 'IRQ': 'Iraq', 'AFG': 'Afghanistan',
            'YEM': 'Yemen', 'LBY': 'Libya', 'UKR': 'Ukraine',
            'RUS': 'Russia', 'ISR': 'Israel', 'PSE': 'Palestine',
            'MLI': 'Mali', 'NGA': 'Nigeria', 'SOM': 'Somalia',
            'SDN': 'Sudan', 'COD': 'Democratic Republic of Congo',
            'ETH': 'Ethiopia', 'BFA': 'Burkina Faso', 'MMR': 'Myanmar'
        }
        return country_mapping.get(country_code.upper(), country_code)

    def _get_demo_events(self, year: str = '2024', limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Retourne des événements de démonstration réalistes lorsque l'API est indisponible
        """
        import random
        from datetime import datetime, timedelta

        demo_countries = [
            {'code': 'UKR', 'name': 'Ukraine', 'region': 'Europe'},
            {'code': 'PSE', 'name': 'Palestine', 'region': 'Middle East'},
            {'code': 'SYR', 'name': 'Syria', 'region': 'Middle East'},
            {'code': 'YEM', 'name': 'Yemen', 'region': 'Middle East'},
            {'code': 'AFG', 'name': 'Afghanistan', 'region': 'Asia'},
            {'code': 'ETH', 'name': 'Ethiopia', 'region': 'Africa'},
            {'code': 'MLI', 'name': 'Mali', 'region': 'Africa'},
            {'code': 'MMR', 'name': 'Myanmar', 'region': 'Asia'},
        ]

        event_types = ['Battles', 'Explosions/Remote violence', 'Violence against civilians', 'Protests', 'Riots']

        events = []
        base_date = datetime.now() - timedelta(days=30)

        for i in range(min(limit, 50)):  # Max 50 événements de démo
            country = random.choice(demo_countries)
            days_ago = random.randint(0, 30)
            event_date = base_date - timedelta(days=days_ago)

            event = {
                'id': f"acled_demo_{year}_{i}",
                'event_type': random.choice(event_types),
                'sub_event_type': '',
                'country': country['name'],
                'region': country['region'],
                'location': f"Location {i}",
                'latitude': round(random.uniform(20.0, 60.0), 4),
                'longitude': round(random.uniform(-10.0, 50.0), 4),
                'date': event_date.strftime('%Y-%m-%d'),
                'fatalities': random.randint(0, 50),
                'actors': {
                    'actor1': 'Government forces',
                    'actor2': 'Rebel groups'
                },
                'notes': 'Demo event - real ACLED data currently unavailable',
                'source': 'ACLED Demo Data (API unavailable)',
                'timestamp': datetime.now().isoformat(),
                'demo_data': True
            }
            events.append(event)

        logger.info(f"[DEMO] {len(events)} événements de démonstration ACLED générés")
        return events

def get_acled_archive_connector() -> ACLEDArchiveConnector:
    """Factory pour obtenir le connecteur ACLED Archive"""
    return ACLEDArchiveConnector()

__all__ = ['ACLEDArchiveConnector', 'get_acled_archive_connector']
