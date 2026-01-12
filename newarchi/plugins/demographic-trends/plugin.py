"""
Plugin: Demographic Trends
Description: Analyse tendances démographiques mondiales - projections, vieillissement, migrations, impact géopolitique
"""

import requests
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Plugin:
    """Classe principale du plugin"""
    
    def __init__(self, settings):
        """Initialisation"""
        self.name = "demographic-trends"
        self.settings = settings
    
    def run(self, payload=None):
        """Point d'entrée principal"""
        if payload is None:
            payload = {}
        
        try:
            # VOTRE LOGIQUE ICI
            results = self._analyze_demographic_trends(payload)
            
            return {
                'status': 'success',
                'plugin': self.name,
                'timestamp': self._get_timestamp(),
                'data': results['data'],
                'metrics': results['metrics'],
                'message': 'Analyse tendances démographiques terminée'
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
    
    def _analyze_demographic_trends(self, payload):
        """Logique d'analyse des tendances démographiques"""
        timeframe = payload.get('timeframe', '2050')
        trend_type = payload.get('trend_type', 'all')
        
        # Données projections démographiques
        population_projections = self._fetch_population_projections(timeframe)
        
        # Données vieillissement
        aging_data = self._fetch_aging_population_data()
        
        # Données transitions démographiques
        demographic_transitions = self._analyze_demographic_transitions()
        
        # Impact géopolitique
        geopolitical_impact = self._assess_geopolitical_impact(population_projections, aging_data)
        
        data = []
        
        # Projections population
        for country in population_projections[:8]:
            data.append({
                'pays': country['country'],
                'type_tendance': 'Projection Population',
                'population_actuelle': country['current_population'],
                'projection_2050': country['projection_2050'],
                'taux_croissance': country['growth_rate'],
                'age_median': country['median_age'],
                'densite_population': country['population_density'],
                'impact_economique': country['economic_impact'],
                'risque_geopolitique': country['geopolitical_risk']
            })
        
        # Vieillissement population
        for country in aging_data[:6]:
            data.append({
                'pays': country['country'],
                'type_tendance': 'Vieillissement',
                'population_actuelle': country['population_65plus'],
                'projection_2050': country['projection_65plus_2050'],
                'taux_croissance': country['aging_rate'],
                'age_median': country['current_median_age'],
                'densite_population': country['dependency_ratio'],
                'impact_economique': country['pension_system_impact'],
                'risque_geopolitique': country['social_stability_risk']
            })
        
        # Transitions démographiques
        for transition in demographic_transitions[:4]:
            data.append({
                'pays': transition['country'],
                'type_tendance': 'Transition Démographique',
                'population_actuelle': transition['current_stage'],
                'projection_2050': transition['projected_stage'],
                'taux_croissance': transition['transition_speed'],
                'age_median': transition['fertility_rate'],
                'densite_population': transition['mortality_rate'],
                'impact_economique': transition['demographic_dividend'],
                'risque_geopolitique': transition['migration_pressure']
            })
        
        metrics = {
            'pays_analysees': len(population_projections),
            'croissance_population_mondiale': self._calculate_global_growth(population_projections),
            'taux_vieillissement_moyen': self._calculate_average_aging(aging_data),
            'pays_transition_avancee': len([t for t in demographic_transitions if t['current_stage'] == 'Phase 4']),
            'impact_geopolitique_global': geopolitical_impact['overall_impact']
        }
        
        return {'data': data, 'metrics': metrics}
    
    def _fetch_population_projections(self, timeframe):
        """Récupère les projections de population"""
        try:
            # Sources: UN World Population Prospects, World Bank
            return [
                {
                    'country': 'Inde',
                    'current_population': 1428,
                    'projection_2050': 1668,
                    'growth_rate': 0.97,
                    'median_age': 28.7,
                    'population_density': 464,
                    'economic_impact': 'Dividende démographique',
                    'geopolitique_risk': 'Pression ressources'
                },
                {
                    'country': 'Chine',
                    'current_population': 1425,
                    'projection_2050': 1312,
                    'growth_rate': -0.12,
                    'median_age': 38.4,
                    'population_density': 148,
                    'economic_impact': 'Vieillissement accéléré',
                    'geopolitique_risk': 'Déclin influence'
                },
                {
                    'country': 'Nigeria',
                    'current_population': 216,
                    'projection_2050': 401,
                    'growth_rate': 2.58,
                    'median_age': 18.1,
                    'population_density': 226,
                    'economic_impact': 'Opportunité transformation',
                    'geopolitique_risk': 'Pression migratoire'
                },
                {
                    'country': 'Allemagne',
                    'current_population': 83,
                    'projection_2050': 79,
                    'growth_rate': -0.12,
                    'median_age': 45.7,
                    'population_density': 240,
                    'economic_impact': 'Pénurie main-d\'œuvre',
                    'geopolitique_risk': 'Dépendance immigration'
                }
            ]
        except Exception as e:
            logger.warning(f"Population projections error: {e}")
            return []
    
    def _fetch_aging_population_data(self):
        """Récupère les données sur le vieillissement"""
        try:
            # Sources: UN Population Division, OCDE
            return [
                {
                    'country': 'Japon',
                    'population_65plus': 28.7,
                    'projection_65plus_2050': 38.4,
                    'aging_rate': 1.2,
                    'current_median_age': 48.6,
                    'dependency_ratio': 52.3,
                    'pension_system_impact': 'Très élevé',
                    'social_stability_risk': 'Élevé'
                },
                {
                    'country': 'Italie',
                    'population_65plus': 23.0,
                    'projection_65plus_2050': 34.2,
                    'aging_rate': 1.1,
                    'current_median_age': 47.3,
                    'dependency_ratio': 48.9,
                    'pension_system_impact': 'Élevé',
                    'social_stability_risk': 'Moyen'
                },
                {
                    'country': 'Corée du Sud',
                    'population_65plus': 15.8,
                    'projection_65plus_2050': 39.8,
                    'aging_rate': 2.8,
                    'current_median_age': 43.7,
                    'dependency_ratio': 21.7,
                    'pension_system_impact': 'Très élevé',
                    'social_stability_risk': 'Élevé'
                }
            ]
        except Exception as e:
            logger.warning(f"Aging population data error: {e}")
            return []
    
    def _analyze_demographic_transitions(self):
        """Analyse les transitions démographiques"""
        return [
            {
                'country': 'Bangladesh',
                'current_stage': 'Phase 3',
                'projected_stage': 'Phase 4 (2040)',
                'transition_speed': 'Rapide',
                'fertility_rate': 2.0,
                'mortality_rate': 5.4,
                'demographic_dividend': 'En cours',
                'migration_pressure': 'Élevée'
            },
            {
                'country': 'Éthiopie',
                'current_stage': 'Phase 2',
                'projected_stage': 'Phase 3 (2035)',
                'transition_speed': 'Modérée',
                'fertility_rate': 4.1,
                'mortality_rate': 6.8,
                'demographic_dividend': 'Futur potentiel',
                'migration_pressure': 'Très élevée'
            },
            {
                'country': 'Brésil',
                'current_stage': 'Phase 4',
                'projected_stage': 'Phase 4 (stabilisation)',
                'transition_speed': 'Achevée',
                'fertility_rate': 1.6,
                'mortality_rate': 6.5,
                'demographic_dividend': 'Terminé',
                'migration_pressure': 'Modérée'
            }
        ]
    
    def _assess_geopolitical_impact(self, population_data, aging_data):
        """Évalue l'impact géopolitique des tendances démographiques"""
        high_risk_countries = len([p for p in population_data if p['geopolitique_risk'] in ['Élevé', 'Très élevé']])
        aging_crisis_countries = len([a for a in aging_data if a['social_stability_risk'] == 'Élevé'])
        
        total_indicators = len(population_data) + len(aging_data)
        
        if total_indicators == 0:
            return {'overall_impact': 'Inconnu'}
        
        risk_score = (high_risk_countries + aging_crisis_countries) / total_indicators
        
        if risk_score > 0.5:
            return {'overall_impact': 'Très élevé'}
        elif risk_score > 0.3:
            return {'overall_impact': 'Élevé'}
        elif risk_score > 0.1:
            return {'overall_impact': 'Modéré'}
        else:
            return {'overall_impact': 'Faible'}
    
    def _calculate_global_growth(self, population_data):
        """Calcule la croissance démographique globale"""
        if not population_data:
            return "0%"
        
        total_current = sum(p['current_population'] for p in population_data)
        total_projected = sum(p['projection_2050'] for p in population_data)
        
        if total_current == 0:
            return "0%"
        
        growth_rate = ((total_projected - total_current) / total_current) * 100
        return f"{growth_rate:.1f}%"
    
    def _calculate_average_aging(self, aging_data):
        """Calcule le taux de vieillissement moyen"""
        if not aging_data:
            return "0%"
        
        avg_aging = sum(a['aging_rate'] for a in aging_data) / len(aging_data)
        return f"{avg_aging:.1f}%"
    
    def _get_timestamp(self):
        """Retourne timestamp ISO"""
        return datetime.now().isoformat()
    
    def get_info(self):
        """Informations du plugin"""
        return {
            'name': self.name,
            'capabilities': ['demographie', 'projections', 'vieillissement', 'transitions'],
            'required_keys': []
        }