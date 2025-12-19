// static/js/sdr_dashboard.js
/**
 * Gestionnaire du Dashboard SDR temps réel
 *
 * Fonctionnalités :
 * - Affichage métriques globales et par zone
 * - Graphiques Charts.js (timeline, camembert, lignes, barres)
 * - Alertes récentes
 * - Auto-refresh configurable
 *
 * Dépendances :
 * - Chart.js v4.4.0+
 * - Bootstrap 5
 *
 * Version: 1.0.0
 */

class SDRDashboard {
    constructor(config = {}) {
        this.config = {
            apiBaseUrl: config.apiBaseUrl || '/api/sdr/dashboard',
            autoRefreshInterval: config.autoRefreshInterval || 30000,  // 30 secondes
            ...config
        };

        // État
        this.isLoading = false;
        this.autoRefresh = false;
        this.refreshTimer = null;

        // Données
        this.dashboardData = null;
        this.charts = {};

        console.log('📊 SDRDashboard initialisé');
    }

    /**
     * Initialise le dashboard
     */
    async init() {
        try {
            console.log('📊 Initialisation du dashboard...');

            // Afficher le loader
            this.showLoader();

            // Charger les données initiales
            await this.loadDashboardData();

            // Créer les graphiques
            this.createCharts();

            // Afficher les métriques
            this.updateMetrics();
            this.updateZones();
            this.updateAlerts();

            // Masquer le loader
            this.hideLoader();

            console.log('✅ Dashboard initialisé');
            return true;

        } catch (error) {
            console.error('❌ Erreur initialisation dashboard:', error);
            this.hideLoader();
            this.showError('Impossible de charger le dashboard');
            return false;
        }
    }

    /**
     * Charge les données du dashboard
     */
    async loadDashboardData() {
        if (this.isLoading) {
            console.warn('⚠️ Chargement déjà en cours');
            return;
        }

        this.isLoading = true;

        try {
            // Charger le résumé complet
            const summaryResponse = await fetch(`${this.config.apiBaseUrl}/summary`);
            if (!summaryResponse.ok) {
                throw new Error(`HTTP ${summaryResponse.status}`);
            }
            const summaryData = await summaryResponse.json();

            if (!summaryData.success) {
                throw new Error(summaryData.error || 'Erreur récupération données');
            }

            this.dashboardData = summaryData.data;

            // Charger les données supplémentaires pour les graphiques
            await this.loadChartData();

            // Mettre à jour le timestamp
            this.updateTimestamp();

            console.log('✅ Données dashboard chargées');
            return this.dashboardData;

        } catch (error) {
            console.error('❌ Erreur chargement données:', error);
            throw error;

        } finally {
            this.isLoading = false;
        }
    }

    /**
     * Charge les données pour les graphiques
     */
    async loadChartData() {
        try {
            // Timeline
            const timelineResponse = await fetch(`${this.config.apiBaseUrl}/timeline?hours=24`);
            if (timelineResponse.ok) {
                const timelineData = await timelineResponse.json();
                this.dashboardData.timelineData = timelineData.timeline || [];
            }

            // Distribution zones
            const zoneDistResponse = await fetch(`${this.config.apiBaseUrl}/charts/zone-distribution`);
            if (zoneDistResponse.ok) {
                const zoneDistData = await zoneDistResponse.json();
                this.dashboardData.zoneDistribution = zoneDistData.data || {};
            }

            // Tendance disponibilité
            const availTrendResponse = await fetch(`${this.config.apiBaseUrl}/charts/availability-trend?hours=24`);
            if (availTrendResponse.ok) {
                const availTrendData = await availTrendResponse.json();
                this.dashboardData.availabilityTrend = availTrendData.data || [];
            }

            // Timeline anomalies
            const anomalyTimelineResponse = await fetch(`${this.config.apiBaseUrl}/charts/anomaly-timeline?hours=24`);
            if (anomalyTimelineResponse.ok) {
                const anomalyTimelineData = await anomalyTimelineResponse.json();
                this.dashboardData.anomalyTimeline = anomalyTimelineData.data || [];
            }

        } catch (error) {
            console.error('❌ Erreur chargement données graphiques:', error);
        }
    }

    /**
     * Met à jour les métriques globales
     */
    updateMetrics() {
        if (!this.dashboardData || !this.dashboardData.global) {
            console.warn('⚠️ Pas de données globales');
            return;
        }

        const global = this.dashboardData.global;

        document.getElementById('totalActive').textContent = global.total_active || 0;
        document.getElementById('totalInactive').textContent = global.total_inactive || 0;
        document.getElementById('totalStations').textContent = global.total_stations || 0;
        document.getElementById('availabilityRate').textContent = `${global.availability_rate || 0}%`;

        // Nombre d'anomalies récentes
        const anomalyCount = this.dashboardData.recent_anomalies?.length || 0;
        document.getElementById('activeAnomalies').textContent = anomalyCount;
    }

    /**
     * Met à jour les zones géopolitiques
     */
    updateZones() {
        if (!this.dashboardData || !this.dashboardData.zones) {
            console.warn('⚠️ Pas de données zones');
            return;
        }

        const container = document.getElementById('zoneMetrics');
        container.innerHTML = '';

        for (const [zoneId, zone] of Object.entries(this.dashboardData.zones)) {
            const zoneCard = `
                <div class="col-md-6 col-lg-3">
                    <div class="zone-card">
                        <div class="d-flex justify-content-between align-items-center mb-2">
                            <h6 class="mb-0">${zone.name}</h6>
                            <span class="zone-status status-${zone.status}">${zone.status}</span>
                        </div>
                        <div class="row">
                            <div class="col-6">
                                <small class="text-muted">Actives</small>
                                <div class="h4 text-success mb-0">${zone.active || 0}</div>
                            </div>
                            <div class="col-6">
                                <small class="text-muted">Santé</small>
                                <div class="h4 mb-0">${zone.health || 0}%</div>
                            </div>
                        </div>
                        ${zone.critical_anomalies > 0 ? `
                            <div class="alert alert-danger mt-2 mb-0 py-1 px-2 small">
                                <i class="fas fa-exclamation-triangle"></i> ${zone.critical_anomalies} anomalie(s) critique(s)
                            </div>
                        ` : ''}
                    </div>
                </div>
            `;

            container.innerHTML += zoneCard;
        }
    }

    /**
     * Met à jour les alertes récentes
     */
    updateAlerts() {
        if (!this.dashboardData || !this.dashboardData.recent_anomalies) {
            console.warn('⚠️ Pas d\'anomalies');
            return;
        }

        const container = document.getElementById('recentAlerts');
        container.innerHTML = '';

        const anomalies = this.dashboardData.recent_anomalies;

        if (anomalies.length === 0) {
            container.innerHTML = `
                <div class="alert alert-info">
                    <i class="fas fa-info-circle"></i> Aucune anomalie détectée dans les dernières 24h
                </div>
            `;
            return;
        }

        anomalies.forEach(anomaly => {
            const alertItem = `
                <div class="alert-item alert-${anomaly.level}">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <strong>${anomaly.zone_id}</strong> - ${anomaly.metric_name}
                            <div class="text-muted small mt-1">${anomaly.description || 'Anomalie détectée'}</div>
                        </div>
                        <div class="text-end">
                            <span class="badge bg-${this.getLevelColor(anomaly.level)}">${anomaly.level}</span>
                            <div class="timestamp small mt-1">${this.formatTimestamp(anomaly.timestamp)}</div>
                        </div>
                    </div>
                </div>
            `;

            container.innerHTML += alertItem;
        });
    }

    /**
     * Crée tous les graphiques
     */
    createCharts() {
        this.createTimelineChart();
        this.createZoneDistributionChart();
        this.createAvailabilityTrendChart();
        this.createAnomalyTimelineChart();
    }

    /**
     * Crée le graphique de timeline
     */
    createTimelineChart() {
        const ctx = document.getElementById('timelineChart');
        if (!ctx) return;

        const timeline = this.dashboardData.timelineData || [];

        // Préparer les données
        const labels = timeline.map(d => this.formatTimestamp(d.timestamp, true));
        const data = timeline.map(d => d.active_stations || 0);

        // Détruire le graphique existant
        if (this.charts.timeline) {
            this.charts.timeline.destroy();
        }

        // Créer le graphique
        this.charts.timeline = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Stations Actives',
                    data: data,
                    borderColor: '#3d5afe',
                    backgroundColor: 'rgba(61, 90, 254, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: { color: '#e0e0e0' }
                    }
                },
                scales: {
                    x: {
                        ticks: { color: '#e0e0e0' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' }
                    },
                    y: {
                        ticks: { color: '#e0e0e0' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' }
                    }
                }
            }
        });
    }

    /**
     * Crée le graphique de distribution par zone
     */
    createZoneDistributionChart() {
        const ctx = document.getElementById('zoneDistributionChart');
        if (!ctx) return;

        const distribution = this.dashboardData.zoneDistribution || {};

        // Détruire le graphique existant
        if (this.charts.zoneDistribution) {
            this.charts.zoneDistribution.destroy();
        }

        // Créer le graphique
        this.charts.zoneDistribution = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: distribution.labels || [],
                datasets: [{
                    data: distribution.values || [],
                    backgroundColor: [
                        '#3d5afe',
                        '#00bcd4',
                        '#4caf50',
                        '#ff9800'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { color: '#e0e0e0' }
                    }
                }
            }
        });
    }

    /**
     * Crée le graphique de tendance de disponibilité
     */
    createAvailabilityTrendChart() {
        const ctx = document.getElementById('availabilityTrendChart');
        if (!ctx) return;

        const trend = this.dashboardData.availabilityTrend || [];

        const labels = trend.map(d => this.formatTimestamp(d.timestamp, true));
        const data = trend.map(d => d.availability_rate || 0);

        // Détruire le graphique existant
        if (this.charts.availabilityTrend) {
            this.charts.availabilityTrend.destroy();
        }

        // Créer le graphique
        this.charts.availabilityTrend = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Disponibilité (%)',
                    data: data,
                    borderColor: '#4caf50',
                    backgroundColor: 'rgba(76, 175, 80, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: { color: '#e0e0e0' }
                    }
                },
                scales: {
                    x: {
                        ticks: { color: '#e0e0e0' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' }
                    },
                    y: {
                        min: 0,
                        max: 100,
                        ticks: { color: '#e0e0e0' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' }
                    }
                }
            }
        });
    }

    /**
     * Crée le graphique de timeline des anomalies
     */
    createAnomalyTimelineChart() {
        const ctx = document.getElementById('anomalyTimelineChart');
        if (!ctx) return;

        const timeline = this.dashboardData.anomalyTimeline || [];

        const labels = timeline.map(d => this.formatTimestamp(d.timestamp, true));
        const totalData = timeline.map(d => d.total_count || 0);
        const criticalData = timeline.map(d => d.critical_count || 0);

        // Détruire le graphique existant
        if (this.charts.anomalyTimeline) {
            this.charts.anomalyTimeline.destroy();
        }

        // Créer le graphique
        this.charts.anomalyTimeline = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Total Anomalies',
                        data: totalData,
                        backgroundColor: 'rgba(255, 152, 0, 0.6)',
                        borderColor: '#ff9800',
                        borderWidth: 1
                    },
                    {
                        label: 'Critiques',
                        data: criticalData,
                        backgroundColor: 'rgba(255, 0, 0, 0.6)',
                        borderColor: '#ff0000',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: { color: '#e0e0e0' }
                    }
                },
                scales: {
                    x: {
                        ticks: { color: '#e0e0e0' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' }
                    },
                    y: {
                        ticks: { color: '#e0e0e0', precision: 0 },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' }
                    }
                }
            }
        });
    }

    /**
     * Met à jour tous les graphiques
     */
    updateCharts() {
        this.createCharts();  // Recréer les graphiques avec nouvelles données
    }

    /**
     * Rafraîchit toutes les données
     */
    async refresh() {
        console.log('🔄 Rafraîchissement dashboard...');

        try {
            this.showRefreshIndicator();

            await this.loadDashboardData();
            this.updateMetrics();
            this.updateZones();
            this.updateAlerts();
            this.updateCharts();

            console.log('✅ Dashboard rafraîchi');
            return true;

        } catch (error) {
            console.error('❌ Erreur rafraîchissement:', error);
            this.showError('Erreur lors du rafraîchissement');
            return false;

        } finally {
            this.hideRefreshIndicator();
        }
    }

    /**
     * Toggle auto-refresh
     */
    toggleAutoRefresh() {
        if (this.autoRefresh) {
            this.stopAutoRefresh();
        } else {
            this.startAutoRefresh();
        }
    }

    /**
     * Démarre l'auto-refresh
     */
    startAutoRefresh() {
        if (this.autoRefresh) {
            console.warn('⚠️ Auto-refresh déjà actif');
            return;
        }

        this.autoRefresh = true;
        this.refreshTimer = setInterval(() => {
            this.refresh();
        }, this.config.autoRefreshInterval);

        // Mettre à jour le bouton
        const btn = document.getElementById('autoRefreshBtn');
        if (btn) {
            btn.innerHTML = '<i class="fas fa-clock"></i> Auto-refresh: ON';
            btn.classList.remove('btn-outline-light');
            btn.classList.add('btn-success');
        }

        console.log(`✅ Auto-refresh activé (${this.config.autoRefreshInterval / 1000}s)`);
    }

    /**
     * Arrête l'auto-refresh
     */
    stopAutoRefresh() {
        if (!this.autoRefresh) return;

        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
            this.refreshTimer = null;
        }

        this.autoRefresh = false;

        // Mettre à jour le bouton
        const btn = document.getElementById('autoRefreshBtn');
        if (btn) {
            btn.innerHTML = '<i class="fas fa-clock"></i> Auto-refresh: OFF';
            btn.classList.remove('btn-success');
            btn.classList.add('btn-outline-light');
        }

        console.log('ℹ️ Auto-refresh désactivé');
    }

    /**
     * Affiche le loader
     */
    showLoader() {
        const loader = document.getElementById('loadingSpinner');
        if (loader) {
            loader.style.display = 'block';
        }

        // Masquer le contenu
        const content = document.getElementById('globalMetrics');
        if (content) {
            content.style.opacity = '0.3';
        }
    }

    /**
     * Masque le loader
     */
    hideLoader() {
        const loader = document.getElementById('loadingSpinner');
        if (loader) {
            loader.style.display = 'none';
        }

        // Afficher le contenu
        const content = document.getElementById('globalMetrics');
        if (content) {
            content.style.opacity = '1';
        }
    }

    /**
     * Affiche l'indicateur de refresh
     */
    showRefreshIndicator() {
        const indicator = document.getElementById('refreshIndicator');
        if (indicator) {
            indicator.style.display = 'block';
        }
    }

    /**
     * Masque l'indicateur de refresh
     */
    hideRefreshIndicator() {
        const indicator = document.getElementById('refreshIndicator');
        if (indicator) {
            setTimeout(() => {
                indicator.style.display = 'none';
            }, 1000);
        }
    }

    /**
     * Affiche une erreur
     */
    showError(message) {
        console.error(`❌ ${message}`);
        alert(`Erreur: ${message}`);
    }

    /**
     * Met à jour le timestamp
     */
    updateTimestamp() {
        const elem = document.getElementById('lastUpdate');
        if (elem && this.dashboardData) {
            const timestamp = this.dashboardData.last_update || new Date().toISOString();
            elem.textContent = `Dernière mise à jour: ${this.formatTimestamp(timestamp)}`;
        }
    }

    /**
     * Formate un timestamp
     */
    formatTimestamp(timestamp, short = false) {
        if (!timestamp) return '--';

        const date = new Date(timestamp);

        if (short) {
            return date.toLocaleTimeString('fr-FR', {
                hour: '2-digit',
                minute: '2-digit'
            });
        }

        return date.toLocaleString('fr-FR', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    }

    /**
     * Retourne la couleur Bootstrap pour un niveau
     */
    getLevelColor(level) {
        const colors = {
            'CRITICAL': 'danger',
            'HIGH_RISK': 'warning',
            'WARNING': 'warning',
            'INFO': 'info'
        };

        return colors[level] || 'secondary';
    }

    /**
     * Nettoyage
     */
    destroy() {
        this.stopAutoRefresh();

        // Détruire les graphiques
        for (const chart of Object.values(this.charts)) {
            if (chart) {
                chart.destroy();
            }
        }

        this.charts = {};
        this.dashboardData = null;

        console.log('🗑️ SDRDashboard détruit');
    }
}

// Export pour utilisation globale
window.SDRDashboard = SDRDashboard;
