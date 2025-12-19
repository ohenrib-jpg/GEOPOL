/**
 * Panneau de contrôle pour les surcouches météo
 * Gère l'interface utilisateur avec boutons on/off
 */

class WeatherControlPanel {
    constructor(mapInstance, apiBaseUrl = '/api/weather') {
        this.map = mapInstance;
        this.apiBaseUrl = apiBaseUrl;
        this.layers = {};
        this.controlPanel = null;
        this.isPanelVisible = false;
        
        // Initialiser
        this.init();
    }
    
    /**
     * Initialise le panneau de contrôle
     */
    async init() {
        // Créer le bouton de contrôle principal
        this.createControlButton();
        
        // Charger la configuration initiale
        await this.loadControlPanelConfig();
        
        // Ajouter le panneau à la carte
        this.addControlPanelToMap();
        
        console.log('✅ WeatherControlPanel initialisé');
    }
    
    /**
     * Crée le bouton de contrôle principal
     */
    createControlButton() {
        // Créer le bouton
        const controlButton = L.Control.extend({
            options: {
                position: 'topright'
            },
            
            onAdd: function(map) {
                const container = L.DomUtil.create('div', 'weather-control-button-container');
                
                const button = L.DomUtil.create('button', 'weather-control-button', container);
                button.innerHTML = '🌤️';
                button.title = 'Panneau de contrôle météo';
                button.style.cssText = `
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    border: none;
                    border-radius: 50%;
                    width: 50px;
                    height: 50px;
                    color: white;
                    font-size: 24px;
                    cursor: pointer;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    transition: all 0.3s ease;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                `;
                
                // Effet hover
                button.onmouseover = () => {
                    button.style.transform = 'scale(1.1)';
                    button.style.boxShadow = '0 6px 8px rgba(0, 0, 0, 0.2)';
                };
                
                button.onmouseout = () => {
                    button.style.transform = 'scale(1)';
                    button.style.boxShadow = '0 4px 6px rgba(0, 0, 0, 0.1)';
                };
                
                // Gestionnaire de clic
                button.onclick = () => {
                    window.weatherControlPanel.toggleControlPanel();
                };
                
                return container;
            }
        });
        
        // Ajouter le bouton à la carte
        this.map.addControl(new controlButton());
    }
    
    /**
     * Ajoute le panneau de contrôle à la carte
     */
    addControlPanelToMap() {
        // Créer le conteneur du panneau
        const panelContainer = L.Control.extend({
            options: {
                position: 'topright'
            },
            
            onAdd: function(map) {
                const container = L.DomUtil.create('div', 'weather-control-panel-container');
                container.style.cssText = `
                    display: none;
                    position: absolute;
                    top: 60px;
                    right: 10px;
                    background: white;
                    border-radius: 10px;
                    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
                    width: 350px;
                    max-height: 80vh;
                    overflow-y: auto;
                    z-index: 1000;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                `;
                
                return container;
            }
        });
        
        this.controlPanel = this.map.addControl(new panelContainer());
        this.panelElement = this.controlPanel.getContainer();
    }
    
    /**
     * Charge la configuration du panneau de contrôle
     */
    async loadControlPanelConfig() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/control-panel`);
            const data = await response.json();
            
            if (data.success) {
                this.renderControlPanel(data.control_panel);
            } else {
                console.error('❌ Erreur chargement panneau:', data.error);
            }
        } catch (error) {
            console.error('❌ Erreur API panneau:', error);
        }
    }
    
    /**
     * Rend le panneau de contrôle
     */
    renderControlPanel(config) {
        if (!this.panelElement) return;
        
        const panelHTML = `
            <div class="weather-control-panel">
                <div class="panel-header">
                    <h3>${config.title}</h3>
                    <p class="panel-description">${config.description}</p>
                    <button class="close-panel" title="Fermer">×</button>
                </div>
                
                <div class="panel-body">
                    <div class="layers-list">
                        ${this.renderLayersList(config.layers)}
                    </div>
                    
                    <div class="panel-actions">
                        <button class="btn-refresh" onclick="window.weatherControlPanel.refreshAllLayers()">
                            🔄 Rafraîchir
                        </button>
                        <button class="btn-show-all" onclick="window.weatherControlPanel.showAllLayers()">
                            👁️ Tout afficher
                        </button>
                        <button class="btn-hide-all" onclick="window.weatherControlPanel.hideAllLayers()">
                            👁️‍🗨️ Tout cacher
                        </button>
                    </div>
                    
                    <div class="panel-status">
                        <div class="status-item">
                            <span class="status-label">Service:</span>
                            <span class="status-value" id="weather-status">Chargement...</span>
                        </div>
                        <div class="status-item">
                            <span class="status-label">Couches actives:</span>
                            <span class="status-value" id="active-layers-count">0</span>
                        </div>
                    </div>
                </div>
                
                <div class="panel-footer">
                    <small>Données Open-Meteo • Mise à jour: ${new Date().toLocaleTimeString()}</small>
                </div>
            </div>
        `;
        
        this.panelElement.innerHTML = panelHTML;
        
        // Ajouter les styles
        this.addPanelStyles();
        
        // Ajouter les gestionnaires d'événements
        this.setupPanelEventListeners();
        
        // Mettre à jour le statut
        this.updateStatus();
    }
    
    /**
     * Rend la liste des couches
     */
    renderLayersList(layers) {
        let html = '';
        
        for (const [layerId, layer] of Object.entries(layers)) {
            if (!layer.enabled) continue;
            
            const isActive = layer.visible ? 'active' : '';
            const hasDataClass = layer.has_data ? 'has-data' : 'no-data';
            
            html += `
                <div class="layer-item ${isActive} ${hasDataClass}" data-layer-id="${layerId}">
                    <div class="layer-icon">${layer.icon}</div>
                    
                    <div class="layer-info">
                        <div class="layer-name">${layer.name}</div>
                        <div class="layer-status">
                            ${layer.has_data ? '📊 Données disponibles' : '⏳ Chargement...'}
                        </div>
                    </div>
                    
                    <div class="layer-controls">
                        <label class="toggle-switch">
                            <input type="checkbox" 
                                   class="layer-toggle" 
                                   ${layer.visible ? 'checked' : ''}
                                   data-layer-id="${layerId}">
                            <span class="toggle-slider"></span>
                        </label>
                        
                        <div class="opacity-control">
                            <input type="range" 
                                   class="opacity-slider" 
                                   min="0" max="100" 
                                   value="${Math.round(layer.opacity * 100)}"
                                   data-layer-id="${layerId}"
                                   title="Opacité: ${Math.round(layer.opacity * 100)}%">
                        </div>
                    </div>
                </div>
            `;
        }
        
        return html;
    }
    
    /**
     * Ajoute les styles CSS au panneau
     */
    addPanelStyles() {
        const styles = `
            <style>
                .weather-control-panel {
                    padding: 0;
                }
                
                .panel-header {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 20px;
                    border-radius: 10px 10px 0 0;
                    position: relative;
                }
                
                .panel-header h3 {
                    margin: 0 0 5px 0;
                    font-size: 18px;
                }
                
                .panel-description {
                    margin: 0;
                    opacity: 0.9;
                    font-size: 12px;
                }
                
                .close-panel {
                    position: absolute;
                    top: 15px;
                    right: 15px;
                    background: rgba(255, 255, 255, 0.2);
                    border: none;
                    color: white;
                    width: 30px;
                    height: 30px;
                    border-radius: 50%;
                    cursor: pointer;
                    font-size: 20px;
                    line-height: 1;
                }
                
                .close-panel:hover {
                    background: rgba(255, 255, 255, 0.3);
                }
                
                .panel-body {
                    padding: 20px;
                }
                
                .layers-list {
                    margin-bottom: 20px;
                }
                
                .layer-item {
                    display: flex;
                    align-items: center;
                    padding: 12px 15px;
                    margin-bottom: 10px;
                    background: #f8f9fa;
                    border-radius: 8px;
                    border: 2px solid transparent;
                    transition: all 0.2s ease;
                }
                
                .layer-item:hover {
                    background: #e9ecef;
                    transform: translateX(-2px);
                }
                
                .layer-item.active {
                    border-color: #667eea;
                    background: #f0f4ff;
                }
                
                .layer-item.no-data {
                    opacity: 0.6;
                }
                
                .layer-icon {
                    font-size: 24px;
                    margin-right: 15px;
                    width: 40px;
                    text-align: center;
                }
                
                .layer-info {
                    flex: 1;
                }
                
                .layer-name {
                    font-weight: 600;
                    margin-bottom: 3px;
                }
                
                .layer-status {
                    font-size: 11px;
                    color: #6c757d;
                }
                
                .layer-controls {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }
                
                /* Toggle switch */
                .toggle-switch {
                    position: relative;
                    display: inline-block;
                    width: 50px;
                    height: 24px;
                }
                
                .toggle-switch input {
                    opacity: 0;
                    width: 0;
                    height: 0;
                }
                
                .toggle-slider {
                    position: absolute;
                    cursor: pointer;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background-color: #ccc;
                    transition: .4s;
                    border-radius: 24px;
                }
                
                .toggle-slider:before {
                    position: absolute;
                    content: "";
                    height: 16px;
                    width: 16px;
                    left: 4px;
                    bottom: 4px;
                    background-color: white;
                    transition: .4s;
                    border-radius: 50%;
                }
                
                input:checked + .toggle-slider {
                    background-color: #667eea;
                }
                
                input:checked + .toggle-slider:before {
                    transform: translateX(26px);
                }
                
                /* Opacity slider */
                .opacity-slider {
                    width: 60px;
                    height: 4px;
                    -webkit-appearance: none;
                    background: #ddd;
                    border-radius: 2px;
                    outline: none;
                }
                
                .opacity-slider::-webkit-slider-thumb {
                    -webkit-appearance: none;
                    width: 16px;
                    height: 16px;
                    border-radius: 50%;
                    background: #667eea;
                    cursor: pointer;
                }
                
                /* Panel actions */
                .panel-actions {
                    display: flex;
                    gap: 10px;
                    margin-bottom: 20px;
                }
                
                .panel-actions button {
                    flex: 1;
                    padding: 10px;
                    border: none;
                    border-radius: 6px;
                    background: #f8f9fa;
                    color: #495057;
                    cursor: pointer;
                    font-size: 14px;
                    transition: all 0.2s ease;
                }
                
                .panel-actions button:hover {
                    background: #e9ecef;
                    transform: translateY(-2px);
                }
                
                .panel-status {
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 8px;
                    font-size: 14px;
                }
                
                .status-item {
                    display: flex;
                    justify-content: space-between;
                    margin-bottom: 8px;
                }
                
                .status-item:last-child {
                    margin-bottom: 0;
                }
                
                .status-label {
                    font-weight: 600;
                    color: #495057;
                }
                
                .status-value {
                    color: #6c757d;
                }
                
                .panel-footer {
                    padding: 15px 20px;
                    background: #f8f9fa;
                    border-top: 1px solid #dee2e6;
                    border-radius: 0 0 10px 10px;
                    text-align: center;
                    color: #6c757d;
                    font-size: 12px;
                }
            </style>
        `;
        
        // Ajouter les styles au document
        if (!document.getElementById('weather-control-styles')) {
            const styleElement = document.createElement('div');
            styleElement.id = 'weather-control-styles';
            styleElement.innerHTML = styles;
            document.head.appendChild(styleElement.firstChild);
        }
    }
    
    /**
     * Configure les écouteurs d'événements du panneau
     */
    setupPanelEventListeners() {
        // Bouton fermer
        const closeButton = this.panelElement.querySelector('.close-panel');
        if (closeButton) {
            closeButton.addEventListener('click', () => {
                this.toggleControlPanel(false);
            });
        }
        
        // Toggle switches
        const toggleSwitches = this.panelElement.querySelectorAll('.layer-toggle');
        toggleSwitches.forEach(toggle => {
            toggle.addEventListener('change', (e) => {
                const layerId = e.target.dataset.layerId;
                const isChecked = e.target.checked;
                this.toggleLayer(layerId, isChecked);
            });
        });
        
        // Opacity sliders
        const opacitySliders = this.panelElement.querySelectorAll('.opacity-slider');
        opacitySliders.forEach(slider => {
            slider.addEventListener('input', (e) => {
                const layerId = e.target.dataset.layerId;
                const opacity = e.target.value / 100;
                this.setLayerOpacity(layerId, opacity);
            });
        });
    }
    
    /**
     * Active/désactive le panneau de contrôle
     */
    toggleControlPanel(show = null) {
        if (show === null) {
            this.isPanelVisible = !this.isPanelVisible;
        } else {
            this.isPanelVisible = show;
        }
        
        if (this.panelElement) {
            this.panelElement.style.display = this.isPanelVisible ? 'block' : 'none';
        }
    }
    
    /**
     * Active/désactive une couche spécifique
     */
    async toggleLayer(layerId, visible) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/layer/${layerId}/toggle`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ visible })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Mettre à jour l'interface
                this.updateLayerUI(layerId, visible);
                
                // Charger les données si la couche est activée
                if (visible) {
                    await this.loadLayerData(layerId);
                } else {
                    this.removeLayer(layerId);
                }
                
                // Mettre à jour le statut
                this.updateStatus();
                
                console.log(`✅ Couche ${layerId}: ${visible ? 'activée' : 'désactivée'}`);
            }
        } catch (error) {
            console.error(`❌ Erreur toggle couche ${layerId}:`, error);
        }
    }
    
    /**
     * Modifie l'opacité d'une couche
     */
    async setLayerOpacity(layerId, opacity) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/layer/${layerId}/opacity`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ opacity })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Mettre à jour l'opacité de la couche sur la carte
                if (this.layers[layerId]) {
                    this.layers[layerId].setStyle({ opacity: opacity });
                }
                
                console.log(`✅ Opacité couche ${layerId}: ${opacity}`);
            }
        } catch (error) {
            console.error(`❌ Erreur opacité couche ${layerId}:`, error);
        }
    }
    
    /**
     * Charge les données d'une couche
     */
    async loadLayerData(layerId) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/layer/${layerId}`);
            const data = await response.json();
            
            if (data.success && data.geojson) {
                // Ajouter la couche à la carte
                this.addLayerToMap(layerId, data.geojson, data.layer_config);
            }
        } catch (error) {
            console.error(`❌ Erreur chargement couche ${layerId}:`, error);
        }
    }
    
    /**
     * Ajoute une couche à la carte
     */
    addLayerToMap(layerId, geojson, layerConfig) {
        // Supprimer la couche existante si elle existe
        this.removeLayer(layerId);
        
        // Créer la couche GeoJSON
        const layer = L.geoJSON(geojson, {
            pointToLayer: function(feature, latlng) {
                // Créer un marqueur circulaire coloré
                return L.circleMarker(latlng, {
                    radius: 12,
                    fillColor: feature.properties.color || '#3388ff',
                    color: '#fff',
                    weight: 2,
                    opacity: layerConfig?.opacity || 0.8,
                    fillOpacity: layerConfig?.opacity || 0.6
                });
            },
            onEachFeature: function(feature, layer) {
                // Ajouter un popup
                if (feature.properties.popup_content) {
                    layer.bindPopup(feature.properties.popup_content);
                }
                
                // Effet hover
                layer.on('mouseover', function(e) {
                    this.setStyle({
                        weight: 3,
                        fillOpacity: 0.8
                    });
                });
                
                layer.on('mouseout', function(e) {
                    this.setStyle({
                        weight: 2,
                        fillOpacity: layerConfig?.opacity || 0.6
                    });
                });
            }
        });
        
        // Ajouter la couche à la carte
        layer.addTo(this.map);
        
        // Stocker la référence
        this.layers[layerId] = layer;
        
        console.log(`✅ Couche ${layerId} ajoutée à la carte`);
    }
    
    /**
     * Supprime une couche de la carte
     */
    removeLayer(layerId) {
        if (this.layers[layerId]) {
            this.map.removeLayer(this.layers[layerId]);
            delete this.layers[layerId];
            console.log(`✅ Couche ${layerId} retirée de la carte`);
        }
    }
    
    /**
     * Met à jour l'interface d'une couche
     */
    updateLayerUI(layerId, isActive) {
        const layerElement = this.panelElement.querySelector(`.layer-item[data-layer-id="${layerId}"]`);
        if (layerElement) {
            if (isActive) {
                layerElement.classList.add('active');
            } else {
                layerElement.classList.remove('active');
            }
            
            const toggle = layerElement.querySelector('.layer-toggle');
            if (toggle) {
                toggle.checked = isActive;
            }
        }
    }
    
    /**
     * Rafraîchit toutes les couches
     */
    async refreshAllLayers() {
        console.log('🔄 Rafraîchissement des couches...');
        
        // Recharger la configuration
        await this.loadControlPanelConfig();
        
        // Recharger les couches actives
        for (const layerId in this.layers) {
            await this.loadLayerData(layerId);
        }
        
        // Mettre à jour le statut
        this.updateStatus();
    }
    
    /**
     * Affiche toutes les couches
     */
    async showAllLayers() {
        for (const layerId in this.layers) {
            await this.toggleLayer(layerId, true);
        }
    }
    
    /**
     * Cache toutes les couches
     */
    async hideAllLayers() {
        for (const layerId in this.layers) {
            await this.toggleLayer(layerId, false);
        }
    }
    
    /**
     * Met à jour le statut du panneau
     */
    async updateStatus() {
        try {
            // Récupérer le statut du service
            const response = await fetch(`${this.apiBaseUrl}/health`);
            const data = await response.json();
            
            if (data.success) {
                const statusElement = document.getElementById('weather-status');
                const countElement = document.getElementById('active-layers-count');
                
                if (statusElement) {
                    statusElement.textContent = data.status === 'healthy' ? '✅ Opérationnel' : '⚠️ Dégradé';
                    statusElement.style.color = data.status === 'healthy' ? '#28a745' : '#dc3545';
                }
                
                if (countElement) {
                    const activeLayers = Object.values(this.layers).length;
                    countElement.textContent = activeLayers;
                }
            }
        } catch (error) {
            console.error('❌ Erreur mise à jour statut:', error);
        }
    }
}

// Exposer globalement pour l'accès depuis le HTML
window.WeatherControlPanel = WeatherControlPanel;