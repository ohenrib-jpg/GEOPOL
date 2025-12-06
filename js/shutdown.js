/**
 * Gestion de l'arrêt propre de GEOPOL
 * Déclenche l'arrêt des services Flask + Mistral
 */

document.addEventListener('DOMContentLoaded', function () {
    const shutdownBtn = document.getElementById('shutdownBtn');

    if (shutdownBtn) {
        shutdownBtn.addEventListener('click', handleShutdown);
    }
});

async function handleShutdown() {
    const shutdownBtn = document.getElementById('shutdownBtn');

    // Demander confirmation
    const confirmed = confirm(
        '🔴 Arrêt complet du système\n\n' +
        'Cette action va fermer :\n' +
        '• Le serveur Flask (interface web)\n' +
        '• Le serveur IA Mistral 7B\n' +
        '• L\'apprentissage continu\n' +
        '• Tous les processus associés\n\n' +
        'Voulez-vous vraiment continuer ?'
    );

    if (!confirmed) {
        return;
    }

    // Désactiver le bouton
    shutdownBtn.disabled = true;
    shutdownBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Arrêt en cours...';
    shutdownBtn.classList.remove('bg-red-600', 'hover:bg-red-700');
    shutdownBtn.classList.add('bg-gray-400', 'cursor-not-allowed');

    try {
        // Afficher un message de confirmation
        showShutdownModal();

        // Envoyer la requête d'arrêt
        const response = await fetch('/api/shutdown', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            const data = await response.json();
            console.log('Arrêt réussi:', data);

            // Message final
            updateShutdownModal('success', data.services_stopped || []);

            // Fermer la page après 3 secondes
            setTimeout(() => {
                window.close();
                // Si window.close() ne fonctionne pas (ouverture directe)
                document.body.innerHTML = `
                    <div class="flex items-center justify-center min-h-screen bg-gray-900">
                        <div class="text-center text-white">
                            <i class="fas fa-check-circle text-6xl text-green-500 mb-4"></i>
                            <h1 class="text-3xl font-bold mb-2">GEOPOL arrêté avec succès</h1>
                            <p class="text-gray-400">Vous pouvez fermer cette page</p>
                        </div>
                    </div>
                `;
            }, 3000);

        } else {
            throw new Error('Erreur lors de l\'arrêt du serveur');
        }

    } catch (error) {
        console.error('Erreur d\'arrêt:', error);

        // En cas d'erreur réseau (normal si le serveur s'est arrêté rapidement)
        if (error.name === 'TypeError' || error.message.includes('Failed to fetch')) {
            updateShutdownModal('success', ['Services arrêtés']);

            setTimeout(() => {
                window.close();
                document.body.innerHTML = `
                    <div class="flex items-center justify-center min-h-screen bg-gray-900">
                        <div class="text-center text-white">
                            <i class="fas fa-check-circle text-6xl text-green-500 mb-4"></i>
                            <h1 class="text-3xl font-bold mb-2">GEOPOL arrêté avec succès</h1>
                            <p class="text-gray-400">Vous pouvez fermer cette page</p>
                        </div>
                    </div>
                `;
            }, 2000);
        } else {
            updateShutdownModal('error', []);

            // Réactiver le bouton
            shutdownBtn.disabled = false;
            shutdownBtn.innerHTML = '<i class="fas fa-power-off mr-2"></i>Arrêt propre du système';
            shutdownBtn.classList.remove('bg-gray-400', 'cursor-not-allowed');
            shutdownBtn.classList.add('bg-red-600', 'hover:bg-red-700');
        }
    }
}

function showShutdownModal() {
    const modal = document.createElement('div');
    modal.id = 'shutdownModal';
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
    modal.innerHTML = `
        <div class="bg-white rounded-lg shadow-2xl p-8 max-w-md w-full mx-4">
            <div class="text-center">
                <div class="mb-4">
                    <i class="fas fa-spinner fa-spin text-5xl text-blue-600"></i>
                </div>
                <h2 class="text-2xl font-bold text-gray-800 mb-2">Arrêt en cours...</h2>
                <p class="text-gray-600 mb-4">Fermeture des services GEOPOL</p>
                <div class="space-y-2 text-sm text-left">
                    <div class="flex items-center text-gray-700">
                        <i class="fas fa-circle-notch fa-spin text-blue-500 mr-2"></i>
                        <span>Arrêt du serveur Flask</span>
                    </div>
                    <div class="flex items-center text-gray-700">
                        <i class="fas fa-circle-notch fa-spin text-blue-500 mr-2"></i>
                        <span>Arrêt du serveur IA Mistral</span>
                    </div>
                    <div class="flex items-center text-gray-700">
                        <i class="fas fa-circle-notch fa-spin text-blue-500 mr-2"></i>
                        <span>Arrêt de l'apprentissage continu</span>
                    </div>
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
}

function updateShutdownModal(status, services) {
    const modal = document.getElementById('shutdownModal');
    if (!modal) return;

    if (status === 'success') {
        modal.innerHTML = `
            <div class="bg-white rounded-lg shadow-2xl p-8 max-w-md w-full mx-4">
                <div class="text-center">
                    <div class="mb-4">
                        <i class="fas fa-check-circle text-6xl text-green-500"></i>
                    </div>
                    <h2 class="text-2xl font-bold text-gray-800 mb-2">Arrêt réussi !</h2>
                    <p class="text-gray-600 mb-4">Tous les services ont été arrêtés proprement</p>
                    ${services.length > 0 ? `
                        <div class="space-y-2 text-sm text-left bg-gray-50 p-4 rounded">
                            <p class="font-semibold text-gray-700 mb-2">Services arrêtés :</p>
                            ${services.map(s => `
                                <div class="flex items-center text-gray-600">
                                    <i class="fas fa-check text-green-500 mr-2"></i>
                                    <span>${s}</span>
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}
                    <p class="text-sm text-gray-500 mt-4">Fermeture automatique...</p>
                </div>
            </div>
        `;
    } else {
        modal.innerHTML = `
            <div class="bg-white rounded-lg shadow-2xl p-8 max-w-md w-full mx-4">
                <div class="text-center">
                    <div class="mb-4">
                        <i class="fas fa-exclamation-triangle text-6xl text-red-500"></i>
                    </div>
                    <h2 class="text-2xl font-bold text-gray-800 mb-2">Erreur</h2>
                    <p class="text-gray-600 mb-4">Une erreur s'est produite lors de l'arrêt</p>
                    <button onclick="document.getElementById('shutdownModal').remove()" 
                            class="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg">
                        Fermer
                    </button>
                </div>
            </div>
        `;
    }
}
