# integrate_sdr.py (à la racine)
"""
Script d'intégration rapide SDR dans GEOPOL
"""

import sys
from pathlib import Path

# Ajouter le chemin
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def integrate_with_flask():
    """Intègre le SDR dans l'app Flask existante"""
    
    print("=" * 70)
    print("INTEGRATION SDR DANS FLASK")
    print("=" * 70)
    
    try:
        # Importer les composants
        from Flask.geopol_data.sdr_analyzer import SDRAnalyzer
        from Flask.geopol_data.connectors.sdr_spectrum_service import SDRSpectrumService
        
        print("1. Composants SDR importés avec succès")
        
        # Créer le code d'intégration
        integration_code = '''
# ============================================
# INTEGRATION SDR DANS VOTRE APP FLASK
# ============================================

# 1. Ajoutez ces imports dans votre fichier principal
from Flask.geopol_data.sdr_analyzer import SDRAnalyzer
from Flask.geopol_data.connectors.sdr_spectrum_service import SDRSpectrumService

# 2. Initialisez les services SDR
def init_sdr_services(app, db_manager):
    """Initialise les services SDR"""
    
    # Créer les instances
    sdr_service = SDRSpectrumService(db_manager)
    sdr_analyzer = SDRAnalyzer(db_manager)
    
    # Ajouter aux variables globales de l'app
    app.sdr_service = sdr_service
    app.sdr_analyzer = sdr_analyzer
    
    print("OK Services SDR initialisés")
    return sdr_service, sdr_analyzer

# 3. Ajoutez ces routes API dans votre blueprint
def add_sdr_routes(bp, sdr_service, sdr_analyzer):
    """Ajoute les routes SDR à un blueprint"""
    
    @bp.route('/api/sdr/health')
    def sdr_health():
        return jsonify({
            'status': 'online',
            'service': 'SDR Spectrum Analyzer',
            'timestamp': datetime.utcnow().isoformat()
        })
    
    @bp.route('/api/sdr/dashboard')
    def sdr_dashboard():
        data = sdr_service.get_dashboard_data()
        return jsonify(data)
    
    @bp.route('/api/sdr/geojson')
    def sdr_geojson():
        geojson = sdr_analyzer.get_geojson_overlay()
        return jsonify(geojson)
    
    @bp.route('/api/sdr/scan')
    def sdr_scan():
        import asyncio
        try:
            # Version asynchrone
            from Flask.geopol_data.connectors.sdr_spectrum_service import AsyncSDRSpectrumService
            async_service = AsyncSDRSpectrumService(sdr_service.db_manager)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(async_service.scan_critical_frequencies())
            loop.close()
            return jsonify(result)
        except:
            # Version synchrone de secours
            return jsonify(sdr_service.scan_frequency(6000))

# 4. Dans votre fonction principale, appelez:
# sdr_service, sdr_analyzer = init_sdr_services(app, db_manager)
# add_sdr_routes(your_blueprint, sdr_service, sdr_analyzer)
'''
        
        print("2. Code d'intégration généré")
        print("\n" + "=" * 70)
        print("ETAPES D'INTEGRATION")
        print("=" * 70)
        print(integration_code)
        
        return True
        
    except Exception as e:
        print(f"ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    integrate_with_flask()