// static/js/geopol_map.js
/**
 * Carte géopolitique interactive avec Leaflet
 * Affiche les données World Bank au clic sur un pays
 */

// Variables globales
let map;
let geojsonLayer;
let currentCountry = null;

// Configuration
const CONFIG = {
    geojsonUrl: '/static/data/countries_simplified.geojson', // Assurez-vous que ce fichier existe
    apiBaseUrl: '/api/geopol',
    defaultCenter: [20, 0],
    defaultZoom: 2,
    maxZoom: 10,
    minZoom: 2
};

// Mapping drapeaux (émojis)
const FLAGS = {
    'FR': '🇫🇷', 'US': '🇺🇸', 'GB': '🇬🇧', 'DE': '🇩🇪', 'ES': '🇪🇸',
    'IT': '🇮🇹', 'CN': '🇨🇳', 'JP': '🇯🇵', 'RU': '🇷🇺', 'BR': '🇧🇷',
    'IN': '🇮🇳', 'CA': '🇨🇦', 'AU': '🇦🇺', 'MX': '🇲🇽', 'KR': '🇰🇷',
    'SA': '🇸🇦', 'TR': '🇹🇷', 'PL': '🇵🇱', 'NL': '🇳🇱', 'BE': '🇧🇪',
    'UA': '🇺🇦', 'IL': '🇮🇱', 'IR': '🇮🇷', 'EG': '🇪🇬', 'NG': '🇳🇬'
    // Ajoutez-en d'autres selon vos besoins
};

// ============================================================================
// INITIALISATION DE LA CARTE
// ============================================================================

function initMap() {
    console.log('🗺️ Initialisation de la carte...');

    // Créer la carte
    map = L.map('map', {
        center: CONFIG.defaultCenter,
        zoom: CONFIG.defaultZoom,
        maxZoom: CONFIG.maxZoom,
        minZoom: CONFIG.minZoom,
        zoomControl: true
    });

    // Ajouter le fond de carte
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors | GEOPOL Analytics',
        maxZoom: CONFIG.maxZoom
    }).addTo(map);

    // Charger le GeoJSON
    loadGeoJSON();

    console.log('✅ Carte initialisée');
}

// ============================================================================
// CHARGEMENT DU GEOJSON
// ============================================================================

function loadGeoJSON() {
    console.log('📥 Chargement GeoJSON...');

    fetch(CONFIG.geojsonUrl)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Erreur HTTP ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log(`✅ GeoJSON chargé: ${data.features.length} pays`);

            // Ajouter la couche GeoJSON
            geojsonLayer = L.geoJSON(data, {
                style: styleCountry,
                onEachFeature: onEachCountry
            }).addTo(map);
        })
        .catch(error => {
            console.error('❌ Erreur chargement GeoJSON:', error);
            showError('Impossible de charger les données cartographiques');
        });
}

// ============================================================================
// STYLE DES PAYS
// ============================================================================

function styleCountry(feature) {
    return {
        fillColor: getCountryColor(feature),
        weight: 1,
        opacity: 1,
        color: '#64748b',
        fillOpacity: 0.6
    };
}

function getCountryColor(feature) {
    // Couleur par défaut
    return '#334155';
}

function highlightCountry(e) {
    const layer = e.target;

    layer.setStyle({
        weight: 3,
        color: '#f59e0b',
        fillOpacity: 0.8
    });

    if (!L.Browser.ie && !L.Browser.opera && !L.Browser.edge) {
        layer.bringToFront();
    }
}

function resetHighlight(e) {
    if (currentCountry && e.target.feature.properties.ISO_A2 === currentCountry.code) {
        // Garder le style sélectionné
        return;
    }

    geojsonLayer.resetStyle(e.target);
}

// ============================================================================
// ÉVÉNEMENTS SUR LES PAYS
// ============================================================================

function onEachCountry(feature, layer) {
    layer.on({
        mouseover: highlightCountry,
        mouseout: resetHighlight,
        click: onCountryClick
    });

    // Tooltip au survol
    const name = feature.properties.NAME || 'Pays inconnu';
    layer.bindTooltip(name, {
        permanent: false,
        direction: 'top'
    });
}

function onCountryClick(e) {
    const feature = e.target.feature;
    const props = feature.properties;

    console.log('📋 Propriétés:', props); // Pour debug

    // STRATÉGIE AMÉLIORÉE : Essayer plusieurs codes dans l'ordre
    let countryCode = null;

    // Ordre de priorité des codes
    const codePriority = [
        props.WB_A2,        // World Bank code (recommandé) - contient "FR" pour la France
        props.ISO_A2_EH,    // ISO alternatif - contient "FR" pour la France
        props.FIPS_10,      // FIPS code - contient "FR" pour la France
        props.iso_a2,       // Format alternatif
        props.ISO2,         // Autre format
        props.ISO_A2        // Dernier recours (mais "-99" pour la France)
    ];

    // Prendre le premier code valide et non "-99"
    for (const code of codePriority) {
        if (code && code !== '-99' && code !== '-099') {
            countryCode = code.toUpperCase();
            break;
        }
    }

    // Si toujours pas de code, essayer avec le nom
    if (!countryCode) {
        console.warn('Aucun code valide, tentative avec nom:', props.NAME);

        // Mapping basique nom -> code
        const nameToCode = {
            'France': 'FR',
            'Espagne': 'ES', 'Spain': 'ES',
            'Portugal': 'PT',
            'Allemagne': 'DE', 'Germany': 'DE',
            'Italie': 'IT', 'Italy': 'IT',
            'United Kingdom': 'GB', 'Royaume-Uni': 'GB',
            'United States': 'US', 'États-Unis': 'US'
        };

        countryCode = nameToCode[props.NAME] || nameToCode[props.NAME_EN] || null;
    }

    if (!countryCode) {
        console.error('Code pays invalide après toutes les tentatives:', props);
        showError(`Impossible de déterminer le code pays pour ${props.NAME || props.NAME_EN || 'cette région'}`);
        return;
    }

    console.log(`✅ Clic sur ${props.NAME} -> code: ${countryCode}`);
    console.log(`📊 Codes disponibles: WB_A2=${props.WB_A2}, ISO_A2_EH=${props.ISO_A2_EH}, FIPS_10=${props.FIPS_10}`);

    // Centrer la carte
    map.fitBounds(e.target.getBounds(), {
        padding: [50, 50],
        maxZoom: 6
    });

    // Charger les données
    loadCountryData(countryCode, props.NAME || props.NAME_EN);
}

// ============================================================================
// CHARGEMENT DES DONNÉES PAYS
// ============================================================================

async function loadCountryData(countryCode, countryName) {
    console.log(`📡 Chargement données ${countryCode}...`);

    // Afficher le loader
    showLoading(countryName);

    try {
        const response = await fetch(`${CONFIG.apiBaseUrl}/country/${countryCode}`);

        if (!response.ok) {
            throw new Error(`Erreur API: ${response.status}`);
        }

        const data = await response.json();

        if (data.success && data.snapshot) {
            console.log('✅ Données reçues:', data.snapshot);
            currentCountry = {
                code: countryCode,
                name: countryName,
                data: data.snapshot
            };
            displayCountryData(data.snapshot);
        } else {
            throw new Error(data.error || 'Données non disponibles');
        }

    } catch (error) {
        console.error('❌ Erreur chargement:', error);
        showError(`Impossible de charger les données pour ${countryName}`);
    }
}

// ============================================================================
// AFFICHAGE DES DONNÉES
// ============================================================================

function displayCountryData(snapshot) {
    const flag = FLAGS[snapshot.country_code] || '🌍';

    const html = `
        <div class="country-header">
            <div class="country-flag">${flag}</div>
            <div class="country-info">
                <h2>${snapshot.country_name}</h2>
                <div class="code">${snapshot.country_code} • Année: ${snapshot.data_year || 'N/A'}</div>
            </div>
        </div>

        <!-- Économie -->
        <div class="data-section">
            <h3>💰 Économie</h3>
            <div class="data-row">
                <span class="data-label">PIB</span>
                <span class="data-value">${snapshot.formatted?.gdp || 'N/A'}</span>
            </div>
            <div class="data-row">
                <span class="data-label">PIB / habitant</span>
                <span class="data-value">${formatCurrency(snapshot.gdp_per_capita)}</span>
            </div>
            ${snapshot.gdp_growth !== null ? `
            <div class="data-row">
                <span class="data-label">Croissance</span>
                <span class="data-value ${snapshot.gdp_growth >= 0 ? 'positive' : 'negative'}">
                    ${snapshot.gdp_growth >= 0 ? '+' : ''}${snapshot.gdp_growth.toFixed(1)}%
                </span>
            </div>
            ` : ''}
            ${snapshot.unemployment !== null ? `
            <div class="data-row">
                <span class="data-label">Chômage</span>
                <span class="data-value">${snapshot.unemployment.toFixed(1)}%</span>
            </div>
            ` : ''}
        </div>

        <!-- Démographie -->
        <div class="data-section">
            <h3>👥 Démographie</h3>
            <div class="data-row">
                <span class="data-label">Population</span>
                <span class="data-value">${snapshot.formatted?.population || 'N/A'}</span>
            </div>
            ${snapshot.urban_population !== null ? `
            <div class="data-row">
                <span class="data-label">Urbanisation</span>
                <span class="data-value">${snapshot.urban_population.toFixed(1)}%</span>
            </div>
            ` : ''}
            ${snapshot.life_expectancy !== null ? `
            <div class="data-row">
                <span class="data-label">Espérance de vie</span>
                <span class="data-value">${snapshot.life_expectancy.toFixed(1)} ans</span>
            </div>
            ` : ''}
        </div>

        <!-- Militaire -->
        <div class="data-section">
            <h3>🎖️ Militaire</h3>
            ${snapshot.military_spending_pct !== null ? `
            <div class="data-row">
                <span class="data-label">Dépenses (% PIB)</span>
                <span class="data-value">${snapshot.military_spending_pct.toFixed(2)}%</span>
            </div>
            <div class="data-row">
                <span class="data-label">Intensité</span>
                <span class="data-value">
                    <span class="score-badge score-${getIntensityClass(snapshot.scores?.military_intensity)}">
                        ${snapshot.scores?.military_intensity || 'UNKNOWN'}
                    </span>
                </span>
            </div>
            ` : '<div class="data-row"><span class="data-label">Données non disponibles</span></div>'}
        </div>

        <!-- Environnement -->
        ${snapshot.pm25 !== null ? `
        <div class="data-section">
            <h3>🌍 Environnement</h3>
            <div class="data-row">
                <span class="data-label">PM2.5</span>
                <span class="data-value">${snapshot.pm25.toFixed(1)} µg/m³</span>
            </div>
            <div class="data-row">
                <span class="data-label">Risque</span>
                <span class="data-value">
                    <span class="score-badge score-${getRiskClass(snapshot.scores?.environmental_risk)}">
                        ${snapshot.scores?.environmental_risk || 'UNKNOWN'}
                    </span>
                </span>
            </div>
        </div>
        ` : ''}

        <!-- Métadonnées -->
        <div class="metadata">
            <div>Source: ${snapshot.source}</div>
            <div>MAJ: ${new Date(snapshot.last_updated).toLocaleString('fr-FR')}</div>
        </div>
    `;

    document.getElementById('sidebar-content').innerHTML = html;
}

// ============================================================================
// UTILITAIRES D'AFFICHAGE
// ============================================================================

function showLoading(countryName) {
    const html = `
        <div class="loading">
            <div class="spinner"></div>
            <p>Chargement des données pour <strong>${countryName}</strong>...</p>
        </div>
    `;
    document.getElementById('sidebar-content').innerHTML = html;
}

function showError(message) {
    const html = `
        <div class="placeholder">
            <i style="color: #ef4444;">⚠️</i>
            <p style="color: #ef4444;">${message}</p>
            <p style="margin-top: 1rem; font-size: 0.875rem; color: #94a3b8;">
                Cliquez sur un autre pays ou réessayez plus tard
            </p>
        </div>
    `;
    document.getElementById('sidebar-content').innerHTML = html;
}

function formatCurrency(value) {
    if (value === null || value === undefined) return 'N/A';
    return new Intl.NumberFormat('fr-FR', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(value);
}

function getIntensityClass(intensity) {
    const map = {
        'LOW': 'low',
        'MEDIUM': 'medium',
        'HIGH': 'high',
        'VERY_HIGH': 'critical',
        'UNKNOWN': 'unknown'
    };
    return map[intensity] || 'unknown';
}

function getRiskClass(risk) {
    const map = {
        'LOW': 'low',
        'MEDIUM': 'medium',
        'HIGH': 'high',
        'CRITICAL': 'critical',
        'UNKNOWN': 'unknown'
    };
    return map[risk] || 'unknown';
}

// ============================================================================
// COUCHE ENTITÉS GÉOPOLITIQUES (Ancienn. Couche SDR)
// ============================================================================

// Variable globale pour la couche entités géopolitiques
let geopoliticalLayerGroup = null;

function addGeopoliticalEntitiesLayer() {
    console.log('🌍 Chargement couche entités géopolitiques...');

    // Vérifier que la carte est initialisée
    if (!map) {
        console.error('❌ La carte n\'est pas initialisée');
        return;
    }

    // Créer un pane pour la couche entités géopolitiques avec z-index inférieur aux pays
    if (!map.getPane('geopoliticalPane')) {
        map.createPane('geopoliticalPane');
        map.getPane('geopoliticalPane').style.zIndex = 350; // Inférieur à overlayPane (400)
    }

    // Charger la couche GeoJSON des entités géopolitiques (zones SDR)
    fetch('/api/sdr/geojson')
        .then(response => {
            if (!response.ok) {
                throw new Error(`Erreur HTTP ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (!data || !data.features) {
                console.warn('⚠️ Aucune donnée géopolitique disponible');
                return;
            }

            // Créer le LayerGroup si nécessaire
            if (!geopoliticalLayerGroup) {
                geopoliticalLayerGroup = L.layerGroup();
                geopoliticalLayerGroup.addTo(map);
            }

            // Vider le groupe avant d'ajouter de nouvelles données
            geopoliticalLayerGroup.clearLayers();

            const geopoliticalLayer = L.geoJSON(data, {
                pane: 'geopoliticalPane', // Utiliser le pane avec z-index inférieur
                style: function (feature) {
                    const status = feature.properties.health_status;
                    const colors = {
                        'CRITICAL': '#ff0000',
                        'HIGH_RISK': '#ff6b00',
                        'WARNING': '#ffd700',
                        'STABLE': '#90ee90',
                        'OPTIMAL': '#00ff00'
                    };
                    return {
                        fillColor: colors[status] || '#3388ff',
                        weight: 2,
                        opacity: 0.7,
                        fillOpacity: 0.3
                    };
                },
                onEachFeature: function (feature, layer) {
                    const props = feature.properties;
                    const popup = `
                        <div class="geopolitical-popup">
                            <h4>🌍 ${props.name || 'Zone Géopolitique'}</h4>
                            <p><strong>Statut:</strong> ${props.health_status || 'UNKNOWN'}</p>
                            <p><strong>Zone:</strong> ${props.zone_id || 'N/A'}</p>
                        </div>
                    `;
                    layer.bindPopup(popup);
                }
            });

            geopoliticalLayerGroup.addLayer(geopoliticalLayer);
            console.log('✅ Couche entités géopolitiques ajoutée à la carte');
        })
        .catch(error => {
            console.error('❌ Erreur chargement entités géopolitiques:', error);
            console.log('ℹ️  La couche entités géopolitiques n\'est pas disponible');
        });
}

// Fonction pour toggle la couche entités géopolitiques
function toggleGeopoliticalEntities(enabled) {
    if (!map || !geopoliticalLayerGroup) {
        console.warn('⚠️ Carte ou couche entités géopolitiques non initialisée');
        return;
    }

    if (enabled) {
        if (!map.hasLayer(geopoliticalLayerGroup)) {
            geopoliticalLayerGroup.addTo(map);
            console.log('✅ Couche entités géopolitiques activée');
        }
    } else {
        if (map.hasLayer(geopoliticalLayerGroup)) {
            map.removeLayer(geopoliticalLayerGroup);
            console.log('❌ Couche entités géopolitiques désactivée');
        }
    }
}

// ============================================================================
// COUCHE RÉCEPTEURS SDR GLOBAUX
// ============================================================================

// Variables globales pour la couche récepteurs SDR
let sdrReceiversLayerGroup = null;
let sdrRefreshInterval = null;
const SDR_REFRESH_INTERVAL_MS = 5 * 60 * 1000; // 5 minutes

function addSDRReceiversLayer() {
    console.log('📡 Chargement couche récepteurs SDR globaux...');

    // Vérifier que la carte est initialisée
    if (!map) {
        console.error('❌ La carte n\'est pas initialisée');
        return;
    }

    // Créer un pane pour les récepteurs SDR avec z-index au-dessus des zones
    if (!map.getPane('sdrReceiversPane')) {
        map.createPane('sdrReceiversPane');
        map.getPane('sdrReceiversPane').style.zIndex = 450; // Au-dessus des pays (400)
    }

    // Charger les données des récepteurs SDR
    // TODO: Implémenter l'API pour récupérer les récepteurs SDR actifs
    // Pour l'instant, endpoint à créer dans Flask/geopol_data/sdr_routes.py
    fetch('/api/geopol/sdr-receivers')
        .then(response => {
            if (!response.ok) {
                throw new Error(`Erreur HTTP ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (!data || !data.receivers) {
                console.warn('⚠️ Aucun récepteur SDR disponible');
                return;
            }

            // Créer le LayerGroup si nécessaire
            if (!sdrReceiversLayerGroup) {
                sdrReceiversLayerGroup = L.layerGroup();
                sdrReceiversLayerGroup.addTo(map);
            }

            // Vider le groupe avant d'ajouter de nouvelles données
            sdrReceiversLayerGroup.clearLayers();

            // Ajouter chaque récepteur comme marqueur
            data.receivers.forEach(receiver => {
                const color = getSDRReceiverColor(receiver.last_seen);

                const marker = L.circleMarker([receiver.lat, receiver.lon], {
                    pane: 'sdrReceiversPane',
                    radius: 4,
                    fillColor: color,
                    color: '#fff',
                    weight: 1,
                    opacity: 1,
                    fillOpacity: 0.8
                });

                // Popup avec infos
                const lastSeenMinutes = Math.floor((Date.now() - new Date(receiver.last_seen)) / 60000);
                const status = lastSeenMinutes < 5 ? 'Actif' :
                              lastSeenMinutes < 30 ? 'Ralenti' : 'Inactif';

                const popup = `
                    <div class="sdr-receiver-popup">
                        <h4>📡 ${receiver.name || receiver.id}</h4>
                        <p><strong>Statut:</strong> ${status}</p>
                        <p><strong>Dernière activité:</strong> ${lastSeenMinutes} min</p>
                        <p><strong>Position:</strong> ${receiver.lat.toFixed(4)}, ${receiver.lon.toFixed(4)}</p>
                        ${receiver.country ? `<p><strong>Pays:</strong> ${receiver.country}</p>` : ''}
                    </div>
                `;
                marker.bindPopup(popup);

                sdrReceiversLayerGroup.addLayer(marker);
            });

            console.log(`✅ ${data.receivers.length} récepteurs SDR ajoutés à la carte`);
        })
        .catch(error => {
            console.error('❌ Erreur chargement récepteurs SDR:', error);
            console.log('ℹ️  L\'API des récepteurs SDR n\'est pas encore implémentée');
            console.log('ℹ️  Endpoint à créer: /api/geopol/sdr-receivers');
        });
}

function getSDRReceiverColor(lastSeen) {
    const minutesAgo = Math.floor((Date.now() - new Date(lastSeen)) / 60000);

    if (minutesAgo < 5) {
        return '#00ff00'; // Vert - Actif
    } else if (minutesAgo < 30) {
        return '#ffd700'; // Jaune - Ralenti
    } else {
        return '#ff0000'; // Rouge - Inactif
    }
}

// Fonction pour toggle la couche récepteurs SDR
function toggleSDRReceivers(enabled) {
    if (!map) {
        console.warn('⚠️ Carte non initialisée');
        return;
    }

    if (enabled) {
        // Charger ou afficher la couche
        if (!sdrReceiversLayerGroup) {
            addSDRReceiversLayer();
        } else if (!map.hasLayer(sdrReceiversLayerGroup)) {
            sdrReceiversLayerGroup.addTo(map);
            console.log('✅ Couche récepteurs SDR activée');
        }

        // Démarrer le rafraîchissement automatique
        if (!sdrRefreshInterval) {
            sdrRefreshInterval = setInterval(() => {
                console.log('🔄 Rafraîchissement automatique des récepteurs SDR...');
                addSDRReceiversLayer();
            }, SDR_REFRESH_INTERVAL_MS);
            console.log(`⏰ Rafraîchissement automatique SDR activé (${SDR_REFRESH_INTERVAL_MS / 60000} min)`);
        }
    } else {
        // Masquer la couche
        if (sdrReceiversLayerGroup && map.hasLayer(sdrReceiversLayerGroup)) {
            map.removeLayer(sdrReceiversLayerGroup);
            console.log('❌ Couche récepteurs SDR désactivée');
        }

        // Arrêter le rafraîchissement automatique
        if (sdrRefreshInterval) {
            clearInterval(sdrRefreshInterval);
            sdrRefreshInterval = null;
            console.log('⏰ Rafraîchissement automatique SDR arrêté');
        }
    }
}

// ============================================================================
// COUCHE MÉTÉO OPEN-METEO
// ============================================================================

// Variables globales pour la couche météo
let weatherLayerGroup = null;
let currentWeatherLayer = 'air_quality'; // Layer par défaut: qualité de l'air (indicateur géopolitique)
let weatherLegend = null;

async function toggleWeatherLayer(enabled) {
    if (!map) {
        console.warn('⚠️ Carte non initialisée');
        return;
    }

    if (enabled) {
        console.log('🌦️ Activation de la couche météo Open-Meteo...');

        // Charger et afficher la couche
        await loadWeatherLayer(currentWeatherLayer);
    } else {
        console.log('🌦️ Désactivation de la couche météo Open-Meteo...');

        // Masquer la couche
        if (weatherLayerGroup && map.hasLayer(weatherLayerGroup)) {
            map.removeLayer(weatherLayerGroup);
            console.log('❌ Couche météo désactivée');
        }

        // Masquer la légende
        if (weatherLegend) {
            weatherLegend.remove();
            weatherLegend = null;
        }
    }
}

async function loadWeatherLayer(layerId) {
    console.log(`📡 Chargement couche météo: ${layerId}...`);

    try {
        // Récupérer les données de la couche
        const response = await fetch(`/api/weather/layer/${layerId}`);

        if (!response.ok) {
            throw new Error(`Erreur HTTP ${response.status}`);
        }

        const data = await response.json();

        if (!data.success || !data.geojson) {
            throw new Error(data.error || 'Données invalides');
        }

        console.log(`✅ Couche ${layerId} reçue: ${data.geojson.features.length} points`);

        // Créer/vider le LayerGroup
        if (!weatherLayerGroup) {
            weatherLayerGroup = L.layerGroup();
        } else {
            weatherLayerGroup.clearLayers();
        }

        // Créer un pane pour les marqueurs météo
        if (!map.getPane('weatherPane')) {
            map.createPane('weatherPane');
            map.getPane('weatherPane').style.zIndex = 500; // Au-dessus de tout
        }

        // Ajouter les marqueurs depuis le GeoJSON
        data.geojson.features.forEach(feature => {
            const props = feature.properties;
            const coords = feature.geometry.coordinates;

            // Créer un marqueur circulaire coloré
            const marker = L.circleMarker([coords[1], coords[0]], {
                pane: 'weatherPane',
                radius: 8,
                fillColor: props.color,
                color: '#ffffff',
                weight: 2,
                opacity: 1,
                fillOpacity: 0.7
            });

            // Popup avec infos
            const popup = `
                <div class="weather-popup">
                    <h4>${props.country_code}</h4>
                    <p><strong>${data.layer_config.name}:</strong> ${props.value} ${props.unit}</p>
                    <p style="font-size: 0.75rem; color: #888;">
                        ${new Date(props.timestamp).toLocaleString('fr-FR')}
                    </p>
                </div>
            `;
            marker.bindPopup(popup);

            weatherLayerGroup.addLayer(marker);
        });

        // Ajouter à la carte
        if (!map.hasLayer(weatherLayerGroup)) {
            weatherLayerGroup.addTo(map);
        }

        // Créer la légende
        createWeatherLegend(data.layer_config);

        console.log(`✅ Couche météo ${layerId} affichée`);

    } catch (error) {
        console.error(`❌ Erreur chargement couche météo: ${error}`);

        // Afficher un message d'erreur à l'utilisateur
        if (window.alert) {
            alert(`Impossible de charger les données météo: ${error.message}`);
        }
    }
}

function createWeatherLegend(layerConfig) {
    // Supprimer l'ancienne légende si elle existe
    if (weatherLegend) {
        weatherLegend.remove();
    }

    // Créer un contrôle Leaflet personnalisé pour la légende
    const Legend = L.Control.extend({
        options: {
            position: 'bottomright'
        },

        onAdd: function(map) {
            const div = L.DomUtil.create('div', 'weather-legend');

            div.innerHTML = `
                <h4>${layerConfig.name}</h4>
                <div class="legend-scale">
                    ${layerConfig.color_scale.map(([value, color]) => `
                        <div class="legend-item">
                            <span class="legend-color" style="background: ${color}"></span>
                            <span>${value}${layerConfig.unit}</span>
                        </div>
                    `).join('')}
                </div>
            `;

            return div;
        }
    });

    weatherLegend = new Legend();
    weatherLegend.addTo(map);

    console.log('✅ Légende météo créée');
}

// ============================================================================
// COUCHE SÉISMES (USGS EARTHQUAKE)
// ============================================================================

// Variables globales pour la couche séismes
let earthquakesLayerGroup = null;
let currentMagnitudeFilter = 4.5;
let earthquakesRefreshInterval = null;
const EARTHQUAKES_REFRESH_INTERVAL_MS = 5 * 60 * 1000; // 5 minutes

async function toggleEarthquakesLayer(enabled) {
    if (!map) {
        console.warn('⚠️ Carte non initialisée');
        return;
    }

    if (enabled) {
        console.log('🌍 Activation de la couche séismes...');

        // Charger et afficher la couche
        await loadEarthquakesLayer();

        // Démarrer le rafraîchissement automatique
        if (!earthquakesRefreshInterval) {
            earthquakesRefreshInterval = setInterval(() => {
                console.log('🔄 Rafraîchissement automatique des séismes...');
                loadEarthquakesLayer();
            }, EARTHQUAKES_REFRESH_INTERVAL_MS);
            console.log(`⏰ Rafraîchissement automatique séismes activé (${EARTHQUAKES_REFRESH_INTERVAL_MS / 60000} min)`);
        }
    } else {
        console.log('🌍 Désactivation de la couche séismes...');

        // Masquer la couche
        if (earthquakesLayerGroup && map.hasLayer(earthquakesLayerGroup)) {
            map.removeLayer(earthquakesLayerGroup);
            console.log('❌ Couche séismes désactivée');
        }

        // Arrêter le rafraîchissement automatique
        if (earthquakesRefreshInterval) {
            clearInterval(earthquakesRefreshInterval);
            earthquakesRefreshInterval = null;
            console.log('⏰ Rafraîchissement automatique séismes arrêté');
        }
    }
}

async function loadEarthquakesLayer() {
    console.log(`📡 Chargement couche séismes (magnitude ≥ ${currentMagnitudeFilter})...`);

    try {
        // Récupérer les données sismiques depuis l'API
        const response = await fetch(`/api/earthquakes/geojson?min_magnitude=${currentMagnitudeFilter}`);

        if (!response.ok) {
            throw new Error(`Erreur HTTP ${response.status}`);
        }

        const data = await response.json();

        if (!data.success || !data.geojson) {
            throw new Error(data.error || 'Données invalides');
        }

        const geojson = data.geojson;
        console.log(`✅ GeoJSON séismes reçu: ${geojson.features.length} séismes`);

        // Créer/vider le LayerGroup
        if (!earthquakesLayerGroup) {
            earthquakesLayerGroup = L.layerGroup();
        } else {
            earthquakesLayerGroup.clearLayers();
        }

        // Créer un pane pour les marqueurs séismes
        if (!map.getPane('earthquakesPane')) {
            map.createPane('earthquakesPane');
            map.getPane('earthquakesPane').style.zIndex = 550; // Au-dessus de la météo (500)
        }

        // Ajouter les marqueurs depuis le GeoJSON
        geojson.features.forEach(feature => {
            const props = feature.properties;
            const coords = feature.geometry.coordinates;

            // Créer un marqueur circulaire pulsant pour les séismes importants
            const isPulse = props.magnitude >= 6.0;

            const marker = L.circleMarker([coords[1], coords[0]], {
                pane: 'earthquakesPane',
                radius: props.size,
                fillColor: props.color,
                color: '#ffffff',
                weight: 2,
                opacity: 1,
                fillOpacity: isPulse ? 0.9 : 0.7,
                className: isPulse ? 'earthquake-pulse' : ''
            });

            // Popup avec infos détaillées
            const popup = `
                <div class="earthquake-popup" style="min-width: 200px;">
                    <h4 style="margin: 0 0 0.5rem 0; color: ${props.color};">
                        🌍 Magnitude ${props.magnitude}
                    </h4>
                    <p style="margin: 0.25rem 0; font-weight: 600;">
                        ${props.place}
                    </p>
                    <p style="margin: 0.25rem 0;">
                        <strong>Date:</strong> ${props.time_formatted}
                    </p>
                    <p style="margin: 0.25rem 0;">
                        <strong>Profondeur:</strong> ${props.depth.toFixed(1)} km (${props.depth_category})
                    </p>
                    <p style="margin: 0.25rem 0;">
                        <strong>Catégorie:</strong> <span style="color: ${props.color}; font-weight: 600;">${props.magnitude_category}</span>
                    </p>
                    ${props.tsunami ? '<p style="margin: 0.5rem 0; padding: 0.5rem; background: #fee; border-left: 3px solid #f00; font-weight: 600;">⚠️ ALERTE TSUNAMI</p>' : ''}
                    <p style="margin: 0.5rem 0 0 0; font-size: 0.75rem;">
                        <a href="${props.url}" target="_blank" style="color: #3b82f6;">Détails USGS →</a>
                    </p>
                </div>
            `;
            marker.bindPopup(popup);

            // Tooltip au survol
            marker.bindTooltip(`Magnitude ${props.magnitude} - ${props.place}`, {
                direction: 'top',
                offset: [0, -10]
            });

            earthquakesLayerGroup.addLayer(marker);
        });

        // Ajouter à la carte
        if (!map.hasLayer(earthquakesLayerGroup)) {
            earthquakesLayerGroup.addTo(map);
        }

        console.log(`✅ Couche séismes affichée (${geojson.features.length} marqueurs)`);

    } catch (error) {
        console.error(`❌ Erreur chargement couche séismes: ${error}`);

        // Afficher un message d'erreur à l'utilisateur
        if (window.alert) {
            alert(`Impossible de charger les données sismiques: ${error.message}`);
        }
    }
}

function updateEarthquakeMagnitude(magnitude) {
    currentMagnitudeFilter = parseFloat(magnitude);

    // Mettre à jour l'affichage de la valeur
    const valueDisplay = document.getElementById('magnitude-value');
    if (valueDisplay) {
        valueDisplay.textContent = currentMagnitudeFilter.toFixed(1);
    }

    console.log(`🎚️ Filtre magnitude mis à jour: ${currentMagnitudeFilter}`);

    // Recharger la couche si elle est active
    const checkbox = document.getElementById('earthquakes-layer-toggle');
    if (checkbox && checkbox.checked) {
        console.log('🔄 Rechargement de la couche séismes avec nouveau filtre...');
        loadEarthquakesLayer();
    }
}

// Ajouter une animation CSS pour les séismes pulsants (magnitude ≥ 6.0)
if (!document.getElementById('earthquake-pulse-style')) {
    const style = document.createElement('style');
    style.id = 'earthquake-pulse-style';
    style.textContent = `
        @keyframes earthquake-pulse {
            0% {
                opacity: 0.9;
                transform: scale(1);
            }
            50% {
                opacity: 0.6;
                transform: scale(1.3);
            }
            100% {
                opacity: 0.9;
                transform: scale(1);
            }
        }
        .earthquake-pulse {
            animation: earthquake-pulse 2s ease-in-out infinite;
        }
    `;
    document.head.appendChild(style);
}

// ============================================================================
// MISE À JOUR DU STATUS
// ============================================================================

async function updateStatus() {
    try {
        const response = await fetch(`${CONFIG.apiBaseUrl}/status`);
        const data = await response.json();

        // Mettre à jour le statut général
        const statusText = document.getElementById('status-text');
        if (statusText) {
            statusText.textContent = 'En ligne';
        }

        // Mettre à jour le statut cache si l'élément existe
        const cacheStatus = document.getElementById('cache-status');
        if (cacheStatus && data.cache) {
            cacheStatus.textContent = `Cache: ${data.cache.cache_size}`;
        }
    } catch (error) {
        console.warn('Status update failed:', error);

        // Mettre à jour le statut en erreur
        const statusText = document.getElementById('status-text');
        if (statusText) {
            statusText.textContent = 'Erreur';
        }
    }
}
async function toggleOverlay(overlayId) {
        const response = await fetch(`/api/overlays/${overlayId}/toggle`, {
            method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({state: true})
        });
    return response.json();

}

// ============================================================================
// TOGGLE SIDEBAR
// ============================================================================

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const toggleIcon = document.getElementById('toggle-icon');

    if (!sidebar || !toggleIcon) {
        console.error('❌ Éléments sidebar non trouvés');
        return;
    }

    // Basculer la classe hidden
    sidebar.classList.toggle('hidden');

    // Changer l'icône
    if (sidebar.classList.contains('hidden')) {
        toggleIcon.textContent = '▶'; // Flèche vers la droite (sidebar cachée)
        console.log('📋 Panneau latéral masqué');
    } else {
        toggleIcon.textContent = '◀'; // Flèche vers la gauche (sidebar visible)
        console.log('📋 Panneau latéral affiché');
    }

    // Recalculer la taille de la carte après l'animation CSS (300ms)
    if (map) {
        setTimeout(() => {
            map.invalidateSize();
            console.log('🗺️  Taille de la carte recalculée');
        }, 350); // Légèrement après la transition CSS (0.3s)
    }
}

// ============================================================================
// GESTION DES SECTIONS DU PANEL DE CONTRÔLE
// ============================================================================

function toggleSection(sectionId) {
    const sectionContent = document.getElementById(sectionId);
    const sectionHeader = sectionContent.previousElementSibling;

    if (!sectionContent || !sectionHeader) {
        console.error('❌ Section non trouvée:', sectionId);
        return;
    }

    // Basculer la classe collapsed
    sectionContent.classList.toggle('collapsed');
    sectionHeader.classList.toggle('collapsed');

    const isCollapsed = sectionContent.classList.contains('collapsed');
    console.log(`${isCollapsed ? '▲' : '▼'} Section ${sectionId} ${isCollapsed ? 'réduite' : 'dépliée'}`);
}

function collapseAllSections() {
    const sections = document.querySelectorAll('.section-content');
    const headers = document.querySelectorAll('.section-header');

    let allCollapsed = true;
    sections.forEach(section => {
        if (!section.classList.contains('collapsed')) {
            allCollapsed = false;
        }
    });

    // Si toutes sont réduites, les déplier toutes
    // Sinon, les réduire toutes
    sections.forEach((section, index) => {
        if (allCollapsed) {
            section.classList.remove('collapsed');
            headers[index].classList.remove('collapsed');
        } else {
            section.classList.add('collapsed');
            headers[index].classList.add('collapsed');
        }
    });

    const btnText = document.querySelector('.collapse-all-btn');
    if (btnText) {
        btnText.textContent = allCollapsed ? '▼' : '▲';
    }

    console.log(`${allCollapsed ? '▼ Toutes les sections dépliées' : '▲ Toutes les sections réduites'}`);
}

function updateLayerStatus(sectionName) {
    // Mettre à jour les indicateurs d'état
    const geopoliticalCheckbox = document.getElementById('geopolitical-entities-toggle');
    const sdrCheckbox = document.getElementById('sdr-receivers-toggle');
    const meteoCheckbox = document.getElementById('meteo-layer-toggle');
    const earthquakesCheckbox = document.getElementById('earthquakes-layer-toggle');

    // Indicateurs individuels
    const geopoliticalStatus = document.getElementById('geopolitical-entities-status');
    const sdrStatus = document.getElementById('sdr-receivers-status');
    const meteoStatus = document.getElementById('meteo-layer-status');
    const earthquakesStatus = document.getElementById('earthquakes-layer-status');

    // Indicateurs de section
    const geopoliticalSectionStatus = document.getElementById('geopolitical-status');
    const surveillanceSectionStatus = document.getElementById('surveillance-status');
    const environmentSectionStatus = document.getElementById('environment-status');
    const earthquakesSectionStatus = document.getElementById('earthquakes-status');

    // Mettre à jour les indicateurs individuels
    if (geopoliticalCheckbox && geopoliticalStatus) {
        if (geopoliticalCheckbox.checked) {
            geopoliticalStatus.classList.add('active');
            geopoliticalStatus.classList.remove('inactive');
        } else {
            geopoliticalStatus.classList.remove('active');
            geopoliticalStatus.classList.add('inactive');
        }
    }

    if (sdrCheckbox && sdrStatus) {
        if (sdrCheckbox.checked) {
            sdrStatus.classList.add('active');
            sdrStatus.classList.remove('inactive');
        } else {
            sdrStatus.classList.remove('active');
            sdrStatus.classList.add('inactive');
        }
    }

    if (meteoCheckbox && meteoStatus) {
        if (meteoCheckbox.checked) {
            meteoStatus.classList.add('active');
            meteoStatus.classList.remove('inactive');
        } else {
            meteoStatus.classList.remove('active');
            meteoStatus.classList.add('inactive');
        }
    }

    if (earthquakesCheckbox && earthquakesStatus) {
        if (earthquakesCheckbox.checked) {
            earthquakesStatus.classList.add('active');
            earthquakesStatus.classList.remove('inactive');
        } else {
            earthquakesStatus.classList.remove('active');
            earthquakesStatus.classList.add('inactive');
        }
    }

    // Mettre à jour les indicateurs de section
    if (geopoliticalSectionStatus) {
        geopoliticalSectionStatus.classList.toggle('active', geopoliticalCheckbox?.checked);
    }

    if (surveillanceSectionStatus) {
        surveillanceSectionStatus.classList.toggle('active', sdrCheckbox?.checked);
    }

    if (environmentSectionStatus) {
        environmentSectionStatus.classList.toggle('active', meteoCheckbox?.checked);
    }

    if (earthquakesSectionStatus) {
        earthquakesSectionStatus.classList.toggle('active', earthquakesCheckbox?.checked);
    }
}

// ============================================================================
// INITIALISATION AU CHARGEMENT DE LA PAGE
// ============================================================================

// Attendre que le DOM soit chargé
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Démarrage GEOPOL Map...');

    // 1. Initialiser la carte
    initMap();

    // 2. Forcer le recalcul de la taille de la carte après initialisation
    setTimeout(() => {
        if (map) {
            map.invalidateSize();
            console.log('🗺️  Taille initiale de la carte recalculée');
        }
    }, 100);

    // 3. Charger la couche entités géopolitiques (après initialisation de la carte)
    setTimeout(() => {
        addGeopoliticalEntitiesLayer();
    }, 1000); // Attendre 1 seconde pour que la carte soit complètement chargée

    // 4. Mettre à jour le status
    updateStatus();
    setInterval(updateStatus, 30000);

    // 5. Initialiser les indicateurs d'état du panel de contrôle
    setTimeout(() => {
        updateLayerStatus('geopolitical');
        console.log('✅ Indicateurs d\'état initialisés');
    }, 500);

    // 6. Recalcul final après chargement complet
    setTimeout(() => {
        if (map) {
            map.invalidateSize();
            console.log('🗺️  Taille finale de la carte recalculée');
        }
    }, 1500);

    console.log('✅ GEOPOL Map initialisé');
});

console.log('✅ Script geopol_map.js chargé');
