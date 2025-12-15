"""
Chargeur Archiviste v3 - Version corrigée
"""

import os
import sys

def load_archiviste_modules():
    """Charge tous les modules"""
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    modules = {}
    
    try:
        from historical_item import HistoricalItem
        modules['HistoricalItem'] = HistoricalItem
        print("✅ HistoricalItem chargé")
    except ImportError as e:
        print(f"❌ HistoricalItem: {e}")
    
    try:
        from archive_client import ArchiveOrgClient
        modules['ArchiveOrgClient'] = ArchiveOrgClient
        print("✅ ArchiveOrgClient chargé")
    except ImportError as e:
        print(f"❌ ArchiveOrgClient: {e}")
    
    try:
        from archiviste_database import ArchivisteDatabase
        modules['ArchivisteDatabase'] = ArchivisteDatabase
        print("✅ ArchivisteDatabase chargé")
    except ImportError as e:
        print(f"❌ ArchivisteDatabase: {e}")
    
    try:
        from archiviste_service import ArchivisteServiceImproved
        modules['ArchivisteServiceImproved'] = ArchivisteServiceImproved
        print("✅ ArchivisteServiceImproved chargé")
    except ImportError as e:
        print(f"❌ ArchivisteServiceImproved: {e}")
    
    try:
        from archiviste_routes import create_archiviste_v3_blueprint
        modules['create_archiviste_v3_blueprint'] = create_archiviste_v3_blueprint
        print("✅ create_archiviste_v3_blueprint chargé")
    except ImportError as e:
        print(f"❌ create_archiviste_v3_blueprint: {e}")
    
    # Nouveau: Gallica client
    try:
    # Chemin direct
        from gallica_client import GallicaClient
        gallica_client = GallicaClient()
        print("✅✅✅ GALLICA INITIALISÉ DIRECTEMENT")
    except:
        print("⚠️  Gallica échoué, mais Archive.org fonctionne!")
        gallica_client = None
    
        return modules

def register_archiviste_v3(app, db_manager, sentiment_analyzer=None):
    """Enregistrement avec Gallica"""
    print("\n🔧 Enregistrement d'Archiviste v3 avec sources multiples...")
    
    modules = load_archiviste_modules()
    
    if 'ArchivisteServiceImproved' in modules and 'create_archiviste_v3_blueprint' in modules:
        # Initialiser Gallica client
        gallica_client = None
        if 'GallicaClient' in modules:
            try:
                gallica_client = modules['GallicaClient']()
            except Exception as e:
                print(f"❌ Erreur initialisation GallicaClient: {e}")
        
        # Créer le service
        archiviste_service = modules['ArchivisteServiceImproved'](
            db_manager,
            sentiment_analyzer=sentiment_analyzer,
            gallica_client=gallica_client
        )
        
        # Créer et enregistrer le blueprint
        archiviste_bp = modules['create_archiviste_v3_blueprint'](archiviste_service)
        app.register_blueprint(archiviste_bp, url_prefix='/archiviste-v3')
        app.config['ARCHIVISTE_V3_SERVICE'] = archiviste_service
        
        print("✅ Archiviste v3 enregistré avec succès")
        print("   • Sources: Archive.org" + (" + Gallica" if gallica_client else ""))
        print(f"   • URL: http://localhost:5000/archiviste-v3/")
        
        return archiviste_service
    else:
        print("❌ Modules Archiviste incomplets")
        return None