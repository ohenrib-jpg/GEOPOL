"""
Test ultra-simple de Gallica
"""

import requests

print("="*70)
print("🧪 TEST CONNEXION GALLICA BASIQUE")
print("="*70)

# Test 1: Page d'accueil
print("\n1️⃣ Test page d'accueil...")
try:
    r = requests.get("https://gallica.bnf.fr", timeout=10)
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        print("   ✅ Gallica accessible")
    else:
        print(f"   ⚠️ Status inhabituel: {r.status_code}")
except Exception as e:
    print(f"   ❌ Erreur: {e}")

# Test 2: API SRU basique (celle qui pose problème)
print("\n2️⃣ Test API SRU (celle qui échoue)...")
try:
    url = "https://gallica.bnf.fr/services/engine/search/sru"
    params = {
        'operation': 'searchRetrieve',
        'version': '1.2',
        'query': 'dc.title all "France"',
        'maximumRecords': 1
    }
    
    r = requests.get(url, params=params, timeout=15)
    print(f"   Status: {r.status_code}")
    
    if r.status_code == 200:
        print("   ✅ API SRU fonctionne !")
        print(f"   Réponse: {r.text[:200]}...")
    else:
        print(f"   ❌ API SRU échoue (status {r.status_code})")
        print(f"   Erreur: {r.text[:200]}")
except Exception as e:
    print(f"   ❌ Exception: {e}")

# Test 3: URL directe d'un document connu
print("\n3️⃣ Test accès document direct...")
try:
    # ARK d'un document connu
    r = requests.get("https://gallica.bnf.fr/ark:/12148/bpt6k1200378", timeout=10)
    print(f"   Status: {r.status_code}")
    if r.status_code in [200, 301, 302]:
        print("   ✅ Accès direct aux documents fonctionne")
    else:
        print(f"   ⚠️ Status: {r.status_code}")
except Exception as e:
    print(f"   ❌ Erreur: {e}")

print("\n" + "="*70)
print("📊 DIAGNOSTIC")
print("="*70)
print("""
L'API SRU de Gallica a des problèmes bien connus:
- Syntaxe très stricte et mal documentée
- Erreurs 500 fréquentes
- Instabilité générale

SOLUTIONS:
1. ✅ Mode hybride: API + références simulées
2. ✅ Scraping léger de l'interface web
3. ✅ Utiliser uniquement Archive.org pour l'instant

RECOMMANDATION:
→ Activer le mode "références indicatives" de Gallica
→ Permet de montrer des documents pertinents même si l'API échoue
→ Archive.org reste la source principale fiable
""")
print("="*70)
