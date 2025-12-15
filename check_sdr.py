# check_sdr_system.py
"""
Vérifie que le système SDR est pleinement opérationnel
"""

import requests
import time

def test_sdr_endpoints(base_url='http://localhost:5000'):
    """Teste tous les endpoints SDR"""
    
    endpoints = [
        '/api/sdr/health',
        '/api/sdr/dashboard', 
        '/api/sdr/geojson',
        '/api/sdr/scan/6000'
    ]
    
    print("🧪 Test des endpoints SDR...")
    print("=" * 60)
    
    for endpoint in endpoints:
        url = base_url + endpoint
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                status = "✅" if data.get('success', True) else "⚠️"
                print(f"{status} {endpoint}: {response.status_code}")
                
                # Afficher quelques infos
                if endpoint == '/api/sdr/dashboard':
                    stats = data.get('stats', {})
                    print(f"   📊 {stats.get('total_frequencies', 0)} fréquences")
                    print(f"   📡 {stats.get('active_servers', 0)} serveurs")
                elif endpoint == '/api/sdr/geojson':
                    features = data.get('features', [])
                    print(f"   🗺️  {len(features)} zones SDR")
                    
            else:
                print(f"❌ {endpoint}: {response.status_code}")
                
        except requests.ConnectionError:
            print(f"🔌 {endpoint}: Serveur non disponible")
        except Exception as e:
            print(f"⚠️  {endpoint}: {str(e)[:50]}")
    
    print("=" * 60)

def test_sdr_functionality():
    """Teste la fonctionnalité SDR complète"""
    
    print("\n🔍 Test fonctionnalité SDR...")
    
    # Test 1: Simulation vs Réel
    import os
    mode = "RÉEL 🌐" if os.getenv('GEOPOL_REAL_MODE', 'false').lower() == 'true' else "SIMULATION 🧪"
    print(f"   Mode actuel: {mode}")
    
    # Test 2: Serveurs disponibles
    try:
        from Flask.geopol_data.connectors.sdr_spectrum_service import SDRSpectrumService
        
        class MockDB:
            def get_connection(self):
                import sqlite3
                return sqlite3.connect(':memory:')
        
        service = SDRSpectrumService(MockDB())
        servers = service.discover_active_servers()
        print(f"   📡 Serveurs: {len(servers)} disponibles")
        
        if servers:
            for server in servers[:3]:  # Afficher les 3 premiers
                print(f"     • {server.get('name', 'Unknown')}")
                
    except Exception as e:
        print(f"   ⚠️  Service SDR: {str(e)[:50]}")
    
    # Test 3: Analyseur
    try:
        from Flask.geopol_data.sdr_analyzer import SDRAnalyzer
        
        analyzer = SDRAnalyzer(MockDB())
        test_data = [{'frequency_khz': 6000}]
        metrics = analyzer.process_scan_data(test_data)
        print(f"   📊 Analyseur: {len(metrics)} zones traitées")
        
    except Exception as e:
        print(f"   ⚠️  Analyseur SDR: {str(e)[:50]}")

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("🚀 VÉRIFICATION SYSTÈME SDR GÉOPOLITIQUE")
    print("=" * 60)
    
    # D'abord, testons l'application en cours d'exécution
    test_sdr_endpoints()
    
    # Ensuite, testons les fonctionnalités locales
    test_sdr_functionality()
    
    print("\n" + "=" * 60)
    print("📋 RÉCAPITULATIF")
    print("=" * 60)
    print("""
Si tout est OK :
1. ✅ Les imports fonctionnent
2. ✅ Les endpoints répondent
3. ✅ Le système est prêt pour l'intégration

Prochaines étapes :
1. Ajouter la couche SDR à votre interface Leaflet
2. Configurer le rafraîchissement automatique (ex: toutes les 5 min)
3. Ajouter des corrélations avec les données géopolitiques
4. Configurer des alertes pour les anomalies SDR critiques
    """)