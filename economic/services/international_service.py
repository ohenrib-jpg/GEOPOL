"""
Service pour les indicateurs economiques internationaux
Sources: yFinance, FRED
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from .base_service import BaseEconomicService
from ..config import EconomicConfig

logger = logging.getLogger(__name__)


class InternationalService(BaseEconomicService):
    """Service pour les indicateurs economiques internationaux"""

    # Noms des categories pour l'affichage
    CATEGORY_NAMES = {
        'macro': 'Stabilite Macro-Financiere',
        'forex': 'Systemes Monetaires',
        'debt': 'Dette Souveraine',
        'commodities': 'Matieres Premieres',
        'indices': 'Indices Boursiers',
        'safe_haven': 'Valeurs Refuges',
        'synthetic': 'Indicateurs Synthetiques'
    }

    def __init__(self, db_manager):
        super().__init__(db_manager)

        # Import conditionnel des connecteurs
        try:
            from Flask.yfinance_connector import YFinanceConnector
            self.yfinance = YFinanceConnector()
        except ImportError:
            try:
                from yfinance_connector import YFinanceConnector
                self.yfinance = YFinanceConnector()
            except ImportError:
                logger.warning("[INTERNATIONAL] yFinance connector non disponible")
                self.yfinance = None

        # Connecteur FRED (Federal Reserve Economic Data)
        try:
            from Flask.fluxStrategiques.indicators.fred_connector import FREDConnector
            self.fred = FREDConnector()
            logger.info("[INTERNATIONAL] FRED connector initialise")
        except ImportError:
            try:
                from fluxStrategiques.indicators.fred_connector import FREDConnector
                self.fred = FREDConnector()
                logger.info("[INTERNATIONAL] FRED connector initialise")
            except ImportError:
                logger.warning("[INTERNATIONAL] FRED connector non disponible")
                self.fred = None

        # Charger la configuration des indicateurs
        self.indicators_config = EconomicConfig.INTERNATIONAL_INDICATORS
        self.categories = EconomicConfig.INTERNATIONAL_CATEGORIES
        self.default_widgets = EconomicConfig.DEFAULT_INTERNATIONAL_WIDGETS
        self.alert_indicators = EconomicConfig.INTERNATIONAL_ALERT_INDICATORS

        logger.info(f"[INTERNATIONAL] Service initialise avec {self._count_indicators()} indicateurs")

    def _count_indicators(self) -> int:
        """Compte le nombre total d'indicateurs"""
        return sum(len(indicators) for indicators in self.indicators_config.values())

    def _build_flat_indicators_list(self) -> List[Dict[str, Any]]:
        """Construit une liste plate de tous les indicateurs"""
        flat_list = []
        for category, indicators in self.indicators_config.items():
            for ind in indicators:
                flat_list.append({
                    **ind,
                    'category_name': self.CATEGORY_NAMES.get(category, category)
                })
        return flat_list

    def get_available_indicators(self) -> List[Dict[str, Any]]:
        """Retourne la liste des indicateurs internationaux disponibles pour configuration"""
        return self._build_flat_indicators_list()

    def get_indicators_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Retourne les indicateurs d'une categorie specifique"""
        if category not in self.indicators_config:
            return []
        return self.indicators_config[category]

    def get_categories(self) -> List[Dict[str, str]]:
        """Retourne la liste des categories avec leurs noms"""
        return [
            {'id': cat, 'name': self.CATEGORY_NAMES.get(cat, cat)}
            for cat in self.categories
        ]

    def get_indicator_by_id(self, indicator_id: str, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """
        Recupere un indicateur par son ID

        Args:
            indicator_id: ID de l'indicateur (ex: 'vix', 'dxy', etc.)
            force_refresh: Forcer le rafraichissement

        Returns:
            Donnees de l'indicateur ou None
        """
        # Trouver la config de l'indicateur
        indicator_config = None
        for indicators in self.indicators_config.values():
            for ind in indicators:
                if ind['id'] == indicator_id:
                    indicator_config = ind
                    break
            if indicator_config:
                break

        if not indicator_config:
            logger.warning(f"[INTERNATIONAL] Indicateur {indicator_id} non trouve")
            return None

        # Router vers la bonne source
        source = indicator_config.get('source', 'yfinance')

        if source == 'yfinance':
            return self._get_yfinance_indicator(indicator_config, force_refresh)
        elif source == 'fred':
            return self._get_fred_indicator(indicator_config, force_refresh)
        else:
            logger.warning(f"[INTERNATIONAL] Source {source} non supportee")
            return None

    def _get_yfinance_indicator(self, config: Dict, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """Recupere un indicateur depuis yFinance"""
        if not self.yfinance:
            return self._get_demo_data(config)

        cache_key = f"intl_{config['id']}"
        symbol = config.get('symbol', '')

        def fetch():
            try:
                import yfinance as yf
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="5d")

                if len(hist) >= 2:
                    current_price = float(hist['Close'].iloc[-1])
                    previous_price = float(hist['Close'].iloc[-2])
                    change_percent = ((current_price - previous_price) / previous_price) * 100

                    return {
                        'id': config['id'],
                        'name': config['name'],
                        'value': round(current_price, 2),
                        'change_percent': round(change_percent, 2),
                        'unit': config.get('unit', ''),
                        'category': config.get('category', ''),
                        'source': 'yfinance',
                        'symbol': symbol,
                        'timestamp': datetime.now().isoformat()
                    }
            except Exception as e:
                logger.error(f"[INTERNATIONAL] Erreur yFinance {symbol}: {e}")
            return None

        result = self.fetch_with_cache(
            cache_key=cache_key,
            fetch_func=fetch,
            data_source='yfinance',
            data_type='international',
            expiry_hours=2,
            force_refresh=force_refresh
        )

        if result is None:
            return self._get_demo_data(config)

        return result

    def _get_fred_indicator(self, config: Dict, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """Recupere un indicateur depuis FRED"""
        if not self.fred:
            return self._get_demo_data(config)

        cache_key = f"intl_fred_{config['id']}"
        series = config.get('series', '')

        def fetch():
            try:
                result = self.fred.get_series(series, limit=2)
                if result and result.get('latest_value') is not None:
                    observations = result.get('observations', [])
                    change_percent = 0
                    if len(observations) >= 2 and observations[0]['value'] and observations[1]['value']:
                        prev_val = observations[1]['value']
                        curr_val = observations[0]['value']
                        if prev_val != 0:
                            change_percent = ((curr_val - prev_val) / abs(prev_val)) * 100

                    return {
                        'id': config['id'],
                        'name': config['name'],
                        'value': round(result['latest_value'], 2),
                        'change_percent': round(change_percent, 2),
                        'unit': config.get('unit', ''),
                        'category': config.get('category', ''),
                        'source': 'fred',
                        'series': series,
                        'period': result.get('latest_date', ''),
                        'timestamp': datetime.now().isoformat()
                    }
            except Exception as e:
                logger.error(f"[INTERNATIONAL] Erreur FRED {series}: {e}")
            return None

        result = self.fetch_with_cache(
            cache_key=cache_key,
            fetch_func=fetch,
            data_source='fred',
            data_type='international',
            expiry_hours=6,
            force_refresh=force_refresh
        )

        if result is None:
            return self._get_demo_data(config)

        return result

    def _get_demo_data(self, config: Dict) -> Dict[str, Any]:
        """Retourne des donnees de demonstration pour un indicateur"""
        # Valeurs de demo par indicateur
        demo_values = {
            'vix': 15.5,
            'dxy': 104.2,
            'eur_usd': 1.085,
            'usd_jpy': 149.5,
            'usd_cny': 7.25,
            'gbp_usd': 1.265,
            'usd_chf': 0.885,
            'usd_rub': 92.5,
            'usd_try': 34.2,
            'usd_brl': 5.15,
            'usd_zar': 18.5,
            'us_10y': 4.35,
            'us_2y': 4.65,
            'fed_rate': 5.25,
            'us_yield_curve': -0.30,
            'us_inflation': 3.2,
            'us_unemployment': 3.7,
            'brent': 78.5,
            'wti': 74.2,
            'gas_us': 2.85,
            'gold': 2045.0,
            'silver': 23.5,
            'copper': 3.85,
            'wheat': 580.0,
            'corn': 455.0,
            'sp500': 5950.0,
            'nasdaq': 19200.0,
            'dow_jones': 42500.0,
            'nikkei': 38500.0,
            'eurostoxx': 4850.0,
            'ftse': 8250.0,
            'dax': 19500.0,
            'bitcoin': 95000.0,
        }

        return {
            'id': config['id'],
            'name': config['name'],
            'value': demo_values.get(config['id'], 100.0),
            'change_percent': round((hash(config['id']) % 10 - 5) / 10, 2),
            'unit': config.get('unit', ''),
            'category': config.get('category', ''),
            'source': 'demo',
            'timestamp': datetime.now().isoformat()
        }

    def get_selected_indicators(self, indicator_ids: List[str], force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Recupere plusieurs indicateurs par leurs IDs (pour les widgets)

        Args:
            indicator_ids: Liste des IDs d'indicateurs
            force_refresh: Forcer le rafraichissement

        Returns:
            Liste des indicateurs avec leurs donnees
        """
        results = []
        for indicator_id in indicator_ids[:8]:  # Max 8 widgets
            data = self.get_indicator_by_id(indicator_id, force_refresh)
            if data:
                results.append(data)
        return results

    def get_dashboard_summary(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Recupere un resume pour le bandeau d'alerte rapide

        Returns:
            Dict avec les indicateurs cles (VIX, DXY, Brent, US 10Y, Or)
        """
        summary = {
            'indicators': [],
            'timestamp': datetime.now().isoformat()
        }

        for indicator_id in self.alert_indicators:
            data = self.get_indicator_by_id(indicator_id, force_refresh)
            if data:
                summary['indicators'].append({
                    'id': data['id'],
                    'name': data['name'],
                    'value': data['value'],
                    'change_percent': data.get('change_percent', 0),
                    'unit': data.get('unit', '')
                })

        return summary

    def get_historical_data(self, indicator_id: str, period: str = '1m') -> Dict[str, Any]:
        """
        Recupere les donnees historiques d'un indicateur pour le graphique

        Args:
            indicator_id: ID de l'indicateur
            period: Periode ('1d', '7d', '1m', '3m', '6m', '1y')

        Returns:
            Donnees historiques avec timestamps et valeurs
        """
        # Trouver la config de l'indicateur
        indicator_config = None
        for indicators in self.indicators_config.values():
            for ind in indicators:
                if ind['id'] == indicator_id:
                    indicator_config = ind
                    break
            if indicator_config:
                break

        if not indicator_config:
            return {'success': False, 'error': f'Indicateur {indicator_id} non trouve'}

        source = indicator_config.get('source', 'yfinance')

        if source == 'yfinance':
            return self._get_yfinance_historical(indicator_config, period)
        elif source == 'fred':
            return self._get_fred_historical(indicator_config, period)
        else:
            return {'success': False, 'error': f'Source {source} non supportee'}

    def _get_yfinance_historical(self, config: Dict, period: str) -> Dict[str, Any]:
        """Recupere les donnees historiques depuis yFinance"""
        if not self.yfinance:
            return {'success': False, 'error': 'yFinance non disponible'}

        symbol = config.get('symbol', '')

        # Mapping des periodes
        period_mapping = {
            '1d': '1d',
            '7d': '5d',
            '1m': '1mo',
            '3m': '3mo',
            '6m': '6mo',
            '1y': '1y'
        }

        yf_period = period_mapping.get(period, '1mo')

        try:
            result = self.yfinance.get_historical_data(symbol, period=yf_period, timeout=15)

            if result.get('success'):
                data = result.get('data', [])

                return {
                    'success': True,
                    'id': config['id'],
                    'name': config['name'],
                    'symbol': symbol,
                    'period': period,
                    'data': data,
                    'last_value': data[-1]['close'] if data else None,
                    'first_value': data[0]['close'] if data else None,
                    'change_percent': round(((data[-1]['close'] - data[0]['close']) / data[0]['close']) * 100, 2) if data and len(data) >= 2 else 0,
                    'records': len(data),
                    'timestamp': datetime.now().isoformat()
                }

            return result

        except Exception as e:
            logger.error(f"[INTERNATIONAL] Erreur historique {symbol}: {e}")
            return {'success': False, 'error': str(e)}

    def _get_fred_historical(self, config: Dict, period: str) -> Dict[str, Any]:
        """Recupere les donnees historiques depuis FRED"""
        if not self.fred:
            return {'success': False, 'error': 'FRED non disponible'}

        series = config.get('series', '')

        # Mapping des periodes vers nombre d'observations
        period_limits = {
            '1d': 2,
            '7d': 10,
            '1m': 30,
            '3m': 90,
            '6m': 180,
            '1y': 365
        }

        limit = period_limits.get(period, 30)

        try:
            result = self.fred.get_series(series, limit=limit)

            if result and result.get('observations'):
                observations = result['observations']
                # Inverser pour avoir l'ordre chronologique
                observations = list(reversed(observations))

                data = [
                    {
                        'date': obs['date'],
                        'close': obs['value']
                    }
                    for obs in observations if obs['value'] is not None
                ]

                return {
                    'success': True,
                    'id': config['id'],
                    'name': config['name'],
                    'series': series,
                    'period': period,
                    'data': data,
                    'last_value': data[-1]['close'] if data else None,
                    'first_value': data[0]['close'] if data else None,
                    'change_percent': round(((data[-1]['close'] - data[0]['close']) / data[0]['close']) * 100, 2) if data and len(data) >= 2 and data[0]['close'] != 0 else 0,
                    'records': len(data),
                    'timestamp': datetime.now().isoformat()
                }

            return {'success': False, 'error': 'Pas de donnees FRED'}

        except Exception as e:
            logger.error(f"[INTERNATIONAL] Erreur historique FRED {series}: {e}")
            return {'success': False, 'error': str(e)}

    def get_all_indicators(self, force_refresh: bool = False) -> Dict[str, List[Dict[str, Any]]]:
        """
        Recupere tous les indicateurs groupes par categorie

        Returns:
            Dict avec les indicateurs par categorie
        """
        all_data = {}

        for category in self.categories:
            category_indicators = self.get_indicators_by_category(category)
            all_data[category] = []

            for config in category_indicators:
                data = self.get_indicator_by_id(config['id'], force_refresh)
                if data:
                    all_data[category].append(data)

        return all_data
