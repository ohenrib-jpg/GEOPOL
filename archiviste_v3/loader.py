"""
Chargeur simplifié pour Archiviste v3
"""

import os
import sys

def load_archiviste_modules():
    """Charge tous les modules Archiviste v3"""
    
    # Ajouter le chemin courant
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    # Charger les modules dans l'ordre correct
    modules = {}
    
    try:
        from historical_item import HistoricalItem
        modules['HistoricalItem'] = HistoricalItem
        print("  ✅ HistoricalItem chargé")
    except ImportError as e:
        print(f"  ❌ Erreur HistoricalItem: {e}")
    
    try:
        from archive_client import ArchiveOrgClient
        modules['ArchiveOrgClient'] = ArchiveOrgClient
        print("  ✅ ArchiveOrgClient chargé")
    except ImportError as e:
        print(f"  ❌ Erreur ArchiveOrgClient: {e}")
    
    try:
        from archiviste_database import ArchivisteDatabase
        modules['ArchivisteDatabase'] = ArchivisteDatabase
        print("  ✅ ArchivisteDatabase chargé")
    except ImportError as e:
        print(f"  ❌ Erreur ArchivisteDatabase: {e}")
    
    try:
        from archiviste_service import ArchivisteServiceImproved
        modules['ArchivisteServiceImproved'] = ArchivisteServiceImproved
        print("  ✅ ArchivisteServiceImproved chargé")
    except ImportError as e:
        print(f"  ❌ Erreur ArchivisteServiceImproved: {e}")
    
    try:
        from archiviste_routes import create_archiviste_v3_blueprint
        modules['create_archiviste_v3_blueprint'] = create_archiviste_v3_blueprint
        print("  ✅ create_archiviste_v3_blueprint chargé")
    except ImportError as e:
        print(f"  ❌ Erreur create_archiviste_v3_blueprint: {e}")
    
    return modules

def register_archiviste_v3(app, db_manager):
    """Fonction d'enregistrement standard"""
    print("🔧 Enregistrement d'Archiviste v3...")
    
    modules = load_archiviste_modules()
    
    if 'ArchivisteServiceImproved' in modules and 'create_archiviste_v3_blueprint' in modules:
        # Créer le service
        archiviste_service = modules['ArchivisteServiceImproved'](db_manager)
        
        # Créer le blueprint
        archiviste_bp = modules['create_archiviste_v3_blueprint'](archiviste_service)
        
        # Enregistrer
        app.register_blueprint(archiviste_bp, url_prefix='/archiviste-v3')
        app.config['ARCHIVISTE_V3_SERVICE'] = archiviste_service
        
        print("✅ Archiviste v3 enregistré avec succès")
        return archiviste_service
    else:
        print("❌ Modules Archiviste v3 incomplets")
        return None