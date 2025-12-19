#!/usr/bin/env python3
"""
Point d'entrée principal de GEOPOL Analytics
Lance le serveur Flask avec configuration optimale
"""

import sys
import os
import warnings
from pathlib import Path

# ============================================================================
# CONFIGURATION WARNINGS
# ============================================================================

# Supprimer les SyntaxWarning de TextBlob (Python 3.12+)
warnings.filterwarnings('ignore', category=SyntaxWarning, module='textblob')

# ============================================================================
# CONFIGURATION DES CHEMINS
# ============================================================================

# S'assurer que le dossier racine est dans le path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

print("=" * 70)
print("🚀 GEOPOL ANALYTICS - Démarrage")
print("=" * 70)
print(f"📁 Dossier projet: {project_root}")
print(f"🐍 Python: {sys.version.split()[0]}")

# ============================================================================
# VÉRIFICATION DES DÉPENDANCES
# ============================================================================

print("\n🔍 Vérification des dépendances...")

required_packages = {
    'flask': 'Flask',
    'feedparser': 'feedparser',
    'textblob': 'TextBlob',
    'nltk': 'NLTK',
    'bs4': 'BeautifulSoup',
    'requests': 'Requests',
}

missing = []
for package, name in required_packages.items():
    try:
        __import__(package)
        print(f"✅ {name}")
    except ImportError:
        print(f"❌ {name}")
        missing.append(name)

if missing:
    print(f"\n❌ Packages manquants: {', '.join(missing)}")
    print("   Installation: pip install " + " ".join(missing))
    sys.exit(1)

# ============================================================================
# IMPORT DE L'APPLICATION
# ============================================================================

print("\n📦 Import de l'application Flask...")

try:
    # Import absolu (correct pour les imports relatifs dans app_factory)
    from Flask.app_factory import create_app
    print("✅ Module app_factory importé")
    
except ImportError as e:
    print(f"❌ Erreur import app_factory: {e}")
    print("\n🔍 Vérifications:")
    print(f"   1. Flask/__init__.py existe: {(project_root / 'Flask' / '__init__.py').exists()}")
    print(f"   2. Flask/app_factory.py existe: {(project_root / 'Flask' / 'app_factory.py').exists()}")
    sys.exit(1)

# ============================================================================
# CRÉATION DE L'APPLICATION
# ============================================================================

print("\n🏗️ Création de l'application Flask...")

try:
    app = create_app()
    
    # VALIDATION CRITIQUE
    if app is None:
        raise RuntimeError("create_app() a retourné None - Vérifier 'return app' dans app_factory.py")
    
    if not hasattr(app, 'run'):
        raise RuntimeError(f"Objet invalide retourné par create_app(): {type(app)}")
    
    print(f"✅ Application créée: {app.name}")
    print(f"   Routes enregistrées: {len(list(app.url_map.iter_rules()))}")
    
except Exception as e:
    print(f"\n❌ Erreur création application: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============================================================================
# CONFIGURATION DU SERVEUR
# ============================================================================

def main():
    """Point d'entrée principal"""
    
    # Configuration depuis variables d'environnement
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'true').lower() == 'true'
    
    print("\n" + "=" * 70)
    print("🌐 SERVEUR FLASK")
    print("=" * 70)
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Debug: {debug}")
    print(f"Mode: {'Développement' if debug else 'Production'}")
    print("=" * 70)
    print(f"\n🌍 URL: http://localhost:{port}")
    print(f"📊 Health: http://localhost:{port}/health")
    print(f"🗺️ Carte: http://localhost:{port}/api/geopol/map")
    print("\n⚠️ Appuyez sur Ctrl+C pour arrêter")
    print("=" * 70 + "\n")
    
    try:
        # Lancer le serveur
        app.run(
            host=host,
            port=port,
            debug=debug,
            use_reloader=debug,  # Reloader seulement en debug
            threaded=True
        )
    
    except KeyboardInterrupt:
        print("\n\n" + "=" * 70)
        print("🛑 ARRÊT DU SERVEUR")
        print("=" * 70)
        print("✅ Serveur arrêté proprement")
        print("=" * 70 + "\n")
    
    except Exception as e:
        print(f"\n❌ Erreur au démarrage: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# ============================================================================
# POINT D'ENTRÉE
# ============================================================================

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ Erreur critique: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)