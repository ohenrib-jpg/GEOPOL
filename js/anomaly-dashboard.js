// static/js/anomaly-dashboard.js - Dashboard des anomalies

class AnomalyDashboard {
    static async loadAnomalyData() {
        try {
            const report = await ApiClient.get('/api/anomalies/report?days=7');
            this.displayAnomalyReport(report);
        } catch (error) {
            console.error('Erreur chargement anomalies:', error);
        }
    }

    static displayAnomalyReport(report) {
        const container = document.getElementById('anomalyDashboard');
        if (!container) return;

        const html = `
            <div class="space-y-6">
                <!-- En-tête -->
                <div class="bg-gradient-to-r from-red-50 to-orange-50 border-l-4 border-red-500 p-4 rounded-lg">
                    <h3 class="text-lg font-semibold text-gray-800">🔍 Détection d'Anomalies</h3>
                    <p class="text-sm text-gray-600">Période: ${report.period_days} derniers jours</p>
                </div>

                <!-- Anomalies de sentiment -->
                <div class="bg-white rounded-lg shadow-md p-4">
                    <h4 class="font-bold text-gray-800 mb-3">
                        <i class="fas fa-exclamation-triangle text-red-500 mr-2"></i>
                        Anomalies de Sentiment (${report.sentiment_anomalies.length})
                    </h4>
                    ${this.renderSentimentAnomalies(report.sentiment_anomalies)}
                </div>

                <!-- Anomalies thématiques -->
                <div class="bg-white rounded-lg shadow-md p-4">
                    <h4 class="font-bold text-gray-800 mb-3">
                        <i class="fas fa-chart-line text-orange-500 mr-2"></i>
                        Anomalies Thématiques (${Object.keys(report.theme_anomalies).length})
                    </h4>
                    ${this.renderThemeAnomalies(report.theme_anomalies)}
                </div>

                <!-- Anomalies de corrélation -->
                <div class="bg-white rounded-lg shadow-md p-4">
                    <h4 class="font-bold text-gray-800 mb-3">
                        <i class="fas fa-project-diagram text-purple-500 mr-2"></i>
                        Anomalies de Corrélation (${report.correlation_anomalies.length})
                    </h4>
                    ${this.renderCorrelationAnomalies(report.correlation_anomalies)}
                </div>
            </div>
        `;

        container.innerHTML = html;
    }

    static renderSentimentAnomalies(anomalies) {
        if (anomalies.length === 0) {
            return '<p class="text-gray-500 text-sm">Aucune anomalie de sentiment détectée</p>';
        }

        return `
            <div class="space-y-2 max-h-64 overflow-y-auto">
                ${anomalies.map(anomaly => `
                    <div class="flex items-center justify-between p-3 bg-gray-50 rounded border-l-4 ${anomaly.is_positive_anomaly ? 'border-green-500' : 'border-red-500'}">
                        <div>
                            <span class="font-medium">Score: ${anomaly.score.toFixed(3)}</span>
                            <span class="text-sm text-gray-600 ml-2">Z-score: ${anomaly.z_score.toFixed(2)}</span>
                        </div>
                        <div class="text-right">
                            <span class="text-xs px-2 py-1 rounded ${anomaly.is_positive_anomaly ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}">
                                ${anomaly.is_positive_anomaly ? 'Pic positif' : 'Creux négatif'}
                            </span>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    static renderThemeAnomalies(themeAnomalies) {
        const themesWithAnomalies = Object.entries(themeAnomalies);
        
        if (themesWithAnomalies.length === 0) {
            return '<p class="text-gray-500 text-sm">Aucune anomalie thématique détectée</p>';
        }

        return `
            <div class="space-y-3">
                ${themesWithAnomalies.map(([themeId, anomaly]) => `
                    <div class="border border-gray-200 rounded-lg p-3">
                        <div class="flex justify-between items-center mb-2">
                            <h5 class="font-medium text-gray-800 capitalize">${themeId}</h5>
                            <span class="text-sm text-gray-500">${anomaly.total_peaks} pic(s)</span>
                        </div>
                        ${anomaly.significant_peaks.map(peak => `
                            <div class="text-sm bg-yellow-50 p-2 rounded mt-2">
                                <span class="font-medium">${peak.date}</span>
                                <span class="ml-2">Articles: ${peak.count}</span>
                                <span class="ml-2 text-orange-600">Z-score: ${peak.z_score.toFixed(2)}</span>
                            </div>
                        `).join('')}
                    </div>
                `).join('')}
            </div>
        `;
    }

    static renderCorrelationAnomalies(correlations) {
        if (correlations.length === 0) {
            return '<p class="text-gray-500 text-sm">Aucune anomalie de corrélation détectée</p>';
        }

        return `
            <div class="space-y-2">
                ${correlations.map(corr => `
                    <div class="p-3 bg-purple-50 rounded border border-purple-200">
                        <div class="flex justify-between items-center">
                            <span class="font-medium text-purple-800">${corr.interpretation}</span>
                            <span class="text-sm ${corr.is_significant ? 'text-green-600' : 'text-gray-500'}">
                                ${corr.is_significant ? 'Significatif' : 'Non significatif'}
                            </span>
                        </div>
                        <div class="mt-2 text-sm">
                            <span>Corrélation: ${corr.correlation.toFixed(3)}</span>
                            <span class="ml-3">p-value: ${corr.p_value.toFixed(4)}</span>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }
}

// Initialisation
document.addEventListener('DOMContentLoaded', function() {
    window.AnomalyDashboard = AnomalyDashboard;
    console.log('✅ AnomalyDashboard initialisé');
});
