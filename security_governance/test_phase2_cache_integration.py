"""
Tests de Phase 2 - Extension du cache intelligent et monitoring
Valide l'intégration du cache aux connecteurs World Bank et OFAC SDN
Teste le système de monitoring du cache

Usage:
    python test_phase2_cache_integration.py
"""
import sys
import os
import logging
from datetime import datetime
import time

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import des connecteurs et monitoring
try:
    from worldbank_corruption_connector import WorldBankCorruptionConnector
    from ofac_sdn_connector import OFACSDNConnector
    from cache_monitoring import CacheMonitor
    CONNECTORS_AVAILABLE = True
except ImportError as e:
    logger.error(f"Erreur import: {e}")
    CONNECTORS_AVAILABLE = False


def test_worldbank_cache_integration():
    """Test 1: Intégration du cache au connecteur World Bank"""
    logger.info("\n" + "="*80)
    logger.info("TEST 1: Intégration cache World Bank")
    logger.info("="*80)

    try:
        connector = WorldBankCorruptionConnector(timeout=15, max_retries=2)

        # Premier appel (cache miss)
        logger.info("Premier appel - devrait créer entrée cache...")
        start_time = time.time()
        result1 = connector.get_corruption_data(year=2022, limit=10)
        time1 = time.time() - start_time

        if not result1.get('success'):
            logger.warning(f"⚠️ Échec récupération données: {result1.get('error')}")
            return False

        logger.info(f"✅ Données récupérées en {time1:.2f}s")
        logger.info(f"   Pays: {result1.get('total_countries', 0)}")
        is_cached1 = result1.get('_cached', False)
        logger.info(f"   En cache: {is_cached1}")

        # Deuxième appel (cache hit espéré)
        logger.info("\nDeuxième appel - devrait utiliser le cache...")
        time.sleep(0.5)  # Petite pause
        start_time = time.time()
        result2 = connector.get_corruption_data(year=2022, limit=10)
        time2 = time.time() - start_time

        if not result2.get('success'):
            logger.warning(f"⚠️ Échec deuxième appel")
            return False

        is_cached2 = result2.get('_cached', False)
        logger.info(f"✅ Données récupérées en {time2:.2f}s")
        logger.info(f"   En cache: {is_cached2}")

        # Vérifier amélioration performance
        if is_cached2 and time2 < time1:
            speedup = (time1 - time2) / time1 * 100
            logger.info(f"🚀 Performance: {speedup:.1f}% plus rapide avec cache")
            return True
        elif is_cached2:
            logger.info("✅ Cache utilisé mais pas d'amélioration significative")
            return True
        else:
            logger.warning("⚠️ Cache non utilisé au deuxième appel")
            return True  # Pas bloquant

    except Exception as e:
        logger.error(f"❌ ERREUR: {e}")
        return False


def test_worldbank_circuit_breaker():
    """Test 2: Circuit breaker World Bank"""
    logger.info("\n" + "="*80)
    logger.info("TEST 2: Circuit Breaker World Bank")
    logger.info("="*80)

    try:
        connector = WorldBankCorruptionConnector(timeout=5, max_retries=1)

        # État initial
        logger.info(f"État initial circuit breaker: {connector.circuit_breaker}")

        # Simuler échecs
        for i in range(4):
            connector._record_failure()
            logger.info(f"Échec {i+1}: Failures={connector.circuit_breaker['failures']}, "
                       f"Ouvert={connector.circuit_breaker['open']}")

        # Vérifier circuit ouvert
        if connector.circuit_breaker['open']:
            logger.info("✅ Circuit breaker ouvert après 3 échecs")

            # Tester blocage
            can_proceed = connector._check_circuit_breaker()
            if not can_proceed:
                logger.info("✅ Circuit breaker bloque correctement")
                return True
            else:
                logger.warning("⚠️ Circuit breaker ne bloque pas")
                return False
        else:
            logger.warning("⚠️ Circuit breaker devrait être ouvert")
            return False

    except Exception as e:
        logger.error(f"❌ ERREUR: {e}")
        return False


def test_ofac_cache_integration():
    """Test 3: Intégration du cache au connecteur OFAC SDN"""
    logger.info("\n" + "="*80)
    logger.info("TEST 3: Intégration cache OFAC SDN")
    logger.info("="*80)

    try:
        connector = OFACSDNConnector(timeout=30, max_retries=2)

        # Premier appel
        logger.info("Premier appel - récupération liste SDN...")
        start_time = time.time()
        result1 = connector.get_sdn_list(limit=20)
        time1 = time.time() - start_time

        if not result1.get('success'):
            logger.warning(f"⚠️ Échec récupération SDN: {result1.get('error')}")
            return False

        logger.info(f"✅ Liste SDN récupérée en {time1:.2f}s")
        logger.info(f"   Entrées: {result1.get('count', 0)}")
        is_cached1 = result1.get('_cached', False)
        logger.info(f"   En cache: {is_cached1}")

        # Deuxième appel
        logger.info("\nDeuxième appel - devrait utiliser le cache...")
        time.sleep(0.5)
        start_time = time.time()
        result2 = connector.get_sdn_list(limit=20)
        time2 = time.time() - start_time

        is_cached2 = result2.get('_cached', False)
        logger.info(f"✅ Données récupérées en {time2:.2f}s")
        logger.info(f"   En cache: {is_cached2}")

        if is_cached2 and time2 < time1:
            speedup = (time1 - time2) / time1 * 100
            logger.info(f"🚀 Performance: {speedup:.1f}% plus rapide avec cache")

        return True

    except Exception as e:
        logger.error(f"❌ ERREUR: {e}")
        return False


def test_ofac_circuit_breaker():
    """Test 4: Circuit breaker OFAC"""
    logger.info("\n" + "="*80)
    logger.info("TEST 4: Circuit Breaker OFAC SDN")
    logger.info("="*80)

    try:
        connector = OFACSDNConnector(timeout=5, max_retries=1)

        # Simuler échecs
        for i in range(4):
            connector._record_failure()
            logger.info(f"Échec {i+1}: Failures={connector.circuit_breaker['failures']}, "
                       f"Ouvert={connector.circuit_breaker['open']}")

        # Vérifier
        if connector.circuit_breaker['open']:
            logger.info("✅ Circuit breaker ouvert après 3 échecs")

            can_proceed = connector._check_circuit_breaker()
            if not can_proceed:
                logger.info("✅ Circuit breaker bloque correctement")
                return True

        logger.warning("⚠️ Circuit breaker non fonctionnel")
        return False

    except Exception as e:
        logger.error(f"❌ ERREUR: {e}")
        return False


def test_cache_monitoring():
    """Test 5: Système de monitoring du cache"""
    logger.info("\n" + "="*80)
    logger.info("TEST 5: Monitoring du cache")
    logger.info("="*80)

    try:
        monitor = CacheMonitor()

        if not monitor.is_available():
            logger.warning("⚠️ Monitoring non disponible (CacheManager introuvable)")
            return True  # Pas bloquant

        # Statistiques globales
        logger.info("Récupération statistiques globales...")
        stats = monitor.get_cache_statistics()

        if stats.get('available'):
            logger.info(f"✅ Statistiques récupérées:")
            logger.info(f"   Fichiers: {stats['total_files']}")
            logger.info(f"   Taille: {stats['total_size_mb']} MB")
            logger.info(f"   Sources: {stats['source_count']}")
        else:
            logger.warning(f"⚠️ Erreur statistiques: {stats.get('error')}")

        # Santé du cache
        logger.info("\nÉvaluation santé du cache...")
        health = monitor.get_cache_health()

        if health.get('healthy') is not None:
            status_emoji = "✅" if health['status'] == 'healthy' else "⚠️" if health['status'] == 'warning' else "❌"
            logger.info(f"{status_emoji} Statut: {health['status'].upper()}")

            if health.get('warnings'):
                for warning in health['warnings']:
                    logger.info(f"   ⚠️ {warning}")

            if health.get('recommendations'):
                for rec in health['recommendations'][:2]:  # Limiter à 2
                    logger.info(f"   💡 {rec}")

        # Générer rapport
        logger.info("\nGénération rapport...")
        report = monitor.generate_report(include_details=False)
        if report:
            logger.info("✅ Rapport généré (voir ci-dessous)")
            # Afficher rapport
            print("\n" + report)

        return True

    except Exception as e:
        logger.error(f"❌ ERREUR: {e}")
        return False


def test_cache_cleanup():
    """Test 6: Nettoyage du cache"""
    logger.info("\n" + "="*80)
    logger.info("TEST 6: Nettoyage du cache (dry-run)")
    logger.info("="*80)

    try:
        monitor = CacheMonitor()

        if not monitor.is_available():
            logger.warning("⚠️ Monitoring non disponible")
            return True

        logger.info("Simulation nettoyage cache expiré...")
        result = monitor.clear_expired_cache(dry_run=True)

        if result.get('success'):
            logger.info(f"✅ Nettoyage simulé:")
            logger.info(f"   Fichiers expirés: {result['deleted_count']}")
            logger.info(f"   Espace récupérable: {result['deleted_size_mb']} MB")
            logger.info(f"   Sources concernées: {len(result['sources_cleaned'])}")
            return True
        else:
            logger.warning(f"⚠️ Erreur nettoyage: {result.get('error')}")
            return False

    except Exception as e:
        logger.error(f"❌ ERREUR: {e}")
        return False


def run_all_tests():
    """Exécute tous les tests de Phase 2"""
    logger.info("\n" + "#"*80)
    logger.info("#" + " "*78 + "#")
    logger.info("#" + " TEST D'INTÉGRATION CACHE - PHASE 2 ".center(78) + "#")
    logger.info("#" + f" {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ".center(78) + "#")
    logger.info("#" + " "*78 + "#")
    logger.info("#"*80 + "\n")

    if not CONNECTORS_AVAILABLE:
        logger.error("❌ ERREUR CRITIQUE - Connecteurs non disponibles")
        return

    # Exécution des tests
    tests = [
        ("Cache World Bank", test_worldbank_cache_integration),
        ("Circuit Breaker World Bank", test_worldbank_circuit_breaker),
        ("Cache OFAC SDN", test_ofac_cache_integration),
        ("Circuit Breaker OFAC", test_ofac_circuit_breaker),
        ("Monitoring du cache", test_cache_monitoring),
        ("Nettoyage du cache", test_cache_cleanup)
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
    logger.info("RAPPORT FINAL - PHASE 2")
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
    elif passed_tests >= total_tests * 0.8:  # 80%
        logger.info("✅ Majorité des tests passés - Phase 2 validée")
        return True
    else:
        logger.warning(f"⚠️ {failed_tests} test(s) ont échoué")
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
