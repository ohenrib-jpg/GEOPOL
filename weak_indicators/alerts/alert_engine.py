"""Moteur d'évaluation d'alertes"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import math

from .models import Alert, AlertRule

logger = logging.getLogger(__name__)

class AlertEngine:
    """Moteur d'évaluation des règles d'alertes"""
    
    # Fonctions mathématiques autorisées dans les conditions
    SAFE_BUILTINS = {
        'abs': abs,
        'round': round,
        'min': min,
        'max': max,
        'len': len,
        'sum': sum,
        'math': math
    }
    
    def __init__(self):
        self.rules: List[AlertRule] = []
        self.trigger_history: Dict[str, datetime] = {}
        
    def add_rule(self, rule: AlertRule):
        """Ajoute une règle d'alerte"""
        self.rules.append(rule)
        logger.info(f"Règle ajoutée: {rule.name} ({rule.category})")
    
    def load_rules(self, rules: List[Dict[str, Any]]):
        """Charge des règles depuis des dictionnaires"""
        for rule_data in rules:
            rule = AlertRule.from_dict(rule_data)
            self.add_rule(rule)
    
    def evaluate_financial_data(self, instrument: Dict[str, Any], 
                               previous_data: Optional[Dict[str, Any]] = None) -> List[Alert]:
        """Évalue les données financières contre les règles"""
        alerts = []
        
        for rule in self.rules:
            if not rule.enabled or rule.category != 'financial':
                continue
            
            # Vérifier le cooldown (éviter spam)
            if self._is_in_cooldown(rule):
                continue
            
            try:
                # Préparer le contexte d'évaluation
                context = {
                    'data': instrument,
                    'previous': previous_data,
                    'current_price': instrument.get('current_price', 0),
                    'change_percent': instrument.get('change_percent', 0),
                    'volume': instrument.get('volume', 0),
                    'symbol': instrument.get('symbol', '')
                }
                
                # Évaluer la condition
                if self._evaluate_condition(rule.condition, context):
                    # Créer l'alerte
                    alert = self._create_alert(rule, instrument)
                    alerts.append(alert)
                    
                    # Mettre à jour la règle
                    rule.last_triggered = datetime.utcnow()
                    rule.trigger_count += 1
                    
            except Exception as e:
                logger.error(f"Erreur évaluation règle {rule.name}: {e}")
        
        return alerts
    
    def evaluate_travel_data(self, advisory: Dict[str, Any],
                            previous_advisory: Optional[Dict[str, Any]] = None) -> List[Alert]:
        """Évalue les données de voyage contre les règles"""
        alerts = []
        
        for rule in self.rules:
            if not rule.enabled or rule.category != 'travel':
                continue
            
            if self._is_in_cooldown(rule):
                continue
            
            try:
                # Vérifier si le pays est concerné par la règle
                countries = rule.parameters.get('countries', [])
                if countries and advisory.get('country_code') not in countries:
                    continue
                
                context = {
                    'data': advisory,
                    'previous': previous_advisory,
                    'risk_level': advisory.get('risk_level', 1),
                    'country_code': advisory.get('country_code', ''),
                    'country_name': advisory.get('country_name', ''),
                    'source': advisory.get('source', '')
                }
                
                if previous_advisory:
                    context['previous_risk'] = previous_advisory.get('risk_level', 1)
                    context['risk_increased'] = advisory.get('risk_level', 1) > previous_advisory.get('risk_level', 1)
                    context['risk_decreased'] = advisory.get('risk_level', 1) < previous_advisory.get('risk_level', 1)
                
                if self._evaluate_condition(rule.condition, context):
                    alert = self._create_alert(rule, advisory)
                    alerts.append(alert)
                    
                    rule.last_triggered = datetime.utcnow()
                    rule.trigger_count += 1
                    
            except Exception as e:
                logger.error(f"Erreur évaluation voyage {rule.name}: {e}")
        
        return alerts
    
    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Évalue une condition Python de manière sécurisée"""
        if not condition:
            return False
        
        try:
            # Nettoyer et valider la condition
            condition = condition.strip()
            if not condition:
                return False
            
            # Créer un environnement sécurisé
            safe_globals = {'__builtins__': None}
            safe_globals.update(self.SAFE_BUILTINS)
            safe_globals.update(context)
            
            # Évaluer
            result = eval(condition, safe_globals, {})
            return bool(result)
            
        except Exception as e:
            logger.warning(f"Condition invalide '{condition}': {e}")
            return False
    
    def _create_alert(self, rule: AlertRule, data: Dict[str, Any]) -> Alert:
        """Crée une instance d'alerte"""
        # Générer le message
        message = rule.message_template.format(**data) if rule.message_template else \
                 self._generate_default_message(rule, data)
        
        return Alert(
            id=f"{rule.id}_{datetime.utcnow().timestamp():.0f}",
            rule_id=rule.id,
            rule_name=rule.name,
            category=rule.category,
            severity=rule.severity,
            message=message,
            timestamp=datetime.utcnow(),
            data=data
        )
    
    def _generate_default_message(self, rule: AlertRule, data: Dict[str, Any]) -> str:
        """Génère un message par défaut"""
        if rule.category == 'financial':
            symbol = data.get('symbol', 'Instrument')
            change = data.get('change_percent', 0)
            return f"{symbol}: {change:+.2f}% - {rule.name}"
        elif rule.category == 'travel':
            country = data.get('country_name', 'Pays inconnu')
            risk = data.get('risk_level', 1)
            return f"{country}: Niveau risque {risk} - {rule.name}"
        return f"Alerte {rule.name} déclenchée"
    
    def _is_in_cooldown(self, rule: AlertRule) -> bool:
        """Vérifie si une règle est en période de repos"""
        if not rule.last_triggered:
            return False
        
        # Cooldown basé sur la sévérité
        cooldowns = {
            'info': timedelta(minutes=30),
            'warning': timedelta(minutes=15),
            'critical': timedelta(minutes=5)
        }
        
        cooldown = cooldowns.get(rule.severity, timedelta(minutes=30))
        time_since_trigger = datetime.utcnow() - rule.last_triggered
        
        return time_since_trigger < cooldown
    
    def get_enabled_rules(self, category: Optional[str] = None) -> List[AlertRule]:
        """Retourne les règles actives"""
        rules = [r for r in self.rules if r.enabled]
        if category:
            rules = [r for r in rules if r.category == category]
        return rules
    
    def get_rule_by_id(self, rule_id: str) -> Optional[AlertRule]:
        """Trouve une règle par son ID"""
        for rule in self.rules:
            if rule.id == rule_id:
                return rule
        return None