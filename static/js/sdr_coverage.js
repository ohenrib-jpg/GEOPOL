// static/js/sdr_coverage.js
/**
 * Gestionnaire de la couverture réseau SDR avec Leaflet Heatmap
 *
 * Fonctionnalités :
 * - Affichage de la heatmap de densité de stations SDR
 * - Marqueurs pour zones sous-couvertes
 * - Statistiques de couverture
 * - Intégration avec geopol_data_map
 *
 * Dépendances :
 * - Leaflet.js
 * - Leaflet.heat plugin (https://github.com/Leaflet/Leaflet.heat)
 *
 * Version: 1.0.0
 */

class SDRCoverageManager {
    constructor(map, config = {}) {
        this.map = map;
        this.config = {
            apiBaseUrl: config.apiBaseUrl || '/api/sdr/coverage',
            refreshInterval: config.refreshInterval || 300000, // 5 minutes
            heatmapOptions: {
                radius: config.heatmapRadius || 25,
                blur: config.heatmapBlur || 15,
                maxZoom: config.heatmapMaxZoom || 10,
                max: config.heatmapMax || 1.0,
                gradient: config.heatmapGradient || {
                    0.0: 'blue',
                    0.3: 'lime',
                    0.5: 'yellow',
                    0.7: 'orange',
                    1.0: 'red'
                }
            },
            ...config
        };

        // Layers
        this.heatmapLayer = null;
        this.undercoveredLayer = null;
        this.markersLayer = null;

        // Data
        this.coverageData = null;
        this.statistics = null;

        // État
        this.isVisible = false;
        this.isLoading = false;
        this.autoRefresh = false;
        this.refreshTimer = null;

        console.log('🗺️ SDRCoverageManager initialisé');
    }

    /**
     * Initialise et affiche la couverture SDR
     */
    async init() {
        try {
            console.log('📡 Initialisation de la couverture SDR...');

            // Charger les données
            await this.loadCoverageData();

            // Créer les layers
            this.createLayers();

            // Afficher sur la carte
            this.show();

            console.log('✅ Couverture SDR initialisée');
            return true;

        } catch (error) {
            console.error('❌ Erreur initialisation SDR Coverage:', error);
            this.showError('Impossible de charger la couverture SDR');
            return false;
        }
    }

    /**
     * Charge les données de couverture depuis l'API
     */
    async loadCoverageData() {
        if (this.isLoading) {
            console.warn('⚠️ Chargement déjà en cours');
            return;
        }

        this.isLoading = true;
        this.showLoader();

        try {
            // Charger la heatmap
            const heatmapResponse = await fetch(`${this.config.apiBaseUrl}/heatmap?active_only=true`);
            if (!heatmapResponse.ok) {
                throw new Error(`HTTP ${heatmapResponse.status}`);
            }
            const heatmapData = await heatmapResponse.json();

            // Charger les zones sous-couvertes
            const undercoveredResponse = await fetch(`${this.config.apiBaseUrl}/undercovered?active_only=true`);
            if (!undercoveredResponse.ok) {
                throw new Error(`HTTP ${undercoveredResponse.status}`);
            }
            const undercoveredData = await undercoveredResponse.json();

            // Charger les statistiques
            const statsResponse = await fetch(`${this.config.apiBaseUrl}/statistics?active_only=true`);
            if (!statsResponse.ok) {
                throw new Error(`HTTP ${statsResponse.status}`);
            }
            const statsData = await statsResponse.json();

            // Stocker les données
            this.coverageData = {
                heatmap: heatmapData.heatmap || [],
                undercovered: undercoveredData.undercovered_zones || [],
                num_stations: heatmapData.num_stations || 0,
                timestamp: heatmapData.timestamp || new Date().toISOString()
            };

            this.statistics = statsData.statistics || {};

            console.log(`✅ Données chargées: ${this.coverageData.heatmap.length} points heatmap, ${this.coverageData.undercovered.length} zones sous-couvertes`);

            return this.coverageData;

        } catch (error) {
            console.error('❌ Erreur chargement données:', error);
            throw error;

        } finally {
            this.isLoading = false;
            this.hideLoader();
        }
    }

    /**
     * Crée les layers Leaflet
     */
    createLayers() {
        // Supprimer les layers existants
        this.removeLayers();

        if (!this.coverageData) {
            console.warn('⚠️ Pas de données pour créer les layers');
            return;
        }

        // Créer la heatmap layer
        this.createHeatmapLayer();

        // Créer les marqueurs pour zones sous-couvertes
        this.createUndercoveredMarkers();

        console.log('✅ Layers créés');
    }

    /**
     * Crée la heatmap Leaflet
     */
    createHeatmapLayer() {
        if (!this.coverageData || !this.coverageData.heatmap.length) {
            console.warn('⚠️ Pas de données heatmap');
            return;
        }

        // Vérifier que Leaflet.heat est disponible
        if (typeof L.heatLayer === 'undefined') {
            console.error('❌ Leaflet.heat plugin non chargé');
            this.showError('Plugin Leaflet Heatmap manquant');
            return;
        }

        // Préparer les données pour Leaflet.heat
        // Format: [[lat, lon, intensity], ...]
        const heatData = this.coverageData.heatmap.map(point => [
            point.lat,
            point.lon,
            point.intensity
        ]);

        // Créer le layer
        this.heatmapLayer = L.heatLayer(heatData, this.config.heatmapOptions);

        console.log(`✅ Heatmap créée: ${heatData.length} points`);
    }

    /**
     * Crée les marqueurs pour zones sous-couvertes
     */
    createUndercoveredMarkers() {
        if (!this.coverageData || !this.coverageData.undercovered.length) {
            console.log('ℹ️ Pas de zones sous-couvertes');
            return;
        }

        // Créer un layer group pour les marqueurs
        this.undercoveredLayer = L.layerGroup();

        // Ajouter un marqueur pour chaque zone
        this.coverageData.undercovered.forEach(zone => {
            const color = zone.level === 'CRITICAL' ? '#ff0000' : '#ff9900';
            const icon = zone.level === 'CRITICAL' ? '⚠️' : '⚡';

            // Créer un cercle
            const circle = L.circle([zone.lat, zone.lon], {
                color: color,
                fillColor: color,
                fillOpacity: 0.2,
                radius: 50000, // 50km en mètres
                weight: 2
            });

            // Créer un marqueur avec popup
            const marker = L.marker([zone.lat, zone.lon], {
                icon: L.divIcon({
                    html: `<div style="font-size: 24px;">${icon}</div>`,
                    className: 'sdr-undercovered-icon',
                    iconSize: [30, 30],
                    iconAnchor: [15, 15]
                })
            });

            // Popup avec infos
            const popup = L.popup({
                maxWidth: 300
            }).setContent(`
                <div class="sdr-coverage-popup">
                    <h4 style="margin: 0 0 10px 0; color: ${color};">
                        ${icon} Zone ${zone.level}
                    </h4>
                    <p style="margin: 5px 0;">
                        <strong>Densité:</strong> ${zone.density.toFixed(2)} stations/100km
                    </p>
                    <p style="margin: 5px 0; font-size: 0.9em; color: #666;">
                        Couverture insuffisante détectée
                    </p>
                </div>
            `);

            marker.bindPopup(popup);

            // Ajouter au layer
            circle.addTo(this.undercoveredLayer);
            marker.addTo(this.undercoveredLayer);
        });

        console.log(`✅ Marqueurs créés: ${this.coverageData.undercovered.length} zones`);
    }

    /**
     * Affiche les layers sur la carte
     */
    show() {
        if (!this.map) {
            console.error('❌ Carte non initialisée');
            return;
        }

        // Ajouter la heatmap
        if (this.heatmapLayer && !this.map.hasLayer(this.heatmapLayer)) {
            this.heatmapLayer.addTo(this.map);
            console.log('✅ Heatmap ajoutée à la carte');
        }

        // Ajouter les marqueurs
        if (this.undercoveredLayer && !this.map.hasLayer(this.undercoveredLayer)) {
            this.undercoveredLayer.addTo(this.map);
            console.log('✅ Marqueurs ajoutés à la carte');
        }

        this.isVisible = true;

        // Afficher les statistiques
        this.displayStatistics();
    }

    /**
     * Masque les layers de la carte
     */
    hide() {
        if (!this.map) return;

        // Retirer la heatmap
        if (this.heatmapLayer && this.map.hasLayer(this.heatmapLayer)) {
            this.map.removeLayer(this.heatmapLayer);
        }

        // Retirer les marqueurs
        if (this.undercoveredLayer && this.map.hasLayer(this.undercoveredLayer)) {
            this.map.removeLayer(this.undercoveredLayer);
        }

        this.isVisible = false;
        console.log('ℹ️ Couverture SDR masquée');
    }

    /**
     * Supprime tous les layers
     */
    removeLayers() {
        this.hide();

        if (this.heatmapLayer) {
            this.heatmapLayer = null;
        }

        if (this.undercoveredLayer) {
            this.undercoveredLayer.clearLayers();
            this.undercoveredLayer = null;
        }
    }

    /**
     * Toggle visibilité
     */
    toggle() {
        if (this.isVisible) {
            this.hide();
        } else {
            this.show();
        }
    }

    /**
     * Rafraîchit les données
     */
    async refresh() {
        console.log('🔄 Rafraîchissement de la couverture SDR...');

        try {
            await this.loadCoverageData();
            this.createLayers();

            if (this.isVisible) {
                this.show();
            }

            console.log('✅ Couverture SDR rafraîchie');
            return true;

        } catch (error) {
            console.error('❌ Erreur rafraîchissement:', error);
            return false;
        }
    }

    /**
     * Active le rafraîchissement automatique
     */
    startAutoRefresh() {
        if (this.autoRefresh) {
            console.warn('⚠️ Auto-refresh déjà actif');
            return;
        }

        this.autoRefresh = true;
        this.refreshTimer = setInterval(() => {
            this.refresh();
        }, this.config.refreshInterval);

        console.log(`✅ Auto-refresh activé (${this.config.refreshInterval / 1000}s)`);
    }

    /**
     * Désactive le rafraîchissement automatique
     */
    stopAutoRefresh() {
        if (!this.autoRefresh) return;

        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
            this.refreshTimer = null;
        }

        this.autoRefresh = false;
        console.log('ℹ️ Auto-refresh désactivé');
    }

    /**
     * Affiche les statistiques dans l'UI
     */
    displayStatistics() {
        if (!this.statistics) return;

        const statsContainer = document.getElementById('sdr-coverage-stats');
        if (!statsContainer) {
            console.warn('⚠️ Container stats non trouvé');
            return;
        }

        statsContainer.innerHTML = `
            <div class="sdr-stats">
                <h4>📊 Statistiques de couverture</h4>
                <div class="stats-grid">
                    <div class="stat-item">
                        <span class="stat-label">Stations actives:</span>
                        <span class="stat-value">${this.statistics.total_stations || 0}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Densité moyenne:</span>
                        <span class="stat-value">${(this.statistics.avg_density || 0).toFixed(2)}</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Couverture:</span>
                        <span class="stat-value">${this.statistics.coverage_percentage || 0}%</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-label">Zones critiques:</span>
                        <span class="stat-value" style="color: ${this.coverageData.undercovered.filter(z => z.level === 'CRITICAL').length > 0 ? '#ff0000' : '#00ff00'}">
                            ${this.coverageData.undercovered.filter(z => z.level === 'CRITICAL').length}
                        </span>
                    </div>
                </div>
                <p class="stats-timestamp">
                    Dernière mise à jour: ${new Date(this.coverageData.timestamp).toLocaleString('fr-FR')}
                </p>
            </div>
        `;
    }

    /**
     * Affiche un loader
     */
    showLoader() {
        const loaderContainer = document.getElementById('sdr-coverage-loader');
        if (loaderContainer) {
            loaderContainer.style.display = 'block';
        }
    }

    /**
     * Masque le loader
     */
    hideLoader() {
        const loaderContainer = document.getElementById('sdr-coverage-loader');
        if (loaderContainer) {
            loaderContainer.style.display = 'none';
        }
    }

    /**
     * Affiche un message d'erreur
     */
    showError(message) {
        console.error(`❌ ${message}`);

        const errorContainer = document.getElementById('sdr-coverage-error');
        if (errorContainer) {
            errorContainer.innerHTML = `
                <div class="alert alert-danger" role="alert">
                    <strong>Erreur:</strong> ${message}
                </div>
            `;
            errorContainer.style.display = 'block';

            // Masquer après 5 secondes
            setTimeout(() => {
                errorContainer.style.display = 'none';
            }, 5000);
        }
    }

    /**
     * Nettoyage
     */
    destroy() {
        this.stopAutoRefresh();
        this.removeLayers();
        this.coverageData = null;
        this.statistics = null;
        console.log('🗑️ SDRCoverageManager détruit');
    }
}

// Export pour utilisation globale
window.SDRCoverageManager = SDRCoverageManager;
