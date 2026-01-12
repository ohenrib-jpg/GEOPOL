"""
Modeles de donnees pour les indicateurs economiques
"""
from dataclasses import dataclass, asdict
from typing import Optional
from datetime import datetime

@dataclass
class EconomicIndicator:
    """Modele pour un indicateur economique"""
    name: str
    value: float
    change_percent: Optional[float] = None
    currency: str = '%'
    source: str = 'unknown'
    fresh: bool = True
    last_updated: Optional[str] = None
    cached_at: Optional[str] = None
    unit: Optional[str] = None
    period: Optional[str] = None
    confidence: float = 0.95

    def to_dict(self) -> dict:
        """Convertit en dictionnaire"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'EconomicIndicator':
        """Cree depuis un dictionnaire"""
        return cls(**data)

@dataclass
class MarketIndex:
    """Modele pour un indice boursier"""
    symbol: str
    name: str
    current_price: float
    change_percent: float
    currency: str
    region: str
    volume: Optional[int] = None
    market_cap: Optional[float] = None
    fresh: bool = True
    last_updated: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

@dataclass
class Commodity:
    """Modele pour une commodite"""
    symbol: str
    name: str
    price: float
    change_percent: float
    unit: str
    fresh: bool = True
    last_updated: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)

@dataclass
class Cryptocurrency:
    """Modele pour une cryptomonnaie"""
    symbol: str
    name: str
    price: float
    change_percent: float
    market_cap: Optional[float] = None
    volume_24h: Optional[float] = None
    fresh: bool = True
    last_updated: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)
