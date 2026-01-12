# Flask/google_finance_scraper.py
"""
Scraper léger Google Finance comme backup pour yFinance
Scrape uniquement les prix actuels et variations, pas d'historique
"""

import logging
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional
import re

logger = logging.getLogger(__name__)


class GoogleFinanceScraper:
    """Scraper Google Finance pour indices boursiers (backup yFinance)"""

    BASE_URL = "https://www.google.com/finance/quote"

    # Mapping symboles yFinance → Google Finance
    SYMBOL_MAPPING = {
        '^FCHI': 'CAC:INDEXEURO',      # CAC 40
        '^DJI': 'DJI:INDEXDJX',         # Dow Jones
        '^GSPC': 'SPX:INDEXSP',         # S&P 500
        '^GDAXI': 'DAX:INDEXDB',        # DAX
        '^FTSE': 'UKX:INDEXFTSE',       # FTSE 100
        '^IXIC': 'IXIC:INDEXNASDAQ',    # NASDAQ
        '^N225': 'NI225:INDEXNIKKEI',   # Nikkei
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        logger.info("[OK] GoogleFinanceScraper initialisé")

    def get_index_data(self, yf_symbol: str) -> Dict[str, Any]:
        """
        Récupère les données d'un indice depuis Google Finance

        Args:
            yf_symbol: Symbole yFinance (ex: '^FCHI')

        Returns:
            Dict avec success, current_price, change_percent
        """
        if yf_symbol not in self.SYMBOL_MAPPING:
            return {
                'success': False,
                'error': f'Symbole {yf_symbol} non supporté par Google Finance scraper'
            }

        gf_symbol = self.SYMBOL_MAPPING[yf_symbol]

        try:
            # Construire l'URL Google Finance
            url = f"{self.BASE_URL}/{gf_symbol}"

            logger.info(f"📡 Scraping Google Finance: {url}")

            response = self.session.get(url, timeout=10)

            if response.status_code != 200:
                logger.warning(f"[WARN] Google Finance retourné status {response.status_code}")
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}'
                }

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extraire le prix actuel
            price_div = soup.find('div', class_=re.compile(r'YMlKec.*'))
            if not price_div:
                logger.warning("[WARN] Prix non trouvé dans la page Google Finance")
                return {
                    'success': False,
                    'error': 'Prix non trouvé'
                }

            price_text = price_div.text.strip()
            # Nettoyer le prix (enlever espaces, virgules)
            price_clean = price_text.replace(',', '').replace(' ', '')
            current_price = float(price_clean)

            # Extraire la variation
            variation_div = soup.find('div', class_=re.compile(r'JwB6zf.*'))
            variation_percent = 0.0

            if variation_div:
                variation_text = variation_div.text.strip()
                # Format: "+1.25%" ou "-0.85%"
                variation_match = re.search(r'([+-]?\d+\.?\d*)%', variation_text)
                if variation_match:
                    variation_percent = float(variation_match.group(1))

            logger.info(f"[OK] Google Finance {yf_symbol}: {current_price} ({variation_percent:+.2f}%)")

            return {
                'success': True,
                'symbol': yf_symbol,
                'current_price': round(current_price, 2),
                'change_percent': round(variation_percent, 2),
                'trend': 'up' if variation_percent > 0 else 'down',
                'source': 'Google Finance (scraping)',
                'data_source': {
                    'type': 'scraping',
                    'api': 'Google Finance',
                    'confidence': 'medium',
                    'note': 'Données scrapées depuis Google Finance'
                }
            }

        except Exception as e:
            logger.error(f"[ERROR] Erreur scraping Google Finance {yf_symbol}: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_all_indices(self) -> Dict[str, Any]:
        """Récupère tous les indices supportés"""
        results = {}

        for yf_symbol in self.SYMBOL_MAPPING.keys():
            data = self.get_index_data(yf_symbol)
            if data.get('success'):
                results[yf_symbol] = data

        return {
            'success': len(results) > 0,
            'indices': results,
            'stats': {
                'total': len(self.SYMBOL_MAPPING),
                'successful': len(results),
                'failed': len(self.SYMBOL_MAPPING) - len(results)
            }
        }


# Test
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    scraper = GoogleFinanceScraper()

    print("\n" + "="*60)
    print("TEST GOOGLE FINANCE SCRAPER")
    print("="*60)

    # Test CAC 40
    print("\n[DATA] Test CAC 40...")
    cac40 = scraper.get_index_data('^FCHI')
    if cac40.get('success'):
        print(f"[OK] CAC 40: {cac40.get('current_price')} ({cac40.get('change_percent'):+.2f}%)")
        print(f"   Source: {cac40.get('source')}")
    else:
        print(f"[ERROR] Échec: {cac40.get('error')}")

    # Test Dow Jones
    print("\n[DATA] Test Dow Jones...")
    dow = scraper.get_index_data('^DJI')
    if dow.get('success'):
        print(f"[OK] Dow Jones: {dow.get('current_price')} ({dow.get('change_percent'):+.2f}%)")
    else:
        print(f"[ERROR] Échec: {dow.get('error')}")

    print("\n" + "="*60)
    print("[OK] Tests terminés")
    print("="*60 + "\n")
