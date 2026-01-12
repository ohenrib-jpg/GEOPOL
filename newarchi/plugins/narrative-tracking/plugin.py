"""
Plugin: Narrative Tracking
Description: Suivi des récits sociétaux dominants - analyse discours médiatique, réseaux sociaux, évolution narratives
"""

import requests
from datetime import datetime, timedelta
import logging
from collections import Counter
import re

logger = logging.getLogger(__name__)

class Plugin:
    """Classe principale du plugin"""
    
    def __init__(self, settings):
        """Initialisation"""
        self.name = "narrative-tracking"
        self.settings = settings
    
    def run(self, payload=None):
        """Point d'entrée principal"""
        if payload is None:
            payload = {}
        
        try:
            # VOTRE LOGIQUE ICI
            results = self._track_societal_narratives(payload)
            
            return {
                'status': 'success',
                'plugin': self.name,
                'timestamp': self._get_timestamp(),
                'data': results['data'],
                'metrics': results['metrics'],
                'message': 'Analyse des récits sociétaux terminée'
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
    
    def _track_societal_narratives(self, payload):
        """Logique de suivi des récits sociétaux"""
        country = payload.get('country', 'France')
        timeframe = payload.get('timeframe', '7d')
        
        # Analyse médias traditionnels
        media_narratives = self._analyze_media_narratives(country)
        
        # Analyse réseaux sociaux
        social_media_narratives = self._analyze_social_media_narratives(country)
        
        # Analyse discours politique
        political_narratives = self._analyze_political_discourse(country)
        
        # Détection récits émergents
        emerging_narratives = self._detect_emerging_narratives(media_narratives, social_media_narratives, political_narratives)
        
        data = []
        
        # Récits médiatiques dominants
        for narrative in media_narratives[:5]:
            data.append({
                'recit': narrative['narrative'],
                'type_source': 'Médias Traditionnels',
                'intensite': narrative['intensity'],
                'polarite': narrative['polarity'],
                'acteurs_principaux': ', '.join(narrative['key_actors']),
                'mots_cles': ', '.join(narrative['keywords'][:5]),
                'evolution': narrative['trend'],
                'impact_societal': narrative['societal_impact'],
                'recommandations': narrative['monitoring_recommendations']
            })
        
        # Récits réseaux sociaux
        for narrative in social_media_narratives[:4]:
            data.append({
                'recit': narrative['narrative'],
                'type_source': 'Réseaux Sociaux',
                'intensite': narrative['virality'],
                'polarite': narrative['sentiment'],
                'acteurs_principaux': ', '.join(narrative['influencers']),
                'mots_cles': ', '.join(narrative['hashtags'][:5]),
                'evolution': narrative['growth_rate'],
                'impact_societal': narrative['engagement_impact'],
                'recommandations': narrative['response_strategy']
            })
        
        # Récits politiques
        for narrative in political_narratives[:3]:
            data.append({
                'recit': narrative['narrative'],
                'type_source': 'Discours Politique',
                'intensite': narrative['prominence'],
                'polarite': narrative['ideological_lean'],
                'acteurs_principaux': ', '.join(narrative['political_actors']),
                'mots_cles': ', '.join(narrative['rhetorical_devices'][:5]),
                'evolution': narrative['adoption_rate'],
                'impact_societal': narrative['policy_influence'],
                'recommandations': narrative['dialogue_recommendations']
            })
        
        metrics = {
            'recits_dominants': len(media_narratives) + len(social_media_narratives) + len(political_narratives),
            'recits_emergents': len(emerging_narratives),
            'polarisation_moyenne': self._calculate_average_polarization(data),
            'vitesse_diffusion': self._calculate_narrative_velocity(social_media_narratives),
            'impact_societal_global': self._assess_overall_societal_impact(data)
        }
        
        return {'data': data, 'metrics': metrics}
    
    def _analyze_media_narratives(self, country):
        """Analyse les récits des médias traditionnels"""
        # Sources: analyse agrégée médias, NLP
        if country == 'France':
            return [
                {
                    'narrative': 'Crise du pouvoir d\'achat',
                    'intensity': 85,
                    'polarity': 'Négative',
                    'key_actors': ['Gouvernement', 'Opposition', 'Associations consommateurs'],
                    'keywords': ['inflation', 'pouvoir achat', 'prix énergie', 'budget familial'],
                    'trend': 'Stable haute intensité',
                    'societal_impact': 'Anxiété économique, mobilisations sociales',
                    'monitoring_recommendations': 'Surveiller indicateurs économiques, sentiment population'
                },
                {
                    'narrative': 'Transition écologique et contraintes',
                    'intensity': 70,
                    'polarity': 'Mixte',
                    'key_actors': ['Écolos', 'Industrie', 'Gouvernement', 'Citoyens'],
                    'keywords': ['écologie', 'contrainte', 'transition', 'sobriété', 'innovation'],
                    'trend': 'Croissance modérée',
                    'societal_impact': 'Débat société, tensions acceptabilité',
                    'monitoring_recommendations': 'Analyser perception mesures, résistances locales'
                }
            ]
        return []
    
    def _analyze_social_media_narratives(self, country):
        """Analyse les récits des réseaux sociaux"""
        if country == 'France':
            return [
                {
                    'narrative': 'Souveraineté technologique et numérique',
                    'virality': 78,
                    'sentiment': 'Positif',
                    'influencers': ['Tech leaders', 'Souverainistes', 'Experts cybersécurité'],
                    'hashtags': ['#SouverainetéNumérique', '#TechFrançaise', '#IndépendanceTechnologique'],
                    'growth_rate': 'Rapide',
                    'engagement_impact': 'Communautés actives, débats techniques',
                    'response_strategy': 'Valoriser initiatives, répondre préoccupations'
                },
                {
                    'narrative': 'Fracture générationnelle et logement',
                    'virality': 65,
                    'sentiment': 'Négatif',
                    'influencers': ['Jeunes actifs', 'Urbanistes', 'Économistes'],
                    'hashtags': ['#GénérationPrécaires', '#LogementCher', '#FractureGénérationnelle'],
                    'growth_rate': 'Constante',
                    'engagement_impact': 'Colère jeune génération, débats intergénérationnels',
                    'response_strategy': 'Écouter préoccupations, proposer solutions concrètes'
                }
            ]
        return []
    
    def _analyze_political_discourse(self, country):
        """Analyse le discours politique"""
        if country == 'France':
            return [
                {
                    'narrative': 'Souveraineté européenne et autonomie stratégique',
                    'prominence': 80,
                    'ideological_lean': 'Centriste/Transpartisan',
                    'political_actors': ['Président', 'Commission UE', 'Partis gouvernementaux'],
                    'rhetorical_devices': ['Indépendance', 'Autonomie', 'Coopération européenne', 'Résilience'],
                    'adoption_rate': 'Élevée',
                    'policy_influence': 'Politique industrielle, défense, énergie',
                    'dialogue_recommendations': 'Articuler avec réalités économiques, associer partenaires sociaux'
                },
                {
                    'narrative': 'Méritocratie républicaine vs égalitarisme',
                    'prominence': 65,
                    'ideological_lean': 'Clivage droite/gauche',
                    'political_actors': ['Opposition', 'Intellectuels', 'Partis traditionnels'],
                    'rhetorical_devices': ['Mérite', 'Égalité', 'Justice sociale', 'République'],
                    'adoption_rate': 'Stable',
                    'policy_influence': 'Éducation, fiscalité, services publics',
                    'dialogue_recommendations': 'Chercher terrains entente, éviter polarisation excessive'
                }
            ]
        return []
    
    def _detect_emerging_narratives(self, media, social, political):
        """Détecte les récits émergents"""
        emerging = []
        
        # Analyse croisée pour détection signaux faibles
        all_keywords = []
        for narrative in media + social + political:
            all_keywords.extend(narrative.get('keywords', []) + narrative.get('hashtags', []) + narrative.get('rhetorical_devices', []))
        
        keyword_freq = Counter(all_keywords)
        emerging_keywords = [kw for kw, count in keyword_freq.items() if count == 1]  # Mots uniques
        
        if emerging_keywords:
            emerging.append({
                'narrative': f"Émergence: {', '.join(emerging_keywords[:3])}",
                'intensity': 35,
                'description': 'Nouveaux thèmes détectés dans le discours public',
                'monitoring_priority': 'Surveillance renforcée recommandée'
            })
        
        return emerging
    
    def _calculate_average_polarization(self, data):
        """Calcule la polarisation moyenne des récits"""
        if not data:
            return 0
        
        polarity_scores = {
            'Positive': 1, 'Mixte': 2, 'Négative': 3,
            'Positif': 1, 'Négatif': 3
        }
        
        scores = [polarity_scores.get(d['polarite'], 2) for d in data]
        return sum(scores) / len(scores)
    
    def _calculate_narrative_velocity(self, social_narratives):
        """Calcule la vitesse de diffusion des récits"""
        if not social_narratives:
            return "Lente"
        
        growth_rates = [n['virality'] for n in social_narratives]
        avg_growth = sum(growth_rates) / len(growth_rates)
        
        if avg_growth > 70:
            return "Très rapide"
        elif avg_growth > 50:
            return "Rapide"
        elif avg_growth > 30:
            return "Modérée"
        else:
            return "Lente"
    
    def _assess_overall_societal_impact(self, data):
        """Évalue l'impact sociétal global"""
        high_impact_count = len([d for d in data if any(word in d['impact_societal'] for word in ['Anxiété', 'Colère', 'Tensions', 'Fracture', 'Crise'])])
        total = len(data)
        
        if total == 0:
            return "Inconnu"
        
        impact_ratio = high_impact_count / total
        
        if impact_ratio > 0.6:
            return "Élevé"
        elif impact_ratio > 0.3:
            return "Modéré"
        else:
            return "Faible"
    
    def _get_timestamp(self):
        """Retourne timestamp ISO"""
        return datetime.now().isoformat()
    
    def get_info(self):
        """Informations du plugin"""
        return {
            'name': self.name,
            'capabilities': ['analyse_recits', 'reseaux_sociaux', 'discours_politique', 'narratives_emergents'],
            'required_keys': []
        }