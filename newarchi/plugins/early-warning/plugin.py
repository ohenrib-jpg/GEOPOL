"""
Plugin: Early Warning System
Description: Système d'alerte précoce - indicateurs avancés et signaux faibles
"""

from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class Plugin:
    """Classe principale du plugin"""
    
    def __init__(self, settings):
        """Initialisation"""
        self.name = "early-warning"
        self.settings = settings
    
    def run(self, payload=None):
        """Point d'entrée principal"""
        if payload is None:
            payload = {}
        
        try:
            # VOTRE LOGIQUE ICI
            results = self._generate_early_warnings(payload)
            
            return {
                'status': 'success',
                'plugin': self.name,
                'timestamp': self._get_timestamp(),
                'data': results['data'],
                'metrics': results['metrics'],
                'message': 'Système d\'alerte précoce exécuté'
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
    
    def _generate_early_warnings(self, payload):
        """Logique de génération d'alertes précoces"""
        warning_type = payload.get('warning_type', 'all')
        time_horizon = payload.get('time_horizon', '3m')
        
        # Collecte des signaux faibles
        weak_signals = self._collect_weak_signals()
        
        # Analyse des indicateurs avancés
        leading_indicators = self._analyze_leading_indicators()
        
        # Modèles prédictifs
        predictive_models = self._run_predictive_models(weak_signals, leading_indicators)
        
        # Génération des alertes
        alerts = self._generate_alerts(weak_signals, leading_indicators, predictive_models)
        
        data = []
        
        # Alertes de sécurité
        for alert in alerts['security_alerts'][:5]:
            data.append({
                'type_alerte': 'Sécurité',
                'niveau_urgence': alert['urgency'],
                'region': alert['region'],
                'signal_detecte': alert['signal'],
                'probabilite': alert['probability'],
                'delai_estime': alert['timeframe'],
                'recommandations': alert['recommendations']
            })
        
        # Alertes économiques
        for alert in alerts['economic_alerts'][:5]:
            data.append({
                'type_alerte': 'Économique',
                'niveau_urgence': alert['urgency'],
                'region': alert['region'],
                'signal_detecte': alert['signal'],
                'probabilite': alert['probability'],
                'delai_estime': alert['timeframe'],
                'recommandations': alert['recommendations']
            })
        
        # Alertes politiques
        for alert in alerts['political_alerts'][:5]:
            data.append({
                'type_alerte': 'Politique',
                'niveau_urgence': alert['urgency'],
                'region': alert['region'],
                'signal_detecte': alert['signal'],
                'probabilite': alert['probability'],
                'delai_estime': alert['timeframe'],
                'recommandations': alert['recommendations']
            })
        
        metrics = {
            'alertes_actives': len(alerts['security_alerts'] + alerts['economic_alerts'] + alerts['political_alerts']),
            'alertes_haute_urgence': len([a for a in alerts['security_alerts'] + alerts['economic_alerts'] + alerts['political_alerts'] if a['urgency'] == 'Haute']),
            'signaux_faibles_detectes': len(weak_signals),
            'indicateurs_avances_anormaux': len([i for i in leading_indicators if i['status'] == 'Anormal']),
            'fiabilité_predictions': self._calculate_prediction_reliability(predictive_models)
        }
        
        return {'data': data, 'metrics': metrics}
    
    def _collect_weak_signals(self):
        """Collecte les signaux faibles"""
        return [
            {
                'type': 'Diplomatique',
                'signal': 'Annulation soudaine de sommets bilatéraux',
                'region': 'Asie-Pacifique',
                'confidence': 0.7,
                'trend': 'Détérioration'
            },
            {
                'type': 'Économique',
                'signal': 'Accumulation dette corporate secteur immobilier',
                'region': 'Chine',
                'confidence': 0.8,
                'trend': 'Accélération'
            },
            {
                'type': 'Sécurité',
                'signal': 'Augmentation cyber-attaques infrastructures critiques',
                'region': 'Europe',
                'confidence': 0.75,
                'trend': 'Escalade'
            },
            {
                'type': 'Social',
                'signal': 'Mobilisations étudiantes sur enjeux climatiques',
                'region': 'Amérique du Nord',
                'confidence': 0.6,
                'trend': 'Émergence'
            }
        ]
    
    def _analyze_leading_indicators(self):
        """Analyse les indicateurs avancés"""
        return [
            {
                'indicator': 'Spread des obligations souveraines',
                'region': 'Économies émergentes',
                'status': 'Anormal',
                'value': '+150bps',
                'threshold': '+100bps',
                'interpretation': 'Stress marché dette'
            },
            {
                'indicator': 'Prix des contrats à terme pétrole',
                'region': 'Global',
                'status': 'Anormal',
                'value': '+25% volatility',
                'threshold': '+20% volatility',
                'interpretation': 'Instabilité énergétique'
            },
            {
                'indicator': 'Trafic internet transfrontalier',
                'region': 'Europe de l\'Est',
                'status': 'Normal',
                'value': '-5%',
                'threshold': '-15%',
                'interpretation': 'Stable'
            },
            {
                'indicator': 'Reserves de change',
                'region': 'Turquie',
                'status': 'Anormal',
                'value': '-30%',
                'threshold': '-25%',
                'interpretation': 'Pression sur devise'
            }
        ]
    
    def _run_predictive_models(self, weak_signals, leading_indicators):
        """Exécute les modèles prédictifs"""
        models = []
        
        # Modèle de risque géopolitique
        geopolitical_risk = self._calculate_geopolitical_risk(weak_signals)
        models.append({
            'model': 'Risque Géopolitique',
            'output': geopolitical_risk['level'],
            'confidence': geopolitical_risk['confidence'],
            'time_horizon': '1-3 mois'
        })
        
        # Modèle de stabilité économique
        economic_stability = self._calculate_economic_stability(leading_indicators)
        models.append({
            'model': 'Stabilité Économique',
            'output': economic_stability['level'],
            'confidence': economic_stability['confidence'],
            'time_horizon': '3-6 mois'
        })
        
        # Modèle de sécurité régionale
        regional_security = self._calculate_regional_security(weak_signals, leading_indicators)
        models.append({
            'model': 'Sécurité Régionale',
            'output': regional_security['level'],
            'confidence': regional_security['confidence'],
            'time_horizon': '1-2 mois'
        })
        
        return models
    
    def _generate_alerts(self, weak_signals, leading_indicators, predictive_models):
        """Génère les alertes basées sur l'analyse"""
        alerts = {
            'security_alerts': [],
            'economic_alerts': [],
            'political_alerts': []
        }
        
        # Alertes de sécurité
        security_indicators = [i for i in leading_indicators if 'cyber' in i['indicator'].lower() or 'infrastructure' in i['indicator'].lower()]
        if security_indicators:
            alerts['security_alerts'].append({
                'urgency': 'Haute',
                'region': 'Europe',
                'signal': 'Augmentation cyber-attaques infrastructures critiques',
                'probability': 0.75,
                'timeframe': '1-2 mois',
                'recommendations': 'Renforcer cyber-défenses, plans continuité'
            })
        
        # Alertes économiques
        economic_anomalies = [i for i in leading_indicators if i['status'] == 'Anormal' and any(word in i['indicator'].lower() for word in ['dette', 'obligation', 'réserve'])]
        if economic_anomalies:
            alerts['economic_alerts'].append({
                'urgency': 'Moyenne',
                'region': 'Économies émergentes',
                'signal': 'Stress sur marchés dette souveraine',
                'probability': 0.65,
                'timeframe': '3-6 mois',
                'recommendations': 'Diversification portefeuille, couverture risque'
            })
        
        # Alertes politiques
        diplomatic_signals = [s for s in weak_signals if s['type'] == 'Diplomatique' and s['confidence'] > 0.6]
        if diplomatic_signals:
            alerts['political_alerts'].append({
                'urgency': 'Moyenne',
                'region': 'Asie-Pacifique',
                'signal': 'Détérioration relations bilatérales',
                'probability': 0.7,
                'timeframe': '2-4 mois',
                'recommendations': 'Diplomatie préventive, canaux de dialogue'
            })
        
        return alerts
    
    def _calculate_geopolitical_risk(self, weak_signals):
        """Calcule le risque géopolitique"""
        high_confidence_signals = [s for s in weak_signals if s['confidence'] >= 0.7]
        
        if len(high_confidence_signals) >= 3:
            return {'level': 'Élevé', 'confidence': 0.8}
        elif len(high_confidence_signals) >= 1:
            return {'level': 'Moyen', 'confidence': 0.6}
        else:
            return {'level': 'Faible', 'confidence': 0.7}
    
    def _calculate_economic_stability(self, leading_indicators):
        """Calcule la stabilité économique"""
        abnormal_indicators = [i for i in leading_indicators if i['status'] == 'Anormal']
        
        if len(abnormal_indicators) >= 2:
            return {'level': 'Instable', 'confidence': 0.75}
        elif len(abnormal_indicators) >= 1:
            return {'level': 'À surveiller', 'confidence': 0.6}
        else:
            return {'level': 'Stable', 'confidence': 0.8}
    
    def _calculate_regional_security(self, weak_signals, leading_indicators):
        """Calcule la sécurité régionale"""
        security_signals = [s for s in weak_signals if 'sécurité' in s['type'].lower() or 'cyber' in s['signal'].lower()]
        security_indicators = [i for i in leading_indicators if 'sécurité' in i['interpretation'].lower()]
        
        if security_signals and security_indicators:
            return {'level': 'Dégradée', 'confidence': 0.7}
        elif security_signals or security_indicators:
            return {'level': 'À risque', 'confidence': 0.6}
        else:
            return {'level': 'Stable', 'confidence': 0.8}
    
    def _calculate_prediction_reliability(self, predictive_models):
        """Calcule la fiabilité globale des prédictions"""
        if not predictive_models:
            return 0
        
        avg_confidence = sum(model['confidence'] for model in predictive_models) / len(predictive_models)
        return int(avg_confidence * 100)
    
    def _get_timestamp(self):
        """Retourne timestamp ISO"""
        return datetime.now().isoformat()
    
    def get_info(self):
        """Informations du plugin"""
        return {
            'name': self.name,
            'capabilities': ['alertes_precoces', 'signaux_faibles', 'modeles_predictifs'],
            'required_keys': []  # Modèles internes
        }