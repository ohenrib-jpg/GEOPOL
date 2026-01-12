class SatelliteIntegration {
    constructor() {
        this.apiBaseUrl = '/satellite/api';
        this.map = null;
        this.currentLayers = new Map();
        this.credentialsStatus = null;
        this.loading = false;
    }
    
    async init(map) {
        this.map = map;
        await this.checkCredentialsStatus();
        await this.loadAvailableLayers();
    }
    
    async checkCredentialsStatus() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/credentials/status`);
            const data = await response.json();
            
            if (data.status === 'success') {
                this.credentialsStatus = data.credentials_status;
                this.updateUIBasedOnStatus();
            }
        } catch (error) {
            console.error('Erreur vérification statut identifiants:', error);
        }
    }
    
    updateUIBasedOnStatus() {
        const statusElement = document.getElementById('satellite-credentials-status');
        const advancedFeatures = document.querySelectorAll('.advanced-feature');
        
        if (statusElement) {
            if (this.credentialsStatus.advanced_mode_available) {
                statusElement.innerHTML = `
                    <span class="status-active">✓ Mode avancé activé</span>
                    <button onclick="satelliteIntegration.clearCredentials()" class="btn-small">Effacer</button>
                `;
                // Activer les fonctionnalités avancées
                advancedFeatures.forEach(el => el.classList.remove('disabled'));
            } else {
                statusElement.innerHTML = `
                    <span class="status-inactive">Mode basique</span>
                    <button onclick="satelliteIntegration.showCredentialsModal()" class="btn-small">Ajouter API</button>
                `;
                // Désactiver les fonctionnalités avancées
                advancedFeatures.forEach(el => el.classList.add('disabled'));
            }
        }
    }
    
    async loadAvailableLayers() {
        this.loading = true;
        try {
            const response = await fetch(`${this.apiBaseUrl}/layers`);
            const data = await response.json();
            
            if (data.status === 'success') {
                this.displayLayers(data.layers);
            }
        } catch (error) {
            console.error('Erreur chargement couches:', error);
        } finally {
            this.loading = false;
        }
    }
    
    displayLayers(layers) {
        const container = document.getElementById('satellite-layers-container');
        if (!container) return;
        
        let html = '<div class="layers-grid">';
        
        Object.keys(layers).forEach(layerId => {
            const layer = layers[layerId];
            html += `
                <div class="layer-card" data-layer-id="${layerId}">
                    <h4>${layer.name || layerId}</h4>
                    ${layer.description ? `<p>${layer.description}</p>` : ''}
                    <button onclick="satelliteIntegration.addLayerToMap('${layerId}')" class="btn-small">
                        Ajouter à la carte
                    </button>
                </div>
            `;
        });
        
        html += '</div>';
        container.innerHTML = html;
    }
    
    async getAvailableDates(bbox, startDate = null, endDate = null) {
        try {
            const requestData = { bbox: bbox };
            
            if (startDate && endDate) {
                requestData.start_date = startDate;
                requestData.end_date = endDate;
            }
            
            const response = await fetch(`${this.apiBaseUrl}/dates`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestData)
            });
            
            const data = await response.json();
            return data.status === 'success' ? data.dates : [];
        } catch (error) {
            console.error('Erreur récupération dates:', error);
            return [];
        }
    }
    
    async addLayerToMap(layerId, date = null) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/layer-url`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ layer_id: layerId, date: date })
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                // Retirer la couche existante si elle est déjà présente
                if (this.currentLayers.has(layerId)) {
                    this.map.removeLayer(this.currentLayers.get(layerId));
                }
                
                // Ajouter la nouvelle couche
                const layer = L.tileLayer(data.url, {
                    attribution: "Copernicus/EOS/USGS",
                    maxZoom: 18
                });
                
                layer.addTo(this.map);
                this.currentLayers.set(layerId, layer);
                
                console.log(`Couche ${layerId} ajoutée à la carte`);
            } else {
                throw new Error(data.error || 'Erreur inconnue');
            }
        } catch (error) {
            console.error('Erreur ajout couche:', error);
            alert(`Erreur: ${error.message}`);
        }
    }
    
    removeLayerFromMap(layerId) {
        if (this.currentLayers.has(layerId)) {
            this.map.removeLayer(this.currentLayers.get(layerId));
            this.currentLayers.delete(layerId);
            console.log(`Couche ${layerId} retirée de la carte`);
        }
    }
    
    clearAllLayers() {
        this.currentLayers.forEach((layer, layerId) => {
            this.map.removeLayer(layer);
        });
        this.currentLayers.clear();
        console.log('Toutes les couches ont été retirées');
    }
    
    showCredentialsModal() {
        // Créer une modale pour saisir les identifiants
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content">
                <span class="close" onclick="this.closest('.modal').remove()">&times;</span>
                <h3>Ajouter vos identifiants Copernicus</h3>
                <p>Pour utiliser les fonctionnalités avancées, vous devez créer un compte gratuit sur 
                   <a href="https://dataspace.copernicus.eu/" target="_blank">dataspace.copernicus.eu</a>
                   et obtenir des identifiants OAuth.</p>
                <form id="credentials-form">
                    <div class="form-group">
                        <label for="client-id">Client ID:</label>
                        <input type="text" id="client-id" required>
                    </div>
                    <div class="form-group">
                        <label for="client-secret">Client Secret:</label>
                        <input type="password" id="client-secret" required>
                    </div>
                    <button type="submit" class="btn">Enregistrer</button>
                </form>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Gérer la soumission du formulaire
        document.getElementById('credentials-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const clientId = document.getElementById('client-id').value;
            const clientSecret = document.getElementById('client-secret').value;
            
            try {
                const response = await fetch(`${this.apiBaseUrl}/credentials`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        client_id: clientId,
                        client_secret: clientSecret
                    })
                });
                
                const data = await response.json();
                
                if (data.status === 'success') {
                    alert('Identifiants enregistrés avec succès!');
                    modal.remove();
                    this.checkCredentialsStatus();
                    this.loadAvailableLayers();
                } else {
                    throw new Error(data.error);
                }
            } catch (error) {
                alert(`Erreur: ${error.message}`);
            }
        });
    }
    
    async clearCredentials() {
        if (confirm('Êtes-vous sûr de vouloir effacer vos identifiants ?')) {
            try {
                const response = await fetch(`${this.apiBaseUrl}/credentials`, {
                    method: 'DELETE'
                });
                
                const data = await response.json();
                
                if (data.status === 'success') {
                    alert('Identifiants effacés');
                    this.checkCredentialsStatus();
                    this.loadAvailableLayers();
                    this.clearAllLayers();
                } else {
                    throw new Error(data.error);
                }
            } catch (error) {
                alert(`Erreur: ${error.message}`);
            }
        }
    }
}

// Initialiser le module
const satelliteIntegration = new SatelliteIntegration();

// Fonction pour initialiser avec la carte Leaflet
function initSatelliteWithMap(map) {
    satelliteIntegration.init(map);
}