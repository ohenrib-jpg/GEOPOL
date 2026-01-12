"""
Plugin: ISO Country Data
Description: Informations pays via API ISO - données standardisées, codes, indicateurs nationaux
"""

import requests
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Plugin:
    """Classe principale du plugin"""
    
    def __init__(self, settings):
        """Initialisation"""
        self.name = "iso-country-data"
        self.settings = settings
    
    def run(self, payload=None):
        """Point d'entrée principal"""
        if payload is None:
            payload = {}
        
        try:
            # VOTRE LOGIQUE ICI
            results = self._fetch_country_data(payload)
            
            return {
                'status': 'success',
                'plugin': self.name,
                'timestamp': self._get_timestamp(),
                'data': results['data'],
                'metrics': results['metrics'],
                'message': 'Données pays ISO récupérées'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'plugin': self.name,
                'timestamp': self._get_timestamp(),
                'data': [],
                'metrics': {},
                'message': f'Erreur: {str(e)}'
            }
    
    def _fetch_country_data(self, payload):
        """Logique de récupération des données pays"""
        countries = payload.get('countries', ['FR', 'DE', 'US', 'CN', 'RU'])
        data_type = payload.get('data_type', 'basic')
        
        country_data = []
        for country_code in countries:
            data = self._get_country_info(country_code, data_type)
            if data:
                country_data.append(data)
        
        metrics = {
            'pays_analyses': len(country_data),
            'couverture_regionale': self._calculate_regional_coverage(country_data),
            'donnees_standardisees': len([c for c in country_data if c.get('iso_standardized', False)]),
            'indicateurs_moyens': sum(len(c.get('indicators', [])) for c in country_data) / len(country_data) if country_data else 0
        }
        
        return {'data': country_data, 'metrics': metrics}
    
    def _get_country_info(self, country_code, data_type):
        """Récupère les informations d'un pays spécifique"""
        try:
            # API REST Countries ou données ISO standardisées
            url = f"https://restcountries.com/v3.1/alpha/{country_code}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()[0]
                return self._format_country_data(data, country_code, data_type)
        except Exception as e:
            logger.warning(f"Country data fetch error for {country_code}: {e}")
        
        # Données de secours basées sur standards ISO
        return self._get_fallback_country_data(country_code, data_type)
    
    def _format_country_data(self, api_data, country_code, data_type):
        """Formate les données pays de l'API"""
        return {
            'pays': api_data.get('name', {}).get('common', 'Inconnu'),
            'code_iso': country_code,
            'code_iso3': api_data.get('cca3', ''),
            'capitale': ', '.join(api_data.get('capital', ['Inconnue'])),
            'region': api_data.get('region', 'Inconnue'),
            'sous_region': api_data.get('subregion', 'Inconnue'),
            'population': api_data.get('population', 0),
            'superficie_km2': api_data.get('area', 0),
            'langues_officielles': ', '.join(api_data.get('languages', {}).values()) if api_data.get('languages') else 'Inconnues',
            'devises': ', '.join(api_data.get('currencies', {}).keys()) if api_data.get('currencies') else 'Inconnues',
            'indicators': self._extract_indicators(api_data),
            'iso_standardized': True
        }
    
    def _get_fallback_country_data(self, country_code, data_type):
        """Données de secours basées sur standards ISO"""
        country_db = {
            'FR': {
                'pays': 'France',
                'code_iso': 'FR',
                'code_iso3': 'FRA',
                'capitale': 'Paris',
                'region': 'Europe',
                'sous_region': 'Europe de l\'Ouest',
                'population': 68000000,
                'superficie_km2': 643801,
                'langues_officielles': 'Français',
                'devises': 'EUR',
                'indicators': ['PIB: 2.9T USD', 'IDH: 0.901', 'Inflation: 4.9%'],
                'iso_standardized': True
            },
            'US': {
                'pays': 'États-Unis',
                'code_iso': 'US',
                'code_iso3': 'USA',
                'capitale': 'Washington D.C.',
                'region': 'Amériques',
                'sous_region': 'Amérique du Nord',
                'population': 331000000,
                'superficie_km2': 9833517,
                'langues_officielles': 'Anglais',
                'devises': 'USD',
                'indicators': ['PIB: 23.3T USD', 'IDH: 0.921', 'Inflation: 3.7%'],
                'iso_standardized': True
            }
        }
        
        return country_db.get(country_code, {
            'pays': f'Pays {country_code}',
            'code_iso': country_code,
            'code_iso3': f'{country_code}XX',
            'capitale': 'Inconnue',
            'region': 'Inconnue',
            'sous_region': 'Inconnue',
            'population': 0,
            'superficie_km2': 0,
            'langues_officielles': 'Inconnues',
            'devises': 'Inconnues',
            'indicators': [],
            'iso_standardized': False
        })
    
    def _extract_indicators(self, api_data):
        """Extrait les indicateurs clés des données pays"""
        indicators = []
        
        if api_data.get('population'):
            indicators.append(f"Population: {api_data['population']:,}")
        
        if api_data.get('area'):
            indicators.append(f"Superficie: {api_data['area']:,} km²")
        
        # Ajouter d'autres indicateurs si disponibles
        if api_data.get('region'):
            indicators.append(f"Région: {api_data['region']}")
        
        return indicators
    
    def _calculate_regional_coverage(self, country_data):
        """Calcule la couverture régionale des données"""
        if not country_data:
            return "Aucune"
        
        regions = set([c['region'] for c in country_data if c['region'] != 'Inconnue'])
        total_regions = 6  # Europe, Asie, Afrique, Amériques, Océanie, Antarctique
        
        coverage = len(regions) / total_regions
        if coverage > 0.8:
            return "Élevée"
        elif coverage > 0.5:
            return "Moyenne"
        else:
            return "Faible"
    
    def _get_timestamp(self):
        """Retourne timestamp ISO"""
        return datetime.now().isoformat()
    
    def get_info(self):
        """Informations du plugin"""
        return {
            'name': self.name,
            'capabilities': ['donnees_pays', 'codes_iso', 'indicateurs_nationaux'],
            'required_keys': []  # API publique
        }