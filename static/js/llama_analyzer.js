// static/js/llama_analyzer.js - Version corrigée pour Mistral 7B

class LlamaAnalyzer {
    static async generateIAReport() {
        const btn = document.getElementById('generateReportBtn');
        const resultDiv = document.getElementById('iaReportResult');

        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Génération en cours...';

        resultDiv.innerHTML = `
            <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div class="flex items-center mb-3">
                    <i class="fas fa-spinner fa-spin text-blue-600 text-xl mr-3"></i>
                    <div class="flex-1">
                        <p class="text-blue-800 font-semibold">Génération du rapport en cours...</p>
                        <p class="text-blue-600 text-sm" id="progressStatus">Initialisation Mistral 7B...</p>
                    </div>
                </div>
                <div class="bg-white rounded p-2 mt-2">
                    <div class="h-2 bg-blue-200 rounded overflow-hidden">
                        <div id="progressBar" class="h-full bg-blue-600 transition-all duration-500" style="width: 0%"></div>
                    </div>
                </div>
            </div>
        `;

        try {
            const reportType = document.getElementById('reportType').value;
            const startDate = document.getElementById('startDate').value;
            const endDate = document.getElementById('endDate').value;
            const includeSentiment = document.getElementById('includeSentiment').checked;
            const includeSources = document.getElementById('includeSources').checked;
            const generatePDF = document.getElementById('generatePDF').checked;

            const selectedThemes = Array.from(document.querySelectorAll('.theme-checkbox:checked'))
                .map(cb => cb.value);

            const requestData = {
                report_type: reportType,
                start_date: startDate,
                end_date: endDate,
                themes: selectedThemes,
                include_sentiment: includeSentiment,
                include_sources: includeSources,
                generate_pdf: generatePDF
            };

            this.updateProgress(15, 'Collecte des articles...');

            const response = await fetch('/api/generate-ia-report', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestData)
            });

            this.updateProgress(50, 'Analyse par Mistral 7B...');

            const data = await response.json();

            if (data.success) {
                this.updateProgress(100, 'Rapport généré avec succès !');
                setTimeout(() => {
                    this.displayIAReportResults(data, resultDiv, generatePDF);
                }, 500);
            } else {
                resultDiv.innerHTML = `
                    <div class="bg-red-50 border border-red-200 rounded-lg p-4">
                        <p class="text-red-800 font-semibold">❌ Erreur lors de la génération</p>
                        <p class="text-red-600 text-sm mt-1">${data.error || 'Erreur inconnue'}</p>
                        ${data.llama_error ? `<p class="text-red-500 text-xs mt-2">Détail: ${data.llama_error}</p>` : ''}
                        ${data.connection_status ? `<p class="text-red-500 text-xs mt-1">Statut: ${data.connection_status}</p>` : ''}
                    </div>
                `;
            }

        } catch (error) {
            resultDiv.innerHTML = `
                <div class="bg-red-50 border border-red-200 rounded-lg p-4">
                    <p class="text-red-800 font-semibold">❌ Erreur réseau</p>
                    <p class="text-red-600 text-sm mt-1">${error.message}</p>
                    <p class="text-red-500 text-xs mt-2">Vérifiez que le serveur Mistral 7B est démarré</p>
                </div>
            `;
        } finally {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-magic mr-2"></i>Générer le rapport IA';
        }
    }

    static updateProgress(percentage, statusText) {
        const progressBar = document.getElementById('progressBar');
        const statusElement = document.getElementById('progressStatus');

        if (progressBar) {
            progressBar.style.width = percentage + '%';
        }
        if (statusElement) {
            statusElement.textContent = statusText;
        }
    }

    static displayIAReportResults(data, resultDiv, generatePDF) {
        let content = `
            <div class="space-y-4">
                <div class="bg-gray-50 border border-gray-200 rounded-lg p-4">
                    <h3 class="font-semibold text-gray-800 mb-2">Rapport ${data.report_type}</h3>
                    <div class="grid grid-cols-2 gap-4 text-sm">
                        <div>
                            <span class="text-gray-600">Articles analysés:</span>
                            <span class="font-medium">${data.articles_analyzed}</span>
                        </div>
                        <div>
                            <span class="text-gray-600">Période:</span>
                            <span class="font-medium">${data.period}</span>
                        </div>
                        <div>
                            <span class="text-gray-600">Modèle:</span>
                            <span class="font-medium">${data.model_used || 'Mistral 7B'}</span>
                        </div>
                        <div>
                            <span class="text-gray-600">Statut:</span>
                            <span class="font-medium ${data.connection_status === 'Connecté' ? 'text-green-600' : 'text-yellow-600'}">${data.connection_status || 'Inconnu'}</span>
                        </div>
                    </div>
                </div>
                
                <div class="border border-gray-200 rounded-lg p-4">
                    <h4 class="font-semibold text-gray-800 mb-3">Analyse</h4>
                    <div class="prose max-w-none">
                        ${data.analysis_html}
                    </div>
                </div>
        `;

        if (data.model_used === 'fallback') {
            content += `
                <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <p class="text-yellow-800 font-semibold">⚠️ Mode dégradé activé</p>
                    <p class="text-yellow-600 text-sm mt-1">Le serveur Mistral 7B est temporairement indisponible. Rapport basique généré.</p>
                </div>
            `;
        }

        if (generatePDF && data.pdf_generation_available) {
            content += `
                <div class="text-center">
                    <button onclick="LlamaAnalyzer.generatePDF()" class="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700">
                        <i class="fas fa-file-pdf mr-2"></i>Télécharger en PDF
                    </button>
                </div>
            `;
        }

        content += '</div>';
        resultDiv.innerHTML = content;
    }

    static async generatePDF() {
        try {
            const resultDiv = document.getElementById('iaReportResult');
            const htmlContent = resultDiv.querySelector('.prose').innerHTML;

            const response = await fetch('/api/generate-pdf', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    html_content: htmlContent,
                    title: 'Rapport d\'analyse IA',
                    type: 'geopolitique'
                })
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.style.display = 'none';
                a.href = url;
                a.download = `rapport_mistral_${new Date().toISOString().split('T')[0]}.pdf`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
            } else {
                alert('Erreur lors de la génération du PDF');
            }
        } catch (error) {
            console.error('Erreur PDF:', error);
            alert('Erreur lors de la génération du PDF');
        }
    }
}

document.addEventListener('DOMContentLoaded', function () {
    window.LlamaAnalyzer = LlamaAnalyzer;
    console.log('✅ MistralAnalyzer initialisé');
});