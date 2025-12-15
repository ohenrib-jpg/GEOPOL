// static/js/sdr_layer.js
/**
 * Couche SDR pour Leaflet
 * Intègre la santé du réseau radio comme indicateur géopolitique
 */

class SDRLayer {
    constructor(map, options = {}) {
        this.map = map;
        this.layer = null;
        this.options = {
            apiUrl: '/api/sdr',
            refreshInterval: 300000, // 5 minutes
            showLegend: true,
            showPopup: true,
            ...options
        };
        
        this.init();
    }
    
    init() {
        // Créer le contrôle de légende
        if (this.options.showLegend) {
            this.createLegend();
        }
        
        // Charger les données initiales
        this.loadData();
        
        // Configurer le rafraîchissement automatique
        if (this.options.refreshInterval > 0) {
            setInterval(() => this.loadData(), this.options.refreshInterval);
        }
    }
    
    createLegend() {
        const legend = L.control({ position: 'bottomright' });
        
        legend.onAdd = () => {
            const div = L.DomUtil.create('div', 'sdr-legend leaflet-control');
            div.innerHTML = `
                <div class="legend-header">
                    <h6>🎯 Santé Réseau SDR</h6>
                </div>
                <div class="legend-items">
                    <div class="legend-item">
                        <span class="legend-color optimal"></span>
                        <span class="legend-label">Optimal</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-color stable"></span>
                        <span class="legend-label">Stable</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-color warning"></span>
                        <span class="legend-label">Warning</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-color high-risk"></span>
                        <span class="legend-label">High Risk</span>
                    </div>
                    <div class="legend-item">
                        <span class="legend-color critical"></span>
                        <span class="legend-label">Critical</span>
                    </div>
                </div>
                <div class="legend-info">
                    <small>Actualisé: <span id="sdr-last-update">--:--</span></small>
                </div>
            `;
            return div;
        };
        
        this.legend = legend;
        this.legend.addTo(this.map);
    }
    
    async loadData() {
        try {
            const response = await fetch(`${this.options.apiUrl}/geojson`);
            const data = await response.json();
            
            if (data.features && data.features.length > 0) {
                this.updateLayer(data);
                this.updateLastUpdate(data.timestamp);
            }
        } catch (error) {
            console.error('❌ Erreur chargement données SDR:', error);
        }
    }
    
    updateLayer(geojsonData) {
        // Supprimer l'ancienne couche
        if (this.layer) {
            this.map.removeLayer(this.layer);
        }
        
        // Style dynamique basé sur le statut
        const style = (feature) => {
            const status = feature.properties.health_status;
            const styles = {
                'CRITICAL': { color: '#ff0000', weight: 3, opacity: 0.8, fillOpacity: 0.4 },
                'HIGH_RISK': { color: '#ff6b00', weight: 3, opacity: 0.7, fillOpacity: 0.3 },
                'WARNING': { color: '#ffd700', weight: 2, opacity: 0.6, fillOpacity: 0.25 },
                'STABLE': { color: '#90ee90', weight: 1, opacity: 0.5, fillOpacity: 0.2 },
                'OPTIMAL': { color: '#00ff00', weight: 1, opacity: 0.4, fillOpacity: 0.15 }
            };
            
            return styles[status] || { color: '#3388ff', weight: 1, opacity: 0.3, fillOpacity: 0.1 };
        };
        
        // Créer la couche GeoJSON
        this.layer = L.geoJSON(geojsonData, {
            style: style,
            onEachFeature: (feature, layer) => {
                if (this.options.showPopup) {
                    layer.bindPopup(this.createPopup(feature.properties));
                }
                
                layer.on('click', () => {
                    this.onZoneClick(feature.properties);
                });
                
                layer.on('mouseover', () => {
                    layer.setStyle({ weight: 4, opacity: 0.9 });
                });
                
                layer.on('mouseout', () => {
                    layer.setStyle(style(feature));
                });
            }
        });
        
        this.layer.addTo(this.map);
        
        // Ajouter des marqueurs au centre des zones
        this.addZoneMarkers(geojsonData.features);
    }
    
    createPopup(properties) {
        return `
            <div class="sdr-popup">
                <h5>📡 ${properties.name}</h5>
                <div class="sdr-metrics">
                    <table>
                        <tr>
                            <td><strong>Statut:</strong></td>
                            <td><span class="status-badge ${properties.health_status.toLowerCase()}">
                                ${properties.health_status}
                            </span></td>
                        </tr>
                        <tr>
                            <td><strong>Activité:</strong></td>
                            <td>${properties.total_activity.toFixed(2)}</td>
                        </tr>
                        <tr>
                            <td><strong>Score anomalie:</strong></td>
                            <td>${properties.anomaly_score.toFixed(1)}/100</td>
                        </tr>
                        <tr>
                            <td><strong>Risque géopolitique:</strong></td>
                            <td>${properties.geopolitical_risk.toFixed(1)}/100</td>
                        </tr>
                        <tr>
                            <td><strong>Santé communications:</strong></td>
                            <td>${properties.communication_health.toFixed(1)}/100</td>
                        </tr>
                    </table>
                </div>
                <div class="sdr-actions">
                    <button class="btn-small" onclick="showSDRAnalysis('${properties.zone_id}')">
                        📊 Analyse détaillée
                    </button>
                    <button class="btn-small" onclick="showTimeline('${properties.zone_id}')">
                        📈 Timeline 24h
                    </button>
                </div>
            </div>
        `;
    }
    
    addZoneMarkers(features) {
        features.forEach(feature => {
            const center = feature.properties.center;
            if (center && center.length === 2) {
                const marker = L.marker(center, {
                    icon: L.divIcon({
                        className: `sdr-marker ${feature.properties.health_status.toLowerCase()}`,
                        html: `<div class="marker-icon">📡</div>`,
                        iconSize: [30, 30]
                    })
                });
                
                marker.bindPopup(this.createPopup(feature.properties));
                marker.addTo(this.map);
            }
        });
    }
    
    updateLastUpdate(timestamp) {
        const element = document.getElementById('sdr-last-update');
        if (element && timestamp) {
            const date = new Date(timestamp);
            element.textContent = date.toLocaleTimeString();
        }
    }
    
    onZoneClick(properties) {
        // Événement personnalisable
        if (typeof this.options.onZoneClick === 'function') {
            this.options.onZoneClick(properties);
        }
        
        // Émettre un événement global
        document.dispatchEvent(new CustomEvent('sdr:zone-click', {
            detail: properties
        }));
    }
    
    showTimeline(zoneId) {
        this.loadTimeline(zoneId).then(timelineData => {
            this.displayTimelineChart(timelineData);
        });
    }
    
    async loadTimeline(zoneId) {
        try {
            const response = await fetch(`${this.options.apiUrl}/timeline/${zoneId}?hours=24`);
            return await response.json();
        } catch (error) {
            console.error('❌ Erreur timeline:', error);
            return null;
        }
    }
    
    displayTimelineChart(data) {
        // Utiliser Chart.js ou Plotly pour afficher la timeline
        console.log('Timeline data:', data);
        // Implémentation de la visualisation...
    }
    
    destroy() {
        if (this.layer) {
            this.map.removeLayer(this.layer);
        }
        if (this.legend) {
            this.map.removeControl(this.legend);
        }
    }
}

// Fonctions globales pour l'interface
window.showSDRAnalysis = function(zoneId) {
    fetch(`/api/sdr/zone/${zoneId}?hours=24`)
        .then(response => response.json())
        .then(data => {
            // Afficher l'analyse dans un modal
            console.log('Analysis data:', data);
            // Implémentation du modal...
        });
};

window.showSDRComparison = function(zone1, zone2) {
    fetch(`/api/sdr/compare?zone1=${zone1}&zone2=${zone2}&hours=24`)
        .then(response => response.json())
        .then(data => {
            // Afficher la comparaison
            console.log('Comparison data:', data);
            // Implémentation de la comparaison...
        });
};

// Initialisation automatique
document.addEventListener('DOMContentLoaded', () => {
    const map = window.geopolMap; // Supposant que votre carte est accessible globalement
    if (map) {
        window.sdrLayer = new SDRLayer(map, {
            refreshInterval: 300000, // 5 minutes
            onZoneClick: (properties) => {
                console.log('Zone SDR cliquée:', properties);
            }
        });
    }
});