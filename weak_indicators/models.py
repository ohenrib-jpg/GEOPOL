# Flask/weak_indicators/models.py
"""Modèles de données pour les indicateurs faibles"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime

@dataclass
class TravelAdvisory:
    """Avis de voyage"""
    country_code: str
    country_name: str
    risk_level: int  # 1-4
    source: str
    summary: str
    last_updated: datetime
    raw_data: Optional[dict] = None

@dataclass
class FinancialInstrument:
    """Instrument financier"""
    symbol: str
    name: str
    current_price: float
    change_percent: float
    volume: Optional[int]
    timestamp: datetime
    source: str
    category: str  # index, commodity, crypto

@dataclass
class SDRActivity:
    """Activité SDR"""
    frequency_khz: int
    name: str
    activity_count: int
    last_seen: datetime
    is_anomaly: bool
    source: str


# nouveau modele pour les alertes
@dataclass
class Alert:
    """Modèle pour compatibilité"""
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

@dataclass
class DashboardData:
    """Données du dashboard consolidé"""
    travel_advisories: List[TravelAdvisory]
    financial_data: List[FinancialInstrument]
    sdr_activities: List[SDRActivity]
    alerts: List[Alert]
    timestamp: datetime
