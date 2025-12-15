// static/js/weather_layers.js
/**
 * Gestionnaire des couches météorologiques Open-Meteo pour Leaflet
 * Intégration avec la carte géopolitique
 */

// ============================================================================
// CLASSE PRINCIPALE : WeatherLayersManager
// ============================================================================

class WeatherLayersManager {
    constructor(map) {
        this.map = map;
        this.layers = {};
        this.layerGroups = {};
        this.config = null;
        
        // Configuration locale
        this.apiBaseUrl = '/api/geopol/weather';
        this.refreshInterval = 15 * 60 * 1000; // 15 minutes
        this.autoRefreshTimer = null;
        
        console.log('🌦️ WeatherLayersManager initialisé');
    }
    
    // ========================================================================
    // INITIALISATION
    // ========================================================================
    
    async initialize() {
        try {
            console.log('📡 Chargement configuration couches météo...');
            
            // Récupérer la configuration
            const response = await fetch(`${this.apiBaseUrl}/layers/config`);
            const data = await response.json();
            
            if (data.success) {
                this.config = data.layers;
                console.log('✅ Configuration chargée:', this.config);
                
                // Créer les layer groups Leaflet
                this.createLayerGroups();
                
                // Charger les données initiales
                await this.loadAllLayers();
                
                // Démarrer le rafraîchissement automatique
                this.startAutoRefresh();
            } else {
                console.error('❌ Erreur chargement config:', data.error);
            }
        } catch (error) {
            console.error('❌ Erreur initialisation météo:', error);
        }
    }
    
    createLayerGroups() {
        // Créer un LayerGroup pour chaque type de couche
        for (const layerType in this.config) {
            this.layerGroups[layerType] = L.layerGroup();
            
            // Ajouter à la carte si visible par défaut
            if (this.config[layerType].visible) {
                this.layerGroups[layerType].addTo(this.map);
            }
        }
        
        console.log('✅ LayerGroups créés:', Object.keys(this.layerGroups));
    }
    
    // ========================================================================
    // CHARGEMENT DES DONNÉES
    // ========================================================================
    
    async loadAllLayers() {
        try {
            console.log('📥 Chargement données météo...');
            
            // Récupérer les couches actives
            const activeTypes = Object.keys(this.config)
                .filter(type => this.config[type].visible)
                .join(',');
            
            if (!activeTypes) {
                console.log('ℹ️ Aucune couche active');
                return;
            }
            
            const response = await fetch(
                `${this.apiBaseUrl}/layers?types=${activeTypes}`
            );
            const data = await response.json();
            
            if (data.success) {
                console.log(`✅ ${data.countries_count} pays chargés`);
                
                // Afficher chaque couche
                for (const layerType in data.layers) {
                    this.displayLayer(layerType, data.layers[layerType]);
                }
            } else {
                console.error('❌ Erreur chargement couches:', data.error);
            }
        } catch (error) {
            console.error('❌ Erreur loadAllLayers:', error);
        }
    }
    
    // ========================================================================
    // AFFICHAGE DES COUCHES
    // ========================================================================
    
    displayLayer(layerType, layerData) {
        // Nettoyer la couche existante
        this.layerGroups[layerType].clearLayers();
        
        // Afficher selon le type
        switch (layerType) {
            case 'temperature':
                this.displayTemperatureLayer(layerData);
                break;
            case 'precipitation':
                this.displayPrecipitationLayer(layerData);
                break;
            case 'wind':
                this.displayWindLayer(layerData);
                break;
            case 'air_quality':
                this.displayAirQualityLayer(layerData);
                break;
            default:
                console.warn(`Type de couche inconnu: ${layerType}`);
        }
    }
    
    displayTemperatureLayer(layerData) {
        const { points, config } = layerData;
        
        points.forEach(point => {
            const marker = L.circleMarker([point.lat, point.lng], {
                radius: 8,
                fillColor: point.color,
                fillOpacity: config.opacity,
                color: '#fff',
                weight: 1
            });
            
            // Popup avec infos
            marker.bindPopup(`
                <strong>Température</strong><br>
                ${point.value.toFixed(1)}°C
            `);
            
            // Tooltip au survol
            marker.bindTooltip(`${point.value.toFixed(1)}°C`, {
                permanent: false,
                direction: 'top'
            });
            
            marker.addTo(this.layerGroups['temperature']);
        });
        
        console.log(`✅ Couche température: ${points.length} points`);
    }
    
    displayPrecipitationLayer(layerData) {
        const { points, config } = layerData;
        
        points.forEach(point => {
            // Taille proportionnelle aux précipitations
            const radius = 5 + (point.intensity * 10);
            
            const marker = L.circleMarker([point.lat, point.lng], {
                radius: radius,
                fillColor: point.color,
                fillOpacity: config.opacity,
                color: '#fff',
                weight: 1
            });
            
            marker.bindPopup(`
                <strong>Précipitations</strong><br>
                ${point.value.toFixed(1)} mm
            `);
            
            marker.addTo(this.layerGroups['precipitation']);
        });
        
        console.log(`✅ Couche précipitations: ${points.length} points`);
    }
    
    displayWindLayer(layerData) {
        const { points, config } = layerData;
        
        points.forEach(point => {
            const marker = L.circleMarker([point.lat, point.lng], {
                radius: 6,
                fillColor: point.color,
                fillOpacity: config.opacity,
                color: '#fff',
                weight: 1
            });
            
            marker.bindPopup(`
                <strong>Vent</strong><br>
                ${point.value.toFixed(0)} km/h
            `);
            
            marker.addTo(this.layerGroups['wind']);
        });
        
        console.log(`✅ Couche vent: ${points.length} points`);
    }
    
    displayAirQualityLayer(layerData) {
        const { points, config } = layerData;
        
        points.forEach(point => {
            const marker = L.circleMarker([point.lat, point.lng], {
                radius: 10,
                fillColor: point.color,
                fillOpacity: config.opacity,
                color: '#fff',
                weight: 2
            });
            
            // Légende du niveau AQI
            const levelText = {
                'GOOD': 'Bon',
                'MODERATE': 'Modéré',
                'UNHEALTHY_SENSITIVE': 'Mauvais (sensibles)',
                'UNHEALTHY': 'Mauvais',
                'VERY_UNHEALTHY': 'Très mauvais',
                'HAZARDOUS': 'Dangereux'
            }[point.level] || point.level;
            
            marker.bindPopup(`
                <strong>Qualité de l'air</strong><br>
                AQI: ${point.value}<br>
                Niveau: ${levelText}
            `);
            
            marker.bindTooltip(`AQI ${point.value}`, {
                permanent: false,
                direction: 'top'
            });
            
            marker.addTo(this.layerGroups['air_quality']);
        });
        
        console.log(`✅ Couche qualité air: ${points.length} points`);
    }
    
    // ========================================================================
    // CONTRÔLE DES COUCHES
    // ========================================================================
    
    toggleLayer(layerType, visible) {
        if (visible) {
            this.layerGroups[layerType].addTo(this.map);
            console.log(`👁️ Couche ${layerType} activée`);
        } else {
            this.map.removeLayer(this.layerGroups[layerType]);
            console.log(`👁️‍🗨️ Couche ${layerType} désactivée`);
        }
        
        // Mettre à jour la config locale
        if (this.config[layerType]) {
            this.config[layerType].visible = visible;
        }
    }
    
    setLayerOpacity(layerType, opacity) {
        // Mettre à jour l'opacité de tous les markers de la couche
        this.layerGroups[layerType].eachLayer(layer => {
            if (layer.setStyle) {
                layer.setStyle({ fillOpacity: opacity });
            }
        });
        
        // Mettre à jour la config locale
        if (this.config[layerType]) {
            this.config[layerType].opacity = opacity;
        }
        
        console.log(`🎨 Opacité ${layerType}: ${opacity}`);
    }
    
    // ========================================================================
    // RAFRAÎCHISSEMENT AUTOMATIQUE
    // ========================================================================
    
    startAutoRefresh() {
        // Nettoyer le timer existant
        if (this.autoRefreshTimer) {
            clearInterval(this.autoRefreshTimer);
        }
        
        // Démarrer un nouveau timer
        this.autoRefreshTimer = setInterval(() => {
            console.log('🔄 Rafraîchissement automatique météo...');
            this.loadAllLayers();
        }, this.refreshInterval);
        
        console.log(`⏰ Rafraîchissement automatique: ${this.refreshInterval / 60000} min`);
    }
    
    stopAutoRefresh() {
        if (this.autoRefreshTimer) {
            clearInterval(this.autoRefreshTimer);
            this.autoRefreshTimer = null;
            console.log('⏸️ Rafraîchissement automatique arrêté');
        }
    }
    
    async refresh() {
        console.log('🔄 Rafraîchissement manuel...');
        await this.loadAllLayers();
    }
    
    // ========================================================================
    // UTILITAIRES
    // ========================================================================
    
    getLayerStatus() {
        const status = {};
        for (const layerType in this.config) {
            status[layerType] = {
                visible: this.config[layerType].visible,
                opacity: this.config[layerType].opacity,
                markers_count: this.layerGroups[layerType].getLayers().length
            };
        }
        return status;
    }
}

// ============================================================================
// CONTRÔLES UI (PANNEAU)
// ============================================================================

class WeatherControlPanel {
    constructor(weatherManager) {
        this.weatherManager = weatherManager;
        this.panel = null;
        this.isOpen = false;
    }
    
    create() {
        // Créer le panneau HTML
        this.panel = document.createElement('div');
        this.panel.className = 'weather-control-panel';
        this.panel.innerHTML = `
            <div class="panel-header">
                <h3>🌦️ Couches Météo</h3>
                <button class="close-btn" onclick="weatherControlPanel.toggle()">×</button>
            </div>
            <div class="panel-content">
                <div class="layer-controls" id="weather-layer-controls"></div>
                <div class="panel-actions">
                    <button class="btn-refresh" onclick="weatherControlPanel.refresh()">
                        🔄 Actualiser
                    </button>
                    <button class="btn-toggle-auto" onclick="weatherControlPanel.toggleAutoRefresh()">
                        ⏸️ Arrêter auto
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(this.panel);
        
        // Générer les contrôles pour chaque couche
        this.renderLayerControls();
        
        console.log('✅ Panneau de contrôle météo créé');
    }
    
    renderLayerControls() {
        const container = document.getElementById('weather-layer-controls');
        if (!container) return;
        
        container.innerHTML = '';
        
        for (const layerType in this.weatherManager.config) {
            const config = this.weatherManager.config[layerType];
            
            const control = document.createElement('div');
            control.className = 'layer-control';
            control.innerHTML = `
                <div class="layer-info">
                    <label>
                        <input type="checkbox" 
                               id="layer-${layerType}"
                               ${config.visible ? 'checked' : ''}
                               onchange="weatherControlPanel.toggleLayer('${layerType}', this.checked)">
                        <span>${config.name}</span>
                    </label>
                    <span class="layer-unit">${config.unit}</span>
                </div>
                <div class="opacity-control">
                    <label>Opacité:</label>
                    <input type="range" 
                           min="0" max="1" step="0.1" 
                           value="${config.opacity}"
                           onchange="weatherControlPanel.setOpacity('${layerType}', this.value)">
                    <span>${(config.opacity * 100).toFixed(0)}%</span>
                </div>
            `;
            
            container.appendChild(control);
        }
    }
    
    toggle() {
        this.isOpen = !this.isOpen;
        this.panel.classList.toggle('open', this.isOpen);
    }
    
    toggleLayer(layerType, visible) {
        this.weatherManager.toggleLayer(layerType, visible);
    }
    
    setOpacity(layerType, opacity) {
        this.weatherManager.setLayerOpacity(layerType, parseFloat(opacity));
        
        // Mettre à jour l'affichage du pourcentage
        const input = document.querySelector(`input[type="range"][onchange*="${layerType}"]`);
        if (input) {
            const span = input.nextElementSibling;
            if (span) {
                span.textContent = `${(opacity * 100).toFixed(0)}%`;
            }
        }
    }
    
    async refresh() {
        await this.weatherManager.refresh();
    }
    
    toggleAutoRefresh() {
        const btn = document.querySelector('.btn-toggle-auto');
        if (this.weatherManager.autoRefreshTimer) {
            this.weatherManager.stopAutoRefresh();
            btn.textContent = '▶️ Démarrer auto';
        } else {
            this.weatherManager.startAutoRefresh();
            btn.textContent = '⏸️ Arrêter auto';
        }
    }
}

// ============================================================================
// STYLES CSS (À AJOUTER DANS LE HTML)
// ============================================================================

const weatherStyles = `
<style>
.weather-control-panel {
    position: fixed;
    top: 100px;
    right: -350px;
    width: 330px;
    background: rgba(30, 41, 59, 0.98);
    border: 2px solid #475569;
    border-radius: 10px 0 0 10px;
    box-shadow: -4px 4px 20px rgba(0, 0, 0, 0.5);
    transition: right 0.3s ease;
    z-index: 1000;
}

.weather-control-panel.open {
    right: 0;
}

.panel-header {
    background: linear-gradient(135deg, #1e293b, #334155);
    padding: 1rem;
    border-bottom: 2px solid #475569;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.panel-header h3 {
    margin: 0;
    color: #60a5fa;
    font-size: 1.1rem;
}

.close-btn {
    background: none;
    border: none;
    color: #94a3b8;
    font-size: 1.5rem;
    cursor: pointer;
    padding: 0;
    width: 30px;
    height: 30px;
}

.close-btn:hover {
    color: #f59e0b;
}

.panel-content {
    padding: 1rem;
}

.layer-control {
    background: rgba(51, 65, 85, 0.5);
    border-radius: 8px;
    padding: 0.75rem;
    margin-bottom: 0.75rem;
    border: 1px solid #475569;
}

.layer-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.5rem;
}

.layer-info label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    cursor: pointer;
    color: #e2e8f0;
}

.layer-unit {
    color: #94a3b8;
    font-size: 0.875rem;
}

.opacity-control {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.875rem;
    color: #cbd5e1;
}

.opacity-control input[type="range"] {
    flex: 1;
}

.panel-actions {
    display: flex;
    gap: 0.5rem;
    margin-top: 1rem;
}

.panel-actions button {
    flex: 1;
    padding: 0.5rem;
    background: #3b82f6;
    border: none;
    border-radius: 5px;
    color: white;
    cursor: pointer;
    font-size: 0.875rem;
}

.panel-actions button:hover {
    background: #2563eb;
}
</style>
`;

// ============================================================================
// BOUTON TOGGLE (À AJOUTER DANS LE HTML)
// ============================================================================

const weatherToggleButton = `
<button class="weather-toggle-btn" onclick="weatherControlPanel.toggle()">
    🌦️
</button>

<style>
.weather-toggle-btn {
    position: fixed;
    top: 150px;
    right: 10px;
    width: 50px;
    height: 50px;
    background: linear-gradient(135deg, #3b82f6, #2563eb);
    border: 2px solid #1e40af;
    border-radius: 50%;
    color: white;
    font-size: 1.5rem;
    cursor: pointer;
    box-shadow: 0 4px 15px rgba(59, 130, 246, 0.4);
    z-index: 999;
    transition: all 0.3s ease;
}

.weather-toggle-btn:hover {
    transform: scale(1.1);
    box-shadow: 0 6px 20px rgba(59, 130, 246, 0.6);
}
</style>
`;

// ============================================================================
// INITIALISATION GLOBALE
// ============================================================================

let weatherLayersManager;
let weatherControlPanel;

async function initializeWeatherLayers(map) {
    try {
        console.log('🚀 Initialisation système météo...');
        
        // Créer le manager
        weatherLayersManager = new WeatherLayersManager(map);
        await weatherLayersManager.initialize();
        
        // Créer le panneau de contrôle
        weatherControlPanel = new WeatherControlPanel(weatherLayersManager);
        weatherControlPanel.create();
        
        // Injecter les styles
        const styleEl = document.createElement('div');
        styleEl.innerHTML = weatherStyles;
        document.head.appendChild(styleEl);
        
        // Injecter le bouton toggle
        const btnEl = document.createElement('div');
        btnEl.innerHTML = weatherToggleButton;
        document.body.appendChild(btnEl);
        
        console.log('✅ Système météo initialisé');
        
        return weatherLayersManager;
    } catch (error) {
        console.error('❌ Erreur initialisation météo:', error);
        return null;
    }
}

console.log('✅ Module weather_layers.js chargé');
