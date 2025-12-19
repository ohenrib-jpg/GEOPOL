// static/js/api-client.js - VERSION CORRIGÉE DU 0912
(function () {
    'use strict';

    // Vérifier si ApiClient existe déjà AVANT de le définir
    if (typeof window.ApiClient !== 'undefined') {
        console.warn('⚠️ ApiClient déjà défini. Utilisation de la version existante.');
        return;
    }

    class ApiClient {
        static async get(url) {
            // Ignorer les requêtes pendant le shutdown
            if (window.isShuttingDown) {
                console.log('🛑 Requête GET annulée (shutdown en cours):', url);
                return Promise.resolve({ success: false, error: 'Shutdown en cours' });
            }

            try {
                console.log(`📡 ApiClient GET: ${url}`);
                const response = await fetch(url);
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                const data = await response.json();
                console.log(`📡 ApiClient GET success:`, data);
                return data;
            } catch (error) {
                // Ne pas logger les erreurs pendant le shutdown
                if (!window.isShuttingDown) {
                    console.error(`❌ ApiClient GET error (${url}):`, error);
                }
                throw error;
            }
        }

        static async post(url, data) {
            // Ignorer les requêtes pendant le shutdown (sauf pour /api/shutdown)
            if (window.isShuttingDown && !url.includes('/api/shutdown')) {
                console.log('🛑 Requête POST annulée (shutdown en cours):', url);
                return Promise.resolve({ success: false, error: 'Shutdown en cours' });
            }

            try {
                console.log(`📡 ApiClient POST: ${url}`, data);
                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify(data)
                });
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                const result = await response.json();
                console.log(`📡 ApiClient POST success:`, result);
                return result;
            } catch (error) {
                // Ne pas logger les erreurs pendant le shutdown
                if (!window.isShuttingDown) {
                    console.error(`❌ ApiClient POST error (${url}):`, error);
                }
                throw error;
            }
        }

        static async put(url, data) {
            // Ignorer les requêtes pendant le shutdown
            if (window.isShuttingDown) {
                console.log('🛑 Requête PUT annulée (shutdown en cours):', url);
                return Promise.resolve({ success: false, error: 'Shutdown en cours' });
            }

            try {
                console.log(`📡 ApiClient PUT: ${url}`, data);
                const response = await fetch(url, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify(data)
                });
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return await response.json();
            } catch (error) {
                if (!window.isShuttingDown) {
                    console.error(`❌ ApiClient PUT error (${url}):`, error);
                }
                throw error;
            }
        }

        static async delete(url) {
            // Ignorer les requêtes pendant le shutdown
            if (window.isShuttingDown) {
                console.log('🛑 Requête DELETE annulée (shutdown en cours):', url);
                return Promise.resolve({ success: false, error: 'Shutdown en cours' });
            }

            try {
                console.log(`📡 ApiClient DELETE: ${url}`);
                const response = await fetch(url, {
                    method: 'DELETE'
                });
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return await response.json();
            } catch (error) {
                if (!window.isShuttingDown) {
                    console.error(`❌ ApiClient DELETE error (${url}):`, error);
                }
                throw error;
            }
        }

        // Méthode pour les appels avec timeout
        static async fetchWithTimeout(url, options = {}, timeout = 10000) {
            const controller = new AbortController();
            const id = setTimeout(() => controller.abort(), timeout);

            try {
                const response = await fetch(url, {
                    ...options,
                    signal: controller.signal
                });
                clearTimeout(id);

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return await response.json();
            } catch (error) {
                clearTimeout(id);
                if (error.name === 'AbortError') {
                    throw new Error(`Timeout après ${timeout}ms`);
                }
                throw error;
            }
        }
    }

    // Exporter uniquement si pas déjà défini
    if (typeof window.ApiClient === 'undefined') {
        window.ApiClient = ApiClient;
        console.log('✅ ApiClient initialisé avec succès');
    }
})();