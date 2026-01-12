"""
Service pour les commodites strategiques
Sources: yFinance (primaire), Alpha Vantage (renfort)
"""
import logging
from typing import Dict, List, Optional, Any

from .base_service import BaseEconomicService
from ..config import EconomicConfig

logger = logging.getLogger(__name__)

class CommodityService(BaseEconomicService):
    """Service pour les commodites et matieres premieres strategiques"""

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
                logger.warning("[COMMODITY] yFinance connector non disponible")
                self.yfinance = None

        # Import Alpha Vantage connector
        try:
            from Flask.fluxStrategiques.indicators.alpha_vantage_connector import AlphaVantageConnector
            self.alpha_vantage = AlphaVantageConnector()
            if self.alpha_vantage.api_key:
                logger.info("[COMMODITY] Alpha Vantage connector disponible en renfort")
            else:
                logger.warning("[COMMODITY] Alpha Vantage: cle API manquante")
                self.alpha_vantage = None
        except ImportError:
            logger.warning("[COMMODITY] Alpha Vantage connector non disponible")
            self.alpha_vantage = None

    def get_all_commodities(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Recupere toutes les commodites strategiques

        Args:
            force_refresh: Forcer rafraichissement

        Returns:
            Liste des commodites
        """
        commodities = []

        # Metaux precieux
        precious_metals = self.get_precious_metals(force_refresh)
        commodities.extend(precious_metals)

        # Energie
        energy = self.get_energy_commodities(force_refresh)
        commodities.extend(energy)

        # Metaux industriels
        industrial = self.get_industrial_metals(force_refresh)
        commodities.extend(industrial)

        # ETFs matieres strategiques
        strategic_etfs = self.get_strategic_material_etfs(force_refresh)
        commodities.extend(strategic_etfs)

        return commodities

    def get_precious_metals(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Recupere les metaux precieux (Or, Argent, Platine, Palladium)"""
        metals = []

        precious = [
            ('GC=F', 'Or', 'USD/oz'),
            ('SI=F', 'Argent', 'USD/oz'),
            ('PL=F', 'Platine', 'USD/oz'),
            ('PA=F', 'Palladium', 'USD/oz')
        ]

        for symbol, name, unit in precious:
            commodity = self._get_commodity_yfinance(
                symbol, name, unit, 'metaux_precieux', force_refresh
            )
            if commodity:
                metals.append(commodity)

        return metals

    def get_energy_commodities(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Recupere les commodites energetiques"""
        energy = []

        # Essayer d'abord yFinance
        energy_list = [
            ('CL=F', 'Petrole WTI', 'USD/barrel'),
            ('BZ=F', 'Petrole Brent', 'USD/barrel'),
            ('NG=F', 'Gaz naturel', 'USD/MMBtu')
        ]

        for symbol, name, unit in energy_list:
            commodity = self._get_commodity_yfinance(
                symbol, name, unit, 'energie', force_refresh
            )
            if commodity:
                energy.append(commodity)

        # Renfort Alpha Vantage si disponible
        if self.alpha_vantage and self.alpha_vantage.api_key:
            # WTI depuis Alpha Vantage (si yFinance a echoue)
            if not any(c['name'] == 'Petrole WTI' for c in energy):
                wti_av = self._get_commodity_alpha_vantage('WTI', 'Petrole WTI', force_refresh)
                if wti_av:
                    energy.append(wti_av)

            # Brent depuis Alpha Vantage
            if not any(c['name'] == 'Petrole Brent' for c in energy):
                brent_av = self._get_commodity_alpha_vantage('BRENT', 'Petrole Brent', force_refresh)
                if brent_av:
                    energy.append(brent_av)

            # Gaz naturel depuis Alpha Vantage
            if not any(c['name'] == 'Gaz naturel' for c in energy):
                gas_av = self._get_commodity_alpha_vantage('NATURAL_GAS', 'Gaz naturel', force_refresh)
                if gas_av:
                    energy.append(gas_av)

        return energy

    def get_industrial_metals(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Recupere les metaux industriels"""
        metals = []

        industrial = [
            ('HG=F', 'Cuivre', 'USD/lb'),
            ('NI=F', 'Nickel', 'USD/lb')
        ]

        for symbol, name, unit in industrial:
            commodity = self._get_commodity_yfinance(
                symbol, name, unit, 'metaux_industriels', force_refresh
            )
            if commodity:
                metals.append(commodity)

        # Renfort Alpha Vantage pour le cuivre et aluminium
        if self.alpha_vantage and self.alpha_vantage.api_key:
            # Cuivre
            if not any(c['name'] == 'Cuivre' for c in metals):
                copper_av = self._get_commodity_alpha_vantage('COPPER', 'Cuivre', force_refresh)
                if copper_av:
                    metals.append(copper_av)

            # Aluminium (disponible uniquement via Alpha Vantage)
            aluminum_av = self._get_commodity_alpha_vantage('ALUMINUM', 'Aluminium', force_refresh)
            if aluminum_av:
                metals.append(aluminum_av)

        return metals

    def get_strategic_material_etfs(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Recupere les ETFs de materiaux strategiques (Lithium, Terres rares)"""
        etfs = []

        strategic_etfs = [
            ('LIT', 'Lithium ETF', 'USD'),
            ('REMX', 'Terres rares ETF', 'USD')
        ]

        for symbol, name, unit in strategic_etfs:
            commodity = self._get_commodity_yfinance(
                symbol, name, unit, 'etf_strategique', force_refresh
            )
            if commodity:
                etfs.append(commodity)

        # Renfort Alpha Vantage pour ETFs supplementaires
        if self.alpha_vantage and self.alpha_vantage.api_key:
            # Uranium ETF
            ura = self._get_etf_alpha_vantage('URA', 'Uranium ETF', force_refresh)
            if ura:
                etfs.append(ura)

        return etfs

    def get_agricultural_commodities(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Recupere les commodites agricoles
        Uniquement disponibles via Alpha Vantage
        """
        if not self.alpha_vantage or not self.alpha_vantage.api_key:
            logger.warning("[COMMODITY] Alpha Vantage requis pour commodites agricoles")
            return []

        agricultural = []

        crops = [
            ('WHEAT', 'Ble'),
            ('CORN', 'Mais'),
            ('COTTON', 'Coton'),
            ('SUGAR', 'Sucre'),
            ('COFFEE', 'Cafe')
        ]

        for symbol, name in crops:
            commodity = self._get_commodity_alpha_vantage(symbol, name, force_refresh)
            if commodity:
                agricultural.append(commodity)

        return agricultural

    def _get_commodity_yfinance(
        self,
        symbol: str,
        name: str,
        unit: str,
        category: str,
        force_refresh: bool
    ) -> Optional[Dict[str, Any]]:
        """Recupere une commodite via yFinance"""
        if not self.yfinance:
            return None

        cache_key = f"commodity_yf_{symbol}"

        def fetch():
            try:
                result = self.yfinance.get_commodity_data(symbol)
                if result.get('success'):
                    return {
                        'name': name,
                        'symbol': symbol,
                        'value': result['current_price'],
                        'change_percent': result['change_percent'],
                        'unit': unit,
                        'category': category
                    }
            except Exception as e:
                logger.error(f"[COMMODITY] Erreur yFinance {symbol}: {e}")
            return None

        return self.fetch_with_cache(
            cache_key=cache_key,
            fetch_func=fetch,
            data_source='yfinance',
            data_type='commodity',
            expiry_hours=2,
            force_refresh=force_refresh
        )

    def _get_commodity_alpha_vantage(
        self,
        symbol: str,
        name: str,
        force_refresh: bool
    ) -> Optional[Dict[str, Any]]:
        """Recupere une commodite via Alpha Vantage"""
        if not self.alpha_vantage or not self.alpha_vantage.api_key:
            return None

        cache_key = f"commodity_av_{symbol}"

        def fetch():
            try:
                result = self.alpha_vantage.get_commodity_price(symbol, interval='monthly')
                if result and 'error' not in result:
                    # Calculer variation si possible
                    change_percent = None
                    if len(result.get('history', [])) >= 2:
                        current = float(result['history'][0]['value'])
                        previous = float(result['history'][1]['value'])
                        change_percent = ((current - previous) / previous) * 100

                    return {
                        'name': name,
                        'symbol': symbol,
                        'value': result['latest_value'],
                        'change_percent': change_percent,
                        'unit': result.get('unit', 'USD'),
                        'category': 'alpha_vantage',
                        'date': result['latest_date']
                    }
            except Exception as e:
                logger.error(f"[COMMODITY] Erreur Alpha Vantage {symbol}: {e}")
            return None

        return self.fetch_with_cache(
            cache_key=cache_key,
            fetch_func=fetch,
            data_source='alpha_vantage',
            data_type='commodity',
            expiry_hours=4,
            force_refresh=force_refresh
        )

    def _get_etf_alpha_vantage(
        self,
        symbol: str,
        name: str,
        force_refresh: bool
    ) -> Optional[Dict[str, Any]]:
        """Recupere un ETF via Alpha Vantage"""
        if not self.alpha_vantage or not self.alpha_vantage.api_key:
            return None

        cache_key = f"etf_av_{symbol}"

        def fetch():
            try:
                result = self.alpha_vantage.get_etf_quote(symbol)
                if result and 'error' not in result:
                    # Extraire le pourcentage de change_percent
                    change_pct = result.get('change_percent', '0%').replace('%', '')
                    try:
                        change_pct = float(change_pct)
                    except:
                        change_pct = None

                    return {
                        'name': name,
                        'symbol': symbol,
                        'value': result['price'],
                        'change_percent': change_pct,
                        'unit': 'USD',
                        'category': 'etf_strategique'
                    }
            except Exception as e:
                logger.error(f"[COMMODITY] Erreur Alpha Vantage ETF {symbol}: {e}")
            return None

        return self.fetch_with_cache(
            cache_key=cache_key,
            fetch_func=fetch,
            data_source='alpha_vantage',
            data_type='etf',
            expiry_hours=4,
            force_refresh=force_refresh
        )
