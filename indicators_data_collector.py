# Flask/indicators_data_collector.py
"""
Collecteur unifié pour le module Indicators
Orchestre toutes les sources de données:
- INSEE (scraping + API Melodi)
- Eurostat (API)
- yFinance (API)
- Google Finance (scraping backup)
"""

import logging
from datetime import datetime
from typing import Dict, Any
# MIGRATION: Utilise nouveau wrapper Eurostat au lieu de scraping INSEE lent
from insee_scraper import INSEEAPIWrapperMigrated as INSEEAPIWrapper
from eurostat_connector import EurostatConnector
from yfinance_connector import YFinanceConnector
from akshare_connector import akshare_connector
from google_finance_scraper import GoogleFinanceScraper

logger = logging.getLogger(__name__)


class IndicatorsDataCollector:
    """Collecteur unifié pour tous les indicateurs économiques"""

    def __init__(self):
        """Initialise tous les connecteurs"""
        try:
            self.insee_scraper = INSEEAPIWrapper()
            logger.info("[OK] INSEE scraper initialisé")
        except Exception as e:
            logger.error(f"[ERROR] Erreur init INSEE scraper: {e}")
            self.insee_scraper = None

        try:
            self.eurostat = EurostatConnector()
            logger.info("[OK] Eurostat connector initialisé")
        except Exception as e:
            logger.error(f"[ERROR] Erreur init Eurostat: {e}")
            self.eurostat = None

        try:
            self.yfinance = YFinanceConnector()
            logger.info("[OK] yFinance connector initialisé")
        except Exception as e:
            logger.error(f"[ERROR] Erreur init yFinance: {e}")
            self.yfinance = None

        try:
            self.akshare = akshare_connector
            logger.info("[OK] AKShare connector initialisé (marchés asiatiques)")
        except Exception as e:
            logger.error(f"[ERROR] Erreur init AKShare: {e}")
            self.akshare = None

        try:
            self.google_finance = GoogleFinanceScraper()
            logger.info("[OK] Google Finance scraper initialisé (backup)")
        except Exception as e:
            logger.error(f"[ERROR] Erreur init Google Finance: {e}")
            self.google_finance = None

        logger.info("[OK] Collecteur unifié indicators prêt")

    def get_france_indicators(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Récupère tous les indicateurs français
        Sources:
        - INSEE scraper: inflation, chômage, croissance (cache 24h)
        - Eurostat: PIB, balance commerciale, dette publique

        Args:
            force_refresh: Si True, force le rafraîchissement du cache
        """
        logger.info("[DATA] Récupération indicateurs France...")

        # 1. Récupérer données INSEE (inflation, chômage, croissance)
        insee_data = {}
        if self.insee_scraper:
            try:
                insee_result = self.insee_scraper.get_indicators(force_refresh=force_refresh)
                if insee_result.get('success'):
                    insee_data = insee_result.get('indicators', {})
                    logger.info(f"[OK] INSEE: {len(insee_data)} indicateurs récupérés")
                else:
                    logger.warning("[WARN] INSEE: pas de données disponibles")
            except Exception as e:
                logger.error(f"[ERROR] Erreur INSEE: {e}")

        # 2. Récupérer données Eurostat complémentaires
        eurostat_data = {}
        if self.eurostat:
            try:
                # PIB France
                gdp_result = self.eurostat.get_indicator_data('gdp', last_n=4)
                if gdp_result.get('success'):
                    eurostat_data['gdp'] = gdp_result

                # Balance commerciale
                trade_result = self.eurostat.get_indicator_data('trade_balance', last_n=12)
                if trade_result.get('success'):
                    eurostat_data['trade_balance'] = trade_result

                # Inflation HICP (si INSEE n'a pas réussi)
                if 'inflation' not in insee_data:
                    hicp_result = self.eurostat.get_indicator_data('hicp', last_n=12)
                    if hicp_result.get('success'):
                        eurostat_data['hicp'] = hicp_result

                # Chômage (si INSEE n'a pas réussi)
                if 'unemployment' not in insee_data:
                    unemployment_result = self.eurostat.get_indicator_data('unemployment', last_n=12)
                    if unemployment_result.get('success'):
                        eurostat_data['unemployment'] = unemployment_result

                logger.info(f"[OK] Eurostat: {len(eurostat_data)} indicateurs récupérés")
            except Exception as e:
                logger.error(f"[ERROR] Erreur Eurostat: {e}")

        # 3. Construire la réponse unifiée
        response = self._build_france_response(insee_data, eurostat_data)

        logger.info(f"[OK] France: {len(response.get('main_indicators', []))} indicateurs principaux")
        return response

    def _build_france_response(self, insee_data: Dict, eurostat_data: Dict) -> Dict[str, Any]:
        """Construit la réponse finale pour les indicateurs France"""

        # PIB (Eurostat)
        gdp_eurostat = eurostat_data.get('gdp', {})
        gdp_value = gdp_eurostat.get('current_value', 2800.5)
        gdp_change = gdp_eurostat.get('change_percent', 2.3)
        gdp_period = gdp_eurostat.get('period', '2024-Q3')
        gdp_source = gdp_eurostat.get('source', 'Données de référence')

        # Inflation (INSEE prioritaire, sinon Eurostat)
        if 'inflation' in insee_data:
            inflation_insee = insee_data['inflation']
            inflation_value = inflation_insee.get('value', 3.2)
            inflation_change = 0  # INSEE ne donne pas la variation
            inflation_period = inflation_insee.get('period', '2024-12')
            inflation_source = inflation_insee.get('source', 'INSEE')
        elif 'hicp' in eurostat_data:
            hicp_eurostat = eurostat_data['hicp']
            inflation_value = hicp_eurostat.get('current_value', 3.2)
            inflation_change = hicp_eurostat.get('change_percent', -0.5)
            inflation_period = hicp_eurostat.get('period', '2024-12')
            inflation_source = hicp_eurostat.get('source', 'Eurostat')
        else:
            inflation_value = 3.2
            inflation_change = -0.5
            inflation_period = '2024-12'
            inflation_source = 'Données de référence'

        # Chômage (INSEE prioritaire, sinon Eurostat)
        if 'unemployment' in insee_data:
            unemployment_insee = insee_data['unemployment']
            unemployment_value = unemployment_insee.get('value', 7.1)
            unemployment_change = 0
            unemployment_period = unemployment_insee.get('period', '2024-12')
            unemployment_source = unemployment_insee.get('source', 'INSEE')
        elif 'unemployment' in eurostat_data:
            unemployment_eurostat = eurostat_data['unemployment']
            unemployment_value = unemployment_eurostat.get('current_value', 7.1)
            unemployment_change = unemployment_eurostat.get('change_percent', -0.3)
            unemployment_period = unemployment_eurostat.get('period', '2024-12')
            unemployment_source = unemployment_eurostat.get('source', 'Eurostat')
        else:
            unemployment_value = 7.1
            unemployment_change = -0.3
            unemployment_period = '2024-12'
            unemployment_source = 'Données de référence'

        # Balance commerciale (Eurostat)
        trade_eurostat = eurostat_data.get('trade_balance', {})
        trade_value = trade_eurostat.get('current_value', -8.5)
        trade_change = trade_eurostat.get('change_percent', 1.2)
        trade_period = trade_eurostat.get('period', '2024-11')
        trade_source = trade_eurostat.get('source', 'Données de référence')

        # Convertir les périodes en format ISO
        def to_iso_date(period_str):
            """Convertit une période en date ISO"""
            try:
                # Format '2024-Q3' → '2024-09-30'
                if 'Q' in period_str:
                    year, quarter = period_str.split('-Q')
                    month = int(quarter) * 3
                    return f"{year}-{month:02d}-30"
                # Format '2024-12' → '2024-12-01'
                elif len(period_str) == 7 and '-' in period_str:
                    return f"{period_str}-01"
                # Format '2024' → '2024-01-01'
                elif len(period_str) == 4:
                    return f"{period_str}-01-01"
                # Déjà au bon format
                else:
                    return period_str
            except:
                return '2024-01-01'

        # Construction de la réponse
        response = {
            'success': True,
            'timestamp': datetime.now().isoformat(),

            # Indicateurs individuels
            'gdp': {
                'value': gdp_value,
                'variation': gdp_change,
                'period': gdp_period,
                'source': gdp_source
            },
            'inflation': {
                'value': inflation_value,
                'variation': inflation_change,
                'period': inflation_period,
                'source': inflation_source
            },
            'unemployment': {
                'value': unemployment_value,
                'variation': unemployment_change,
                'period': unemployment_period,
                'source': unemployment_source
            },
            'trade': {
                'value': trade_value,
                'variation': trade_change,
                'period': trade_period,
                'source': trade_source
            },

            # Indicateurs additionnels (fallback pour l'instant)
            'public_debt': {
                'value': 112.5,
                'variation': 2.1,
                'period': '2024-Q3',
                'source': 'Données de référence'
            },
            'deficit': {
                'value': -4.8,
                'variation': -0.3,
                'period': '2024',
                'source': 'Données de référence'
            },
            'consumer_confidence': {
                'value': 95,
                'variation': 2,
                'period': '2024-12',
                'source': 'Données de référence'
            },

            # Format pour le tableau principal
            'main_indicators': [
                {
                    'name': 'PIB',
                    'value': gdp_value,
                    'unit': 'Md€',
                    'variation': gdp_change,
                    'period': to_iso_date(gdp_period),
                    'source': gdp_source
                },
                {
                    'name': 'Inflation (IPCH)',
                    'value': inflation_value,
                    'unit': '%',
                    'variation': inflation_change,
                    'period': to_iso_date(inflation_period),
                    'source': inflation_source
                },
                {
                    'name': 'Chômage',
                    'value': unemployment_value,
                    'unit': '%',
                    'variation': unemployment_change,
                    'period': to_iso_date(unemployment_period),
                    'source': unemployment_source
                },
                {
                    'name': 'Balance Commerciale',
                    'value': trade_value,
                    'unit': 'Md€',
                    'variation': trade_change,
                    'period': to_iso_date(trade_period),
                    'source': trade_source
                }
            ],

            # Indicateurs détaillés
            'detailed_indicators': [
                {
                    'name': 'Dette Publique',
                    'value': 112.5,
                    'unit': '% PIB',
                    'variation': 2.1,
                    'period': '2024-09-30',
                    'source': 'Données de référence'
                },
                {
                    'name': 'Déficit Public',
                    'value': -4.8,
                    'unit': '% PIB',
                    'variation': -0.3,
                    'period': '2024-01-01',
                    'source': 'Données de référence'
                },
                {
                    'name': 'Confiance Consommateurs',
                    'value': 95,
                    'unit': 'pts',
                    'variation': 2,
                    'period': '2024-12-01',
                    'source': 'Données de référence'
                }
            ],

            # Métadonnées sur les sources
            'data_sources': {
                'insee': len(insee_data) > 0,
                'eurostat': len(eurostat_data) > 0,
                'insee_indicators': list(insee_data.keys()) if insee_data else [],
                'eurostat_indicators': list(eurostat_data.keys()) if eurostat_data else []
            }
        }

        return response

    def get_international_indicators(self) -> Dict[str, Any]:
        """
        Récupère les indicateurs internationaux
        Pour l'instant: données de référence
        TODO: Implémenter avec Eurostat pour pays européens
        """
        logger.info("[GLOBAL] Récupération indicateurs internationaux...")

        # TODO: Utiliser Eurostat pour récupérer données pays européens
        # Pour l'instant, retourner des données de référence

        response = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'regions': [
                {
                    'name': 'Zone Euro',
                    'gdp': 14500.0,
                    'growth': 1.5,
                    'countries_count': 20
                },
                {
                    'name': 'Union Européenne',
                    'gdp': 17000.0,
                    'growth': 1.7,
                    'countries_count': 27
                },
                {
                    'name': 'Amérique du Nord',
                    'gdp': 25000.0,
                    'growth': 2.5,
                    'countries_count': 3
                }
            ],
            'countries': [
                {
                    'name': 'France',
                    'gdp': 2800.5,
                    'growth': 2.3,
                    'inflation': 3.2,
                    'unemployment': 7.1
                },
                {
                    'name': 'Allemagne',
                    'gdp': 4200.0,
                    'growth': 1.8,
                    'inflation': 2.8,
                    'unemployment': 5.5
                },
                {
                    'name': 'Italie',
                    'gdp': 2100.0,
                    'growth': 1.2,
                    'inflation': 3.5,
                    'unemployment': 8.2
                },
                {
                    'name': 'Espagne',
                    'gdp': 1450.0,
                    'growth': 2.5,
                    'inflation': 3.1,
                    'unemployment': 11.5
                },
                {
                    'name': 'États-Unis',
                    'gdp': 25000.0,
                    'growth': 2.8,
                    'inflation': 3.7,
                    'unemployment': 3.9
                }
            ],
            'data_sources': {
                'eurostat': False,
                'world_bank': False,
                'note': 'Données de référence - implémentation API en cours'
            }
        }

        return response

    def get_markets_indicators(self, period: str = '6mo') -> Dict[str, Any]:
        """
        Récupère les indicateurs des marchés financiers
        Sources:
        - yFinance: indices boursiers (temps réel)
        - Google Finance scraping: backup
        """
        logger.info(f"[CHART] Récupération marchés financiers (période: {period})...")

        markets_data = {}
        use_fallback = False

        if self.yfinance:
            try:
                # CAC 40 avec historique
                logger.info("Tentative récupération CAC 40...")
                cac40_current = self.yfinance.get_index_data('^FCHI')

                if cac40_current.get('success'):
                    logger.info(f"[OK] CAC 40: {cac40_current.get('current_price')} ({cac40_current.get('change_percent'):+.2f}%)")

                    markets_data['cac40'] = {
                        'value': cac40_current.get('current_price', 7523.45),
                        'variation': cac40_current.get('change_percent', 1.25),
                        'source': cac40_current.get('source', 'Yahoo Finance'),
                        'history': []
                    }

                    # Ajouter l'historique si disponible
                    logger.info(f"Tentative récupération historique CAC 40 ({period})...")
                    cac40_history = self.yfinance.get_historical_data('^FCHI', period=period)

                    if cac40_history.get('success') and cac40_history.get('data'):
                        markets_data['cac40']['history'] = [
                            {
                                'date': item['date'],
                                'close': item['close']
                            }
                            for item in cac40_history.get('data', [])
                        ]
                        logger.info(f"[OK] Historique CAC 40: {len(markets_data['cac40']['history'])} points")
                    else:
                        logger.warning("[WARN] Pas d'historique pour CAC 40")
                else:
                    logger.warning(f"[WARN] Échec CAC 40: {cac40_current.get('error', 'Erreur inconnue')}")
                    use_fallback = True

                # Dow Jones
                logger.info("Tentative récupération Dow Jones...")
                dow_data = self.yfinance.get_index_data('^DJI')
                if dow_data.get('success'):
                    markets_data['dow'] = {
                        'value': dow_data.get('current_price', 37800.50),
                        'variation': dow_data.get('change_percent', 0.85),
                        'source': dow_data.get('source', 'Yahoo Finance')
                    }
                    logger.info(f"[OK] Dow Jones: {dow_data.get('current_price')}")
                else:
                    logger.warning(f"[WARN] Échec Dow Jones: {dow_data.get('error', 'Erreur inconnue')}")

                # S&P 500
                logger.info("Tentative récupération S&P 500...")
                sp500_data = self.yfinance.get_index_data('^GSPC')
                if sp500_data.get('success'):
                    markets_data['sp500'] = {
                        'value': sp500_data.get('current_price', 4750.30),
                        'variation': sp500_data.get('change_percent', 0.95),
                        'source': sp500_data.get('source', 'Yahoo Finance')
                    }
                    logger.info(f"[OK] S&P 500: {sp500_data.get('current_price')}")
                else:
                    logger.warning(f"[WARN] Échec S&P 500: {sp500_data.get('error', 'Erreur inconnue')}")

                # DAX
                logger.info("Tentative récupération DAX...")
                dax_data = self.yfinance.get_index_data('^GDAXI')
                if dax_data.get('success'):
                    markets_data['dax'] = {
                        'value': dax_data.get('current_price', 16900.20),
                        'variation': dax_data.get('change_percent', 1.15),
                        'source': dax_data.get('source', 'Yahoo Finance')
                    }
                    logger.info(f"[OK] DAX: {dax_data.get('current_price')}")
                else:
                    logger.warning(f"[WARN] Échec DAX: {dax_data.get('error', 'Erreur inconnue')}")

                if markets_data:
                    logger.info(f"[OK] yFinance: {len(markets_data)} indices récupérés")
                else:
                    logger.warning("[WARN] Aucun indice récupéré via yFinance")
                    use_fallback = True

            except Exception as e:
                logger.error(f"[ERROR] Erreur yFinance marchés: {e}")
                use_fallback = True

        # Indices asiatiques via AKShare (marchés complémentaires)
        asian_markets_data = {}
        if self.akshare:
            try:
                logger.info("[AKSHARE] Récupération indices asiatiques...")

                # Récupérer les principaux indices asiatiques
                asian_symbols = ['sh000001', 'hsi']  # Shanghai Composite et Hang Seng
                asian_results = self.akshare.get_multiple_indices(asian_symbols)

                for symbol, data in asian_results.items():
                    if data.get('success'):
                        # Mapper les symboles à des noms plus lisibles
                        market_key = 'shanghai' if symbol == 'sh000001' else 'hang_seng'
                        asian_markets_data[market_key] = {
                            'value': data.get('current_price'),
                            'variation': data.get('change_percent'),
                            'source': data.get('source', 'AKShare'),
                            'symbol': symbol,
                            'name': data.get('name', '')
                        }
                        logger.info(f"[OK] AKShare {symbol}: {data.get('current_price')} ({data.get('change_percent'):+.2f}%)")
                    else:
                        logger.warning(f"[WARN] AKShare {symbol}: {data.get('error', 'Erreur inconnue')}")

                if asian_markets_data:
                    logger.info(f"[OK] AKShare: {len(asian_markets_data)} indices asiatiques récupérés")
                    # Fusionner avec les données principales
                    markets_data.update(asian_markets_data)
                else:
                    logger.warning("[WARN] AKShare: aucun indice asiatique récupéré")

            except Exception as e:
                logger.error(f"[ERROR] Erreur AKShare marchés asiatiques: {e}")

        # Fallback Google Finance si yFinance échoue
        if (use_fallback or not markets_data) and self.google_finance:
            logger.info("[MIGRATION] Tentative Google Finance (backup)...")
            try:
                # CAC 40
                cac40_gf = self.google_finance.get_index_data('^FCHI')
                if cac40_gf.get('success'):
                    markets_data['cac40'] = {
                        'value': cac40_gf.get('current_price'),
                        'variation': cac40_gf.get('change_percent'),
                        'source': cac40_gf.get('source'),
                        'history': []  # Pas d'historique avec scraping
                    }

                # Dow Jones
                dow_gf = self.google_finance.get_index_data('^DJI')
                if dow_gf.get('success'):
                    markets_data['dow'] = {
                        'value': dow_gf.get('current_price'),
                        'variation': dow_gf.get('change_percent'),
                        'source': dow_gf.get('source')
                    }

                # S&P 500
                sp500_gf = self.google_finance.get_index_data('^GSPC')
                if sp500_gf.get('success'):
                    markets_data['sp500'] = {
                        'value': sp500_gf.get('current_price'),
                        'variation': sp500_gf.get('change_percent'),
                        'source': sp500_gf.get('source')
                    }

                # DAX
                dax_gf = self.google_finance.get_index_data('^GDAXI')
                if dax_gf.get('success'):
                    markets_data['dax'] = {
                        'value': dax_gf.get('current_price'),
                        'variation': dax_gf.get('change_percent'),
                        'source': dax_gf.get('source')
                    }

                if markets_data:
                    logger.info(f"[OK] Google Finance: {len(markets_data)} indices récupérés")
                    use_fallback = False  # Succès avec Google Finance
                else:
                    logger.warning("[WARN] Google Finance n'a pu récupérer aucun indice")

            except Exception as e:
                logger.error(f"[ERROR] Erreur Google Finance: {e}")

        # Fallback si pas de données ou erreur
        if use_fallback or not markets_data or len(markets_data) == 0:
            logger.warning("[WARN] Utilisation données fallback pour les marchés")
            markets_data = {
                'cac40': {
                    'value': 7523.45,
                    'variation': 1.25,
                    'source': 'Données de référence',
                    'history': []
                },
                'dow': {
                    'value': 37800.50,
                    'variation': 0.85,
                    'source': 'Données de référence'
                },
                'sp500': {
                    'value': 4750.30,
                    'variation': 0.95,
                    'source': 'Données de référence'
                },
                'dax': {
                    'value': 16900.20,
                    'variation': 1.15,
                    'source': 'Données de référence'
                }
            }

        # Déterminer quelles sources ont été utilisées
        yfinance_used = any('Yahoo Finance' in str(m.get('source', '')) for m in markets_data.values() if isinstance(m, dict))
        google_finance_used = any('Google Finance' in str(m.get('source', '')) for m in markets_data.values() if isinstance(m, dict))
        akshare_used = any('AKShare' in str(m.get('source', '')) for m in markets_data.values() if isinstance(m, dict))

        response = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            **markets_data,
            'data_sources': {
                'yfinance': yfinance_used,
                'google_finance': google_finance_used,
                'akshare': akshare_used,
                'fallback': use_fallback and not google_finance_used,
                'indices_count': len(markets_data)
            }
        }

        return response


# Instance globale (singleton)
_collector_instance = None

def get_collector() -> IndicatorsDataCollector:
    """Retourne l'instance singleton du collecteur"""
    global _collector_instance
    if _collector_instance is None:
        _collector_instance = IndicatorsDataCollector()
    return _collector_instance


# Test
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    collector = get_collector()

    print("\n" + "="*60)
    print("TEST COLLECTEUR INDICATORS")
    print("="*60)

    # Test France
    print("\n[DATA] Test indicateurs France...")
    france_data = collector.get_france_indicators()
    if france_data.get('success'):
        print(f"[OK] {len(france_data.get('main_indicators', []))} indicateurs principaux")
        for ind in france_data.get('main_indicators', []):
            print(f"   • {ind['name']}: {ind['value']} {ind['unit']} ({ind['source']})")

    # Test International
    print("\n[GLOBAL] Test indicateurs internationaux...")
    intl_data = collector.get_international_indicators()
    if intl_data.get('success'):
        print(f"[OK] {len(intl_data.get('countries', []))} pays")

    # Test Marchés
    print("\n[CHART] Test marchés financiers...")
    markets_data = collector.get_markets_indicators()
    if markets_data.get('success'):
        print(f"[OK] {markets_data.get('data_sources', {}).get('indices_count', 0)} indices")
        if 'cac40' in markets_data:
            cac40 = markets_data['cac40']
            print(f"   • CAC 40: {cac40.get('value')} ({cac40.get('variation'):+.2f}%)")

    print("\n" + "="*60)
    print("[OK] Tests terminés")
    print("="*60 + "\n")
