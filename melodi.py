# test_api_melodi.py - Script de test de l'API Melodi
"""
Script pour tester la connexion à l'API INSEE Melodi
Usage: python test_api_melodi.py
"""

import requests
import json
from datetime import datetime

class MelodiAPITester:
    def __init__(self):
        self.base_url = 'https://api.insee.fr/melodi/donnees/v1'
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json'
        })
    
    def test_dataflow(self, dataflow_id, description):
        """Test un dataflow spécifique"""
        print(f"\n{'='*60}")
        print(f"🔍 Test: {description}")
        print(f"   Dataflow: {dataflow_id}")
        print(f"{'='*60}")
        
        try:
            url = f"{self.base_url}/{dataflow_id}"
            params = {
                'detail': 'full',
                'format': 'json'
            }
            
            print(f"📡 URL: {url}")
            print(f"   Params: {params}")
            
            response = self.session.get(url, params=params, timeout=30)
            
            print(f"📊 Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Analyser la structure
                print("✅ Réponse reçue!")
                print(f"   Taille: {len(json.dumps(data))} caractères")
                
                # Essayer d'extraire des observations
                try:
                    datasets = data.get('data', {}).get('dataSets', [])
                    if datasets:
                        dataset = datasets[0]
                        series = dataset.get('series', {})
                        obs_count = sum(len(s.get('observations', {})) for s in series.values())
                        print(f"   📈 {len(series)} séries, {obs_count} observations")
                        
                        # Afficher un échantillon
                        if series:
                            first_series = list(series.values())[0]
                            first_obs = list(first_series.get('observations', {}).values())[0]
                            print(f"   📝 Exemple valeur: {first_obs}")
                    else:
                        print("   ⚠️  Pas de datasets trouvés")
                        
                except Exception as e:
                    print(f"   ⚠️  Erreur parsing: {e}")
                
                return True
            else:
                print(f"❌ Erreur {response.status_code}")
                print(f"   Message: {response.text[:200]}")
                return False
                
        except requests.exceptions.Timeout:
            print("❌ Timeout de la requête")
            return False
        except requests.exceptions.ConnectionError:
            print("❌ Erreur de connexion")
            return False
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return False
    
    def list_available_dataflows(self):
        """Liste les dataflows disponibles (endpoint de découverte)"""
        print(f"\n{'='*60}")
        print("📋 Recherche des dataflows disponibles")
        print(f"{'='*60}")
        
        try:
            # L'API Melodi expose un endpoint de métadonnées
            url = f"{self.base_url.replace('/donnees/v1', '')}/dataflow"
            
            print(f"📡 URL: {url}")
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                print("✅ Liste des dataflows récupérée")
                # Parser et afficher les premiers dataflows
                data = response.json()
                print(json.dumps(data, indent=2)[:500])
            else:
                print(f"⚠️  Endpoint metadata non accessible ({response.status_code})")
                
        except Exception as e:
            print(f"⚠️  Erreur: {e}")
    
    def run_full_test(self):
        """Exécute tous les tests"""
        print("\n" + "="*60)
        print("🚀 TESTS API INSEE MELODI")
        print(f"   Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        # Tests des dataflows connus
        tests = [
            ("CNT-2020-PIB-EQB-RF", "PIB Trimestriel"),
            ("CHOMAGE-TRIM-NATIONAL", "Chômage Trimestriel"),
            ("IPC-2015-COICOP", "Indice Prix Consommation"),
        ]
        
        results = []
        for dataflow, desc in tests:
            success = self.test_dataflow(dataflow, desc)
            results.append((desc, success))
        
        # Résumé
        print(f"\n{'='*60}")
        print("📊 RÉSUMÉ DES TESTS")
        print(f"{'='*60}")
        
        for desc, success in results:
            status = "✅" if success else "❌"
            print(f"{status} {desc}")
        
        success_count = sum(1 for _, s in results if s)
        print(f"\n✅ {success_count}/{len(results)} tests réussis")
        
        # Recommandations
        print(f"\n{'='*60}")
        print("💡 RECOMMANDATIONS")
        print(f"{'='*60}")
        
        if success_count == 0:
            print("❌ Aucun test réussi:")
            print("   1. Vérifiez votre connexion internet")
            print("   2. L'API Melodi pourrait être temporairement indisponible")
            print("   3. Les identifiants de dataflow ont peut-être changé")
            print("   4. Consultez: https://api.insee.fr/melodi")
        elif success_count < len(results):
            print("⚠️  Certains tests ont échoué:")
            print("   1. Certains dataflows peuvent ne pas être accessibles publiquement")
            print("   2. Vérifiez les identifiants de dataflow dans la documentation")
            print("   3. L'application utilisera des données simulées en fallback")
        else:
            print("✅ Tous les tests ont réussi!")
            print("   L'API Melodi est pleinement fonctionnelle")
            print("   Votre application peut récupérer les données en temps réel")

def main():
    """Fonction principale"""
    tester = MelodiAPITester()
    
    # Exécuter les tests
    tester.run_full_test()
    
    # Essayer de lister les dataflows disponibles
    # tester.list_available_dataflows()
    
    print("\n" + "="*60)
    print("✅ Tests terminés")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
