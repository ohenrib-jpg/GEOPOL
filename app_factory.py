# Flask/app_factory.py - VERSION AVEC ARCHIVISTE COMPARATIF
import sys
import os
import logging
from flask import Flask, jsonify, request
import signal
import psutil
import time
import threading

logger = logging.getLogger(__name__)

def create_app():
    """Factory pour créer l'application Flask"""
    
    # Chemins des dossiers
    flask_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(flask_dir)
    template_dir = os.path.join(base_dir, 'templates')
    static_dir = os.path.join(base_dir, 'static')
    
    print(f"📂 Répertoire Flask: {flask_dir}")
    print(f"📂 Répertoire base: {base_dir}")
    print(f"📂 Dossier templates: {template_dir}")
    print(f"📂 Dossier static: {static_dir}")
    
    # Vérifier/créer les dossiers
    if not os.path.exists(template_dir):
        print(f"⚠️ ATTENTION: Le dossier templates n'existe pas: {template_dir}")
        os.makedirs(template_dir, exist_ok=True)
        print(f"✅ Création du dossier templates: {template_dir}")
    
    if not os.path.exists(static_dir):
        print(f"⚠️ ATTENTION: Le dossier static n'existe pas: {static_dir}")
        os.makedirs(static_dir, exist_ok=True)
        print(f"✅ Création du dossier static: {static_dir}")
    
    # Créer l'application Flask
    app = Flask(__name__, 
                template_folder=template_dir,
                static_folder=static_dir)
    
    # Configuration
    from .config import DB_PATH
    app.config['DATABASE_PATH'] = DB_PATH
    
    # Initialisation des managers
    from .database import DatabaseManager
    db_manager = DatabaseManager()
    
    # Exécuter les migrations
    from .database_migrations import run_migrations
    run_migrations(db_manager)

    # ============================================================
    # INITIALISATION GEO NARRATIVE ANALYZER
    # ============================================================
    try:
        from .geo_narrative_analyzer import GeoNarrativeAnalyzer
        geo_narrative_analyzer = GeoNarrativeAnalyzer(db_manager)
        print("✅ GeoNarrativeAnalyzer initialisé avec succès")
    except ImportError as e:
        print(f"❌ GeoNarrativeAnalyzer non disponible: {e}")
        geo_narrative_analyzer = None

    # ============================================================
    # INITIALISATION INDICATEURS FRANÇAIS
    # ============================================================
    try:
        from .routes_indicateurs import create_indicateurs_blueprint
        indicateurs_bp = create_indicateurs_blueprint(db_manager)
        app.register_blueprint(indicateurs_bp)
        print("✅ Blueprint Indicateurs Français enregistré")
    except Exception as e:
        print(f"❌ Erreur enregistrement Indicateurs Français: {e}")
        import traceback
        traceback.print_exc()

    # ============================================================
    # INITIALISATION MODULE ENTITÉS GÉOPOLITIQUES
    # ============================================================
    print("\n🌍 Initialisation du module Entités Géopolitiques...")
    
    try:
        from .geopolitical_entity_extractor import GeopoliticalEntityExtractor
        from .entity_database_manager import EntityDatabaseManager
        from .entity_routes import register_entity_routes
        
        # Créer l'extracteur d'entités
        entity_extractor = GeopoliticalEntityExtractor(model_name="fr_core_news_lg")
        print("✅ Extracteur d'entités SpaCy initialisé")
        
        # Créer le gestionnaire de base de données d'entités
        entity_db_manager = EntityDatabaseManager(db_manager)
        print("✅ Gestionnaire BDD entités initialisé")
        
        # Enregistrer les routes
        register_entity_routes(app, db_manager, entity_extractor, entity_db_manager)
        print("✅ Routes API entités enregistrées")
        
        # Stocker dans la config de l'app
        app.config['ENTITY_EXTRACTOR'] = entity_extractor
        app.config['ENTITY_DB_MANAGER'] = entity_db_manager
        
        print("🎉 Module Entités Géopolitiques prêt !")
        
    except ImportError as e:
        print(f"⚠️ Module entités non disponible: {e}")
        print("💡 Installation requise: pip install spacy")
        print("💡 Modèle requis: python -m spacy download fr_core_news_lg")
        entity_extractor = None
        entity_db_manager = None
    except Exception as e:
        print(f"❌ Erreur initialisation entités: {e}")
        import traceback
        traceback.print_exc()
        entity_extractor = None
        entity_db_manager = None
    
    print()  # Ligne vide pour la lisibilité

    # ============================================================
    # CRÉATION DES MANAGERS PRINCIPAUX
    # ============================================================
    from .theme_manager import ThemeManager
    from .theme_manager_advanced import AdvancedThemeManager 
    from .theme_analyzer import ThemeAnalyzer
    from .rss_manager import RSSManager
    from .bayesian_analyzer import BayesianSentimentAnalyzer  
    from .corroboration_engine import CorroborationEngine     
    from .llama_client import get_llama_client
    from .sentiment_analyzer import SentimentAnalyzer
    from .batch_sentiment_analyzer import create_batch_analyzer
    from .alerts_routes import register_alerts_routes

    # Initialisation des managers
    theme_manager = ThemeManager(db_manager)
    advanced_theme_manager = AdvancedThemeManager(db_manager)
    theme_analyzer = ThemeAnalyzer(db_manager)
    rss_manager = RSSManager(db_manager)
    bayesian_analyzer = BayesianSentimentAnalyzer()          
    corroboration_engine = CorroborationEngine()             
    llama_client = get_llama_client()
    sentiment_analyzer = SentimentAnalyzer()
    
    print("✅ Managers principaux initialisés")

    # Créer l'analyseur batch
    batch_analyzer = create_batch_analyzer(
        sentiment_analyzer,
        corroboration_engine,
        bayesian_analyzer
    )
    
    # Stocker dans la config de l'app
    app.config['BATCH_ANALYZER'] = batch_analyzer
    app.config['SENTIMENT_ANALYZER'] = sentiment_analyzer
    app.config['CORROBORATION_ENGINE'] = corroboration_engine
    app.config['BAYESIAN_ANALYZER'] = bayesian_analyzer
    app.config['GEO_NARRATIVE_ANALYZER'] = geo_narrative_analyzer

    # ============================================================
    # ARCHIVISTE COMPARATIF - NOUVELLE VERSION
    # ============================================================
    print("\n🔄 Initialisation Archiviste Comparatif...")
    
    try:
        # Importer le module comparatif
        from .archiviste_comparative import ComparativeArchiviste
        from .routes_archiviste import create_archiviste_blueprint
        
        # Créer l'instance avec le sentiment_analyzer
        comparative_archiviste = ComparativeArchiviste(
            db_manager=db_manager,
            sentiment_analyzer=sentiment_analyzer
        )
        
        # Enregistrer le blueprint
        archiviste_bp = create_archiviste_blueprint(
            db_manager=db_manager,
            comparative_archiviste=comparative_archiviste
        )
        app.register_blueprint(archiviste_bp)
        
        print("✅ Archiviste Comparatif initialisé avec succès")
        print("📊 Routes Archiviste:")
        for rule in app.url_map.iter_rules():
            if 'archiviste' in rule.rule:
                print(f"  • {rule.rule} [{', '.join(rule.methods)}]")
        
    except ImportError as e:
        print(f"⚠️ Module archiviste_comparative non trouvé: {e}")
        print("   → Utilisation du module archiviste_enhanced (legacy)")
        
        # Fallback sur l'ancien module
        try:
            from .archiviste_enhanced import EnhancedArchiviste
            archiviste = EnhancedArchiviste(db_manager)
            
            from .routes_archiviste import create_archiviste_blueprint
            archiviste_bp = create_archiviste_blueprint(db_manager, archiviste)
            app.register_blueprint(archiviste_bp)
            
            print("✅ Archiviste Enhanced (legacy) initialisé")
            
        except Exception as e2:
            print(f"❌ Erreur initialisation Archiviste legacy: {e2}")
            import traceback
            traceback.print_exc()
            
    except Exception as e:
        print(f"❌ Erreur initialisation Archiviste Comparatif: {e}")
        import traceback
        traceback.print_exc()
    
    print()  # Ligne vide pour la lisibilité
    
    # ============================================================
    # ENREGISTREMENT DES BLUEPRINTS
    # ============================================================
    from .weak_indicators_routes import weak_indicators_bp
    from .alerts_system_routes import alerts_system_bp
    
    app.register_blueprint(weak_indicators_bp, url_prefix='/weak-indicators')  
    app.register_blueprint(alerts_system_bp, url_prefix='/alerts')
    print("✅ Blueprints weak_indicators et alerts enregistrés")
    
    # ============================================================
    # ROUTES SDR UNIFIÉES
    # ============================================================
    try:
        from .sdr_unified_routes import register_unified_sdr_routes
        register_unified_sdr_routes(app, db_manager)
        print("✅ Routes SDR unifiées enregistrées")
    except ImportError as e:
        print(f"ℹ️ Routes SDR unifiées non disponibles: {e}")
    except Exception as e:
        print(f"❌ Erreur enregistrement routes SDR: {e}")

    # ============================================================
    # ENREGISTREMENT DES ROUTES PRINCIPALES
    # ============================================================
    from .routes import register_routes
    from .routes_advanced import register_advanced_routes
    from .routes_social import register_social_routes
    from .kiwisdr_schema_fix import fix_kiwisdr_schema

    # Fixer le schéma KiwiSDR
    fix_kiwisdr_schema(db_manager)

    # Enregistrement des routes
    register_routes(app, db_manager, theme_manager, theme_analyzer, rss_manager, 
                   advanced_theme_manager, llama_client, sentiment_analyzer, batch_analyzer)
    
    register_advanced_routes(app, db_manager, bayesian_analyzer, corroboration_engine) 
    register_social_routes(app, db_manager)
    register_alerts_routes(app, db_manager)
    
    print("✅ Routes principales enregistrées")
    
    # ============================================================
    # ROUTES KIWISDR ET STOCK
    # ============================================================
    try:
        from .kiwisdr_routes import register_kiwisdr_routes
        register_kiwisdr_routes(app, db_manager)
        print("✅ Routes KiwiSDR enregistrées")
    except ImportError as e:
        print(f"ℹ️ Routes KiwiSDR non disponibles: {e}")
    
    try:
        from .stock_routes import register_stock_routes
        register_stock_routes(app, db_manager)
        print("✅ Routes Stock enregistrées")
    except ImportError as e:
        print(f"ℹ️ Routes Stock non disponibles: {e}")

    # ============================================================
    # INITIALISATION INDICATEURS FAIBLES
    # ============================================================
    try:
        from .weak_indicators_routes import init_weak_indicators
        init_weak_indicators(db_manager)
        print("✅ Système indicateurs faibles initialisé")
    except Exception as e:
        print(f"❌ Erreur initialisation indicateurs faibles: {e}")

    # ============================================================
    # VÉRIFICATION ET CORRECTION BASE DE DONNÉES ARCHIVISTE
    # ============================================================
    try:
        from .archiviste_db_fix import fix_archiviste_database, get_database_status
        
        print("\n🔍 Vérification base de données Archiviste...")
        status = get_database_status()
        
        if status['issues'] or not all(status['archiviste_tables'].values()):
            print("🔧 Correction nécessaire de la base de données...")
            fix_archiviste_database()
            print("✅ Base de données Archiviste corrigée")
        else:
            print("✅ Base de données Archiviste OK")
        
        # Afficher le statut
        status = get_database_status()
        print(f"📊 Archiviste - Thèmes: {status['theme_count']}, "
              f"Tables: {len([t for t in status['archiviste_tables'].values() if t])}/3, "
              f"Items: {status.get('archiviste_items_count', 0)}")
        
    except Exception as e:
        print(f"⚠️ Vérification base de données Archiviste échouée: {e}")

    # ============================================================
    # AFFICHAGE DES ROUTES (DEBUG)
    # ============================================================
    print("\n📋 Routes enregistrées importantes:")
    important_prefixes = ['api', 'weak-indicators', 'alerts', 'sdr', 'archiviste']
    for rule in app.url_map.iter_rules():
        if any(prefix in rule.rule for prefix in important_prefixes):
            methods = ', '.join(m for m in rule.methods if m not in ['HEAD', 'OPTIONS'])
            print(f"  • {rule.endpoint:40} {rule.rule:50} [{methods}]")

    # ============================================================
    # INITIALISATION FINALE
    # ============================================================
    try:
        print("\n🔄 Initialisation finale du serveur...")

        # Initialisation SDR
        from .weak_indicators_routes import init_weak_indicators_tables
        init_weak_indicators_tables(db_manager)
        print("✅ Tables indicateurs faibles initialisées")

        from .sdr_config import initialize_sdr_streams
        try:
            sdr_count = initialize_sdr_streams(db_manager)
            print(f"🎯 {sdr_count} flux SDR configurés")
        except Exception as e:
            print(f"⚠️ Erreur initialisation SDR: {e}")

        # Export initial
        from .data_exporter import DataExporter
        from .config import DB_PATH
        exporter = DataExporter(DB_PATH)
        exporter.export_daily_analytics()
        print("✅ Export initial créé")

        print("\n🎉 Application Flask initialisée avec succès!")
        print("="*70)

    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation finale: {e}")
        print("⚠️ L'application démarre malgré l'erreur d'initialisation")

    # ============================================================
    # ROUTES DE GESTION DU SYSTÈME
    # ============================================================
    
    @app.route('/api/shutdown', methods=['POST'])
    def shutdown():
        """Endpoint pour arrêter proprement tous les services GEOPOL"""
        try:
            print("\n🔴 Demande d'arrêt propre reçue...")
            services_stopped = []
            
            def shutdown_services():
                time.sleep(0.5)
                
                try:
                    # Arrêter le serveur Llama (Mistral)
                    print("  → Recherche du serveur Mistral...")
                    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                        try:
                            if 'llama-server.exe' in proc.info['name'].lower():
                                print(f"  → Arrêt du serveur IA (PID: {proc.info['pid']})")
                                proc.terminate()
                                services_stopped.append("Serveur IA Mistral")
                                
                                try:
                                    proc.wait(timeout=5)
                                    print("  ✅ Serveur IA arrêté proprement")
                                except psutil.TimeoutExpired:
                                    print("  ⚠️ Forçage de l'arrêt...")
                                    proc.kill()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue
                    
                    # Arrêter Flask
                    print("  → Arrêt du serveur Flask...")
                    services_stopped.append("Serveur Flask")
                    os.kill(os.getpid(), signal.SIGTERM)
                    
                except Exception as e:
                    print(f"  ❌ Erreur lors de l'arrêt: {e}")
            
            shutdown_thread = threading.Thread(target=shutdown_services, daemon=True)
            shutdown_thread.start()
            
            return jsonify({
                'status': 'success',
                'message': 'Arrêt en cours...',
                'services_stopped': ['Flask', 'Serveur IA Mistral']
            }), 200
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/health', methods=['GET'])
    def health():
        """Endpoint de santé pour vérifier que le serveur est actif"""
        return jsonify({
            'status': 'ok',
            'services': {
                'flask': 'running',
                'database': 'ok',
                'archiviste': 'ok' if 'archiviste' in str(app.url_map) else 'disabled'
            }
        }), 200

    # ============================================================
    # FONCTION EXPOSÉE GLOBALEMENT
    # ============================================================
    
    def get_geo_narrative_analyzer():
        """Fonction exposée globalement pour récupérer l'analyseur géo-narratif"""
        return app.config.get('GEO_NARRATIVE_ANALYZER')
    
    app.get_geo_narrative_analyzer = get_geo_narrative_analyzer
    
# ============================================================
# FONCTION ER EXPOSEE GLOBALEMENT - MODULE ENTITES MAJ 2211
# ============================================================

    def get_entity_extractor():
        """Fonction exposée globalement pour récupérer l'extracteur d'entités"""
        return app.config.get('ENTITY_EXTRACTOR')
    
    def get_entity_db_manager():
        """Fonction exposée globalement pour récupérer le gestionnaire BDD entités"""
        return app.config.get('ENTITY_DB_MANAGER')
    
    app.get_entity_extractor = get_entity_extractor
    app.get_entity_db_manager = get_entity_db_manager

    return app
