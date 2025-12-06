// static/js/app.js - Fonctions globales et utilitaires CORRIGÉ

// Configuration
const CONFIG = {
    API_BASE_URL: '',
    DEBOUNCE_DELAY: 300
};

// Utilitaires de formatage
class Formatters {
    static formatDate(dateString) {
        if (!dateString) return 'Date inconnue';
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('fr-FR', {
                day: 'numeric',
                month: 'short',
                year: 'numeric'
            });
        } catch (e) {
            return 'Date invalide';
        }
    }

    static truncateText(text, maxLength = 200) {
        if (!text) return 'Aucun contenu';
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }

    static getSentimentColor(sentiment) {
        switch (sentiment) {
            case 'positive': return 'border-green-500';
            case 'negative': return 'border-red-500';
            default: return 'border-gray-500';
        }
    }

    static getSentimentBadge(sentiment) {
        switch (sentiment) {
            case 'positive': return 'bg-green-100 text-green-800';
            case 'negative': return 'bg-red-100 text-red-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    }

    static getSentimentIcon(sentiment) {
        switch (sentiment) {
            case 'positive': return 'fa-smile';
            case 'negative': return 'fa-frown';
            default: return 'fa-meh';
        }
    }
}

// Gestionnaire d'API COMPLET
class ApiClient {
    static async get(url) {
        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('API GET Error:', error);
            throw error;
        }
    }

    static async post(url, data) {
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('API POST Error:', error);
            throw error;
        }
    }

    static async put(url, data) {
        try {
            const response = await fetch(url, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('API PUT Error:', error);
            throw error;
        }
    }

    static async delete(url) {
        try {
            const response = await fetch(url, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('API DELETE Error:', error);
            throw error;
        }
    }
}

// Gestionnaire de modales
class ModalManager {
    static showModal(modalId) {
        const modal = document.getElementById(modalId);
        const overlay = document.getElementById('overlay');

        if (modal) {
            modal.classList.remove('hidden');
            modal.style.display = 'block';
        }
        if (overlay) {
            overlay.classList.remove('hidden');
            overlay.style.display = 'block';
        }
    }

    static hideModal(modalId) {
        const modal = document.getElementById(modalId);
        const overlay = document.getElementById('overlay');

        if (modal) {
            modal.classList.add('hidden');
            modal.style.display = 'none';
        }
        if (overlay) {
            overlay.classList.add('hidden');
            overlay.style.display = 'none';
        }
    }

    static setupModalClose(modalId, closeButtonId) {
        const modal = document.getElementById(modalId);
        const closeBtn = document.getElementById(closeButtonId);

        if (modal && closeBtn) {
            closeBtn.addEventListener('click', () => this.hideModal(modalId));
            modal.addEventListener('click', (e) => {
                if (e.target === modal) this.hideModal(modalId);
            });
        }
    }
}

// Gestionnaire de navigation
class NavigationManager {
    static init() {
        this.setupMobileMenu();
        this.setupCurrentTime();
        this.setupNavigationLinks();
    }

    static setupMobileMenu() {
        const menuToggle = document.getElementById('menuToggle');
        const overlay = document.getElementById('overlay');
        const sidebar = document.querySelector('.sidebar');

        if (menuToggle && overlay && sidebar) {
            menuToggle.addEventListener('click', () => {
                sidebar.classList.toggle('active');
                overlay.classList.toggle('hidden');
            });

            overlay.addEventListener('click', () => {
                sidebar.classList.remove('active');
                overlay.classList.add('hidden');
            });
        }
    }

    static setupCurrentTime() {
        const updateTime = () => {
            const now = new Date();
            const currentTimeElement = document.getElementById('currentTime');
            if (currentTimeElement) {
                currentTimeElement.textContent = now.toLocaleTimeString('fr-FR', {
                    hour: '2-digit',
                    minute: '2-digit'
                });
            }
        };

        updateTime();
        setInterval(updateTime, 1000);
    }

    static setupNavigationLinks() {
        // Navigation vers la gestion des thèmes
        const navThemes = document.querySelector('.nav-themes');
        if (navThemes) {
            navThemes.addEventListener('click', function (e) {
                e.preventDefault();
                if (typeof ThemeManager !== 'undefined') {
                    ThemeManager.loadThemes();
                    ModalManager.showModal('themeManagerModal');
                } else {
                    console.error('ThemeManager non disponible');
                }
            });
        }

        // Navigation vers les articles
        const navArticles = document.querySelector('.nav-articles');
        if (navArticles) {
            navArticles.addEventListener('click', function (e) {
                e.preventDefault();
                if (typeof ArticleManager !== 'undefined') {
                    ArticleManager.showAllArticles();
                } else {
                    console.error('ArticleManager non disponible');
                }
            });
        }

        // Navigation vers les paramètres
        const navSettings = document.querySelector('.nav-settings');
        if (navSettings) {
            navSettings.addEventListener('click', function (e) {
                e.preventDefault();
                if (typeof SettingsManager !== 'undefined') {
                    SettingsManager.showSettings();
                } else {
                    console.error('SettingsManager non disponible');
                }
            });
        }
    }
}

//spectrum-sdr : Interface pour le monitoring automatique du spectre
class SpectrumMonitorUI {
    static activeMonitors = new Map();
    static spectrumChart = null;
    static updateInterval = null;

    static async initialize() {
        console.log('📡 Initialisation Spectrum Monitor UI...');

        try {
            await this.checkAvailableSources();
            await this.loadMonitoringStatus();
            this.setupEventListeners();
            this.startStatusUpdates();

            console.log('✅ Spectrum Monitor UI initialisé');
        } catch (error) {
            console.error('❌ Erreur initialisation:', error);
        }
    }

    static async checkAvailableSources() {
        try {
            const response = await fetch('/api/spectrum/sources');
            const data = await response.json();

            if (data.success) {
                this.displayAvailableSources(data.sources, data.recommendations);
            }
        } catch (error) {
            console.error('Erreur vérification sources:', error);
        }
    }

    static displayAvailableSources(sources, recommendations) {
        const container = document.getElementById('spectrum-sources-info');
        if (!container) return;

        const getSourceBadge = (name, available) => {
            const color = available ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-500';
            const icon = available ? '✅' : '❌';
            return `<span class="${color} px-3 py-1 rounded-full text-sm">${icon} ${name.toUpperCase()}</span>`;
        };

        container.innerHTML = `
            <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h4 class="font-semibold mb-2 text-blue-800">📊 Sources de données spectrales</h4>
                <div class="space-y-2">
                    <div class="flex items-center justify-between">
                        <span class="text-sm">WebSDR (Université Twente)</span>
                        ${getSourceBadge('websdr', sources.websdr)}
                    </div>
                    <div class="flex items-center justify-between">
                        <span class="text-sm">RTL-SDR Local</span>
                        ${getSourceBadge('rtlsdr', sources.rtlsdr)}
                    </div>
                    <div class="mt-3 text-xs text-blue-700">
                        <p><strong>Source par défaut :</strong> ${sources.default.toUpperCase()}</p>
                        <p class="mt-1">${recommendations[sources.default]}</p>
                    </div>
                </div>
            </div>
        `;
    }

    static async testSpectrumAnalysis(frequencyKhz) {
        try {
            this.showNotification('🧪 Test d\'analyse en cours...', 'info');

            const response = await fetch(`/api/spectrum/test?frequency_khz=${frequencyKhz}`);
            const data = await response.json();

            if (data.success) {
                this.showNotification(`✅ ${data.peaks_detected} pics détectés (test)`, 'success');
                this.displayTestResults(data);
            } else {
                throw new Error(data.error || 'Erreur test');
            }
        } catch (error) {
            console.error('Erreur test:', error);
            this.showNotification('❌ Erreur lors du test : ' + error.message, 'error');
        }
    }

    static displayTestResults(data) {
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4';
        modal.innerHTML = `
            <div class="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-screen overflow-hidden flex flex-col">
                <div class="flex justify-between items-center p-4 border-b">
                    <h3 class="text-lg font-semibold">🧪 Résultats du test - ${data.frequency_khz} kHz</h3>
                    <button onclick="this.closest('.fixed').remove()" class="text-gray-500 hover:text-gray-700">
                        <i class="fas fa-times text-xl"></i>
                    </button>
                </div>
                
                <div class="p-6 overflow-y-auto flex-1">
                    <!-- Statistiques -->
                    <div class="grid grid-cols-2 gap-4 mb-6">
                        <div class="text-center p-4 bg-blue-50 rounded-lg">
                            <div class="text-3xl font-bold text-blue-600">${data.peaks_detected}</div>
                            <div class="text-sm text-blue-800">Pics détectés</div>
                        </div>
                        <div class="text-center p-4 bg-green-50 rounded-lg">
                            <div class="text-3xl font-bold text-green-600">${data.frequency_khz}</div>
                            <div class="text-sm text-green-800">Fréquence (kHz)</div>
                        </div>
                    </div>

                    <!-- Graphique du spectre -->
                    <div class="mb-6">
                        <h4 class="font-semibold mb-2">📈 Spectre de puissance</h4>
                        <canvas id="testSpectrumChart" height="200"></canvas>
                    </div>

                    <!-- Liste des pics -->
                    <div>
                        <h4 class="font-semibold mb-2">🔍 Pics détectés (Top 10)</h4>
                        <div class="space-y-2 max-h-64 overflow-y-auto">
                            ${data.peaks.slice(0, 10).map((peak, i) => `
                                <div class="flex items-center justify-between p-3 bg-gray-50 rounded">
                                    <div>
                                        <span class="font-mono text-sm">${peak.frequency_khz.toFixed(3)} kHz</span>
                                        <span class="text-xs text-gray-500 ml-2">BW: ${peak.bandwidth_khz.toFixed(2)} kHz</span>
                                    </div>
                                    <div class="text-right">
                                        <div class="font-medium ${peak.power_db > -70 ? 'text-red-600' : 'text-blue-600'}">
                                            ${peak.power_db.toFixed(1)} dB
                                        </div>
                                        <div class="text-xs text-gray-500">
                                            ${peak.power_db > -70 ? 'Fort' : peak.power_db > -85 ? 'Moyen' : 'Faible'}
                                        </div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>

                    <div class="mt-4 bg-yellow-50 border border-yellow-200 rounded p-3 text-sm text-yellow-800">
                        ⚠️ Données simulées pour test - Les vraies données viendront de WebSDR ou RTL-SDR
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Créer le graphique
        setTimeout(() => {
            const canvas = document.getElementById('testSpectrumChart');
            if (canvas && data.spectrum_sample) {
                new Chart(canvas, {
                    type: 'line',
                    data: {
                        labels: data.spectrum_sample.frequencies.map(f => f.toFixed(1)),
                        datasets: [{
                            label: 'Puissance (dB)',
                            data: data.spectrum_sample.powers,
                            borderColor: '#3B82F6',
                            backgroundColor: 'rgba(59, 130, 246, 0.1)',
                            tension: 0.1,
                            pointRadius: 0,
                            borderWidth: 2
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            legend: { display: false }
                        },
                        scales: {
                            x: {
                                title: { display: true, text: 'Fréquence (kHz)' }
                            },
                            y: {
                                title: { display: true, text: 'Puissance (dB)' }
                            }
                        }
                    }
                });
            }
        }, 100);
    }

    static async startAutomatedMonitoring(frequencyId, frequencyKhz, name) {
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4';
        modal.innerHTML = `
            <div class="bg-white rounded-lg shadow-xl w-full max-w-md">
                <div class="flex justify-between items-center p-4 border-b">
                    <h3 class="text-lg font-semibold">🤖 Monitoring automatique</h3>
                    <button onclick="this.closest('.fixed').remove()" class="text-gray-500 hover:text-gray-700">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                
                <form id="start-monitoring-form" class="p-4 space-y-4">
                    <div class="bg-blue-50 border border-blue-200 rounded p-3">
                        <p class="text-sm"><strong>Fréquence :</strong> ${name}</p>
                        <p class="text-sm"><strong>MHz :</strong> ${(frequencyKhz / 1000).toFixed(3)}</p>
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium mb-1">Durée (minutes)</label>
                        <input type="number" name="duration_minutes" min="5" max="1440" value="60"
                               class="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500">
                        <p class="text-xs text-gray-500 mt-1">1 heure = 60 min, 24h = 1440 min</p>
                    </div>
                    
                    <div>
                        <label class="block text-sm font-medium mb-1">Intervalle de scan (secondes)</label>
                        <input type="number" name="scan_interval" min="60" max="3600" value="300"
                               class="w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-blue-500">
                        <p class="text-xs text-gray-500 mt-1">300s = 5 minutes entre chaque scan</p>
                    </div>

                    <div class="bg-yellow-50 border border-yellow-200 rounded p-3 text-sm">
                        <p class="font-medium text-yellow-800 mb-1">ℹ️ Information</p>
                        <p class="text-yellow-700">
                            Le système va automatiquement scanner le spectre et compter les pics d'émission.
                            Le monitoring se fait en arrière-plan.
                        </p>
                    </div>
                    
                    <div class="flex justify-end space-x-2 pt-2">
                        <button type="button" onclick="this.closest('.fixed').remove()"
                                class="px-4 py-2 border rounded-md hover:bg-gray-50">
                            Annuler
                        </button>
                        <button type="submit"
                                class="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700">
                            <i class="fas fa-play mr-2"></i>Démarrer
                        </button>
                    </div>
                </form>
            </div>
        `;

        document.body.appendChild(modal);

        modal.querySelector('#start-monitoring-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);

            try {
                const response = await fetch('/api/spectrum/monitor/start', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        frequency_id: frequencyId,
                        frequency_khz: frequencyKhz,
                        duration_minutes: parseInt(formData.get('duration_minutes')),
                        scan_interval_seconds: parseInt(formData.get('scan_interval'))
                    })
                });

                const result = await response.json();

                if (result.success || response.status === 202) {
                    this.showNotification('✅ Monitoring démarré en arrière-plan', 'success');
                    modal.remove();
                    await this.loadMonitoringStatus();
                } else {
                    throw new Error(result.error || 'Erreur serveur');
                }
            } catch (error) {
                console.error('Erreur démarrage:', error);
                alert('Erreur : ' + error.message);
            }
        });
    }

    static async loadMonitoringStatus() {
        try {
            const response = await fetch('/api/spectrum/monitor/status');
            const data = await response.json();

            if (data.success) {
                this.displayMonitoringStatus(data);
            }
        } catch (error) {
            console.error('Erreur statut monitoring:', error);
        }
    }

    static displayMonitoringStatus(data) {
        const container = document.getElementById('active-monitors-status');
        if (!container) return;

        if (data.monitors.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <i class="fas fa-info-circle text-3xl mb-3"></i>
                    <p>Aucun monitoring automatique en cours</p>
                    <p class="text-sm mt-2">Démarrez un monitoring sur une fréquence surveillée</p>
                </div>
            `;
            return;
        }

        container.innerHTML = `
            <div class="space-y-3">
                <h4 class="font-semibold text-gray-800 flex items-center">
                    <i class="fas fa-broadcast-tower text-green-600 mr-2"></i>
                    Monitorings actifs (${data.active_monitors})
                </h4>
                ${data.monitors.map(monitor => `
                    <div class="bg-${monitor.status === 'running' ? 'green' : 'gray'}-50 border border-${monitor.status === 'running' ? 'green' : 'gray'}-200 rounded-lg p-4">
                        <div class="flex items-center justify-between mb-2">
                            <div>
                                <span class="font-medium">${(monitor.frequency_khz / 1000).toFixed(3)} MHz</span>
                                <span class="ml-2 px-2 py-1 text-xs rounded-full ${monitor.status === 'running'
                ? 'bg-green-200 text-green-800'
                : 'bg-gray-200 text-gray-800'
            }">
                                    ${monitor.status === 'running' ? '🟢 En cours' : '⚪ Terminé'}
                                </span>
                            </div>
                            ${monitor.status === 'running' ? `
                                <button onclick="SpectrumMonitorUI.stopMonitoring(${monitor.frequency_id})"
                                        class="text-red-600 hover:text-red-800 text-sm">
                                    <i class="fas fa-stop-circle mr-1"></i>Arrêter
                                </button>
                            ` : ''}
                        </div>
                        <div class="text-xs text-gray-600 space-y-1">
                            <p>Démarré : ${new Date(monitor.started_at).toLocaleString('fr-FR')}</p>
                            <p>Durée : ${monitor.duration_minutes} minutes</p>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    static async stopMonitoring(frequencyId) {
        if (!confirm('Arrêter ce monitoring ?')) return;

        try {
            const response = await fetch(`/api/spectrum/monitor/stop/${frequencyId}`, {
                method: 'POST'
            });

            const result = await response.json();

            if (result.success) {
                this.showNotification('⏹️ Monitoring arrêté', 'success');
                await this.loadMonitoringStatus();
            } else {
                throw new Error(result.error || 'Erreur serveur');
            }
        } catch (error) {
            console.error('Erreur arrêt:', error);
            this.showNotification('Erreur : ' + error.message, 'error');
        }
    }

    static setupEventListeners() {
        // Actualiser le statut régulièrement
        this.updateInterval = setInterval(() => {
            this.loadMonitoringStatus();
        }, 30000);
    }

    static startStatusUpdates() {
        // Déjà géré dans setupEventListeners
    }

    static showNotification(message, type = 'info') {
        const notification = document.createElement('div');

        const colors = {
            success: 'bg-green-500',
            error: 'bg-red-500',
            info: 'bg-blue-500',
            warning: 'bg-yellow-500'
        };

        const icons = {
            success: 'check-circle',
            error: 'exclamation-triangle',
            info: 'info-circle',
            warning: 'exclamation-triangle'
        };

        notification.className = `fixed top-4 right-4 ${colors[type]} text-white p-4 rounded-lg shadow-lg z-50 max-w-md`;
        notification.innerHTML = `
            <div class="flex items-center">
                <i class="fas fa-${icons[type]} mr-3 text-xl"></i>
                <span>${message}</span>
            </div>
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transition = 'opacity 0.5s';
            setTimeout(() => notification.remove(), 500);
        }, 5000);
    }

    static destroy() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
        if (this.spectrumChart) {
            this.spectrumChart.destroy();
        }
    }
}

// Initialisation automatique
if (window.location.pathname.includes('/weak-indicators')) {
    document.addEventListener('DOMContentLoaded', () => {
        SpectrumMonitorUI.initialize();
    });

    window.addEventListener('beforeunload', () => {
        SpectrumMonitorUI.destroy();
    });
}

// Exposer globalement
window.SpectrumMonitorUI = SpectrumMonitorUI;

console.log('✅ Spectrum Monitor UI chargé');

// Initialisation globale
document.addEventListener('DOMContentLoaded', function () {
    NavigationManager.init();
    ModalManager.setupModalClose('themeManagerModal', 'closeThemeManager');

    console.log('✅ App initialisée avec ApiClient.put()');
});

// Exposer les classes globalement
window.Formatters = Formatters;
window.ApiClient = ApiClient;
window.ModalManager = ModalManager;
window.NavigationManager = NavigationManager;