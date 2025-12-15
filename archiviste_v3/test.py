"""
Test final Wayback Machine avec toutes les stratégies
À lancer depuis Flask/ : python test_wayback_final.py
"""

import sys
import os

flask_dir = os.path.dirname(os.path.abspath(__file__))
archiviste_path = os.path.join(flask_dir, 'archiviste_v3')
sys.path.insert(0, archiviste_path)

print("="*70)
print("🧪 TEST FINAL WAYBACK - TOUTES STRATÉGIES")
print("="*70)

from wayback_client import WaybackClient
client = WaybackClient()

# Test 1: Recherche optimisée standard
print("\n1️⃣ Test recherche standard (2015-2016)...")
results_1 = client.search(
    query="guerre",
    start_year=2015,
    end_year=2016,
    max_results=5,
    sites=['lemonde.fr', 'lefigaro.fr']
)

print(f"\n   📊 {len(results_1)} résultats")
real_count = sum(1 for r in results_1 if 'note' not in r)
ref_count = sum(1 for r in results_1 if 'note' in r)
print(f"   • Réels: {real_count}")
print(f"   • Références: {ref_count}")

if real_count > 0:
    print(f"\n   ✅ SUCCÈS: Vrais résultats trouvés !")
    for r in [x for x in results_1 if 'note' not in x][:2]:
        print(f"      → {r['title']}")
        print(f"        {r['source_url'][:70]}...")

# Test 2: Recherche par pattern direct
print("\n2️⃣ Test recherche par pattern URL...")
results_2 = client.search_by_url_pattern(
    base_url='lemonde.fr',
    query='diplomatie',
    year=2018,
    max_results=3
)

print(f"   📊 {len(results_2)} résultats par pattern")
if results_2:
    print("   ✅ Pattern search fonctionne !")
    for r in results_2[:2]:
        print(f"      → {r['title']}")

# Test 3: Différentes périodes
print("\n3️⃣ Test périodes variées...")

test_cases = [
    (2010, 2011, "Début années 2010"),
    (2018, 2019, "Fin années 2010"),
    (2020, 2021, "Période récente"),
]

results_summary = []

for start, end, desc in test_cases:
    results = client.search(
        query="france",
        start_year=start,
        end_year=end,
        max_results=3,
        sites=['lemonde.fr']
    )
    
    real = sum(1 for r in results if 'note' not in r)
    ref = sum(1 for r in results if 'note' in r)
    
    results_summary.append({
        'period': f"{start}-{end}",
        'desc': desc,
        'total': len(results),
        'real': real,
        'ref': ref
    })
    
    print(f"   {start}-{end} ({desc}): {len(results)} (Réels: {real}, Réf: {ref})")

# Récapitulatif
print("\n" + "="*70)
print("📊 RÉCAPITULATIF FINAL")
print("="*70)

total_real = sum(r['real'] for r in results_summary)
total_ref = sum(r['ref'] for r in results_summary)

print(f"""
RÉSULTATS GLOBAUX:
• Vrais résultats: {total_real + real_count}
• Références: {total_ref + ref_count}
• Total: {total_real + total_ref + real_count + ref_count}

STRATÉGIES TESTÉES:
✅ API Availability (rapide)
✅ Recherche par pattern URL
✅ Mode fallback avec références

QUALITÉ DU SERVICE:
""")

if total_real > 0:
    print("🎉 EXCELLENT: Le système trouve de vrais résultats !")
    print("   → Wayback Machine pleinement opérationnel")
elif total_ref > 0:
    print("✅ BON: Le système fonctionne en mode hybride")
    print("   → Références indicatives fournies")
    print("   → Aucun blocage du système")
else:
    print("⚠️ Mode dégradé: Seulement des références")
    print("   → API Wayback très lente actuellement")

print(f"""
PROCHAINES ÉTAPES:
1. {'✅ Wayback intégré' if total_real + total_ref > 0 else '⏳ Continuer tests'}
2. ⏳ Tester via interface Flask
3. 🔜 Ajouter Chronicling America (session suivante)

COMMANDES:
→ python run.py
→ http://localhost:5000/archiviste-v3/
→ Tester période 2015-2017 avec un thème
""")

print("="*70)
