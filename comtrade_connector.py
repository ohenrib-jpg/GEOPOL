# Flask/comtrade_connector.py
"""
Connecteur pour UN Comtrade API
Source officielle des données de commerce international (Nations Unies)

API Documentation: https://comtradeapi.un.org/
Inscription gratuite: https://comtradeapi.un.org/

Avantages vs Eurostat:
- Couverture mondiale (tous les pays)
- Données très détaillées (codes HS à 6 chiffres)
- API stable et bien documentée
- Gratuit avec subscription (500 req/heure)
"""

import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import time

logger = logging.getLogger(__name__)


class ComtradeConnector:
    """
    Connecteur pour UN Comtrade API
    Récupère les données de commerce international
    """

    # API V1 (nouvelle version)
    BASE_URL = "https://comtradeapi.un.org/data/v1/get"

    # Limites API (gratuit)
    MAX_REQUESTS_PER_HOUR = 500
    REQUEST_DELAY = 1.0  # 1 seconde entre requêtes

    # Mapping des codes pays ISO vers Comtrade (codes numériques)
    # Source: https://comtradeapi.un.org/files/v1/app/reference/Reporters.json
    COUNTRY_CODES = {
        'EU27': '97',   # European Union (27 members)
        'EU': '97',     # Alias
        'USA': '842',   # USA (alias)
        'US': '842',    # USA
        'CHINA': '156', # China (alias)
        'CN': '156',    # China
        'JAPAN': '392', # Japan (alias)
        'JP': '392',    # Japan
        'FR': '251',    # France
        'DE': '276',    # Germany (Allemagne)
        'IT': '380',    # Italy (Italie)
        'ES': '724',    # Spain (Espagne)
        'UK': '826',    # United Kingdom
        'GB': '826',    # United Kingdom (alias)
        'IN': '699',    # India (Inde)
        'AU': '36',     # Australia (Australie)
        'BR': '76',     # Brazil (Brésil)
        'RU': '643',    # Russian Federation
        'CA': '124',    # Canada
        'KR': '410',    # Republic of Korea
        'MX': '484',    # Mexico (Mexique)
        'NL': '528',    # Netherlands (Pays-Bas)
        'PL': '616'     # Poland (Pologne)
    }

    # Mapping codes CN vers codes HS (Harmonized System)
    # Note: CN codes européens ~ HS codes internationaux à 6 chiffres
    CN_TO_HS_MAPPING = {
        '2805': '280530',  # Terres rares (Nd, Dy, Tb, Eu, La, Ce, Pr)
        '280530': '280530',
        '8112': '811292',  # Métaux stratégiques (Ga, Ge, In, Te)
        '811292': '811292',
        '811299': '811299',
        '280480': '280480',  # Arsenic
        '280490': '280490',  # Selenium
        '280519': '280519',  # Lithium
        '2804': '280461',  # Silicium
        '280461': '280461',
        '8542': '854231',  # Circuits intégrés
        '854231': '854231'
    }

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialise le connecteur Comtrade

        Args:
            api_key: Clé API Comtrade (optionnel pour accès public limité)
                    Inscription gratuite sur https://comtradeapi.un.org/
        """
        self.api_key = api_key
        self.session = requests.Session()

        # Headers
        headers = {
            'User-Agent': 'Geopol-Analytics/1.0',
            'Accept': 'application/json'
        }

        if self.api_key:
            headers['Ocp-Apim-Subscription-Key'] = self.api_key
            logger.info("[OK] Comtrade API initialisé avec clé API")
        else:
            logger.info("[WARN] Comtrade API initialisé sans clé (accès public limité)")

        self.session.headers.update(headers)

    def normalize_cn_to_hs(self, cn_code: str) -> str:
        """
        Normalise un code CN (Combined Nomenclature) vers un code HS à 6 chiffres.

        Règles:
        1. Si le code est dans le mapping explicite, utiliser ce mapping
        2. Si le code a 8 chiffres, prendre les 6 premiers (correspondance CN -> HS)
        3. Si le code a 6 chiffres, considérer que c'est déjà un code HS
        4. Sinon, retourner le code tel quel (peut nécessiter un mapping supplémentaire)
        """
        # Vérifier le mapping explicite
        if cn_code in self.CN_TO_HS_MAPPING:
            return self.CN_TO_HS_MAPPING[cn_code]

        # Normalisation automatique basée sur la longueur
        if len(cn_code) == 8:
            # Code CN 8 chiffres: les 6 premiers sont le code HS
            hs_code = cn_code[:6]
            logger.debug(f"Normalisation CN {cn_code} -> HS {hs_code} (8→6 chiffres)")
            return hs_code
        elif len(cn_code) == 6:
            # Déjà un code HS probable
            return cn_code
        else:
            # Autres longueurs: retourner tel quel (mapping peut être nécessaire)
            logger.warning(f"Code CN {cn_code} de longueur {len(cn_code)} non standard - mapping HS peut être nécessaire")
            return cn_code

    def get_trade_data(self,
                       reporter_code: str,
                       hs_code: str,
                       year: int = 2023,
                       flow_code: str = 'M',  # M=imports, X=exports
                       partner_code: str = '0') -> Optional[Dict[str, Any]]:
        """
        Récupère les données de commerce depuis Comtrade

        Args:
            reporter_code: Code numérique pays reporter (ex: '842' pour USA, '251' pour France)
            hs_code: Code HS à 6 chiffres (ex: '280530')
            year: Année (2000-2023)
            flow_code: 'M' (imports), 'X' (exports), ou 'all'
            partner_code: Code numérique pays partenaire ou '0' pour monde entier

        Returns:
            Dict avec données de commerce ou None
        """
        try:
            # Construire l'URL avec typeCode, freqCode, clCode dans le chemin
            url = f"{self.BASE_URL}/C/A/HS"  # C=Commodities, A=Annual, HS=Harmonized System

            # Paramètres de requête
            params = {
                'period': str(year),
                'reporterCode': reporter_code,
                'cmdCode': hs_code,
                'flowCode': flow_code,
                'partnerCode': partner_code,
                'motCode': '0',   # 0=All modes of transport
                'customsCode': 'C00',  # C00=All customs procedures
                'partner2Code': '0'
            }

            logger.info(f"[DATA] Comtrade: {reporter_code} - HS {hs_code} ({year})")

            # Respecter rate limit
            time.sleep(self.REQUEST_DELAY)

            # Requête API avec timeout réduit pour éviter blocage
            response = self.session.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return self._parse_response(data, reporter_code, hs_code, year)

            elif response.status_code == 401:
                logger.error("[ERROR] Comtrade: Authentification requise (clé API invalide)")
                return None

            elif response.status_code == 429:
                logger.error("[ERROR] Comtrade: Limite de requêtes atteinte (500/heure)")
                return None

            else:
                logger.warning(f"[WARN] Comtrade: Status {response.status_code}")
                return None

        except requests.Timeout:
            logger.error("[ERROR] Comtrade: Timeout")
            return None

        except Exception as e:
            logger.error(f"[ERROR] Comtrade error: {e}")
            return None

    def _parse_response(self, data: Dict, reporter_code: str, hs_code: str, year: int) -> Optional[Dict[str, Any]]:
        """Parse la réponse Comtrade"""
        try:
            # Vérifier si données présentes
            if 'data' not in data or not data['data']:
                logger.warning(f"[WARN] Pas de données Comtrade pour HS {hs_code}")
                return None

            # Agréger les données
            total_imports = 0
            total_exports = 0
            import_sources = {}

            for record in data['data']:
                flow = record.get('flowCode', '')
                value = record.get('primaryValue', 0) or 0  # Valeur en USD
                partner = record.get('partnerCode', 'unknown')

                if flow == 'M':  # Imports
                    total_imports += value
                    if partner != 'all' and partner != '0':
                        import_sources[partner] = import_sources.get(partner, 0) + value

                elif flow == 'X':  # Exports
                    total_exports += value

            # Convertir USD en tonnes (approximation si nécessaire)
            # Pour les matériaux stratégiques, on peut estimer le poids
            # Ici on garde les valeurs en USD pour cohérence

            total_trade = total_imports + total_exports
            dependency_ratio = (total_imports / total_trade * 100) if total_trade > 0 else 0

            # Vérifier fraîcheur des données
            data_date = f"{year}-12-31"
            freshness = self._check_freshness(data_date)

            result = {
                'success': True,
                'hs_code': hs_code,
                'reporter': reporter_code,
                'year': year,
                'imports': round(total_imports / 1000000, 2),  # Millions USD
                'exports': round(total_exports / 1000000, 2),  # Millions USD
                'trade_balance': round((total_exports - total_imports) / 1000000, 2),
                'import_sources': {k: round(v / 1000000, 2) for k, v in import_sources.items()},
                'dependency_ratio': round(dependency_ratio, 2),
                'unit': 'Millions USD',
                'source': f'UN Comtrade ({year})',
                'note': f'Données officielles Nations Unies - Commerce international {year}',
                'data_source': {
                    'type': 'real_api',
                    'api': 'UN Comtrade',
                    'dataset': f'HS{hs_code}',
                    'confidence': 'high',
                    'last_update': data_date,
                    'freshness': freshness
                }
            }

            logger.info(f"[OK] Comtrade {reporter_code} HS{hs_code}: Imports=${total_imports/1e6:.1f}M, Exports=${total_exports/1e6:.1f}M")

            return result

        except Exception as e:
            logger.error(f"[ERROR] Erreur parsing Comtrade: {e}")
            return None

    def _check_freshness(self, last_update_str: str) -> Dict[str, Any]:
        """Vérifie la fraîcheur des données (même logique qu'Eurostat)"""
        try:
            last_update = datetime.strptime(last_update_str, '%Y-%m-%d')
            now = datetime.now()
            age_days = (now - last_update).days

            MAX_AGE = 730  # 2 ans pour données annuelles
            WARN_AGE = 365  # 1 an

            if age_days > MAX_AGE:
                return {
                    'fresh': False,
                    'age_days': age_days,
                    'status': 'too_old',
                    'message': f'Données trop anciennes ({age_days} jours)'
                }
            elif age_days > WARN_AGE:
                return {
                    'fresh': True,
                    'age_days': age_days,
                    'status': 'warning',
                    'message': f'Données de {last_update.year} (à actualiser)'
                }
            else:
                return {
                    'fresh': True,
                    'age_days': age_days,
                    'status': 'ok',
                    'message': f'Données récentes ({last_update.year})'
                }
        except Exception as e:
            logger.error(f"Erreur vérification fraîcheur: {e}")
            return {
                'fresh': False,
                'age_days': 999,
                'status': 'error',
                'message': 'Erreur vérification'
            }

    def get_trade_by_cn(self, cn_code: str, region: str = 'EU27', year: int = 2023) -> Optional[Dict[str, Any]]:
        """
        Récupère les données de commerce pour un code CN (compatible avec Eurostat)

        Args:
            cn_code: Code CN à 2-8 chiffres
            region: Code région/pays (EU27, FR, US, CN, etc.)
            year: Année

        Returns:
            Dict avec imports/exports ou None
        """
        # Convertir CN vers HS
        hs_code = self.normalize_cn_to_hs(cn_code)

        # Convertir région vers code Comtrade
        reporter = self.COUNTRY_CODES.get(region.upper(), region)

        # Si EU27, on ne peut pas récupérer directement (pas de reporter "EU")
        # Solution: agréger les principaux pays EU
        if region.upper() == 'EU27':
            return self._get_eu27_aggregate(hs_code, year)

        # Récupérer imports et exports séparément
        imports_data = self.get_trade_data(reporter, hs_code, year, flow_code='M')
        exports_data = self.get_trade_data(reporter, hs_code, year, flow_code='X')

        if not imports_data and not exports_data:
            return None

        # Fusionner les résultats
        imports = imports_data['imports'] if imports_data else 0
        exports = exports_data['exports'] if exports_data else 0
        import_sources = imports_data.get('import_sources', {}) if imports_data else {}

        total_trade = imports + exports
        dependency_ratio = (imports / total_trade * 100) if total_trade > 0 else 0

        data_date = f"{year}-12-31"
        freshness = self._check_freshness(data_date)

        return {
            'success': True,
            'cn_code': cn_code,
            'hs_code': hs_code,
            'region': region,
            'year': year,
            'imports': imports,
            'exports': exports,
            'trade_balance': round(exports - imports, 2),
            'import_sources': import_sources,
            'dependency_ratio': round(dependency_ratio, 2),
            'unit': 'Millions USD',
            'source': f'UN Comtrade ({year})',
            'note': f'Données officielles Nations Unies - Commerce international {year}',
            'data_source': {
                'type': 'real_api',
                'api': 'UN Comtrade',
                'dataset': f'HS{hs_code}',
                'confidence': 'high',
                'last_update': data_date,
                'freshness': freshness
            }
        }

    def _get_eu27_aggregate(self, hs_code: str, year: int) -> Optional[Dict[str, Any]]:
        """Agrège les données des principaux pays EU27"""
        logger.info(f"[DATA] Agrégation EU27 pour HS {hs_code}")

        # Principaux pays EU (représentent ~80% du commerce EU) - codes numériques
        eu_countries = ['251', '276', '380', '724', '528', '616']  # FR, DE, IT, ES, NL, PL

        total_imports = 0
        total_exports = 0
        aggregated_sources = {}

        for country in eu_countries:
            try:
                data = self.get_trade_data(country, hs_code, year, flow_code='M')
                if data:
                    total_imports += data['imports']
                    # Agréger les sources
                    for partner, value in data.get('import_sources', {}).items():
                        aggregated_sources[partner] = aggregated_sources.get(partner, 0) + value

                data = self.get_trade_data(country, hs_code, year, flow_code='X')
                if data:
                    total_exports += data['exports']

                # Small delay entre pays
                time.sleep(0.5)

            except Exception as e:
                logger.warning(f"[WARN] Erreur agrégation {country}: {e}")
                continue

        if total_imports == 0 and total_exports == 0:
            logger.warning("[WARN] Pas de données EU27")
            return None

        total_trade = total_imports + total_exports
        dependency_ratio = (total_imports / total_trade * 100) if total_trade > 0 else 0

        data_date = f"{year}-12-31"
        freshness = self._check_freshness(data_date)

        return {
            'success': True,
            'hs_code': hs_code,
            'region': 'EU27',
            'year': year,
            'imports': round(total_imports, 2),
            'exports': round(total_exports, 2),
            'trade_balance': round(total_exports - total_imports, 2),
            'import_sources': aggregated_sources,
            'dependency_ratio': round(dependency_ratio, 2),
            'unit': 'Millions USD',
            'source': f'UN Comtrade ({year}) - Agrégation EU27',
            'note': f'Agrégation des principaux pays EU: {", ".join(eu_countries)}',
            'data_source': {
                'type': 'real_api',
                'api': 'UN Comtrade (EU27 aggregated)',
                'dataset': f'HS{hs_code}',
                'confidence': 'high',
                'last_update': data_date,
                'freshness': freshness
            }
        }

    def get_trade_balance(self, country: str, product_code: str, year: str) -> Dict[str, Any]:
        """
        Récupère les données de balance commerciale pour un pays et produit donné

        Args:
            country: Code pays (EU27, US, CN, JP, etc.)
            product_code: Code produit HS ou 'all' pour tous
            year: Année

        Returns:
            Dict avec données de balance commerciale
        """
        try:
            # Si product_code est 'all', on récupère plusieurs produits courants
            if product_code == 'all':
                # Produits stratégiques à surveiller
                strategic_products = {
                    '280530': 'Terres rares',
                    '280519': 'Lithium',
                    '854231': 'Circuits intégrés',
                    '270900': 'Pétrole'
                }

                results = {}
                for hs_code, name in strategic_products.items():
                    data = self.get_trade_by_cn(hs_code, country, int(year))
                    if data and data.get('success'):
                        results[hs_code] = {
                            'name': name,
                            'imports': data.get('imports', 0),
                            'exports': data.get('exports', 0),
                            'balance': data.get('trade_balance', 0),
                            'dependency_ratio': data.get('dependency_ratio', 0),
                            'unit': 'Millions USD'
                        }
                    else:
                        results[hs_code] = None

                return {
                    'success': True,
                    'country': country,
                    'year': year,
                    'products': results,
                    'source': 'UN Comtrade',
                    'note': 'Données agrégées pour produits stratégiques'
                }
            else:
                # Produit spécifique
                data = self.get_trade_by_cn(product_code, country, int(year))
                if data and data.get('success'):
                    return {
                        'success': True,
                        'country': country,
                        'year': year,
                        'product': {
                            'hs_code': product_code,
                            'name': data.get('name', f'HS {product_code}'),
                            'imports': data.get('imports', 0),
                            'exports': data.get('exports', 0),
                            'balance': data.get('trade_balance', 0),
                            'dependency_ratio': data.get('dependency_ratio', 0),
                            'unit': 'Millions USD'
                        },
                        'source': 'UN Comtrade'
                    }
                else:
                    return {
                        'success': False,
                        'error': f'Données non disponibles pour {product_code}',
                        'country': country,
                        'year': year
                    }

        except Exception as e:
            logger.error(f"[ERROR] Erreur balance commerciale {country}/{product_code}: {e}")
            return {
                'success': False,
                'error': str(e),
                'country': country,
                'year': year
            }

    def test_connection(self) -> bool:
        """Teste la connexion à l'API Comtrade"""
        try:
            logger.info("Test connexion UN Comtrade...")

            # Test simple: récupérer données USA, lithium, 2022
            result = self.get_trade_data('842', '280519', 2022, 'M')

            if result and result.get('success'):
                logger.info("[OK] Connexion Comtrade OK")
                return True
            else:
                logger.error("[ERROR] Connexion Comtrade échouée")
                return False

        except Exception as e:
            logger.error(f"[ERROR] Test Comtrade échoué: {e}")
            return False


# Export
__all__ = ['ComtradeConnector']


# Test si exécuté directement
if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    print("=" * 70)
    print("TEST UN COMTRADE API CONNECTOR")
    print("=" * 70)

    # Créer le connecteur (sans clé API pour test public)
    connector = ComtradeConnector()

    # Test 1: Connexion
    print("\n1. Test connexion...")
    if connector.test_connection():
        print("[OK] API accessible")
    else:
        print("[ERROR] API inaccessible")
        print("\nNote: Inscription gratuite sur https://comtradeapi.un.org/")
        print("Puis: connector = ComtradeConnector(api_key='VOTRE_CLE')")

    # Test 2: Données USA - Lithium
    print("\n2. Test données USA - Lithium (HS 280519)...")
    try:
        result = connector.get_trade_by_cn('280519', 'US', 2022)
        if result and result['success']:
            print(f"[OK] USA Lithium 2022:")
            print(f"   Imports: ${result['imports']}M USD")
            print(f"   Exports: ${result['exports']}M USD")
            print(f"   Dependency: {result['dependency_ratio']}%")
            print(f"   Source: {result['data_source']['api']}")
            print(f"   Fraîcheur: {result['data_source']['freshness']['message']}")
        else:
            print("[WARN] Pas de données")
    except Exception as e:
        print(f"[ERROR] Erreur: {e}")

    # Test 3: Données France - Terres rares
    print("\n3. Test données France - Terres rares (HS 280530)...")
    try:
        result = connector.get_trade_by_cn('2805', 'FR', 2022)
        if result and result['success']:
            print(f"[OK] France Terres rares 2022:")
            print(f"   Imports: ${result['imports']}M USD")
            print(f"   Exports: ${result['exports']}M USD")
            print(f"   Dependency: {result['dependency_ratio']}%")
        else:
            print("[WARN] Pas de données")
    except Exception as e:
        print(f"[ERROR] Erreur: {e}")

    print("\n" + "=" * 70)
    print("TESTS TERMINÉS")
    print("=" * 70)
    print("\n[IDEA] Pour utiliser pleinement l'API:")
    print("   1. Créer un compte sur https://comtradeapi.un.org/")
    print("   2. Obtenir une clé API (gratuit)")
    print("   3. connector = ComtradeConnector(api_key='VOTRE_CLE')")
