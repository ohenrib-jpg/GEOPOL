"""Modèles de données pour les alertes"""
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Dict, Any, List
import json

@dataclass
class AlertRule:
    """Règle d'alerte configurable par l'utilisateur"""
    id: str
    name: str
    category: str  # 'financial', 'travel', 'sdr'
    enabled: bool = True
    severity: str = 'warning'  # 'info', 'warning', 'critical'
    condition: str = ""  # Expression Python simple
    parameters: Dict[str, Any] = None
    message_template: str = ""
    created_at: datetime = None
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.parameters is None:
            self.parameters = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire pour JSON/YAML"""
        data = asdict(self)
        # Convertir les datetime en string
        for key in ['created_at', 'last_triggered']:
            if data[key]:
                data[key] = data[key].isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AlertRule':
        """Crée depuis un dictionnaire"""
        # Convertir les strings en datetime
        for key in ['created_at', 'last_triggered']:
            if key in data and data[key]:
                data[key] = datetime.fromisoformat(data[key])
        return cls(**data)

@dataclass
class Alert:
    """Instance d'une alerte déclenchée"""
    id: str
    rule_id: str
    rule_name: str
    category: str
    severity: str
    message: str
    timestamp: datetime
    data: Dict[str, Any]
    acknowledged: bool = False
    archived: bool = False
    
    def __post_init__(self):
        if not self.id:
            self.id = f"alert_{self.timestamp.timestamp()}_{hash(self.message) % 10000:04d}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit en dictionnaire"""
        return {
            'id': self.id,
            'rule_id': self.rule_id,
            'rule_name': self.rule_name,
            'category': self.category,
            'severity': self.severity,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'acknowledged': self.acknowledged,
            'archived': self.archived,
            'data_summary': self.get_data_summary()
        }
    
    def get_data_summary(self) -> str:
        """Résumé des données pour affichage"""
        if self.category == 'financial':
            symbol = self.data.get('symbol', '')
            change = self.data.get('change_percent', 0)
            return f"{symbol}: {change:+.2f}%"
        elif self.category == 'travel':
            country = self.data.get('country_name', '')
            risk = self.data.get('risk_level', 0)
            return f"{country} (niveau {risk})"
        return json.dumps(self.data, ensure_ascii=False)[:100]
    
    def acknowledge(self):
        """Marque l'alerte comme lue"""
        self.acknowledged = True
    
    def archive(self):
        """Archive l'alerte"""
        self.archived = True