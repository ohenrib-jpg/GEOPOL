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
// COUCHE RESEAU SDR
//=============================================================================
function addSDRLayer() {
    // Charger la couche SDR GeoJSON
    fetch('/api/sdr/geojson')
        .then(response => response.json())
        .then(data => {
            const sdrLayer = L.geoJSON(data, {
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
                        <div class="sdr-popup">
                            <h4>📡 ${props.name}</h4>
                            <p><strong>Statut:</strong> ${props.health_status}</p>
                            <p><strong>Zone:</strong> ${props.zone_id}</p>
                        </div>
                    `;
                    layer.bindPopup(popup);
                }
            });

            sdrLayer.addTo(map);
            console.log('✅ Couche SDR ajoutée à la carte');
        })
        .catch(error => console.error('❌ Erreur chargement SDR:', error));
}

// Appeler après l'initialisation de la carte
addSDRLayer();

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

// Mettre à jour le status toutes les 30 secondes
setInterval(updateStatus, 30000);
updateStatus();

console.log('✅ Script geopol_map.js chargé');
