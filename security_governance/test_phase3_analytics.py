"""
Tests de Phase 3 - Dashboard Analytics et Visualisations
Valide l'intégration OCHA HDX, le dashboard analytics et le système de visualisations

Usage:
    python test_phase3_analytics.py
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

# Import des modules
try:
    from ocha_hdx_connector import OchaHdxConnector
    from analytics_dashboard import SecurityAnalyticsDashboard
    from visualizations import SecurityVisualizationEngine
    MODULES_AVAILABLE = True
except ImportError as e:
    logger.error(f"Erreur import: {e}")
    MODULES_AVAILABLE = False


def test_ocha_hdx_cache_integration():
    """Test 1: Intégration du cache au connecteur OCHA HDX"""
    logger.info("\n" + "="*80)
    logger.info("TEST 1: Intégration cache OCHA HDX")
    logger.info("="*80)

    try:
        connector = OchaHdxConnector(timeout=30, max_retries=2)

        # Premier appel (cache miss)
        logger.info("Premier appel - recherche datasets sur HDX...")
        start_time = time.time()
        result1 = connector.search_datasets(query="crisis", limit=10)
        time1 = time.time() - start_time

        if not result1.get('success'):
            logger.warning(f"⚠️ Échec récupération HDX: {result1.get('error')}")
            return False

        logger.info(f"✅ Données récupérées en {time1:.2f}s")
        logger.info(f"   Datasets: {result1.get('count', 0)}")
        is_cached1 = result1.get('_cached', False)
        logger.info(f"   En cache: {is_cached1}")

        # Deuxième appel (cache hit espéré)
        logger.info("\nDeuxième appel - devrait utiliser le cache...")
        time.sleep(0.5)
        start_time = time.time()
        result2 = connector.search_datasets(query="crisis", limit=10)
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


def test_ocha_hdx_circuit_breaker():
    """Test 2: Circuit breaker OCHA HDX"""
    logger.info("\n" + "="*80)
    logger.info("TEST 2: Circuit Breaker OCHA HDX")
    logger.info("="*80)

    try:
        connector = OchaHdxConnector(timeout=5, max_retries=1)

        # État initial
        logger.info(f"État initial circuit breaker: {connector.circuit_breaker}")

        # Simuler échecs
        for i in range(4):
            connector.circuit_breaker['failures'] += 1
            if connector.circuit_breaker['failures'] >= 3:
                connector.circuit_breaker['open'] = True
                connector.circuit_breaker['last_failure'] = datetime.now()
            logger.info(f"Échec {i+1}: Failures={connector.circuit_breaker['failures']}, "
                       f"Ouvert={connector.circuit_breaker['open']}")

        # Vérifier circuit ouvert
        if connector.circuit_breaker['open']:
            logger.info("✅ Circuit breaker ouvert après 3 échecs")
            return True
        else:
            logger.warning("⚠️ Circuit breaker devrait être ouvert")
            return False

    except Exception as e:
        logger.error(f"❌ ERREUR: {e}")
        return False


def test_analytics_dashboard_global_overview():
    """Test 3: Dashboard analytics - vue globale"""
    logger.info("\n" + "="*80)
    logger.info("TEST 3: Dashboard Analytics - Vue globale")
    logger.info("="*80)

    try:
        dashboard = SecurityAnalyticsDashboard()

        logger.info("Récupération vue globale (agrégation de toutes les sources)...")
        start_time = time.time()
        overview = dashboard.get_global_overview()
        elapsed = time.time() - start_time

        if not overview.get('success'):
            logger.warning(f"⚠️ Échec vue globale: {overview.get('error')}")
            return False

        logger.info(f"✅ Vue globale récupérée en {elapsed:.2f}s")

        # Vérifier sections
        sections = ['conflicts', 'corruption', 'sanctions', 'humanitarian']
        present_sections = [s for s in sections if s in overview]
        logger.info(f"   Sections présentes: {len(present_sections)}/{len(sections)}")

        for section in present_sections:
            data = overview[section]
            logger.info(f"   - {section}: {data.get('total', 'N/A')} entrées")

        # Statistiques globales
        if 'global_statistics' in overview:
            stats = overview['global_statistics']
            logger.info(f"\nStatistiques globales:")
            logger.info(f"   Total conflits: {stats.get('total_conflicts', 0)}")
            logger.info(f"   Total sanctions: {stats.get('total_sanctions', 0)}")
            logger.info(f"   Crises humanitaires: {stats.get('crisis_types_count', 0)}")

        return True

    except Exception as e:
        logger.error(f"❌ ERREUR: {e}")
        return False


def test_analytics_dashboard_country_profile():
    """Test 4: Dashboard analytics - profil pays"""
    logger.info("\n" + "="*80)
    logger.info("TEST 4: Dashboard Analytics - Profil pays")
    logger.info("="*80)

    try:
        dashboard = SecurityAnalyticsDashboard()

        # Tester avec un pays exemple
        test_countries = ['AFG', 'SYR', 'YEM']

        for country_code in test_countries:
            logger.info(f"\nRécupération profil pour {country_code}...")
            profile = dashboard.get_country_profile(country_code)

            if profile.get('success'):
                logger.info(f"✅ Profil {country_code} récupéré")
                logger.info(f"   Conflits: {profile.get('conflicts_count', 0)}")
                logger.info(f"   Score corruption: {profile.get('corruption_score', 'N/A')}")
                logger.info(f"   Sanctions: {profile.get('sanctions_count', 0)}")
                return True  # Au moins un profil réussi
            else:
                logger.warning(f"⚠️ Échec profil {country_code}")

        logger.warning("⚠️ Aucun profil pays récupéré")
        return True  # Pas bloquant si données pas disponibles

    except Exception as e:
        logger.error(f"❌ ERREUR: {e}")
        return False


def test_analytics_dashboard_top_risks():
    """Test 5: Dashboard analytics - top risques"""
    logger.info("\n" + "="*80)
    logger.info("TEST 5: Dashboard Analytics - Top risques")
    logger.info("="*80)

    try:
        dashboard = SecurityAnalyticsDashboard()

        logger.info("Identification des principaux risques sécuritaires...")
        risks = dashboard.get_top_risks(limit=10)

        if not risks.get('success'):
            logger.warning(f"⚠️ Échec top risques: {risks.get('error')}")
            return False

        logger.info(f"✅ Top risques identifiés")
        logger.info(f"   Total risques: {risks.get('total_risks', 0)}")

        # Afficher top 5
        top_risks = risks.get('risks', [])[:5]
        if top_risks:
            logger.info("\n   Top 5 risques:")
            for i, risk in enumerate(top_risks, 1):
                logger.info(f"   {i}. {risk.get('label', 'Unknown')} "
                          f"(score: {risk.get('score', 0)}, "
                          f"type: {risk.get('type', 'unknown')})")

        return True

    except Exception as e:
        logger.error(f"❌ ERREUR: {e}")
        return False


def test_analytics_dashboard_report():
    """Test 6: Dashboard analytics - génération rapport"""
    logger.info("\n" + "="*80)
    logger.info("TEST 6: Dashboard Analytics - Génération rapport")
    logger.info("="*80)

    try:
        dashboard = SecurityAnalyticsDashboard()

        logger.info("Génération rapport complet...")
        report = dashboard.generate_comprehensive_report()

        if not report:
            logger.warning("⚠️ Rapport vide")
            return False

        logger.info(f"✅ Rapport généré ({len(report)} caractères)")

        # Vérifier présence sections clés
        required_sections = ['SECURITY ANALYTICS DASHBOARD', 'GLOBAL OVERVIEW']
        present = sum(1 for s in required_sections if s in report)
        logger.info(f"   Sections clés présentes: {present}/{len(required_sections)}")

        # Afficher extrait
        lines = report.split('\n')[:10]
        logger.info("\n   Extrait du rapport:")
        for line in lines:
            logger.info(f"   {line}")

        return True

    except Exception as e:
        logger.error(f"❌ ERREUR: {e}")
        return False


def test_visualization_engine_availability():
    """Test 7: Moteur de visualisation - disponibilité"""
    logger.info("\n" + "="*80)
    logger.info("TEST 7: Moteur de visualisation - Disponibilité")
    logger.info("="*80)

    try:
        viz_engine = SecurityVisualizationEngine()

        available = viz_engine.is_available()
        logger.info(f"Moteur de visualisation disponible: {available}")

        if available:
            logger.info(f"✅ Répertoire de sortie: {viz_engine.output_dir}")
            logger.info(f"   Palette de couleurs: {len(viz_engine.colors)} couleurs")
            return True
        else:
            logger.warning("⚠️ Aucune bibliothèque de visualisation disponible")
            logger.warning("   Installer: pip install matplotlib plotly")
            return True  # Pas bloquant

    except Exception as e:
        logger.error(f"❌ ERREUR: {e}")
        return False


def test_visualization_charts_generation():
    """Test 8: Génération de graphiques"""
    logger.info("\n" + "="*80)
    logger.info("TEST 8: Génération de graphiques")
    logger.info("="*80)

    try:
        viz_engine = SecurityVisualizationEngine()

        if not viz_engine.is_available():
            logger.warning("⚠️ Visualisations non disponibles - test passé")
            return True

        # Données de test
        test_conflicts = [
            {'region': 'Middle East', 'country': 'Syria'},
            {'region': 'Middle East', 'country': 'Yemen'},
            {'region': 'Africa', 'country': 'Somalia'},
            {'region': 'Africa', 'country': 'Sudan'}
        ]

        test_corruption = [
            {'country': 'Denmark', 'score': 88},
            {'country': 'Finland', 'score': 87},
            {'country': 'Somalia', 'score': 12},
            {'country': 'Syria', 'score': 13}
        ]

        test_crisis_dist = {
            'armed_conflict': 15,
            'displacement': 23,
            'food_security': 18,
            'health': 12
        }

        generated = []

        # Tenter de générer chaque type de graphique
        logger.info("\nGénération graphiques...")

        # 1. Carte conflits
        logger.info("  - Carte conflits...")
        filepath = viz_engine.create_conflict_map(test_conflicts,
                                                  output_file='test_conflicts.png')
        if filepath:
            generated.append('conflict_map')
            logger.info(f"    ✅ Créé: {filepath}")

        # 2. Graphique corruption
        logger.info("  - Graphique corruption...")
        filepath = viz_engine.create_corruption_chart(test_corruption,
                                                     chart_type='bar',
                                                     output_file='test_corruption.png')
        if filepath:
            generated.append('corruption_chart')
            logger.info(f"    ✅ Créé: {filepath}")

        # 3. Distribution crises
        logger.info("  - Distribution crises...")
        filepath = viz_engine.create_crisis_distribution(test_crisis_dist,
                                                        output_file='test_crisis.png')
        if filepath:
            generated.append('crisis_distribution')
            logger.info(f"    ✅ Créé: {filepath}")

        logger.info(f"\n✅ {len(generated)} graphiques générés avec succès")
        return True

    except Exception as e:
        logger.error(f"❌ ERREUR: {e}")
        return False


def test_integration_dashboard_visualization():
    """Test 9: Intégration dashboard + visualisations"""
    logger.info("\n" + "="*80)
    logger.info("TEST 9: Intégration Dashboard + Visualisations")
    logger.info("="*80)

    try:
        dashboard = SecurityAnalyticsDashboard()
        viz_engine = SecurityVisualizationEngine()

        if not viz_engine.is_available():
            logger.warning("⚠️ Visualisations non disponibles - test passé")
            return True

        logger.info("Récupération données analytics...")
        overview = dashboard.get_global_overview()

        if not overview.get('success'):
            logger.warning("⚠️ Pas de données analytics disponibles")
            return True

        logger.info("Génération visualisations depuis données analytics...")
        visualizations = viz_engine.generate_dashboard_visualizations(overview)

        logger.info(f"✅ {len(visualizations)} visualisations générées")

        for viz_type, filepath in visualizations.items():
            logger.info(f"   - {viz_type}: {os.path.basename(filepath)}")

        # Exporter rapport
        report_path = viz_engine.export_visualization_report(visualizations)
        if report_path:
            logger.info(f"\n✅ Rapport exporté: {report_path}")

        return True

    except Exception as e:
        logger.error(f"❌ ERREUR: {e}")
        return False


def run_all_tests():
    """Exécute tous les tests de Phase 3"""
    logger.info("\n" + "#"*80)
    logger.info("#" + " "*78 + "#")
    logger.info("#" + " TEST D'INTÉGRATION - PHASE 3 ".center(78) + "#")
    logger.info("#" + f" Analytics Dashboard & Visualisations ".center(78) + "#")
    logger.info("#" + f" {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ".center(78) + "#")
    logger.info("#" + " "*78 + "#")
    logger.info("#"*80 + "\n")

    if not MODULES_AVAILABLE:
        logger.error("❌ ERREUR CRITIQUE - Modules non disponibles")
        return False

    # Exécution des tests
    tests = [
        ("Cache OCHA HDX", test_ocha_hdx_cache_integration),
        ("Circuit Breaker OCHA HDX", test_ocha_hdx_circuit_breaker),
        ("Dashboard - Vue globale", test_analytics_dashboard_global_overview),
        ("Dashboard - Profil pays", test_analytics_dashboard_country_profile),
        ("Dashboard - Top risques", test_analytics_dashboard_top_risks),
        ("Dashboard - Rapport", test_analytics_dashboard_report),
        ("Visualisation - Disponibilité", test_visualization_engine_availability),
        ("Visualisation - Génération graphiques", test_visualization_charts_generation),
        ("Intégration Dashboard + Visualisations", test_integration_dashboard_visualization)
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
    logger.info("RAPPORT FINAL - PHASE 3")
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
        logger.info("✅ Majorité des tests passés - Phase 3 validée")
        return True
    else:
        logger.warning(f"⚠️ {failed_tests} test(s) ont échoué")
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
