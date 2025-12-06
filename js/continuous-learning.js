// Geo/static/js/continuous-learning.js
/**
 * Interface utilisateur pour l'apprentissage continu
 */

class ContinuousLearningManager {
    static async showLearningPanel() {
        const content = document.getElementById('themeManagerContent');
        const title = document.getElementById('modalTitle');

        if (!content || !title) return;

        title.textContent = '🧠 Apprentissage Continu';

        content.className = 'p-6 overflow-y-auto flex-1 modal-form-container';

        content.innerHTML = `
        <div class="max-w-6xl mx-auto space-y-6 modal-form-container">
            <!-- En-tête explicatif -->
            <div class="bg-gradient-to-r from-purple-50 to-blue-50 border-l-4 border-purple-500 p-4 rounded-lg">
                <div class="flex items-start">
                    <div class="flex-shrink-0">
                        <i class="fas fa-brain text-purple-500 text-2xl"></i>
                    </div>
                    <div class="ml-3">
                        <h3 class="text-lg font-semibold text-gray-800">Système d'Apprentissage Continu</h3>
                        <p class="mt-2 text-sm text-gray-600">
                            Le système s'améliore automatiquement grâce aux corrections et feedbacks.
                        </p>
                    </div>
                </div>
            </div>

            <!-- Statistiques -->
            <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div class="bg-white rounded-lg shadow p-4 border border-gray-200">
                    <div class="flex items-center">
                        <div class="bg-blue-100 p-2 rounded-full">
                            <i class="fas fa-chart-line text-blue-600"></i>
                        </div>
                        <div class="ml-3">
                            <p class="text-sm text-gray-600">Total Feedbacks</p>
                            <p id="totalFeedbacks" class="text-xl font-bold text-gray-800">0</p>
                        </div>
                    </div>
                </div>

                <div class="bg-white rounded-lg shadow p-4 border border-gray-200">
                    <div class="flex items-center">
                        <div class="bg-green-100 p-2 rounded-full">
                            <i class="fas fa-check-circle text-green-600"></i>
                        </div>
                        <div class="ml-3">
                            <p class="text-sm text-gray-600">Traité</p>
                            <p id="processedFeedbacks" class="text-xl font-bold text-gray-800">0</p>
                        </div>
                    </div>
                </div>

                <div class="bg-white rounded-lg shadow p-4 border border-gray-200">
                    <div class="flex items-center">
                        <div class="bg-yellow-100 p-2 rounded-full">
                            <i class="fas fa-clock text-yellow-600"></i>
                        </div>
                        <div class="ml-3">
                            <p class="text-sm text-gray-600">En attente</p>
                            <p id="pendingFeedbacks" class="text-xl font-bold text-gray-800">0</p>
                        </div>
                    </div>
                </div>

                <div class="bg-white rounded-lg shadow p-4 border border-gray-200">
                    <div class="flex items-center">
                        <div class="bg-purple-100 p-2 rounded-full">
                            <i class="fas fa-robot text-purple-600"></i>
                        </div>
                        <div class="ml-3">
                            <p class="text-sm text-gray-600">Modèle</p>
                            <p id="modelStatus" class="text-xl font-bold text-gray-800">❌</p>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Distribution des sentiments -->
            <div class="bg-white rounded-lg shadow p-6 border border-gray-200">
                <h3 class="text-lg font-semibold text-gray-800 mb-4">
                    <i class="fas fa-chart-pie mr-2"></i>
                    Distribution des Corrections
                </h3>
                <div id="sentimentDistribution" class="space-y-2">
                    <div class="text-center py-4 text-gray-500">
                        <i class="fas fa-spinner fa-spin mr-2"></i>
                        Chargement...
                    </div>
                </div>
            </div>

            <!-- Test de prédiction -->
            <div class="bg-white rounded-lg shadow p-6 border border-gray-200">
                <h3 class="text-lg font-semibold text-gray-800 mb-4">
                    <i class="fas fa-flask mr-2"></i>
                    Test de Prédiction
                </h3>
                <div class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-2">
                            Texte à analyser
                        </label>
                        <textarea id="testText" rows="3" 
                                  class="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                                  placeholder="Entrez un texte pour tester la prédiction..."></textarea>
                    </div>
                    
                    <button onclick="ContinuousLearningManager.testPrediction()"
                            id="testPredictionBtn"
                            class="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition duration-200">
                        <i class="fas fa-brain mr-2"></i>
                        Tester la Prédiction
                    </button>
                    
                    <div id="predictionResult" class="mt-4"></div>
                </div>
            </div>

            <!-- Historique des feedbacks -->
            <div class="bg-white rounded-lg shadow p-6 border border-gray-200">
                <h3 class="text-lg font-semibold text-gray-800 mb-4">
                    <i class="fas fa-history mr-2"></i>
                    Feedbacks Récents
                </h3>
                <div id="recentFeedbacks" class="space-y-3">
                    <div class="text-center py-4 text-gray-500">
                        <i class="fas fa-spinner fa-spin mr-2"></i>
                        Chargement...
                    </div>
                </div>
            </div>
        </div>
        `;

        ModalManager.showModal('themeManagerModal');
        this.loadLearningStats();
        this.loadRecentFeedbacks();
    }

    static async loadLearningStats() {
        try {
            const response = await fetch('/api/learning/feedback/stats');
            const data = await response.json();

            if (response.ok) {
                document.getElementById('totalFeedbacks').textContent = data.total_feedbacks;
                document.getElementById('processedFeedbacks').textContent = data.processed_feedbacks;
                document.getElementById('pendingFeedbacks').textContent = data.pending_feedbacks;

                this.displaySentimentDistribution(data.sentiment_distribution);
            }
        } catch (error) {
            console.error('Erreur chargement stats:', error);
        }

        // Charger le statut du modèle
        try {
            const response = await fetch('/api/learning/model/status');
            const data = await response.json();

            if (response.ok) {
                document.getElementById('modelStatus').innerHTML = data.model_exists ? 
                    '<span class="text-green-600">✅</span>' : 
                    '<span class="text-red-600">❌</span>';
            }
        } catch (error) {
            console.error('Erreur statut modèle:', error);
        }
    }

    static displaySentimentDistribution(distribution) {
        const container = document.getElementById('sentimentDistribution');
        
        if (!distribution || distribution.length === 0) {
            container.innerHTML = '<p class="text-gray-500 text-sm">Aucune donnée disponible</p>';
            return;
        }

        const colors = {
            'positive': 'bg-green-100 text-green-800',
            'neutral_positive': 'bg-blue-100 text-blue-800',
            'neutral_negative': 'bg-yellow-100 text-yellow-800',
            'negative': 'bg-red-100 text-red-800'
        };

        container.innerHTML = distribution.map(item => `
            <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span class="font-medium text-gray-700">${item.sentiment}</span>
                <div class="flex items-center space-x-2">
                    <div class="w-32 bg-gray-200 rounded-full h-2">
                        <div class="bg-blue-600 h-2 rounded-full" 
                             style="width: ${(item.count / Math.max(...distribution.map(d => d.count)) * 100)}%"></div>
                    </div>
                    <span class="text-sm font-semibold text-gray-600">${item.count}</span>
                </div>
            </div>
        `).join('');
    }

    static async testPrediction() {
        const btn = document.getElementById('testPredictionBtn');
        const resultDiv = document.getElementById('predictionResult');
        const text = document.getElementById('testText').value;

        if (!text.trim()) {
            resultDiv.innerHTML = '<div class="bg-yellow-50 border border-yellow-200 rounded-lg p-3 text-yellow-800">Veuillez entrer du texte</div>';
            return;
        }

        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Analyse en cours...';

        try {
            const response = await fetch('/api/learning/test-prediction', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text: text })
            });

            const data = await response.json();

            if (response.ok) {
                const sentimentColors = {
                    'positive': 'text-green-600',
                    'neutral_positive': 'text-blue-600',
                    'neutral_negative': 'text-yellow-600',
                    'negative': 'text-red-600'
                };

                resultDiv.innerHTML = `
                    <div class="bg-gray-50 border border-gray-200 rounded-lg p-4">
                        <div class="flex items-center justify-between mb-3">
                            <span class="font-semibold text-gray-800">Résultat de la prédiction</span>
                            <span class="px-2 py-1 rounded text-xs font-medium ${sentimentColors[data.sentiment] || 'text-gray-600'}">
                                ${data.sentiment}
                            </span>
                        </div>
                        <div class="space-y-2 text-sm">
                            <p><strong>Confiance:</strong> ${(data.confidence * 100).toFixed(1)}%</p>
                            <p><strong>Modèle continu utilisé:</strong> ${data.continuous_model_used ? '✅' : '❌'}</p>
                            ${data.base_sentiment ? `<p><strong>Analyse de base:</strong> ${data.base_sentiment}</p>` : ''}
                        </div>
                    </div>
                `;
            } else {
                resultDiv.innerHTML = `<div class="bg-red-50 border border-red-200 rounded-lg p-3 text-red-800">${data.error}</div>`;
            }

        } catch (error) {
            resultDiv.innerHTML = `<div class="bg-red-50 border border-red-200 rounded-lg p-3 text-red-800">Erreur: ${error.message}</div>`;
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-brain mr-2"></i>Tester la Prédiction';
        }
    }

    static async loadRecentFeedbacks() {
        const container = document.getElementById('recentFeedbacks');
        
        try {
            // Pour l'instant, on affiche un message d'information
            // Dans une version future, on pourrait récupérer les feedbacks récents
            container.innerHTML = `
                <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <div class="flex items-start">
                        <i class="fas fa-info-circle text-blue-500 mt-1 mr-3"></i>
                        <div>
                            <p class="font-semibold text-blue-800">Système d'apprentissage actif</p>
                            <p class="text-blue-600 text-sm mt-1">
                                Les feedbacks sont collectés automatiquement et le système s'améliore progressivement.
                                Les corrections apportées via l'interface d'analyse sont automatiquement intégrées.
                            </p>
                        </div>
                    </div>
                </div>
            `;
        } catch (error) {
            container.innerHTML = `<div class="text-red-500 text-sm">Erreur: ${error.message}</div>`;
        }
    }

    static async submitFeedback(articleId, predicted, corrected, text, confidence = 0.5) {
        try {
            const response = await fetch('/api/learning/collect-feedback', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    article_id: articleId,
                    predicted: predicted,
                    corrected: corrected,
                    text: text,
                    confidence: confidence
                })
            });

            const data = await response.json();

            if (response.ok) {
                console.log('Feedback soumis avec succès:', data);
                return true;
            } else {
                console.error('Erreur feedback:', data);
                return false;
            }
        } catch (error) {
            console.error('Erreur réseau feedback:', error);
            return false;
        }
    }
}

// Initialisation
document.addEventListener('DOMContentLoaded', function () {
    window.ContinuousLearningManager = ContinuousLearningManager;
    console.log('✅ ContinuousLearningManager initialisé');
});
