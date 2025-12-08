// static/js/continuous-learning-integration.js
/**
 * Module d'intégration de l'apprentissage continu
 * Ce module connecte l'apprentissage continu à l'interface utilisateur
 */

class ContinuousLearningIntegration {
    constructor() {
        this.feedbackQueue = [];
        this.autoSubmitEnabled = true;
        this.initialized = false;
    }

    /**
     * Initialise l'intégration de l'apprentissage continu
     */
    async initialize() {
        console.log('🧠 Initialisation intégration apprentissage continu...');
        
        try {
            // Vérifier que les dépendances sont chargées
            if (typeof ContinuousLearningManager === 'undefined') {
                console.error('❌ ContinuousLearningManager non chargé');
                return false;
            }

            // Vérifier le statut du système
            const status = await this.checkSystemStatus();
            
            if (status.success) {
                console.log('✅ Système d\'apprentissage actif');
                this.initialized = true;
                
                // Activer la collecte automatique de feedback
                this.enableAutoFeedback();
                
                // Afficher le statut dans l'interface
                this.updateUIStatus(true);
                
                return true;
            } else {
                console.warn('⚠️ Système d\'apprentissage inactif:', status.message);
                this.updateUIStatus(false, status.message);
                return false;
            }
        } catch (error) {
            console.error('❌ Erreur initialisation:', error);
            this.updateUIStatus(false, error.message);
            return false;
        }
    }

    /**
     * Vérifie le statut du système d'apprentissage
     */
    async checkSystemStatus() {
        try {
            const response = await fetch('/api/learning/model/status');
            const data = await response.json();
            
            return {
                success: response.ok,
                data: data,
                message: response.ok ? 'Système actif' : 'Système inactif'
            };
        } catch (error) {
            return {
                success: false,
                message: error.message
            };
        }
    }

    /**
     * Active la collecte automatique de feedback
     */
    enableAutoFeedback() {
        console.log('📡 Activation collecte automatique de feedback');
        
        // Écouter les corrections de sentiment dans l'interface
        document.addEventListener('sentiment-corrected', (event) => {
            this.handleSentimentCorrection(event.detail);
        });

        // Écouter les analyses d'articles
        document.addEventListener('article-analyzed', (event) => {
            this.handleArticleAnalysis(event.detail);
        });
    }

    /**
     * Gère une correction de sentiment
     */
    async handleSentimentCorrection(data) {
        console.log('🔧 Correction de sentiment détectée:', data);
        
        const feedback = {
            article_id: data.articleId,
            predicted_sentiment: data.predicted,
            corrected_sentiment: data.corrected,
            text_content: data.text,
            confidence: data.confidence || 0.5
        };

        // Ajouter à la file d'attente
        this.feedbackQueue.push(feedback);

        // Soumettre si auto-submit activé
        if (this.autoSubmitEnabled) {
            await this.submitFeedback(feedback);
        }
    }

    /**
     * Gère l'analyse d'un article
     */
    async handleArticleAnalysis(data) {
        console.log('📊 Analyse d\'article:', data);
        
        // Si l'utilisateur a corrigé le sentiment, créer un feedback
        if (data.userCorrected) {
            await this.handleSentimentCorrection({
                articleId: data.articleId,
                predicted: data.originalSentiment,
                corrected: data.correctedSentiment,
                text: data.text,
                confidence: data.confidence
            });
        }
    }

    /**
     * Soumet un feedback au serveur
     */
    async submitFeedback(feedback) {
        try {
            const response = await fetch('/api/learning/feedback', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(feedback)
            });

            const result = await response.json();

            if (result.status === 'success') {
                console.log('✅ Feedback soumis avec succès');
                // Retirer de la file d'attente
                const index = this.feedbackQueue.indexOf(feedback);
                if (index > -1) {
                    this.feedbackQueue.splice(index, 1);
                }
                return true;
            } else {
                console.error('❌ Échec soumission feedback:', result);
                return false;
            }
        } catch (error) {
            console.error('❌ Erreur soumission feedback:', error);
            return false;
        }
    }

    /**
     * Soumet tous les feedbacks en attente
     */
    async submitQueuedFeedbacks() {
        console.log(`📤 Soumission de ${this.feedbackQueue.length} feedbacks en attente`);
        
        const promises = this.feedbackQueue.map(feedback => 
            this.submitFeedback(feedback)
        );

        const results = await Promise.allSettled(promises);
        
        const succeeded = results.filter(r => r.status === 'fulfilled' && r.value).length;
        const failed = results.length - succeeded;

        console.log(`✅ ${succeeded} réussis, ❌ ${failed} échoués`);
        
        return { succeeded, failed };
    }

    /**
     * Met à jour le statut dans l'interface utilisateur
     */
    updateUIStatus(active, message = '') {
        // Chercher les indicateurs de statut
        const statusIndicators = document.querySelectorAll('.learning-status-indicator');
        
        statusIndicators.forEach(indicator => {
            if (active) {
                indicator.classList.remove('inactive');
                indicator.classList.add('active');
                indicator.innerHTML = '<i class="fas fa-check-circle text-green-500"></i> Apprentissage actif';
            } else {
                indicator.classList.remove('active');
                indicator.classList.add('inactive');
                indicator.innerHTML = `<i class="fas fa-exclamation-circle text-yellow-500"></i> ${message || 'Apprentissage inactif'}`;
            }
        });

        // Mettre à jour le badge dans les paramètres
        const settingsBadge = document.querySelector('#learning-settings-badge');
        if (settingsBadge) {
            settingsBadge.className = active ? 'badge-success' : 'badge-warning';
            settingsBadge.textContent = active ? 'Actif' : 'Inactif';
        }
    }

    /**
     * Affiche les statistiques d'apprentissage
     */
    async displayStatistics() {
        try {
            const response = await fetch('/api/learning/feedback/stats');
            const stats = await response.json();

            console.log('📊 Statistiques d\'apprentissage:', stats);

            return stats;
        } catch (error) {
            console.error('❌ Erreur récupération stats:', error);
            return null;
        }
    }

    /**
     * Force une session d'apprentissage
     */
    async triggerLearningSession() {
        console.log('🎯 Déclenchement session d\'apprentissage...');
        
        try {
            // Soumettre tous les feedbacks en attente
            await this.submitQueuedFeedbacks();

            // Vérifier si le seuil est atteint
            const stats = await this.displayStatistics();
            
            if (stats && stats.pending_feedbacks >= 20) {
                console.log('✅ Seuil atteint, apprentissage va démarrer automatiquement');
                return { success: true, message: 'Session déclenchée' };
            } else {
                console.log(`⏳ ${stats?.pending_feedbacks || 0}/20 feedbacks - En attente du seuil`);
                return { success: false, message: 'Seuil non atteint', pending: stats?.pending_feedbacks || 0 };
            }
        } catch (error) {
            console.error('❌ Erreur déclenchement:', error);
            return { success: false, message: error.message };
        }
    }
}

// Instance globale
window.LearningIntegration = new ContinuousLearningIntegration();

// Initialisation automatique au chargement
document.addEventListener('DOMContentLoaded', async function() {
    console.log('🔄 Initialisation automatique de l\'apprentissage continu...');
    
    // Attendre que tous les modules soient chargés
    setTimeout(async () => {
        const success = await window.LearningIntegration.initialize();
        
        if (success) {
            console.log('🎉 Intégration apprentissage continu prête !');
            
            // Afficher les stats initiales
            const stats = await window.LearningIntegration.displayStatistics();
            if (stats) {
                console.log(`📊 État actuel: ${stats.total_feedbacks} feedbacks, ${stats.pending_feedbacks} en attente`);
            }
        } else {
            console.warn('⚠️ Intégration apprentissage continu en mode dégradé');
        }
    }, 1000);
});

// Export pour utilisation dans d'autres modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ContinuousLearningIntegration;
}
