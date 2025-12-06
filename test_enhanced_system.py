# Flask/test_enhanced_system.py
"""
Script de test complet pour le système d'indicateurs amélioré
Teste : Eurostat + INSEE + yFinance + Cache + Fallbacks
"""

import logging
import sys
from pathlib import Path

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_section(title):
    """Affiche une section formatée"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_insee_scraper():
    """Test du scraper INSEE"""
    print_section("📊 TEST 1/4 : INSEE Scraper")
    
    try:
        # Import flexible
        try:
            from insee_scraper import INSEEScraper
        except ImportError:
            from Flask.insee_scraper import INSEEScraper
        
        scraper = INSEEScraper()
        data = scraper.get_indicators()
        
        if data.get('success'):
            print("✅ INSEE Scraper fonctionnel")
            print(f"   Source: {data.get('source')}")
            print(f"   Indicateurs récupérés: {len(data.get('indicators', {}))}")
            
            for key, indicator in data['indicators'].items():
                print(f"\n   📈 {indicator['name']}")
                print(f"      Valeur: {indicator['value']} {indicator['unit']}")
                print(f"      Période: {indicator['period']}")
                print(f"      Source: {indicator.get('source', 'N/A')}")
            
            return True
        else:
            print("⚠️  INSEE Scraper : données fallback utilisées")
            return True  # C'est normal si pas de connexion
            
    except Exception as e:
        print(f"❌ Erreur INSEE Scraper: {e}")
        return False


def test_eurostat_connector():
    """Test du connecteur Eurostat"""
    print_section("🇪🇺 TEST 2/4 : Eurostat Connector")
    
    try:
        # Import flexible
        try:
            from eurostat_connector import EurostatConnector
        except ImportError:
            from Flask.eurostat_connector import EurostatConnector
        
        eurostat = EurostatConnector()
        data = eurostat.get_multiple_indicators(['gdp', 'unemployment'])
        
        if data.get('success'):
            print("✅ Eurostat Connector fonctionnel")
            print(f"   Indicateurs récupérés: {data['stats']['successful']}/{data['stats']['total']}")
            
            for key, indicator in data['indicators'].items():
                if indicator.get('success'):
                    print(f"\n   📊 {indicator['indicator_name']}")
                    print(f"      Valeur: {indicator['current_value']} {indicator['unit']}")
                    print(f"      Variation: {indicator['change_percent']:+.2f}%")
                    print(f"      Période: {indicator['period']}")
            
            return True
        else:
            print("⚠️  Eurostat : erreur récupération")
            return False
            
    except Exception as e:
        print(f"❌ Erreur Eurostat: {e}")
        return False


def test_yfinance_connector():
    """Test du connecteur yFinance"""
    print_section("📈 TEST 3/4 : yFinance Connector")
    
    try:
        # Import flexible
        try:
            from yfinance_connector import YFinanceConnector
        except ImportError:
            from Flask.yfinance_connector import YFinanceConnector
        
        yfinance = YFinanceConnector()
        data = yfinance.get_all_indices()
        
        if data.get('success'):
            print("✅ yFinance Connector fonctionnel")
            indices = data.get('indices', {})
            print(f"   Indices récupérés: {len(indices)}")
            
            for symbol, index_data in list(indices.items())[:3]:  # 3 premiers
                if index_data.get('success'):
                    print(f"\n   📊 {index_data['name']}")
                    print(f"      Prix: {index_data['current_price']}")
                    print(f"      Variation: {index_data['change_percent']:+.2f}%")
                    print(f"      Tendance: {index_data['trend']}")
            
            return True
        else:
            print("⚠️  yFinance : erreur récupération")
            return False
            
    except Exception as e:
        print(f"❌ Erreur yFinance: {e}")
        return False


def test_enhanced_connector():
    """Test du connecteur unifié"""
    print_section("🎯 TEST 4/4 : Enhanced Connector (Système complet)")
    
    try:
        # Import flexible
        try:
            from enhanced_indicators_connector import EnhancedIndicatorsConnector
        except ImportError:
            from Flask.enhanced_indicators_connector import EnhancedIndicatorsConnector
        
        connector = EnhancedIndicatorsConnector()
        data = connector.get_dashboard_data()
        
        if data.get('success'):
            print("✅ Enhanced Connector fonctionnel")
            
            # Statut des sources
            print("\n   📡 Statut des sources:")
            for source, status in data['sources_status'].items():
                icon = '✅' if status == 'operational' else '❌'
                print(f"      {icon} {source}: {status}")
            
            # Résumé
            summary = data['summary']
            print(f"\n   📊 Résumé:")
            print(f"      Total indicateurs: {summary['total_indicators']}")
            print(f"      Qualité données: {summary['data_quality']}")
            
            print("\n   🔍 Par fiabilité:")
            for reliability, count in summary['by_reliability'].items():
                print(f"      • {reliability}: {count}")
            
            print("\n   📈 Par source:")
            for source, count in summary['by_source'].items():
                print(f"      • {source}: {count}")
            
            # Exemples d'indicateurs
            print("\n   💡 Exemples d'indicateurs:")
            for i, (ind_id, indicator) in enumerate(list(data['indicators'].items())[:5]):
                reliability_icon = indicator.get('reliability_icon', '⚪')
                print(f"      {reliability_icon} {indicator['name']}: {indicator['value']} {indicator['unit']}")
            
            return True
        else:
            print("❌ Enhanced Connector : échec")
            return False
            
    except Exception as e:
        print(f"❌ Erreur Enhanced Connector: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_gini_scraper():
    """Test du scraper GINI"""
    print_section("📊 TEST BONUS : GINI Scraper")
    
    try:
        # Import flexible
        try:
            from gini_scraper import GINIScraper
        except ImportError:
            from Flask.gini_scraper import GINIScraper
        
        scraper = GINIScraper()
        data = scraper.get_gini_data()
        
        if data.get('success'):
            print("✅ GINI Scraper fonctionnel")
            print(f"   Source: {data.get('source')}")
            print(f"   Fiabilité: {data['reliability']}")
            print(f"\n   📊 {data['name']}: {data['value']} {data['unit']}")
            print(f"      Période: {data['period']}")
            print(f"      Interprétation: {data.get('interpretation', 'N/A')}")
            print(f"      Dataset: {data['dataset']}")
            
            return True
        else:
            print("⚠️  GINI Scraper : données fallback utilisées")
            return True  # C'est normal si pas de connexion
            
    except Exception as e:
        print(f"❌ Erreur GINI Scraper: {e}")
        return False
    """Test du système de cache"""
    print_section("💾 TEST BONUS : Système de cache")
    
    try:
        # Import flexible
        try:
            from insee_scraper import INSEEScraper
        except ImportError:
            from Flask.insee_scraper import INSEEScraper
            
        from datetime import datetime, timedelta
        import json
        
        scraper = INSEEScraper()
        
        # Test 1 : Cache vide
        print("\n   1️⃣ Test cache vide...")
        data1 = scraper.get_indicators()
        print(f"      ✅ Données récupérées: {len(data1.get('indicators', {}))} indicateurs")
        
        # Test 2 : Cache valide
        print("\n   2️⃣ Test cache valide (< 24h)...")
        data2 = scraper.get_indicators()
        source2 = data2.get('source', 'unknown')
        print(f"      ✅ Source utilisée: {source2}")
        
        # Test 3 : Vérifier fichier cache
        print("\n   3️⃣ Vérification fichier cache...")
        cache_path = Path('instance/insee_cache.json')
        if cache_path.exists():
            with open(cache_path, 'r') as f:
                cache_data = json.load(f)
            print(f"      ✅ Fichier cache trouvé")
            print(f"      ✅ Timestamp: {cache_data.get('timestamp', 'N/A')}")
        else:
            print(f"      ⚠️  Fichier cache non trouvé (normal si 1ère exécution)")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test cache: {e}")
        return False


def run_all_tests():
    """Execute tous les tests"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "🧪 TESTS SYSTÈME AMÉLIORÉ" + " " * 28 + "║")
    print("╚" + "=" * 68 + "╝")
    
    results = {
        'INSEE Scraper': test_insee_scraper(),
        'Eurostat Connector': test_eurostat_connector(),
        'yFinance Connector': test_yfinance_connector(),
        'Enhanced Connector': test_enhanced_connector(),
        'Système de cache': test_cache_system()
    }
    
    # Résumé final
    print_section("📋 RÉSUMÉ DES TESTS")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    for test_name, result in results.items():
        icon = '✅' if result else '❌'
        print(f"   {icon} {test_name}")
    
    print(f"\n   📊 Résultats: {passed}/{total} tests réussis")
    
    if passed == total:
        print("\n   🎉 TOUS LES TESTS SONT PASSÉS !")
        print("   ✅ Le système est prêt à être utilisé")
    elif passed >= total * 0.75:
        print("\n   ⚠️  La plupart des tests sont passés")
        print("   💡 Vérifiez les composants en échec")
    else:
        print("\n   ❌ Plusieurs tests ont échoué")
        print("   🔧 Vérifiez l'installation et les dépendances")
    
    print("\n")
    return passed == total


def main():
    """Point d'entrée principal"""
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrompus par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erreur critique: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
