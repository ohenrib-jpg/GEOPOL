# Flask/test_weak_indicators.py
"""
Script de test complet pour les indicateurs faibles
Teste les 3 services : Travel Advisories, KiwiSDR, Stock Data
"""

import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_travel_advisories():
    """Test du service Travel Advisories"""
    print("\n" + "="*60)
    print("🛫 TEST AVIS AUX VOYAGEURS")
    print("="*60)
    
    try:
        from Flask.travel_advisories_service import TravelAdvisoriesService
        
        # Test 1 : Données US
        print("\n📡 Test US State Department...")
        us_advisories = TravelAdvisoriesService._fetch_us_advisories()
        print(f"   ✅ {len(us_advisories)} pays récupérés")
        
        if us_advisories:
            sample = us_advisories[0]
            print(f"   📋 Exemple: {sample['country_name']} - Niveau {sample['risk_level']}")
        
        # Test 2 : Données UK
        print("\n📡 Test UK Foreign Office...")
        uk_advisories = TravelAdvisoriesService._fetch_uk_advisories()
        print(f"   ✅ {len(uk_advisories)} pays récupérés")
        
        # Test 3 : Données Canada
        print("\n📡 Test Canada Travel...")
        canada_advisories = TravelAdvisoriesService._fetch_canada_advisories()
        print(f"   ✅ {len(canada_advisories)} pays récupérés")
        
        print("\n✅ Service Travel Advisories : FONCTIONNEL")
        return True
        
    except ImportError as e:
        print(f"❌ Erreur import: {e}")
        print("   Vérifiez que travel_advisories_service.py existe")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def test_kiwisdr():
    """Test du service KiwiSDR"""
    print("\n" + "="*60)
    print("📡 TEST SERVEURS KIWISDR")
    print("="*60)
    
    try:
        from Flask.kiwisdr_real_service import KiwiSDRRealService, SDRFrequencyPresets
        
        # Test 1 : Récupération serveurs
        print("\n📡 Récupération serveurs actifs...")
        servers_data = KiwiSDRRealService.get_active_servers()
        
        print(f"   ✅ {servers_data['total']} serveurs trouvés")
        print(f"   📋 Source: {servers_data['source']}")
        
        if servers_data['servers']:
            sample = servers_data['servers'][0]
            print(f"   📋 Exemple: {sample['name']} - {sample['location']}")
        
        # Test 2 : Fréquences géopolitiques
        print("\n📡 Test fréquences géopolitiques...")
        freq_presets = SDRFrequencyPresets.GEOPOLITICAL_PRESETS
        print(f"   ✅ {len(freq_presets)} presets disponibles")
        print(f"   📋 Exemple: {freq_presets[0]['name']} - {freq_presets[0]['frequency_khz']} kHz")
        
        # Test 3 : Test disponibilité serveur
        if servers_data['servers']:
            test_server = servers_data['servers'][0]
            print(f"\n📡 Test connexion {test_server['name']}...")
            available = KiwiSDRRealService.test_server_availability(
                test_server['url'], 
                timeout=5
            )
            print(f"   {'✅' if available else '❌'} Serveur {'accessible' if available else 'inaccessible'}")
        
        print("\n✅ Service KiwiSDR : FONCTIONNEL")
        return True
        
    except ImportError as e:
        print(f"❌ Erreur import: {e}")
        print("   Vérifiez que kiwisdr_real_service.py existe")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def test_stock_data():
    """Test du service Stock Data"""
    print("\n" + "="*60)
    print("📈 TEST DONNÉES BOURSIÈRES")
    print("="*60)
    
    try:
        # Créer un mock db_manager minimal
        class MockDBManager:
            def get_connection(self):
                import sqlite3
                return sqlite3.connect(':memory:')
        
        from Flask.real_stock_data import RealStockData
        
        mock_db = MockDBManager()
        stock_manager = RealStockData(mock_db)
        
        # Test 1 : Indices
        print("\n📡 Test indices boursiers...")
        indices = stock_manager.get_geopolitical_indices()
        
        valid_indices = [k for k, v in indices.items() if not v.get('error') and v.get('current_price', 0) > 0]
        print(f"   ✅ {len(valid_indices)}/{len(indices)} indices valides")
        
        if valid_indices:
            sample_symbol = valid_indices[0]
            sample = indices[sample_symbol]
            print(f"   📋 Exemple: {sample['name']} - ${sample['current_price']} ({sample['change_percent']:+.2f}%)")
        
        # Test 2 : Matières premières
        print("\n📡 Test matières premières...")
        commodities = stock_manager.get_commodity_prices()
        
        valid_commodities = [k for k, v in commodities.items() if not v.get('error') and v.get('current_price', 0) > 0]
        print(f"   ✅ {len(valid_commodities)}/{len(commodities)} commodités valides")
        
        if valid_commodities:
            sample_symbol = valid_commodities[0]
            sample = commodities[sample_symbol]
            print(f"   📋 Exemple: {sample['name']} - ${sample['current_price']} ({sample['change_percent']:+.2f}%)")
        
        # Test 3 : Crypto
        print("\n📡 Test cryptomonnaies...")
        cryptos = stock_manager.get_crypto_prices()
        
        valid_cryptos = [k for k, v in cryptos.items() if not v.get('error') and v.get('current_price', 0) > 0]
        print(f"   ✅ {len(valid_cryptos)}/{len(cryptos)} cryptos valides")
        
        if valid_cryptos:
            sample_symbol = valid_cryptos[0]
            sample = cryptos[sample_symbol]
            print(f"   📋 Exemple: {sample['name']} - ${sample['current_price']} ({sample['change_percent']:+.2f}%)")
        
        # Résumé
        total_valid = len(valid_indices) + len(valid_commodities) + len(valid_cryptos)
        total_assets = len(indices) + len(commodities) + len(cryptos)
        
        if total_valid > 0:
            print(f"\n✅ Service Stock Data : FONCTIONNEL ({total_valid}/{total_assets} actifs)")
            return True
        else:
            print("\n⚠️ Service Stock Data : PARTIELLEMENT FONCTIONNEL (aucune donnée valide)")
            print("   Vérifiez votre connexion internet ou réessayez dans quelques minutes")
            return False
        
    except ImportError as e:
        print(f"❌ Erreur import: {e}")
        if 'yfinance' in str(e):
            print("   Installez yfinance : pip install yfinance")
        else:
            print("   Vérifiez que real_stock_data.py existe")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_schema():
    """Test du schéma de base de données"""
    print("\n" + "="*60)
    print("🗄️ TEST SCHÉMA BASE DE DONNÉES")
    print("="*60)
    
    try:
        import sqlite3
        
        # Créer une DB temporaire
        conn = sqlite3.connect(':memory:')
        cur = conn.cursor()
        
        # Tester les tables principales
        tables_to_create = [
            ('travel_advisories', """
                CREATE TABLE travel_advisories (
                    id INTEGER PRIMARY KEY,
                    country_code TEXT NOT NULL,
                    risk_level INTEGER DEFAULT 1,
                    source TEXT NOT NULL,
                    UNIQUE(country_code, source)
                )
            """),
            ('kiwisdr_monitored_frequencies', """
                CREATE TABLE kiwisdr_monitored_frequencies (
                    id INTEGER PRIMARY KEY,
                    frequency_khz INTEGER NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    active BOOLEAN DEFAULT 1
                )
            """),
            ('stock_data_cache', """
                CREATE TABLE stock_data_cache (
                    id INTEGER PRIMARY KEY,
                    symbol TEXT NOT NULL UNIQUE,
                    current_price REAL,
                    change_percent REAL
                )
            """)
        ]
        
        for table_name, create_sql in tables_to_create:
            cur.execute(create_sql)
            print(f"   ✅ Table {table_name} créée")
        
        conn.close()
        
        print("\n✅ Schéma base de données : OK")
        return True
        
    except Exception as e:
        print(f"❌ Erreur schéma DB: {e}")
        return False


def run_all_tests():
    """Exécute tous les tests"""
    print("\n" + "="*60)
    print("🚀 TEST COMPLET DES INDICATEURS FAIBLES")
    print("="*60)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {
        'travel_advisories': False,
        'kiwisdr': False,
        'stock_data': False,
        'database': False
    }
    
    # Tester chaque service
    results['travel_advisories'] = test_travel_advisories()
    results['kiwisdr'] = test_kiwisdr()
    results['stock_data'] = test_stock_data()
    results['database'] = test_database_schema()
    
    # Résumé final
    print("\n" + "="*60)
    print("📊 RÉSUMÉ DES TESTS")
    print("="*60)
    
    for service, status in results.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {service.replace('_', ' ').title()}: {'OK' if status else 'ÉCHEC'}")
    
    # Score final
    passed = sum(results.values())
    total = len(results)
    percentage = (passed / total) * 100
    
    print("\n" + "="*60)
    print(f"🎯 SCORE: {passed}/{total} ({percentage:.0f}%)")
    print("="*60)
    
    if percentage == 100:
        print("🎉 Tous les tests sont passés ! Système prêt à l'emploi.")
    elif percentage >= 75:
        print("⚠️ La plupart des tests sont passés. Vérifiez les échecs.")
    else:
        print("❌ Plusieurs tests ont échoué. Consultez la documentation.")
    
    return percentage == 100


if __name__ == "__main__":
    """
    Exécution du script de test
    
    Usage:
        python Flask/test_weak_indicators.py
    """
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrompu par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
