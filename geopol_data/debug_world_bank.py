#!/usr/bin/env python3
"""
Script de debug pour comprendre le format de réponse World Bank
"""

import requests
import json

# Test direct sur l'API
url = "https://api.worldbank.org/v2/country/FR/indicator/NY.GDP.MKTP.CD"
params = {
    'format': 'json',
    'per_page': 10,
    'date': 'MRV:1'  # Most Recent Value
}

print("🔍 Test URL:", url)
print("📋 Params:", params)
print("\n" + "="*70)

response = requests.get(url, params=params, timeout=10)
print(f"Status: {response.status_code}")
print(f"Content-Type: {response.headers.get('Content-Type')}")
print("\n📦 Réponse brute:")
print("="*70)

try:
    data = response.json()
    print(json.dumps(data, indent=2, ensure_ascii=False))
except:
    print(response.text)

print("\n" + "="*70)
print("🔍 Type de réponse:", type(data))
if isinstance(data, list):
    print(f"   Longueur: {len(data)}")
    for i, item in enumerate(data):
        print(f"   [{i}] Type: {type(item)}, Contenu: {str(item)[:100]}...")
