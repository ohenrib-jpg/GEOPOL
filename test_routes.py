#!/usr/bin/env python3
"""
Script de test complet pour vérifier toutes les routes et la configuration
"""

import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_application_creation():
    """Teste la création de l'application Flask"""
    print("\n" + "=" * 60)
    print("🧪 TEST DE CRÉATION DE L'APPLICATION")
    print("=" * 60)
    
    try:
        from Flask.app_factory import create_app
        app = create_app()
        
        print("✅ Application créée avec succès")
        print(f"   📦 Nom: {app.name}")
        print(f"   🔧 Mode debug: {app.debug}")
        
        return app, True
    except Exception as e:
        print(f"❌ Erreur création application: {e}")
        import traceback
        traceback.print_exc()
        return None, False

def test_advanced_routes(app):
    """Vérifie que toutes les routes avancées sont enregistrées"""
    print("\n" + "=" * 60)
    print("🔍 TEST DES ROUTES AVANCÉES")
    print("=" * 60)
    
    required_routes = [
        '/api/bayesian/analyze-article/<int:article_id>',
        '/api/bayesian/batch-analyze',
        '/api/corroboration/find/<int:article_id>',
        '/api/corroboration/batch-process',
        '/api/corroboration/stats/<int:article_id>',
        '/api/advanced/full-analysis/<int:article_id>',
        '/api/analyzed-articles'  # Cette route manque !
    ]
    
    all_routes = []
    for rule in app.url_map.iter_rules():
        all_routes.append(str(rule))
    
    missing_routes = []
    found_routes = []
    
    for route in required_routes:
        # Nettoyer la route pour la comparaison
        route_pattern = route.replace('<int:article_id>', '<article_id>')
        
        found = False
        for app_route in all_routes:
            if route_pattern in app_route or route.split('<')[0] in app_route:
                found = True
                found_routes.append(route)
                break
        
        if not found:
            missing_routes.append(route)
    
    print(f"\n📊 Routes avancées trouvées: {len(found_routes)}/{len(required_routes)}")
    
    if found_routes:
        print("\n✅ Routes trouvées:")
        for route in found_routes:
            print(f"   • {route}")
    
    if missing_routes:
        print(f"\n❌ Routes manquantes: {len(missing_routes)}")
        for route in missing_routes:
            print(f"   • {route}")
        return False
    
    print("\n✅ Toutes les routes avancées sont enregistrées")
    return True

def test_database():
    """Vérifie la structure de la base de données"""
    print("\n" + "=" * 60)
    print("💾 TEST DE LA BASE DE DONNÉES")
    print("=" * 60)
    
    try:
        from Flask.database import DatabaseManager
        db = DatabaseManager()
        
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Lister les tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"\n📊 Tables trouvées: {len(tables)}")
        
        required_tables = [
            'articles', 
            'themes', 
            'theme_analyses',
            'article_corroborations'
        ]
        
        for table in required_tables:
            if table in tables:
                print(f"  ✅ {table}")
            else:
                print(f"  ❌ {table} (MANQUANTE)")
        
        # Vérifier les colonnes de la table articles
        cursor.execute("PRAGMA table_info(articles)")
        columns = [row[1] for row in cursor.fetchall()]
        
        print(f"\n📋 Colonnes de 'articles': {len(columns)}")
        
        required_columns = [
            'id', 'title', 'content', 'sentiment_score', 'sentiment_type',
            'bayesian_confidence', 'bayesian_evidence_count', 'analyzed_at'
        ]
        
        for col in required_columns:
            if col in columns:
                print(f"  ✅ {col}")
            else:
                print(f"  ❌ {col} (MANQUANTE)")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur test base de données: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_imports():
    """Teste les imports des modules avancés"""
    print("\n" + "=" * 60)
    print("📦 TEST DES IMPORTS")
    print("=" * 60)
    
    modules = [
        ('Flask.bayesian_analyzer', 'BayesianSentimentAnalyzer'),
        ('Flask.corroboration_engine', 'CorroborationEngine'),
        ('Flask.database_migrations', 'run_migrations'),
        ('Flask.theme_manager_advanced', 'AdvancedThemeManager'),
    ]
    
    all_ok = True
    
    for module_name, class_name in modules:
        try:
            module = __import__(module_name, fromlist=[class_name])
            getattr(module, class_name)
            print(f"  ✅ {module_name}.{class_name}")
        except Exception as e:
            print(f"  ❌ {module_name}.{class_name}: {e}")
            all_ok = False
    
    return all_ok

def main():
    """Fonction principale"""
    print("=" * 60)
    print("🚀 DÉMARRAGE DES TESTS COMPLETS")
    print("=" * 60)
    
    results = {}
    
    # Test 1: Imports
    results['imports'] = test_imports()
    
    # Test 2: Création application
    app, results['app_creation'] = test_application_creation()
    
    if app:
        # Test 3: Routes avancées
        results['advanced_routes'] = test_advanced_routes(app)
    else:
        results['advanced_routes'] = False
    
    # Test 4: Base de données
    results['database'] = test_database()
    
    # Résumé
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅" if passed else "❌"
        print(f"{status} {test_name.replace('_', ' ').title()}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n✅ TOUS LES TESTS RÉUSSIS")
    else:
        print("\n❌ CERTAINS TESTS ONT ÉCHOUÉ")
        print("\n🔧 Actions recommandées:")
        
        if not results.get('imports'):
            print("   - Vérifiez que tous les fichiers Python sont présents dans Flask/")
        
        if not results.get('advanced_routes'):
            print("   - Ajoutez la route /api/analyzed-articles dans routes_advanced.py")
            print("   - Vérifiez que register_advanced_routes() est appelé dans app_factory.py")
        
        if not results.get('database'):
            print("   - Exécutez les migrations de base de données")
            print("   - Vérifiez Flask/database_migrations.py")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
