"""
Service pour les indicateurs economiques de la France
Sources: Eurostat, yFinance
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from .base_service import BaseEconomicService
from ..config import EconomicConfig
from ..models.indicator import EconomicIndicator

logger = logging.getLogger(__name__)


# Liste complete des indicateurs France disponibles pour configuration widgets
AVAILABLE_FRANCE_INDICATORS = [
    {'id': 'cac40', 'name': 'CAC 40', 'category': 'Indice', 'source': 'yfinance', 'symbol': '^FCHI', 'unit': 'points', 'currency': 'EUR'},
    {'id': 'pib', 'name': 'PIB France', 'category': 'Macro', 'source': 'eurostat', 'unit': 'Md EUR', 'currency': 'Md EUR'},
    {'id': 'inflation', 'name': 'Inflation', 'category': 'Macro', 'source': 'eurostat', 'unit': '%', 'currency': '%'},
    {'id': 'chomage', 'name': 'Chomage', 'category': 'Macro', 'source': 'eurostat', 'unit': '%', 'currency': '%'},
    {'id': 'balance_commerciale', 'name': 'Balance Commerciale', 'category': 'Commerce', 'source': 'eurostat', 'unit': 'Md EUR', 'currency': 'Md EUR'},
    {'id': 'dette_publique', 'name': 'Dette Publique', 'category': 'Macro', 'source': 'eurostat', 'unit': '% PIB', 'currency': '% PIB'},
    {'id': 'taux_interet', 'name': 'Taux BCE', 'category': 'Monetaire', 'source': 'eurostat', 'unit': '%', 'currency': '%'},
    {'id': 'production_industrielle', 'name': 'Production Industrielle', 'category': 'Industrie', 'source': 'eurostat', 'unit': 'indice', 'currency': ''},
    {'id': 'confiance_consommateur', 'name': 'Confiance Consommateur', 'category': 'Sentiment', 'source': 'eurostat', 'unit': 'indice', 'currency': ''},
    {'id': 'pmi_manufacturier', 'name': 'PMI Manufacturier', 'category': 'Industrie', 'source': 'eurostat', 'unit': 'indice', 'currency': ''},
    {'id': 'immobilier', 'name': 'Indice Immobilier', 'category': 'Immobilier', 'source': 'eurostat', 'unit': 'indice', 'currency': ''},
    {'id': 'euro_usd', 'name': 'EUR/USD', 'category': 'Devise', 'source': 'yfinance', 'symbol': 'EURUSD=X', 'unit': '', 'currency': 'USD'},
]


class FranceService(BaseEconomicService):
    """Service pour les indicateurs economiques francais"""

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
                logger.warning("[FRANCE] yFinance connector non disponible")
                self.yfinance = None

        # Connecteur Eurostat Hybrid (avec fallback World Bank, OECD)
        try:
            from Flask.eurostat_connector import EurostatHybridConnector
            self.eurostat = EurostatHybridConnector()
            logger.info("[FRANCE] Eurostat Hybrid connector initialise")
        except ImportError:
            try:
                from eurostat_connector import EurostatHybridConnector
                self.eurostat = EurostatHybridConnector()
                logger.info("[FRANCE] Eurostat Hybrid connector initialise")
            except ImportError:
                logger.warning("[FRANCE] Eurostat connector non disponible")
                self.eurostat = None

    def get_france_indicators(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Recupere tous les indicateurs economiques francais

        Args:
            force_refresh: Forcer rafraichissement des donnees

        Returns:
            Liste des indicateurs
        """
        indicators = []

        # CAC 40
        cac40 = self.get_cac40(force_refresh)
        if cac40:
            indicators.append(cac40)

        # PIB France
        gdp = self.get_gdp_france(force_refresh)
        if gdp:
            indicators.append(gdp)

        # Inflation France
        inflation = self.get_inflation_france(force_refresh)
        if inflation:
            indicators.append(inflation)

        # Chomage France
        unemployment = self.get_unemployment_france(force_refresh)
        if unemployment:
            indicators.append(unemployment)

        return indicators

    def get_cac40(self, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """Recupere les donnees du CAC 40 via yFinance"""
        if not self.yfinance:
            logger.warning("[FRANCE] yFinance non disponible pour CAC 40")
            return None

        cache_key = "france_cac40"

        def fetch():
            try:
                result = self.yfinance.get_index_data('^FCHI')
                if result.get('success'):
                    return {
                        'name': 'CAC 40',
                        'value': result['current_price'],
                        'change_percent': result['change_percent'],
                        'currency': 'EUR',
                        'unit': 'points'
                    }
            except Exception as e:
                logger.error(f"[FRANCE] Erreur CAC 40: {e}")
            return None

        return self.fetch_with_cache(
            cache_key=cache_key,
            fetch_func=fetch,
            data_source='yfinance',
            data_type='index',
            expiry_hours=2,
            force_refresh=force_refresh
        )

    def get_gdp_france(self, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """
        Recupere le PIB francais depuis Eurostat
        Dataset: namq_10_gdp (GDP and main components)
        """
        cache_key = "france_gdp"

        def fetch():
            if self.eurostat:
                try:
                    result = self.eurostat.get_indicator('gdp', force_refresh=force_refresh)
                    if result and result.get('success', True) and 'value' in result:
                        return {
                            'name': 'PIB France',
                            'value': round(result['value'], 1),
                            'change_percent': round(result.get('change_percent', 0), 2),
                            'currency': '%',  # CLV_PCH_PRE = variation en %
                            'unit': '% croissance',
                            'period': result.get('period', 'N/A'),
                            'source': 'eurostat'
                        }
                except Exception as e:
                    logger.error(f"[FRANCE] Erreur Eurostat PIB: {e}")

            # Fallback donnees de demonstration
            logger.warning("[FRANCE] PIB: utilisation donnees demo")
            return {
                'name': 'PIB France',
                'value': 0.2,
                'change_percent': 0.1,
                'currency': '%',
                'unit': '% croissance',
                'period': '2024-Q4',
                'source': 'demo'
            }

        return self.fetch_with_cache(
            cache_key=cache_key,
            fetch_func=fetch,
            data_source='eurostat',
            data_type='macroeconomic',
            expiry_hours=24,
            force_refresh=force_refresh
        )

    def get_inflation_france(self, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """
        Recupere l'inflation francaise depuis Eurostat
        Dataset: prc_hicp_midx (HICP - monthly data)
        """
        cache_key = "france_inflation"

        def fetch():
            if self.eurostat:
                try:
                    result = self.eurostat.get_indicator('inflation', force_refresh=force_refresh)
                    if result and result.get('success', True) and 'value' in result:
                        return {
                            'name': 'Inflation France',
                            'value': round(result['value'], 1),
                            'change_percent': round(result.get('change_percent', 0), 2),
                            'currency': '%',
                            'unit': '%',
                            'period': result.get('period', 'N/A'),
                            'source': 'eurostat'
                        }
                except Exception as e:
                    logger.error(f"[FRANCE] Erreur Eurostat Inflation: {e}")

            # Fallback donnees de demonstration
            logger.warning("[FRANCE] Inflation: utilisation donnees demo")
            return {
                'name': 'Inflation France',
                'value': 1.8,
                'change_percent': -0.2,
                'currency': '%',
                'unit': '%',
                'period': '2024-12',
                'source': 'demo'
            }

        return self.fetch_with_cache(
            cache_key=cache_key,
            fetch_func=fetch,
            data_source='eurostat',
            data_type='macroeconomic',
            expiry_hours=24,
            force_refresh=force_refresh
        )

    def get_unemployment_france(self, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """
        Recupere le taux de chomage francais depuis Eurostat
        Dataset: une_rt_m (Unemployment rate - monthly)
        La valeur retournee par Eurostat est deja en pourcentage (ex: 7.4 = 7.4%)
        """
        cache_key = "france_unemployment"

        def fetch():
            if self.eurostat:
                try:
                    result = self.eurostat.get_indicator('unemployment', force_refresh=force_refresh)
                    if result and result.get('success', True) and 'value' in result:
                        # Eurostat retourne directement le taux en % (ex: 7.4)
                        value = result['value']

                        # Calculer la variation par rapport a la valeur precedente
                        # change_percent ici = difference en points de pourcentage, pas en %
                        prev_value = result.get('previous_value', value)
                        change_points = value - prev_value  # Variation en points

                        return {
                            'name': 'Chomage France',
                            'value': round(value, 1),
                            'change_percent': round(change_points, 2),  # Points de variation
                            'currency': '%',
                            'unit': '%',
                            'period': result.get('period', 'N/A'),
                            'source': 'eurostat'
                        }
                except Exception as e:
                    logger.error(f"[FRANCE] Erreur Eurostat Chomage: {e}")

            # Fallback donnees de demonstration
            logger.warning("[FRANCE] Chomage: utilisation donnees demo")
            return {
                'name': 'Chomage France',
                'value': 7.3,
                'change_percent': -0.1,
                'currency': '%',
                'unit': '%',
                'period': '2024-12',
                'source': 'demo'
            }

        return self.fetch_with_cache(
            cache_key=cache_key,
            fetch_func=fetch,
            data_source='eurostat',
            data_type='macroeconomic',
            expiry_hours=24,
            force_refresh=force_refresh
        )

    def get_balance_commerciale(self, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """
        Recupere la balance commerciale francaise

        TODO: Implementer avec Eurostat ou Comtrade
        """
        cache_key = "france_trade_balance"

        def fetch():
            # TODO: Implementer
            return {
                'name': 'Balance commerciale',
                'value': -8.2,
                'change_percent': 1.5,
                'currency': 'Md EUR',
                'unit': 'Md EUR',
                'period': '2024-Q4'
            }

        return self.fetch_with_cache(
            cache_key=cache_key,
            fetch_func=fetch,
            data_source='eurostat',
            data_type='trade',
            expiry_hours=24,
            force_refresh=force_refresh
        )

    def get_available_indicators(self) -> List[Dict[str, Any]]:
        """Retourne la liste des indicateurs France disponibles pour configuration"""
        return AVAILABLE_FRANCE_INDICATORS

    def get_indicator_by_id(self, indicator_id: str, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """
        Recupere un indicateur par son ID

        Args:
            indicator_id: ID de l'indicateur (ex: 'cac40', 'pib', etc.)
            force_refresh: Forcer le rafraichissement

        Returns:
            Donnees de l'indicateur ou None
        """
        # Mapping des IDs vers les methodes
        indicator_methods = {
            'cac40': self.get_cac40,
            'pib': self.get_gdp_france,
            'inflation': self.get_inflation_france,
            'chomage': self.get_unemployment_france,
            'balance_commerciale': self.get_balance_commerciale,
            'dette_publique': self._get_dette_publique,
            'taux_interet': self._get_taux_bce,
            'production_industrielle': self._get_production_industrielle,
            'confiance_consommateur': self._get_confiance_consommateur,
            'pmi_manufacturier': self._get_pmi_manufacturier,
            'immobilier': self._get_indice_immobilier,
            'euro_usd': self._get_euro_usd,
        }

        method = indicator_methods.get(indicator_id)
        if method:
            return method(force_refresh)
        return None

    def get_cac40_historical(self, period: str = '1d') -> Dict[str, Any]:
        """
        Recupere les donnees historiques du CAC40 pour le graphique

        Args:
            period: Periode ('realtime', '1d', '2d', '3d', '7d', '1m')

        Returns:
            Donnees historiques avec timestamps et valeurs
        """
        if not self.yfinance:
            return {'success': False, 'error': 'yFinance non disponible'}

        # Mapping des periodes vers yfinance
        period_mapping = {
            'realtime': '1d',   # Donnees intraday du jour
            '1d': '1d',
            '2d': '2d',
            '3d': '5d',         # yfinance n'a pas 3d, on prend 5d
            '7d': '5d',
            '1m': '1mo'
        }

        yf_period = period_mapping.get(period, '1d')

        try:
            result = self.yfinance.get_historical_data('^FCHI', period=yf_period, timeout=15)

            if result.get('success'):
                data = result.get('data', [])

                # Pour realtime, on garde seulement les dernieres heures
                if period == 'realtime' and data:
                    # Garder seulement les 24 dernieres heures
                    data = data[-24:] if len(data) > 24 else data

                # Pour 7d, filtrer les donnees
                if period == '7d' and data:
                    today = datetime.now()
                    week_ago = today - timedelta(days=7)
                    data = [d for d in data if datetime.strptime(d['date'], '%Y-%m-%d') >= week_ago]

                return {
                    'success': True,
                    'symbol': '^FCHI',
                    'name': 'CAC 40',
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
            logger.error(f"[FRANCE] Erreur historique CAC40: {e}")
            return {'success': False, 'error': str(e)}

    # Methodes pour les indicateurs supplementaires (donnees de demo pour l'instant)
    def _get_dette_publique(self, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """Dette publique en % du PIB"""
        return {
            'id': 'dette_publique',
            'name': 'Dette Publique',
            'value': 111.8,
            'change_percent': 0.5,
            'currency': '% PIB',
            'unit': '% PIB',
            'period': '2024-Q4',
            'source': 'eurostat'
        }

    def _get_taux_bce(self, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """Taux directeur BCE"""
        return {
            'id': 'taux_interet',
            'name': 'Taux BCE',
            'value': 4.25,
            'change_percent': 0.0,
            'currency': '%',
            'unit': '%',
            'period': '2024-12',
            'source': 'bce'
        }

    def _get_production_industrielle(self, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """Indice de production industrielle"""
        return {
            'id': 'production_industrielle',
            'name': 'Production Industrielle',
            'value': 98.5,
            'change_percent': -1.2,
            'currency': '',
            'unit': 'indice base 100',
            'period': '2024-12',
            'source': 'insee'
        }

    def _get_confiance_consommateur(self, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """Indice de confiance des consommateurs"""
        return {
            'id': 'confiance_consommateur',
            'name': 'Confiance Consommateur',
            'value': 92,
            'change_percent': 2.0,
            'currency': '',
            'unit': 'indice',
            'period': '2024-12',
            'source': 'insee'
        }

    def _get_pmi_manufacturier(self, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """PMI Manufacturier France"""
        return {
            'id': 'pmi_manufacturier',
            'name': 'PMI Manufacturier',
            'value': 43.1,
            'change_percent': -0.5,
            'currency': '',
            'unit': 'indice',
            'period': '2024-12',
            'source': 'spglobal'
        }

    def _get_indice_immobilier(self, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """Indice des prix immobiliers"""
        return {
            'id': 'immobilier',
            'name': 'Indice Immobilier',
            'value': 127.3,
            'change_percent': -3.5,
            'currency': '',
            'unit': 'indice base 100',
            'period': '2024-Q4',
            'source': 'insee'
        }

    def _get_euro_usd(self, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
        """Taux de change EUR/USD"""
        if not self.yfinance:
            return {
                'id': 'euro_usd',
                'name': 'EUR/USD',
                'value': 1.08,
                'change_percent': 0.1,
                'currency': 'USD',
                'unit': '',
                'source': 'demo'
            }

        cache_key = "france_eurusd"

        def fetch():
            try:
                result = self.yfinance.get_index_data('EURUSD=X')
                if result.get('success'):
                    return {
                        'id': 'euro_usd',
                        'name': 'EUR/USD',
                        'value': result['current_price'],
                        'change_percent': result['change_percent'],
                        'currency': 'USD',
                        'unit': '',
                        'source': 'yfinance'
                    }
            except Exception as e:
                logger.error(f"[FRANCE] Erreur EUR/USD: {e}")
            return None

        return self.fetch_with_cache(
            cache_key=cache_key,
            fetch_func=fetch,
            data_source='yfinance',
            data_type='forex',
            expiry_hours=1,
            force_refresh=force_refresh
        )

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
                data['id'] = indicator_id
                results.append(data)
        return results
