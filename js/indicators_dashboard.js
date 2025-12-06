// static/js/indicators_dashboard.js - VERSION CORRIGÉE ET AMÉLIORÉE

class IndicatorsDashboard {
    constructor() {
        this.selectedCustomIndicators = [];
        this.currentChart = null;
        this.currentData = {};
        this.availableIndicators = [];
        this.init();
    }

    async init() {
        console.log('🚀 Initialisation Dashboard Indicateurs...');

        // Charger les préférences
        await this.loadPreferences();

        // Charger les indicateurs disponibles
        await this.loadAvailableIndicators();

        // Charger les données
        await this.loadAllData();

        // Configuration des événements
        this.setupEventListeners();

        console.log('✅ Dashboard initialisé');
    }

    setupEventListeners() {
        // Bouton rafraîchir
        const refreshBtn = document.getElementById('refreshDataBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.loadAllData());
        }

        // Bouton paramètres
        const settingsBtn = document.getElementById('settingsBtn');
        if (settingsBtn) {
            settingsBtn.addEventListener('click', () => this.openSettings());
        }

        // Fermer modal
        const closeBtn = document.getElementById('closeSettingsBtn');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.closeSettings());
        }

        // Annuler
        const cancelBtn = document.getElementById('cancelSettingsBtn');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => this.closeSettings());
        }

        // Sauvegarder
        const saveBtn = document.getElementById('saveSettingsBtn');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.saveSettings());
        }

        // Sélection période
        const periodSelect = document.getElementById('periodSelect');
        if (periodSelect) {
            periodSelect.addEventListener('change', (e) => {
                this.loadHistoricalChart('^FCHI', e.target.value);
            });
        }

        // Fermer modal en cliquant en dehors
        const modal = document.getElementById('settingsModal');
        if (modal) {
            modal.addEventListener('click', (e) => {
                if (e.target.id === 'settingsModal') {
                    this.closeSettings();
                }
            });
        }
    }

    async loadPreferences() {
        try {
            const response = await fetch('/indicators/api/preferences');
            const data = await response.json();

            if (data.success) {
                this.selectedCustomIndicators = data.selected_indicators.filter(
                    id => !['gdp', 'unemployment', 'hicp', 'trade_balance'].includes(id)
                );
                console.log('✅ Préférences chargées:', this.selectedCustomIndicators);
            }
        } catch (error) {
            console.error('❌ Erreur chargement préférences:', error);
        }
    }

    async loadAvailableIndicators() {
        try {
            const response = await fetch('/indicators/api/available');
            const data = await response.json();

            if (data.success) {
                // Filtrer les indicateurs par défaut
                this.availableIndicators = data.indicators.filter(
                    ind => !['gdp', 'unemployment', 'hicp', 'trade_balance'].includes(ind.id)
                );
                console.log('✅ Indicateurs disponibles:', this.availableIndicators.length);
            }
        } catch (error) {
            console.error('❌ Erreur chargement indicateurs:', error);
        }
    }

    async loadAllData() {
        try {
            this.showLoading();

            // Construire la liste des IDs (défaut + personnalisés)
            const defaultIds = ['gdp', 'unemployment', 'hicp', 'trade_balance'];
            const allIds = [...defaultIds, ...this.selectedCustomIndicators];

            // Charger les indicateurs
            const response = await fetch(`/indicators/api/data?ids=${allIds.join(',')}`);
            const data = await response.json();

            if (data.success) {
                this.currentData = data.indicators;
                this.renderIndicators();
                this.renderDetailedTable();
            }

            // Charger les indices internationaux
            await this.loadInternationalIndices();

            // Charger le graphique CAC 40
            await this.loadHistoricalChart('^FCHI', '6mo');

            // Mise à jour timestamp
            this.updateTimestamp();

        } catch (error) {
            console.error('❌ Erreur chargement données:', error);
            this.showError();
        }
    }

    renderIndicators() {
        const defaultGrid = document.getElementById('indicatorsGrid');
        const customGrid = document.getElementById('customIndicatorsGrid');
        const customSection = document.getElementById('customIndicatorsSection');

        if (!defaultGrid) return;

        // Indicateurs par défaut
        const defaultIds = ['gdp', 'unemployment', 'hicp', 'trade_balance'];
        defaultGrid.innerHTML = defaultIds.map(id => {
            const indicator = this.currentData[id];
            if (!indicator || !indicator.success) {
                return this.getErrorCard(id);
            }
            return this.getIndicatorCard(indicator);
        }).join('');

        // Indicateurs personnalisés
        if (this.selectedCustomIndicators.length > 0 && customGrid && customSection) {
            customSection.classList.remove('hidden');
            customGrid.innerHTML = this.selectedCustomIndicators.map(id => {
                const indicator = this.currentData[id];
                if (!indicator || !indicator.success) {
                    return this.getErrorCard(id);
                }
                return this.getIndicatorCard(indicator, true);
            }).join('');
        } else if (customSection) {
            customSection.classList.add('hidden');
        }
    }

    getIndicatorCard(indicator, isCustom = false) {
        const trendIcon = indicator.change_percent > 0 ? '📈' :
            indicator.change_percent < 0 ? '📉' : '➡️';
        const trendColor = indicator.change_percent > 0 ? 'text-green-600' :
            indicator.change_percent < 0 ? 'text-red-600' : 'text-gray-600';

        const categoryColors = {
            'macro': 'from-blue-500 to-blue-600',
            'employment': 'from-red-500 to-red-600',
            'prices': 'from-orange-500 to-orange-600',
            'trade': 'from-purple-500 to-purple-600',
            'finance': 'from-green-500 to-green-600',
            'production': 'from-indigo-500 to-indigo-600'
        };

        const gradient = categoryColors[indicator.category] || 'from-gray-500 to-gray-600';

        return `
            <div class="bg-gradient-to-br ${gradient} rounded-xl shadow-lg p-6 text-white border-2 border-white border-opacity-20 transform hover:scale-105 transition duration-200">
                <div class="flex items-center justify-between mb-4">
                    <h3 class="text-lg font-semibold">${this.truncateName(indicator.indicator_name)}</h3>
                    ${isCustom ? '<i class="fas fa-star text-yellow-300"></i>' : ''}
                </div>
                <div class="text-3xl font-bold mb-2">${indicator.current_value} ${indicator.unit}</div>
                <div class="flex justify-between items-center text-sm opacity-90 mb-2">
                    <span class="${trendColor} font-medium">${trendIcon} ${indicator.change_percent >= 0 ? '+' : ''}${indicator.change_percent}%</span>
                    <span>${indicator.period}</span>
                </div>
                <div class="text-xs opacity-75 flex items-center justify-between">
                    <span title="${indicator.description}">
                        <i class="fas fa-info-circle mr-1"></i>${indicator.frequency === 'M' ? 'Mensuel' : indicator.frequency === 'Q' ? 'Trimestriel' : 'Annuel'}
                    </span>
                    <span>${indicator.source}</span>
                </div>
                <div class="mt-3 text-xs opacity-80">
                    <a href="https://ec.europa.eu/eurostat/databrowser/view/${indicator.dataset}/default/table?lang=fr" 
                       target="_blank" class="underline hover:text-white">
                        <i class="fas fa-external-link-alt mr-1"></i>Voir données Eurostat
                    </a>
                </div>
            </div>
        `;
    }

    getErrorCard(id) {
        return `
            <div class="bg-gray-100 rounded-xl shadow-lg p-6 border border-gray-300">
                <div class="text-center text-gray-500">
                    <i class="fas fa-exclamation-triangle text-2xl mb-2"></i>
                    <p class="text-sm">Données temporairement indisponibles</p>
                    <p class="text-xs mt-1">${id}</p>
                </div>
            </div>
        `;
    }

    truncateName(name) {
        if (name.length > 30) {
            return name.substring(0, 27) + '...';
        }
        return name;
    }

    renderDetailedTable() {
        const tbody = document.getElementById('detailedTableBody');
        if (!tbody) return;

        const allIndicators = Object.values(this.currentData).filter(ind => ind.success);

        if (allIndicators.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" class="px-6 py-8 text-center text-gray-500">
                        Aucune donnée disponible
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = allIndicators.map(indicator => {
            const trendClass = indicator.change_percent > 0 ? 'text-green-600 font-medium' :
                indicator.change_percent < 0 ? 'text-red-600 font-medium' : 'text-gray-600';

            return `
                <tr class="hover:bg-gray-50">
                    <td class="px-6 py-4 text-sm font-medium text-gray-900">
                        <div>${indicator.indicator_name}</div>
                        <div class="text-xs text-gray-500 mt-1">${indicator.dataset}</div>
                    </td>
                    <td class="px-6 py-4 text-sm text-gray-500">${indicator.current_value} ${indicator.unit}</td>
                    <td class="px-6 py-4 text-sm ${trendClass}">
                        ${indicator.change_percent >= 0 ? '+' : ''}${indicator.change_percent}%
                    </td>
                    <td class="px-6 py-4 text-sm text-gray-500">${indicator.period}</td>
                    <td class="px-6 py-4 text-sm text-gray-500">${indicator.source}</td>
                </tr>
            `;
        }).join('');
    }

    async loadInternationalIndices() {
        try {
            const response = await fetch('/indicators/api/indices');
            const data = await response.json();

            if (data.success) {
                this.renderInternationalIndices(data.indices);
            }
        } catch (error) {
            console.error('❌ Erreur indices internationaux:', error);
        }
    }

    renderInternationalIndices(indices) {
        const container = document.getElementById('internationalIndices');
        if (!container) return;

        container.innerHTML = Object.values(indices).map(index => {
            const trendColor = index.trend === 'up' ? 'text-green-600' : 'text-red-600';
            const trendIcon = index.trend === 'up' ? '↑' : '↓';

            return `
                <div class="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition">
                    <div class="text-sm font-medium text-gray-600 mb-1">${index.name}</div>
                    <div class="text-2xl font-bold text-gray-900 mb-1">${index.current_price}</div>
                    <div class="${trendColor} text-sm font-medium">
                        ${trendIcon} ${index.change_percent >= 0 ? '+' : ''}${index.change_percent}%
                    </div>
                </div>
            `;
        }).join('');
    }

    async loadHistoricalChart(symbol, period) {
        try {
            const response = await fetch(`/indicators/api/historical/${symbol}?period=${period}`);
            const data = await response.json();

            if (data.success) {
                this.renderChart(data.data);

                // Mise à jour info
                const cac40Info = document.getElementById('cac40Info');
                if (cac40Info && data.data.length > 0) {
                    const latest = data.data[data.data.length - 1];
                    cac40Info.textContent = `Dernière valeur: ${latest.close} pts (${latest.date})`;
                }
            }
        } catch (error) {
            console.error('❌ Erreur graphique historique:', error);
        }
    }

    renderChart(data) {
        const ctx = document.getElementById('mainChart');
        if (!ctx) return;

        // Détruire l'ancien graphique
        if (this.currentChart) {
            this.currentChart.destroy();
        }

        const dates = data.map(item => item.date);
        const values = data.map(item => item.close);

        this.currentChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [{
                    label: 'CAC 40',
                    data: values,
                    borderColor: '#3B82F6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 2,
                    pointHoverRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function (context) {
                                return `CAC 40: ${context.parsed.y.toFixed(2)} pts`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        },
                        ticks: {
                            callback: function (value) {
                                return value.toFixed(0) + ' pts';
                            }
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            maxRotation: 45,
                            minRotation: 45
                        }
                    }
                }
            }
        });
    }

    openSettings() {
        const modal = document.getElementById('settingsModal');
        if (!modal) return;

        // Afficher les indicateurs disponibles
        this.renderAvailableIndicators();

        modal.classList.remove('hidden');
    }

    renderAvailableIndicators() {
        const container = document.getElementById('availableIndicators');
        if (!container) return;

        // Grouper par catégorie
        const byCategory = {};
        this.availableIndicators.forEach(ind => {
            if (!byCategory[ind.category]) {
                byCategory[ind.category] = [];
            }
            byCategory[ind.category].push(ind);
        });

        const categoryNames = {
            'macro': '📊 Macro-économie',
            'employment': '👥 Emploi',
            'prices': '💰 Prix',
            'trade': '🌍 Commerce',
            'finance': '🏛️ Finance publique',
            'production': '🏭 Production'
        };

        let html = '';

        Object.entries(byCategory).forEach(([category, indicators]) => {
            html += `
                <div class="mb-4">
                    <h5 class="font-semibold text-gray-700 mb-2 flex items-center">
                        ${categoryNames[category] || category}
                        <span class="ml-2 text-xs text-gray-500">(${indicators.length} disponibles)</span>
                    </h5>
                    <div class="space-y-2">
                        ${indicators.map(ind => {
                const checked = this.selectedCustomIndicators.includes(ind.id) ? 'checked' : '';
                return `
                                <label class="flex items-start p-3 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer transition border border-gray-200">
                                    <input type="checkbox" 
                                           class="indicator-checkbox mt-1 mr-3 rounded text-blue-600 focus:ring-2 focus:ring-blue-500" 
                                           data-id="${ind.id}"
                                           ${checked}>
                                    <div class="flex-1">
                                        <div class="font-medium text-gray-800">${ind.name}</div>
                                        <div class="text-xs text-gray-600 mt-1">${ind.description}</div>
                                        <div class="text-xs text-gray-500 mt-1 flex items-center space-x-2">
                                            <span class="bg-blue-100 text-blue-800 px-2 py-0.5 rounded">${ind.unit}</span>
                                            <span>•</span>
                                            <span>${ind.frequency === 'M' ? '📅 Mensuel' : ind.frequency === 'Q' ? '📅 Trimestriel' : '📅 Annuel'}</span>
                                            <span>•</span>
                                            <span class="text-gray-400">${ind.dataset}</span>
                                        </div>
                                        <div class="mt-2">
                                            <a href="https://ec.europa.eu/eurostat/databrowser/view/${ind.dataset}/default/table?lang=fr" 
                                               target="_blank" class="text-xs text-blue-600 hover:underline">
                                                <i class="fas fa-external-link-alt mr-1"></i>Voir sur Eurostat
                                            </a>
                                        </div>
                                    </div>
                                </label>
                            `;
            }).join('')}
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;

        // Limiter à 4 sélections
        const checkboxes = container.querySelectorAll('.indicator-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const checked = container.querySelectorAll('.indicator-checkbox:checked');
                if (checked.length > 4) {
                    e.target.checked = false;
                    this.showNotification('Maximum 4 indicateurs personnalisés', 'warning');
                }
            });
        });
    }

    async saveSettings() {
        const checkboxes = document.querySelectorAll('.indicator-checkbox:checked');
        const selected = Array.from(checkboxes).map(cb => cb.dataset.id);

        try {
            // Combiner avec les indicateurs par défaut
            const defaultIds = ['gdp', 'unemployment', 'hicp', 'trade_balance'];
            const allSelected = [...defaultIds, ...selected];

            const response = await fetch('/indicators/api/preferences', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    selected_indicators: allSelected
                })
            });

            const data = await response.json();

            if (data.success) {
                this.selectedCustomIndicators = selected;
                this.showNotification('✅ Préférences enregistrées', 'success');
                this.closeSettings();

                // Recharger les données
                await this.loadAllData();
            } else {
                this.showNotification('❌ Erreur lors de la sauvegarde', 'error');
            }

        } catch (error) {
            console.error('❌ Erreur sauvegarde:', error);
            this.showNotification('❌ Erreur lors de la sauvegarde', 'error');
        }
    }

    closeSettings() {
        const modal = document.getElementById('settingsModal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    showLoading() {
        const tbody = document.getElementById('detailedTableBody');
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" class="px-6 py-8 text-center text-gray-500">
                        <i class="fas fa-spinner fa-spin mr-2"></i>Chargement des données...
                    </td>
                </tr>
            `;
        }
    }

    showError() {
        const tbody = document.getElementById('detailedTableBody');
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="5" class="px-6 py-8 text-center text-red-500">
                        <i class="fas fa-exclamation-triangle mr-2"></i>Erreur de chargement
                        <button onclick="indicatorsDashboard.loadAllData()" class="ml-3 text-blue-600 hover:underline">
                            <i class="fas fa-redo mr-1"></i>Réessayer
                        </button>
                    </td>
                </tr>
            `;
        }
    }

    updateTimestamp() {
        const lastUpdate = document.getElementById('lastUpdate');
        if (lastUpdate) {
            const now = new Date();
            lastUpdate.textContent = now.toLocaleString('fr-FR', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        }
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        const bgColors = {
            'success': 'bg-green-500',
            'error': 'bg-red-500',
            'warning': 'bg-yellow-500',
            'info': 'bg-blue-500'
        };

        const icons = {
            'success': 'fa-check-circle',
            'error': 'fa-times-circle',
            'warning': 'fa-exclamation-triangle',
            'info': 'fa-info-circle'
        };

        notification.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${bgColors[type]} text-white transform transition-all duration-300`;

        notification.innerHTML = `
            <div class="flex items-center">
                <i class="fas ${icons[type]} mr-2"></i>
                <span>${message}</span>
            </div>
        `;

        document.body.appendChild(notification);

        // Animation d'entrée
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 10);

        // Suppression après 3 secondes
        setTimeout(() => {
            notification.style.transform = 'translateX(400px)';
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 3000);
    }
}

// Initialisation automatique
document.addEventListener('DOMContentLoaded', () => {
    window.indicatorsDashboard = new IndicatorsDashboard();
    console.log('✅ Dashboard Indicateurs initialisé');
});
