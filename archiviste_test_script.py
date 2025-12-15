"""
Script de test automatique pour Archiviste v3.0
À exécuter depuis le dossier Flask/
Usage: python test_archiviste_v3.py
"""

import sys
import os
import json

# Ajouter le chemin Flask au sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_archiviste_v3():
    """Test complet d'Archiviste v3"""
    
    print("=" * 70)
    print("🧪 TEST ARCHIVISTE V3.0")
    print("=" * 70)
    
    # Test 1: Import des modules
    print("\n📦 Test 1: Import des modules...")
    try:
        from database import DatabaseManager
        from archiviste_v3.archiviste_service import ArchivisteServiceImproved
        from archiviste_v3.archive_client import ArchiveOrgClient
        from archiviste_v3.archiviste_database import ArchivisteDatabase
        print("✅ Tous les modules importés avec succès")
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        return False
    
    # Test 2: Initialisation du service
    print("\n🔧 Test 2: Initialisation du service...")
    try:
        db_manager = DatabaseManager()
        service = ArchivisteServiceImproved(db_manager)
        print("✅ Service initialisé")
    except Exception as e:
        print(f"❌ Erreur initialisation: {e}")
        return False
    
    # Test 3: Vérification des périodes
    print("\n📅 Test 3: Récupération des périodes...")
    try:
        periods = service.get_available_periods()
        print(f"✅ {len(periods)} périodes disponibles")
        print(f"   Exemples: {list(periods.keys())[:3]}")
    except Exception as e:
        print(f"❌ Erreur périodes: {e}")
        return False
    
    # Test 4: Vérification des thèmes
    print("\n🏷️  Test 4: Récupération des thèmes...")
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM themes")
        themes_count = cursor.fetchone()[0]
        conn.close()
        
        if themes_count == 0:
            print("⚠️  Aucun thème trouvé - Créez un thème dans l'interface")
            print("   Instructions: Dashboard > Gérer les thèmes > Créer")
            return False
        
        print(f"✅ {themes_count} thème(s) trouvé(s)")
        
        # Récupérer le premier thème
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM themes LIMIT 1")
        theme_row = cursor.fetchone()
        conn.close()
        
        if theme_row:
            test_theme_id = theme_row[0]
            test_theme_name = theme_row[1]
            print(f"   Thème de test: {test_theme_name} (ID: {test_theme_id})")
        else:
            print("❌ Impossible de récupérer un thème de test")
            return False
            
    except Exception as e:
        print(f"❌ Erreur thèmes: {e}")
        return False
    
    # Test 5: Récupération des mots-clés
    print("\n🔑 Test 5: Récupération des mots-clés du thème...")
    try:
        keywords = service.get_theme_keywords(test_theme_id)
        if not keywords:
            print("⚠️  Aucun mot-clé pour ce thème")
            print("   Ajoutez des mots-clés dans l'interface de gestion")
            return False
        
        print(f"✅ {len(keywords)} mots-clés récupérés")
        print(f"   Mots-clés: {', '.join(keywords[:5])}")
        if len(keywords) > 5:
            print(f"   + {len(keywords) - 5} autres...")
    except Exception as e:
        print(f"❌ Erreur mots-clés: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test 6: Construction de requête
    print("\n📝 Test 6: Construction de la requête Archive.org...")
    try:
        query = service.build_theme_based_query(test_theme_id)
        print(f"✅ Requête construite ({len(query)} caractères)")
        print(f"   Aperçu: {query[:100]}...")
    except Exception as e:
        print(f"❌ Erreur construction requête: {e}")
        return False
    
    # Test 7: Test Archive.org (optionnel - peut être lent)
    print("\n🌐 Test 7: Connexion à Archive.org...")
    print("   (Ce test peut prendre 10-30 secondes...)")
    try:
        archive_client = ArchiveOrgClient()
        
        # Test simple avec un mot-clé générique
        results = archive_client.search_press_articles(
            query="war",
            start_year=2020,
            end_year=2025,
            max_results=5
        )
        
        if results:
            print(f"✅ Archive.org accessible - {len(results)} résultats test")
            print(f"   Premier résultat: {results[0].get('title', 'Sans titre')[:50]}...")
        else:
            print("⚠️  Archive.org accessible mais aucun résultat pour le test")
            print("   (Ceci est normal si les serveurs sont temporairement vides)")
    except Exception as e:
        print(f"⚠️  Erreur connexion Archive.org: {e}")
        print("   (Le service fonctionne quand même, mais Archive.org est inaccessible)")
    
    # Test 8: Analyse complète (optionnel)
    print("\n🎯 Test 8: Test d'analyse complète...")
    print("   Voulez-vous tester une analyse complète ? (peut prendre 30s-1min)")
    print("   Ceci effectuera une vraie requête à Archive.org")
    
    user_input = input("   Continuer ? (o/N): ").strip().lower()
    
    if user_input == 'o':
        try:
            print(f"   Analyse: Période 2022-2025 + Thème '{test_theme_name}'")
            result = service.analyze_period_with_theme(
                period_key='2022-2025',
                theme_id=test_theme_id,
                max_items=10
            )
            
            if result.get('success'):
                print(f"✅ Analyse réussie !")
                print(f"   📊 Documents analysés: {result.get('items_analyzed', 0)}")
                print(f"   ⭐ Documents clés: {len(result.get('key_items', []))}")
                
                # Afficher les insights
                if result.get('insights'):
                    print(f"   💡 Insights:")
                    for insight in result['insights'][:3]:
                        print(f"      - {insight}")
                
                # Afficher métadonnées de recherche
                metadata = result.get('search_metadata', {})
                if metadata.get('theme_keywords'):
                    print(f"   🔑 Mots-clés utilisés: {', '.join(metadata['theme_keywords'][:5])}")
            else:
                print(f"⚠️  Analyse terminée mais sans résultats")
                print(f"   Erreur: {result.get('error', 'Inconnue')}")
                print(f"   Suggestions: {result.get('suggestions', [])}")
        except Exception as e:
            print(f"❌ Erreur analyse: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("   ⏭️  Test d'analyse sauté")
    
    # Test 9: Vérification base de données
    print("\n💾 Test 9: Vérification des tables de la base...")
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Vérifier les tables Archiviste v3
        tables_to_check = [
            'archiviste_v3_items',
            'archiviste_v3_embeddings',
            'archiviste_v3_period_analyses'
        ]
        
        for table in tables_to_check:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   ✅ {table}: {count} entrée(s)")
        
        conn.close()
    except Exception as e:
        print(f"❌ Erreur vérification BDD: {e}")
        return False
    
    # Résumé final
    print("\n" + "=" * 70)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 70)
    print("✅ Modules: OK")
    print("✅ Service: OK")
    print("✅ Périodes: OK")
    print("✅ Thèmes: OK")
    print("✅ Mots-clés: OK")
    print("✅ Requêtes: OK")
    print("✅ Base de données: OK")
    print("=" * 70)
    print("\n🎉 TOUS LES TESTS SONT PASSÉS !")
    print("\n📋 Prochaines étapes:")
    print("   1. Lancer le serveur Flask: python run.py")
    print("   2. Accéder à: http://localhost:5000/archiviste-v3/")
    print("   3. Tester l'interface web")
    print("=" * 70)
    
    return True


def create_test_theme(db_manager):
    """Crée un thème de test si aucun n'existe"""
    print("\n🛠️  Création d'un thème de test...")
    
    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Vérifier si un thème existe déjà
        cursor.execute("SELECT COUNT(*) FROM themes")
        if cursor.fetchone()[0] > 0:
            print("   ℹ️  Des thèmes existent déjà, pas besoin de créer un thème de test")
            conn.close()
            return
        
        # Créer un thème de test
        test_keywords = json.dumps([
            'guerre', 'conflit', 'diplomatie', 'sanctions', 
            'ukraine', 'russie', 'otan', 'peace', 'war'
        ])
        
        cursor.execute("""
            INSERT INTO themes (id, name, keywords, color, description)
            VALUES (?, ?, ?, ?, ?)
        """, (
            'test_archiviste',
            'Test Archiviste v3',
            test_keywords,
            '#6366f1',
            'Thème de test pour Archiviste v3.0'
        ))
        
        conn.commit()
        conn.close()
        
        print("   ✅ Thème de test créé: 'Test Archiviste v3'")
        print("   🔑 Mots-clés: guerre, conflit, diplomatie, sanctions, ukraine...")
        
    except Exception as e:
        print(f"   ❌ Erreur création thème de test: {e}")


if __name__ == "__main__":
    print("\n🚀 Démarrage des tests Archiviste v3.0...\n")
    
    # Option: créer un thème de test si nécessaire
    try:
        from database import DatabaseManager
        db_manager = DatabaseManager()
        
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM themes")
        themes_count = cursor.fetchone()[0]
        conn.close()
        
        if themes_count == 0:
            print("⚠️  Aucun thème trouvé dans la base de données")
            user_input = input("   Voulez-vous créer un thème de test ? (O/n): ").strip().lower()
            if user_input != 'n':
                create_test_theme(db_manager)
    except Exception as e:
        print(f"⚠️  Impossible de vérifier les thèmes: {e}")
    
    # Lancer les tests
    success = test_archiviste_v3()
    
    if not success:
        print("\n❌ Certains tests ont échoué")
        print("   Vérifiez les messages d'erreur ci-dessus")
        sys.exit(1)
    else:
        sys.exit(0)
