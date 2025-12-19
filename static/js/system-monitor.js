/**
 * Moniteur de ressources système en temps réel
 * Met à jour les statistiques CPU, mémoire et services
 */

class SystemMonitor {
    constructor() {
        this.updateInterval = 3000; // Mise à jour toutes les 3 secondes
        this.intervalId = null;
        this.isRunning = false;
    }

    /**
     * Initialise le moniteur système
     */
    async initialize() {
        console.log('🖥️ Initialisation du moniteur système...');

        // Vérifier que les éléments HTML existent
        if (!this.checkElements()) {
            console.warn('⚠️ Éléments HTML du moniteur système non trouvés');
            return false;
        }

        // Première mise à jour immédiate
        await this.updateStats();

        // Démarrer les mises à jour périodiques
        this.start();

        console.log('✅ Moniteur système actif');
        return true;
    }

    /**
     * Vérifie que les éléments HTML existent
     */
    checkElements() {
        const elements = [
            'system-status',
            'cpu-usage',
            'memory-usage',
            'llama-status'
        ];

        return elements.every(id => document.getElementById(id) !== null);
    }

    /**
     * Démarre les mises à jour périodiques
     */
    start() {
        if (this.isRunning) return;

        this.intervalId = setInterval(() => {
            this.updateStats();
        }, this.updateInterval);

        this.isRunning = true;
    }

    /**
     * Arrête les mises à jour périodiques
     */
    stop() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
        this.isRunning = false;
    }

    /**
     * Met à jour les statistiques système
     */
    async updateStats() {
        try {
            const response = await fetch('/api/system-stats');

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error || 'Erreur inconnue');
            }

            // Mettre à jour les éléments HTML
            this.updateCPU(data.cpu);
            this.updateMemory(data.memory);
            this.updateLlamaStatus(data.llama);
            this.updateSystemStatus(true);

        } catch (error) {
            console.error('❌ Erreur mise à jour stats système:', error);
            this.updateSystemStatus(false);
        }
    }

    /**
     * Met à jour l'affichage CPU
     */
    updateCPU(cpuData) {
        const element = document.getElementById('cpu-usage');
        if (!element) return;

        const percent = cpuData.percent;
        element.textContent = `${percent}%`;

        // Changer la couleur selon la charge
        element.classList.remove('text-green-400', 'text-yellow-400', 'text-orange-400', 'text-red-400');

        if (percent < 30) {
            element.classList.add('text-green-400');
        } else if (percent < 60) {
            element.classList.add('text-yellow-400');
        } else if (percent < 85) {
            element.classList.add('text-orange-400');
        } else {
            element.classList.add('text-red-400');
        }
    }

    /**
     * Met à jour l'affichage mémoire
     */
    updateMemory(memoryData) {
        const element = document.getElementById('memory-usage');
        if (!element) return;

        const usedGb = memoryData.used_gb;
        const percent = memoryData.percent;

        element.textContent = `${usedGb}GB (${percent}%)`;

        // Changer la couleur selon l'utilisation
        element.classList.remove('text-green-400', 'text-blue-400', 'text-yellow-400', 'text-orange-400', 'text-red-400');

        if (percent < 50) {
            element.classList.add('text-green-400');
        } else if (percent < 70) {
            element.classList.add('text-blue-400');
        } else if (percent < 85) {
            element.classList.add('text-yellow-400');
        } else if (percent < 95) {
            element.classList.add('text-orange-400');
        } else {
            element.classList.add('text-red-400');
        }
    }

    /**
     * Met à jour le statut du serveur Llama/Mistral
     */
    updateLlamaStatus(llamaData) {
        const element = document.getElementById('llama-status');
        if (!element) return;

        if (llamaData.active) {
            const memoryMb = llamaData.memory_mb;
            const memoryGb = (memoryMb / 1024).toFixed(1);

            element.textContent = `● ACTIF (${memoryGb}GB)`;
            element.classList.remove('text-gray-400', 'text-red-400');
            element.classList.add('text-green-400');
        } else {
            element.textContent = '● INACTIF';
            element.classList.remove('text-green-400', 'text-red-400');
            element.classList.add('text-gray-400');
        }
    }

    /**
     * Met à jour le statut système global
     */
    updateSystemStatus(isOnline) {
        const element = document.getElementById('system-status');
        if (!element) return;

        if (isOnline) {
            element.textContent = '● ACTIF';
            element.classList.remove('text-red-400');
            element.classList.add('text-green-400');
        } else {
            element.textContent = '● ERREUR';
            element.classList.remove('text-green-400');
            element.classList.add('text-red-400');
        }
    }
}

// Initialiser le moniteur au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    // Attendre un peu que les autres scripts soient chargés
    setTimeout(() => {
        const monitor = new SystemMonitor();
        monitor.initialize();

        // Rendre le moniteur accessible globalement
        window.SystemMonitor = monitor;
    }, 1000);
});
