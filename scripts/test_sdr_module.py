# Flask/scripts/test_sdr_module.py
"""
Script de test du module SDR
"""

import sys
from pathlib import Path

# Ajouter le chemin du projet
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_sdr_connection():
    """Teste la connexion aux serveurs SDR"""
    
    print("=" * 60)
    print("TEST CONNEXION SDR")
    print("=" * 60)
    
    try:
        from geopol_data.connectors.sdr_spectrum_service import SDRSpectrumService
        from geopol_data.sdr_config import SDR_CONFIG
        
        print(f"Mode SDR: {SDR_CONFIG['mode']}")
        
        # Créer un service de test
        class MockDBManager:
            def get_connection(self):
                import sqlite3
                return sqlite3.connect(':memory:')
        
        db_manager = MockDBManager()
        service = SDRSpectrumService(db_manager)
        
        # Tester la découverte des serveurs
        print("\n🔍 Test découverte serveurs...")
        servers = service.discover_active_servers()
        
        print(f"\n📡 Serveurs actifs: {len(servers)}")
        for server in servers:
            status = "✅" if server.get('status') == 'active' else "❌"
            print(f"  {status} {server['name']} ({server['location']})")
        
        # Tester un scan simple
        if servers:
            print("\n📊 Test scan fréquence...")
            try:
                # Scanner une fréquence test
                result = service.scan_frequency(6000, 'broadcast')
                if result.get('success'):
                    print(f"  ✅ Scan réussi: {result['peak_count']} pics, {result['power_db']} dB")
                else:
                    print(f"  ❌ Scan échoué: {result.get('error', 'Unknown')}")
            except Exception as e:
                print(f"  ⚠️  Erreur scan: {e}")
        
        # Tester le dashboard
        print("\n📈 Test dashboard...")
        dashboard = service.get_dashboard_data()
        if dashboard.get('success'):
            stats = dashboard.get('stats', {})
            print(f"  ✅ Dashboard: {stats.get('total_frequencies', 0)} fréquences")
            print(f"     Anomalies: {stats.get('anomalies_count', 0)}")
            print(f"     Données réelles: {dashboard.get('real_data', False)}")
        
        print("\n" + "=" * 60)
        print("TEST TERMINÉ")
        
        return len(servers) > 0
        
    except Exception as e:
        print(f"\n❌ Erreur test SDR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_sdr_analyzer():
    """Teste l'analyseur SDR géopolitique"""
    
    print("\n" + "=" * 60)
    print("TEST ANALYSEUR SDR GÉOPOLITIQUE")
    print("=" * 60)
    
    try:
        from geopol_data.sdr_analyzer import SDRAnalyzer
        
        class MockDBManager:
            def get_connection(self):
                import sqlite3
                return sqlite3.connect(':memory:')
        
        db_manager = MockDBManager()
        analyzer = SDRAnalyzer(db_manager)
        
        # Tester avec des données simulées
        scan_data = [
            {
                'frequency_khz': 4625,
                'power_db': -65,
                'bandwidth_khz': 5,
                'timestamp': '2024-01-15T10:00:00Z',
                'latitude': 55.7558,
                'longitude': 37.6173,
                'country_code': 'RU'
            },
            {
                'frequency_khz': 11175,
                'power_db': -70,
                'bandwidth_khz': 5,
                'timestamp': '2024-01-15T10:00:00Z',
                'latitude': 38.9072,
                'longitude': -77.0369,
                'country_code': 'US'
            }
        ]
        
        print("\n📊 Traitement données SDR...")
        metrics = analyzer.process_scan_data(scan_data)
        
        print(f"\n📈 Métriques générées: {len(metrics)} zones")
        for zone_id, zone_metrics in metrics.items():
            print(f"\n  Zone: {zone_id}")
            print(f"    Statut: {zone_metrics.get_health_status().value}")
            print(f"    Activité: {zone_metrics.total_activity:.2f}")
            print(f"    Risque géopolitique: {zone_metrics.geopolitical_risk:.1f}")
        
        # Tester la corrélation NER
        print("\n🤝 Test corrélation NER...")
        ner_entities = {
            'locations': ['Moscou', 'Russie', 'Ukraine'],
            'organizations': ['OTAN', 'Ministère de la Défense'],
            'persons': ['Poutine', 'Biden']
        }
        
        correlations = analyzer.correlate_with_ner_entities(ner_entities)
        print(f"  Corrélations trouvées: {correlations['correlations_found']}")
        
        print("\n" + "=" * 60)
        print("TEST ANALYSEUR TERMINÉ")
        
        return len(metrics) > 0
        
    except Exception as e:
        print(f"\n❌ Erreur analyseur SDR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    # Tester la connexion
    connection_ok = test_sdr_connection()
    
    # Tester l'analyseur
    analyzer_ok = test_sdr_analyzer()
    
    print("\n" + "=" * 60)
    print("RÉCAPITULATIF TESTS")
    print("=" * 60)
    print(f"Connexion SDR: {'✅ OK' if connection_ok else '❌ ÉCHEC'}")
    print(f"Analyseur SDR: {'✅ OK' if analyzer_ok else '❌ ÉCHEC'}")
    
    if connection_ok and analyzer_ok:
        print("\n🎉 Module SDR prêt pour l'intégration !")
    else:
        print("\n⚠️  Des problèmes ont été détectés")
        print("\nActions recommandées:")
        if not connection_ok:
            print("  • Vérifier la connexion Internet")
            print("  • Activer le mode simulation: export GEOPOL_REAL_MODE=false")
        if not analyzer_ok:
            print("  • Exécuter le script de migration: python Flask/scripts/migrate_sdr_tables.py")