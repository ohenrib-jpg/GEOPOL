/**
 * Satellite Panel - Frontend JavaScript
 *
 * Gère l'interface utilisateur du panneau satellite :
 * - Chargement et affichage des couches
 * - Intégration Leaflet
 * - Gestion mode avancé
 * - Recherche et filtrage
 * - Contrôles carte
 *
 * Version: 2.0.0
 * Author: GEOPOL Analytics
 */

class SatellitePanel {
    constructor(config = {}) {
        this.config = {
            mapElementId: config.mapElementId || 'map',
            apiBaseUrl: config.apiBaseUrl || '/satellite/api',
            defaultCenter: config.defaultCenter || [48.8566, 2.3522],  // Paris
            defaultZoom: config.defaultZoom || 5,
            ...config
        };

        // État
        this.map = null;
        this.layers = {};
        this.currentLayer = null;
        this.activeLayerObject = null;
        this.advancedMode = false;
        this.allLayersData = {};

        console.log('🛰️ SatellitePanel initialisé');
    }

    /**
     * Initialise le panneau satellite
     */
    async init() {
        try {
            console.log('📡 Initialisation du panneau satellite...');

            // Créer la carte Leaflet
            this.initMap();

            // Charger les couches
            await this.loadLayers();

            // Vérifier le statut mode avancé
            await this.checkAdvancedStatus();

            console.log('✅ Panneau satellite initialisé');
            return true;

        } catch (error) {
            console.error('❌ Erreur initialisation:', error);
            this.showToast('Erreur initialisation du panneau', 'error');
            return false;
        }
    }

    /**
     * Initialise la carte Leaflet
     */
    initMap() {
        // Créer la carte
        this.map = L.map(this.config.mapElementId).setView(
            this.config.defaultCenter,
            this.config.defaultZoom
        );

        // Ajouter une couche de base par défaut (OSM)
        L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19
        }).addTo(this.map);

        console.log('🗺️ Carte Leaflet initialisée');
    }

    /**
     * Charge toutes les couches disponibles
     */
    async loadLayers() {
        try {
            this.showLoading(true);

            const response = await fetch(`${this.config.apiBaseUrl}/layers`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error || 'Erreur chargement couches');
            }

            this.allLayersData = data.layers;
            this.advancedMode = data.advanced_enabled;

            // Afficher les couches
            this.displayLayers('all');

            console.log(`✅ ${data.count} couches chargées`);
            this.showToast(`${data.count} couches disponibles`, 'success');

        } catch (error) {
            console.error('❌ Erreur chargement couches:', error);
            this.showToast('Impossible de charger les couches', 'error');
        } finally {
            this.showLoading(false);
        }
    }

    /**
     * Affiche les couches dans la sidebar
     */
    displayLayers(category = 'all') {
        const containers = {
            'all': document.getElementById('allLayersList'),
            'satellite': document.getElementById('satelliteLayersList'),
            'basemap': document.getElementById('basemapLayersList')
        };

        const container = containers[category];
        if (!container) return;

        container.innerHTML = '';

        // Filtrer les couches selon la catégorie
        let filteredLayers = Object.entries(this.allLayersData);

        if (category === 'satellite') {
            filteredLayers = filteredLayers.filter(([id, layer]) =>
                layer.category === 'satellite'
            );
        } else if (category === 'basemap') {
            filteredLayers = filteredLayers.filter(([id, layer]) =>
                layer.category === 'basemap'
            );
        }

        // Si aucune couche, afficher un message
        if (filteredLayers.length === 0) {
            container.innerHTML = '<p class="text-muted text-center">Aucune couche disponible</p>';
            return;
        }

        // Créer les cartes de couches
        filteredLayers.forEach(([layerId, layer]) => {
            const card = this.createLayerCard(layerId, layer);
            container.appendChild(card);
        });

        // Mettre à jour le select
        this.updateLayerSelect();
    }

    /**
     * Crée une carte de couche
     */
    createLayerCard(layerId, layer) {
        const card = document.createElement('div');
        card.className = 'layer-card';
        card.dataset.layerId = layerId;

        // Badge catégorie
        const badgeClass = `badge-${layer.category || 'satellite'}`;
        const categoryText = this.getCategoryText(layer.category);

        card.innerHTML = `
            <div class="layer-name">${layer.name}</div>
            <div class="layer-description">${layer.description || 'Pas de description'}</div>
            <span class="layer-badge ${badgeClass}">${categoryText}</span>
            ${layer.requires_auth ? '<span class="layer-badge badge-satellite"><i class="fas fa-lock"></i> Avancé</span>' : ''}
        `;

        // Événement click
        card.addEventListener('click', () => {
            this.selectLayer(layerId);
        });

        return card;
    }

    /**
     * Retourne le texte de catégorie
     */
    getCategoryText(category) {
        const categories = {
            'satellite': 'Satellite',
            'basemap': 'Fond de carte',
            'thematic': 'Thématique'
        };
        return categories[category] || 'Autre';
    }

    /**
     * Sélectionne une couche
     */
    async selectLayer(layerId) {
        try {
            console.log(`📡 Sélection couche: ${layerId}`);

            // Marquer comme sélectionnée dans l'UI
            document.querySelectorAll('.layer-card').forEach(card => {
                card.classList.remove('selected');
            });

            const card = document.querySelector(`.layer-card[data-layer-id="${layerId}"]`);
            if (card) {
                card.classList.add('selected');
            }

            // Charger la couche sur la carte
            await this.loadLayerOnMap(layerId);

            // Mettre à jour le select
            document.getElementById('activeLayerSelect').value = layerId;
            this.currentLayer = layerId;

        } catch (error) {
            console.error('❌ Erreur sélection couche:', error);
            this.showToast('Erreur chargement de la couche', 'error');
        }
    }

    /**
     * Charge une couche sur la carte
     */
    async loadLayerOnMap(layerId) {
        const layer = this.allLayersData[layerId];
        if (!layer) {
            console.error(`Couche ${layerId} non trouvée`);
            return;
        }

        // Supprimer la couche active précédente
        if (this.activeLayerObject) {
            this.map.removeLayer(this.activeLayerObject);
            this.activeLayerObject = null;
        }

        // Ajouter la nouvelle couche
        if (layer.url_template) {
            // Couche tuiles
            this.activeLayerObject = L.tileLayer(layer.url_template, {
                attribution: layer.attribution || '',
                maxZoom: layer.max_zoom || 19,
                subdomains: layer.subdomains || ['a', 'b', 'c']
            }).addTo(this.map);

            console.log(`✅ Couche ${layerId} chargée (tuiles)`);
            this.showToast(`Couche "${layer.name}" chargée`, 'success');

        } else if (layer.type === 'wms') {
            // Couche WMS - nécessite bbox
            const bounds = this.map.getBounds();
            const bbox = [
                bounds.getWest(),
                bounds.getSouth(),
                bounds.getEast(),
                bounds.getNorth()
            ].join(',');

            try {
                const response = await fetch(
                    `${this.config.apiBaseUrl}/layer-url/${layerId}?bbox=${bbox}`
                );

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                const data = await response.json();

                if (data.success && data.url) {
                    // Utiliser l'URL WMS
                    this.activeLayerObject = L.tileLayer.wms(data.url, {
                        layers: layer.wms_layers,
                        format: layer.wms_format || 'image/png',
                        transparent: true,
                        attribution: layer.attribution || ''
                    }).addTo(this.map);

                    console.log(`✅ Couche WMS ${layerId} chargée`);
                    this.showToast(`Couche "${layer.name}" chargée`, 'success');
                }

            } catch (error) {
                console.error('❌ Erreur chargement WMS:', error);
                this.showToast('Erreur chargement couche WMS', 'error');
            }

        } else if (layer.requires_auth) {
            // Couche avancée Sentinel
            this.showToast('Couche avancée - Nécessite mode avancé activé', 'info');
        }
    }

    /**
     * Change l'opacité de la couche active
     */
    changeOpacity(value) {
        if (this.activeLayerObject) {
            const opacity = value / 100;
            this.activeLayerObject.setOpacity(opacity);
            document.getElementById('opacityValue').textContent = value;
        }
    }

    /**
     * Change la couche active depuis le select
     */
    changeActiveLayer(layerId) {
        if (layerId) {
            this.selectLayer(layerId);
        } else {
            this.clearLayer();
        }
    }

    /**
     * Efface la couche active
     */
    clearLayer() {
        if (this.activeLayerObject) {
            this.map.removeLayer(this.activeLayerObject);
            this.activeLayerObject = null;
            this.currentLayer = null;

            // Réinitialiser UI
            document.querySelectorAll('.layer-card').forEach(card => {
                card.classList.remove('selected');
            });

            document.getElementById('activeLayerSelect').value = '';
            document.getElementById('opacitySlider').value = 100;
            document.getElementById('opacityValue').textContent = '100';

            console.log('🗑️ Couche effacée');
            this.showToast('Couche supprimée', 'info');
        }
    }

    /**
     * Met à jour le select de couches
     */
    updateLayerSelect() {
        const select = document.getElementById('activeLayerSelect');
        select.innerHTML = '<option value="">Aucune</option>';

        Object.entries(this.allLayersData).forEach(([layerId, layer]) => {
            const option = document.createElement('option');
            option.value = layerId;
            option.textContent = layer.name;
            select.appendChild(option);
        });
    }

    /**
     * Recherche de couches
     */
    searchLayers(query) {
        query = query.toLowerCase().trim();

        document.querySelectorAll('.layer-card').forEach(card => {
            const layerId = card.dataset.layerId;
            const layer = this.allLayersData[layerId];

            const matchName = layer.name.toLowerCase().includes(query);
            const matchDescription = (layer.description || '').toLowerCase().includes(query);
            const matchId = layerId.toLowerCase().includes(query);

            if (query === '' || matchName || matchDescription || matchId) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
    }

    /**
     * Change d'onglet
     */
    switchTab(tabName) {
        // Désactiver tous les boutons et contenus
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });

        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });

        // Activer le bon onglet
        event.target.classList.add('active');

        if (tabName === 'all') {
            document.getElementById('allLayers').classList.add('active');
            this.displayLayers('all');
        } else if (tabName === 'satellite') {
            document.getElementById('satelliteLayers').classList.add('active');
            this.displayLayers('satellite');
        } else if (tabName === 'basemap') {
            document.getElementById('basemapLayers').classList.add('active');
            this.displayLayers('basemap');
        }
    }

    // ========================================
    // MODE AVANCÉ
    // ========================================

    /**
     * Vérifie le statut du mode avancé
     */
    async checkAdvancedStatus() {
        try {
            const response = await fetch(`${this.config.apiBaseUrl}/advanced/status`);
            if (!response.ok) return;

            const data = await response.json();

            if (data.success && data.enabled) {
                this.advancedMode = true;
                this.updateAdvancedUI(true);
            } else {
                this.advancedMode = false;
                this.updateAdvancedUI(false);
            }

        } catch (error) {
            console.error('❌ Erreur vérification mode avancé:', error);
        }
    }

    /**
     * Met à jour l'UI du mode avancé
     */
    updateAdvancedUI(enabled) {
        const indicator = document.getElementById('advancedIndicator');
        const statusText = document.getElementById('advancedStatusText');
        const button = document.getElementById('toggleAdvancedBtn');

        if (enabled) {
            indicator.classList.add('active');
            statusText.textContent = 'Mode Avancé Actif';
            button.innerHTML = '<i class="fas fa-times"></i> Désactiver Mode Avancé';
            button.onclick = () => this.deactivateAdvancedMode();
        } else {
            indicator.classList.remove('active');
            statusText.textContent = 'Mode Public';
            button.innerHTML = '<i class="fas fa-key"></i> Activer Mode Avancé';
            button.onclick = () => this.toggleAdvancedMode();
        }
    }

    /**
     * Toggle mode avancé (ouvre modal)
     */
    toggleAdvancedMode() {
        if (this.advancedMode) {
            this.deactivateAdvancedMode();
        } else {
            // Ouvrir le modal
            const modal = new bootstrap.Modal(document.getElementById('advancedModal'));
            modal.show();
        }
    }

    /**
     * Active le mode avancé
     */
    async activateAdvancedMode() {
        const clientId = document.getElementById('clientIdInput').value.trim();
        const clientSecret = document.getElementById('clientSecretInput').value.trim();
        const errorDiv = document.getElementById('advancedError');

        // Validation
        if (!clientId || !clientSecret) {
            errorDiv.textContent = 'Client ID et Client Secret requis';
            errorDiv.style.display = 'block';
            return;
        }

        errorDiv.style.display = 'none';

        try {
            const response = await fetch(`${this.config.apiBaseUrl}/advanced/enable`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    client_id: clientId,
                    client_secret: clientSecret
                })
            });

            const data = await response.json();

            if (data.success) {
                // Fermer le modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('advancedModal'));
                modal.hide();

                // Mettre à jour l'UI
                this.advancedMode = true;
                this.updateAdvancedUI(true);

                // Recharger les couches
                await this.loadLayers();

                this.showToast('Mode avancé activé avec succès', 'success');
            } else {
                errorDiv.textContent = data.error || 'Échec activation';
                errorDiv.style.display = 'block';
            }

        } catch (error) {
            console.error('❌ Erreur activation mode avancé:', error);
            errorDiv.textContent = 'Erreur réseau';
            errorDiv.style.display = 'block';
        }
    }

    /**
     * Désactive le mode avancé
     */
    async deactivateAdvancedMode() {
        try {
            const response = await fetch(`${this.config.apiBaseUrl}/advanced/disable`, {
                method: 'POST'
            });

            const data = await response.json();

            if (data.success) {
                this.advancedMode = false;
                this.updateAdvancedUI(false);

                // Recharger les couches
                await this.loadLayers();

                this.showToast('Mode avancé désactivé', 'info');
            }

        } catch (error) {
            console.error('❌ Erreur désactivation mode avancé:', error);
            this.showToast('Erreur désactivation', 'error');
        }
    }

    // ========================================
    // UTILITAIRES
    // ========================================

    /**
     * Affiche/masque le loader
     */
    showLoading(show) {
        const loaders = document.querySelectorAll('.loading-spinner');
        loaders.forEach(loader => {
            loader.style.display = show ? 'block' : 'none';
        });
    }

    /**
     * Affiche un toast notification
     */
    showToast(message, type = 'info') {
        const container = document.getElementById('toastContainer');

        const toast = document.createElement('div');
        toast.className = `custom-toast toast-${type}`;
        toast.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px;">
                <i class="fas fa-${this.getToastIcon(type)}"></i>
                <span>${message}</span>
            </div>
        `;

        container.appendChild(toast);

        // Auto-suppression après 3 secondes
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transition = 'opacity 0.3s';

            setTimeout(() => {
                container.removeChild(toast);
            }, 300);
        }, 3000);
    }

    /**
     * Retourne l'icône pour un toast
     */
    getToastIcon(type) {
        const icons = {
            'success': 'check-circle',
            'error': 'exclamation-circle',
            'info': 'info-circle',
            'warning': 'exclamation-triangle'
        };
        return icons[type] || 'info-circle';
    }

    /**
     * Nettoyage
     */
    destroy() {
        if (this.map) {
            this.map.remove();
            this.map = null;
        }

        if (this.activeLayerObject) {
            this.activeLayerObject = null;
        }

        console.log('🗑️ SatellitePanel détruit');
    }
}

// Export global
window.SatellitePanel = SatellitePanel;
