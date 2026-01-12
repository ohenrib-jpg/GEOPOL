"""
Service pour les données cryptomonnaies
Sources: yFinance, CoinGecko (si disponible)
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from .base_service import BaseEconomicService

logger = logging.getLogger(__name__)


class CryptoService(BaseEconomicService):
    """Service pour les données cryptomonnaies"""

    # Cryptomonnaies surveillées (limité à 3)
    TRACKED_CRYPTOS = [
        {'id': 'bitcoin', 'symbol': 'BTC-USD', 'name': 'Bitcoin', 'max_supply': 21000000},
        {'id': 'ethereum', 'symbol': 'ETH-USD', 'name': 'Ethereum', 'max_supply': None},
        {'id': 'solana', 'symbol': 'SOL-USD', 'name': 'Solana', 'max_supply': None},
        {'id': 'cardano', 'symbol': 'ADA-USD', 'name': 'Cardano', 'max_supply': 45000000000},
        {'id': 'ripple', 'symbol': 'XRP-USD', 'name': 'Ripple', 'max_supply': 100000000000},
        {'id': 'polkadot', 'symbol': 'DOT-USD', 'name': 'Polkadot', 'max_supply': None},
        {'id': 'binance', 'symbol': 'BNB-USD', 'name': 'Binance Coin', 'max_supply': 200000000},
    ]

    def __init__(self, db_manager):
        super().__init__(db_manager)

        # Import conditionnel des connecteurs
        try:
            from Flask.yfinance_connector import YFinanceConnector
            self.yfinance = YFinanceConnector()
            logger.info("[CRYPTO] Connecteur yFinance initialisé")
        except ImportError:
            try:
                from yfinance_connector import YFinanceConnector
                self.yfinance = YFinanceConnector()
                logger.info("[CRYPTO] Connecteur yFinance initialisé")
            except ImportError:
                logger.warning("[CRYPTO] Connecteur yFinance non disponible")
                self.yfinance = None

        # Connecteur CoinGecko (optionnel)
        self.coingecko = None
        try:
            # TODO: Implémenter le connecteur CoinGecko si nécessaire
            pass
        except ImportError:
            pass

    def get_crypto_data(self, crypto_id: str) -> Dict[str, Any]:
        """
        Récupère les données d'une cryptomonnaie

        Args:
            crypto_id: ID de la cryptomonnaie (bitcoin, ethereum, etc.)

        Returns:
            Données de la cryptomonnaie
        """
        crypto_config = next((c for c in self.TRACKED_CRYPTOS if c['id'] == crypto_id), None)
        if not crypto_config:
            return {'success': False, 'error': f'Cryptomonnaie {crypto_id} non supportée'}

        if not self.yfinance:
            return {'success': False, 'error': 'Connecteur yFinance non disponible'}

        try:
            # Utiliser yFinance pour les données en temps réel
            symbol = crypto_config['symbol']
            result = self.yfinance.get_index_data(symbol)

            if result.get('success'):
                return {
                    'success': True,
                    'id': crypto_id,
                    'symbol': symbol,
                    'name': crypto_config['name'],
                    'current_price': result['current_price'],
                    'change_percent': result['change_percent'],
                    'trend': result['trend'],
                    'market_cap': 0,  # TODO: Récupérer via CoinGecko
                    'volume_24h': 0,   # TODO: Récupérer via CoinGecko
                    'max_supply': crypto_config['max_supply'],
                    'timestamp': datetime.now().isoformat(),
                    'source': 'yFinance'
                }
            else:
                return result

        except Exception as e:
            logger.error(f"[CRYPTO] Erreur données {crypto_id}: {e}")
            return {'success': False, 'error': str(e)}

    def get_all_cryptos(self, limit: int = 3) -> Dict[str, Any]:
        """
        Récupère les données des cryptomonnaies surveillées (limité à 3)

        Args:
            limit: Nombre maximum de cryptomonnaies à retourner

        Returns:
            Liste des cryptomonnaies
        """
        if not self.yfinance:
            return {'success': False, 'error': 'Connecteur yFinance non disponible'}

        try:
            cryptos = []
            for crypto in self.TRACKED_CRYPTOS[:limit]:
                data = self.get_crypto_data(crypto['id'])
                if data.get('success'):
                    cryptos.append(data)

            return {
                'success': True,
                'cryptos': cryptos,
                'count': len(cryptos),
                'limit': limit,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"[CRYPTO] Erreur toutes cryptos: {e}")
            return {'success': False, 'error': str(e)}

    def get_crypto_historical_data(self, crypto_id: str, period: str = '1m') -> Dict[str, Any]:
        """
        Récupère les données historiques d'une cryptomonnaie pour le graphique

        Args:
            crypto_id: ID de la cryptomonnaie
            period: Période ('1d', '7d', '1m', '3m', '6m', '1y')

        Returns:
            Données historiques
        """
        crypto_config = next((c for c in self.TRACKED_CRYPTOS if c['id'] == crypto_id), None)
        if not crypto_config:
            return {'success': False, 'error': f'Cryptomonnaie {crypto_id} non supportée'}

        if not self.yfinance:
            return {'success': False, 'error': 'Connecteur yFinance non disponible'}

        try:
            symbol = crypto_config['symbol']
            result = self.yfinance.get_historical_data(symbol, period=self._map_period(period))

            if result.get('success'):
                # Adapter le format pour correspondre aux attentes des graphiques
                data = result.get('data', [])
                return {
                    'success': True,
                    'id': crypto_id,
                    'symbol': symbol,
                    'name': crypto_config['name'],
                    'period': period,
                    'data': data,
                    'last_value': data[-1]['close'] if data else None,
                    'first_value': data[0]['close'] if data else None,
                    'change_percent': round(((data[-1]['close'] - data[0]['close']) / data[0]['close']) * 100, 2) if data and len(data) >= 2 else 0,
                    'records': len(data),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return result

        except Exception as e:
            logger.error(f"[CRYPTO] Erreur historique {crypto_id}: {e}")
            return {'success': False, 'error': str(e)}

    def get_crypto_market_overview(self) -> Dict[str, Any]:
        """
        Récupère une vue d'ensemble du marché des cryptomonnaies

        Returns:
            Vue d'ensemble du marché
        """
        try:
            # TODO: Implémenter avec CoinGecko ou autre API
            return {
                'success': True,
                'total_market_cap': 0,
                'total_volume_24h': 0,
                'btc_dominance': 0,
                'fear_greed_index': 0,
                'active_cryptos': len(self.TRACKED_CRYPTOS),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"[CRYPTO] Erreur market overview: {e}")
            return {'success': False, 'error': str(e)}

    def get_crypto_news(self, limit: int = 5) -> Dict[str, Any]:
        """
        Récupère les actualités récentes sur les cryptomonnaies

        Args:
            limit: Nombre maximum d'actualités

        Returns:
            Liste d'actualités
        """
        try:
            # TODO: Implémenter avec une API d'actualités
            return {
                'success': True,
                'news': [],
                'count': 0,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"[CRYPTO] Erreur news: {e}")
            return {'success': False, 'error': str(e)}

    def _map_period(self, period: str) -> str:
        """
        Mappe les périodes du frontend vers les périodes yFinance

        Args:
            period: Période frontend ('1d', '7d', '1m', '3m', '6m', '1y')

        Returns:
            Période yFinance
        """
        mapping = {
            '1d': '1d',
            '7d': '5d',
            '1m': '1mo',
            '3m': '3mo',
            '6m': '6mo',
            '1y': '1y'
        }
        return mapping.get(period, '1mo')

    def validate_crypto_limit(self, current_count: int) -> Dict[str, Any]:
        """
        Vérifie si la limite de cryptomonnaies surveillées est atteinte

        Args:
            current_count: Nombre actuel de cryptomonnaies surveillées

        Returns:
            Statut de validation
        """
        max_limit = 3  # Limite configurable
        return {
            'success': True,
            'current_count': current_count,
            'max_limit': max_limit,
            'can_add': current_count < max_limit,
            'remaining': max(max_limit - current_count, 0)
        }