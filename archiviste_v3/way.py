"""
Test rapide Wayback Machine - Version optimisée
À lancer depuis Flask/ : python test_wayback_simple.py
"""

import sys
import os

flask_dir = os.path.dirname(os.path.abspath(__file__))
archiviste_path = os.path.join(flask_dir, 'archiviste_v3')
sys.path.insert(0, archiviste_path)

print("="*70)
print("🧪 TEST WAYBACK - VERSION RAPIDE")
print("="*70)

# Import
from wayback_client import WaybackClient
client = WaybackClient()

# Test 1: Connexion basique
print("\n1️⃣ Test connexion...")
if client.test_connection():
    print("   ✅ Wayback accessible")

# Test 2: Recherche optimisée (courte période)
print("\n2️⃣ Test recherche optimisée...")
try:
    results = client.search(
        query="guerre",
        start_year=2015,
        end_year=2016,  # Juste 1-2 ans
        max_results=5,
        sites=['lemonde.fr', 'lefigaro.fr']  # Seulement 2 sites
    )
    
    print(f"   ✅ {len(results)} résultats")
    
    if results:
        print("\n   📄 Exemples:")
        for i, r in enumerate(results[:3], 1):
            print(f"      {i}. {r['title']}")
            print(f"         {r['source_url'][:70]}...")
            if 'note' in r:
                print(f"         {r['note']}")
    else:
        print("   ⚠️ Aucun résultat (API lente ou période sans données)")
        
except Exception as e:
    print(f"   ❌ Erreur: {e}")

# Test 3: Vérification availability API
print("\n3️⃣ Test API Availability (rapide)...")
try:
    import requests
    
    response = requests.get(
        'https://archive.org/wayback/available',
        params={'url': 'lemonde.fr'},
        timeout=5
    )
    
    if response.status_code == 200:
        data = response.json()
        if data.get('archived_snapshots'):
            print("   ✅ API Availability fonctionne")
            snapshot = data['archived_snapshots'].get('closest', {})
            if snapshot:
                print(f"   📸 Dernier snapshot: {snapshot.get('timestamp', 'N/A')}")
        else:
            print("   ⚠️ Pas de snapshot pour lemonde.fr")
    else:
        print(f"   ⚠️ Status: {response.status_code}")
        
except Exception as e:
    print(f"   ❌ Erreur: {e}")

print("\n" + "="*70)
print("📊 DIAGNOSTIC")
print("="*70)

print("""
PROBLÈME IDENTIFIÉ:
→ L'API CDX de Wayback est TRÈS LENTE sur de grandes périodes
→ Timeout systématique sur requêtes larges

SOLUTIONS IMPLÉMENTÉES:
✅ Réduction fenêtre temporelle (1-2 ans max)
✅ Limitation à 2-5 sites ciblés
✅ Mode fallback avec archives de référence
✅ API Availability (plus rapide que CDX)
✅ Timeouts réduits (5-10s)

UTILISATION RECOMMANDÉE:
• Périodes courtes: 2-3 ans maximum
• Sites ciblés: 2-5 sites max
• Pas de scan exhaustif (trop lent)

SI PROBLÈME PERSISTE:
→ Mode "références indicatives" activé automatiquement
→ Donne des liens vers archives connues pertinentes
→ Système ne bloque jamais

PROCHAINES ÉTAPES:
1. Relancer Flask: python run.py
2. Tester interface avec période 2015-2017
3. Observer les résultats (vrais + références)
""")

print("="*70)
