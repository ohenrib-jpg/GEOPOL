"""
Plugin: Alliance Dynamics
Description: Analyse des alliances et partenariats stratégiques - visualisation par mappemonde
"""

import requests
from datetime import datetime
import logging
import json
import plotly.express as px
import pandas as pd
import pycountry

logger = logging.getLogger(__name__)

class Plugin:
    """Classe principale du plugin"""
    
    def __init__(self, settings):
        """Initialisation"""
        self.name = "alliance-dynamics"
        self.settings = settings
        self.alliance_colors = {
            'OTAN': '#1f77b4',          # Bleu
            'UE': '#ff7f0e',            # Orange
            'OTSC': '#d62728',          # Rouge
            'RCEP': '#2ca02c',          # Vert
            'BRICS+': '#9467bd',        # Violet
            'ALENA': '#8c564b',         # Marron
            'ASEAN': '#e377c2',         # Rose
            'Ligue Arabe': '#7f7f7f',   # Gris
            'Union Africaine': '#bcbd22', # Vert olive
            'MERCOSUR': '#17becf'       # Cyan
        }
    
    def run(self, payload=None):
        """Point d'entrée principal"""
        if payload is None:
            payload = {}
        
        try:
            results = self._analyze_alliances(payload)
            
            return {
                'status': 'success',
                'plugin': self.name,
                'timestamp': self._get_timestamp(),
                'data': results['data'],
                'metrics': results['metrics'],
                'visualization': results['visualization'],
                'message': 'Analyse des dynamiques d\'alliances terminée'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'plugin': self.name,
                'timestamp': self._get_timestamp(),
                'data': [],
                'metrics': {},
                'visualization': {},
                'message': f'Erreur: {str(e)}'
            }
    
    def _analyze_alliances(self, payload):
        """Logique d'analyse des alliances"""
        region = payload.get('region', 'global')
        
        # Données des alliances géopolitiques
        alliances_data = self._fetch_geopolitical_alliances()
        
        # Préparation données pour la mappemonde
        world_map_data = self._prepare_world_map_data(alliances_data)
        
        # Génération de la mappemonde
        world_map = self._create_world_map(world_map_data)
        
        data = []
        for alliance in alliances_data:
            data.append({
                'alliance': alliance['name'],
                'type': alliance['type'],
                'membres_principaux': ', '.join(alliance['key_members']),
                'annee_creation': alliance['founding_year'],
                'objectifs_principaux': ', '.join(alliance['key_objectives']),
                'pays_membres': len(alliance['member_countries']),
                'couleur_alliance': self.alliance_colors.get(alliance['name'], '#000000'),
                'influence_globale': alliance['global_influence']
            })
        
        metrics = {
            'alliances_actives': len(alliances_data),
            'pays_couverts': len(set([country for alliance in alliances_data for country in alliance['member_countries']])),
            'nouvelles_adhesions_12m': self._count_recent_memberships(alliances_data),
            'tendance_cooperation': self._assess_cooperation_trend(alliances_data)
        }
        
        return {
            'data': data, 
            'metrics': metrics,
            'visualization': {
                'type': 'world_map',
                'title': 'Carte des Alliances Géopolitiques Mondiales',
                'data': world_map
            }
        }
    
    def _fetch_geopolitical_alliances(self):
        """Récupère les données des alliances géopolitiques (hors ONU)"""
        alliances = [
            {
                'name': 'OTAN',
                'type': 'Alliance militaire',
                'key_members': ['États-Unis', 'France', 'Allemagne', 'Royaume-Uni', 'Canada'],
                'member_countries': ['United States', 'Canada', 'United Kingdom', 'France', 'Germany', 
                                   'Italy', 'Spain', 'Turkey', 'Poland', 'Netherlands', 'Belgium',
                                   'Norway', 'Denmark', 'Portugal', 'Greece', 'Czech Republic',
                                   'Hungary', 'Romania', 'Bulgaria', 'Slovakia', 'Slovenia',
                                   'Croatia', 'Albania', 'Montenegro', 'North Macedonia', 'Lithuania',
                                   'Latvia', 'Estonia', 'Finland', 'Sweden'],
                'founding_year': 1949,
                'key_objectives': ['Défense collective', 'Sécurité transatlantique'],
                'global_influence': 'Très élevée'
            },
            {
                'name': 'UE',
                'type': 'Union politique et économique',
                'key_members': ['Allemagne', 'France', 'Italie', 'Espagne', 'Pologne'],
                'member_countries': ['Germany', 'France', 'Italy', 'Spain', 'Poland', 'Netherlands',
                                   'Belgium', 'Greece', 'Portugal', 'Sweden', 'Austria', 'Denmark',
                                   'Finland', 'Ireland', 'Romania', 'Czech Republic', 'Hungary',
                                   'Slovakia', 'Croatia', 'Bulgaria', 'Lithuania', 'Slovenia',
                                   'Latvia', 'Estonia', 'Cyprus', 'Luxembourg', 'Malta'],
                'founding_year': 1993,
                'key_objectives': ['Intégration économique', 'Coopération politique'],
                'global_influence': 'Élevée'
            },
            {
                'name': 'OTSC',
                'type': 'Alliance militaire',
                'key_members': ['Russie', 'Biélorussie', 'Kazakhstan', 'Arménie'],
                'member_countries': ['Russia', 'Belarus', 'Kazakhstan', 'Armenia', 'Kyrgyzstan', 'Tajikistan'],
                'founding_year': 2002,
                'key_objectives': ['Sécurité collective', 'Coopération militaire'],
                'global_influence': 'Moyenne'
            },
            {
                'name': 'BRICS+',
                'type': 'Alliance économique',
                'key_members': ['Chine', 'Russie', 'Inde', 'Brésil', 'Afrique du Sud'],
                'member_countries': ['China', 'Russia', 'India', 'Brazil', 'South Africa', 
                                   'Egypt', 'Ethiopia', 'Iran', 'Saudi Arabia', 'United Arab Emirates'],
                'founding_year': 2009,
                'key_objectives': ['Coopération Sud-Sud', 'Multipolarité économique'],
                'global_influence': 'Élevée'
            },
            {
                'name': 'ASEAN',
                'type': 'Organisation régionale',
                'key_members': ['Indonésie', 'Thaïlande', 'Malaisie', 'Singapour', 'Vietnam'],
                'member_countries': ['Indonesia', 'Thailand', 'Malaysia', 'Singapore', 'Vietnam',
                                   'Philippines', 'Myanmar', 'Cambodia', 'Laos', 'Brunei'],
                'founding_year': 1967,
                'key_objectives': ['Coopération régionale', 'Intégration économique Asie du Sud-Est'],
                'global_influence': 'Moyenne'
            }
        ]
        return alliances
    
    def _prepare_world_map_data(self, alliances_data):
        """Prépare les données pour la mappemonde"""
        map_data = []
        
        for alliance in alliances_data:
            color = self.alliance_colors.get(alliance['name'], '#000000')
            
            for country_name in alliance['member_countries']:
                country_code = self._get_country_iso_code(country_name)
                if country_code:
                    map_data.append({
                        'country': country_name,
                        'country_code': country_code,
                        'alliance': alliance['name'],
                        'alliance_type': alliance['type'],
                        'color': color,
                        'founding_year': alliance['founding_year'],
                        'influence': alliance['global_influence']
                    })
        
        return map_data
    
    def _create_world_map(self, map_data):
        """Crée une mappemonde interactive des alliances"""
        if not map_data:
            return {"error": "Aucune donnée disponible pour la carte"}
        
        df = pd.DataFrame(map_data)
        
        # Compter le nombre d'alliances par pays pour l'opacité
        alliance_count = df.groupby('country_code').size().reset_index(name='alliance_count')
        df = df.merge(alliance_count, on='country_code')
        
        fig = px.choropleth(
            df,
            locations="country_code",
            color="alliance",
            hover_name="country",
            hover_data={
                "alliance": True,
                "alliance_type": True,
                "founding_year": True,
                "influence": True,
                "country_code": False
            },
            color_discrete_map=self.alliance_colors,
            title="Carte des Alliances Géopolitiques Mondiales",
            labels={'alliance': 'Alliance', 'alliance_type': 'Type d\'alliance'}
        )
        
        fig.update_geos(
            showcoastlines=True,
            coastlinecolor="Black",
            showland=True,
            landcolor="lightgray",
            showocean=True,
            oceancolor="azure"
        )
        
        fig.update_layout(
            height=600,
            geo=dict(
                showframe=False,
                showcoastlines=True,
                projection_type='equirectangular'
            )
        )
        
        # Convertir en HTML pour l'affichage dans Streamlit
        return fig.to_html()
    
    def _get_country_iso_code(self, country_name):
        """Convertit le nom du pays en code ISO Alpha-3"""
        try:
            # Gestion des cas particuliers
            special_cases = {
                'United States': 'USA',
                'Russia': 'RUS',
                'United Kingdom': 'GBR',
                'South Korea': 'KOR',
                'North Korea': 'PRK',
                'Vietnam': 'VNM',
                'Czech Republic': 'CZE'
            }
            
            if country_name in special_cases:
                return special_cases[country_name]
            
            country = pycountry.countries.get(name=country_name)
            if country:
                return country.alpha_3
        except Exception as e:
            logger.warning(f"Erreur conversion pays {country_name}: {e}")
        
        return None
    
    def _count_recent_memberships(self, alliances_data):
        """Compte les nouvelles adhésions récentes"""
        current_year = datetime.now().year
        recent_threshold = current_year - 2  # 2 dernières années
        
        recent_count = 0
        for alliance in alliances_data:
            # Simuler quelques adhésions récentes
            if alliance['name'] in ['OTAN', 'BRICS+']:
                recent_count += 3
        
        return recent_count
    
    def _assess_cooperation_trend(self, alliances_data):
        """Évalue la tendance de coopération internationale"""
        recent_alliances = len([a for a in alliances_data if a['founding_year'] >= 2000])
        total_alliances = len(alliances_data)
        
        if total_alliances == 0:
            return 'Stable'
        
        recent_ratio = recent_alliances / total_alliances
        
        if recent_ratio > 0.6:
            return 'Expansion'
        elif recent_ratio > 0.3:
            return 'Stable'
        else:
            return 'Consolidation'
    
    def _get_timestamp(self):
        """Retourne timestamp ISO"""
        return datetime.now().isoformat()
    
    def get_info(self):
        """Informations du plugin"""
        return {
            'name': self.name,
            'capabilities': ['analyse_alliances', 'carte_geopolitique', 'visualisation_mondiale'],
            'required_keys': []
        }