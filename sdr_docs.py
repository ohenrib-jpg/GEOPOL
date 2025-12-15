# Flask/sdr_docs.py
from flask import Blueprint, render_template_string

sdr_docs_bp = Blueprint('sdr_docs', __name__)

@sdr_docs_bp.route('/api/sdr/docs')
def sdr_api_docs():
    """Documentation de l'API SDR"""
    docs_html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>API SDR Spectrum - Documentation</title>
        <style>
            body { font-family: Arial, sans-serif; padding: 20px; }
            .endpoint { background: #f5f5f5; padding: 15px; margin: 10px 0; border-radius: 5px; }
            .method { display: inline-block; padding: 5px 10px; border-radius: 3px; color: white; }
            .get { background: #61affe; }
            .post { background: #49cc90; }
        </style>
    </head>
    <body>
        <h1>📡 API SDR Spectrum Analyzer</h1>
        
        <div class="endpoint">
            <span class="method get">GET</span>
            <strong>/api/sdr/dashboard</strong>
            <p>Données du dashboard SDR</p>
        </div>
        
        <div class="endpoint">
            <span class="method post">POST</span>
            <strong>/api/sdr/scan</strong>
            <p>Scanne une fréquence spécifique</p>
            <pre>{"frequency": 4625, "bandwidth": 5}</pre>
        </div>
        
        <!-- Ajouter d'autres endpoints -->
    </body>
    </html>
    '''
    
    return render_template_string(docs_html)