"""
Service pour les marches financiers internationaux
Sources: yFinance (indices mondiaux, ETFs)
"""
import logging
from typing import Dict, List, Optional, Any

from .base_service import BaseEconomicService
from ..config import EconomicConfig

logger = logging.getLogger(__name__)

class MarketService(BaseEconomicService):
    """Service pour les marches financiers internationaux"""

    def __init__(self, db_manager):
        super().__init__(db_manager)

        # Import yFinance connector
        try:
            from Flask.yfinance_connector import YFinanceConnector
            self.yfinance = YFinanceConnector()
        except ImportError:
            try:
                from yfinance_connector import YFinanceConnector
                self.yfinance = YFinanceConnector()
            except ImportError:
                logger.warning("[MARKET] yFinance connector non disponible")
                self.yfinance = None

    def get_all_indices(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Recupere tous les indices internationaux par defaut

        Args:
            force_refresh: Forcer rafraichissement

        Returns:
            Liste des indices
        """
        indices = []

        for index_config in EconomicConfig.DEFAULT_INTERNATIONAL_INDICES:
            index_data = self.get_index(
                index_config['symbol'],
                index_config['name'],
                index_config['region'],
                force_refresh
            )
            if index_data:
                indices.append(index_data)

        return indices

    def get_index(
        self,
        symbol: str,
        name: str,
        region: str,
        force_refresh: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Recupere un indice boursier specifique

        Args:
            symbol: Symbole de l'indice (ex: ^GSPC)
            name: Nom de l'indice
            region: Region (USA, Europe, Asie)
            force_refresh: Forcer rafraichissement

        Returns:
            Donnees de l'indice
        """
        if not self.yfinance:
            return None

        cache_key = f"index_{symbol}"

        def fetch():
            try:
                result = self.yfinance.get_index_data(symbol)
                if result.get('success'):
                    return {
                        'symbol': symbol,
                        'name': name,
                        'region': region,
                        'value': result['current_price'],
                        'change_percent': result['change_percent'],
                        'trend': 'up' if result['change_percent'] > 0 else 'down',
                        'currency': 'USD',  # La plupart des indices en USD
                        'country': result.get('country', region)
                    }
            except Exception as e:
                logger.error(f"[MARKET] Erreur index {symbol}: {e}")
            return None

        return self.fetch_with_cache(
            cache_key=cache_key,
            fetch_func=fetch,
            data_source='yfinance',
            data_type='index',
            expiry_hours=2,
            force_refresh=force_refresh
        )

    def get_indices_by_region(
        self,
        region: str,
        force_refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Recupere les indices d'une region specifique

        Args:
            region: Region (USA, Europe, Asie)
            force_refresh: Forcer rafraichissement

        Returns:
            Liste des indices de la region
        """
        all_indices = self.get_all_indices(force_refresh)
        return [idx for idx in all_indices if idx.get('region') == region]

    def get_etf_data(
        self,
        symbol: str,
        name: str,
        force_refresh: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Recupere les donnees d'un ETF

        Args:
            symbol: Symbole ETF
            name: Nom ETF
            force_refresh: Forcer rafraichissement

        Returns:
            Donnees de l'ETF
        """
        if not self.yfinance:
            return None

        cache_key = f"etf_{symbol}"

        def fetch():
            try:
                result = self.yfinance.get_index_data(symbol)
                if result.get('success'):
                    return {
                        'symbol': symbol,
                        'name': name,
                        'type': 'etf',
                        'value': result['current_price'],
                        'change_percent': result['change_percent'],
                        'trend': 'up' if result['change_percent'] > 0 else 'down',
                        'currency': 'USD'
                    }
            except Exception as e:
                logger.error(f"[MARKET] Erreur ETF {symbol}: {e}")
            return None

        return self.fetch_with_cache(
            cache_key=cache_key,
            fetch_func=fetch,
            data_source='yfinance',
            data_type='etf',
            expiry_hours=2,
            force_refresh=force_refresh
        )

    def get_crypto_data(
        self,
        symbol: str,
        name: str,
        force_refresh: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        Recupere les donnees d'une cryptomonnaie

        Args:
            symbol: Symbole crypto (ex: BTC-USD)
            name: Nom crypto
            force_refresh: Forcer rafraichissement

        Returns:
            Donnees de la crypto
        """
        if not self.yfinance:
            return None

        cache_key = f"crypto_{symbol}"

        def fetch():
            try:
                result = self.yfinance.get_index_data(symbol)
                if result.get('success'):
                    return {
                        'symbol': symbol,
                        'name': name,
                        'type': 'crypto',
                        'value': result['current_price'],
                        'change_percent': result['change_percent'],
                        'trend': 'up' if result['change_percent'] > 0 else 'down',
                        'currency': 'USD'
                    }
            except Exception as e:
                logger.error(f"[MARKET] Erreur crypto {symbol}: {e}")
            return None

        return self.fetch_with_cache(
            cache_key=cache_key,
            fetch_func=fetch,
            data_source='yfinance',
            data_type='crypto',
            expiry_hours=1,  # Crypto plus volatile, cache 1h
            force_refresh=force_refresh
        )

    def get_market_summary(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Recupere un resume des marches mondiaux

        Args:
            force_refresh: Forcer rafraichissement

        Returns:
            Resume avec indices par region
        """
        indices = self.get_all_indices(force_refresh)

        # Grouper par region
        by_region = {}
        for index in indices:
            region = index.get('region', 'Other')
            if region not in by_region:
                by_region[region] = []
            by_region[region].append(index)

        # Calculer moyennes par region
        region_summary = {}
        for region, region_indices in by_region.items():
            changes = [idx['change_percent'] for idx in region_indices if idx.get('change_percent') is not None]
            if changes:
                avg_change = sum(changes) / len(changes)
                region_summary[region] = {
                    'count': len(region_indices),
                    'avg_change': round(avg_change, 2),
                    'trend': 'up' if avg_change > 0 else 'down',
                    'indices': region_indices
                }

        return {
            'total_indices': len(indices),
            'by_region': region_summary,
            'timestamp': indices[0].get('last_updated') if indices else None
        }
