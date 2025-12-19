// ============================================================================
// DASHBOARD ÉCONOMIQUE UNIFIÉ - GEOPOL ANALYTICS
// ============================================================================

// ============================================================================
// VARIABLES GLOBALES
// ============================================================================

let charts = {
    france: null,
    international: null,
    mainIndex: null
};

let currentTab = 'france';
let userSectors = [];
let refreshIntervalId = null;

// ============================================================================
// GESTION DES ONGLETS
// ============================================================================

function switchTab(tabName) {
    // Masquer tous les contenus
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.add('hidden');
        content.classList.remove('active');
    });

    // Désactiver tous les boutons
    document.querySelectorAll('.tab-button').forEach(button => {
        button.classList.remove('active');
    });

    // Activer l'onglet sélectionné
    document.getElementById(`content-${tabName}`).classList.remove('hidden');
    document.getElementById(`content-${tabName}`).classList.add('active');
    document.getElementById(`tab-${tabName}`).classList.add('active');

    currentTab = tabName;

    // Charger les données spécifiques à l'onglet
    switch(tabName) {
        case 'france':
            loadFranceData();
            break;
        case 'international':
            loadInternationalData();
            break;
        case 'stocks':
            loadStocksData();
            break;
        case 'settings':
            loadSettings();
            break;
    }

    console.log(`📑 Onglet activé: ${tabName}`);
}

// ============================================================================
// ONGLET FRANCE
// ============================================================================

async function loadFranceData() {
    console.log('🇫🇷 Chargement des données France...');

    try {
        // Charger les indicateurs avec fallback
        await loadFranceIndicatorsWithFallback();

        // Charger le graphique CAC 40 avec fallback
        await loadCac40ChartWithFallback();

    } catch (error) {
        console.error('❌ Erreur chargement France:', error);
    }
}

// Fonction pour charger les VRAIES données Eurostat avec fallback minimal
async function loadFranceIndicatorsWithFallback() {
    const eurostatGrid = document.getElementById('eurostatIndicatorsGrid');
    const inseeGrid = document.getElementById('inseeIndicatorsGrid');

    // === EUROSTAT (PRIORITAIRE - VRAIES DONNÉES) ===
    let eurostatRealData = false;

    try {
        console.log('📡 Tentative de récupération des vraies données Eurostat...');
        const response = await fetch('/indicators/france/api/eurostat');

        if (response.ok) {
            const data = await response.json();

            if (data.success && data.indicators) {
                // Transformer les données Eurostat en format affichable
                const eurostatCards = transformEurostatData(data.indicators, true); // true = données réelles

                if (eurostatCards.length > 0) {
                    console.log(`✅ ${eurostatCards.length} indicateurs Eurostat RÉELS chargés !`);
                    renderIndicatorCards(eurostatGrid, eurostatCards);
                    eurostatRealData = true;

                    // Ajouter un badge de statut global
                    addDataStatusBadge(eurostatGrid, true);
                } else {
                    throw new Error('Aucune donnée valide');
                }
            } else {
                throw new Error('Format de données invalide');
            }
        } else {
            throw new Error(`HTTP ${response.status}`);
        }
    } catch (error) {
        console.error(`❌ Eurostat API échoué: ${error.message}`);
        console.log('⚠️ Affichage du message d\'erreur Eurostat');

        eurostatGrid.innerHTML = `
            <div class="col-span-full bg-yellow-900/20 border border-yellow-600/50 rounded-xl p-6 text-center">
                <i class="fas fa-exclamation-triangle text-yellow-400 text-3xl mb-3"></i>
                <p class="text-yellow-200 font-semibold mb-2">Données Eurostat temporairement indisponibles</p>
                <p class="text-yellow-300/70 text-sm">
                    Vérifiez votre connexion internet ou réessayez dans quelques instants.<br>
                    Les données seront chargées automatiquement dès que l'API Eurostat répondra.
                </p>
                <button onclick="loadFranceData()" class="mt-4 bg-yellow-600 hover:bg-yellow-700 text-white px-4 py-2 rounded-lg text-sm transition">
                    <i class="fas fa-sync-alt mr-2"></i>Réessayer
                </button>
            </div>
        `;
    }

    // === INSEE (avec Eurostat en fallback si disponible) ===
    try {
        console.log('📡 Tentative de récupération des données INSEE...');
        const response = await fetch('/indicators/france/api/insee');

        if (response.ok) {
            const data = await response.json();

            if (data.success && data.indicators) {
                const indicators = Array.isArray(data.indicators)
                    ? data.indicators
                    : Object.values(data.indicators);

                if (indicators.length > 0) {
                    console.log(`✅ ${indicators.length} indicateurs INSEE chargés !`);
                    renderIndicatorCards(inseeGrid, indicators);
                } else {
                    throw new Error('Aucune donnée INSEE');
                }
            } else {
                throw new Error('Format invalide');
            }
        } else {
            throw new Error(`HTTP ${response.status}`);
        }
    } catch (error) {
        console.error(`❌ INSEE API échoué: ${error.message}`);
        console.log('⚠️ Affichage du message d\'info INSEE');

        inseeGrid.innerHTML = `
            <div class="col-span-full bg-blue-900/20 border border-blue-600/50 rounded-xl p-6 text-center">
                <i class="fas fa-info-circle text-blue-400 text-3xl mb-3"></i>
                <p class="text-blue-200 font-semibold mb-2">Données INSEE en cours de chargement</p>
                <p class="text-blue-300/70 text-sm">
                    Le scraping INSEE n'est pas encore configuré.<br>
                    Toutes les données économiques françaises sont disponibles via Eurostat ci-dessus.
                </p>
            </div>
        `;
    }
}

// Transformer les données Eurostat brutes en format d'affichage
function transformEurostatData(indicators) {
    const iconMap = {
        'gdp': { icon: 'fas fa-chart-line', color: '#3b82f6' },
        'unemployment': { icon: 'fas fa-users', color: '#10b981' },
        'hicp': { icon: 'fas fa-percentage', color: '#f59e0b' },
        'trade_balance': { icon: 'fas fa-balance-scale', color: '#ef4444' },
        'gini': { icon: 'fas fa-chart-pie', color: '#8b5cf6' }
    };

    const cards = [];

    for (const [key, indicator] of Object.entries(indicators)) {
        console.log(`🔍 Traitement indicateur ${key}:`, indicator);

        if (indicator.success && indicator.current_value !== undefined && indicator.current_value !== null) {
            const iconConfig = iconMap[key] || { icon: 'fas fa-chart-bar', color: '#64748b' };

            // Formater la valeur avec l'unité
            let displayValue;
            const value = indicator.current_value;
            const unit = indicator.unit || '';

            // Formatage spécifique selon l'indicateur
            if (key === 'gdp') {
                // PIB en milliards
                displayValue = `${value.toFixed(1)}`;
            } else if (key === 'unemployment' || key === 'hicp') {
                // Pourcentages
                displayValue = `${value.toFixed(1)}%`;
            } else if (key === 'trade_balance') {
                // Balance en milliards
                const billions = value / 1000;
                displayValue = `${billions.toFixed(1)}B`;
            } else if (key === 'gini') {
                // GINI - nombre entre 0 et 100
                displayValue = `${value.toFixed(1)}`;
            } else {
                displayValue = `${value}`;
            }

            cards.push({
                name: indicator.indicator_name || indicator.name || key,
                value: displayValue,
                unit: unit,
                changePercent: indicator.change_percent || 0,
                icon: iconConfig.icon,
                color: iconConfig.color,
                source: indicator.source || 'Eurostat',
                period: indicator.period || '',
                note: indicator.note || null
            });

            console.log(`✅ Carte créée: ${cards[cards.length - 1].name} = ${displayValue}`);
        } else {
            console.warn(`⚠️ Indicateur ${key} ignoré:`, indicator);
        }
    }

    return cards;
}

// Fonction helper pour rendre les cartes de manière uniforme
function renderIndicatorCards(container, indicators) {
    container.innerHTML = '';

    indicators.forEach(indicator => {
        const card = createSimpleIndicatorCard(indicator);
        container.appendChild(card);
    });
}

// Carte d'indicateur ULTRA-SIMPLE : Fond noir, texte blanc, widgets colorés
function createSimpleIndicatorCard(indicator) {
    const div = document.createElement('div');

    const change = parseFloat(indicator.changePercent || indicator.change_percent || 0);
    const value = indicator.value || indicator.current || '--';
    const unit = indicator.unit || '';
    const name = indicator.name || indicator.label || 'Indicateur';
    const icon = indicator.icon || 'fas fa-chart-line';

    // Couleur du widget selon la variation
    let widgetColor;
    if (change > 0) {
        widgetColor = '#10b981'; // Vert
    } else if (change < 0) {
        widgetColor = '#ef4444'; // Rouge
    } else {
        widgetColor = '#3b82f6'; // Bleu
    }

    const arrow = change > 0 ? '▲' : (change < 0 ? '▼' : '•');

    // STYLE ULTRA-SIMPLE : Fond noir, bordure colorée, texte blanc
    div.style.cssText = `
        background: #000000;
        border: 2px solid ${widgetColor};
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 8px;
    `;

    div.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <span style="color: #ffffff; font-size: 14px; font-weight: 500;">${name}</span>
            <i class="${icon}" style="color: ${widgetColor}; font-size: 20px;"></i>
        </div>
        <div style="color: #ffffff; font-size: 36px; font-weight: bold; margin-bottom: 12px;">
            ${value}
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="color: ${widgetColor}; font-size: 14px; font-weight: 600;">
                ${arrow} ${Math.abs(change).toFixed(1)}%
            </span>
            <span style="color: #888888; font-size: 12px;">${unit}</span>
        </div>
    `;

    return div;
}

// Graphique CAC 40 avec fallback robuste
async function loadCac40ChartWithFallback() {
    const period = document.getElementById('periodSelectFrance')?.value || '6mo';
    const infoEl = document.getElementById('cac40Info');

    // Données de fallback pour le graphique
    const fallbackData = {
        name: 'CAC 40',
        current: 7456.32,
        change: 0.85,
        dates: generateDateRange(period),
        prices: generateMockPrices(7456.32, period)
    };

    try {
        // Essayer d'abord avec l'API France
        const response = await fetch(`/indicators/france/api/chart?symbol=^FCHI&period=${period}`);

        if (response.ok) {
            const data = await response.json();
            if (data.success && data.dates && data.prices) {
                updateCac40Display(data);
                renderChart('chartFrance', data.dates, data.prices, 'CAC 40', 'france');
                console.log('✅ Graphique CAC 40 chargé (API France)');
                return;
            }
        }

        // Si l'API France échoue, essayer l'API générale
        const response2 = await fetch(`/indicators/api/chart?symbol=^FCHI&period=${period}`);

        if (response2.ok) {
            const data = await response2.json();
            if (data.success && data.dates && data.prices) {
                updateCac40Display(data);
                renderChart('chartFrance', data.dates, data.prices, 'CAC 40', 'france');
                console.log('✅ Graphique CAC 40 chargé (API générale)');
                return;
            }
        }

        throw new Error('APIs non disponibles');

    } catch (error) {
        console.log('⚠️ Utilisation des données de fallback CAC 40');
        updateCac40Display(fallbackData);
        renderChart('chartFrance', fallbackData.dates, fallbackData.prices, 'CAC 40 (Demo)', 'france');
    }
}

function updateCac40Display(data) {
    const infoEl = document.getElementById('cac40Info');
    if (!infoEl) return;

    const change = data.change || 0;
    const current = data.current || 0;
    const arrow = change >= 0 ? '▲' : '▼';
    const colorClass = change >= 0 ? 'text-green-400' : 'text-red-400';

    infoEl.innerHTML = `
        <span class="font-semibold text-white">${data.name || 'CAC 40'}</span>
        <span class="mx-2 text-slate-500">•</span>
        <span class="text-lg font-bold ${colorClass}">
            ${current.toFixed(2)}
        </span>
        <span class="ml-2 ${colorClass}">
            ${arrow} ${Math.abs(change).toFixed(2)}%
        </span>
    `;
}

// Générer des dates pour le fallback
function generateDateRange(period) {
    const dates = [];
    const today = new Date();
    let days = 180; // 6 mois par défaut

    switch(period) {
        case '1mo': days = 30; break;
        case '3mo': days = 90; break;
        case '6mo': days = 180; break;
        case '1y': days = 365; break;
        case '2y': days = 730; break;
    }

    for (let i = days; i >= 0; i--) {
        const date = new Date(today);
        date.setDate(date.getDate() - i);
        dates.push(date.toISOString().split('T')[0]);
    }

    return dates;
}

// Générer des prix réalistes pour le fallback
function generateMockPrices(basePrice, period) {
    const dates = generateDateRange(period);
    const prices = [];
    let currentPrice = basePrice;

    for (let i = 0; i < dates.length; i++) {
        // Variation aléatoire de -1% à +1%
        const variation = (Math.random() - 0.5) * 0.02;
        currentPrice = currentPrice * (1 + variation);
        prices.push(parseFloat(currentPrice.toFixed(2)));
    }

    return prices;
}

function refreshFranceData() {
    console.log('🔄 Rafraîchissement France...');
    loadFranceData();
}

// Event listener pour changement de période CAC 40
document.addEventListener('DOMContentLoaded', () => {
    const periodSelect = document.getElementById('periodSelectFrance');
    if (periodSelect) {
        periodSelect.addEventListener('change', () => loadCac40ChartWithFallback());
    }
});

// ============================================================================
// ONGLET INTERNATIONAL
// ============================================================================

async function loadInternationalData() {
    console.log('🌍 Chargement des données internationales...');

    try {
        await loadInternationalIndices();
        await loadEuropeanIndices();
        await loadInternationalChart();

    } catch (error) {
        console.error('❌ Erreur chargement International:', error);
    }
}

async function loadInternationalIndices() {
    try {
        const symbols = ['^GSPC', '^DJI', '^IXIC', '^N225', '^HSI'];
        const response = await fetch('/indicators/api/quotes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symbols })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        const grid = document.getElementById('internationalIndices');
        grid.innerHTML = '';

        if (data.success && data.quotes) {
            data.quotes.forEach(quote => {
                const card = createIndexCard(quote);
                grid.appendChild(card);
            });
        } else {
            grid.innerHTML = `<div class="col-span-full text-center py-4 text-slate-400">Aucune donnée disponible</div>`;
        }

        console.log('✅ Indices internationaux chargés');

    } catch (error) {
        console.error('❌ Erreur indices internationaux:', error);
        const grid = document.getElementById('internationalIndices');
        grid.innerHTML = `<div class="col-span-full text-center py-4 text-red-400">Erreur: ${error.message}</div>`;
    }
}

async function loadEuropeanIndices() {
    try {
        const symbols = ['^FCHI', '^GDAXI', '^FTSE'];
        const response = await fetch('/indicators/api/quotes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symbols })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        const grid = document.getElementById('europeanIndices');
        grid.innerHTML = '';

        if (data.success && data.quotes) {
            data.quotes.forEach(quote => {
                const card = createIndexCard(quote);
                grid.appendChild(card);
            });
        } else {
            grid.innerHTML = `<div class="col-span-full text-center py-4 text-slate-400">Aucune donnée disponible</div>`;
        }

        console.log('✅ Indices européens chargés');

    } catch (error) {
        console.error('❌ Erreur indices européens:', error);
        const grid = document.getElementById('europeanIndices');
        grid.innerHTML = `<div class="col-span-full text-center py-4 text-red-400">Erreur: ${error.message}</div>`;
    }
}

async function loadInternationalChart() {
    const symbol = document.getElementById('indexSelector').value;
    const period = document.getElementById('periodSelectInternational').value;

    try {
        const response = await fetch(`/indicators/api/chart?symbol=${symbol}&period=${period}`);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        if (!data.success) {
            throw new Error(data.error || 'Erreur graphique');
        }

        // Mettre à jour les infos
        document.getElementById('indexInfo').innerHTML = `
            <span class="font-semibold text-white">${data.name || symbol}</span>
            <span class="mx-2">•</span>
            <span class="text-lg font-bold ${data.change >= 0 ? 'text-green-400' : 'text-red-400'}">
                ${data.current?.toFixed(2) || '--'}
            </span>
            <span class="ml-2 ${data.change >= 0 ? 'text-green-400' : 'text-red-400'}">
                ${data.change >= 0 ? '▲' : '▼'} ${Math.abs(data.change || 0).toFixed(2)}%
            </span>
        `;

        // Créer/mettre à jour le graphique
        renderChart('chartInternational', data.dates, data.prices, data.name || symbol, 'international');

        console.log('✅ Graphique international chargé');

    } catch (error) {
        console.error('❌ Erreur graphique international:', error);
        document.getElementById('indexInfo').innerHTML = '<span class="text-red-400">Erreur de chargement</span>';
    }
}

function changeInternationalIndex() {
    loadInternationalChart();
}

function refreshInternationalData() {
    console.log('🔄 Rafraîchissement International...');
    loadInternationalData();
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    const periodSelect = document.getElementById('periodSelectInternational');
    if (periodSelect) {
        periodSelect.addEventListener('change', () => loadInternationalChart());
    }
});

// ============================================================================
// ONGLET BOURSE PERSONNALISÉE
// ============================================================================

async function loadStocksData() {
    console.log('📈 Chargement du suivi boursier personnalisé...');

    try {
        await loadFixedIndicators();
        await loadUserSectors();
        await loadMainIndexChart();

    } catch (error) {
        console.error('❌ Erreur chargement bourse perso:', error);
    }
}

async function loadFixedIndicators() {
    try {
        const response = await fetch('/api/stocks/fixed-indicators');
        const data = await response.json();

        if (data.success) {
            updateFixedIndicator('vix', data.vix);
            updateFixedIndicator('gold', data.gold);
            updateFixedIndicator('oil', data.oil);
            updateFixedIndicator('uranium', data.uranium);
        }

        console.log('✅ Indicateurs fixes chargés');

    } catch (error) {
        console.error('❌ Erreur indicateurs fixes:', error);
    }
}

function updateFixedIndicator(type, data) {
    if (!data) return;

    const valueEl = document.getElementById(`${type}Value`);
    const changeEl = document.getElementById(`${type}Change`);

    if (valueEl) {
        valueEl.textContent = `$${data.price.toFixed(2)}`;
    }

    if (changeEl) {
        const changePercent = data.changePercent || 0;
        const arrow = changePercent >= 0 ? '▲' : '▼';
        const colorClass = changePercent >= 0 ? 'text-green-400' : 'text-red-400';

        changeEl.innerHTML = `<span class="${colorClass}">${arrow} ${Math.abs(changePercent).toFixed(2)}%</span>`;
    }
}

async function loadUserSectors() {
    try {
        const response = await fetch('/api/stocks/portfolios/sectors');
        const data = await response.json();

        if (data.success) {
            userSectors = data.sectors || [];
            renderSectors();

            // Mettre à jour le bouton
            const addBtn = document.getElementById('addSectorBtn');
            if (userSectors.length >= 4) {
                addBtn.disabled = true;
                addBtn.classList.add('opacity-50', 'cursor-not-allowed');
                addBtn.innerHTML = '<i class="fas fa-lock mr-2"></i>Maximum atteint (4/4)';
            } else {
                addBtn.disabled = false;
                addBtn.classList.remove('opacity-50', 'cursor-not-allowed');
                addBtn.innerHTML = `<i class="fas fa-plus mr-2"></i>Ajouter un secteur (${userSectors.length}/4)`;
            }
        }

        console.log('✅ Secteurs utilisateur chargés');

    } catch (error) {
        console.error('❌ Erreur secteurs:', error);
    }
}

function renderSectors() {
    const container = document.getElementById('sectorsContainer');

    if (userSectors.length === 0) {
        container.innerHTML = `
            <div class="text-center py-12 text-slate-400">
                <i class="fas fa-folder-open text-4xl mb-4"></i>
                <p>Aucun secteur configuré</p>
                <p class="text-sm mt-2">Cliquez sur "Ajouter un secteur" pour commencer</p>
            </div>
        `;
        return;
    }

    container.innerHTML = '';

    userSectors.forEach(sector => {
        const sectorCard = createSectorCard(sector);
        container.appendChild(sectorCard);
    });

    // Charger les prix des valeurs
    loadSectorsPrices();
}

function createSectorCard(sector) {
    const div = document.createElement('div');
    div.className = 'bg-slate-800/50 backdrop-blur-sm rounded-xl border border-slate-700 p-6';
    div.innerHTML = `
        <div class="flex items-center justify-between mb-4">
            <h4 class="text-lg font-bold text-white">
                <i class="fas fa-folder mr-2 text-blue-400"></i>
                ${sector.sector_name}
            </h4>
            <div class="flex gap-2">
                <button onclick="editSector(${sector.id})" class="text-yellow-400 hover:text-yellow-300 transition">
                    <i class="fas fa-edit"></i>
                </button>
                <button onclick="deleteSector(${sector.id})" class="text-red-400 hover:text-red-300 transition">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
        <div id="sector-stocks-${sector.id}" class="space-y-2">
            <!-- Valeurs chargées dynamiquement -->
            <div class="text-center py-4 text-slate-400">
                <i class="fas fa-spinner fa-spin"></i> Chargement...
            </div>
        </div>
    `;
    return div;
}

async function loadSectorsPrices() {
    for (const sector of userSectors) {
        try {
            const symbols = JSON.parse(sector.stock_symbols || '[]');
            if (symbols.length === 0) continue;

            const response = await fetch('/api/stocks/quotes/multiple', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ symbols })
            });

            const data = await response.json();

            if (data.success) {
                renderSectorStocks(sector.id, data.quotes);
            }

        } catch (error) {
            console.error(`❌ Erreur prix secteur ${sector.id}:`, error);
        }
    }
}

function renderSectorStocks(sectorId, quotes) {
    const container = document.getElementById(`sector-stocks-${sectorId}`);
    if (!container) return;

    container.innerHTML = '';

    quotes.forEach(quote => {
        const row = document.createElement('div');
        row.className = 'flex items-center justify-between p-3 bg-slate-700/30 rounded-lg hover:bg-slate-700/50 transition';

        const change = quote.changePercent || 0;
        const arrow = change >= 0 ? '▲' : '▼';
        const colorClass = change >= 0 ? 'text-green-400' : 'text-red-400';

        row.innerHTML = `
            <div class="flex-1">
                <span class="font-semibold text-white">${quote.symbol}</span>
                <span class="text-sm text-slate-400 ml-2">${quote.name || ''}</span>
            </div>
            <div class="flex items-center gap-4">
                <span class="text-white font-bold">$${quote.price.toFixed(2)}</span>
                <span class="${colorClass} text-sm font-semibold min-w-[80px] text-right">
                    ${arrow} ${Math.abs(change).toFixed(2)}%
                </span>
                <button onclick="openAlertModal('${quote.symbol}')" class="text-yellow-400 hover:text-yellow-300 transition">
                    <i class="fas fa-bell"></i>
                </button>
            </div>
        `;

        container.appendChild(row);
    });
}

async function loadMainIndexChart() {
    const symbol = document.getElementById('mainIndexSelector').value;

    try {
        const response = await fetch(`/indicators/api/chart?symbol=${symbol}&period=1mo`);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        if (data.success && data.dates && data.prices) {
            renderChart('chartMainIndex', data.dates, data.prices, data.name || symbol, 'mainIndex');
            console.log('✅ Graphique indice principal chargé');
        } else {
            throw new Error(data.error || 'Données invalides');
        }

    } catch (error) {
        console.error('❌ Erreur graphique indice principal:', error);
        const canvas = document.getElementById('chartMainIndex');
        if (canvas) {
            const ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = '#f87171';
            ctx.font = '14px Arial';
            ctx.textAlign = 'center';
            ctx.fillText(`Erreur: ${error.message}`, canvas.width / 2, canvas.height / 2);
        }
    }
}

function changeMainIndex() {
    loadMainIndexChart();
}

// ============================================================================
// GESTION DES SECTEURS (MODAL)
// ============================================================================

function openSectorModal(sectorId = null) {
    const modal = document.getElementById('sectorModal');
    modal.classList.remove('hidden');
    modal.classList.add('flex');

    if (sectorId) {
        // Mode édition
        const sector = userSectors.find(s => s.id === sectorId);
        if (sector) {
            document.getElementById('modalTitle').textContent = 'Modifier le Secteur';
            document.getElementById('sectorId').value = sector.id;
            document.getElementById('sectorName').value = sector.sector_name;

            const symbols = JSON.parse(sector.stock_symbols || '[]');
            generateStockInputs(symbols);
        }
    } else {
        // Mode création
        document.getElementById('modalTitle').textContent = 'Nouveau Secteur';
        document.getElementById('sectorId').value = '';
        document.getElementById('sectorName').value = '';
        generateStockInputs([]);
    }
}

function closeSectorModal() {
    const modal = document.getElementById('sectorModal');
    modal.classList.add('hidden');
    modal.classList.remove('flex');
    document.getElementById('sectorForm').reset();
}

function generateStockInputs(existingSymbols = []) {
    const container = document.getElementById('stockInputs');
    container.innerHTML = '';

    for (let i = 0; i < 5; i++) {
        const value = existingSymbols[i] || '';
        const input = document.createElement('div');
        input.className = 'flex gap-2';
        input.innerHTML = `
            <input type="text"
                   name="stock${i}"
                   value="${value}"
                   placeholder="Symbole (ex: AAPL)"
                   maxlength="10"
                   class="flex-1 bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white placeholder-slate-400 uppercase focus:outline-none focus:ring-2 focus:ring-blue-500">
            <button type="button" onclick="searchStock(${i})" class="bg-blue-600 hover:bg-blue-700 text-white px-4 rounded-lg transition">
                <i class="fas fa-search"></i>
            </button>
        `;
        container.appendChild(input);
    }
}

async function searchStock(index) {
    const input = document.querySelector(`input[name="stock${index}"]`);
    const query = input.value.trim();

    if (!query) return;

    // Simuler une recherche (à implémenter avec vraie API)
    console.log(`🔍 Recherche: ${query}`);

    // Pour l'instant, juste transformer en majuscules
    input.value = query.toUpperCase();
}

async function saveSector(event) {
    event.preventDefault();

    const sectorId = document.getElementById('sectorId').value;
    const sectorName = document.getElementById('sectorName').value;

    // Récupérer les symboles non vides
    const symbols = [];
    for (let i = 0; i < 5; i++) {
        const input = document.querySelector(`input[name="stock${i}"]`);
        if (input && input.value.trim()) {
            symbols.push(input.value.trim().toUpperCase());
        }
    }

    if (symbols.length === 0) {
        alert('⚠️ Veuillez ajouter au moins une valeur boursière');
        return;
    }

    try {
        const url = sectorId
            ? `/api/stocks/portfolios/sectors/${sectorId}`
            : '/api/stocks/portfolios/sectors';

        const method = sectorId ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                sector_name: sectorName,
                stock_symbols: JSON.stringify(symbols)
            })
        });

        const data = await response.json();

        if (data.success) {
            closeSectorModal();
            await loadUserSectors();
            console.log('✅ Secteur enregistré');
        } else {
            alert(`❌ Erreur: ${data.error}`);
        }

    } catch (error) {
        console.error('❌ Erreur sauvegarde secteur:', error);
        alert('❌ Erreur lors de l\'enregistrement');
    }
}

async function editSector(sectorId) {
    openSectorModal(sectorId);
}

async function deleteSector(sectorId) {
    if (!confirm('⚠️ Supprimer ce secteur et toutes ses valeurs ?')) {
        return;
    }

    try {
        const response = await fetch(`/api/stocks/portfolios/sectors/${sectorId}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (data.success) {
            await loadUserSectors();
            console.log('✅ Secteur supprimé');
        } else {
            alert(`❌ Erreur: ${data.error}`);
        }

    } catch (error) {
        console.error('❌ Erreur suppression secteur:', error);
        alert('❌ Erreur lors de la suppression');
    }
}

// ============================================================================
// GESTION DES ALERTES
// ============================================================================

function openAlertModal(symbol) {
    // TODO: Implémenter modal d'alerte avec intégration au système existant
    console.log(`🔔 Configuration alerte pour ${symbol}`);
    alert(`Configuration d'alerte pour ${symbol}\n(À implémenter avec le système d'alertes existant)`);
}

async function loadSettings() {
    console.log('⚙️ Chargement des paramètres...');
    // TODO: Charger les alertes actives
    await loadActiveAlerts();
}

async function loadActiveAlerts() {
    try {
        const response = await fetch('/api/stocks/alerts');
        const data = await response.json();

        const container = document.getElementById('activeAlertsList');

        if (data.success && data.alerts && data.alerts.length > 0) {
            container.innerHTML = '';
            data.alerts.forEach(alert => {
                const alertCard = createAlertCard(alert);
                container.appendChild(alertCard);
            });
        } else {
            container.innerHTML = `
                <div class="text-center py-8 text-slate-400">
                    <i class="fas fa-bell-slash text-3xl mb-3"></i>
                    <p>Aucune alerte configurée</p>
                </div>
            `;
        }

    } catch (error) {
        console.error('❌ Erreur chargement alertes:', error);
    }
}

function createAlertCard(alert) {
    const div = document.createElement('div');
    div.className = 'flex items-center justify-between p-4 bg-slate-700/30 rounded-lg';
    div.innerHTML = `
        <div class="flex-1">
            <span class="font-semibold text-white">${alert.stock_symbol}</span>
            <span class="text-sm text-slate-400 ml-3">${alert.condition}</span>
        </div>
        <div class="flex items-center gap-3">
            <span class="text-xs px-2 py-1 rounded ${alert.active ? 'bg-green-500/20 text-green-400' : 'bg-gray-500/20 text-gray-400'}">
                ${alert.active ? 'Actif' : 'Inactif'}
            </span>
            <button onclick="deleteAlert(${alert.id})" class="text-red-400 hover:text-red-300">
                <i class="fas fa-trash"></i>
            </button>
        </div>
    `;
    return div;
}

async function deleteAlert(alertId) {
    if (!confirm('Supprimer cette alerte ?')) return;

    try {
        const response = await fetch(`/api/stocks/alerts/${alertId}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (data.success) {
            await loadActiveAlerts();
            console.log('✅ Alerte supprimée');
        }

    } catch (error) {
        console.error('❌ Erreur suppression alerte:', error);
    }
}

// ============================================================================
// UTILITAIRES - CRÉATION DE CARTES
// ============================================================================

function createIndicatorCard(indicator) {
    const div = document.createElement('div');
    div.className = 'indicator-card bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6';

    const change = indicator.change_percent || indicator.changePercent || 0;
    const value = indicator.value || indicator.current || '--';
    const arrow = change >= 0 ? '▲' : '▼';
    const colorClass = change >= 0 ? 'text-green-400' : 'text-red-400';

    div.innerHTML = `
        <div class="flex items-center justify-between mb-3">
            <span class="text-sm text-slate-400">${indicator.name || indicator.label}</span>
            <i class="${indicator.icon || 'fas fa-chart-line'} text-blue-400"></i>
        </div>
        <div class="text-2xl font-bold text-white mb-2">${value}</div>
        <div class="flex items-center justify-between">
            <span class="${colorClass} text-sm font-semibold">
                ${arrow} ${Math.abs(change).toFixed(2)}%
            </span>
            <span class="text-xs text-slate-500">${indicator.source || ''}</span>
        </div>
    `;

    return div;
}

function createIndexCard(quote) {
    const div = document.createElement('div');
    div.className = 'bg-slate-700/30 rounded-lg p-4 hover:bg-slate-700/50 transition cursor-pointer';

    const change = quote.changePercent || 0;
    const arrow = change >= 0 ? '▲' : '▼';
    const colorClass = change >= 0 ? 'text-green-400' : 'text-red-400';

    div.innerHTML = `
        <div class="text-sm text-slate-400 mb-1">${quote.name || quote.symbol}</div>
        <div class="text-xl font-bold text-white mb-1">${quote.price?.toFixed(2) || '--'}</div>
        <div class="${colorClass} text-sm font-semibold">
            ${arrow} ${Math.abs(change).toFixed(2)}%
        </div>
    `;

    return div;
}

// ============================================================================
// UTILITAIRES - GRAPHIQUES
// ============================================================================

function renderChart(canvasId, labels, data, label, chartKey) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) {
        console.error(`Canvas ${canvasId} introuvable`);
        return;
    }

    const ctx = canvas.getContext('2d');

    // Détruire le graphique existant
    if (charts[chartKey]) {
        charts[chartKey].destroy();
    }

    // Créer le nouveau graphique
    charts[chartKey] = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: data,
                borderColor: 'rgb(59, 130, 246)',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 0,
                pointHoverRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(15, 23, 42, 0.9)',
                    borderColor: 'rgb(59, 130, 246)',
                    borderWidth: 1
                }
            },
            scales: {
                x: {
                    grid: {
                        color: 'rgba(148, 163, 184, 0.1)'
                    },
                    ticks: {
                        color: 'rgba(148, 163, 184, 0.7)'
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(148, 163, 184, 0.1)'
                    },
                    ticks: {
                        color: 'rgba(148, 163, 184, 0.7)'
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
}

// ============================================================================
// INITIALISATION
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Dashboard Économique Unifié - Initialisation...');

    // Charger l'onglet par défaut
    switchTab('france');

    // Configurer le rafraîchissement automatique
    const refreshInterval = document.getElementById('refreshInterval');
    if (refreshInterval) {
        refreshInterval.addEventListener('change', (e) => {
            const interval = parseInt(e.target.value);

            if (refreshIntervalId) {
                clearInterval(refreshIntervalId);
                refreshIntervalId = null;
            }

            if (interval > 0) {
                refreshIntervalId = setInterval(() => {
                    console.log('🔄 Rafraîchissement automatique...');
                    switch(currentTab) {
                        case 'france':
                            loadFranceData();
                            break;
                        case 'international':
                            loadInternationalData();
                            break;
                        case 'stocks':
                            loadStocksData();
                            break;
                    }
                }, interval * 1000);
                console.log(`⏰ Rafraîchissement automatique activé (${interval}s)`);
            }
        });
    }

    console.log('✅ Dashboard initialisé');
});
