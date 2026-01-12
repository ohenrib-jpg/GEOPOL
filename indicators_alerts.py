# Flask/indicators_alerts.py
"""
Système d'alertes pour les indicateurs économiques
Surveillance des variations significatives
"""

import logging
from datetime import datetime
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class IndicatorAlerts:
    """Système d'alertes pour indicateurs économiques"""
    
    def __init__(self, db_manager=None):
        self.db_manager = db_manager
        self.thresholds = self._load_default_thresholds()
        logger.info("[OK] IndicatorAlerts initialisé")
    
    def _load_default_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Seuils par défaut pour les alertes"""
        return {
            'eurostat_gdp': {
                'variance_threshold': 0.5,  # 0.5% de variation
                'description': 'PIB'
            },
            'eurostat_hicp': {
                'variance_threshold': 0.3,  # 0.3% d'inflation
                'description': 'Inflation'
            },
            'eurostat_unemployment': {
                'variance_threshold': 0.2,  # 0.2% de chômage
                'description': 'Chômage'
            },
            'eurostat_gini': {
                'variance_threshold': 1.0,  # 1 point GINI
                'description': 'Inégalités'
            },
            'insee_inflation': {
                'variance_threshold': 0.3,
                'description': 'Inflation INSEE'
            }
        }
    
    def check_alerts(self, indicator_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Vérifie si des indicateurs dépassent les seuils critiques"""
        alerts = []
        
        for indicator_id, data in indicator_data.items():
            # Pour les données du format dashboard
            if isinstance(data, dict) and 'change_percent' in data:
                threshold_info = self.thresholds.get(indicator_id.split('_')[1] if '_' in indicator_id else indicator_id)
                
                if threshold_info:
                    change_percent = data['change_percent']
                    threshold = threshold_info['variance_threshold']
                    
                    if abs(change_percent) > threshold:
                        alerts.append({
                            'indicator_id': indicator_id,
                            'indicator_name': data.get('name', indicator_id),
                            'current_value': data.get('value', 'N/A'),
                            'change_percent': change_percent,
                            'threshold': threshold,
                            'severity': self._calculate_severity(change_percent, threshold),
                            'category': data.get('category', 'unknown'),
                            'timestamp': datetime.now().isoformat(),
                            'message': f"{data.get('name', indicator_id)} : {change_percent:+.2f}% (seuil: ±{threshold}%)"
                        })
        
        return sorted(alerts, key=lambda x: abs(x['change_percent']), reverse=True)
    
    def _calculate_severity(self, change_percent: float, threshold: float) -> str:
        """Calcule la sévérité de l'alerte"""
        abs_change = abs(change_percent)
        if abs_change > threshold * 3:
            return 'critical'
        elif abs_change > threshold * 2:
            return 'high'
        elif abs_change > threshold * 1.5:
            return 'medium'
        else:
            return 'low'
    
    def get_alert_summary(self, indicator_data: Dict[str, Any]) -> Dict[str, Any]:
        """Résumé des alertes par sévérité"""
        alerts = self.check_alerts(indicator_data)
        
        summary = {
            'total_alerts': len(alerts),
            'by_severity': {},
            'by_category': {},
            'most_critical': alerts[:3] if alerts else []
        }
        
        # Regrouper par sévérité
        for alert in alerts:
            severity = alert['severity']
            summary['by_severity'][severity] = summary['by_severity'].get(severity, 0) + 1
            
            category = alert['category']
            summary['by_category'][category] = summary['by_category'].get(category, 0) + 1
        
        return summary


# Test du module
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Données de test
    test_data = {
        'eurostat_gdp': {
            'name': 'PIB France',
            'value': 695.2,
            'change_percent': -1.2,  # Variation importante
            'category': 'macro'
        },
        'eurostat_hicp': {
            'name': 'Inflation',
            'value': 2.2,
            'change_percent': 0.1,   # Variation normale
            'category': 'prices'
        }
    }
    
    alerts_system = IndicatorAlerts()
    alerts = alerts_system.check_alerts(test_data)
    
    print("=" * 50)
    print("🔔 ALERTES INDICATEURS")
    print("=" * 50)
    
    for alert in alerts:
        print(f"\n🚨 {alert['severity'].upper()}: {alert['message']}")
        print(f"   Catégorie: {alert['category']}")
        print(f"   Valeur: {alert['current_value']}")
