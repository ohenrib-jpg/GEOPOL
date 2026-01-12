"""
Connecteur AKShare pour les marchés asiatiques (Chine, Hong Kong)
Architecture similaire à yfinance_connector.py
Compatible avec cache_manager et indicators_data_collector
"""

import logging
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from cache_manager import cache_manager

logger = logging.getLogger(__name__)


class AKShareConnector:
    """
    Connecteur pour les marchés asiatiques via AKShare
    Données: Shanghai, Shenzhen, Hong Kong, A-Shares
    """

    # Mapping des indices asiatiques
    ASIAN_INDICES = {
        # Shanghai Stock Exchange
        'sh000001': {'name': 'Shanghai Composite', 'symbol_ak': '000001', 'exchange': 'SSE'},
        'sh000016': {'name': 'SSE 50', 'symbol_ak': '000016', 'exchange': 'SSE'},
        'sh000300': {'name': 'CSI 300', 'symbol_ak': '000300', 'exchange': 'CSI'},

        # Shenzhen Stock Exchange
        'sz399001': {'name': 'Shenzhen Component', 'symbol_ak': '399001', 'exchange': 'SZSE'},
        'sz399006': {'name': 'ChiNext', 'symbol_ak': '399006', 'exchange': 'SZSE'},

        # Hong Kong
        'hsi': {'name': 'Hang Seng Index', 'symbol_ak': 'HSI', 'exchange': 'HKEX'},
    }

    def __init__(self):
        """Initialise le connecteur AKShare"""
        self.cache = cache_manager
        logger.info("AKShare Connector initialized for Asian markets")

    def get_index_data(self, symbol: str, use_cache: bool = True) -> Dict[str, Any]:
        """
        Récupère les données d'un indice asiatique

        Args:
            symbol: Code de l'indice (ex: 'sh000001' pour Shanghai Composite)
            use_cache: Utiliser le cache si disponible

        Returns:
            Dict avec les données de l'indice
        """
        try:
            # Vérifier le cache d'abord
            if use_cache:
                cached = self.cache.get('akshare', f'index_{symbol}')
                if cached:
                    logger.debug(f"Cache hit: akshare index {symbol}")
                    return cached['data']

            # Vérifier si l'indice existe dans notre mapping
            if symbol not in self.ASIAN_INDICES:
                logger.warning(f"Indice non supporté: {symbol}")
                return {'success': False, 'error': f'Index {symbol} not supported'}

            index_info = self.ASIAN_INDICES[symbol]
            symbol_ak = index_info['symbol_ak']

            # Récupérer les données historiques (30 derniers jours)
            hist_data = ak.index_zh_a_hist(symbol=symbol_ak, period='daily')

            if hist_data is None or len(hist_data) == 0:
                logger.warning(f"Pas de données pour {symbol}")
                return {'success': False, 'error': 'No data available'}

            # Obtenir les dernières données
            latest = hist_data.tail(1).iloc[0]
            previous = hist_data.tail(2).iloc[0] if len(hist_data) >= 2 else None

            # Calculer la variation
            current_price = float(latest['收盘'])  # Close price
            if previous is not None:
                prev_price = float(previous['收盘'])
                change = current_price - prev_price
                change_percent = (change / prev_price) * 100
            else:
                change = 0
                change_percent = 0

            # Construire la réponse
            result = {
                'success': True,
                'symbol': symbol,
                'name': index_info['name'],
                'exchange': index_info['exchange'],
                'current_price': current_price,
                'open': float(latest['开盘']),  # Open
                'high': float(latest['最高']),  # High
                'low': float(latest['最低']),   # Low
                'volume': int(latest['成交量']) if '成交量' in latest.index else 0,
                'change': round(change, 2),
                'change_percent': round(change_percent, 2),
                'date': str(latest['日期']),
                'timestamp': datetime.now().isoformat(),
                'source': 'AKShare'
            }

            # Sauvegarder dans le cache (1 heure)
            self.cache.set('akshare', f'index_{symbol}', result, ttl_hours=1, compress=True)

            logger.info(f"Retrieved {symbol}: {current_price} ({change_percent:+.2f}%)")
            return result

        except Exception as e:
            logger.error(f"Error fetching {symbol}: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'symbol': symbol
            }

    def get_multiple_indices(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Récupère plusieurs indices en une seule fois

        Args:
            symbols: Liste des codes d'indices

        Returns:
            Dict {symbol: data}
        """
        results = {}

        for symbol in symbols:
            try:
                data = self.get_index_data(symbol)
                results[symbol] = data
            except Exception as e:
                logger.error(f"Error fetching {symbol}: {e}")
                results[symbol] = {'success': False, 'error': str(e)}

        return results

    def get_all_main_indices(self) -> Dict[str, Any]:
        """
        Récupère tous les indices principaux asiatiques

        Returns:
            Dict avec tous les indices
        """
        main_symbols = ['sh000001', 'sh000300', 'sz399001', 'hsi']
        return self.get_multiple_indices(main_symbols)

    def get_stock_data(self, symbol: str) -> Dict[str, Any]:
        """
        Récupère les données d'une action A-share chinoise

        Args:
            symbol: Code de l'action (ex: '600519' pour Kweichow Moutai)

        Returns:
            Dict avec les données de l'action
        """
        try:
            # Vérifier le cache
            cached = self.cache.get('akshare', f'stock_{symbol}')
            if cached:
                return cached['data']

            # Récupérer données en temps réel
            # Note: AKShare utilise stock_zh_a_spot_em() pour le temps réel
            spot_data = ak.stock_zh_a_spot_em()

            if spot_data is None or len(spot_data) == 0:
                return {'success': False, 'error': 'No market data available'}

            # Trouver l'action
            stock_row = spot_data[spot_data['代码'] == symbol]

            if stock_row.empty:
                return {'success': False, 'error': f'Stock {symbol} not found'}

            stock = stock_row.iloc[0]

            result = {
                'success': True,
                'symbol': symbol,
                'name': stock['名称'],
                'current_price': float(stock['最新价']),
                'change_percent': float(stock['涨跌幅']),
                'change': float(stock['涨跌额']),
                'volume': int(stock['成交量']),
                'turnover': float(stock['成交额']),
                'high': float(stock['最高']),
                'low': float(stock['最低']),
                'open': float(stock['今开']),
                'prev_close': float(stock['昨收']),
                'timestamp': datetime.now().isoformat(),
                'source': 'AKShare'
            }

            # Cache 5 minutes pour les actions
            self.cache.set('akshare', f'stock_{symbol}', result, ttl_hours=0.08, compress=True)

            return result

        except Exception as e:
            logger.error(f"Error fetching stock {symbol}: {e}")
            return {'success': False, 'error': str(e)}

    def get_historical_data(self, symbol: str, days: int = 90) -> Optional[pd.DataFrame]:
        """
        Récupère les données historiques pour calculs d'indicateurs techniques

        Args:
            symbol: Code de l'indice
            days: Nombre de jours de données

        Returns:
            DataFrame avec les données historiques
        """
        try:
            if symbol not in self.ASIAN_INDICES:
                logger.warning(f"Index {symbol} not supported")
                return None

            symbol_ak = self.ASIAN_INDICES[symbol]['symbol_ak']

            # Récupérer l'historique
            hist_data = ak.index_zh_a_hist(symbol=symbol_ak, period='daily')

            if hist_data is None or len(hist_data) == 0:
                return None

            # Limiter aux N derniers jours
            hist_data = hist_data.tail(days)

            # Renommer les colonnes pour standardisation
            hist_data = hist_data.rename(columns={
                '日期': 'date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume'
            })

            # Convertir les types
            for col in ['open', 'close', 'high', 'low']:
                hist_data[col] = pd.to_numeric(hist_data[col], errors='coerce')

            if 'volume' in hist_data.columns:
                hist_data['volume'] = pd.to_numeric(hist_data['volume'], errors='coerce')

            return hist_data

        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            return None

    def get_market_summary(self) -> Dict[str, Any]:
        """
        Résumé du marché asiatique

        Returns:
            Dict avec statistiques globales
        """
        try:
            indices = self.get_all_main_indices()

            summary = {
                'timestamp': datetime.now().isoformat(),
                'market_status': 'open',  # TODO: Vérifier heures d'ouverture
                'indices': indices,
                'statistics': {
                    'total_indices': len(indices),
                    'positive': sum(1 for i in indices.values() if i.get('success') and i.get('change_percent', 0) > 0),
                    'negative': sum(1 for i in indices.values() if i.get('success') and i.get('change_percent', 0) < 0),
                }
            }

            return summary

        except Exception as e:
            logger.error(f"Error getting market summary: {e}")
            return {'error': str(e)}


# Instance globale
akshare_connector = AKShareConnector()
