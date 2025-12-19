// static/js/indicators_dashboard_enhanced.js - VERSION CORRIGÉE

class EnhancedIndicatorsDashboard {
    constructor() {
        this.currentData = {};
        this.currentChart = null;
        this.refreshInterval = null;
        this.displaySettings = {
            showAlerts: true,
            showInternational: true,
            showDetailedTable: true,
            theme: 'light',
            refresh_interval: 300000 // 5 minutes par défaut
        };
        this.isLoading = false;
        this.init();
    }

    async init() {
        console.log('🚀 Initialisation Enhanced Dashboard...');

        try {
            // Charger les préférences
            await this.loadPreferences();
            await this.loadAllData();
            this.setupEventListeners();
            this.setupFilters();
            this.startAutoRefresh();
            console.log('✅ Dashboard Enhanced initialisé');
        } catch (error) {
            console.error('❌ Erreur initialisation:', error);
            this.showError('Erreur initialisation dashboard');
        }
    }

    setupEventListeners() {
        // Délégation d'événements pour les boutons dynamiques
        document.addEventListener('click', (e) => {
            if (e.target.id === 'refreshDataBtn' || e.target.closest('#refreshDataBtn')) {
                e.preventDefault();
                this.forceRefresh();
            }
            if (e.target.id === 'settingsBtn' || e.target.closest('#settingsBtn')) {
                e.preventDefault();
                this.openSettings();
            }
            if (e.target.id === 'exportBtn' || e.target.closest('#exportBtn')) {
                e.preventDefault();
                this.exportData();
            }
            if (e.target.id === 'alertsBtn' || e.target.closest('#alertsBtn')) {
                e.preventDefault();
                this.showAlertsModal();
            }
        });

        // Sélection période
        const periodSelect = document.getElementById('periodSelect');
        if (periodSelect) {
            periodSelect.addEventListener('change', (e) => {
                this.loadHistoricalChart('^FCHI', e.target.value);
            });
        }

        // Toggle sections
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('toggle-section')) {
                const section = e.target.dataset.section;
                this.toggleSection(section);
            }
        });
    }

    setupFilters() {
        // Filtres par catégorie
        const categoryFilter = document.getElementById('categoryFilter');
        const sourceFilter = document.getElementById('sourceFilter');
        const reliabilityFilter = document.getElementById('reliabilityFilter');

        [categoryFilter, sourceFilter, reliabilityFilter].forEach(filter => {
            if (filter) {
                filter.addEventListener('change', () => this.applyFilters());
            }
        });
    }

    async loadPreferences() {
        try {
            const response = await fetch('/indicators/api/settings');
            const data = await response.json();

            if (data && !data.error) {
                this.displaySettings = {
                    ...this.displaySettings,
                    refresh_interval: data.refresh_interval || 300000,
                    default_view: data.default_view || 'chart',
                    eurostat_enabled: data.eurostat_enabled !== false,
                    notifications: data.notifications !== false
                };
                console.log('✅ Préférences chargées:', this.displaySettings);
            }
        } catch (error) {
            console.warn('⚠️ Pas de préférences sauvegardées, utilisation des valeurs par défaut');
        }
    }

    async loadAllData() {
        if (this.isLoading) return;
        this.isLoading = true;

        try {
            this.showLoading();

            // Récupérer toutes les données via l'endpoint unifié
            const response = await fetch('/indicators/api/dashboard');
            const data = await response.json();

            if (data && data.status === 'success') {
                this.currentData = data;
                console.log('📊 Données reçues:', data);
                this.renderAllComponents();
                this.updateSystemStatus(data);
                if (data.alerts) {
                    this.renderAlerts(data.alerts);
                }
            } else {
                throw new Error(data.error || 'Erreur chargement données');
            }

        } catch (error) {
            console.error('❌ Erreur chargement données:', error);
            this.showError('Erreur de connexion');
        } finally {
            this.isLoading = false;
        }
    }

    renderAllComponents() {
        // 1. Indicateurs principaux
        this.renderMainIndicators();

        // 2. Indicateurs complémentaires (INSEE)
        this.renderSupplementaryIndicators();

        // 3. Indices internationaux
        this.renderInternationalIndices();

        // 4. Tableau détaillé
        this.renderDetailedTable();

        // 5. Graphique CAC 40
        this.loadHistoricalChart('^FCHI', '6mo');

        // 6. Mise à jour timestamp
        this.updateTimestamp();
    }

    renderMainIndicators() {
        const grid = document.getElementById('indicatorsGrid');
        if (!grid) return;

        // ✅ CORRECTION : Vérifier si les indicateurs existent et sont dans le bon format
        const indicators = this.currentData.indicators || {};

        // Convertir en array pour prendre les 4 premiers
        const indicatorArray = Object.values(indicators);

        if (indicatorArray.length === 0) {
            grid.innerHTML = '<div class="col-span-4 text-center text-gray-500">Aucun indicateur disponible</div>';
            return;
        }

        // Prendre les 4 premiers indicateurs
        const mainIndicators = indicatorArray.slice(0, 4);

        grid.innerHTML = mainIndicators.map(indicator =>
            this.createIndicatorCard(indicator, false)
        ).join('');
    }

    renderSupplementaryIndicators() {
        const section = document.getElementById('supplementaryIndicatorsSection');
        const grid = document.getElementById('supplementaryIndicatorsGrid');

        if (!section || !grid) return;

        // ✅ CORRECTION : Filtrer uniquement INSEE
        const indicators = this.currentData.indicators || {};
        const inseeIndicators = Object.values(indicators).filter(indicator =>
            indicator.source && indicator.source.includes('INSEE')
        );

        if (inseeIndicators.length === 0) {
            section.classList.add('hidden');
            return;
        }

        section.classList.remove('hidden');
        grid.innerHTML = inseeIndicators.map(indicator =>
            this.createIndicatorCard(indicator, true)
        ).join('');
    }

    createIndicatorCard(indicator, isSupplementary = false) {
        const trendIcon = indicator.change_percent > 0 ? '📈' :
            indicator.change_percent < 0 ? '📉' : '➡️';
        const trendColor = indicator.change_percent > 0 ? 'text-green-600' :
            indicator.change_percent < 0 ? 'text-red-600' : 'text-gray-600';

        // ✅ CORRECTION : Couleurs très contrastées pour TOUS les widgets
        const categoryColors = {
            'macro': 'from-blue-600 to-blue-800',           // PIB - Bleu foncé
            'employment': 'from-red-600 to-red-800',        // Emploi - Rouge foncé
            'prices': 'from-purple-600 to-purple-800',      // IPCH - Violet foncé
            'trade': 'from-purple-600 to-purple-800',       // Commerce - Violet foncé
            'finance': 'from-green-600 to-green-800',       // Finance - Vert foncé
            'production': 'from-indigo-600 to-indigo-800',  // Production - Indigo foncé
            'inequality': 'from-pink-600 to-pink-800'       // GINI - Rose foncé
        };

        const gradient = categoryColors[indicator.category] || 'from-gray-600 to-gray-800';

        // Badge de fiabilité
        const reliabilityBadge = {
            'official': '<span class="text-xs bg-white bg-opacity-30 px-2 py-1 rounded-full">🔵 Officiel</span>',
            'scraped': '<span class="text-xs bg-white bg-opacity-30 px-2 py-1 rounded-full">🟢 Temps réel</span>',
            'fallback': '<span class="text-xs bg-white bg-opacity-30 px-2 py-1 rounded-full">🟡 Cache</span>'
        };

        // Alerte si variation importante
        let alertBadge = '';
        if (Math.abs(indicator.change_percent) > 1.0) {
            const severity = Math.abs(indicator.change_percent) > 3.0 ? 'critical' :
                Math.abs(indicator.change_percent) > 2.0 ? 'high' : 'medium';
            const alertColors = {
                'critical': 'bg-red-500',
                'high': 'bg-orange-500',
                'medium': 'bg-yellow-500'
            };
            alertBadge = `<span class="text-xs ${alertColors[severity]} text-white px-2 py-1 rounded-full ml-2">⚠️ ${severity}</span>`;
        }

        return `
            <div class="bg-gradient-to-br ${gradient} rounded-xl shadow-lg p-6 text-white border-2 border-white border-opacity-20 transform hover:scale-105 transition duration-200">
                <div class="flex items-center justify-between mb-3">
                    <h3 class="text-lg font-semibold text-white">${this.truncateName(indicator.name)}</h3>
                    ${isSupplementary ? '<i class="fas fa-star text-yellow-300"></i>' : ''}
                    ${alertBadge}
                </div>
                
                <div class="text-3xl font-bold mb-2 text-white">
                    ${indicator.value} ${indicator.unit}
                </div>
                
                <div class="flex justify-between items-center text-sm mb-2">
                    <span class="font-medium text-white opacity-90">
                        ${trendIcon} ${indicator.change_percent >= 0 ? '+' : ''}${indicator.change_percent.toFixed(2)}%
                    </span>
                    <span class="text-white opacity-90">${indicator.period}</span>
                </div>
                
                <div class="text-xs opacity-75 mb-2 text-white">
                    <span title="${indicator.description}">
                        ${indicator.source}
                    </span>
                </div>
                
                <div class="mt-2">
                    ${reliabilityBadge[indicator.reliability] || ''}
                </div>
            </div>
        `;
    }

    renderInternationalIndices() {
        const container = document.getElementById('internationalIndices');
        if (!container) return;

        // Données factices pour l'instant
        const markets = {
            'CAC40': { name: 'CAC 40', current_price: '7200.45', change_percent: 0.65, trend: 'up' },
            'DAX': { name: 'DAX', current_price: '16500.30', change_percent: 0.45, trend: 'up' },
            'S&P500': { name: 'S&P 500', current_price: '4750.20', change_percent: -0.15, trend: 'down' },
            'Nikkei': { name: 'Nikkei 225', current_price: '33500.80', change_percent: 1.25, trend: 'up' },
            'FTSE100': { name: 'FTSE 100', current_price: '7550.10', change_percent: 0.30, trend: 'up' }
        };

        if (Object.keys(markets).length === 0) {
            container.innerHTML = '<div class="col-span-5 text-center text-gray-500">Chargement indices...</div>';
            return;
        }

        container.innerHTML = Object.values(markets).map(index => {
            const trendColor = index.trend === 'up' ? 'text-green-600' : 'text-red-600';
            const trendIcon = index.trend === 'up' ? '↑' : '↓';

            return `
                <div class="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition">
                    <div class="text-sm font-medium text-gray-600 mb-1">${index.name}</div>
                    <div class="text-2xl font-bold text-gray-900 mb-1">${index.current_price}</div>
                    <div class="${trendColor} text-sm font-medium">
                        ${trendIcon} ${index.change_percent >= 0 ? '+' : ''}${index.change_percent.toFixed(2)}%
                    </div>
                </div>
            `;
        }).join('');
    }

    renderDetailedTable() {
        const tbody = document.getElementById('detailedTableBody');
        if (!tbody) return;

        const indicators = this.currentData.indicators || {};
        const allIndicators = Object.values(indicators);

        if (allIndicators.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" class="px-6 py-8 text-center text-gray-500">
                        Aucune donnée disponible
                    </td>
                </tr>
            `;
            return;
        }

        tbody.innerHTML = allIndicators.map(indicator => {
            const trendClass = indicator.change_percent > 0 ? 'text-green-600 font-medium' :
                indicator.change_percent < 0 ? 'text-red-600 font-medium' : 'text-gray-600';

            const reliabilityIcon = indicator.reliability_icon || '⚪';

            // Alerte si variation importante
            let alertCell = '';
            if (Math.abs(indicator.change_percent) > 1.0) {
                const severity = Math.abs(indicator.change_percent) > 3.0 ? 'critical' :
                    Math.abs(indicator.change_percent) > 2.0 ? 'high' : 'medium';
                alertCell = `<span class="ml-2 px-2 py-1 text-xs rounded-full ${severity === 'critical' ? 'bg-red-100 text-red-800' :
                    severity === 'high' ? 'bg-orange-100 text-orange-800' :
                        'bg-yellow-100 text-yellow-800'
                    }">⚠️ ${severity}</span>`;
            }

            return `
                <tr class="hover:bg-gray-50">
                    <td class="px-6 py-4 text-sm">
                        <span class="text-lg mr-2">${reliabilityIcon}</span>
                        <span class="font-medium text-gray-900">${indicator.name}</span>
                    </td>
                    <td class="px-6 py-4 text-sm text-gray-500">${indicator.value} ${indicator.unit}</td>
                    <td class="px-6 py-4 text-sm ${trendClass}">
                        ${indicator.change_percent >= 0 ? '+' : ''}${indicator.change_percent.toFixed(2)}%
                        ${alertCell}
                    </td>
                    <td class="px-6 py-4 text-sm text-gray-500">${indicator.period}</td>
                    <td class="px-6 py-4 text-sm text-gray-500">${indicator.source}</td>
                    <td class="px-6 py-4 text-xs">
                        <span class="px-2 py-1 rounded-full ${indicator.reliability === 'official' ? 'bg-blue-100 text-blue-800' :
                    indicator.reliability === 'scraped' ? 'bg-green-100 text-green-800' :
                        'bg-yellow-100 text-yellow-800'
                }">
                            ${indicator.reliability}
                        </span>
                    </td>
                </tr>
            `;
        }).join('');
    }

    renderAlerts(alertsData) {
        const alertsContainer = document.getElementById('alertsContainer');
        if (!alertsContainer) return;

        const alerts = alertsData?.items || [];

        if (alerts.length === 0) {
            alertsContainer.innerHTML = '<div class="text-center text-gray-500 py-4">Aucune alerte active</div>';
            return;
        }

        const alertHtml = alerts.map(alert => {
            const severityColors = {
                'critical': 'bg-red-100 border-red-500 text-red-800',
                'high': 'bg-orange-100 border-orange-500 text-orange-800',
                'medium': 'bg-yellow-100 border-yellow-500 text-yellow-800',
                'low': 'bg-blue-100 border-blue-500 text-blue-800'
            };

            return `
                <div class="border-l-4 ${severityColors[alert.severity] || 'bg-gray-100'} p-4 mb-3 rounded-r">
                    <div class="flex justify-between items-start">
                        <div>
                            <h4 class="font-semibold">${alert.indicator_name}</h4>
                            <p class="text-sm mt-1">${alert.message}</p>
                            <p class="text-xs text-gray-600 mt-1">Catégorie: ${alert.category}</p>
                        </div>
                        <span class="text-xs bg-white px-2 py-1 rounded-full">${alert.severity}</span>
                    </div>
                </div>
            `;
        }).join('');

        alertsContainer.innerHTML = `
            <div class="bg-white rounded-xl shadow-lg p-6 mb-6 border border-gray-100">
                <h3 class="text-xl font-bold text-gray-800 mb-4 flex items-center">
                    <i class="fas fa-bell mr-2 text-orange-500"></i>
                    Alertes Actives (${alerts.length})
                    <button id="alertsBtn" class="ml-auto bg-orange-500 hover:bg-orange-600 text-white px-3 py-1 rounded text-sm">
                        Voir détails
                    </button>
                </h3>
                <div class="max-h-64 overflow-y-auto">
                    ${alertHtml}
                </div>
            </div>
        `;
    }

    async loadHistoricalChart(symbol, period) {
        try {
            // Pour l'instant, générer des données factices
            const data = this.generateMockChartData();
            this.renderChart(data);

            const info = document.getElementById('cac40Info');
            if (info && data.length > 0) {
                const latest = data[data.length - 1];
                info.textContent = `Dernière valeur: ${latest.close} pts (${latest.date})`;
            }
        } catch (error) {
            console.error('❌ Erreur graphique:', error);
        }
    }

    generateMockChartData() {
        const data = [];
        const baseValue = 7200;
        const today = new Date();

        for (let i = 30; i >= 0; i--) {
            const date = new Date(today);
            date.setDate(date.getDate() - i);

            const variation = (Math.random() - 0.5) * 100;
            const close = baseValue + (i * 10) + variation;

            data.push({
                date: date.toLocaleDateString('fr-FR'),
                close: close.toFixed(2)
            });
        }

        return data;
    }

    renderChart(data) {
        const ctx = document.getElementById('mainChart');
        if (!ctx) return;

        if (this.currentChart) {
            this.currentChart.destroy();
        }

        const dates = data.map(item => item.date);
        const values = data.map(item => parseFloat(item.close));

        this.currentChart = new Chart(ctx.getContext('2d'), {
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
                    legend: { display: true, position: 'top' },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function (context) {
                                return `CAC 40: ${context.parsed.y.toFixed(2)} points`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        grid: { color: 'rgba(0, 0, 0, 0.05)' },
                        ticks: {
                            callback: function (value) {
                                return value.toLocaleString() + ' pts';
                            }
                        }
                    },
                    x: {
                        grid: { display: false },
                        ticks: {
                            maxRotation: 45,
                            minRotation: 45
                        }
                    }
                }
            }
        });
    }

    updateSystemStatus(data) {
        const statusDiv = document.getElementById('systemStatus');
        if (!statusDiv) return;

        const quality = data.summary?.data_quality || 'acceptable';
        const qualityInfo = {
            'excellent': { icon: '🟢', text: 'Excellente', color: 'green' },
            'good': { icon: '🟡', text: 'Bonne', color: 'yellow' },
            'acceptable': { icon: '🟠', text: 'Acceptable', color: 'orange' },
            'limited': { icon: '🔴', text: 'Limité', color: 'red' }
        };

        const info = qualityInfo[quality] || qualityInfo['acceptable'];

        const sourcesHtml = Object.entries(data.sources_status || {})
            .map(([source, status]) => {
                const icon = status === 'operational' ? '✅' : '❌';
                return `<span class="text-sm">${icon} ${source}</span>`;
            })
            .join(' • ');

        statusDiv.innerHTML = `
            <div class="relative">
                <div class="flex items-center justify-between flex-wrap gap-4">
                    <div class="flex items-center">
                        <span class="text-2xl mr-3">${info.icon}</span>
                        <div>
                            <h4 class="font-semibold text-${info.color}-800">
                                Qualité des données: ${info.text}
                            </h4>
                            <p class="text-sm text-${info.color}-700">${sourcesHtml}</p>
                        </div>
                    </div>
                    <div class="flex flex-wrap gap-2 items-center">
                        <button id="refreshDataBtn" class="bg-${info.color}-600 hover:bg-${info.color}-700 text-white px-4 py-2 rounded-lg text-sm transition whitespace-nowrap flex items-center shadow-md">
                            <i class="fas fa-sync-alt mr-2"></i>Actualiser
                        </button>
                        <button id="settingsBtn" class="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg text-sm transition whitespace-nowrap flex items-center shadow-md">
                            <i class="fas fa-cog mr-2"></i>Paramètres
                        </button>
                        <button id="exportBtn" class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm transition whitespace-nowrap flex items-center shadow-md">
                            <i class="fas fa-download mr-2"></i>Exporter
                        </button>
                        <a href="https://ec.europa.eu/eurostat/fr/data/database" target="_blank"
                           class="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg text-sm transition whitespace-nowrap flex items-center shadow-md">
                            <i class="fas fa-external-link-alt mr-2"></i>Eurostat DB
                        </a>
                    </div>
                </div>
            </div>
        `;
    }

    async forceRefresh() {
        try {
            this.showNotification('🔄 Rafraîchissement en cours...', 'info');
            await this.loadAllData();
            this.showNotification('✅ Données rafraîchies', 'success');
        } catch (error) {
            console.error('❌ Erreur refresh:', error);
            this.showNotification('❌ Erreur rafraîchissement', 'error');
        }
    }

    startAutoRefresh() {
        // Arrêter l'intervalle précédent s'il existe
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }

        // Utiliser l'intervalle des préférences, avec un minimum de 30 secondes
        let interval = this.displaySettings.refresh_interval || 300000;
        if (interval < 30000) {
            interval = 30000;
        }

        this.refreshInterval = setInterval(() => {
            console.log('🔄 Auto-refresh...');
            this.loadAllData();
        }, interval);
    }

    truncateName(name) {
        return name.length > 30 ? name.substring(0, 27) + '...' : name;
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

    showLoading() {
        const tbody = document.getElementById('detailedTableBody');
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" class="px-6 py-8 text-center text-gray-500">
                        <i class="fas fa-spinner fa-spin mr-2"></i>Chargement des données...
                    </td>
                </tr>
            `;
        }
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showNotification(message, type = 'info') {
        // Supprimer les notifications existantes
        const existing = document.querySelectorAll('.dashboard-notification');
        existing.forEach(el => el.remove());

        const notification = document.createElement('div');
        const colors = {
            'success': 'bg-green-500',
            'error': 'bg-red-500',
            'warning': 'bg-yellow-500',
            'info': 'bg-blue-500'
        };

        notification.className = `dashboard-notification fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${colors[type]} text-white transform transition-all duration-300`;
        notification.textContent = message;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.transform = 'translateX(400px)';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    openSettings() {
        // Rediriger vers la page de paramètres
        window.location.href = '/indicators/dashboard?settings=1';
    }

    async exportData() {
        try {
            // Créer un CSV simple
            const indicators = this.currentData.indicators || {};
            const csvContent = [
                ['Nom', 'Valeur', 'Unité', 'Variation %', 'Période', 'Source', 'Fiabilité'],
                ...Object.values(indicators).map(ind => [
                    ind.name,
                    ind.value,
                    ind.unit,
                    ind.change_percent,
                    ind.period,
                    ind.source,
                    ind.reliability
                ])
            ].map(row => row.join(',')).join('\n');

            const blob = new Blob([csvContent], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `indicators_export_${new Date().toISOString().split('T')[0]}.csv`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            this.showNotification('✅ Export CSV réussi', 'success');
        } catch (error) {
            console.error('❌ Erreur export:', error);
            this.showNotification('❌ Erreur export', 'error');
        }
    }

    showAlertsModal() {
        const modal = document.getElementById('alertsModal');
        if (!modal) {
            this.createAlertsModal();
        } else {
            modal.classList.remove('hidden');
        }
    }

    createAlertsModal() {
        const modal = document.createElement('div');
        modal.id = 'alertsModal';
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4';
        modal.innerHTML = `
            <div class="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[80vh] overflow-hidden">
                <div class="p-6 border-b border-gray-200">
                    <div class="flex justify-between items-center">
                        <h3 class="text-xl font-bold text-gray-800">
                            <i class="fas fa-bell text-orange-500 mr-2"></i>
                            Alertes et Notifications
                        </h3>
                        <button id="closeAlertsModal" class="text-gray-500 hover:text-gray-700">
                            <i class="fas fa-times text-xl"></i>
                        </button>
                    </div>
                </div>
                <div class="p-6 overflow-y-auto max-h-[60vh]">
                    <div id="alertsModalContent" class="space-y-4">
                        <div class="text-center text-gray-500 py-8">
                            <i class="fas fa-check-circle text-green-500 text-4xl mb-4"></i>
                            <p>Aucune alerte critique en ce moment</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }

    closeAlertsModal() {
        const modal = document.getElementById('alertsModal');
        if (modal) {
            modal.classList.add('hidden');
        }
    }

    applyFilters() {
        const category = document.getElementById('categoryFilter')?.value;
        const source = document.getElementById('sourceFilter')?.value;
        const reliability = document.getElementById('reliabilityFilter')?.value;

        // Filtrer les indicateurs affichés
        const filteredIndicators = Object.fromEntries(
            Object.entries(this.currentData.indicators || {}).filter(([id, indicator]) => {
                return (!category || indicator.category === category) &&
                    (!source || indicator.source.includes(source)) &&
                    (!reliability || indicator.reliability === reliability);
            })
        );

        // Mettre à jour les grilles avec les indicateurs filtrés
        const mainGrid = document.getElementById('indicatorsGrid');
        const supplementaryGrid = document.getElementById('supplementaryIndicatorsGrid');

        if (mainGrid) {
            const mainIndicators = Object.values(filteredIndicators).slice(0, 4);
            mainGrid.innerHTML = mainIndicators.map(indicator =>
                this.createIndicatorCard(indicator, false)
            ).join('');
        }

        if (supplementaryGrid) {
            const frenchIndicators = Object.values(filteredIndicators).filter(indicator =>
                indicator.source && indicator.source.includes('INSEE')
            );
            supplementaryGrid.innerHTML = frenchIndicators.map(indicator =>
                this.createIndicatorCard(indicator, true)
            ).join('');
        }
    }

    toggleSection(section) {
        const element = document.getElementById(`${section}Section`);
        if (element) {
            element.classList.toggle('hidden');
        }
    }
}

// Initialisation automatique
document.addEventListener('DOMContentLoaded', () => {
    window.enhancedDashboard = new EnhancedIndicatorsDashboard();
    console.log('✅ Enhanced Dashboard chargé');
});

// Fermer modals en cliquant en dehors
document.addEventListener('click', (e) => {
    const alertsModal = document.getElementById('alertsModal');
    if (alertsModal && !alertsModal.classList.contains('hidden') &&
        e.target === alertsModal) {
        window.enhancedDashboard.closeAlertsModal();
    }
});