#!/usr/bin/env python3
# debug_theme_creation.py - Debug détaillé de la création de thème

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Flask.database import DatabaseManager
from Flask.theme_manager import ThemeManager
import json
import sqlite3

def test_direct_insert():
    """Test d'insertion directe sans passer par les managers"""
    
    print("🔍 TEST D'INSERTION DIRECTE")
    print("=" * 70)
    
    db_path = os.path.join('instance', 'geopol.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Base de données non trouvée: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. Vérifier la structure
        print("\n1️⃣ Structure de la table themes:")
        cursor.execute("PRAGMA table_info(themes)")
        for col in cursor.fetchall():
            print(f"   {col[1]:20} {col[2]:15} {'NOT NULL' if col[3] else ''}")
        
        # 2. Test avec différents formats
        test_id = 'debug_test'
        
        # Supprimer s'il existe
        cursor.execute("DELETE FROM themes WHERE id = ?", (test_id,))
        conn.commit()
        
        print("\n2️⃣ Test avec JSON string (format correct):")
        try:
            keywords_json = json.dumps(['test1', 'test2', 'test3'])
            print(f"   Keywords: {keywords_json}")
            print(f"   Type: {type(keywords_json)}")
            
            cursor.execute("""
                INSERT INTO themes (id, name, keywords, color, description)
                VALUES (?, ?, ?, ?, ?)
            """, (test_id, 'Test Debug', keywords_json, '#FF0000', 'Test'))
            
            conn.commit()
            print("   ✅ Insertion réussie")
            
            # Vérifier
            cursor.execute("SELECT * FROM themes WHERE id = ?", (test_id,))
            row = cursor.fetchone()
            if row:
                print(f"   ✅ Récupéré: {row[1]}")
                print(f"   ✅ Keywords (brut): {row[2]}")
                print(f"   ✅ Keywords (parsé): {json.loads(row[2])}")
            
            # Nettoyer
            cursor.execute("DELETE FROM themes WHERE id = ?", (test_id,))
            conn.commit()
            
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
            conn.rollback()
            return False
        
        print("\n3️⃣ Test avec les données exactes du frontend:")
        try:
            # Simuler les données du frontend
            frontend_data = {
                'id': 'test',
                'name': 'test',
                'keywords': ['test', 'essai', 'demo'],  # Liste Python
                'color': '#6366f1',
                'description': 'test'
            }
            
            print(f"   Données reçues: {frontend_data}")
            
            # Convertir keywords en JSON (ce que devrait faire routes.py)
            keywords_json = json.dumps(frontend_data['keywords'], ensure_ascii=False)
            print(f"   Keywords JSON: {keywords_json}")
            print(f"   Type: {type(keywords_json)}")
            
            cursor.execute("""
                INSERT INTO themes (id, name, keywords, color, description)
                VALUES (?, ?, ?, ?, ?)
            """, (
                frontend_data['id'],
                frontend_data['name'],
                keywords_json,
                frontend_data['color'],
                frontend_data['description']
            ))
            
            conn.commit()
            print("   ✅ Insertion réussie avec données frontend")
            
            # Nettoyer
            cursor.execute("DELETE FROM themes WHERE id = ?", (frontend_data['id'],))
            conn.commit()
            
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
            conn.rollback()
            return False
        
        print("\n4️⃣ Test avec ThemeManager:")
        try:
            db_manager = DatabaseManager()
            theme_manager = ThemeManager(db_manager)
            
            success = theme_manager.create_theme(
                theme_id='debug_manager_test',
                name='Test Manager',
                keywords=['test', 'manager', 'debug'],
                color='#00FF00',
                description='Test via manager'
            )
            
            if success:
                print("   ✅ Création via ThemeManager réussie")
                
                # Vérifier
                theme = theme_manager.get_theme('debug_manager_test')
                if theme:
                    print(f"   ✅ Thème récupéré: {theme['name']}")
                    print(f"   ✅ Keywords: {theme['keywords']}")
                
                # Nettoyer
                theme_manager.delete_theme('debug_manager_test')
            else:
                print("   ❌ Échec création via ThemeManager")
                return False
            
        except Exception as e:
            print(f"   ❌ Erreur ThemeManager: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        print("\n" + "=" * 70)
        print("✅ Tous les tests ont réussi !")
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur critique: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        conn.close()

def check_actual_data_types():
    """Vérifie les types réels des données dans la table"""
    
    print("\n\n🔍 VÉRIFICATION DES TYPES DE DONNÉES")
    print("=" * 70)
    
    db_path = os.path.join('instance', 'geopol.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT id, name, keywords, typeof(keywords) as kw_type FROM themes")
        
        print("\nThèmes existants et leurs types:")
        print(f"{'ID':20} {'Nom':30} {'Type keywords':15}")
        print("-" * 70)
        
        for row in cursor.fetchall():
            theme_id, name, keywords, kw_type = row
            print(f"{theme_id:20} {name:30} {kw_type:15}")
            
            if kw_type != 'text':
                print(f"   ⚠️  PROBLÈME: Type incorrect détecté!")
                print(f"   Valeur: {keywords}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    print("🧪 SCRIPT DE DEBUG CRÉATION DE THÈME\n")
    
    # D'abord vérifier les types
    check_actual_data_types()
    
    # Puis tester l'insertion
    if test_direct_insert():
        print("\n✅ Le problème n'est PAS dans la base de données")
        print("→ Le problème est probablement dans Flask/routes.py ou Flask/theme_manager.py")
    else:
        print("\n❌ Le problème est dans la base de données")
        print("→ Exécutez: python init_database.py")
