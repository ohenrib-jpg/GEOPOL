# Flask/geopol_data/models.py
"""
Modèles de données pour le module Geopol-Data
Classes représentant les snapshots de pays avec leurs indicateurs
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# CLASSE PRINCIPALE : COUNTRY SNAPSHOT
# ============================================================================

@dataclass
class CountrySnapshot:
    """
    Snapshot (instantané) des données d'un pays à un moment donné
    Contient tous les indicateurs économiques, démographiques et environnementaux
    """
    
    # Identification
    country_code: str              # Code ISO Alpha-2 (ex: 'FR', 'US')
    country_name: str              # Nom complet (ex: 'France')
    
    # Économie
    gdp: Optional[float] = None                    # PIB en USD courants
    gdp_per_capita: Optional[float] = None         # PIB par habitant
    gdp_growth: Optional[float] = None             # Croissance PIB (%)
    inflation: Optional[float] = None              # Inflation (%)
    debt: Optional[float] = None                   # Dette publique (% PIB)
    
    # Démographie
    population: Optional[float] = None             # Population totale
    urban_population: Optional[float] = None       # Urbanisation (%)
    fertility: Optional[float] = None              # Taux de fertilité
    life_expectancy: Optional[float] = None        # Espérance de vie (années)
    
    # Travail
    unemployment: Optional[float] = None           # Chômage (%)
    labor_force: Optional[float] = None            # Force de travail
    
    # Militaire & Sécurité
    military_spending_pct: Optional[float] = None  # Dépenses militaires (% PIB)
    military_spending_usd: Optional[float] = None  # Dépenses militaires (USD)
    
    # Environnement
    pm25: Optional[float] = None                   # PM2.5 moyen (µg/m³)
    co2_per_capita: Optional[float] = None         # Émissions CO2 (tonnes/hab)
    forest_area: Optional[float] = None            # Forêts (% territoire)
    renewable_energy: Optional[float] = None       # Énergies renouvelables (%)
    
    # Énergie
    energy_imports: Optional[float] = None         # Imports énergétiques (% conso)
    electricity_access: Optional[float] = None     # Accès électricité (%)
    
    # Métadonnées
    last_updated: datetime = field(default_factory=datetime.utcnow)
    data_year: Optional[int] = None                # Année des données
    source: str = 'world_bank'
    
    # Données brutes (pour debug)
    raw_data: Dict[str, Any] = field(default_factory=dict)
    
    # Indicateurs calculés (Phase 3)
    calculated_indices: Dict[str, Any] = field(default_factory=dict)
    
    def __repr__(self):
        """Représentation lisible du snapshot"""
        return (
            f"CountrySnapshot('{self.country_name}' [{self.country_code}] - "
            f"PIB: {self.format_gdp()} - "
            f"Pop: {self.format_population()} - "
            f"Mil: {self.military_spending_pct or 'N/A'}% PIB)"
        )
    
    # ========================================================================
    # MÉTHODES DE FORMATAGE
    # ========================================================================
    
    def format_gdp(self) -> str:
        """Formate le PIB en notation courte (ex: 2.78T$)"""
        if self.gdp is None:
            return 'N/A'
        
        if self.gdp >= 1e12:  # Trillions
            return f"{self.gdp/1e12:.2f}T$"
        elif self.gdp >= 1e9:  # Billions
            return f"{self.gdp/1e9:.2f}B$"
        elif self.gdp >= 1e6:  # Millions
            return f"{self.gdp/1e6:.2f}M$"
        else:
            return f"{self.gdp:.2f}$"
    
    def format_population(self) -> str:
        """Formate la population (ex: 67.8M)"""
        if self.population is None:
            return 'N/A'
        
        if self.population >= 1e9:
            return f"{self.population/1e9:.2f}B"
        elif self.population >= 1e6:
            return f"{self.population/1e6:.1f}M"
        elif self.population >= 1e3:
            return f"{self.population/1e3:.1f}K"
        else:
            return f"{int(self.population)}"
    
    def format_military_spending(self) -> str:
        """Formate les dépenses militaires"""
        if self.military_spending_usd is None:
            return 'N/A'
        
        if self.military_spending_usd >= 1e9:
            return f"{self.military_spending_usd/1e9:.1f}B$"
        elif self.military_spending_usd >= 1e6:
            return f"{self.military_spending_usd/1e6:.1f}M$"
        else:
            return f"{self.military_spending_usd:.0f}$"
    
    # ========================================================================
    # MÉTHODES D'ANALYSE
    # ========================================================================
    
    def is_complete(self, min_indicators: int = 3) -> bool:
        """Vérifie si le snapshot a suffisamment de données"""
        filled_fields = sum([
            self.gdp is not None,
            self.population is not None,
            self.gdp_per_capita is not None,
            self.military_spending_pct is not None,
            self.unemployment is not None,
            self.pm25 is not None,
        ])
        return filled_fields >= min_indicators
    
    def get_economic_health_score(self) -> Optional[float]:
        """
        Calcule un score de santé économique (0-100)
        Basé sur: croissance PIB, chômage, inflation, dette
        """
        if not all([self.gdp_growth, self.unemployment, self.inflation, self.debt]):
            return None
        
        # Normaliser chaque facteur (0 = mauvais, 1 = bon)
        growth_score = min(1, max(0, (self.gdp_growth + 5) / 10))  # -5% à +5%
        unemployment_score = max(0, 1 - (self.unemployment / 20))   # 0% à 20%
        inflation_score = max(0, 1 - abs(self.inflation - 2) / 5)  # Cible 2%
        debt_score = max(0, 1 - (self.debt / 100))                 # 0% à 100%
        
        # Moyenne pondérée
        score = (
            growth_score * 0.3 +
            unemployment_score * 0.3 +
            inflation_score * 0.2 +
            debt_score * 0.2
        ) * 100
        
        return round(score, 1)
    
    def get_military_intensity(self) -> str:
        """
        Retourne l'intensité militaire (LOW, MEDIUM, HIGH, VERY_HIGH)
        Basé sur le % du PIB consacré à la défense
        """
        if self.military_spending_pct is None:
            return 'UNKNOWN'
        
        if self.military_spending_pct < 1.5:
            return 'LOW'
        elif self.military_spending_pct < 2.5:
            return 'MEDIUM'
        elif self.military_spending_pct < 4.0:
            return 'HIGH'
        else:
            return 'VERY_HIGH'
    
    def get_environmental_risk(self) -> str:
        """
        Retourne le risque environnemental (LOW, MEDIUM, HIGH, CRITICAL)
        Basé sur PM2.5 et émissions CO2
        """
        if self.pm25 is None:
            return 'UNKNOWN'
        
        # Seuils OMS: 10 µg/m³ = recommandé, 25+ = dangereux, 50+ = très dangereux
        if self.pm25 < 15:
            return 'LOW'
        elif self.pm25 < 35:
            return 'MEDIUM'
        elif self.pm25 < 55:
            return 'HIGH'
        else:
            return 'CRITICAL'
    
    # ========================================================================
    # MÉTHODE FACTORY : Création depuis World Bank
    # ========================================================================
    
    @classmethod
    def from_world_bank(cls, country_code: str, country_name: str, 
                       wb_data: List[Dict[str, Any]]) -> 'CountrySnapshot':
        """
        Crée un CountrySnapshot depuis les données brutes de World Bank API
        
        Args:
            country_code: Code ISO du pays (ex: 'FR')
            country_name: Nom du pays (ex: 'France')
            wb_data: Liste de réponses World Bank (format API v2)
        
        Returns:
            CountrySnapshot avec données parsées
        
        Exemple de wb_data (réponse World Bank):
        [
            {
                'indicator': {'id': 'NY.GDP.MKTP.CD', 'value': 'PIB'},
                'country': {'id': 'FR', 'value': 'France'},
                'value': 2780000000000,
                'date': '2022'
            },
            ...
        ]
        """
        # Initialiser le snapshot
        snapshot = cls(
            country_code=country_code,
            country_name=country_name,
            source='world_bank',
            last_updated=datetime.utcnow()
        )
        
        # Parser les indicateurs
        indicator_map = {
            'NY.GDP.MKTP.CD': 'gdp',
            'NY.GDP.PCAP.CD': 'gdp_per_capita',
            'NY.GDP.MKTP.KD.ZG': 'gdp_growth',
            'FP.CPI.TOTL.ZG': 'inflation',
            'GC.DOD.TOTL.GD.ZS': 'debt',
            'SP.POP.TOTL': 'population',
            'SP.URB.TOTL.IN.ZS': 'urban_population',
            'SP.DYN.TFRT.IN': 'fertility',
            'SP.DYN.LE00.IN': 'life_expectancy',
            'SL.UEM.TOTL.ZS': 'unemployment',
            'SL.TLF.TOTL.IN': 'labor_force',
            'MS.MIL.XPND.GD.ZS': 'military_spending_pct',
            'MS.MIL.XPND.CD': 'military_spending_usd',
            'EN.ATM.PM25.MC.M3': 'pm25',
            'EN.ATM.CO2E.PC': 'co2_per_capita',
            'AG.LND.FRST.ZS': 'forest_area',
            'EG.FEC.RNEW.ZS': 'renewable_energy',
            'EG.IMP.CONS.ZS': 'energy_imports',
            'EG.ELC.ACCS.ZS': 'electricity_access',
        }
        
        # Stocker l'année la plus récente
        latest_year = None
        
        for item in wb_data:
            try:
                # Extraire l'indicateur
                indicator_code = item.get('indicator', {}).get('id')
                value = item.get('value')
                year = item.get('date')
                
                # Vérifier que les données sont valides
                if not indicator_code or value is None:
                    continue
                
                # Mapper vers l'attribut du snapshot
                attr_name = indicator_map.get(indicator_code)
                if attr_name:
                    setattr(snapshot, attr_name, float(value))
                    
                    # Mettre à jour l'année
                    if year and (latest_year is None or int(year) > latest_year):
                        latest_year = int(year)
                
            except (ValueError, KeyError, TypeError) as e:
                logger.warning(f"Erreur parsing indicateur {indicator_code}: {e}")
                continue
        
        snapshot.data_year = latest_year
        snapshot.raw_data = wb_data
        
        return snapshot
    
    # ========================================================================
    # SÉRIALISATION
    # ========================================================================
    
    def to_dict(self, include_raw: bool = False) -> Dict[str, Any]:
        """
        Convertit le snapshot en dictionnaire (pour JSON)
        
        Args:
            include_raw: Inclure les données brutes World Bank
        
        Returns:
            Dictionnaire sérialisable
        """
        data = asdict(self)
        
        # Convertir datetime en string ISO
        data['last_updated'] = self.last_updated.isoformat()
        
        # Supprimer raw_data si non demandé
        if not include_raw:
            data.pop('raw_data', None)
        
        # Ajouter des champs formatés
        data['formatted'] = {
            'gdp': self.format_gdp(),
            'population': self.format_population(),
            'military_spending': self.format_military_spending(),
        }
        
        # Ajouter les scores calculés
        data['scores'] = {
            'economic_health': self.get_economic_health_score(),
            'military_intensity': self.get_military_intensity(),
            'environmental_risk': self.get_environmental_risk(),
        }
        
        return data
    
    def to_summary(self) -> str:
        """Retourne un résumé textuel du snapshot (pour CLI)"""
        lines = [
            f"\n{'='*70}",
            f"📊 {self.country_name} ({self.country_code})",
            f"{'='*70}",
            f"\n💰 ÉCONOMIE",
            f"  PIB:              {self.format_gdp()}",
            f"  PIB/habitant:     ${self.gdp_per_capita:,.0f}" if self.gdp_per_capita else "  PIB/habitant:     N/A",
            f"  Croissance:       {self.gdp_growth:+.1f}%" if self.gdp_growth else "  Croissance:       N/A",
            f"  Chômage:          {self.unemployment:.1f}%" if self.unemployment else "  Chômage:          N/A",
            f"\n👥 DÉMOGRAPHIE",
            f"  Population:       {self.format_population()}",
            f"  Urbanisation:     {self.urban_population:.1f}%" if self.urban_population else "  Urbanisation:     N/A",
            f"  Espérance de vie: {self.life_expectancy:.1f} ans" if self.life_expectancy else "  Espérance de vie: N/A",
            f"\n🎖️  MILITAIRE",
            f"  Dépenses:         {self.military_spending_pct:.2f}% du PIB" if self.military_spending_pct else "  Dépenses:         N/A",
            f"  Montant:          {self.format_military_spending()}",
            f"  Intensité:        {self.get_military_intensity()}",
            f"\n🌍 ENVIRONNEMENT",
            f"  PM2.5:            {self.pm25:.1f} µg/m³" if self.pm25 else "  PM2.5:            N/A",
            f"  Risque:           {self.get_environmental_risk()}",
            f"  CO2/hab:          {self.co2_per_capita:.1f} tonnes" if self.co2_per_capita else "  CO2/hab:          N/A",
            f"\n📅 MÉTADONNÉES",
            f"  Année des données: {self.data_year or 'N/A'}",
            f"  Dernière MAJ:      {self.last_updated.strftime('%Y-%m-%d %H:%M:%S')}",
            f"  Source:            {self.source}",
            f"{'='*70}\n"
        ]
        
        return '\n'.join(lines)

# ============================================================================
# CLASSES AUXILIAIRES (Phase 3)
# ============================================================================

@dataclass
class GeopoliticalIndex:
    """
    Indice géopolitique calculé (ex: pression environnementale, instabilité)
    """
    name: str
    value: float
    level: str  # LOW, MEDIUM, HIGH, CRITICAL
    color: str  # Code couleur hex (pour visualisation)
    description: str
    factors: Dict[str, float]  # Facteurs ayant contribué au calcul
    calculated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'value': round(self.value, 2),
            'level': self.level,
            'color': self.color,
            'description': self.description,
            'factors': self.factors,
            'calculated_at': self.calculated_at.isoformat()
        }