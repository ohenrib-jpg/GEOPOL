#!/usr/bin/env python3
# fix_themes_table.py - Correction de la structure de la table themes

import sqlite3
import os
import json
from datetime import datetime

def fix_themes_table():
    """Corrige la structure de la table themes"""
    
    db_path = os.path.join('instance', 'geopol.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Base de données non trouvée: {db_path}")
        return False
    
    print("🔧 Correction de la table themes...")
    print("=" * 60)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. Vérifier la structure actuelle
        print("\n1️⃣ Structure actuelle de la table themes:")
        cursor.execute("PRAGMA table_info(themes)")
        columns = cursor.fetchall()
        
        for col in columns:
            print(f"   {col[1]:20} {col[2]:10} {'NOT NULL' if col[3] else ''} {'DEFAULT ' + str(col[4]) if col[4] else ''}")
        
        # 2. Récupérer les données existantes
        print("\n2️⃣ Sauvegarde des thèmes existants...")
        cursor.execute("SELECT * FROM themes")
        existing_themes = cursor.fetchall()
        print(f"   {len(existing_themes)} thèmes à sauvegarder")
        
        # Sauvegarder en JSON
        themes_backup = []
        for row in existing_themes:
            theme = {
                'id': row[0],
                'name': row[1],
                'keywords': row[2],  # Peut être JSON ou texte
                'color': row[3] if len(row) > 3 else None,
                'description': row[4] if len(row) > 4 else None,
                'created_at': row[5] if len(row) > 5 else None
            }
            themes_backup.append(theme)
            print(f"   - {theme['id']}: {theme['name']}")
        
        # 3. Supprimer l'ancienne table
        print("\n3️⃣ Suppression de l'ancienne table...")
        cursor.execute("DROP TABLE IF EXISTS themes_old")
        cursor.execute("ALTER TABLE themes RENAME TO themes_old")
        print("   ✅ Table renommée en themes_old")
        
        # 4. Créer la nouvelle table avec la bonne structure
        print("\n4️⃣ Création de la nouvelle table...")
        cursor.execute("""
            CREATE TABLE themes (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                keywords TEXT NOT NULL,
                color TEXT DEFAULT '#6366f1',
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("   ✅ Nouvelle table créée")
        
        # 5. Restaurer les données
        print("\n5️⃣ Restauration des données...")
        for theme in themes_backup:
            # Nettoyer et valider les keywords
            keywords = theme['keywords']
            
            # Si c'est déjà du JSON valide, le garder
            if keywords:
                try:
                    # Essayer de parser en JSON
                    if isinstance(keywords, str):
                        parsed = json.loads(keywords)
                        if isinstance(parsed, list):
                            keywords_json = keywords
                        else:
                            # Pas une liste, créer une liste
                            keywords_json = json.dumps([str(parsed)])
                    else:
                        keywords_json = json.dumps([])
                except json.JSONDecodeError:
                    # Pas du JSON, séparer par virgules
                    kw_list = [k.strip() for k in str(keywords).split(',') if k.strip()]
                    keywords_json = json.dumps(kw_list)
            else:
                keywords_json = json.dumps([])
            
            # Insérer
            cursor.execute("""
                INSERT INTO themes (id, name, keywords, color, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                theme['id'],
                theme['name'],
                keywords_json,
                theme['color'] or '#6366f1',
                theme['description'] or '',
                theme['created_at'] or datetime.now().isoformat()
            ))
            print(f"   ✅ Restauré: {theme['id']}")
        
        # 6. Vérifier les données restaurées
        print("\n6️⃣ Vérification...")
        cursor.execute("SELECT id, name, keywords FROM themes")
        restored = cursor.fetchall()
        
        print(f"   {len(restored)} thèmes restaurés:")
        for row in restored:
            try:
                kw_list = json.loads(row[2])
                print(f"   - {row[0]}: {row[1]} ({len(kw_list)} mots-clés)")
            except:
                print(f"   - {row[0]}: {row[1]} (keywords invalides)")
        
        # 7. Supprimer l'ancienne table
        print("\n7️⃣ Nettoyage...")
        cursor.execute("DROP TABLE themes_old")
        print("   ✅ Ancienne table supprimée")
        
        conn.commit()
        print("\n" + "=" * 60)
        print("✅ Table themes corrigée avec succès!")
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False
        
    finally:
        conn.close()

def test_insert():
    """Test d'insertion après correction"""
    print("\n🧪 Test d'insertion...")
    
    db_path = os.path.join('instance', 'geopol.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Supprimer le test s'il existe
        cursor.execute("DELETE FROM themes WHERE id = 'test_fix'")
        
        # Insérer un nouveau thème
        test_data = {
            'id': 'test_fix',
            'name': 'Test Fix',
            'keywords': json.dumps(['test', 'fix', 'validation']),
            'color': '#FF6B6B',
            'description': 'Test après correction'
        }
        
        cursor.execute("""
            INSERT INTO themes (id, name, keywords, color, description)
            VALUES (?, ?, ?, ?, ?)
        """, (
            test_data['id'],
            test_data['name'],
            test_data['keywords'],
            test_data['color'],
            test_data['description']
        ))
        
        conn.commit()
        print("   ✅ Insertion test réussie!")
        
        # Vérifier
        cursor.execute("SELECT * FROM themes WHERE id = 'test_fix'")
        row = cursor.fetchone()
        
        if row:
            print(f"   ✅ Thème récupéré: {row[1]}")
            print(f"   ✅ Keywords: {row[2]}")
        
        # Nettoyer
        cursor.execute("DELETE FROM themes WHERE id = 'test_fix'")
        conn.commit()
        print("   ✅ Test nettoyé")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur test: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    print("🔧 Script de correction de la table themes")
    print()
    
    if fix_themes_table():
        print()
        test_insert()
        print()
        print("✅ Tout est prêt ! Vous pouvez maintenant créer des thèmes.")
    else:
        print()
        print("❌ La correction a échoué. Vérifiez les erreurs ci-dessus.")
