"""
Service pour la surveillance personnalisee (watchlist)
Limites: 8 indices maximum + 10 ETF maximum
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from .base_service import BaseEconomicService
from ..config import EconomicConfig

logger = logging.getLogger(__name__)

class WatchlistService(BaseEconomicService):
    """Service pour la surveillance personnalisee des indices et ETFs"""

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
                logger.warning("[WATCHLIST] yFinance connector non disponible")
                self.yfinance = None

    def get_watchlist(self, watchlist_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Recupere la watchlist

        Args:
            watchlist_type: Type ('index', 'etf', ou None pour tous)

        Returns:
            Liste des elements surveilles
        """
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()

            if watchlist_type:
                cursor.execute("""
                    SELECT id, symbol, name, watchlist_type, data_source, enabled, display_order
                    FROM economic_watchlist
                    WHERE watchlist_type = ? AND enabled = 1
                    ORDER BY display_order, name
                """, (watchlist_type,))
            else:
                cursor.execute("""
                    SELECT id, symbol, name, watchlist_type, data_source, enabled, display_order
                    FROM economic_watchlist
                    WHERE enabled = 1
                    ORDER BY watchlist_type, display_order, name
                """)

            watchlist = []
            for row in cursor.fetchall():
                watchlist.append({
                    'id': row[0],
                    'symbol': row[1],
                    'name': row[2],
                    'watchlist_type': row[3],
                    'data_source': row[4],
                    'enabled': row[5],
                    'display_order': row[6]
                })

            conn.close()
            return watchlist

        except Exception as e:
            logger.error(f"[WATCHLIST] Erreur recuperation watchlist: {e}")
            return []

    def get_watchlist_with_prices(
        self,
        watchlist_type: Optional[str] = None,
        force_refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Recupere la watchlist avec les prix actuels

        Args:
            watchlist_type: Type ('index', 'etf', ou None)
            force_refresh: Forcer rafraichissement des prix

        Returns:
            Liste des elements avec prix
        """
        watchlist = self.get_watchlist(watchlist_type)

        # Enrichir avec les prix
        for item in watchlist:
            price_data = self._get_price_data(
                item['symbol'],
                item['name'],
                item['watchlist_type'],
                force_refresh
            )
            if price_data:
                item.update(price_data)

        return watchlist

    def add_to_watchlist(
        self,
        symbol: str,
        name: str,
        watchlist_type: str,
        data_source: str = 'yfinance'
    ) -> Dict[str, Any]:
        """
        Ajoute un element a la watchlist

        Args:
            symbol: Symbole (ex: AAPL, ^GSPC)
            name: Nom descriptif
            watchlist_type: 'index' ou 'etf'
            data_source: Source de donnees

        Returns:
            Resultat avec succes/erreur
        """
        # Verifier les limites
        current_count = self._count_watchlist(watchlist_type)

        if watchlist_type == 'index':
            max_allowed = EconomicConfig.MAX_WATCHLIST_INDICES
        elif watchlist_type == 'etf':
            max_allowed = EconomicConfig.MAX_WATCHLIST_ETFS
        else:
            return {
                'success': False,
                'error': f"Type invalide: {watchlist_type}. Utiliser 'index' ou 'etf'"
            }

        if current_count >= max_allowed:
            return {
                'success': False,
                'error': f"Limite atteinte: maximum {max_allowed} {watchlist_type}",
                'current_count': current_count,
                'max_allowed': max_allowed
            }

        # Ajouter a la DB
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()

            # Verifier si deja existant
            cursor.execute("""
                SELECT id FROM economic_watchlist
                WHERE symbol = ? AND watchlist_type = ?
            """, (symbol, watchlist_type))

            if cursor.fetchone():
                conn.close()
                return {
                    'success': False,
                    'error': f"{symbol} deja dans la watchlist"
                }

            # Inserer
            now = datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO economic_watchlist (
                    symbol, name, watchlist_type, data_source, enabled, display_order, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, 1, 0, ?, ?)
            """, (symbol, name, watchlist_type, data_source, now, now))

            conn.commit()
            item_id = cursor.lastrowid
            conn.close()

            logger.info(f"[WATCHLIST] Ajout: {symbol} ({watchlist_type})")

            return {
                'success': True,
                'id': item_id,
                'message': f"{name} ajoute a la watchlist",
                'current_count': current_count + 1,
                'max_allowed': max_allowed
            }

        except Exception as e:
            logger.error(f"[WATCHLIST] Erreur ajout {symbol}: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def remove_from_watchlist(self, item_id: int) -> Dict[str, Any]:
        """
        Retire un element de la watchlist

        Args:
            item_id: ID de l'element

        Returns:
            Resultat
        """
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()

            cursor.execute("DELETE FROM economic_watchlist WHERE id = ?", (item_id,))
            conn.commit()

            deleted = cursor.rowcount > 0
            conn.close()

            if deleted:
                logger.info(f"[WATCHLIST] Suppression: ID {item_id}")
                return {
                    'success': True,
                    'message': 'Element retire de la watchlist'
                }
            else:
                return {
                    'success': False,
                    'error': 'Element non trouve'
                }

        except Exception as e:
            logger.error(f"[WATCHLIST] Erreur suppression {item_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def update_display_order(self, items_order: List[Dict[str, int]]) -> Dict[str, Any]:
        """
        Met a jour l'ordre d'affichage des elements

        Args:
            items_order: Liste de {id, order}

        Returns:
            Resultat
        """
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()

            for item in items_order:
                cursor.execute("""
                    UPDATE economic_watchlist
                    SET display_order = ?, updated_at = ?
                    WHERE id = ?
                """, (item['order'], datetime.now().isoformat(), item['id']))

            conn.commit()
            conn.close()

            logger.info(f"[WATCHLIST] Ordre mis a jour: {len(items_order)} elements")

            return {
                'success': True,
                'message': f'Ordre mis a jour pour {len(items_order)} elements'
            }

        except Exception as e:
            logger.error(f"[WATCHLIST] Erreur mise a jour ordre: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_watchlist_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques de la watchlist"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()

            # Compter par type
            cursor.execute("""
                SELECT watchlist_type, COUNT(*) as count
                FROM economic_watchlist
                WHERE enabled = 1
                GROUP BY watchlist_type
            """)

            counts = dict(cursor.fetchall())
            conn.close()

            indices_count = counts.get('index', 0)
            etf_count = counts.get('etf', 0)

            return {
                'indices': {
                    'count': indices_count,
                    'max': EconomicConfig.MAX_WATCHLIST_INDICES,
                    'remaining': EconomicConfig.MAX_WATCHLIST_INDICES - indices_count
                },
                'etfs': {
                    'count': etf_count,
                    'max': EconomicConfig.MAX_WATCHLIST_ETFS,
                    'remaining': EconomicConfig.MAX_WATCHLIST_ETFS - etf_count
                },
                'total': indices_count + etf_count
            }

        except Exception as e:
            logger.error(f"[WATCHLIST] Erreur stats: {e}")
            return {}

    def _count_watchlist(self, watchlist_type: str) -> int:
        """Compte les elements d'un type"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT COUNT(*) FROM economic_watchlist
                WHERE watchlist_type = ? AND enabled = 1
            """, (watchlist_type,))

            count = cursor.fetchone()[0]
            conn.close()
            return count

        except Exception as e:
            logger.error(f"[WATCHLIST] Erreur count: {e}")
            return 0

    def _get_price_data(
        self,
        symbol: str,
        name: str,
        watchlist_type: str,
        force_refresh: bool
    ) -> Optional[Dict[str, Any]]:
        """Recupere les donnees de prix pour un element de la watchlist"""
        if not self.yfinance:
            return None

        cache_key = f"watchlist_{symbol}"

        def fetch():
            try:
                result = self.yfinance.get_index_data(symbol)
                if result.get('success'):
                    return {
                        'value': result['current_price'],
                        'change_percent': result['change_percent'],
                        'trend': 'up' if result['change_percent'] > 0 else 'down'
                    }
            except Exception as e:
                logger.error(f"[WATCHLIST] Erreur prix {symbol}: {e}")
            return None

        return self.fetch_with_cache(
            cache_key=cache_key,
            fetch_func=fetch,
            data_source='yfinance',
            data_type='watchlist',
            expiry_hours=2,
            force_refresh=force_refresh
        )
