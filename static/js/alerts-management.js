// static/js/alerts-management.js - CORRIGÉ
class AlertsManager {
    static async initialize() {
        console.log('🔔 Initialisation AlertsManager...');

        try {
            await this.loadAlerts();
            await this.loadTriggeredAlerts();
            console.log('✅ AlertsManager initialisé');
        } catch (error) {
            console.error('❌ Erreur initialisation alerts:', error);
        }
    }

    static async loadAlerts() {
        try {
            // ✅ CORRECTION : URL avec préfixe /alerts
            const response = await fetch('/alerts/api/alerts');
            const data = await response.json();

            if (data.success) {
                this.displayAlerts(data.alerts);
            }
        } catch (error) {
            console.error('Erreur chargement alerts:', error);
        }
    }

    static async loadTriggeredAlerts() {
        try {
            // ✅ CORRECTION : URL avec préfixe /alerts
            const response = await fetch('/alerts/api/alerts/triggered?hours=24');
            const data = await response.json();

            if (data.success) {
                this.displayTriggeredAlerts(data.alerts);
            }
        } catch (error) {
            console.error('Erreur chargement alerts déclenchées:', error);
        }
    }

    static displayAlerts(alerts) {
        const container = document.getElementById('alerts-container');
        if (!container) return;

        if (!alerts || alerts.length === 0) {
            container.innerHTML = `
                <div class="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
                    <i class="fas fa-check-circle text-green-600 text-xl mb-2"></i>
                    <p class="text-green-800">Aucune alerte en cours</p>
                </div>
            `;
            return;
        }

        container.innerHTML = alerts.map(alert => `
            <div class="border-l-4 ${this.getAlertColor(alert.type)} bg-white p-4 mb-2 rounded shadow-sm">
                <div class="flex justify-between items-center">
                    <div>
                        <p class="font-semibold">${alert.message}</p>
                        <p class="text-sm text-gray-500">${new Date(alert.timestamp).toLocaleString()}</p>
                    </div>
                    <span class="px-2 py-1 text-xs rounded ${this.getAlertBadgeColor(alert.type)}">
                        ${alert.read ? '✅ Lu' : '🆕 Non lu'}
                    </span>
                </div>
            </div>
        `).join('');
    }

    static displayTriggeredAlerts(alerts) {
        const container = document.getElementById('triggered-alerts-container');
        if (!container) return;

        if (!alerts || alerts.length === 0) {
            container.innerHTML = `
                <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 text-center">
                    <i class="fas fa-info-circle text-blue-600 text-xl mb-2"></i>
                    <p class="text-blue-800">Aucune alerte déclenchée récemment</p>
                </div>
            `;
            return;
        }

        container.innerHTML = alerts.map(alert => `
            <div class="border border-${this.getAlertColor(alert.severity)} rounded-lg p-3 mb-2">
                <div class="flex justify-between items-start mb-2">
                    <div>
                        <p class="font-semibold">${alert.description}</p>
                        <p class="text-sm text-gray-600">${(alert.frequency_khz / 1000).toFixed(3)} MHz</p>
                    </div>
                    <span class="px-2 py-1 text-xs rounded-full ${this.getAlertBadgeColor(alert.severity)}">
                        ${alert.severity}
                    </span>
                </div>
                <p class="text-xs text-gray-500">Déclenché: ${new Date(alert.triggered_at).toLocaleString()}</p>
            </div>
        `).join('');
    }

    static getAlertColor(type) {
        const colors = {
            'info': 'border-blue-500',
            'warning': 'border-yellow-500',
            'error': 'border-red-500',
            'high': 'border-red-500',
            'medium': 'border-yellow-500',
            'low': 'border-blue-500'
        };
        return colors[type] || 'border-gray-500';
    }

    static getAlertBadgeColor(type) {
        const colors = {
            'info': 'bg-blue-100 text-blue-800',
            'warning': 'bg-yellow-100 text-yellow-800',
            'error': 'bg-red-100 text-red-800',
            'high': 'bg-red-100 text-red-800',
            'medium': 'bg-yellow-100 text-yellow-800',
            'low': 'bg-blue-100 text-blue-800'
        };
        return colors[type] || 'bg-gray-100 text-gray-800';
    }
}

// Initialisation automatique
if (window.location.pathname.includes('/weak-indicators')) {
    document.addEventListener('DOMContentLoaded', () => {
        AlertsManager.initialize();
    });
}

console.log('✅ AlertsManager chargé');