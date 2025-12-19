import os
from Flask.app_factory import create_app

app = create_app()

if __name__ == '__main__':
    # SÉCURITÉ: Ne jamais utiliser debug=True en production
    # Utiliser une variable d'environnement pour contrôler le mode debug
    debug_mode = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'

    # SÉCURITÉ: Utiliser 127.0.0.1 par défaut au lieu de 0.0.0.0
    # 0.0.0.0 expose l'application à tout le réseau
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', '5000'))

    app.run(debug=debug_mode, host=host, port=port)