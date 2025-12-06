# Flask/app_factory.py - VERSION CORRIGÉE COMPLÈTE

import sys
import os
from dotenv import load_dotenv
import logging
from flask import Flask, jsonify, request, render_template
import signal
import psutil
import time
import threading

load_dotenv()
logger = logging.getLogger(__name__)

def create_app():
    """Factory pour créer l'application Flask"""
    
    # Chemins des dossiers
    flask_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(flask_dir)
    template_dir = os.path.join(base_dir, 'templates')
    static_dir = os.path.join(base_dir, 'static')
    
    print("=" * 70)
    print("🚀 GEOPOL ANALYTICS - Initialisation du système")
    print("=" * 70)
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
    
    # ============================================================
    # DÉTECTION DU MODE RÉEL
    # ============================================================
    print("\n🔍 Détection du mode d'opération...")
    
    REAL_MODE = False
    try:
        # Vérifier si le mode réel est activé
        REAL_MODE = os.getenv('GEOPOL_REAL_MODE', 'false').lower() == 'true'
        if REAL_MODE:
            print("✅ MODE RÉEL activé")
            print("   • Données temps réel")
            print("   • Surveillance active")
            print("   • Connexions externes")
        else:
            print("🧪 MODE SIMULATION activé")
            print("   • Données de démonstration")
            print("   • Pas de connexions externes")
    except:
        print("ℹ️ Mode par défaut: SIMULATION")
    
    app.config['REAL_MODE'] = REAL_MODE
    
    # ============================================================
    # INITIALISATION DE LA BASE DE DONNÉES
    # ============================================================
    print("\n💾 Initialisation de la base de données...")
    
    from .database import DatabaseManager
    db_manager = DatabaseManager()
    
    # Exécuter les migrations
    from .database_migrations import run_migrations
    run_migrations(db_manager)
    print("✅ Migrations exécutées")
    
    # ============================================================
    # INITIALISATION DES MANAGERS PRINCIPAUX
    # ============================================================
    print("\n🧠 Initialisation des managers principaux...")
    
    # Variables pour stocker les managers
    theme_manager = None
    theme_analyzer = None
    rss_manager = None
    advanced_theme_manager = None
    llama_client = None
    sentiment_analyzer = None
    batch_analyzer = None
    bayesian_analyzer = None
    corroboration_engine = None
    geo_narrative_analyzer = None
    
    # 1. Theme Manager
    try:
        from .theme_manager import ThemeManager
        theme_manager = ThemeManager(db_manager)
        print("✅ ThemeManager initialisé")
    except Exception as e:
        print(f"⚠️ ThemeManager non disponible: {e}")
    
    # 2. Theme Analyzer
    try:
        from .theme_analyzer import ThemeAnalyzer
        theme_analyzer = ThemeAnalyzer(db_manager)
        print("✅ ThemeAnalyzer initialisé")
    except Exception as e:
        print(f"⚠️ ThemeAnalyzer non disponible: {e}")
    
    # 3. RSS Manager
    try:
        from .rss_manager import RSSManager
        rss_manager = RSSManager(db_manager)
        print("✅ RSSManager initialisé")
    except Exception as e:
        print(f"⚠️ RSSManager non disponible: {e}")
    
    # 4. Advanced Theme Manager
    try:
        from .theme_manager_advanced import AdvancedThemeManager
        advanced_theme_manager = AdvancedThemeManager(db_manager)
        print("✅ AdvancedThemeManager initialisé")
    except Exception as e:
        print(f"⚠️ AdvancedThemeManager non disponible: {e}")
    
    # 5. IA Llama/Mistral
    try:
        from .llama_client import get_llama_client
        llama_client = get_llama_client()
        app.config['LLAMA_CLIENT'] = llama_client
        print("✅ LlamaClient initialisé")
    except Exception as e:
        print(f"⚠️ LlamaClient non disponible: {e}")
    
    # 6. Analyseur de sentiment
    try:
        from .sentiment_analyzer import SentimentAnalyzer
        sentiment_analyzer = SentimentAnalyzer()
        print("✅ SentimentAnalyzer initialisé")
    except Exception as e:
        print(f"⚠️ SentimentAnalyzer non disponible: {e}")
    
    # 7. Analyseur bayésien
    try:
        from .bayesian_analyzer import BayesianSentimentAnalyzer
        bayesian_analyzer = BayesianSentimentAnalyzer()
        print("✅ BayesianSentimentAnalyzer initialisé")
    except Exception as e:
        print(f"⚠️ BayesianSentimentAnalyzer non disponible: {e}")
    
    # 8. Moteur de corroboration
    try:
        from .corroboration_engine import CorroborationEngine
        corroboration_engine = CorroborationEngine()
        print("✅ CorroborationEngine initialisé")
    except Exception as e:
        print(f"⚠️ CorroborationEngine non disponible: {e}")
    
    # 9. Batch Analyzer
    try:
        from .batch_sentiment_analyzer import create_batch_analyzer
        if sentiment_analyzer and corroboration_engine and bayesian_analyzer:
            batch_analyzer = create_batch_analyzer(
                sentiment_analyzer,
                corroboration_engine,
                bayesian_analyzer
            )
            print("✅ BatchAnalyzer initialisé")
    except Exception as e:
        print(f"⚠️ BatchAnalyzer non disponible: {e}")
    
    # 10. Geo Narrative Analyzer
    try:
        from .geo_narrative_analyzer import GeoNarrativeAnalyzer
        geo_narrative_analyzer = GeoNarrativeAnalyzer(db_manager)
        print("✅ GeoNarrativeAnalyzer initialisé")
    except Exception as e:
        print(f"⚠️ GeoNarrativeAnalyzer non disponible: {e}")
    
    # ============================================================
    # 🆕 INITIALISATION DU MODULE WEAK INDICATORS (CORRIGÉ)
    # ============================================================
    print("\n📡 Initialisation du module Weak Indicators...")
    
    weak_indicators_service = None
    weak_indicators_bp = None
    
    try:
        # Configuration
        weak_indicators_config = {
            'real_mode': REAL_MODE,
            'sdr_enabled': True,
            'travel_enabled': True,
            'financial_enabled': True
        }
        
        # Importer et créer le blueprint
        from .weak_indicators.routes import create_weak_indicators_blueprint
        
        # Créer et enregistrer le blueprint
        weak_indicators_bp = create_weak_indicators_blueprint(db_manager, weak_indicators_config)
        app.register_blueprint(weak_indicators_bp)
        print("✅ Blueprint Weak Indicators enregistré")
        
        # Essayer de créer le service (mais ne pas bloquer si ça échoue)
        try:
            from .weak_indicators.service import WeakIndicatorsService
            weak_indicators_service = WeakIndicatorsService(db_manager, weak_indicators_config)
            app.config['WEAK_INDICATORS_SERVICE'] = weak_indicators_service
            print("✅ Service Weak Indicators créé")
        except Exception as e:
            print(f"⚠️ Service Weak Indicators non créé: {e}")
            weak_indicators_service = None
        
        print("✅ Module Weak Indicators initialisé avec succès")
        
    except ImportError as e:
        print(f"❌ Module Weak Indicators non trouvé: {e}")
        print("💡 Vérifiez que le dossier weak_indicators existe dans Flask/")
    except Exception as e:
        print(f"❌ Erreur initialisation Weak Indicators: {e}")
        import traceback
        traceback.print_exc()
    
    # =======================================================================
    # INITIALISATION DU MODULE DE SUIVI FINANCIER PERSONNALISE
    # ========================================================================
    print("\n📊 Initialisation du module Suivi Personnalisé...")

    try:
        from .custom_tracking.routes import create_custom_tracking_blueprint
    
    # CRÉER LE BLUEPRINT
        tracking_bp = create_custom_tracking_blueprint(db_manager)
    
    # ENREGISTRER AVEC LE BON PRÉFIXE
        app.register_blueprint(tracking_bp, url_prefix='/api')
    
        print(f"✅ Module Suivi Personnalisé initialisé sur /api")
    
    except ImportError as e:
        print(f"❌ Erreur import: {e}")
    
    # Créer un blueprint de secours
        from flask import Blueprint, jsonify
        from datetime import datetime
    
        fallback_bp = Blueprint('financial_fallback', __name__)
    
        @fallback_bp.route('/api/financial-tracking/test')
        def test():
            return jsonify({'status': 'fallback_active'})
    
        @fallback_bp.route('/api/financial-tracking/instruments')
        def instruments():
            return jsonify({
            'instruments': [
                {'id': 1, 'symbol': 'AAPL', 'name': 'Apple Inc.'},
                {'id': 2, 'symbol': 'BTC-USD', 'name': 'Bitcoin'}
            ]
        })
    
        app.register_blueprint(fallback_bp)
        print("✅ Fallback Financial Tracking activé")
    
    except Exception as e:
        print(f"❌ Erreur module Suivi: {e}")
        import traceback
        traceback.print_exc()

    # =============================================================
    # ARCHIVISTE
    # =============================================================
    print("\n📚 Initialisation du module Archiviste...")
    
    try:
        from .archiviste_enhanced import EnhancedArchiviste
        archiviste = EnhancedArchiviste(db_manager)
    
        from .routes_archiviste import create_archiviste_blueprint
        archiviste_bp = create_archiviste_blueprint(db_manager, archiviste)
        app.register_blueprint(archiviste_bp)
    
        print("✅ Archiviste Enhanced initialisé")
    except Exception as e:
        print(f"❌ Erreur initialisation Archiviste: {e}")
        import traceback
        traceback.print_exc()

    # ============================================================
    # INITIALISATION DES ENTITÉS GÉOPOLITIQUES
    # ============================================================
    print("\n🌍 Initialisation du module Entités Géopolitiques...")
    
    entity_extractor = None
    entity_db_manager = None
    
    try:
        from .geopolitical_entity_extractor import GeopoliticalEntityExtractor
        from .entity_database_manager import EntityDatabaseManager
        from .entity_routes import register_entity_routes
        
        entity_extractor = GeopoliticalEntityExtractor(model_name="fr_core_news_lg")
        print("✅ Extracteur d'entités SpaCy initialisé")
        
        entity_db_manager = EntityDatabaseManager(db_manager)
        print("✅ Gestionnaire BDD entités initialisé")
        
        register_entity_routes(app, db_manager, entity_extractor, entity_db_manager)
        print("✅ Routes API entités enregistrées")
        
        app.config['ENTITY_EXTRACTOR'] = entity_extractor
        app.config['ENTITY_DB_MANAGER'] = entity_db_manager
        
        print("🎉 Module Entités Géopolitiques prêt !")
        
    except ImportError as e:
        print(f"⚠️ Module entités non disponible: {e}")
        print("💡 Installation requise: pip install spacy")
        print("💡 Modèle requis: python -m spacy download fr_core_news_lg")
    except Exception as e:
        print(f"❌ Erreur initialisation entités: {e}")
        import traceback
        traceback.print_exc()
    
    # ============================================================
    # INITIALISATION MODULE INDICATEURS ÉCONOMIQUES FRANÇAIS
    # ============================================================
    print("\n🇫🇷 Initialisation du module Indicateurs Économiques Français...")
    
    try:
        from .routes_indicators_france import create_france_indicators_blueprint
        indicators_france_bp = create_france_indicators_blueprint(db_manager)
        app.register_blueprint(indicators_france_bp)
        print("✅ Blueprint indicateurs français enregistré")
        print("   • Eurostat (officiel) - Indicateurs France")
        print("   • INSEE (scraping) - Données en temps réel France")
        print("   • yFinance - Marchés financiers")
    except Exception as e:
        print(f"❌ Erreur module indicateurs français: {e}")
        import traceback
        traceback.print_exc()

    # ============================================================
    # INITIALISATION MODULE INDICATEURS ÉCONOMIQUES INTERNATIONAUX
    # ============================================================
    print("\n🌍 Initialisation du module Indicateurs Économiques Internationaux...")
    
    try:
        from .routes_indicators import create_indicators_blueprint
        indicators_intl_bp = create_indicators_blueprint(db_manager)
        app.register_blueprint(indicators_intl_bp)
        print("✅ Blueprint indicateurs internationaux enregistré")
        print("   • yFinance - Marchés financiers")
        print("   • Banque Mondiale - Indicateurs macroéconomiques")
        print("   • OpenSanctions - Sanctions internationales")
        print("   • BRICS - Analyse des économies émergentes")
    except Exception as e:
        print(f"❌ Erreur module indicateurs internationaux: {e}")
        import traceback
        traceback.print_exc()

    # ============================================================
    # ROUTES ASSISTANT IA
    # ============================================================
    print("\n🤖 Initialisation du module Assistant IA...")

    try:
        from .assistant_routes import create_assistant_blueprint
        assistant_bp = create_assistant_blueprint(db_manager)
        app.register_blueprint(assistant_bp)
        print("✅ Blueprint assistant IA enregistré")
    
        # Configuration du client Llama
        if llama_client:
            app.config['LLAMA_CLIENT'] = llama_client
            print("✅ LlamaClient configuré pour l'assistant")
        else:
            print("⚠️ LlamaClient non disponible pour l'assistant")
        
    except Exception as e:
        print(f"❌ Erreur initialisation assistant IA: {e}")
        import traceback
        traceback.print_exc()
    
    # ============================================================
    # ENREGISTREMENT DES ROUTES PRINCIPALES
    # ============================================================
    print("\n🛣️ Enregistrement des routes...")
    
    # Routes principales
    try:
        from .routes import register_routes
        register_routes(app, db_manager, theme_manager, theme_analyzer, rss_manager, 
                       advanced_theme_manager, llama_client, sentiment_analyzer, batch_analyzer)
        print("✅ Routes principales enregistrées")
    except Exception as e:
        print(f"⚠️ Routes principales non disponibles: {e}")
    
    # Routes avancées
    try:
        from .routes_advanced import register_advanced_routes
        register_advanced_routes(app, db_manager, bayesian_analyzer, corroboration_engine)
        print("✅ Routes avancées enregistrées")
    except Exception as e:
        print(f"⚠️ Routes avancées non disponibles: {e}")
    
    # Routes sociales
    try:
        from .routes_social import register_social_routes
        register_social_routes(app, db_manager)
        print("✅ Routes sociales enregistrées")
    except Exception as e:
        print(f"⚠️ Routes sociales non disponibles: {e}")
    
    # Routes alertes
    try:
        from .alerts_routes import register_alerts_routes
        register_alerts_routes(app, db_manager)
        print("✅ Routes alertes enregistrées")
    except Exception as e:
        print(f"⚠️ Routes alertes non disponibles: {e}")
    
    # Routes géo-narrative
    try:
        from .routes_geo_narrative import register_geo_narrative_routes
        if geo_narrative_analyzer:
            register_geo_narrative_routes(app, db_manager, geo_narrative_analyzer)
            print("✅ Routes géo-narrative enregistrées")
    except Exception as e:
        print(f"⚠️ Routes géo-narrative non disponibles: {e}")
    
    # Routes stock
    try:
        from .stock_routes import register_stock_routes
        register_stock_routes(app, db_manager)
        print("✅ Routes stock enregistrées")
    except Exception as e:
        print(f"ℹ️ Routes Stock non disponibles: {e}")
    
    # Routes apprentissage
    try:
        from .learning_routes import create_learning_blueprint
        from .continuous_learning import start_passive_learning
        
        learning_engine = start_passive_learning(db_manager, sentiment_analyzer)
        app.config['LEARNING_ENGINE'] = learning_engine
        print("✅ Apprentissage continu démarré")
        
        learning_bp = create_learning_blueprint(db_manager)
        app.register_blueprint(learning_bp)
        print("✅ Routes apprentissage enregistrées")
    except Exception as e:
        print(f"⚠️ Routes apprentissage non disponibles: {e}")
    
    # ============================================================
    # ROUTES WEAK INDICATORS (DÉJÀ ENREGISTRÉES PLUS HAUT)
    # ============================================================
    print("✅ Routes Weak Indicators enregistrées via blueprint")
    
    # ============================================================
    # INITIALISATION FINALE
    # ============================================================
    try:
        print("\n🔄 Initialisation finale du serveur...")
        
        # Export initial
        from .data_exporter import DataExporter
        from .config import DB_PATH
        exporter = DataExporter(DB_PATH)
        exporter.export_daily_analytics()
        print("✅ Export initial créé")
        
        print("\n" + "="*70)
        print("🎉 GEOPOL ANALYTICS - SYSTÈME COMPLET INITIALISÉ !")
        print("="*70)
        print(f"📡 MODE: {'RÉEL 🌐' if REAL_MODE else 'SIMULATION 🧪'}")
        print("📊 MODULES ACTIFS:")
        print("   • Weak Indicators (SDR/Voyage/Financier)")
        print("   • Analyse IA (Mistral/Sentiment)")
        print("   • Entités Géopolitiques")
        print("   • Géo-Narrative")
        print("   • Apprentissage Continu")
        print("   • Indicateurs Économiques Français ⭐ NOUVEAU")
        print("   • Indicateurs Économiques Internationaux ⭐ NOUVEAU")
        print("   • Export de données")
        print("="*70)
        print("🌐 URLS DISPONIBLES:")
        print("   • http://localhost:5000/ - Tableau de bord")
        print("   • http://localhost:5000/weak-indicators - Indicateurs Faibles")
        print("   • http://localhost:5000/indicators/france - Indicateurs Français ⭐")
        print("   • http://localhost:5000/indicators - Indicateurs Internationaux ⭐")
        print("   • http://localhost:5000/dashboard - Analyses")
        print("   • http://localhost:5000/social - Veille Réseaux")
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
            
            # Arrêter l'apprentissage passif
            try:
                from .continuous_learning import stop_passive_learning
                stop_passive_learning()
                services_stopped.append("Apprentissage Continu")
                print("  ✅ Apprentissage continu arrêté")
            except Exception as e:
                print(f"  ⚠️ Erreur arrêt apprentissage: {e}")
            
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
                'services_stopped': services_stopped
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
                'weak_indicators': 'active' if weak_indicators_service else 'inactive',
                'economic_indicators_france': 'active',
                'economic_indicators_intl': 'active',
                'ia_system': 'active' if llama_client else 'inactive',
                'entity_extraction': 'active' if entity_extractor else 'inactive',
                'real_mode': REAL_MODE
            }
        }), 200
    
    @app.route('/api/system/status')
    def system_status():
        """Statut détaillé du système"""
        return jsonify({
            'success': True,
            'system': {
                'mode': 'REAL' if REAL_MODE else 'SIMULATION',
                'version': '0.6PP',
                'modules': {
                    'weak_indicators': weak_indicators_service is not None,
                    'economic_indicators_france': True,
                    'economic_indicators_intl': True,
                    'ia_system': llama_client is not None,
                    'entity_extraction': entity_extractor is not None,
                    'geo_narrative': geo_narrative_analyzer is not None,
                    'batch_analysis': batch_analyzer is not None,
                    'continuous_learning': app.config.get('LEARNING_ENGINE') is not None
                }
            },
            'database': {
                'path': DB_PATH,
                'exists': os.path.exists(DB_PATH)
            },
            'server': {
                'host': '0.0.0.0',
                'port': 5000
            }
        }), 200
    
    @app.route('/api/system/data-status')
    def data_status():
        """Statut des données (réel vs simulation)"""
        return jsonify({
            'success': True,
            'real_mode': REAL_MODE,
            'weak_indicators_available': weak_indicators_service is not None,
            'economic_indicators_france_available': True,
            'economic_indicators_intl_available': True,
            'recommendation': 'Activez GEOPOL_REAL_MODE=true dans .env pour passer en mode réel' if not REAL_MODE else None
        }), 200
    
    # ============================================================
    # FONCTIONS EXPOSÉES GLOBALEMENT
    # ============================================================
    
    def get_entity_extractor():
        return app.config.get('ENTITY_EXTRACTOR')
    
    def get_entity_db_manager():
        return app.config.get('ENTITY_DB_MANAGER')
    
    def get_weak_indicators_service():
        return app.config.get('WEAK_INDICATORS_SERVICE')
    
    def get_real_mode():
        return app.config.get('REAL_MODE', False)
    
    def get_economic_manager():
        return app.config.get('ECO_MANAGER')
    
    app.get_entity_extractor = get_entity_extractor
    app.get_entity_db_manager = get_entity_db_manager
    app.get_weak_indicators_service = get_weak_indicators_service
    app.get_real_mode = get_real_mode
    app.get_economic_manager = get_economic_manager
    
    return app
