# Flask/geopol_data/connectors/world_bank.py
"""
Connecteur pour l'API World Bank
Récupération des indicateurs économiques, démographiques et environnementaux
Documentation: https://datahelpdesk.worldbank.org/knowledgebase/articles/889392
"""

import requests
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

# Import avec gestion d'erreur pour exécution standalone
try:
    from ..config import Config
    from ..constants import CORE_INDICATORS, WORLD_BANK_INDICATORS
except ImportError:
    # Si imports relatifs échouent (exécution standalone)
    import sys
    from pathlib import Path
    
    # Ajouter le dossier parent au path
    parent_dir = Path(__file__).parent.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))
    
    from geopol_data.config import Config
    from geopol_data.constants import CORE_INDICATORS, WORLD_BANK_INDICATORS

logger = logging.getLogger(__name__)

# ============================================================================
# CLASSE PRINCIPALE : WORLD BANK CONNECTOR
# ============================================================================

class WorldBankConnector:
    """
    Connecteur pour l'API World Bank v2
    Gère les requêtes HTTP, retry, timeout et parsing
    """
    
    def __init__(self):
        self.base_url = Config.world_bank.BASE_URL
        self.timeout = Config.world_bank.TIMEOUT
        self.max_retries = Config.world_bank.MAX_RETRIES
        self.default_params = Config.world_bank.DEFAULT_PARAMS.copy()
        
        # Session HTTP réutilisable
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'GEOPOL-Analytics/1.0',
            'Accept': 'application/json'
        })
        
        logger.info("WorldBankConnector initialisé")
    
    # ========================================================================
    # MÉTHODE PRINCIPALE : Fetch Indicators
    # ========================================================================
    
    def fetch_indicators(self, country_code: str, 
                        indicators: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Récupère les indicateurs pour un pays
        
        Args:
            country_code: Code ISO Alpha-2 du pays (ex: 'FR', 'US')
            indicators: Liste des codes d'indicateurs (ex: ['NY.GDP.MKTP.CD'])
                       Si None, utilise CORE_INDICATORS
        
        Returns:
            Liste de dictionnaires avec les données, format:
            [
                {
                    'indicator': {'id': 'NY.GDP.MKTP.CD', 'value': 'PIB'},
                    'country': {'id': 'FR', 'value': 'France'},
                    'value': 2780000000000,
                    'date': '2022'
                },
                ...
            ]
        
        Raises:
            WorldBankAPIError: Si l'API est inaccessible après tous les retries
        """
        if indicators is None:
            indicators = CORE_INDICATORS
        
        logger.info(f"Fetch World Bank - Pays: {country_code} - Indicateurs: {len(indicators)}")
        
        all_data = []
        
        # Récupérer chaque indicateur
        for indicator_code in indicators:
            try:
                data = self._fetch_single_indicator(country_code, indicator_code)
                if data:
                    all_data.extend(data)
                    logger.debug(f"✓ {indicator_code}: {len(data)} valeurs")
                else:
                    logger.warning(f"⚠️ {indicator_code}: aucune donnée")
                
                # Petit délai pour ne pas surcharger l'API
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"❌ Erreur {indicator_code}: {e}")
                continue
        
        logger.info(f"✅ Total: {len(all_data)} données récupérées pour {country_code}")
        return all_data
    
    # ========================================================================
    # MÉTHODE INTERNE : Fetch Single Indicator
    # ========================================================================
    
    def _fetch_single_indicator(self, country_code: str, 
                                indicator_code: str) -> List[Dict[str, Any]]:
        """
        Récupère un seul indicateur pour un pays
        Gère les retries en cas d'échec
        
        Args:
            country_code: Code ISO du pays
            indicator_code: Code de l'indicateur (ex: 'NY.GDP.MKTP.CD')
        
        Returns:
            Liste de données (historique si disponible)
        """
        # URL format: /v2/country/{code}/indicator/{indicator}
        url = f"{self.base_url}/country/{country_code}/indicator/{indicator_code}"
        
        # Paramètres: on récupère les 5 dernières années pour avoir la plus récente
        params = self.default_params.copy()
        params['per_page'] = 5  # Limiter à 5 résultats
        
        # Tentatives avec retry
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Requête {url} (tentative {attempt + 1}/{self.max_retries})")
                
                response = self.session.get(
                    url,
                    params=params,
                    timeout=self.timeout
                )
                
                # Vérifier le status
                response.raise_for_status()
                
                # Parser la réponse JSON
                json_data = response.json()
                
                # DEBUG: Afficher le format de réponse
                logger.debug(f"Type réponse: {type(json_data)}")
                if isinstance(json_data, list):
                    logger.debug(f"Longueur liste: {len(json_data)}")
                
                # CAS 1: Erreur API (message d'erreur)
                if isinstance(json_data, list) and len(json_data) == 1:
                    if isinstance(json_data[0], dict) and 'message' in json_data[0]:
                        error_messages = json_data[0]['message']
                        if isinstance(error_messages, list) and len(error_messages) > 0:
                            error = error_messages[0]
                            logger.error(f"Erreur API pour {indicator_code}: {error.get('value', 'Unknown error')}")
                            return []
                
                # CAS 2: Format standard [metadata, data]
                if isinstance(json_data, list) and len(json_data) >= 2:
                    metadata = json_data[0]
                    data = json_data[1]
                    
                    # Vérifier si data est une liste non-vide
                    if isinstance(data, list) and len(data) > 0:
                        # Filtrer les valeurs null et trier par date (plus récent d'abord)
                        valid_data = [d for d in data if d.get('value') is not None]
                        
                        if valid_data:
                            # Trier par année (plus récent en premier)
                            valid_data.sort(key=lambda x: int(x.get('date', 0)), reverse=True)
                            
                            # Retourner seulement la valeur la plus récente
                            logger.debug(f"✓ Donnée trouvée: {valid_data[0].get('date')} = {valid_data[0].get('value')}")
                            return [valid_data[0]]  # Retourner seulement la plus récente
                        else:
                            logger.warning(f"Toutes les valeurs sont null pour {indicator_code}")
                            return []
                    
                    # Si data est None ou vide
                    elif data is None or (isinstance(data, list) and len(data) == 0):
                        logger.warning(f"Liste de données vide pour {indicator_code} ({country_code})")
                        
                        # Vérifier le message d'erreur dans metadata
                        if isinstance(metadata, dict):
                            page = metadata.get('page', 0)
                            total = metadata.get('total', 0)
                            logger.debug(f"Metadata: page={page}, total={total}")
                            
                            if total == 0:
                                logger.warning(f"Indicateur {indicator_code} non disponible pour {country_code}")
                        
                        return []
                    
                    else:
                        logger.error(f"Format data invalide: {type(data)}")
                        return []
                
                # CAS 3: Format dictionnaire d'erreur
                elif isinstance(json_data, dict):
                    if 'message' in json_data:
                        logger.error(f"Erreur API: {json_data['message']}")
                    else:
                        logger.error(f"Réponse dict inattendue: {json_data}")
                    return []
                
                # CAS 4: Format inconnu
                else:
                    logger.error(f"Format réponse inconnu pour {indicator_code}: {type(json_data)}")
                    logger.debug(f"Contenu: {str(json_data)[:200]}")
                    return []
                
            except requests.Timeout:
                logger.warning(f"⏱️ Timeout tentative {attempt + 1} pour {indicator_code}")
                if attempt < self.max_retries - 1:
                    time.sleep(1 * (attempt + 1))  # Backoff exponentiel
                    continue
                else:
                    logger.error(f"❌ Timeout définitif pour {indicator_code}")
                    return []
            
            except requests.HTTPError as e:
                if e.response.status_code == 404:
                    logger.warning(f"⚠️ Indicateur {indicator_code} non disponible pour {country_code}")
                    return []
                else:
                    logger.error(f"❌ Erreur HTTP {e.response.status_code}: {e}")
                    if attempt < self.max_retries - 1:
                        time.sleep(1)
                        continue
                    return []
            
            except requests.RequestException as e:
                logger.error(f"❌ Erreur réseau: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(1)
                    continue
                return []
            
            except Exception as e:
                logger.error(f"❌ Erreur inattendue: {e}")
                return []
        
        return []
    
    # ========================================================================
    # MÉTHODES UTILITAIRES
    # ========================================================================
    
    def fetch_country_info(self, country_code: str) -> Optional[Dict[str, Any]]:
        """
        Récupère les informations générales d'un pays
        
        Args:
            country_code: Code ISO du pays
        
        Returns:
            Dict avec nom, région, niveau de revenu, etc.
        """
        url = f"{self.base_url}/country/{country_code}"
        
        try:
            response = self.session.get(
                url,
                params={'format': 'json'},
                timeout=self.timeout
            )
            response.raise_for_status()
            
            json_data = response.json()
            if isinstance(json_data, list) and len(json_data) >= 2:
                country_info = json_data[1]
                if country_info and len(country_info) > 0:
                    return country_info[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Erreur récupération info pays {country_code}: {e}")
            return None
    
    def get_latest_value(self, data: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Extrait la valeur la plus récente d'une liste de données historiques
        
        Args:
            data: Liste de données World Bank avec dates
        
        Returns:
            Dict avec la valeur la plus récente
        """
        if not data:
            return None
        
        # Trier par date (plus récent en premier)
        sorted_data = sorted(
            data,
            key=lambda x: int(x.get('date', 0)),
            reverse=True
        )
        
        # Trouver la première valeur non-null
        for item in sorted_data:
            if item.get('value') is not None:
                return item
        
        return None
    
    def test_connection(self) -> bool:
        """
        Teste la connexion à l'API World Bank
        
        Returns:
            True si l'API est accessible
        """
        try:
            logger.info("Test connexion World Bank API...")
            
            # Requête simple sur les USA (population)
            url = f"{self.base_url}/country/US/indicator/SP.POP.TOTL"
            response = self.session.get(
                url,
                params={'format': 'json', 'per_page': 1},
                timeout=5
            )
            response.raise_for_status()
            
            # Vérifier que la réponse n'est pas une erreur
            json_data = response.json()
            
            # Vérifier le format d'erreur
            if isinstance(json_data, list) and len(json_data) == 1:
                if isinstance(json_data[0], dict) and 'message' in json_data[0]:
                    logger.error("❌ API retourne une erreur")
                    return False
            
            # Si on arrive ici, l'API fonctionne
            logger.info("✅ Connexion World Bank OK")
            return True
            
        except Exception as e:
            logger.error(f"❌ Connexion World Bank échouée: {e}")
            return False
    
    def get_available_indicators(self) -> List[str]:
        """
        Retourne la liste des indicateurs configurés
        
        Returns:
            Liste des codes d'indicateurs disponibles
        """
        return list(WORLD_BANK_INDICATORS.values())
    
    def get_indicator_name(self, indicator_code: str) -> str:
        """
        Retourne le nom lisible d'un indicateur
        
        Args:
            indicator_code: Code de l'indicateur (ex: 'NY.GDP.MKTP.CD')
        
        Returns:
            Nom lisible (ex: 'PIB')
        """
        for name, code in WORLD_BANK_INDICATORS.items():
            if code == indicator_code:
                return name.replace('_', ' ').title()
        return indicator_code
    
    def debug_single_request(self, country_code: str, indicator_code: str):
        """
        Méthode de debug pour examiner une requête spécifique
        Affiche tous les détails de la réponse
        
        Args:
            country_code: Code ISO du pays
            indicator_code: Code de l'indicateur
        """
        url = f"{self.base_url}/country/{country_code}/indicator/{indicator_code}"
        
        # Paramètres simplifiés (sans date)
        params = {'format': 'json', 'per_page': 5}
        
        print("\n" + "="*70)
        print("🔍 DEBUG - Requête World Bank")
        print("="*70)
        print(f"URL: {url}")
        print(f"Params: {params}")
        print()
        
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            
            print(f"Status Code: {response.status_code}")
            print(f"Content-Type: {response.headers.get('Content-Type')}")
            print(f"Content-Length: {response.headers.get('Content-Length')}")
            print()
            
            if response.status_code == 200:
                json_data = response.json()
                
                print("📦 Structure de la réponse:")
                print(f"   Type: {type(json_data)}")
                
                if isinstance(json_data, list):
                    print(f"   Longueur: {len(json_data)}")
                    
                    for i, item in enumerate(json_data):
                        print(f"\n   [{i}] Type: {type(item)}")
                        
                        if isinstance(item, dict):
                            print(f"        Clés: {list(item.keys())[:10]}")
                            
                            # Vérifier si c'est une erreur
                            if 'message' in item:
                                print(f"        ⚠️ Message d'erreur détecté:")
                                print(f"           {item['message']}")
                            
                            # Afficher metadata
                            if i == 0 and 'page' in item:
                                print(f"        Page: {item.get('page')}")
                                print(f"        Total: {item.get('total')}")
                                print(f"        Per_page: {item.get('per_page')}")
                        
                        elif isinstance(item, list):
                            print(f"        Longueur: {len(item)}")
                            if len(item) > 0:
                                print(f"        Premier élément: {str(item[0])[:150]}")
                                
                                # Afficher les années disponibles
                                if all(isinstance(x, dict) for x in item[:3]):
                                    years = [x.get('date') for x in item[:3] if x.get('date')]
                                    if years:
                                        print(f"        Années: {', '.join(years)}")
                
                print("\n📄 Réponse JSON complète (extrait):")
                print("-" * 70)
                import json
                formatted = json.dumps(json_data, indent=2, ensure_ascii=False)
                print(formatted[:1500])
                if len(formatted) > 1500:
                    print("...")
                print("-" * 70)
            else:
                print(f"❌ Erreur HTTP: {response.status_code}")
                print(f"   Réponse: {response.text[:500]}")
            
        except Exception as e:
            print(f"❌ Exception: {e}")
            import traceback
            traceback.print_exc()
        
        print("="*70 + "\n")

# ============================================================================
# EXCEPTIONS PERSONNALISÉES
# ============================================================================

class WorldBankAPIError(Exception):
    """Exception levée quand l'API World Bank est inaccessible"""
    pass

class InvalidCountryCodeError(Exception):
    """Exception levée quand le code pays est invalide"""
    pass

# ============================================================================
# FONCTIONS HELPER (pour utilisation directe)
# ============================================================================

def fetch_indicators(country_code: str, 
                    indicators: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Fonction wrapper simple pour récupérer des indicateurs
    Utilise une instance de WorldBankConnector
    
    Args:
        country_code: Code ISO du pays
        indicators: Liste des codes d'indicateurs (optionnel)
    
    Returns:
        Liste de données World Bank
    
    Example:
        >>> data = fetch_indicators('FR', ['NY.GDP.MKTP.CD', 'SP.POP.TOTL'])
        >>> print(data)
    """
    connector = WorldBankConnector()
    return connector.fetch_indicators(country_code, indicators)

def test_world_bank_api() -> bool:
    """
    Test rapide de l'API World Bank
    
    Returns:
        True si l'API est accessible
    """
    connector = WorldBankConnector()
    return connector.test_connection()

# ============================================================================
# EXEMPLE D'UTILISATION (si exécuté directement)
# ============================================================================

if __name__ == '__main__':
    # Configuration du logging pour les tests
    logging.basicConfig(
        level=logging.DEBUG,  # Changed to DEBUG
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 70)
    print("TEST WORLD BANK CONNECTOR")
    print("=" * 70)
    
    connector = WorldBankConnector()
    
    # Test DEBUG: Examiner une requête en détail
    print("\n🔍 DEBUG MODE: Analyse d'une requête")
    connector.debug_single_request('FR', 'NY.GDP.MKTP.CD')
    
    # Test 1: Connexion
    print("\n1. Test connexion API...")
    if connector.test_connection():
        print("✅ API accessible")
    else:
        print("❌ API inaccessible")
        exit(1)
    
    # Test 2: Récupération indicateurs France
    print("\n2. Test récupération France (6 indicateurs core)...")
    try:
        data = connector.fetch_indicators('FR', CORE_INDICATORS)
        print(f"✅ {len(data)} données récupérées")
        
        # Afficher un exemple
        if data:
            print("\nExemple de donnée:")
            example = data[0]
            print(f"  Indicateur: {example.get('indicator', {}).get('value')}")
            print(f"  Valeur: {example.get('value')}")
            print(f"  Année: {example.get('date')}")
    
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    # Test 3: Récupération info pays
    print("\n3. Test info pays...")
    try:
        info = connector.fetch_country_info('FR')
        if info:
            print(f"✅ Pays: {info.get('name')}")
            print(f"   Région: {info.get('region', {}).get('value')}")
            print(f"   Capital: {info.get('capitalCity')}")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    print("\n" + "=" * 70)
    print("TESTS TERMINÉS")
    print("=" * 70)