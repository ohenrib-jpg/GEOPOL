"""Gestionnaire principal des alertes"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

from .alert_engine import AlertEngine
from .alert_config import AlertConfig
from .models import Alert, AlertRule

logger = logging.getLogger(__name__)

class AlertManager:
    """Gestionnaire central des alertes"""
    
    def __init__(self, db_path: Optional[str] = None):
        self.engine = AlertEngine()
        self.config = AlertConfig()
        self.db_path = db_path
        
        # Charger les règles
        self._load_rules_from_config()
        
        # Alertes actives
        self.active_alerts: List[Alert] = []
        self.alert_history: List[Alert] = []
        
        # Statistiques
        self.stats = {
            'total_alerts': 0,
            'alerts_today': 0,
            'by_category': {'financial': 0, 'travel': 0, 'sdr': 0},
            'by_severity': {'info': 0, 'warning': 0, 'critical': 0}
        }
        
        # Initialiser
        self._init_stats()
    
    def _load_rules_from_config(self):
        """Charge les règles depuis la configuration"""
        try:
            rules_data = self.config.rules
            self.engine.load_rules(rules_data)
            logger.info(f"Règles chargées: {len(rules_data)}")
        except Exception as e:
            logger.error(f"Erreur chargement règles: {e}")
    
    def _init_stats(self):
        """Initialise les statistiques depuis les archives"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            today_dir = self.config.archive_dir / today
            
            if today_dir.exists():
                csv_file = today_dir / 'alerts.csv'
                if csv_file.exists():
                    import csv
                    with open(csv_file, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        self.stats['alerts_today'] = sum(1 for _ in reader)
        except Exception as e:
            logger.error(f"Erreur initialisation stats: {e}")
    
    def check_financial_data(self, instruments: List[Dict[str, Any]], 
                            previous_data: Optional[Dict[str, Dict]] = None) -> List[Alert]:
        """Vérifie les données financières pour alertes"""
        alerts = []
        
        for instrument in instruments:
            symbol = instrument.get('symbol')
            previous = previous_data.get(symbol) if previous_data else None
            
            instrument_alerts = self.engine.evaluate_financial_data(instrument, previous)
            alerts.extend(instrument_alerts)
        
        return self._process_new_alerts(alerts)
    
    def check_travel_data(self, advisories: List[Dict[str, Any]],
                         previous_data: Optional[Dict[str, Dict]] = None) -> List[Alert]:
        """Vérifie les données de voyage pour alertes"""
        alerts = []
        
        for advisory in advisories:
            country_code = advisory.get('country_code')
            previous = previous_data.get(country_code) if previous_data else None
            
            travel_alerts = self.engine.evaluate_travel_data(advisory, previous)
            alerts.extend(travel_alerts)
        
        return self._process_new_alerts(alerts)
    
    def _process_new_alerts(self, new_alerts: List[Alert]) -> List[Alert]:
        """Traite les nouvelles alertes"""
        valid_alerts = []
        
        for alert in new_alerts:
            # Vérifier si une alerte similaire existe déjà
            if not self._is_duplicate_alert(alert):
                # Ajouter aux alertes actives
                self.active_alerts.append(alert)
                self.alert_history.append(alert)
                
                # Mettre à jour les statistiques
                self._update_stats(alert)
                
                # Archiver
                self.config.archive_alert(alert.to_dict())
                
                valid_alerts.append(alert)
                
                logger.info(f"Alerte déclenchée: {alert.rule_name} ({alert.severity})")
        
        return valid_alerts
    
    def _is_duplicate_alert(self, alert: Alert, time_window: int = 3600) -> bool:
        """Vérifie si une alerte similaire a été déclenchée récemment"""
        for existing in self.active_alerts[-20:]:  # Vérifier les 20 dernières
            if (existing.rule_id == alert.rule_id and 
                existing.data.get('symbol') == alert.data.get('symbol') and
                (existing.timestamp - alert.timestamp).total_seconds() < time_window):
                return True
        return False
    
    def _update_stats(self, alert: Alert):
        """Met à jour les statistiques"""
        self.stats['total_alerts'] += 1
        self.stats['alerts_today'] += 1
        self.stats['by_category'][alert.category] = self.stats['by_category'].get(alert.category, 0) + 1
        self.stats['by_severity'][alert.severity] = self.stats['by_severity'].get(alert.severity, 0) + 1
    
    def get_active_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retourne les alertes actives non lues"""
        unread = [a for a in self.active_alerts if not a.acknowledged]
        return [a.to_dict() for a in unread[:limit]]
    
    def get_all_alerts(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Retourne toutes les alertes"""
        return [a.to_dict() for a in self.alert_history[-limit:]]
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Marque une alerte comme lue"""
        for alert in self.active_alerts:
            if alert.id == alert_id:
                alert.acknowledge()
                return True
        return False
    
    def acknowledge_all(self):
        """Marque toutes les alertes comme lues"""
        for alert in self.active_alerts:
            alert.acknowledge()
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques"""
        return {
            **self.stats,
            'active_count': len([a for a in self.active_alerts if not a.acknowledged]),
            'rules_count': len(self.engine.get_enabled_rules())
        }
    
    def get_rules(self) -> List[Dict[str, Any]]:
        """Retourne toutes les règles"""
        return [rule.to_dict() for rule in self.engine.rules]
    
    def update_rule(self, rule_id: str, updates: Dict[str, Any]) -> bool:
        """Met à jour une règle"""
        rule = self.engine.get_rule_by_id(rule_id)
        if not rule:
            return False
        
        # Appliquer les mises à jour
        for key, value in updates.items():
            if hasattr(rule, key):
                setattr(rule, key, value)
        
        # Sauvegarder la configuration
        self._save_rules_to_config()
        
        return True
    
    def add_rule(self, rule_data: Dict[str, Any]) -> bool:
        """Ajoute une nouvelle règle"""
        try:
            rule = AlertRule.from_dict(rule_data)
            self.engine.add_rule(rule)
            self._save_rules_to_config()
            return True
        except Exception as e:
            logger.error(f"Erreur ajout règle: {e}")
            return False
    
    def _save_rules_to_config(self):
        """Sauvegarde toutes les règles dans la configuration"""
        rules_data = [rule.to_dict() for rule in self.engine.rules]
        self.config.save_rules(rules_data)
    
    def cleanup_old_alerts(self, days_to_keep: int = 30):
        """Nettoie les anciennes alertes"""
        # Nettoyer les archives
        self.config.cleanup_old_alerts(days_to_keep)
        
        # Nettoyer l'historique en mémoire
        cutoff = datetime.utcnow() - timedelta(days=days_to_keep)
        self.alert_history = [a for a in self.alert_history if a.timestamp > cutoff]
        self.active_alerts = [a for a in self.active_alerts if a.timestamp > cutoff]