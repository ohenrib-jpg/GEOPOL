// static/js/article-analysis-feedback.js
/**
 * Module de collecte automatique de feedback lors de l'analyse d'articles
 * Connecte l'analyse de sentiment au système d'apprentissage continu
 */

class ArticleAnalysisFeedback {
    constructor() {
        this.enabled = true;
        this.autoLearnThreshold = 0.4; // Seuil de confiance en dessous duquel on demande confirmation
        this.feedbackCount = 0;
    }

    /**
     * Initialise le système de collecte de feedback
     */
    initialize() {
        console.log('🔗 Initialisation collecte feedback articles...');

        // Intercepter les analyses d'articles
        this.interceptArticleAnalysis();

        // Utiliser délégation d'événements pour les boutons de correction
        this.setupEventDelegation();

        console.log('✅ Collecte feedback articles initialisée');
    }

    /**
     * Configure la délégation d'événements pour les boutons de correction
     */
    setupEventDelegation() {
        document.addEventListener('click', (e) => {
            const btn = e.target.closest('.feedback-correction-btn');
            if (btn) {
                e.preventDefault();
                e.stopPropagation();

                const articleId = btn.dataset.articleId;
                const currentSentiment = btn.dataset.currentSentiment || 'neutral';

                console.log('🔧 Clic sur bouton correction, article:', articleId);

                // Trouver la carte d'article parente
                const articleCard = btn.closest('[data-article-id]');
                if (articleCard) {
                    this.showCorrectionModal(articleCard);
                }
            }
        });

        console.log('✅ Délégation d\'événements configurée pour les boutons de correction');
    }

    /**
     * Intercepte les analyses d'articles pour collecter automatiquement les feedbacks
     */
    interceptArticleAnalysis() {
        // Hook sur la fonction d'analyse (si elle existe)
        const originalAnalyze = window.analyzeArticles;
        
        if (typeof originalAnalyze === 'function') {
            window.analyzeArticles = async (...args) => {
                const results = await originalAnalyze.apply(this, args);
                
                // Collecter les feedbacks des résultats
                if (results && Array.isArray(results)) {
                    this.processAnalysisResults(results);
                }
                
                return results;
            };
            console.log('✅ Hook sur analyzeArticles installé');
        }
    }

    /**
     * Traite les résultats d'analyse pour générer des feedbacks
     */
    async processAnalysisResults(results) {
        console.log(`📊 Traitement de ${results.length} résultats d'analyse`);
        
        for (const result of results) {
            // Si la confiance est faible, créer un feedback automatique
            if (result.confidence && result.confidence < this.autoLearnThreshold) {
                await this.createAutoFeedback(result);
            }
        }
    }

    /**
     * Crée un feedback automatique pour un article à faible confiance
     */
    async createAutoFeedback(result) {
        const feedback = {
            article_id: result.article_id || result.id,
            predicted_sentiment: result.sentiment || result.sentiment_type,
            corrected_sentiment: result.sentiment || result.sentiment_type, // Même valeur initialement
            text_content: `${result.title || ''} ${result.content || ''}`.substring(0, 500),
            confidence: result.confidence || 0.5,
            auto_generated: true,
            needs_review: true
        };

        try {
            const response = await fetch('/api/learning/feedback', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(feedback)
            });

            if (response.ok) {
                this.feedbackCount++;
                console.log(`✅ Feedback auto créé (${this.feedbackCount})`);
            }
        } catch (error) {
            console.error('❌ Erreur création feedback auto:', error);
        }
    }

    /**
     * Ajoute des boutons de correction dans l'interface d'articles
     */
    addCorrectionButtons() {
        // Observer les articles affichés pour ajouter des boutons
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                mutation.addedNodes.forEach((node) => {
                    if (node.nodeType === 1) { // Element node
                        // Chercher les cartes d'articles
                        const articleCards = node.querySelectorAll 
                            ? node.querySelectorAll('.article-card, [data-article-id]')
                            : [];
                        
                        articleCards.forEach(card => this.addCorrectionButton(card));
                        
                        // Si le node lui-même est une carte d'article
                        if (node.classList?.contains('article-card') || node.dataset?.articleId) {
                            this.addCorrectionButton(node);
                        }
                    }
                });
            });
        });

        // Observer le body pour détecter les nouveaux articles
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });

        // Traiter les articles déjà présents
        document.querySelectorAll('.article-card, [data-article-id]').forEach(card => {
            this.addCorrectionButton(card);
        });

        console.log('✅ Observateur de boutons de correction activé');
    }

    /**
     * Ajoute un bouton de correction à une carte d'article
     */
    addCorrectionButton(articleCard) {
        // Vérifier si le bouton existe déjà
        if (articleCard.querySelector('.feedback-correction-btn')) {
            return;
        }

        const articleId = articleCard.dataset.articleId || 
                         articleCard.getAttribute('data-article-id');
        
        if (!articleId) return;

        // Trouver l'endroit où insérer le bouton (près du sentiment)
        const sentimentElement = articleCard.querySelector('.sentiment, [class*="sentiment"]');
        
        if (sentimentElement) {
            const correctionBtn = document.createElement('button');
            correctionBtn.className = 'feedback-correction-btn';
            correctionBtn.innerHTML = '<i class="fas fa-edit"></i>';
            correctionBtn.title = 'Corriger le sentiment';
            correctionBtn.style.cssText = `
                margin-left: 8px;
                padding: 4px 8px;
                background: #6366f1;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 12px;
                transition: background 0.2s;
            `;
            
            correctionBtn.addEventListener('mouseenter', () => {
                correctionBtn.style.background = '#4f46e5';
            });
            
            correctionBtn.addEventListener('mouseleave', () => {
                correctionBtn.style.background = '#6366f1';
            });
            
            correctionBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.showCorrectionModal(articleCard);
            });
            
            sentimentElement.appendChild(correctionBtn);
        }
    }

    /**
     * Affiche une modal de correction de sentiment
     */
    showCorrectionModal(articleCard) {
        const articleId = articleCard.dataset.articleId;
        const currentSentiment = articleCard.dataset.sentiment || 
                                articleCard.querySelector('[data-sentiment]')?.dataset.sentiment || 
                                'neutral';
        const title = articleCard.querySelector('.article-title, h3, h4')?.textContent || 'Article';
        const content = articleCard.querySelector('.article-content, .content')?.textContent || '';

        // Créer la modal
        const modal = document.createElement('div');
        modal.className = 'feedback-modal';
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 10000;
        `;

        modal.innerHTML = `
            <div style="background: white; padding: 24px; border-radius: 8px; max-width: 500px; width: 90%;">
                <h3 style="margin: 0 0 16px 0; font-size: 18px; font-weight: 600;">
                    🔧 Corriger le sentiment
                </h3>
                
                <div style="margin-bottom: 16px;">
                    <strong>Article:</strong> ${title.substring(0, 100)}...
                </div>
                
                <div style="margin-bottom: 16px;">
                    <label style="display: block; margin-bottom: 8px; font-weight: 500;">
                        Sentiment actuel: <span style="color: #6366f1;">${currentSentiment}</span>
                    </label>
                    
                    <label style="display: block; margin-bottom: 4px;">
                        Corriger en:
                    </label>
                    <select id="correctedSentiment" style="width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                        <option value="positive" ${currentSentiment === 'positive' ? 'selected' : ''}>
                            🟢 Positive
                        </option>
                        <option value="neutral_positive" ${currentSentiment === 'neutral_positive' ? 'selected' : ''}>
                            🔵 Neutral Positive
                        </option>
                        <option value="neutral_negative" ${currentSentiment === 'neutral_negative' ? 'selected' : ''}>
                            🟡 Neutral Negative
                        </option>
                        <option value="negative" ${currentSentiment === 'negative' ? 'selected' : ''}>
                            🔴 Negative
                        </option>
                    </select>
                </div>
                
                <div style="display: flex; gap: 8px; justify-content: flex-end;">
                    <button id="cancelBtn" style="padding: 8px 16px; border: 1px solid #ddd; background: white; border-radius: 4px; cursor: pointer;">
                        Annuler
                    </button>
                    <button id="submitBtn" style="padding: 8px 16px; background: #10b981; color: white; border: none; border-radius: 4px; cursor: pointer;">
                        ✅ Valider la correction
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Event listeners
        modal.querySelector('#cancelBtn').addEventListener('click', () => {
            document.body.removeChild(modal);
        });

        modal.querySelector('#submitBtn').addEventListener('click', async () => {
            const correctedSentiment = modal.querySelector('#correctedSentiment').value;
            
            await this.submitCorrection(
                articleId,
                currentSentiment,
                correctedSentiment,
                `${title} ${content}`.substring(0, 1000)
            );
            
            document.body.removeChild(modal);
            
            // Mettre à jour l'affichage
            articleCard.dataset.sentiment = correctedSentiment;
            const sentimentBadge = articleCard.querySelector('.sentiment, [class*="sentiment"]');
            if (sentimentBadge) {
                sentimentBadge.textContent = correctedSentiment;
                sentimentBadge.className = `sentiment sentiment-${correctedSentiment}`;
            }
            
            // Notification
            this.showNotification('✅ Correction enregistrée pour l\'apprentissage');
        });

        // Fermer en cliquant à l'extérieur
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                document.body.removeChild(modal);
            }
        });
    }

    /**
     * Soumet une correction de sentiment
     */
    async submitCorrection(articleId, predicted, corrected, text) {
        try {
            const response = await fetch('/api/learning/feedback', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    article_id: parseInt(articleId),
                    predicted_sentiment: predicted,
                    corrected_sentiment: corrected,
                    text_content: text,
                    confidence: 0.8,
                    user_corrected: true
                })
            });

            const result = await response.json();

            if (result.status === 'success') {
                this.feedbackCount++;
                console.log(`✅ Correction soumise (${this.feedbackCount} total)`);
                
                // Émettre l'événement pour l'intégration
                if (typeof window.emitSentimentCorrection === 'function') {
                    window.emitSentimentCorrection(articleId, predicted, corrected, text, 0.8);
                }
                
                return true;
            } else {
                console.error('❌ Échec soumission:', result);
                return false;
            }
        } catch (error) {
            console.error('❌ Erreur soumission correction:', error);
            return false;
        }
    }

    /**
     * Affiche une notification temporaire
     */
    showNotification(message) {
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #10b981;
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            z-index: 10001;
            animation: slideIn 0.3s ease;
        `;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => {
                if (notification.parentNode) {
                    document.body.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }
}

// Instance globale
window.ArticleAnalysisFeedback = new ArticleAnalysisFeedback();

// Initialisation automatique IMMÉDIATE (pas de délai)
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.ArticleAnalysisFeedback.initialize();
    });
} else {
    // DOM déjà chargé, initialiser immédiatement
    window.ArticleAnalysisFeedback.initialize();
}

// Styles pour les animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
    
    .feedback-correction-btn:hover {
        transform: scale(1.1);
    }
`;
document.head.appendChild(style);
