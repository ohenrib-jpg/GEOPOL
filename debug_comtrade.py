"""
Script de débogage pour l'API Comtrade
Affiche l'URL exacte et la réponse de l'API
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Fix encoding for Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Charger les variables d'environnement
load_dotenv()

print("=" * 70)
print("DEBUG UN COMTRADE API")
print("=" * 70)

# Récupérer la clé API
api_key = os.getenv('COMTRADE_API_KEY')
print(f"\n1. Clé API: {api_key[:8]}...{api_key[-4:]}")

# Construire la requête exactement comme le connecteur
base_url = "https://comtradeapi.un.org/data/v1/get"
url = f"{base_url}/C/A/HS"

params = {
    'period': '2022',
    'reporterCode': '842',  # USA
    'cmdCode': '280519',
    'flowCode': 'M',
    'partnerCode': '0',  # World
    'motCode': '0',
    'customsCode': 'C00',
    'partner2Code': '0'
}

headers = {
    'User-Agent': 'Geopol-Analytics/1.0',
    'Accept': 'application/json',
    'Ocp-Apim-Subscription-Key': api_key
}

print(f"\n2. URL: {url}")
print(f"\n3. Paramètres:")
for k, v in params.items():
    print(f"   {k}: {v}")

print(f"\n4. Headers:")
for k, v in headers.items():
    if k != 'Ocp-Apim-Subscription-Key':
        print(f"   {k}: {v}")
    else:
        print(f"   {k}: {v[:8]}...{v[-4:]}")

# Faire la requête
print(f"\n5. Envoi de la requête...")
try:
    response = requests.get(url, params=params, headers=headers, timeout=30)

    print(f"\n6. Réponse:")
    print(f"   Status code: {response.status_code}")
    print(f"   Headers: {dict(response.headers)}")

    # Construire l'URL complète avec paramètres
    full_url = response.url
    print(f"\n7. URL complète générée:")
    print(f"   {full_url}")

    print(f"\n8. Corps de la réponse:")
    try:
        data = response.json()
        import json
        print(json.dumps(data, indent=2))
    except:
        print(f"   (Texte brut) {response.text[:500]}")

except Exception as e:
    print(f"\n[ERROR] Erreur: {e}")

print("\n" + "=" * 70)
