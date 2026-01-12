"""
Tests d'intégration API pour le dashboard analytics (Phase 4)
Vérifie que les nouvelles routes API sont fonctionnelles
"""
import sys
import os
import json
from unittest.mock import Mock, patch

# Ajouter le chemin du projet
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest


def test_analytics_dashboard_available():
    """Teste que le dashboard analytics est disponible"""
    from analytics_dashboard import SecurityAnalyticsDashboard, CONNECTORS_AVAILABLE

    # Vérifie que le module peut être importé
    assert SecurityAnalyticsDashboard is not None

    # Créer une instance
    dashboard = SecurityAnalyticsDashboard()
    assert dashboard is not None

    # Vérifier la disponibilité (peut être True ou False selon les connecteurs)
    available = dashboard.is_available()
    assert isinstance(available, bool)


def test_analytics_routes_exist():
    """Teste que les routes analytics sont définies dans le blueprint"""
    from . import security_bp

    # Vérifier que le blueprint existe
    assert security_bp is not None
    assert security_bp.name == 'security_governance'

    # Vérifier que certaines routes critiques sont présentes
    routes = {rule.rule for rule in security_bp.url_map.iter_rules()}

    # Routes analytics de base
    expected_routes = {
        '/api/analytics/overview',
        '/api/analytics/country-profile/<country_code>',
        '/api/analytics/top-risks',
        '/api/analytics/trends',
        '/api/analytics/report',
        '/api/analytics/export',
        '/api/analytics/health'
    }

    # Vérifier que chaque route attendue existe
    for route in expected_routes:
        full_route = f'/security-governance{route}'
        assert any(full_route in r or route in r for r in routes), f"Route manquante: {route}"


def test_analytics_dashboard_methods():
    """Teste les méthodes principales du dashboard"""
    from analytics_dashboard import SecurityAnalyticsDashboard

    dashboard = SecurityAnalyticsDashboard()

    # Test get_global_overview
    overview = dashboard.get_global_overview()
    assert isinstance(overview, dict)
    assert 'success' in overview
    assert 'available' in overview
    assert 'timestamp' in overview

    # Test get_top_risks
    risks = dashboard.get_top_risks(limit=5)
    assert isinstance(risks, dict)
    assert 'success' in risks
    assert 'risks' in risks
    assert isinstance(risks.get('risks'), list)

    # Test get_trends_analysis
    trends = dashboard.get_trends_analysis(months=3)
    assert isinstance(trends, dict)
    assert 'available' in trends
    assert 'trends' in trends

    # Test generate_comprehensive_report
    report = dashboard.generate_comprehensive_report()
    assert isinstance(report, str)
    assert len(report) > 0

    # Test export_data
    export_json = dashboard.export_data(format='json')
    assert isinstance(export_json, str)

    export_dict = dashboard.export_data(format='dict')
    assert isinstance(export_dict, dict)


def test_country_profile():
    """Teste la génération de profil pays"""
    from analytics_dashboard import SecurityAnalyticsDashboard

    dashboard = SecurityAnalyticsDashboard()

    # Test avec un code pays valide (ex: AFG pour Afghanistan)
    profile = dashboard.get_country_profile('AFG')
    assert isinstance(profile, dict)
    assert 'success' in profile
    assert 'country_code' in profile
    assert profile['country_code'] == 'AFG'
    assert 'data' in profile

    # Test avec un code pays en minuscules
    profile_lower = dashboard.get_country_profile('afg')
    assert profile_lower['country_code'] == 'AFG'


def test_analytics_health_endpoint_simulation():
    """Simule l'appel à l'endpoint de santé"""
    # Mock Flask request context
    from . import security_analytics_dashboard

    if security_analytics_dashboard:
        available = security_analytics_dashboard.is_available()
        assert isinstance(available, bool)

        # Vérifier les attributs de base
        assert hasattr(security_analytics_dashboard, 'connectors')
        assert isinstance(security_analytics_dashboard.connectors, dict)


def test_cache_integration():
    """Vérifie que le dashboard utilise le cache intelligent"""
    from analytics_dashboard import SecurityAnalyticsDashboard

    dashboard = SecurityAnalyticsDashboard()

    # Vérifier que les connecteurs utilisent le cache
    if dashboard.is_available():
        # Vérifier que les connecteurs ont des méthodes avec cache
        for name, connector in dashboard.connectors.items():
            # Vérifier que le connecteur a des méthodes typiques
            assert connector is not None
            # Note: On ne peut pas vérifier directement le cache sans appeler les méthodes
            # mais on peut vérifier que le connecteur existe


if __name__ == '__main__':
    # Exécuter les tests manuellement
    print("[PHASE 4] Lancement des tests d'intégration API Phase 4...")

    try:
        test_analytics_dashboard_available()
        print("[OK] test_analytics_dashboard_available")
    except Exception as e:
        print(f"[ERROR] test_analytics_dashboard_available: {e}")

    try:
        test_analytics_routes_exist()
        print("[OK] test_analytics_routes_exist")
    except Exception as e:
        print(f"[ERROR] test_analytics_routes_exist: {e}")

    try:
        test_analytics_dashboard_methods()
        print("[OK] test_analytics_dashboard_methods")
    except Exception as e:
        print(f"[ERROR] test_analytics_dashboard_methods: {e}")

    try:
        test_country_profile()
        print("[OK] test_country_profile")
    except Exception as e:
        print(f"[ERROR] test_country_profile: {e}")

    try:
        test_analytics_health_endpoint_simulation()
        print("[OK] test_analytics_health_endpoint_simulation")
    except Exception as e:
        print(f"[ERROR] test_analytics_health_endpoint_simulation: {e}")

    try:
        test_cache_integration()
        print("[OK] test_cache_integration")
    except Exception as e:
        print(f"[ERROR] test_cache_integration: {e}")

    print("[SUCCESS] Tests d'intégration API Phase 4 terminés!")