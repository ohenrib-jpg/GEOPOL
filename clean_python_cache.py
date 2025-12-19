#!/usr/bin/env python3
"""
Script de nettoyage du cache Python
Résout les problèmes d'imports circulaires et de modules cachés
"""

import os
import shutil
from pathlib import Path

print("=" * 70)
print("🧹 NETTOYAGE DU CACHE PYTHON")
print("=" * 70)

# Dossier racine du projet
project_root = Path(__file__).parent

# ============================================================================
# 1. SUPPRIMER __pycache__
# ============================================================================

print("\n1️⃣ Suppression des dossiers __pycache__...")

pycache_count = 0
for pycache in project_root.rglob('__pycache__'):
    try:
        shutil.rmtree(pycache)
        print(f"   ✅ Supprimé: {pycache.relative_to(project_root)}")
        pycache_count += 1
    except Exception as e:
        print(f"   ⚠️ Erreur: {e}")

if pycache_count == 0:
    print("   ℹ️ Aucun __pycache__ trouvé")
else:
    print(f"   ✅ {pycache_count} dossiers __pycache__ supprimés")

# ============================================================================
# 2. SUPPRIMER .pyc
# ============================================================================

print("\n2️⃣ Suppression des fichiers .pyc...")

pyc_count = 0
for pyc in project_root.rglob('*.pyc'):
    try:
        pyc.unlink()
        print(f"   ✅ Supprimé: {pyc.relative_to(project_root)}")
        pyc_count += 1
    except Exception as e:
        print(f"   ⚠️ Erreur: {e}")

if pyc_count == 0:
    print("   ℹ️ Aucun .pyc trouvé")
else:
    print(f"   ✅ {pyc_count} fichiers .pyc supprimés")

# ============================================================================
# 3. SUPPRIMER .pyo
# ============================================================================

print("\n3️⃣ Suppression des fichiers .pyo...")

pyo_count = 0
for pyo in project_root.rglob('*.pyo'):
    try:
        pyo.unlink()
        print(f"   ✅ Supprimé: {pyo.relative_to(project_root)}")
        pyo_count += 1
    except Exception as e:
        print(f"   ⚠️ Erreur: {e}")

if pyo_count == 0:
    print("   ℹ️ Aucun .pyo trouvé")
else:
    print(f"   ✅ {pyo_count} fichiers .pyo supprimés")

# ============================================================================
# 4. VÉRIFIER LES FICHIERS __init__.py
# ============================================================================

print("\n4️⃣ Vérification des __init__.py...")

flask_dir = project_root / 'Flask'
geopol_dir = flask_dir / 'geopol_data'

required_inits = [
    flask_dir / '__init__.py',
    geopol_dir / '__init__.py',
    geopol_dir / 'connectors' / '__init__.py',
]

missing_inits = []
for init_file in required_inits:
    if not init_file.exists():
        missing_inits.append(init_file)
        print(f"   ⚠️ Manquant: {init_file.relative_to(project_root)}")
    else:
        print(f"   ✅ Présent: {init_file.relative_to(project_root)}")

# Créer les __init__.py manquants
if missing_inits:
    print("\n   🔧 Création des __init__.py manquants...")
    for init_file in missing_inits:
        try:
            init_file.parent.mkdir(parents=True, exist_ok=True)
            init_file.touch()
            print(f"      ✅ Créé: {init_file.relative_to(project_root)}")
        except Exception as e:
            print(f"      ❌ Erreur: {e}")

# ============================================================================
# 5. VÉRIFIER routes.py
# ============================================================================

print("\n5️⃣ Vérification de routes.py...")

routes_file = geopol_dir / 'routes.py'

if routes_file.exists():
    with open(routes_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Chercher 'return bp'
    if 'return bp' in content:
        print("   ✅ 'return bp' trouvé")
        
        # Compter les occurrences
        count = content.count('return bp')
        print(f"   ℹ️ {count} occurrence(s) de 'return bp'")
        
        # Vérifier dans create_geopol_data_blueprint
        lines = content.split('\n')
        in_function = False
        found_return = False
        
        for i, line in enumerate(lines):
            if 'def create_geopol_data_blueprint' in line:
                in_function = True
                print(f"   ✅ Fonction trouvée ligne {i+1}")
            elif in_function and 'return bp' in line:
                found_return = True
                print(f"   ✅ 'return bp' trouvé ligne {i+1}")
                print(f"      Code: {line.strip()}")
                break
            elif in_function and line.strip().startswith('def '):
                # Nouvelle fonction, on sort
                break
        
        if not found_return:
            print("   ⚠️ 'return bp' non trouvé dans create_geopol_data_blueprint()")
            print("   🔧 Correction nécessaire")
    else:
        print("   ❌ 'return bp' MANQUANT dans routes.py")
        print("   🔧 Correction URGENTE nécessaire")
else:
    print("   ❌ routes.py introuvable")

# ============================================================================
# 6. TESTER L'IMPORT
# ============================================================================

print("\n6️⃣ Test d'import...")

import sys
if str(flask_dir) not in sys.path:
    sys.path.insert(0, str(flask_dir))

try:
    # Forcer le rechargement
    if 'geopol_data' in sys.modules:
        del sys.modules['geopol_data']
    if 'geopol_data.routes' in sys.modules:
        del sys.modules['geopol_data.routes']
    if 'geopol_data.service' in sys.modules:
        del sys.modules['geopol_data.service']
    
    from geopol_data.routes import create_geopol_data_blueprint
    from geopol_data.service import DataService
    
    print("   ✅ Imports OK")
    
    # Tester la création
    class MockDB:
        pass
    
    service = DataService()
    bp = create_geopol_data_blueprint(MockDB(), service)
    
    if bp is None:
        print("   ❌ Blueprint est None après création")
    else:
        print(f"   ✅ Blueprint créé: {bp.name}")
    
except Exception as e:
    print(f"   ❌ Erreur import: {e}")
    import traceback
    traceback.print_exc()

# ============================================================================
# RÉSUMÉ
# ============================================================================

print("\n" + "=" * 70)
print("✅ NETTOYAGE TERMINÉ")
print("=" * 70)
print("\n📝 Prochaines étapes:")
print("   1. Redémarrer Python complètement")
print("   2. Redémarrer Flask: python run.py")
print("   3. Tester: curl http://localhost:5000/api/geopol/health")
print("\n⚠️ Si le problème persiste:")
print("   • Remplacer Flask/geopol_data/routes.py par la version corrigée")
print("   • Vérifier que 'return bp' est à la ligne de create_geopol_data_blueprint()")
print("=" * 70 + "\n")
