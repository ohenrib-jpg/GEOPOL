// Version simplifiée du layer SDR
class SDRGlobalLayer {
    constructor(map, options = {}) {
        this.map = map;
        this.options = options;
        console.log('🗺️ SDRGlobalLayer initialisé');
    }
    
    async loadData() {
        try {
            const response = await fetch('/api/sdr-global/servers/geojson');
            const data = await response.json();
            console.log('✅ Données chargées:', data.features?.length || 0, 'serveurs');
        } catch (error) {
            console.error('❌ Erreur:', error);
        }
    }
}

// Initialisation
document.addEventListener('DOMContentLoaded', () => {
    if (window.geopolMap) {
        window.sdrGlobalLayer = new SDRGlobalLayer(window.geopolMap);
        window.sdrGlobalLayer.loadData();
    }
});
