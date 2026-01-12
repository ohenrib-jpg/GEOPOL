# Flask/enhanced_indicators_connector.py - VERSION AMÉLIORÉE
"""
Connecteur unifié et amélioré pour le dashboard économique
Combine: Eurostat (officiel) + INSEE (scraping page d'accueil) + yFinance
Avec cache intelligent et données de secours
"""

import logging
from datetime import datetime
from typing import Dict, Any, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EconomicIndicator:
    """Modèle d'indicateur économique unifié"""
    id: str
    name: str
    value: float
    unit: str
    period: str
    change_percent: float
    source: str
    category: str
    description: str
    last_update: str
    reliability: str  # 'official', 'scraped', 'fallback'
    confidence: str = 'medium'  # 'low', 'medium', 'high'


class EnhancedIndicatorsConnector:
    """
    Connecteur unifié pour tous les indicateurs économiques
    Architecture: 3 sources de données avec fallback automatique
    """
    
    def __init__(self, db_manager=None):
        self.db_manager = db_manager
        
        # Initialiser les connecteurs avec imports flexibles
        try:
            # Essayer import relatif (quand utilisé comme module)
            from .eurostat_connector import EurostatConnector
            from .insee_scraper import INSEEScraper
            from .yfinance_connector import YFinanceConnector
            from .gini_scraper import GINIScraper
        except ImportError:
            # Import absolu (quand exécuté directement)
            from eurostat_connector import EurostatConnector
            from insee_scraper import INSEEScraper
            from yfinance_connector import YFinanceConnector
            from gini_scraper import GINIScraper
        
        self.eurostat = EurostatConnector()
        self.insee = INSEEScraper()
        self.yfinance = YFinanceConnector()
        self.gini = GINIScraper()
        
        logger.info("[OK] EnhancedIndicatorsConnector initialisé (avec GINI)")
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Récupère toutes les données pour le dashboard
        Combine intelligemment les 3 sources
        """
        result = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'sources_status': {},
            'indicators': {},
            'financial_markets': {},
            'summary': {}
        }
        
        # [OK] CORRECTION : Tracker les IDs pour éviter doublons
        added_ids = set()
        
        # 1. Indicateurs Eurostat (données officielles UE pour France)
        try:
            eurostat_data = self._get_eurostat_indicators()
            result['sources_status']['eurostat'] = 'operational'
            
            # Ajouter sans doublons
            for key, indicator in eurostat_data.items():
                if key not in added_ids:
                    result['indicators'][key] = indicator
                    added_ids.add(key)
                    
        except Exception as e:
            logger.error(f"[ERROR] Erreur Eurostat: {e}")
            result['sources_status']['eurostat'] = 'error'
        
        # 2. Indicateurs INSEE (scraping page d'accueil)
        try:
            insee_data = self._get_insee_indicators()
            result['sources_status']['insee'] = 'operational'
            
            # Ajouter sans doublons
            for key, indicator in insee_data.items():
                if key not in added_ids:
                    result['indicators'][key] = indicator
                    added_ids.add(key)
                    
        except Exception as e:
            logger.error(f"[ERROR] Erreur INSEE: {e}")
            result['sources_status']['insee'] = 'error'
        
        # 3. Marchés financiers (yFinance)
        try:
            markets_data = self._get_financial_markets()
            result['sources_status']['yfinance'] = 'operational'
            result['financial_markets'] = markets_data
        except Exception as e:
            logger.error(f"[ERROR] Erreur yFinance: {e}")
            result['sources_status']['yfinance'] = 'error'
        
        # 4. Générer le résumé
        result['summary'] = self._generate_summary(result)
        
        logger.info(f"[DATA] Dashboard: {len(result['indicators'])} indicateurs chargés")
        logger.info(f"   IDs: {list(result['indicators'].keys())}")
        
        return result
    
    def _get_eurostat_indicators(self) -> Dict[str, EconomicIndicator]:
        """
        Récupère les indicateurs Eurostat
        Priorité: données officielles
        """
        indicators = {}
        
        # [OK] Indicateurs par défaut (avec GINI)
        default_ids = ['gdp', 'hicp', 'trade_balance', 'gini']
        
        try:
            raw_data = self.eurostat.get_multiple_indicators(default_ids)
            
            if raw_data.get('success'):
                for indicator_id, data in raw_data['indicators'].items():
                    if data.get('success'):
                        indicators[f'eurostat_{indicator_id}'] = self._create_indicator(
                            id=f'eurostat_{indicator_id}',
                            name=data['indicator_name'],
                            value=data['current_value'],
                            unit=data['unit'],
                            period=data['period'],
                            change_percent=data['change_percent'],
                            source='Eurostat (officiel)',
                            category=data['category'],
                            description=data['description'],
                            reliability='official',
                            confidence='high'
                        )
        
        except Exception as e:
            logger.error(f"Erreur récupération Eurostat: {e}")
        
        # [OK] AJOUTER GINI spécifique si pas déjà inclus
        if 'eurostat_gini' not in indicators:
            try:
                gini_data = self.gini.get_gini_data()
                
                if gini_data.get('success'):
                    indicators['eurostat_gini'] = self._create_indicator(
                        id='eurostat_gini',
                        name=gini_data['name'],
                        value=gini_data['value'],
                        unit=gini_data['unit'],
                        period=gini_data['period'],
                        change_percent=gini_data['change_percent'],
                        source=gini_data['source'],
                        category=gini_data['category'],
                        description=f"{gini_data['description']} - {gini_data.get('interpretation', '')}",
                        reliability=gini_data['reliability'],
                        confidence='high' if gini_data['reliability'] == 'official' else 'medium'
                    )
                    logger.info(f"[OK] GINI ajouté: {gini_data['value']} ({gini_data['reliability']})")
            
            except Exception as e:
                logger.error(f"Erreur récupération GINI: {e}")
        
        return indicators
    
    def _get_insee_indicators(self) -> Dict[str, EconomicIndicator]:
        """
        Récupère les indicateurs INSEE via scraping
        Complément aux données Eurostat
        """
        indicators = {}
        
        try:
            insee_data = self.insee.get_indicators()
            
            if insee_data.get('success'):
                for key, data in insee_data['indicators'].items():
                    # Déterminer la fiabilité
                    reliability = data.get('reliability', 'scraped') if 'reliability' in data else \
                                'scraped' if insee_data['source'] == 'INSEE scraping' else 'fallback'
                    
                    confidence = data.get('confidence', 'medium')
                    
                    indicators[f'insee_{key}'] = self._create_indicator(
                        id=f'insee_{key}',
                        name=data['name'],
                        value=data['value'],
                        unit=data['unit'],
                        period=data['period'],
                        change_percent=data.get('change_percent', 0.0),
                        source=data.get('source', 'INSEE'),
                        category=data.get('category', 'macro'),
                        description=f"Indicateur INSEE: {data['name']}",
                        reliability=reliability,
                        confidence=confidence
                    )
        
        except Exception as e:
            logger.error(f"Erreur récupération INSEE: {e}")
        
        return indicators
    
    def _get_financial_markets(self) -> Dict[str, Any]:
        """
        Récupère les données des marchés financiers
        """
        try:
            markets = self.yfinance.get_all_indices()
            return markets if markets.get('success') else {}
        except Exception as e:
            logger.error(f"Erreur marchés financiers: {e}")
            return {}
    
    def _create_indicator(
        self,
        id: str,
        name: str,
        value: float,
        unit: str,
        period: str,
        change_percent: float,
        source: str,
        category: str,
        description: str,
        reliability: str,
        confidence: str = 'medium'
    ) -> Dict[str, Any]:
        """Crée un indicateur au format unifié"""
        return {
            'id': id,
            'name': name,
            'value': value,
            'unit': unit,
            'period': period,
            'change_percent': change_percent,
            'change_direction': 'up' if change_percent > 0 else 'down' if change_percent < 0 else 'stable',
            'source': source,
            'category': category,
            'description': description,
            'last_update': datetime.now().isoformat(),
            'reliability': reliability,
            'confidence': confidence,
            'reliability_icon': {
                'official': '🔵',  # Officiel
                'scraped': '🟢',   # Scrapé (fiable)
                'fallback': '🟡'   # Données de secours
            }.get(reliability, '⚪')
        }
    
    def _generate_summary(self, data: Dict) -> Dict[str, Any]:
        """Génère un résumé des données"""
        indicators = data.get('indicators', {})
        
        # Compter par source
        by_source = {}
        by_reliability = {}
        by_category = {}
        
        for indicator in indicators.values():
            source = indicator['source']
            reliability = indicator['reliability']
            category = indicator['category']
            
            by_source[source] = by_source.get(source, 0) + 1
            by_reliability[reliability] = by_reliability.get(reliability, 0) + 1
            by_category[category] = by_category.get(category, 0) + 1
        
        return {
            'total_indicators': len(indicators),
            'by_source': by_source,
            'by_reliability': by_reliability,
            'by_category': by_category,
            'data_quality': self._assess_data_quality(by_reliability),
            'last_update': datetime.now().isoformat()
        }
    
    def _assess_data_quality(self, by_reliability: Dict) -> str:
        """Évalue la qualité globale des données"""
        official = by_reliability.get('official', 0)
        scraped = by_reliability.get('scraped', 0)
        fallback = by_reliability.get('fallback', 0)
        total = official + scraped + fallback
        
        if total == 0:
            return 'no_data'
        
        official_percent = (official / total) * 100
        
        if official_percent >= 70:
            return 'excellent'  # 70%+ données officielles
        elif official_percent >= 50:
            return 'good'       # 50-70% données officielles
        elif scraped > fallback:
            return 'acceptable' # Plus de scraping que de fallback
        else:
            return 'limited'    # Beaucoup de fallback
    
    def get_indicator_by_id(self, indicator_id: str) -> Dict[str, Any]:
        """Récupère un indicateur spécifique"""
        all_data = self.get_dashboard_data()
        return all_data['indicators'].get(indicator_id, {
            'success': False,
            'error': 'Indicateur non trouvé'
        })
    
    def get_available_indicators(self) -> Dict[str, Any]:
        """Liste tous les indicateurs disponibles"""
        # Combiner Eurostat + INSEE
        eurostat_indicators = list(self.eurostat.AVAILABLE_INDICATORS.keys())
        insee_indicators = ['inflation', 'unemployment', 'growth']
        
        return {
            'success': True,
            'indicators': {
                'eurostat': eurostat_indicators,
                'insee': insee_indicators,
                'total': len(eurostat_indicators) + len(insee_indicators)
            }
        }
    
    def force_refresh(self) -> Dict[str, Any]:
        """Force le rafraîchissement de toutes les sources"""
        logger.info("[MIGRATION] Rafraîchissement forcé de toutes les sources")
        
        # Forcer rafraîchissement INSEE
        try:
            self.insee.force_refresh()
        except Exception as e:
            logger.error(f"Erreur refresh INSEE: {e}")
        
        # Forcer rafraîchissement GINI
        try:
            self.gini.force_refresh()
        except Exception as e:
            logger.error(f"Erreur refresh GINI: {e}")
        
        # Récupérer les nouvelles données
        return self.get_dashboard_data()


# Fonction helper pour l'intégration dans les routes
def create_enhanced_connector(db_manager=None):
    """Fonction factory pour créer le connecteur"""
    return EnhancedIndicatorsConnector(db_manager)


# Test du module
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    connector = EnhancedIndicatorsConnector()
    data = connector.get_dashboard_data()
    
    print("=" * 70)
    print("[DATA] DASHBOARD ÉCONOMIQUE COMPLET")
    print("=" * 70)
    
    print(f"\n📡 Statut des sources:")
    for source, status in data['sources_status'].items():
        icon = '[OK]' if status == 'operational' else '[ERROR]'
        print(f"  {icon} {source}: {status}")
    
    print(f"\n[CHART] Indicateurs récupérés: {data['summary']['total_indicators']}")
    print(f"[TARGET] Qualité des données: {data['summary']['data_quality']}")
    
    print("\n[DATA] Indicateurs par source:")
    for source, count in data['summary']['by_source'].items():
        print(f"  • {source}: {count}")
    
    print("\n[SEARCH] Fiabilité:")
    for reliability, count in data['summary']['by_reliability'].items():
        print(f"  • {reliability}: {count}")
    
    print("\n🏷 Catégories:")
    for category, count in data['summary']['by_category'].items():
        print(f"  • {category}: {count}")
    
    print("\n[CHART_DOWN] Détail des indicateurs:")
    for ind_id, indicator in data['indicators'].items():
        print(f"\n  {indicator['reliability_icon']} {indicator['name']}")
        print(f"     Valeur: {indicator['value']} {indicator['unit']}")
        print(f"     Variation: {indicator['change_percent']:+.2f}%")
        print(f"     Période: {indicator['period']}")
        print(f"     Source: {indicator['source']}")
        print(f"     Fiabilité: {indicator['reliability']}")
        if 'confidence' in indicator:
            print(f"     Confiance: {indicator['confidence']}")
