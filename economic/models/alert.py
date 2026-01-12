"""
Modèles d'alerte pour le module économique
"""
from dataclasses import dataclass, asdict
from typing import Optional, List
from datetime import datetime
import json

@dataclass
class EconomicAlert:
    """Configuration d'une alerte économique"""
    id: Optional[int] = None
    name: str = ""
    description: str = ""
    indicator_id: str = ""           # ID de l'indicateur (ex: 'sp500', 'gold', 'eur_usd')
    indicator_type: str = ""         # 'index', 'commodity', 'forex', 'crypto', 'macro'
    condition: str = ""              # '>', '<', 'change_abs', 'change_pct'
    threshold: float = 0.0           # valeur seuil
    threshold_type: str = ""         # 'absolute', 'percentage'
    active: bool = True
    user_id: Optional[int] = None    # ID utilisateur (pour multi-utilisateurs futurs)
    email_notification: bool = True  # Envoyer un email
    dashboard_notification: bool = True  # Afficher dans le dashboard
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Convertit en dictionnaire"""
        data = asdict(self)
        # Convertir les datetime en string ISO
        data['created_at'] = self.created_at.isoformat() if self.created_at else None
        data['updated_at'] = self.updated_at.isoformat() if self.updated_at else None
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'EconomicAlert':
        """Crée depuis un dictionnaire"""
        # Convertir les strings ISO en datetime
        if 'created_at' in data and data['created_at']:
            data['created_at'] = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
        if 'updated_at' in data and data['updated_at']:
            data['updated_at'] = datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00'))
        return cls(**data)

@dataclass
class TriggeredAlert:
    """Enregistrement d'une alerte déclenchée"""
    id: Optional[int] = None
    alert_id: int = 0
    indicator_id: str = ""
    indicator_type: str = ""
    actual_value: float = 0.0
    threshold: float = 0.0
    condition: str = ""
    triggered_at: datetime = None
    notified: bool = False
    notification_sent_at: Optional[datetime] = None

    def __post_init__(self):
        if self.triggered_at is None:
            self.triggered_at = datetime.utcnow()

    def to_dict(self) -> dict:
        """Convertit en dictionnaire"""
        data = asdict(self)
        data['triggered_at'] = self.triggered_at.isoformat() if self.triggered_at else None
        data['notification_sent_at'] = self.notification_sent_at.isoformat() if self.notification_sent_at else None
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'TriggeredAlert':
        """Crée depuis un dictionnaire"""
        if 'triggered_at' in data and data['triggered_at']:
            data['triggered_at'] = datetime.fromisoformat(data['triggered_at'].replace('Z', '+00:00'))
        if 'notification_sent_at' in data and data['notification_sent_at']:
            data['notification_sent_at'] = datetime.fromisoformat(data['notification_sent_at'].replace('Z', '+00:00'))
        return cls(**data)