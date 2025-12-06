// static/js/economic-indicators.js
/**
 * Gestionnaire des Indicateurs Économiques Internationaux
 */

const EconomicIndicators = {
    currentTab: 'indices',
    charts: {},
    data: {},

    /**
     * Initialisation du module
     */
    init() {
        console.log('📊 Initialisation Economic Indicators');
        this.loadInitialData();
    },

    /**
     * Charge les données initiales
     */
    async loadInitialData() {
        try {
            // Charger le dashboard complet
            const response = await fetch('/api/economic/dashboard');
            const result = await response.json();

            if (result.success) {
                this.data = result.data;
                this.renderIndices();
                this.renderCommodities();
                this.renderCurrencies();
                this.loadSanctionsSummary();
            }
        } catch (error) {
            console.error('❌ Erreur chargement données:', error);
            this.showError('Erreur de chargement des données');
        }
    },

    /**
     * Change d'onglet
     */
    switchTab(tabName) {
        // Masquer tous les onglets
        document.querySelectorAll('.eco-tab-content').forEach(tab => {
            tab.classList.add('hidden');
        });

        // Désactiver tous les boutons
        document.querySelectorAll('.eco-tab').forEach(btn => {
            btn.classList.remove('active');
        });

        // Activer l'onglet sélectionné
        const contentTab = document.getElementById(`tab-${tabName}`);
        if (contentTab) {
            contentTab.classList.remove('hidden');
        }

        const button = document.querySelector(`.eco-tab[data-tab="${tabName}"]`);
        if (button) {
            button.classList.add('active');
        }

        this.currentTab = tabName;

        // Charger les données si nécessaire
        if (tabName === 'brics' && !this.data.brics) {
            this.loadBricsData();
        }
    },

    /**
     * Rafraîchit toutes les données
     */
    async refreshAll(event) {
        event.preventDefault();
        const btn = event.currentTarget;
        const icon = btn.querySelector('i');

        if (icon) {
            icon.classList.add('fa-spin');
        }

        try {
            await this.loadInitialData();
            this.showSuccess('Données actualisées');
        } catch (error) {
            this.showError('Erreur lors de l\'actualisation');
        } finally {
            if (icon) {
                icon.classList.remove('fa-spin');
            }
        }
    },

    /**
     * Affiche les indices boursiers
     */
    renderIndices() {
        const grid = document.getElementById('indices-grid');
        if (!grid || !this.data.indices) return;

        grid.innerHTML = '';

        const indicesNames = {
            '^GSPC': { name: 'S&P 500', icon: '🇺🇸', country: 'USA' },
            '^DJI': { name: 'Dow Jones', icon: '🇺🇸', country: 'USA' },
            '^IXIC': { name: 'NASDAQ', icon: '🇺🇸', country: 'USA' },
            '^FTSE': { name: 'FTSE 100', icon: '🇬🇧', country: 'UK' },
            '^GDAXI': { name: 'DAX', icon: '🇩🇪', country: 'Allemagne' },
            '000001.SS': { name: 'Shanghai', icon: '🇨🇳', country: 'Chine' },
            '^HSI': { name: 'Hang Seng', icon: '🇭🇰', country: 'Hong Kong' },
            '^N225': { name: 'Nikkei 225', icon: '🇯🇵', country: 'Japon' }
        };

        Object.entries(this.data.indices).forEach(([symbol, data]) => {
            if (data.error) return;

            const info = indicesNames[symbol] || { name: symbol, icon: '📊', country: '' };
            const change = data.change_percent || 0;
            const isPositive = change >= 0;

            const card = document.createElement('div');
            card.className = 'indicator-card';
            card.innerHTML = `
                <div class="flex justify-between items-start mb-3">
                    <div>
                        <span class="text-3xl">${info.icon}</span>
                        <p class="text-sm text-gray-600 mt-1">${info.country}</p>
                    </div>
                    <span class="px-2 py-1 rounded text-xs font-semibold ${isPositive ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                }">
                        ${isPositive ? '▲' : '▼'} ${Math.abs(change).toFixed(2)}%
                    </span>
                </div>
                <h4 class="font-bold text-gray-800 text-lg mb-1">${info.name}</h4>
                <div class="flex items-baseline">
                    <span class="text-2xl font-bold ${isPositive ? 'indicator-value-up' : 'indicator-value-down'}">
                        ${this.formatNumber(data.current_price)}
                    </span>
                    <span class="text-sm text-gray-500 ml-2">${data.currency}</span>
                </div>
                <div class="mt-3 pt-3 border-t border-gray-200 grid grid-cols-3 gap-2 text-xs">
                    <div>
                        <p class="text-gray-500">Haut</p>
                        <p class="font-semibold">${this.formatNumber(data.high)}</p>
                    </div>
                    <div>
                        <p class="text-gray-500">Bas</p>
                        <p class="font-semibold">${this.formatNumber(data.low)}</p>
                    </div>
                    <div>
                        <p class="text-gray-500">Vol.</p>
                        <p class="font-semibold">${this.formatVolume(data.volume)}</p>
                    </div>
                </div>
            `;
            grid.appendChild(card);
        });

        this.renderIndicesChart();
    },

    /**
     * Affiche les matières premières
     */
    renderCommodities() {
        const grid = document.getElementById('commodities-grid');
        if (!grid || !this.data.commodities) return;

        grid.innerHTML = '';

        const commoditiesNames = {
            'GC=F': { name: 'Or', icon: '🏆', unit: 'oz' },
            'SI=F': { name: 'Argent', icon: '🥈', unit: 'oz' },
            'CL=F': { name: 'Pétrole WTI', icon: '🛢️', unit: 'baril' },
            'BZ=F': { name: 'Pétrole Brent', icon: '⚫', unit: 'baril' },
            'NG=F': { name: 'Gaz Naturel', icon: '🔥', unit: 'MMBtu' }
        };

        Object.entries(this.data.commodities).forEach(([symbol, data]) => {
            if (data.error) return;

            const info = commoditiesNames[symbol] || { name: symbol, icon: '📦', unit: 'unité' };
            const change = data.change_percent || 0;
            const isPositive = change >= 0;

            const card = document.createElement('div');
            card.className = 'indicator-card';
            card.innerHTML = `
                <div class="flex justify-between items-center mb-4">
                    <div class="flex items-center">
                        <span class="text-4xl mr-3">${info.icon}</span>
                        <div>
                            <h4 class="font-bold text-gray-800">${info.name}</h4>
                            <p class="text-xs text-gray-500">Par ${info.unit}</p>
                        </div>
                    </div>
                    <span class="px-3 py-1 rounded-full text-sm font-bold ${isPositive ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                }">
                        ${isPositive ? '+' : ''}${change.toFixed(2)}%
                    </span>
                </div>
                <div class="text-3xl font-bold ${isPositive ? 'indicator-value-up' : 'indicator-value-down'}">
                    $${this.formatNumber(data.current_price)}
                </div>
                <div class="mt-4 grid grid-cols-2 gap-3 text-sm">
                    <div class="bg-gray-50 p-2 rounded">
                        <p class="text-gray-600 text-xs">Maximum</p>
                        <p class="font-semibold">${this.formatNumber(data.high)}</p>
                    </div>
                    <div class="bg-gray-50 p-2 rounded">
                        <p class="text-gray-600 text-xs">Minimum</p>
                        <p class="font-semibold">${this.formatNumber(data.low)}</p>
                    </div>
                </div>
            `;
            grid.appendChild(card);
        });

        this.renderCommoditiesChart();
    },

    /**
     * Affiche les devises
     */
    renderCurrencies() {
        const grid = document.getElementById('currencies-grid');
        if (!grid || !this.data.currencies) return;

        grid.innerHTML = '';

        const currenciesInfo = {
            'EURUSD=X': { name: 'EUR/USD', icon: '🇪🇺→🇺🇸', label: 'Euro → Dollar' },
            'GBPUSD=X': { name: 'GBP/USD', icon: '🇬🇧→🇺🇸', label: 'Livre → Dollar' },
            'JPYUSD=X': { name: 'JPY/USD', icon: '🇯🇵→🇺🇸', label: 'Yen → Dollar' },
            'CNYUSD=X': { name: 'CNY/USD', icon: '🇨🇳→🇺🇸', label: 'Yuan → Dollar' },
            'RUBUSD=X': { name: 'RUB/USD', icon: '🇷🇺→🇺🇸', label: 'Rouble → Dollar' }
        };

        Object.entries(this.data.currencies).forEach(([symbol, data]) => {
            if (data.error) return;

            const info = currenciesInfo[symbol] || { name: symbol, icon: '💱', label: symbol };
            const change = data.change_percent || 0;
            const isPositive = change >= 0;

            const card = document.createElement('div');
            card.className = 'indicator-card';
            card.innerHTML = `
                <div class="text-center mb-3">
                    <div class="text-3xl mb-2">${info.icon}</div>
                    <h4 class="font-bold text-gray-700 text-sm">${info.label}</h4>
                </div>
                <div class="text-center">
                    <div class="text-3xl font-bold ${isPositive ? 'indicator-value-up' : 'indicator-value-down'}">
                        ${data.current_price.toFixed(4)}
                    </div>
                    <span class="inline-block mt-2 px-3 py-1 rounded-full text-sm font-semibold ${isPositive ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                }">
                        ${isPositive ? '▲' : '▼'} ${Math.abs(change).toFixed(2)}%
                    </span>
                </div>
            `;
            grid.appendChild(card);
        });

        this.renderCurrenciesChart();
    },

    /**
     * Graphique des indices
     */
    renderIndicesChart() {
        const ctx = document.getElementById('indicesChart');
        if (!ctx || !this.data.indices) return;

        if (this.charts.indices) {
            this.charts.indices.destroy();
        }

        const labels = [];
        const values = [];
        const colors = [];

        Object.entries(this.data.indices).forEach(([symbol, data]) => {
            if (data.error) return;
            labels.push(symbol.replace('^', '').replace('.SS', ''));
            values.push(data.current_price);
            colors.push(data.change_percent >= 0 ? '#10b981' : '#ef4444');
        });

        this.charts.indices = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Valeur actuelle',
                    data: values,
                    backgroundColor: colors,
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                return `${this.formatNumber(context.parsed.y)} USD`;
                            }
                        }
                    }
                },
                scales: {
                    y: { beginAtZero: false }
                }
            }
        });
    },

    /**
     * Graphique des commodités
     */
    renderCommoditiesChart() {
        const ctx = document.getElementById('commoditiesChart');
        if (!ctx || !this.data.commodities) return;

        if (this.charts.commodities) {
            this.charts.commodities.destroy();
        }

        const labels = [];
        const values = [];

        Object.entries(this.data.commodities).forEach(([symbol, data]) => {
            if (data.error) return;
            labels.push(symbol.replace('=F', ''));
            values.push(data.current_price);
        });

        this.charts.commodities = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Prix (USD)',
                    data: values,
                    borderColor: '#f59e0b',
                    backgroundColor: 'rgba(245, 158, 11, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: { display: false }
                }
            }
        });
    },

    /**
     * Graphique des devises
     */
    renderCurrenciesChart() {
        const ctx = document.getElementById('currenciesChart');
        if (!ctx || !this.data.currencies) return;

        if (this.charts.currencies) {
            this.charts.currencies.destroy();
        }

        const labels = [];
        const values = [];

        Object.entries(this.data.currencies).forEach(([symbol, data]) => {
            if (data.error) return;
            labels.push(symbol.replace('=X', ''));
            values.push(data.current_price);
        });

        this.charts.currencies = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Taux de change',
                    data: values,
                    backgroundColor: 'rgba(59, 130, 246, 0.2)',
                    borderColor: '#3b82f6',
                    pointBackgroundColor: '#3b82f6'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true
            }
        });
    },

    /**
     * Charge les données Banque Mondiale
     */
    async fetchWorldBank() {
        const countrySelect = document.getElementById('wb-country');
        const indicatorSelect = document.getElementById('wb-indicator');
        const yearsInput = document.getElementById('wb-years');

        const countries = Array.from(countrySelect.selectedOptions).map(o => o.value);
        const indicator = indicatorSelect.value;
        const years = parseInt(yearsInput.value);

        if (countries.length === 0) {
            this.showError('Sélectionnez au moins un pays');
            return;
        }

        try {
            const response = await fetch('/api/economic/worldbank/fetch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ countries, indicator, years })
            });

            const result = await response.json();

            if (result.success) {
                this.renderWorldBankResults(result.data, indicator);
            } else {
                this.showError(result.error);
            }
        } catch (error) {
            console.error('❌ Erreur World Bank:', error);
            this.showError('Erreur de récupération des données');
        }
    },

    /**
     * Affiche les résultats Banque Mondiale
     */
    renderWorldBankResults(data, indicator) {
        const container = document.getElementById('worldbank-results');
        if (!container) return;

        container.innerHTML = '<h3 class="text-xl font-bold mb-4 text-gray-800">Résultats</h3>';

        Object.entries(data).forEach(([country, countryData]) => {
            if (countryData.error || countryData.length === 0) return;

            const div = document.createElement('div');
            div.className = 'mb-6';

            const countryName = countryData[0]?.country_name || country;
            const indicatorName = countryData[0]?.indicator_name || indicator;

            let tableHTML = `
                <h4 class="font-bold text-lg mb-2">${countryName}</h4>
                <p class="text-sm text-gray-600 mb-3">${indicatorName}</p>
                <table class="min-w-full border">
                    <thead class="bg-gray-100">
                        <tr>
                            <th class="px-4 py-2 border">Année</th>
                            <th class="px-4 py-2 border">Valeur</th>
                        </tr>
                    </thead>
                    <tbody>
            `;

            countryData.forEach(entry => {
                tableHTML += `
                    <tr class="hover:bg-gray-50">
                        <td class="px-4 py-2 border font-semibold">${entry.year}</td>
                        <td class="px-4 py-2 border">${this.formatNumber(entry.value)}</td>
                    </tr>
                `;
            });

            tableHTML += '</tbody></table>';
            div.innerHTML = tableHTML;
            container.appendChild(div);
        });
    },

    /**
     * Charge le résumé des sanctions
     */
    async loadSanctionsSummary() {
        try {
            const response = await fetch('/api/economic/sanctions/summary');
            const result = await response.json();

            if (result.success) {
                const summary = result.data;

                document.getElementById('sanctions-total').textContent = summary.total.toLocaleString();
                document.getElementById('sanctions-countries').textContent = summary.by_country.length;
                document.getElementById('sanctions-types').textContent = summary.by_type.length;

                this.renderSanctionsCharts(summary);
            }
        } catch (error) {
            console.error('❌ Erreur sanctions summary:', error);
        }
    },

    /**
     * Récupère les sanctions complètes
     */
    async fetchSanctions() {
        try {
            const response = await fetch('/api/economic/sanctions/fetch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({})
            });

            const result = await response.json();

            if (result.success) {
                this.renderSanctionsList(result.data.sanctions);
                this.showSuccess(`${result.data.total} sanctions chargées`);
            }
        } catch (error) {
            console.error('❌ Erreur fetch sanctions:', error);
        }
    },

    /**
     * Affiche la liste des sanctions
     */
    renderSanctionsList(sanctions) {
        const container = document.getElementById('sanctions-list');
        if (!container) return;

        container.innerHTML = '';

        sanctions.slice(0, 50).forEach(sanction => {
            const div = document.createElement('div');
            div.className = 'sanction-item';
            div.innerHTML = `
                <div class="flex justify-between items-start">
                    <div class="flex-1">
                        <h4 class="font-bold text-gray-800">${sanction.name}</h4>
                        <p class="text-sm text-gray-600 mt-1">
                            <span class="font-semibold">Type:</span> ${sanction.type} |
                            <span class="font-semibold">Pays:</span> ${sanction.countries.join(', ')}
                        </p>
                        ${sanction.reason ? `<p class="text-xs text-gray-500 mt-2">${sanction.reason}</p>` : ''}
                    </div>
                    <span class="px-2 py-1 bg-red-600 text-white text-xs rounded">${sanction.sanctions.join(', ')}</span>
                </div>
            `;
            container.appendChild(div);
        });
    },

    /**
     * Graphiques des sanctions
     */
    renderSanctionsCharts(summary) {
        // Graphique par pays
        const ctxCountry = document.getElementById('sanctionsCountryChart');
        if (ctxCountry) {
            if (this.charts.sanctionsCountry) {
                this.charts.sanctionsCountry.destroy();
            }

            this.charts.sanctionsCountry = new Chart(ctxCountry, {
                type: 'bar',
                data: {
                    labels: summary.by_country.map(c => c.country),
                    datasets: [{
                        label: 'Nombre de sanctions',
                        data: summary.by_country.map(c => c.count),
                        backgroundColor: '#ef4444'
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: true
                }
            });
        }

        // Graphique par type
        const ctxType = document.getElementById('sanctionsTypeChart');
        if (ctxType) {
            if (this.charts.sanctionsType) {
                this.charts.sanctionsType.destroy();
            }

            this.charts.sanctionsType = new Chart(ctxType, {
                type: 'doughnut',
                data: {
                    labels: summary.by_type.map(t => t.type),
                    datasets: [{
                        data: summary.by_type.map(t => t.count),
                        backgroundColor: ['#ef4444', '#f59e0b', '#10b981', '#3b82f6', '#8b5cf6']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true
                }
            });
        }
    },

    /**
     * Charge les données BRICS
     */
    async loadBricsData() {
        try {
            const response = await fetch('/api/economic/brics');
            const result = await response.json();

            if (result.success) {
                this.data.brics = result.data;
                this.renderBricsCharts();
            }
        } catch (error) {
            console.error('❌ Erreur BRICS:', error);
        }
    },

    /**
     * Graphiques BRICS
     */
    renderBricsCharts() {
        if (!this.data.brics) return;

        const countries = ['BR', 'RU', 'IN', 'CN', 'ZA'];
        const countryNames = {
            'BR': 'Brésil',
            'RU': 'Russie',
            'IN': 'Inde',
            'CN': 'Chine',
            'ZA': 'Afr. Sud'
        };

        // PIB
        const ctxGdp = document.getElementById('bricsGdpChart');
        if (ctxGdp && this.data.brics.gdp) {
            if (this.charts.bricsGdp) {
                this.charts.bricsGdp.destroy();
            }

            const gdpData = countries.map(c => {
                const data = this.data.brics.gdp[c];
                if (data && data.length > 0) {
                    return data[0].value / 1e9; // Convertir en milliards
                }
                return 0;
            });

            this.charts.bricsGdp = new Chart(ctxGdp, {
                type: 'bar',
                data: {
                    labels: countries.map(c => countryNames[c]),
                    datasets: [{
                        label: 'PIB (Milliards USD)',
                        data: gdpData,
                        backgroundColor: ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6']
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true
                }
            });
        }

        // Inflation
        const ctxInflation = document.getElementById('bricsInflationChart');
        if (ctxInflation && this.data.brics.inflation) {
            if (this.charts.bricsInflation) {
                this.charts.bricsInflation.destroy();
            }

            const inflationData = countries.map(c => {
                const data = this.data.brics.inflation[c];
                if (data && data.length > 0) {
                    return data[0].value;
                }
                return 0;
            });

            this.charts.bricsInflation = new Chart(ctxInflation, {
                type: 'line',
                data: {
                    labels: countries.map(c => countryNames[c]),
                    datasets: [{
                        label: 'Inflation (%)',
                        data: inflationData,
                        borderColor: '#ef4444',
                        backgroundColor: 'rgba(239, 68, 68, 0.1)',
                        tension: 0.4,
                        fill: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true
                }
            });
        }
    },

    /**
     * Exporte les données
     */
    exportData() {
        const dataStr = JSON.stringify(this.data, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(dataBlob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `economic-indicators-${Date.now()}.json`;
        link.click();
        URL.revokeObjectURL(url);
        this.showSuccess('Données exportées');
    },

    /**
     * Utilitaires de formatage
     */
    formatNumber(num) {
        if (!num) return '0';
        return parseFloat(num).toLocaleString('fr-FR', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    },

    formatVolume(vol) {
        if (!vol) return '0';
        if (vol >= 1e9) return `${(vol / 1e9).toFixed(1)}B`;
        if (vol >= 1e6) return `${(vol / 1e6).toFixed(1)}M`;
        if (vol >= 1e3) return `${(vol / 1e3).toFixed(1)}K`;
        return vol.toString();
    },

    /**
     * Messages utilisateur
     */
    showSuccess(message) {
        console.log('✅', message);
        // Implémenter une vraie notification si nécessaire
    },

    showError(message) {
        console.error('❌', message);
        alert(message);
    }
};

// Initialisation au chargement
document.addEventListener('DOMContentLoaded', () => {
    if (window.location.pathname === '/indicators') {
        EconomicIndicators.init();
    }
});
