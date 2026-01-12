"""
Test de résilience pour les connecteurs sécurité & gouvernance - Phase 1
Tests de validation des corrections DNS UCDP et URLs CPI
Tests du circuit breaker et retry logic

Usage:
    python test_phase1_resilience.py
"""
import sys
import os
import logging
from datetime import datetime
import json

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import des connecteurs
try:
    from ucdp_connector import UCDPConnector
    from transparency_cpi_connector import TransparencyCPIConnector
    CONNECTORS_AVAILABLE = True
except ImportError as e:
    logger.error(f"Erreur import connecteurs: {e}")
    CONNECTORS_AVAILABLE = False


def test_ucdp_api_connection():
    """Test 1: Vérification de la connexion à l'API UCDP avec nouvelle URL"""
    logger.info("\n" + "="*80)
    logger.info("TEST 1: Connexion API UCDP (nouvelle URL)")
    logger.info("="*80)

    try:
        connector = UCDPConnector(timeout=15, max_retries=2)
        logger.info(f"Base URL configurée: {connector.BASE_URL}")
        logger.info(f"Timeout: {connector.timeout}s, Max retries: {connector.max_retries}")

        # Test requête simple
        logger.info("Tentative de récupération des conflits récents...")
        result = connector.get_recent_conflicts(days=7, limit=10)

        if result.get('success'):
            logger.info(f"✅ SUCCÈS - API UCDP accessible")
            logger.info(f"   Source: {result.get('source')}")
            logger.info(f"   Événements: {result.get('total_events', 0)}")
            if result.get('events'):
                logger.info(f"   Premier événement: {result['events'][0].get('country', 'N/A')}")
            return True
        else:
            logger.warning(f"⚠️ ÉCHEC - API UCDP non accessible")
            logger.warning(f"   Erreur: {result.get('error', 'Unknown')}")
            logger.warning(f"   Message: {result.get('message', 'N/A')}")
            return False

    except Exception as e:
        logger.error(f"❌ ERREUR - Exception lors du test UCDP: {e}")
        return False


def test_ucdp_circuit_breaker():
    """Test 2: Validation du circuit breaker UCDP"""
    logger.info("\n" + "="*80)
    logger.info("TEST 2: Circuit Breaker UCDP")
    logger.info("="*80)

    try:
        connector = UCDPConnector(timeout=5, max_retries=1)

        # État initial
        logger.info(f"État circuit breaker initial: {connector.circuit_breaker}")

        # Test avec endpoint invalide (forcer échecs)
        logger.info("Test avec endpoint invalide pour déclencher circuit breaker...")

        for i in range(4):
            result = connector._make_request('/api/invalid_endpoint', {})
            logger.info(f"Tentative {i+1}: Échecs={connector.circuit_breaker['failures']}, "
                       f"Ouvert={connector.circuit_breaker['open']}")

        # Vérifier que le circuit est ouvert après 3 échecs
        if connector.circuit_breaker['open']:
            logger.info("✅ SUCCÈS - Circuit breaker ouvert après 3 échecs")
            return True
        else:
            logger.warning("⚠️ ÉCHEC - Circuit breaker devrait être ouvert")
            return False

    except Exception as e:
        logger.error(f"❌ ERREUR - Exception lors du test circuit breaker: {e}")
        return False


def test_cpi_data_access():
    """Test 3: Accès aux données CPI avec nouvelles URLs"""
    logger.info("\n" + "="*80)
    logger.info("TEST 3: Accès données CPI (sources alternatives)")
    logger.info("="*80)

    try:
        connector = TransparencyCPIConnector(timeout=30, max_retries=2)
        logger.info(f"URLs alternatives configurées:")
        for name, url in connector.ALT_URLS.items():
            logger.info(f"   - {name}: {url}")

        # Test récupération données
        logger.info("Tentative de récupération données CPI 2023...")
        result = connector.get_cpi_data(year=2023)

        if result.get('success'):
            logger.info(f"✅ SUCCÈS - Données CPI accessibles")
            logger.info(f"   Année: {result.get('year')}")
            logger.info(f"   Pays: {result.get('total_countries', 0)}")
            logger.info(f"   Source: {result.get('source')}")

            # Afficher top 5 pays
            if result.get('data'):
                logger.info("   Top 5 pays les moins corrompus:")
                for i, country in enumerate(result['data'][:5], 1):
                    logger.info(f"      {i}. {country.get('country')}: {country.get('cpi_score')}")
            return True
        else:
            logger.warning(f"⚠️ ÉCHEC - Données CPI non accessibles")
            logger.warning(f"   Erreur: {result.get('error', 'Unknown')}")
            return False

    except Exception as e:
        logger.error(f"❌ ERREUR - Exception lors du test CPI: {e}")
        return False


def test_cpi_circuit_breaker():
    """Test 4: Validation du circuit breaker CPI"""
    logger.info("\n" + "="*80)
    logger.info("TEST 4: Circuit Breaker CPI")
    logger.info("="*80)

    try:
        connector = TransparencyCPIConnector(timeout=5, max_retries=1)

        # État initial
        logger.info(f"État circuit breaker initial: {connector.circuit_breaker}")

        # Forcer des échecs
        logger.info("Simulation d'échecs pour déclencher circuit breaker...")

        for i in range(4):
            connector._record_failure()
            logger.info(f"Échec {i+1}: Failures={connector.circuit_breaker['failures']}, "
                       f"Ouvert={connector.circuit_breaker['open']}")

        # Vérifier que le circuit est ouvert
        if connector.circuit_breaker['open']:
            logger.info("✅ SUCCÈS - Circuit breaker ouvert après 3 échecs")

            # Test vérification circuit breaker
            can_proceed = connector._check_circuit_breaker()
            if not can_proceed:
                logger.info("✅ SUCCÈS - Circuit breaker bloque correctement les requêtes")
                return True
            else:
                logger.warning("⚠️ ÉCHEC - Circuit breaker ne bloque pas les requêtes")
                return False
        else:
            logger.warning("⚠️ ÉCHEC - Circuit breaker devrait être ouvert")
            return False

    except Exception as e:
        logger.error(f"❌ ERREUR - Exception lors du test circuit breaker CPI: {e}")
        return False


def test_config_file_loading():
    """Test 5: Chargement du fichier de configuration"""
    logger.info("\n" + "="*80)
    logger.info("TEST 5: Chargement configuration sources")
    logger.info("="*80)

    config_path = os.path.join(os.path.dirname(__file__), 'data_sources_config.json')

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        logger.info(f"✅ Configuration chargée: {config_path}")
        logger.info(f"   Version: {config['metadata']['version']}")
        logger.info(f"   Dernière mise à jour: {config['metadata']['last_updated']}")
        logger.info(f"   Sources configurées: {len(config['sources'])}")

        # Vérifier sources critiques
        critical_sources = ['ucdp', 'transparency_cpi']
        for source in critical_sources:
            if source in config['sources']:
                source_config = config['sources'][source]
                logger.info(f"   ✅ {source}: {source_config.get('name')}")
                logger.info(f"      - Timeout: {source_config.get('timeout')}s")
                logger.info(f"      - Max retries: {source_config.get('max_retries')}")
            else:
                logger.warning(f"   ⚠️ {source}: NON CONFIGURÉ")

        return True

    except FileNotFoundError:
        logger.error(f"❌ ERREUR - Fichier de configuration non trouvé: {config_path}")
        return False
    except json.JSONDecodeError as e:
        logger.error(f"❌ ERREUR - Configuration JSON invalide: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ ERREUR - Exception lors du chargement config: {e}")
        return False


def run_all_tests():
    """Exécute tous les tests de phase 1"""
    logger.info("\n" + "#"*80)
    logger.info("#" + " "*78 + "#")
    logger.info("#" + " TEST DE RÉSILIENCE - PHASE 1 ".center(78) + "#")
    logger.info("#" + f" {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ".center(78) + "#")
    logger.info("#" + " "*78 + "#")
    logger.info("#"*80 + "\n")

    if not CONNECTORS_AVAILABLE:
        logger.error("❌ ERREUR CRITIQUE - Connecteurs non disponibles")
        return

    # Exécution des tests
    tests = [
        ("Configuration sources", test_config_file_loading),
        ("API UCDP", test_ucdp_api_connection),
        ("Circuit Breaker UCDP", test_ucdp_circuit_breaker),
        ("Données CPI", test_cpi_data_access),
        ("Circuit Breaker CPI", test_cpi_circuit_breaker)
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"Exception non gérée dans {test_name}: {e}")
            results[test_name] = False

    # Rapport final
    logger.info("\n" + "="*80)
    logger.info("RAPPORT FINAL")
    logger.info("="*80)

    total_tests = len(results)
    passed_tests = sum(1 for r in results.values() if r)
    failed_tests = total_tests - passed_tests

    for test_name, result in results.items():
        status = "✅ RÉUSSI" if result else "❌ ÉCHEC"
        logger.info(f"{status} - {test_name}")

    logger.info("-"*80)
    logger.info(f"Total: {total_tests} tests | "
                f"Réussis: {passed_tests} | "
                f"Échecs: {failed_tests} | "
                f"Taux: {(passed_tests/total_tests)*100:.1f}%")
    logger.info("="*80 + "\n")

    if passed_tests == total_tests:
        logger.info("🎉 TOUS LES TESTS SONT PASSÉS!")
        return True
    else:
        logger.warning(f"⚠️ {failed_tests} test(s) ont échoué - revue nécessaire")
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
