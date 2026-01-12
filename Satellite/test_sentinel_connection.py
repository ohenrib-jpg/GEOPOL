"""
Test de connexion Sentinel Hub avec identifiants .env

Teste :
1. Chargement des identifiants depuis .env
2. Authentification OAuth2
3. Récupération de métadonnées
"""

import os
import sys
from pathlib import Path

# Ajouter le répertoire parent au path
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

from dotenv import load_dotenv
load_dotenv()

# Import du module satellite avancé
from Flask.Satellite.satellite_advanced import SatelliteAdvanced

def test_sentinel_connection():
    """Test connexion Sentinel Hub"""

    print("=" * 70)
    print("TEST CONNEXION SENTINEL HUB")
    print("=" * 70)

    # 1. Charger identifiants depuis .env
    print("\n[1] Chargement identifiants depuis .env...")
    client_id = os.getenv('COPERNICUS_CLIENT_ID')
    client_secret = os.getenv('COPERNICUS_CLIENT_SECRET')

    if not client_id or not client_secret:
        print("[ERROR] Identifiants non trouves dans .env")
        print("   Verifiez que COPERNICUS_CLIENT_ID et COPERNICUS_CLIENT_SECRET sont definis")
        return False

    print(f"[OK] Client ID: {client_id[:20]}...")
    print(f"[OK] Client Secret: {'*' * 20}")

    # 2. Initialiser module avancé
    print("\n[2] Initialisation module Satellite Advanced...")
    satellite = SatelliteAdvanced(client_id, client_secret)
    print("[OK] Module initialise")

    # 3. Tester connexion
    print("\n[3] Test authentification OAuth2...")
    try:
        connection_ok = satellite.test_connection()

        if connection_ok:
            print("[OK] CONNEXION REUSSIE!")
            print(f"   Token valide jusqu'a: {satellite.token_expiry}")
        else:
            print("[ERROR] ECHEC CONNEXION")
            return False

    except Exception as e:
        print(f"[ERROR] {e}")
        return False

    # 4. Lister couches disponibles
    print("\n[4] Recuperation couches Sentinel disponibles...")
    layers = satellite.get_available_layers()
    print(f"[OK] {len(layers)} couches disponibles:")

    for layer_id, metadata in list(layers.items())[:5]:
        print(f"   - {layer_id}: {metadata['name']}")

    # 5. Test génération URL image (optionnel)
    print("\n[5] Test generation URL image Sentinel-2...")

    # Bbox Paris
    bbox = (2.2, 48.8, 2.4, 48.9)

    try:
        url = satellite.get_layer_url(
            layer_id='sentinel2_l2a_truecolor',
            bbox=bbox,
            width=512,
            height=512,
            date='2024-12-01'
        )

        if url:
            print(f"[OK] URL generee: {url[:100]}...")
        else:
            print("[WARN] Pas d'URL (normal en mode test)")

    except Exception as e:
        print(f"[WARN] Erreur generation URL: {e}")

    # 6. Informations quota
    print("\n[6] Informations quota...")
    quota_info = satellite.get_quota_info()
    if quota_info:
        print(f"[OK] Quota: {quota_info}")

    print("\n" + "=" * 70)
    print("[OK] TEST TERMINE AVEC SUCCES")
    print("=" * 70)

    return True

if __name__ == '__main__':
    success = test_sentinel_connection()
    sys.exit(0 if success else 1)
