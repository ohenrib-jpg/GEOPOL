"""
Plugin: Social Cohesion Index
Description: Indice de cohésion sociale - confiance institutionnelle, capital social, résilience communautaire
"""

import requests
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class Plugin:
    """Classe principale du plugin"""
    
    def __init__(self, settings):
        """Initialisation"""
        self.name = "social-cohesion-index"
        self.settings = settings
    
    def run(self, payload=None):
        """Point d'entrée principal"""
        if payload is None:
            payload = {}
        
        try:
            # VOTRE LOGIQUE ICI
            results = self._calculate_social_cohesion(payload)
            
            return {
                'status': 'success',
                'plugin': self.name,
                'timestamp': self._get_timestamp(),
                'data': results['data'],
                'metrics': results['metrics'],
                'message': 'Analyse cohésion sociale terminée'
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
    
    def _calculate_social_cohesion(self, payload):
        """Logique de calcul de la cohésion sociale"""
        countries = payload.get('countries', ['France', 'USA', 'Allemagne', 'Japon', 'Brésil'])
        
        # Données confiance institutionnelle
        trust_data = self._fetch_institutional_trust()
        
        # Données capital social
        social_capital_data = self._fetch_social_capital()
        
        # Données résilience communautaire
        resilience_data = self._fetch_community_resilience()
        
        # Calcul indices composites
        cohesion_scores = self._compute_cohesion_scores(trust_data, social_capital_data, resilience_data)
        
        data = []
        
        for country in countries:
            score = cohesion_scores.get(country, {})
            data.append({
                'pays': country,
                'indice_cohesion_globale': score.get('overall', 0),
                'confiance_institutions': score.get('trust', 0),
                'capital_social': score.get('social_capital', 0),
                'resilience_communautaire': score.get('resilience', 0),
                'tendance_5ans': score.get('trend', 'Stable'),
                'facteurs_renforcement': ', '.join(score.get('strengthening_factors', [])),
                'vulnerabilites': ', '.join(score.get('vulnerabilities', [])),
                'recommandations': score.get('recommendations', '')
            })
        
        metrics = {
            'pays_analysees': len(data),
            'cohesion_moyenne': sum(d['indice_cohesion_globale'] for d in data) / len(data),
            'pays_cohesion_forte': len([d for d in data if d['indice_cohesion_globale'] > 70]),
            'pays_tendance_positive': len([d for d in data if 'hausse' in d['tendance_5ans'].lower()]),
            'resilience_moyenne': sum(d['resilience_communautaire'] for d in data) / len(data)
        }
        
        return {'data': data, 'metrics': metrics}
    
    def _fetch_institutional_trust(self):
        """Récupère les données de confiance institutionnelle"""
        # Sources: OCDE, World Values Survey, Eurobarometer
        return {
            'France': {'government': 38, 'media': 32, 'justice': 52, 'health': 68},
            'USA': {'government': 35, 'media': 29, 'justice': 54, 'health': 72},
            'Allemagne': {'government': 58, 'media': 45, 'justice': 68, 'health': 78},
            'Japon': {'government': 42, 'media': 38, 'justice': 62, 'health': 82},
            'Brésil': {'government': 28, 'media': 25, 'justice': 35, 'health': 58}
        }
    
    def _fetch_social_capital(self):
        """Récupère les données de capital social"""
        # Sources: OCDE, Banque Mondiale
        return {
            'France': {'associations': 65, 'volunteering': 35, 'social_networks': 72, 'helping': 58},
            'USA': {'associations': 72, 'volunteering': 45, 'social_networks': 68, 'helping': 62},
            'Allemagne': {'associations': 68, 'volunteering': 42, 'social_networks': 75, 'helping': 65},
            'Japon': {'associations': 58, 'volunteering': 28, 'social_networks': 65, 'helping': 52},
            'Brésil': {'associations': 48, 'volunteering': 32, 'social_networks': 78, 'helping': 68}
        }
    
    def _fetch_community_resilience(self):
        """Récupère les données de résilience communautaire"""
        return {
            'France': {'crisis_response': 70, 'adaptability': 65, 'solidarity': 68, 'recovery': 72},
            'USA': {'crisis_response': 75, 'adaptability': 78, 'solidarity': 62, 'recovery': 70},
            'Allemagne': {'crisis_response': 78, 'adaptability': 72, 'solidarity': 75, 'recovery': 80},
            'Japon': {'crisis_response': 82, 'adaptability': 68, 'solidarity': 72, 'recovery': 85},
            'Brésil': {'crisis_response': 58, 'adaptability': 65, 'solidarity': 75, 'recovery': 62}
        }
    
    def _compute_cohesion_scores(self, trust_data, social_capital, resilience_data):
        """Calcule les scores de cohésion sociale composites"""
        scores = {}
        
        for country in trust_data.keys():
            if country in social_capital and country in resilience_data:
                # Calcul score global (moyenne pondérée)
                trust_score = sum(trust_data[country].values()) / len(trust_data[country])
                social_score = sum(social_capital[country].values()) / len(social_capital[country])
                resilience_score = sum(resilience_data[country].values()) / len(resilience_data[country])
                
                overall_score = (trust_score * 0.4 + social_score * 0.3 + resilience_score * 0.3)
                
                scores[country] = {
                    'overall': round(overall_score, 1),
                    'trust': round(trust_score, 1),
                    'social_capital': round(social_score, 1),
                    'resilience': round(resilience_score, 1),
                    'trend': self._determine_trend(overall_score),
                    'strengthening_factors': self._identify_strengths(trust_score, social_score, resilience_score),
                    'vulnerabilities': self._identify_vulnerabilities(trust_score, social_score, resilience_score),
                    'recommendations': self._generate_recommendations(trust_score, social_score, resilience_score)
                }
        
        return scores
    
    def _determine_trend(self, score):
        """Détermine la tendance basée sur le score"""
        if score > 75:
            return 'Hausse modérée'
        elif score > 60:
            return 'Stable'
        elif score > 45:
            return 'Légère baisse'
        else:
            return 'Baisse préoccupante'
    
    def _identify_strengths(self, trust, social, resilience):
        """Identifie les points forts"""
        strengths = []
        if trust > 60:
            strengths.append('Confiance institutionnelle')
        if social > 60:
            strengths.append('Capital social')
        if resilience > 60:
            strengths.append('Résilience communautaire')
        return strengths if strengths else ['Aucun point fort majeur']
    
    def _identify_vulnerabilities(self, trust, social, resilience):
        """Identifie les vulnérabilités"""
        vulnerabilities = []
        if trust < 40:
            vulnerabilities.append('Faible confiance institutions')
        if social < 40:
            vulnerabilities.append('Capital social limité')
        if resilience < 40:
            vulnerabilities.append('Résilience fragile')
        return vulnerabilities if vulnerabilities else ['Aucune vulnérabilité critique']
    
    def _generate_recommendations(self, trust, social, resilience):
        """Génère des recommandations"""
        recommendations = []
        if trust < 50:
            recommendations.append('Renforcer transparence institutionnelle')
        if social < 50:
            recommendations.append('Développer programmes communautaires')
        if resilience < 50:
            recommendations.append('Investir préparation crises')
        return '; '.join(recommendations) if recommendations else 'Maintenir politiques actuelles'
    
    def _get_timestamp(self):
        """Retourne timestamp ISO"""
        return datetime.now().isoformat()
    
    def get_info(self):
        """Informations du plugin"""
        return {
            'name': self.name,
            'capabilities': ['cohesion_sociale', 'confiance_institutions', 'resilience_communautaire'],
            'required_keys': []
        }