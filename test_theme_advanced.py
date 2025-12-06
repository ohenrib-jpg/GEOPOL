#!/usr/bin/env python3
"""
Script de test pour le module avancé
"""

import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_import():
    """Test d'import des modules"""
    print("🧪 Test d'import des modules...\n")
    
    try:
        print("1. Import DatabaseManager...")
        from Flask.database import DatabaseManager
        print("   ✅ DatabaseManager OK")
        
        print("\n2. Import ThemeManagerAdvanced...")
        from Flask.theme_manager_advanced import AdvancedThemeManager
        print("   ✅ AdvancedThemeManager OK")
        
        print("\n3. Création instance DatabaseManager...")
        db = DatabaseManager()
        print("   ✅ Instance créée")
        
        print("\n4. Création instance AdvancedThemeManager...")
        atm = AdvancedThemeManager(db)
        print("   ✅ Instance créée")
        
        print("\n5. Test de création de thème...")
        test_theme = {
            'id': 'test_geopolitique',
            'name': 'Test Géopolitique',
            'color': '#FF6B6B',
            'description': 'Test',
            'keywords': [
                {'word': 'guerre', 'weight': 3.0, 'category': 'critical'},
                {'word': 'paix', 'weight': 2.0, 'category': 'primary'}
            ],
            'synonyms': {
                'guerre': ['conflit', 'hostilités']
            },
            'context': {
                'regions': ['Europe', 'Asie'],
                'actors': ['États']
            }
        }
        
        result = atm.create_advanced_theme(test_theme)
        if result:
            print("   ✅ Thème créé avec succès!")
            
            # Récupérer les détails
            print("\n6. Récupération des détails...")
            details = atm.get_theme_with_details('test_geopolitique')
            print(f"   ✅ Détails récupérés: {details['name']}")
            print(f"   📊 Mots-clés pondérés: {len(details.get('weighted_keywords', []))}")
            print(f"   🔄 Synonymes: {len(details.get('synonyms', {}))}")
            
            # Nettoyer
            print("\n7. Nettoyage...")
            db.execute_query("DELETE FROM themes WHERE id = ?", ('test_geopolitique',))
            print("   ✅ Test nettoyé")
        else:
            print("   ❌ Échec de création")
        
        print("\n" + "="*50)
        print("✅ TOUS LES TESTS RÉUSSIS!")
        print("="*50)
        return True
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_import()
    sys.exit(0 if success else 1)