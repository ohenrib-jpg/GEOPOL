#!/usr/bin/env python3
"""
Initialise la base de données démographique avec des données
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def init_database():
    print("🗄️ Initialisation de la base de données démographique...")
    
    try:
        from database import DatabaseManager
        from demographic_service import DemographicDataService
        
        # Connexion à la base
        db = DatabaseManager()
        service = DemographicDataService(db)
        
        print(f"✅ Connexion: {db.db_path}")
        
        # Données de démonstration
        demo_indicators = [
            # Population (Eurostat style)
            {
                'indicator_id': 'demo_pjan',
                'country_code': 'FR',
                'country_name': 'France',
                'value': 67843000,
                'year': 2024,
                'source': 'eurostat',
                'category': 'population',
                'unit': 'persons'
            },
            {
                'indicator_id': 'demo_pjan',
                'country_code': 'DE',
                'country_name': 'Allemagne',
                'value': 84270625,
                'year': 2024,
                'source': 'eurostat',
                'category': 'population',
                'unit': 'persons'
            },
            {
                'indicator_id': 'demo_pjan',
                'country_code': 'ES',
                'country_name': 'Espagne',
                'value': 48563736,
                'year': 2024,
                'source': 'eurostat',
                'category': 'population',
                'unit': 'persons'
            },
            {
                'indicator_id': 'demo_pjan',
                'country_code': 'IT',
                'country_name': 'Italie',
                'value': 58870762,
                'year': 2024,
                'source': 'eurostat',
                'category': 'population',
                'unit': 'persons'
            },
            {
                'indicator_id': 'demo_pjan',
                'country_code': 'UK',
                'country_name': 'Royaume-Uni',
                'value': 67791400,
                'year': 2024,
                'source': 'eurostat',
                'category': 'population',
                'unit': 'persons'
            },
            
            # PIB (World Bank style)
            {
                'indicator_id': 'NY.GDP.MKTP.CD',
                'country_code': 'FR',
                'country_name': 'France',
                'value': 3038000000000,
                'year': 2023,
                'source': 'worldbank',
                'category': 'economy',
                'unit': 'USD'
            },
            {
                'indicator_id': 'NY.GDP.MKTP.CD',
                'country_code': 'DE',
                'country_name': 'Allemagne',
                'value': 4456000000000,
                'year': 2023,
                'source': 'worldbank',
                'category': 'economy',
                'unit': 'USD'
            },
            {
                'indicator_id': 'NY.GDP.MKTP.CD',
                'country_code': 'ES',
                'country_name': 'Espagne',
                'value': 1592000000000,
                'year': 2023,
                'source': 'worldbank',
                'category': 'economy',
                'unit': 'USD'
            },
            
            # Inflation (ECB style)
            {
                'indicator_id': 'ICP',
                'country_code': 'EU',
                'country_name': 'Zone Euro',
                'value': 2.4,
                'year': 2024,
                'source': 'ecb',
                'category': 'economy',
                'unit': '%'
            }
        ]
        
        # Stocker les données
        stored = service.store_indicators(demo_indicators)
        
        print(f"✅ {stored} indicateurs stockés")
        
        # Vérifier
        countries = service.get_available_countries()
        indicators = service.get_available_indicators()
        
        print(f"\n📊 BASE INITIALISÉE:")
        print(f"   • Pays: {len(countries)}")
        for country in countries:
            print(f"     - {country['name']}: {country['indicators']} indicateurs")
        
        print(f"\n   • Indicateurs: {len(indicators)}")
        for ind in indicators:
            print(f"     - {ind['id']} ({ind['source']}): {ind['countries']} pays")
        
        print("\n🎉 Base prête ! Redémarrez Flask et visitez:")
        print("   http://localhost:5000/demographic/")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)