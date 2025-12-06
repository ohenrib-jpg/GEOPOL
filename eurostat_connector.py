# Flask/eurostat_connector.py
"""
Connecteur Eurostat pour indicateurs économiques
Sources : https://ec.europa.eu/eurostat/web/main/data/web-services
Utilisation : Éducation et Recherche
"""

import logging
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import time

logger = logging.getLogger(__name__)


class IndicatorCategory(Enum):
    """Catégories d'indicateurs"""
    MACRO = "macro"
    EMPLOYMENT = "employment"
    PRICES = "prices"
    TRADE = "trade"
    FINANCE = "finance"
    PRODUCTION = "production"
    INEQUALITY = "inequality"


@dataclass
class EurostatIndicator:
    """Définition d'un indicateur Eurostat"""
    id: str
    name: str
    category: IndicatorCategory
    dataset: str
    filters: Dict[str, str]
    unit: str
    description: str
    frequency: str
    last_update: Optional[str] = None


class EurostatConnector:
    """Connecteur pour l'API Eurostat"""
    
    BASE_URL = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"
    REQUEST_DELAY = 0.5  # Délai entre les requêtes pour respecter les limites
    
    # === INDICATEURS DISPONIBLES ===
    AVAILABLE_INDICATORS = {
        'gdp': EurostatIndicator(
            id='gdp',
            name='PIB (Produit Intérieur Brut)',
            category=IndicatorCategory.MACRO,
            dataset='namq_10_gdp',
            filters={'geo': 'FR', 'unit': 'CP_MEUR', 'na_item': 'B1GQ', 's_adj': 'SCA'},
            unit='Milliards €',
            description='PIB en prix courants désaisonnalisé',
            frequency='Q'
        ),
        'unemployment': EurostatIndicator(
            id='unemployment',
            name='Taux de chômage',
            category=IndicatorCategory.EMPLOYMENT,
            dataset='une_rt_m',
            filters={'geo': 'FR', 's_adj': 'SA', 'age': 'TOTAL', 'sex': 'T'},
            unit='%',
            description='Taux de chômage désaisonnalisé',
            frequency='M'
        ),
        'hicp': EurostatIndicator(
            id='hicp',
            name='Inflation (IPCH)',
            category=IndicatorCategory.PRICES,
            dataset='prc_hicp_manr',
            filters={'geo': 'FR', 'coicop': 'CP00', 'unit': 'RCH_A'},
            unit='%',
            description='Variation annuelle des prix à la consommation',
            frequency='M'
        ),
        'trade_balance': EurostatIndicator(
            id='trade_balance',
            name='Balance commerciale',
            category=IndicatorCategory.TRADE,
            dataset='ext_lt_intratrd',
            filters={'geo': 'FR', 'partner': 'EXT_EU27_2020', 'sitc06': 'TOTAL', 'stk_flow': 'BAL'},
            unit='Millions €',
            description='Solde commercial (exports - imports)',
            frequency='M'
        ),
        'gini': EurostatIndicator(
            id='gini',
            name='Indice GINI (inégalités)',
            category=IndicatorCategory.INEQUALITY,
            dataset='ilc_di12',
            filters={'geo': 'FR', 'indic_il': 'GINI', 'unit': 'PC'},
            unit='Points (0-100)',
            description='Coefficient de Gini pour la distribution des revenus',
            frequency='A'
        )
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GEO-Educational-Research/1.0',
            'Accept': 'application/json'
        })
        logger.info("✅ Connecteur Eurostat initialisé")
    
    def get_indicator_data(self, indicator_id: str, last_n: int = 12) -> Dict[str, Any]:
        """Récupère les données d'un indicateur"""
        if indicator_id not in self.AVAILABLE_INDICATORS:
            return {'success': False, 'error': f'Indicateur {indicator_id} inconnu'}
        
        indicator = self.AVAILABLE_INDICATORS[indicator_id]
        
        try:
            url = f"{self.BASE_URL}/{indicator.dataset}"
            params = {
                'format': 'JSON',
                'lang': 'FR',
                **indicator.filters,
                'lastTimePeriod': last_n
            }
            
            logger.info(f"📊 Requête: {indicator.name}")
            
            # Respecter les limites de requêtes
            time.sleep(self.REQUEST_DELAY)
            
            response = self.session.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                parsed = self._parse_response(data, indicator)
                
                if parsed['success']:
                    logger.info(f"✅ {indicator.name}: {parsed['current_value']} {indicator.unit}")
                    return parsed
            
            logger.warning(f"⚠️ Fallback pour {indicator.name}")
            return self._get_fallback(indicator)
                
        except Exception as e:
            logger.error(f"❌ Erreur {indicator_id}: {e}")
            return self._get_fallback(indicator)
    
    def _parse_response(self, data: Dict, indicator: EurostatIndicator) -> Dict[str, Any]:
        """Parse la réponse Eurostat avec validation des valeurs"""
        try:
            if 'value' not in data or not data['value']:
                return {'success': False}
            
            values = data['value']
            dimensions = data.get('dimension', {})
            time_dim = dimensions.get('time', {}).get('category', {}).get('index', {})
            
            if not values or not time_dim:
                return {'success': False}
            
            sorted_times = sorted(time_dim.keys(), key=lambda x: time_dim[x])
            
            if not sorted_times:
                return {'success': False}
            
            # Dernière valeur
            latest_time = sorted_times[-1]
            latest_value_str = values.get(str(time_dim[latest_time]), 0)
            
            # Convertir en float avec validation
            try:
                latest_value = float(latest_value_str)
            except (ValueError, TypeError):
                logger.warning(f"⚠️ Valeur invalide pour {indicator.id}: {latest_value_str}")
                return {'success': False}
            
            # Validation des plages raisonnables
            if not self._is_value_reasonable(latest_value, indicator.id):
                logger.warning(f"⚠️ Valeur aberrante pour {indicator.id}: {latest_value}")
                return {'success': False}
            
            # Valeur précédente
            previous_value = latest_value
            if len(sorted_times) > 1:
                previous_time = sorted_times[-2]
                previous_value_str = values.get(str(time_dim[previous_time]), latest_value)
                try:
                    previous_value = float(previous_value_str)
                except (ValueError, TypeError):
                    previous_value = latest_value
            
            # Variation
            change = latest_value - previous_value
            change_percent = (change / previous_value * 100) if previous_value != 0 and abs(previous_value) > 0.001 else 0
            
            # Validation de la variation
            if abs(change_percent) > 1000:  # Variation > 1000% = aberrante
                logger.warning(f"⚠️ Variation aberrante pour {indicator.id}: {change_percent}%")
                change_percent = 0
                change = 0
            
            # Historique
            historical = []
            for time_key in sorted_times[-12:]:
                val_index = str(time_dim[time_key])
                if val_index in values:
                    try:
                        hist_value = float(values[val_index])
                        if self._is_value_reasonable(hist_value, indicator.id):
                            historical.append({
                                'period': time_key,
                                'value': round(hist_value, 2)
                            })
                    except (ValueError, TypeError):
                        continue
            
            return {
                'success': True,
                'indicator_id': indicator.id,
                'indicator_name': indicator.name,
                'current_value': round(latest_value, 2),
                'previous_value': round(previous_value, 2),
                'change': round(change, 2),
                'change_percent': round(change_percent, 2),
                'unit': indicator.unit,
                'period': latest_time,
                'source': 'Eurostat',
                'dataset': indicator.dataset,
                'description': indicator.description,
                'frequency': indicator.frequency,
                'category': indicator.category.value,
                'last_update': datetime.now().isoformat(),
                'historical': historical
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur parsing: {e}")
            return {'success': False}
    
    def _is_value_reasonable(self, value: float, indicator_id: str) -> bool:
        """Vérifie si une valeur est raisonnable pour un indicateur donné"""
        ranges = {
            'gdp': (-1000000, 1000000),      # PIB en milliards
            'unemployment': (0, 30),          # Taux de chômage en %
            'hicp': (-20, 50),               # Inflation en %
            'trade_balance': (-1000000, 1000000),  # Balance en millions
            'gini': (0, 100),                # Indice GINI
            'default': (-1000000, 1000000)   # Plage par défaut
        }
        
        min_val, max_val = ranges.get(indicator_id, ranges['default'])
        return min_val <= value <= max_val
    
    def _get_fallback(self, indicator: EurostatIndicator) -> Dict[str, Any]:
        """Données de référence avec valeurs réalistes"""
        fallbacks = {
            'gdp': {'value': 695.2, 'period': '2024-Q3'},
            'unemployment': {'value': 7.1, 'period': '2024-10'},
            'hicp': {'value': 2.2, 'period': '2024-10'},
            'trade_balance': {'value': -4.8, 'period': '2024-09'},
            'gini': {'value': 29.4, 'period': '2023'}
        }
        
        fb = fallbacks.get(indicator.id, {'value': 0, 'period': '2024'})
        
        return {
            'success': True,
            'indicator_id': indicator.id,
            'indicator_name': indicator.name,
            'current_value': fb['value'],
            'previous_value': fb['value'],
            'change': 0,
            'change_percent': 0,
            'unit': indicator.unit,
            'period': fb['period'],
            'source': 'Données de référence',
            'dataset': indicator.dataset,
            'description': indicator.description,
            'frequency': indicator.frequency,
            'category': indicator.category.value,
            'last_update': datetime.now().isoformat(),
            'note': 'Données de référence - API temporairement indisponible',
            'historical': []
        }
    
    def get_multiple_indicators(self, indicator_ids: List[str]) -> Dict[str, Any]:
        """Récupère plusieurs indicateurs"""
        results = {}
        
        for indicator_id in indicator_ids:
            if indicator_id in self.AVAILABLE_INDICATORS:
                results[indicator_id] = self.get_indicator_data(indicator_id)
        
        successful = sum(1 for r in results.values() if r.get('success'))
        
        return {
            'success': True,
            'indicators': results,
            'stats': {
                'total': len(indicator_ids),
                'successful': successful,
                'failed': len(indicator_ids) - successful
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def get_available_indicators(self) -> Dict[str, Any]:
        """Liste des indicateurs disponibles"""
        indicators_list = []
        
        for indicator_id, indicator in self.AVAILABLE_INDICATORS.items():
            indicators_list.append({
                'id': indicator_id,
                'name': indicator.name,
                'category': indicator.category.value,
                'unit': indicator.unit,
                'description': indicator.description,
                'frequency': indicator.frequency,
                'dataset': indicator.dataset
            })
        
        # Grouper par catégorie
        by_category = {}
        for ind in indicators_list:
            category = ind['category']
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(ind)
        
        return {
            'success': True,
            'total_indicators': len(indicators_list),
            'indicators': indicators_list,
            'by_category': by_category,
            'default_indicators': ['gdp', 'unemployment', 'hicp', 'trade_balance']
        }
