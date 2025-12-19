/**
 * Gestionnaire de configurations et profils utilisateur pour la carte géopolitique.
 *
 * Fonctionnalités:
 * - Sauvegarde/chargement de profils dans localStorage
 * - Synchronisation avec l'API backend
 * - Application de profils à la carte
 * - Capture de l'état actuel de la carte
 *
 * @version 1.0.0
 */

class ConfigManager {
    constructor() {
        this.STORAGE_KEY = 'geopol_map_config';
        this.CURRENT_PROFILE_KEY = 'geopol_current_profile';
        this.API_BASE = '/api/geopol/profiles';

        // Cache des profils
        this.profiles = {
            'default': null,
            'analyst': null,
            'meteo': null
        };

        // État actuel de la carte
        this.currentState = null;

        // Profil actuellement actif
        this.activeProfile = null;

        // État "dirty" (modifié)
        this.isDirty = false;

        // Référence au badge
        this.dirtyBadge = null;

        // Initialisation
        this.init();
    }

    /**
     * Initialise le gestionnaire de configuration.
     */
    async init() {
        console.log('🎨 Initialisation du ConfigManager...');

        // Récupérer la référence au badge
        this.dirtyBadge = document.getElementById('dirtyBadge');

        // Charger les profils par défaut depuis le backend
        await this.loadDefaultProfiles();

        // Charger le dernier profil actif
        const lastProfileName = this.getLastActiveProfile();
        if (lastProfileName) {
            console.log(`📂 Chargement du dernier profil actif: ${lastProfileName}`);
            await this.loadProfile(lastProfileName, false); // false = ne pas appliquer immédiatement
        } else {
            // Charger le profil par défaut
            console.log('📂 Chargement du profil par défaut');
            await this.loadProfile('default', false);
        }

        // Initialiser la détection de dirty state
        this.initDirtyStateDetection();

        console.log('✅ ConfigManager initialisé');
    }

    /**
     * Charge les profils par défaut depuis le backend.
     */
    async loadDefaultProfiles() {
        try {
            const response = await fetch(this.API_BASE);
            const data = await response.json();

            if (data.success) {
                console.log(`📦 ${data.count} profils disponibles`);

                // Charger les profils par défaut
                for (const profileName of ['default', 'analyst', 'meteo']) {
                    const profileResponse = await fetch(`${this.API_BASE}/${profileName}`);
                    const profileData = await profileResponse.json();

                    if (profileData.success) {
                        this.profiles[profileName] = profileData.profile;
                        console.log(`  ✓ Profil "${profileName}" chargé`);
                    }
                }
            }
        } catch (error) {
            console.error('❌ Erreur lors du chargement des profils par défaut:', error);
        }
    }

    /**
     * Récupère l'état actuel de la carte.
     * Cette fonction doit être implémentée pour capturer tous les paramètres actifs.
     *
     * @returns {Object} État actuel de la carte
     */
    captureCurrentState() {
        const state = {
            layers: {},
            entities: [],
            weather: {
                metric: 'temperature',
                show_forecast: false,
                forecast_days: 7,
                color_scale: 'default'
            },
            earthquakes: {
                min_magnitude: 4.5,
                time_period: 'last_7_days',
                show_legends: true,
                pulse_animation: true
            },
            theme: 'light',
            entity_marker_size: 'medium',
            show_tooltips: true,
            default_view: {
                center: [20, 0],
                zoom: 2
            }
        };

        // Capturer l'état des couches (checkboxes)
        const layerCheckboxes = {
            'geopolitical_entities': document.getElementById('geopolitical-entities-toggle'),
            'sdr_receivers': document.getElementById('sdr-receivers-toggle'),
            'weather': document.getElementById('meteo-layer-toggle'),
            'earthquakes': document.getElementById('earthquakes-layer-toggle')
        };

        for (const [layerName, checkbox] of Object.entries(layerCheckboxes)) {
            if (checkbox) {
                state.layers[layerName] = {
                    enabled: checkbox.checked,
                    opacity: 0.7, // Valeur par défaut
                    z_index: this.getLayerZIndex(layerName)
                };
            }
        }

        // Capturer les entités géopolitiques actives
        // (à adapter selon votre implémentation)
        if (state.layers['geopolitical_entities']?.enabled) {
            state.entities = ['GPE']; // Par défaut
        }

        // Capturer la magnitude des séismes
        const magnitudeSlider = document.getElementById('magnitude-slider');
        if (magnitudeSlider) {
            state.earthquakes.min_magnitude = parseFloat(magnitudeSlider.value);
        }

        // Capturer la vue actuelle de la carte (si disponible)
        if (typeof map !== 'undefined' && map) {
            const center = map.getCenter();
            state.default_view = {
                center: [center.lat, center.lng],
                zoom: map.getZoom()
            };
        }

        this.currentState = state;
        return state;
    }

    /**
     * Retourne le z-index d'une couche.
     */
    getLayerZIndex(layerName) {
        const zIndexMap = {
            'geopolitical_entities': 350,
            'sdr_receivers': 450,
            'weather': 200,
            'earthquakes': 400
        };
        return zIndexMap[layerName] || 100;
    }

    /**
     * Sauvegarde l'état actuel en tant que nouveau profil.
     *
     * @param {string} name - Nom du profil
     * @param {string} description - Description du profil
     * @returns {Promise<boolean>} Succès de la sauvegarde
     */
    async saveCurrentAsProfile(name, description) {
        try {
            // Vérifier si le profil existe déjà
            const existingProfile = await this.loadProfile(name, false);
            if (existingProfile) {
                // Empêcher l'écrasement des profils par défaut
                if (['default', 'analyst', 'meteo'].includes(name)) {
                    alert(`❌ Impossible d'écraser le profil par défaut "${name}".\n\nVeuillez choisir un autre nom.`);
                    console.error(`❌ Tentative d'écrasement du profil par défaut "${name}"`);
                    return false;
                }

                // Demander confirmation pour les profils personnalisés
                const overwrite = confirm(
                    `⚠️ Un profil nommé "${name}" existe déjà.\n\nVoulez-vous l'écraser ?`
                );
                if (!overwrite) {
                    console.log('❌ Sauvegarde annulée par l\'utilisateur');
                    return false;
                }
            }

            // Capturer l'état actuel
            const currentState = this.captureCurrentState();

            // Créer le profil via l'API
            const response = await fetch(`${this.API_BASE}/from-state`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: name,
                    description: description,
                    current_state: currentState
                })
            });

            const data = await response.json();

            if (data.success) {
                console.log(`✅ Profil "${name}" sauvegardé avec succès`);

                // Sauvegarder aussi dans localStorage
                this.saveToLocalStorage(name, data.profile);

                return true;
            } else {
                console.error(`❌ Erreur lors de la sauvegarde du profil: ${data.error}`);
                return false;
            }
        } catch (error) {
            console.error('❌ Erreur lors de la sauvegarde du profil:', error);
            return false;
        }
    }

    /**
     * Charge un profil et l'applique à la carte.
     *
     * @param {string} name - Nom du profil
     * @param {boolean} apply - Appliquer le profil immédiatement (défaut: true)
     * @returns {Promise<Object|null>} Le profil chargé ou null
     */
    async loadProfile(name, apply = true) {
        try {
            // Vérifier d'abord dans le cache local
            if (this.profiles[name]) {
                console.log(`📂 Profil "${name}" chargé depuis le cache`);
                const profile = this.profiles[name];

                if (apply) {
                    this.applyProfile(profile);
                }

                return profile;
            }

            // Sinon, charger depuis l'API
            const response = await fetch(`${this.API_BASE}/${name}`);
            const data = await response.json();

            if (data.success) {
                console.log(`📂 Profil "${name}" chargé depuis l'API`);
                const profile = data.profile;

                // Mettre en cache
                this.profiles[name] = profile;

                if (apply) {
                    this.applyProfile(profile);
                }

                return profile;
            } else {
                console.error(`❌ Profil "${name}" non trouvé`);
                return null;
            }
        } catch (error) {
            console.error(`❌ Erreur lors du chargement du profil "${name}":`, error);
            return null;
        }
    }

    /**
     * Applique un profil à la carte.
     *
     * @param {Object} profile - Le profil à appliquer
     */
    applyProfile(profile) {
        console.log(`🎨 Application du profil "${profile.name}"...`);

        // Appliquer les couches
        for (const [layerName, layerConfig] of Object.entries(profile.layers)) {
            this.applyLayerConfig(layerName, layerConfig);
        }

        // Appliquer la configuration météo
        if (profile.weather) {
            this.applyWeatherConfig(profile.weather);
        }

        // Appliquer la configuration séismes
        if (profile.earthquakes) {
            this.applyEarthquakeConfig(profile.earthquakes);
        }

        // Appliquer le thème
        if (profile.theme) {
            this.applyTheme(profile.theme);
        }

        // Appliquer la vue par défaut
        if (profile.default_view && typeof map !== 'undefined' && map) {
            const { center, zoom } = profile.default_view;
            map.setView(center, zoom);
        }

        // Sauvegarder comme profil actif
        this.activeProfile = profile;
        this.setLastActiveProfile(profile.name);

        // Réinitialiser le dirty state (le profil vient d'être chargé, donc clean)
        this.setDirty(false);

        console.log(`✅ Profil "${profile.name}" appliqué`);

        // Déclencher un événement personnalisé
        window.dispatchEvent(new CustomEvent('profileApplied', {
            detail: { profile: profile }
        }));
    }

    /**
     * Applique la configuration d'une couche.
     *
     * @param {string} layerName - Nom de la couche
     * @param {Object} config - Configuration de la couche
     */
    applyLayerConfig(layerName, config) {
        const checkboxMap = {
            'geopolitical_entities': 'geopolitical-entities-toggle',
            'sdr_receivers': 'sdr-receivers-toggle',
            'weather': 'meteo-layer-toggle',
            'earthquakes': 'earthquakes-layer-toggle'
        };

        const checkboxId = checkboxMap[layerName];
        if (!checkboxId) return;

        const checkbox = document.getElementById(checkboxId);
        if (!checkbox) return;

        // Appliquer l'état enabled
        if (checkbox.checked !== config.enabled) {
            checkbox.checked = config.enabled;

            // Déclencher l'événement change pour mettre à jour la carte
            checkbox.dispatchEvent(new Event('change'));
        }
    }

    /**
     * Applique la configuration météo.
     *
     * @param {Object} weatherConfig - Configuration météo
     */
    applyWeatherConfig(weatherConfig) {
        // À implémenter selon votre interface météo
        console.log('🌤️ Application de la config météo:', weatherConfig);
    }

    /**
     * Applique la configuration des séismes.
     *
     * @param {Object} earthquakeConfig - Configuration séismes
     */
    applyEarthquakeConfig(earthquakeConfig) {
        // Appliquer la magnitude minimale
        const magnitudeSlider = document.getElementById('magnitude-slider');
        if (magnitudeSlider && earthquakeConfig.min_magnitude) {
            magnitudeSlider.value = earthquakeConfig.min_magnitude;

            // Mettre à jour l'affichage
            const magnitudeValue = document.getElementById('magnitude-value');
            if (magnitudeValue) {
                magnitudeValue.textContent = earthquakeConfig.min_magnitude.toFixed(1);
            }

            // Déclencher l'événement pour mettre à jour la carte
            magnitudeSlider.dispatchEvent(new Event('input'));
        }
    }

    /**
     * Applique un thème visuel.
     *
     * @param {string} theme - Nom du thème (light, dark, satellite)
     */
    applyTheme(theme) {
        const mapElement = document.querySelector('.geopol-map');
        if (mapElement) {
            mapElement.setAttribute('data-theme', theme);
        }

        // Mettre à jour les tuiles de la carte si nécessaire
        if (typeof map !== 'undefined' && map) {
            // Implémenter le changement de tuiles selon le thème
            console.log(`🎨 Thème "${theme}" appliqué`);
        }
    }

    /**
     * Liste tous les profils disponibles.
     *
     * @returns {Promise<Array>} Liste des profils
     */
    async listProfiles() {
        try {
            const response = await fetch(this.API_BASE);
            const data = await response.json();

            if (data.success) {
                return Object.entries(data.profiles).map(([name, info]) => ({
                    name: name,
                    ...info
                }));
            }
            return [];
        } catch (error) {
            console.error('❌ Erreur lors de la récupération des profils:', error);
            return [];
        }
    }

    /**
     * Supprime un profil personnalisé.
     *
     * @param {string} name - Nom du profil
     * @returns {Promise<boolean>} Succès de la suppression
     */
    async deleteProfile(name) {
        try {
            const response = await fetch(`${this.API_BASE}/${name}`, {
                method: 'DELETE'
            });

            const data = await response.json();

            if (data.success) {
                console.log(`🗑️ Profil "${name}" supprimé`);

                // Supprimer du cache
                delete this.profiles[name];

                // Supprimer du localStorage
                this.removeFromLocalStorage(name);

                return true;
            } else {
                console.error(`❌ Erreur lors de la suppression: ${data.error}`);
                return false;
            }
        } catch (error) {
            console.error('❌ Erreur lors de la suppression du profil:', error);
            return false;
        }
    }

    /**
     * Sauvegarde un profil dans le localStorage.
     *
     * @param {string} name - Nom du profil
     * @param {Object} profile - Le profil à sauvegarder
     */
    saveToLocalStorage(name, profile) {
        try {
            const allProfiles = this.getAllFromLocalStorage();
            allProfiles[name] = profile;

            localStorage.setItem(this.STORAGE_KEY, JSON.stringify(allProfiles));
            console.log(`💾 Profil "${name}" sauvegardé dans localStorage`);
        } catch (error) {
            console.error('❌ Erreur localStorage:', error);
        }
    }

    /**
     * Récupère tous les profils du localStorage.
     *
     * @returns {Object} Tous les profils
     */
    getAllFromLocalStorage() {
        try {
            const data = localStorage.getItem(this.STORAGE_KEY);
            return data ? JSON.parse(data) : {};
        } catch (error) {
            console.error('❌ Erreur lecture localStorage:', error);
            return {};
        }
    }

    /**
     * Supprime un profil du localStorage.
     *
     * @param {string} name - Nom du profil
     */
    removeFromLocalStorage(name) {
        try {
            const allProfiles = this.getAllFromLocalStorage();
            delete allProfiles[name];

            localStorage.setItem(this.STORAGE_KEY, JSON.stringify(allProfiles));
            console.log(`🗑️ Profil "${name}" supprimé du localStorage`);
        } catch (error) {
            console.error('❌ Erreur suppression localStorage:', error);
        }
    }

    /**
     * Définit le dernier profil actif.
     *
     * @param {string} name - Nom du profil
     */
    setLastActiveProfile(name) {
        try {
            localStorage.setItem(this.CURRENT_PROFILE_KEY, name);
        } catch (error) {
            console.error('❌ Erreur sauvegarde profil actif:', error);
        }
    }

    /**
     * Récupère le dernier profil actif.
     *
     * @returns {string|null} Nom du profil ou null
     */
    getLastActiveProfile() {
        try {
            return localStorage.getItem(this.CURRENT_PROFILE_KEY);
        } catch (error) {
            console.error('❌ Erreur lecture profil actif:', error);
            return null;
        }
    }

    /**
     * Réinitialise au profil par défaut.
     */
    async resetToDefault() {
        console.log('🔄 Réinitialisation au profil par défaut');
        await this.loadProfile('default', true);
    }

    /**
     * Exporte un profil en JSON et déclenche le téléchargement.
     *
     * @param {string} name - Nom du profil
     * @returns {Promise<boolean>} Succès de l'export
     */
    async exportProfile(name) {
        try {
            const profile = await this.loadProfile(name, false);
            if (!profile) {
                console.error(`❌ Profil "${name}" introuvable`);
                return false;
            }

            // Créer le contenu JSON
            const jsonString = JSON.stringify(profile, null, 2);
            const blob = new Blob([jsonString], { type: 'application/json' });

            // Créer un lien de téléchargement
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `geopol_profile_${profile.name}_${Date.now()}.json`;

            // Déclencher le téléchargement
            document.body.appendChild(a);
            a.click();

            // Nettoyage
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            console.log(`📤 Profil "${name}" exporté avec succès`);
            return true;
        } catch (error) {
            console.error('❌ Erreur lors de l\'export du profil:', error);
            return false;
        }
    }

    /**
     * Importe un profil depuis un fichier JSON.
     *
     * @param {File} file - Fichier JSON à importer
     * @returns {Promise<boolean>} Succès de l'import
     */
    async importProfileFromFile(file) {
        try {
            // Lire le fichier
            const jsonString = await this.readFileAsText(file);

            // Parser le JSON
            const profile = JSON.parse(jsonString);

            console.log(`📥 Import du profil "${profile.name}"...`);

            // Vérifier si le profil existe déjà
            const existingProfile = await this.loadProfile(profile.name, false);
            if (existingProfile) {
                const overwrite = confirm(
                    `⚠️ Un profil nommé "${profile.name}" existe déjà.\n\nVoulez-vous l'écraser ?`
                );
                if (!overwrite) {
                    console.log('❌ Import annulé par l\'utilisateur');
                    return false;
                }
            }

            // Valider via l'API
            const response = await fetch(`${this.API_BASE}/validate`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: jsonString
            });

            const data = await response.json();

            if (!data.success || !data.valid) {
                alert(`❌ Profil invalide: ${data.error || 'Erreur de validation'}`);
                console.error(`❌ Profil invalide: ${data.error}`);
                return false;
            }

            // Sauvegarder le profil
            const saveResponse = await fetch(this.API_BASE, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: jsonString
            });

            const saveData = await saveResponse.json();

            if (saveData.success) {
                console.log(`✅ Profil "${profile.name}" importé avec succès`);
                alert(`✅ Profil "${profile.name}" importé avec succès !`);

                // Mettre en cache
                this.profiles[profile.name] = profile;

                // Rafraîchir la liste
                if (typeof refreshProfilesList === 'function') {
                    refreshProfilesList();
                }

                return true;
            } else {
                alert(`❌ Erreur lors de la sauvegarde: ${saveData.error}`);
                return false;
            }
        } catch (error) {
            console.error('❌ Erreur lors de l\'import du profil:', error);
            alert(`❌ Erreur lors de l'import: ${error.message}`);
            return false;
        }
    }

    /**
     * Lit un fichier comme texte.
     *
     * @param {File} file - Fichier à lire
     * @returns {Promise<string>} Contenu du fichier
     */
    readFileAsText(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = (e) => reject(new Error('Erreur de lecture du fichier'));
            reader.readAsText(file);
        });
    }

    // ========================================
    // DÉTECTION DIRTY STATE
    // ========================================

    /**
     * Initialise la détection de modifications (dirty state).
     */
    initDirtyStateDetection() {
        // Écouter les changements sur les checkboxes
        const checkboxIds = [
            'geopolitical-entities-toggle',
            'sdr-receivers-toggle',
            'meteo-layer-toggle',
            'earthquakes-layer-toggle'
        ];

        checkboxIds.forEach(id => {
            const checkbox = document.getElementById(id);
            if (checkbox) {
                checkbox.addEventListener('change', () => {
                    // Petit délai pour que le changement soit effectif
                    setTimeout(() => this.detectDirtyState(), 100);
                });
            }
        });

        // Écouter les changements sur le slider de magnitude
        const magnitudeSlider = document.getElementById('magnitude-slider');
        if (magnitudeSlider) {
            magnitudeSlider.addEventListener('input', () => {
                setTimeout(() => this.detectDirtyState(), 100);
            });
        }

        console.log('🔍 Détection dirty state activée');
    }

    /**
     * Détecte si l'état actuel diffère du profil chargé.
     */
    detectDirtyState() {
        if (!this.activeProfile) {
            // Pas de profil actif, pas de dirty state
            this.setDirty(false);
            return;
        }

        // Capturer l'état actuel
        const currentState = this.captureCurrentState();

        // Comparer avec le profil actif
        const isDifferent = !this.compareStates(currentState, this.activeProfile);

        this.setDirty(isDifferent);
    }

    /**
     * Compare deux états de configuration.
     *
     * @param {Object} state1 - Premier état
     * @param {Object} state2 - Deuxième état (profil)
     * @returns {boolean} True si identiques, false sinon
     */
    compareStates(state1, state2) {
        // Comparer les couches
        for (const [layerName, layerConfig] of Object.entries(state1.layers)) {
            const profileLayer = state2.layers?.[layerName];
            if (!profileLayer) continue;

            // Comparer enabled
            if (layerConfig.enabled !== profileLayer.enabled) {
                console.log(`🔍 Différence détectée: ${layerName}.enabled`, layerConfig.enabled, '!=', profileLayer.enabled);
                return false;
            }
        }

        // Comparer la magnitude des séismes
        if (state1.earthquakes.min_magnitude !== state2.earthquakes.min_magnitude) {
            console.log('🔍 Différence détectée: magnitude', state1.earthquakes.min_magnitude, '!=', state2.earthquakes.min_magnitude);
            return false;
        }

        // États identiques
        return true;
    }

    /**
     * Met à jour l'indicateur de dirty state.
     *
     * @param {boolean} isDirty - True si modifié, false sinon
     */
    setDirty(isDirty) {
        this.isDirty = isDirty;

        if (this.dirtyBadge) {
            if (isDirty) {
                this.dirtyBadge.style.display = 'inline-block';
                console.log('🔴 État modifié (dirty)');
            } else {
                this.dirtyBadge.style.display = 'none';
                console.log('✅ État propre (clean)');
            }
        }
    }
}

// Créer une instance globale
const configManager = new ConfigManager();

// Exporter pour utilisation globale
window.configManager = configManager;
