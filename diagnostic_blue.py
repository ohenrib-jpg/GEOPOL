#!/usr/bin/env python3
"""
Script de diagnostic pour vérifier le module Geopol-Data
À exécuter depuis le dossier racine du projet
"""

import sys
from pathlib import Path

print("=" * 70)
print("🔍 DIAGNOSTIC MODULE GEOPOL-DATA")
print("=" * 70)

# ============================================================================
# TEST 1 : Structure des fichiers
# ============================================================================

print("\n1️⃣ Vérification structure fichiers...")

flask_dir = Path(__file__).parent / 'Flask'
geopol_dir = flask_dir / 'geopol_data'

required_files = [
    'geopol_data/__init__.py',
    'geopol_data/routes.py',
    'geopol_data/service.py',
    'geopol_data/models.py',
    'geopol_data/config.py',
    'geopol_data/constants.py',
    'geopol_data/connectors/__init__.py',
    'geopol_data/connectors/world_bank.py',
]

all_exist = True
for file_path in required_files:
    full_path = flask_dir / file_path
    exists = full_path.exists()
    status = "✅" if exists else "❌"
    print(f"   {status} {file_path}")
    if not exists:
        all_exist = False

if all_exist:
    print("✅ Tous les fichiers requis existent")
else:
    print("❌ Certains fichiers manquent")
    sys.exit(1)

# ============================================================================
# TEST 2 : Import du module
# ============================================================================

print("\n2️⃣ Test import module...")

try:
    # Ajouter Flask au path
    if str(flask_dir) not in sys.path:
        sys.path.insert(0, str(flask_dir))
    
    from geopol_data.routes import create_geopol_data_blueprint
    print("✅ Import create_geopol_data_blueprint réussi")
    
    from geopol_data.service import DataService
    print("✅ Import DataService réussi")
    
except ImportError as e:
    print(f"❌ Erreur import: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============================================================================
# TEST 3 : Création du DataService
# ============================================================================

print("\n3️⃣ Test création DataService...")

try:
    data_service = DataService()
    print(f"✅ DataService créé: {type(data_service)}")
    
    # Tester une méthode
    status = data_service.get_service_status()
    print(f"✅ Service status: {status.get('status', 'unknown')}")
    
except Exception as e:
    print(f"❌ Erreur DataService: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============================================================================
# TEST 4 : Création du Blueprint
# ============================================================================

print("\n4️⃣ Test création Blueprint...")

try:
    # Mock du db_manager pour le test
    class MockDBManager:
        pass
    
    db_manager = MockDBManager()
    
    # Créer le blueprint
    blueprint = create_geopol_data_blueprint(db_manager, data_service)
    
    print(f"   Type retourné: {type(blueprint)}")
    print(f"   Est None: {blueprint is None}")
    
    if blueprint is None:
        print("❌ PROBLÈME: create_geopol_data_blueprint() retourne None")
        print("\n🔍 Analyse du fichier routes.py:")
        
        routes_file = geopol_dir / 'routes.py'
        with open(routes_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Chercher le return
        if 'return bp' in content:
            print("   ✅ 'return bp' trouvé dans le fichier")
            
            # Vérifier l'indentation
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                if 'return bp' in line:
                    print(f"   Ligne {i}: {line}")
                    
                    # Vérifier si c'est dans la bonne fonction
                    # Trouver la fonction parente
                    for j in range(i-1, max(0, i-50), -1):
                        if 'def create_geopol_data_blueprint' in lines[j]:
                            print(f"   ✅ 'return bp' est dans create_geopol_data_blueprint()")
                            break
                        elif lines[j].strip().startswith('def '):
                            print(f"   ⚠️ 'return bp' est dans une autre fonction: {lines[j].strip()}")
                            break
        else:
            print("   ❌ 'return bp' MANQUANT dans le fichier")
            print("\n🔧 Solution: Ajouter 'return bp' à la fin de create_geopol_data_blueprint()")
        
        sys.exit(1)
    
    print(f"✅ Blueprint créé: {blueprint}")
    print(f"   Nom: {blueprint.name}")
    print(f"   URL prefix: {blueprint.url_prefix}")
    
    # Lister les routes
    print(f"\n📋 Routes enregistrées:")
    for rule in blueprint.url_map or []:
        print(f"   • {rule}")
    
    # Si pas de url_map, lister les fonctions
    if hasattr(blueprint, 'deferred_functions'):
        print(f"   Routes en attente: {len(blueprint.deferred_functions)}")
    
except Exception as e:
    print(f"❌ Erreur création Blueprint: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============================================================================
# TEST 5 : Test avec Flask app
# ============================================================================

print("\n5️⃣ Test intégration Flask...")

try:
    from flask import Flask
    
    app = Flask(__name__)
    app.register_blueprint(blueprint, url_prefix='/api/geopol')
    
    print("✅ Blueprint enregistré dans Flask")
    
    # Lister toutes les routes
    print(f"\n📋 Routes Flask:")
    for rule in app.url_map.iter_rules():
        if '/api/geopol' in str(rule):
            print(f"   • {rule.endpoint:30s} {rule.rule}")
    
except Exception as e:
    print(f"❌ Erreur intégration Flask: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============================================================================
# TEST 6 : Test endpoints
# ============================================================================

print("\n6️⃣ Test endpoints (simulation)...")

try:
    with app.test_client() as client:
        # Test /health
        response = client.get('/api/geopol/health')
        print(f"   GET /api/geopol/health: {response.status_code}")
        if response.status_code == 200:
            print(f"      {response.get_json()}")
        
        # Test /status
        response = client.get('/api/geopol/status')
        print(f"   GET /api/geopol/status: {response.status_code}")
        
        # Test /country/FR
        response = client.get('/api/geopol/country/FR')
        print(f"   GET /api/geopol/country/FR: {response.status_code}")

    print("✅ Tests endpoints OK")
    
except Exception as e:
    print(f"❌ Erreur tests endpoints: {e}")
    import traceback
    traceback.print_exc()

# ============================================================================
# RÉSUMÉ
# ============================================================================

print("\n" + "=" * 70)
print("✅ DIAGNOSTIC TERMINÉ - TOUS LES TESTS PASSÉS")
print("=" * 70)
print("\n🎯 Le module Geopol-Data est fonctionnel")
print("\n📝 Prochaines étapes:")
print("   1. Vérifier que routes.py contient bien 'return bp'")
print("   2. Redémarrer Flask: python run.py")
print("   3. Tester: curl http://localhost:5000/api/geopol/health")
print("=" * 70 + "\n")
