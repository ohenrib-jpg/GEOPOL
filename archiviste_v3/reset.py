"""
reset_via_api.py - Réinitialise via l'API
"""

import requests

try:
    print("🔄 Envoi requête de réinitialisation...")
    response = requests.post("http://localhost:5000/archiviste-v3/api/reset-database")
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            print("✅ Base réinitialisée via API")
        else:
            print(f"❌ Erreur: {result.get('error')}")
    else:
        print(f"❌ Erreur HTTP {response.status_code}")
        
except Exception as e:
    print(f"❌ Erreur connexion: {e}")
    print("Assurez-vous que Flask est en cours d'exécution sur http://localhost:5000")