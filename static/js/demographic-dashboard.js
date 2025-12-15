/**
 * Dashboard démographique - GEOPOL Analytics
 * Gère l'interface utilisateur et les appels API
 */

class DemographicDashboard {
    constructor() {
        this.baseUrl = '/demographic/api';
        this.currentData = null;
        this.chart = null;

        // Initialisation
        this.init();
    }

    async init() {
        console.log('📊 Initialisation du dashboard démographique...');

        // Charger les données initiales
        await this.loadStats();
        await this.loadCountries();
        await this.loadIndicators();

        // Configurer les événements
        this.setupEventListeners();

        // Initialiser le graphique
        this.initChart();

        console.log('✅ Dashboard prêt');
    }

    async loadStats() {
        try {
            console.log('📈 Chargement des statistiques...');
            const response = await fetch(`${this.baseUrl}/stats`);
            const data = await response.json();

            if (data.success) {
                this.updateStats(data.stats);
            }
        } catch (error) {
            console.error('Erreur stats:', error);
            this.showError('stats', 'Impossible de charger les statistiques');
        }
    }

    async loadCountries() {
        try {
            console.log('🌍 Chargement des pays...');
            const response = await fetch(`${this.baseUrl}/countries`);
            const data = await response.json();

            if (data.success) {
                this.populateCountrySelect(data.countries);
            }
        } catch (error) {
            console.error('Erreur pays:', error);
            this.showError('countries', 'Impossible de charger la liste des pays');
        }
    }

    async loadIndicators() {
        try {
            console.log('📊 Chargement des indicateurs...');
            const response = await fetch(`${this.baseUrl}/indicators`);
            const data = await response.json();

            if (data.success) {
                this.populateIndicatorSelect(data.indicators);
            }
        } catch (error) {
            console.error('Erreur indicateurs:', error);
            this.showError('indicators', 'Impossible de charger la liste des indicateurs');
        }
    }

    updateStats(stats) {
        // Mettre à jour l'affichage
        const countriesEl = document.getElementById('total-countries');
        const indicatorsEl = document.getElementById('total-indicators');
        const countriesLoading = document.getElementById('countries-loading');
        const indicatorsLoading = document.getElementById('indicators-loading');

        if (countriesEl) {
            countriesEl.textContent = stats.countries || 0;
            if (countriesLoading) {
                countriesLoading.textContent = stats.mode === 'demo' ? 'Mode démo' : 'Données réelles';
            }
        }

        if (indicatorsEl) {
            indicatorsEl.textContent = stats.indicators || 0;
            if (indicatorsLoading) {
                indicatorsLoading.textContent = stats.mode === 'demo' ? 'Mode démo' : 'Données réelles';
            }
        }
    }

    populateCountrySelect(countries) {
        const select = document.getElementById('country-select');
        if (!select) return;

        select.innerHTML = '<option value="">Sélectionnez un pays</option>';

        if (!countries || countries.length === 0) {
            const option = document.createElement('option');
            option.value = '';
            option.textContent = 'Aucun pays disponible';
            option.disabled = true;
            select.appendChild(option);
            return;
        }

        countries.forEach(country => {
            const option = document.createElement('option');
            option.value = country.code;
            option.textContent = `${country.name} (${country.indicators || 0} indicateurs)`;
            select.appendChild(option);
        });
    }

    populateIndicatorSelect(indicators) {
        const select = document.getElementById('indicator-select');
        if (!select) return;

        select.innerHTML = '<option value="">Sélectionnez un indicateur</option>';

        if (!indicators || indicators.length === 0) {
            const option = document.createElement('option');
            option.value = '';
            option.textContent = 'Aucun indicateur disponible';
            option.disabled = true;
            select.appendChild(option);
            return;
        }

        indicators.forEach(indicator => {
            const option = document.createElement('option');
            option.value = indicator.id;
            option.textContent = `${indicator.name || indicator.id} (${indicator.source})`;
            select.appendChild(option);
        });
    }

    setupEventListeners() {
        // Sélection de pays
        const countrySelect = document.getElementById('country-select');
        if (countrySelect) {
            countrySelect.addEventListener('change', (e) => {
                this.loadCountryData(e.target.value);
            });
        }

        // Sélection d'indicateur
        const indicatorSelect = document.getElementById('indicator-select');
        if (indicatorSelect) {
            indicatorSelect.addEventListener('change', (e) => {
                this.loadIndicatorData(e.target.value);
            });
        }

        // Boutons de collecte
        const collectDemo = document.getElementById('collect-demo');
        const collectQuick = document.getElementById('collect-quick');
        const collectAll = document.getElementById('collect-all');

        if (collectDemo) {
            collectDemo.addEventListener('click', () => this.collectData('demo'));
        }
        if (collectQuick) {
            collectQuick.addEventListener('click', () => this.collectData('quick'));
        }
        if (collectAll) {
            collectAll.addEventListener('click', () => this.collectData('all'));
        }
    }

    async loadCountryData(countryCode) {
        if (!countryCode) {
            this.hideCountryData();
            return;
        }

        try {
            this.showLoading('country-data');

            const response = await fetch(`${this.baseUrl}/country/${countryCode}`);
            const data = await response.json();

            if (data.success) {
                this.displayCountryData(data);
                this.updateTableWithCountryData(data);
                this.updateChartWithCountryData(data);
            } else {
                this.showError('country-data', data.error || 'Erreur inconnue');
            }
        } catch (error) {
            console.error('Erreur données pays:', error);
            this.showError('country-data', 'Erreur réseau');
        }
    }

    async loadIndicatorData(indicatorId) {
        if (!indicatorId) {
            this.hideIndicatorData();
            return;
        }

        try {
            this.showLoading('indicator-data');

            // Pour l'instant, simulation
            const select = document.getElementById('indicator-select');
            const selectedOption = select.options[select.selectedIndex];

            this.displayIndicatorData({
                id: indicatorId,
                name: selectedOption.textContent,
                source: 'simulation'
            });

        } catch (error) {
            console.error('Erreur données indicateur:', error);
            this.showError('indicator-data', 'Erreur lors du chargement');
        }
    }

    displayCountryData(data) {
        const container = document.getElementById('country-data');
        if (!container) return;

        const html = `
            <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h4 class="text-lg font-bold text-blue-800 mb-3">
                    <i class="fas fa-flag mr-2"></i>${data.country_code}
                </h4>
                <div class="space-y-2">
                    <div class="flex justify-between">
                        <span class="text-gray-600">Données disponibles:</span>
                        <span class="font-semibold">${data.categories?.length || 0} catégories</span>
                    </div>
                    <div class="text-sm text-gray-500">
                        Sélectionnez des données dans le tableau pour plus de détails
                    </div>
                </div>
            </div>
        `;

        container.innerHTML = html;
        container.classList.remove('hidden');
    }

    displayIndicatorData(data) {
        const container = document.getElementById('indicator-data');
        if (!container) return;

        const html = `
            <div class="bg-green-50 border border-green-200 rounded-lg p-4">
                <h4 class="text-lg font-bold text-green-800 mb-2">
                    <i class="fas fa-chart-line mr-2"></i>${data.name}
                </h4>
                <div class="text-sm">
                    <div class="mb-2"><strong>ID:</strong> <code>${data.id}</code></div>
                    <div class="mb-2"><strong>Source:</strong> ${data.source}</div>
                </div>
            </div>
        `;

        container.innerHTML = html;
        container.classList.remove('hidden');
    }

    async collectData(action) {
        const statusDiv = document.getElementById('collect-status');
        if (statusDiv) {
            statusDiv.innerHTML = `
                <div class="bg-blue-50 border border-blue-200 rounded p-3">
                    <div class="flex items-center">
                        <div class="loading w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full mr-2"></div>
                        <span class="text-blue-600">Collecte en cours...</span>
                    </div>
                </div>
            `;
            statusDiv.classList.remove('hidden');
        }

        try {
            let url;
            let method = 'GET';
            let body = null;

            switch (action) {
                case 'demo':
                    url = `${this.baseUrl}/collect/demo`;
                    break;
                case 'quick':
                    url = `${this.baseUrl}/collect/quick`;
                    break;
                case 'all':
                    url = `${this.baseUrl}/collect`;
                    method = 'POST';
                    body = JSON.stringify({ countries: ['FR', 'DE', 'ES', 'IT', 'UK'] });
                    break;
                default:
                    throw new Error('Action inconnue');
            }

            const options = { method };
            if (body) {
                options.headers = { 'Content-Type': 'application/json' };
                options.body = body;
            }

            const response = await fetch(url, options);
            const data = await response.json();

            if (data.success) {
                this.showSuccess(`✅ ${data.message || 'Collecte réussie'}`);

                // Recharger les données
                await this.loadStats();
                await this.loadCountries();
                await this.loadIndicators();

            } else {
                this.showError('collect', data.error || 'Erreur lors de la collecte');
            }

        } catch (error) {
            console.error('Erreur collecte:', error);
            this.showError('collect', error.message);
        }
    }

    updateTableWithCountryData(data) {
        const tbody = document.getElementById('data-table-body');
        if (!tbody) return;

        if (!data.data || Object.keys(data.data).length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="4" class="px-4 py-4 text-center text-gray-500">
                        Aucune donnée disponible pour ce pays
                    </td>
                </tr>
            `;
            return;
        }

        let rows = '';
        Object.entries(data.data).forEach(([category, items]) => {
            items.forEach(item => {
                rows += `
                    <tr class="hover:bg-gray-50">
                        <td class="px-4 py-3 whitespace-nowrap">${data.country_code}</td>
                        <td class="px-4 py-3">${item.indicator}</td>
                        <td class="px-4 py-3 font-medium">${this.formatValue(item.value)} ${item.unit || ''}</td>
                        <td class="px-4 py-3">${item.year}</td>
                    </tr>
                `;
            });
        });

        tbody.innerHTML = rows;
    }

    initChart() {
        const ctx = document.getElementById('data-chart');
        if (!ctx) return;

        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: []
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    title: {
                        display: true,
                        text: 'Données démographiques'
                    }
                }
            }
        });
    }

    updateChartWithCountryData(data) {
        if (!this.chart || !data.data) return;

        // Mettre à jour le graphique avec les données
        // (simplifié pour l'exemple)
    }

    // Méthodes utilitaires
    formatValue(value) {
        if (value >= 1000000000) {
            return (value / 1000000000).toFixed(2) + 'B';
        }
        if (value >= 1000000) {
            return (value / 1000000).toFixed(2) + 'M';
        }
        if (value >= 1000) {
            return (value / 1000).toFixed(2) + 'K';
        }
        return value.toLocaleString('fr-FR');
    }

    showLoading(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.innerHTML = `
                <div class="text-center py-4">
                    <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                    <p class="mt-2 text-gray-600">Chargement...</p>
                </div>
            `;
            element.classList.remove('hidden');
        }
    }

    hideCountryData() {
        const element = document.getElementById('country-data');
        if (element) {
            element.classList.add('hidden');
        }
    }

    hideIndicatorData() {
        const element = document.getElementById('indicator-data');
        if (element) {
            element.classList.add('hidden');
        }
    }

    showSuccess(message) {
        const statusDiv = document.getElementById('collect-status');
        if (statusDiv) {
            statusDiv.innerHTML = `
                <div class="bg-green-50 border border-green-200 rounded p-3">
                    <div class="flex items-center">
                        <i class="fas fa-check-circle text-green-600 mr-2"></i>
                        <span class="text-green-600">${message}</span>
                    </div>
                </div>
            `;
            statusDiv.classList.remove('hidden');

            setTimeout(() => {
                statusDiv.classList.add('hidden');
            }, 5000);
        }
    }

    showError(context, message) {
        console.error(`[${context}] ${message}`);

        const element = document.getElementById(`${context}-data`) || document.getElementById('collect-status');
        if (element) {
            element.innerHTML = `
                <div class="bg-red-50 border border-red-200 rounded p-3">
                    <div class="flex items-center">
                        <i class="fas fa-exclamation-circle text-red-600 mr-2"></i>
                        <span class="text-red-600">${message}</span>
                    </div>
                </div>
            `;
            element.classList.remove('hidden');
        }
    }
}

// Initialiser le dashboard quand la page est prête
document.addEventListener('DOMContentLoaded', () => {
    window.demographicDashboard = new DemographicDashboard();
});