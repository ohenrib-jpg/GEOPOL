// static/js/assistant.js - Assistant IA simple
class MistralAssistant {
    constructor() {
        this.isVisible = false;
        this.initialize();
    }

    initialize() {
        // Créer l'interface de l'assistant
        this.createAssistantUI();
        this.bindEvents();

        console.log('🤖 Assistant Mistral initialisé');
    }

    createAssistantUI() {
        // Créer le conteneur de l'assistant
        const assistantHTML = `
        <div id="mistralAssistant" class="fixed bottom-6 right-6 z-50 hidden flex flex-col" style="width: 400px; height: 600px;">
            <!-- En-tête -->
            <div class="bg-gradient-to-r from-indigo-600 to-purple-600 text-white p-4 rounded-t-2xl flex-shrink-0">
                <div class="flex justify-between items-center">
                    <div class="flex items-center space-x-3">
                        <div class="bg-white p-2 rounded-full">
                            <i class="fas fa-robot text-indigo-600 text-xl"></i>
                        </div>
                        <div>
                            <h3 class="font-bold text-lg">GEOPOL Assistant</h3>
                            <p class="text-sm text-indigo-100">Mistral 7B Expert</p>
                        </div>
                    </div>
                    <button id="closeAssistant" class="text-white hover:text-gray-200">
                        <i class="fas fa-times text-xl"></i>
                    </button>
                </div>
            </div>

            <!-- Contenu - Doit pouvoir scroll -->
            <div class="flex-1 p-4 overflow-y-auto bg-white" id="assistantContent" style="min-height: 0;">
                <div class="text-center py-8">
                    <div class="mb-4">
                        <i class="fas fa-comments text-gray-300 text-4xl"></i>
                    </div>
                    <p class="text-gray-600 mb-2">Bonjour ! Je suis GEOPOL Assistant.</p>
                    <p class="text-gray-500 text-sm">Posez-moi une question sur la géopolitique, l'économie ou l'analyse des données.</p>
                </div>
                
                <!-- Messages -->
                <div id="assistantMessages" class="space-y-4 mb-4"></div>
            </div>

            <!-- Input - Fixé en bas -->
            <div class="border-t border-gray-200 p-4 bg-gray-50 rounded-b-2xl flex-shrink-0">
                <div class="flex space-x-2">
                    <input type="text" 
                           id="assistantInput" 
                           placeholder="Posez votre question..."
                           class="flex-1 border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-indigo-500 focus:border-transparent">
                    <button id="sendMessage" 
                            class="bg-indigo-600 text-white px-5 py-3 rounded-lg hover:bg-indigo-700 transition duration-200">
                        <i class="fas fa-paper-plane"></i>
                    </button>
                </div>
                <div class="text-xs text-gray-500 mt-2 flex justify-between">
                    <span id="assistantStatus">Prêt</span>
                    <span>Mistral 7B</span>
                </div>
            </div>
        </div>
        
        <!-- Bouton flottant pour ouvrir - EN DEHORS du container -->
        <button id="toggleAssistant" 
                class="fixed bottom-24 right-6 bg-gradient-to-r from-indigo-600 to-purple-600 text-white p-4 rounded-full shadow-lg hover:shadow-xl transition-all duration-200 hover:scale-110"
                style="z-index: 10001;">
            <i class="fas fa-robot text-2xl"></i>
        </button>
    `;

        // Ajouter au body
        document.body.insertAdjacentHTML('beforeend', assistantHTML);

        // Références
        this.container = document.getElementById('mistralAssistant');
        this.input = document.getElementById('assistantInput');
        this.messagesContainer = document.getElementById('assistantMessages');
        this.statusElement = document.getElementById('assistantStatus');
    }

    bindEvents() {
        // Toggle assistant
        document.getElementById('toggleAssistant').addEventListener('click', () => this.toggle());
        document.getElementById('closeAssistant').addEventListener('click', () => this.hide());

        // Envoyer message
        document.getElementById('sendMessage').addEventListener('click', () => this.sendMessage());
        this.input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });
    }

    toggle() {
        this.isVisible = !this.isVisible;
        if (this.isVisible) {
            this.container.classList.remove('hidden');
            this.container.classList.add('flex');
            this.input.focus();
            this.testConnection();
        } else {
            this.container.classList.add('hidden');
            this.container.classList.remove('flex');
        }
    }

    hide() {
        this.container.classList.add('hidden');
        this.container.classList.remove('flex');
        this.isVisible = false;
    }

    async testConnection() {
        this.updateStatus('Vérification connexion...');

        try {
            const response = await fetch('/api/assistant/status');
            const data = await response.json();

            if (data.connected) {
                this.updateStatus('Connecté ✓', 'text-green-600');
                this.addSystemMessage("Assistant Mistral 7B connecté. Posez-moi une question !");
            } else {
                this.updateStatus('Hors ligne ⚠️', 'text-yellow-600');
                this.addSystemMessage("Assistant en mode limité. Le serveur Mistral est hors ligne.");
            }
        } catch (error) {
            this.updateStatus('Erreur de connexion', 'text-red-600');
            this.addSystemMessage("Impossible de vérifier l'état de l'assistant.");
        }
    }

    async sendMessage() {
        const message = this.input.value.trim();
        if (!message) return;

        // Ajouter le message utilisateur
        this.addUserMessage(message);
        this.input.value = '';

        // Mettre à jour le statut
        this.updateStatus('Analyse en cours...', 'text-blue-600');

        try {
            const response = await fetch('/api/assistant/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    page: window.location.pathname
                })
            });

            const data = await response.json();

            if (data.success) {
                this.addAssistantMessage(data.response);
                this.updateStatus('Prêt', 'text-green-600');
            } else {
                this.addAssistantMessage(`❌ ${data.response || data.error}`);
                this.updateStatus('Erreur', 'text-red-600');
            }

        } catch (error) {
            console.error('Erreur assistant:', error);
            this.addAssistantMessage("Désolé, une erreur réseau s'est produite. Veuillez réessayer.");
            this.updateStatus('Erreur réseau', 'text-red-600');
        }
    }

    addUserMessage(text) {
        const messageHTML = `
            <div class="flex justify-end mb-2">
                <div class="bg-indigo-100 text-gray-800 rounded-2xl rounded-br-none px-4 py-3 max-w-[80%]">
                    <p class="text-sm">${this.escapeHtml(text)}</p>
                    <div class="text-xs text-gray-500 text-right mt-1">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
                </div>
            </div>
        `;
        this.messagesContainer.insertAdjacentHTML('beforeend', messageHTML);
        this.scrollToBottom();
    }

    addAssistantMessage(text) {
        const messageHTML = `
            <div class="flex justify-start mb-2">
                <div class="bg-gray-100 text-gray-800 rounded-2xl rounded-bl-none px-4 py-3 max-w-[80%]">
                    <p class="text-sm">${this.escapeHtml(text)}</p>
                    <div class="text-xs text-gray-500 mt-1">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} • Mistral 7B</div>
                </div>
            </div>
        `;
        this.messagesContainer.insertAdjacentHTML('beforeend', messageHTML);
        this.scrollToBottom();
    }

    addSystemMessage(text) {
        const messageHTML = `
            <div class="text-center mb-2">
                <div class="inline-block bg-gray-200 text-gray-600 text-xs px-3 py-1 rounded-full">
                    <i class="fas fa-info-circle mr-1"></i> ${this.escapeHtml(text)}
                </div>
            </div>
        `;
        this.messagesContainer.insertAdjacentHTML('beforeend', messageHTML);
        this.scrollToBottom();
    }

    updateStatus(text, className = 'text-gray-600') {
        this.statusElement.textContent = text;
        this.statusElement.className = className;
    }

    scrollToBottom() {
        const content = document.getElementById('assistantContent');
        content.scrollTop = content.scrollHeight;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialiser l'assistant quand la page est chargée
document.addEventListener('DOMContentLoaded', () => {
    window.MistralAssistant = new MistralAssistant();
    console.log('🤖 Assistant Mistral prêt');
});

// DEBUG: Vérifier si le bouton existe
setTimeout(() => {
    const btn = document.getElementById('toggleAssistant');
    const container = document.getElementById('mistralAssistant');

    console.log('🔍 DEBUG Assistant:');
    console.log('- Bouton trouvé?:', btn ? 'OUI' : 'NON');
    console.log('- Container trouvé?:', container ? 'OUI' : 'NON');

    if (btn) {
        console.log('- Style bouton:', window.getComputedStyle(btn));
        console.log('- Position:', btn.getBoundingClientRect());

        // Forcer l'affichage temporaire
        btn.style.backgroundColor = 'red !important';
        btn.style.border = '3px solid yellow !important';
        btn.style.zIndex = '99999 !important';
        btn.style.opacity = '1 !important';
        btn.style.visibility = 'visible !important';
    }

    if (container) {
        console.log('- Container visible?:', container.classList.contains('hidden'));
    }
}, 1000);