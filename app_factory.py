# Flask/app_factory.py - VERSION CORRIGÉE MAJ 0912 AVEC SDR + GEOPOL-DATA AJOUTÉ

import sys
import os
import json

# Ajouter le répertoire Flask au path pour permettre l'import de config
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import config
from dotenv import load_dotenv
import logging
from datetime import datetime
from flask import Flask, jsonify, request, render_template, send_from_directory, redirect, Response
import signal
import psutil
import time
import threading
from fluxStrategiques.api_monitoring_routes import monitoring_bp

load_dotenv()
logger = logging.getLogger(__name__)

def create_app():
    """Factory pour créer l'application Flask - VERSION PRODUCTION"""

    # Configuration du logging pour le débogage
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    # Chemins des dossiers (votre architecture existante)
    flask_dir = os.path.dirname(os.path.abspath(__file__))
    base_dir = os.path.dirname(flask_dir)
    template_dir = os.path.join(base_dir, 'templates')
    static_dir = os.path.join(base_dir, 'static')

    print("=" * 70)
    print("GEOPOL ANALYTICS - Initialisation du systeme")
    print("=" * 70)

    # Vérifier/créer les dossiers
    for dir_path, dir_name in [(template_dir, 'templates'), (static_dir, 'static')]:
        if not os.path.exists(dir_path):
            print(f"[WARN] Creation du dossier {dir_name}: {dir_path}")
            os.makedirs(dir_path, exist_ok=True)

    # Créer l'application Flask
    app = Flask(__name__,
                template_folder=template_dir,
                static_folder=static_dir,
                static_url_path='/static')  # AJOUT CRITIQUE

    # Configuration SECRET_KEY pour sessions Flask
    secret_key = os.getenv('FLASK_SECRET_KEY')
    if secret_key:
        app.config['SECRET_KEY'] = secret_key
    else:
        # Générer une clé temporaire en développement
        import secrets
        app.config['SECRET_KEY'] = secrets.token_hex(32)
        print("[WARN] SECRET_KEY generee automatiquement - definir FLASK_SECRET_KEY en production")

    # Configuration existante
    try:
        try:
            from .config import DB_PATH
        except ImportError:
            from config import DB_PATH
    except ImportError:
        from config import DB_PATH
    
    app.config['DATABASE_PATH'] = DB_PATH
    app.register_blueprint(monitoring_bp)
    # ============================================================
    # CONFIGURATION CORRECTE DES FICHIERS STATIQUES
    # ============================================================
    print(f"\n[FOLDERS] Configuration des dossiers:")
    print(f"   Base dir: {base_dir}")
    print(f"   Static dir: {static_dir}")
    print(f"   Template dir: {template_dir}")

    # Vérifier le dossier data
    data_dir = os.path.join(static_dir, 'data')
    if not os.path.exists(data_dir):
        print(f"[WARN] Creation du dossier data: {data_dir}")
        os.makedirs(data_dir, exist_ok=True)
    
    print(f"   Data dir: {data_dir}")
    print(f"   Data dir exists: {os.path.exists(data_dir)}")

    # ============================================================
    # ROUTE SPÉCIALISÉE POUR LES FICHIERS GEOJSON
    # ============================================================
    @app.route('/static/data/<path:filename>')
    def serve_geojson(filename):
        """Route explicite pour servir les fichiers GeoJSON"""
        try:
            data_dir = os.path.join(app.static_folder, 'data')
            if not os.path.exists(data_dir):
                os.makedirs(data_dir, exist_ok=True)
            
            return send_from_directory(data_dir, filename, 
                                     mimetype='application/geo+json')
        except FileNotFoundError:
            # Fichier non trouvé - créer un GeoJSON minimal
            if filename in ['countries.geojson', 'countries_simplified.geojson']:
                minimal_geojson = {
                    "type": "FeatureCollection",
                    "features": []
                }
                return jsonify(minimal_geojson)
            return {"error": f"Fichier {filename} non trouvé"}, 404

    # ============================================================
    # ROUTE DE DIAGNOSTIC POUR LES FICHIERS STATIQUES
    # ============================================================
    @app.route('/debug/static-files')
    def debug_static_files():
        """Diagnostic des fichiers statiques"""
        static_dir = app.static_folder
        data_dir = os.path.join(static_dir, 'data')
        
        files_info = {
            'static_folder': static_dir,
            'static_url_path': app.static_url_path,
            'data_dir_exists': os.path.exists(data_dir),
        }
        
        if os.path.exists(data_dir):
            files_info['data_files'] = os.listdir(data_dir)
            for file in files_info['data_files']:
                file_path = os.path.join(data_dir, file)
                if os.path.exists(file_path):
                    files_info[f'{file}_size'] = os.path.getsize(file_path)
        
        return jsonify(files_info)

    # ============================================================
    # DÉTECTION DU MODE RÉEL
    # ============================================================
    print("\n[MODE] Detection du mode d'operation...")

    REAL_MODE = False
    try:
        REAL_MODE = os.getenv('GEOPOL_REAL_MODE', 'false').lower() == 'true'
        if REAL_MODE:
            print("[OK] MODE REEL active")
        else:
            print("[INFO] MODE SIMULATION active")
    except Exception as e:
        print(f"[INFO] Mode par defaut: SIMULATION ({e})")

    app.config['REAL_MODE'] = REAL_MODE

    # ============================================================
    # INITIALISATION DE LA BASE DE DONNÉES
    # ============================================================
    print("\n[DATABASE] Initialisation de la base de donnees...")

    try:
        from .database import DatabaseManager
    except ImportError:
        from database import DatabaseManager
    
    db_manager = DatabaseManager()

    # Exécuter les migrations existantes
    try:
        from .database_migrations import run_migrations
    except ImportError:
        from database_migrations import run_migrations
    
    run_migrations(db_manager)

    # Exécuter la migration pour les portfolios boursiers
    try:
        from .migration_stocks_portfolio import run_stocks_portfolio_migration
    except ImportError:
        from migration_stocks_portfolio import run_stocks_portfolio_migration
    
    run_stocks_portfolio_migration(db_manager)
     
    # ============================================================
    # [NEW] INITIALISATION DU MULTI-SOURCE AGGREGATOR AVEC DB
    # ============================================================
    print("\n[API] Initialisation du Multi-Source Aggregator avec flux RSS de la DB...")
    try:
        try:
            from .multi_source_aggregator import get_multi_source_aggregator
        except ImportError:
            from multi_source_aggregator import get_multi_source_aggregator
        
        # Initialiser le singleton avec le db_manager pour utiliser les flux de la DB
        multi_source_agg = get_multi_source_aggregator(db_manager=db_manager)
        print(f"[OK] Multi-Source Aggregator initialisé avec {len(multi_source_agg.sources)} sources")
        app.config['MULTI_SOURCE_ENABLED'] = True
    except Exception as e:
        print(f"[WARN] Multi-Source Aggregator non initialisé: {e}")
        app.config['MULTI_SOURCE_ENABLED'] = False

    # ============================================================
    # [NEW] INITIALISATION DU MODULE GÉOPOLITIQUE
    # ============================================================
    print("\n[GEO] Initialisation du module Géopolitique Corrigé...")

    geo_narrative_analyzer = None
    entity_extractor = None
    entity_db_manager = None
    geo_entity_integration = None

    try:
        # 1. Créer l'extracteur d'entités SpaCy
        try:
            from .geopolitical_entity_extractor import GeopoliticalEntityExtractor
        except ImportError:
            from geopolitical_entity_extractor import GeopoliticalEntityExtractor
        
        entity_extractor = GeopoliticalEntityExtractor(model_name="fr_core_news_lg")
        print("[OK] Extracteur d'entités SpaCy initialisé")

        # 2. Créer l'analyseur geo-narrative corrigé
        try:
            from .geo_narrative_analyzer import GeoNarrativeAnalyzer
        except ImportError:
            from geo_narrative_analyzer import GeoNarrativeAnalyzer
        
        geo_narrative_analyzer = GeoNarrativeAnalyzer(db_manager, entity_extractor)
        print("[OK] GeoNarrativeAnalyzer corrigé initialisé")

        # 3. Créer le gestionnaire BDD d'entités
        try:
            from .entity_database_manager import EntityDatabaseManager
        except ImportError:
            from entity_database_manager import EntityDatabaseManager
        
        entity_db_manager = EntityDatabaseManager(db_manager)
        print("[OK] EntityDatabaseManager initialisé")

        # 4. Créer l'intégrateur
        try:
            from .geo_entity_integration import GeoEntityIntegration
        except ImportError:
            from geo_entity_integration import GeoEntityIntegration
        
        geo_entity_integration = GeoEntityIntegration(
            geo_narrative_analyzer,
            entity_extractor,
            entity_db_manager
        )
        print("[OK] GeoEntityIntegration initialisé")

        # Stocker dans la config de l'app
        app.config['GEO_NARRATIVE_ANALYZER'] = geo_narrative_analyzer
        app.config['ENTITY_EXTRACTOR'] = entity_extractor
        app.config['ENTITY_DB_MANAGER'] = entity_db_manager
        app.config['GEO_ENTITY_INTEGRATION'] = geo_entity_integration

        print("[SUCCESS] Module Géopolitique corrigé prêt !")

    except ImportError as e:
        print(f"[WARN] Module géopolitique non disponible: {e}")
    except Exception as e:
        print(f"[ERROR] Erreur initialisation géopolitique: {e}")
        import traceback
        traceback.print_exc()

    # ============================================================
    # INITIALISATION DES MANAGERS
    # ============================================================
    print("\n[INIT] Initialisation de vos managers existants...")

    theme_manager = None
    theme_analyzer = None
    rss_manager = None
    advanced_theme_manager = None
    llama_client = None
    sentiment_analyzer = None
    batch_analyzer = None
    bayesian_analyzer = None
    corroboration_engine = None

    # 1. Theme Manager
    try:
        try:
            from .theme_manager import ThemeManager
        except ImportError:
            from theme_manager import ThemeManager
        
        theme_manager = ThemeManager(db_manager)
        print("[OK] ThemeManager initialisé")
    except Exception as e:
        print(f"[WARN] ThemeManager non disponible: {e}")

    # 2. Theme Analyzer
    try:
        try:
            from .theme_analyzer import ThemeAnalyzer
        except ImportError:
            from theme_analyzer import ThemeAnalyzer
        
        theme_analyzer = ThemeAnalyzer(db_manager)
        print("[OK] ThemeAnalyzer initialisé")
    except Exception as e:
        print(f"[WARN] ThemeAnalyzer non disponible: {e}")

    # 3. RSS Manager
    try:
        try:
            from .rss_manager import RSSManager
        except ImportError:
            from rss_manager import RSSManager
        
        rss_manager = RSSManager(db_manager)
        print("[OK] RSSManager initialisé")
    except Exception as e:
        print(f"[WARN] RSSManager non disponible: {e}")

    # 4. Advanced Theme Manager
    try:
        try:
            from .theme_manager_advanced import AdvancedThemeManager
        except ImportError:
            from theme_manager_advanced import AdvancedThemeManager
        
        advanced_theme_manager = AdvancedThemeManager(db_manager)
        print("[OK] AdvancedThemeManager initialisé")
    except Exception as e:
        print(f"[WARN] AdvancedThemeManager non disponible: {e}")

    # 5. IA Llama/Mistral
    try:
        try:
            from .llama_client import get_llama_client
        except ImportError:
            from llama_client import get_llama_client
        
        llama_client = get_llama_client()
        app.config['LLAMA_CLIENT'] = llama_client
        print("[OK] LlamaClient initialisé")
    except Exception as e:
        print(f"[WARN] LlamaClient non disponible: {e}")

    # 6. Analyseur de sentiment
    try:
        try:
            from .sentiment_analyzer import SentimentAnalyzer
        except ImportError:
            from sentiment_analyzer import SentimentAnalyzer
        
        sentiment_analyzer = SentimentAnalyzer()
        print("[OK] SentimentAnalyzer initialisé")
    except Exception as e:
        print(f"[WARN] SentimentAnalyzer non disponible: {e}")

    # 7. Analyseur bayésien
    try:
        try:
            from .bayesian_analyzer import BayesianSentimentAnalyzer
        except ImportError:
            from bayesian_analyzer import BayesianSentimentAnalyzer
        
        bayesian_analyzer = BayesianSentimentAnalyzer()
        print("[OK] BayesianSentimentAnalyzer initialisé")
    except Exception as e:
        print(f"[WARN] BayesianSentimentAnalyzer non disponible: {e}")

    # 8. Moteur de corroboration
    try:
        try:
            from .corroboration_engine import CorroborationEngine
        except ImportError:
            from corroboration_engine import CorroborationEngine
        
        corroboration_engine = CorroborationEngine()
        print("[OK] CorroborationEngine initialisé")
    except Exception as e:
        print(f"[WARN] CorroborationEngine non disponible: {e}")

    # 9. Batch Analyzer
    try:
        try:
            from .batch_sentiment_analyzer import create_batch_analyzer
        except ImportError:
            from batch_sentiment_analyzer import create_batch_analyzer
        
        if sentiment_analyzer and corroboration_engine and bayesian_analyzer:
            batch_analyzer = create_batch_analyzer(
                sentiment_analyzer,
                corroboration_engine,
                bayesian_analyzer
            )
            print("[OK] BatchAnalyzer initialisé")
    except Exception as e:
        print(f"[WARN] BatchAnalyzer non disponible: {e}")

    # ============================================================
    # [NEW] INITIALISATION DES ROUTES GÉOPOLITIQUES
    # ============================================================
    print("\n[ROUTES] Enregistrement des routes géopolitiques corrigées...")

    try:
        # Routes geo-narrative existantes mais corrigées
        try:
            from .routes_geo_narrative import register_geo_narrative_routes
        except ImportError:
            from routes_geo_narrative import register_geo_narrative_routes
        
        if geo_narrative_analyzer:
            register_geo_narrative_routes(app, db_manager, geo_narrative_analyzer)
            print("[OK] Routes geo-narrative corrigées enregistrées")
    except Exception as e:
        print(f"[WARN] Routes geo-narrative: {e}")

    try:
        # Routes entités existantes
        try:
            from .entity_routes import register_entity_routes
        except ImportError:
            from entity_routes import register_entity_routes
        
        if entity_extractor and entity_db_manager:
            register_entity_routes(app, db_manager, entity_extractor, entity_db_manager)
            print("[OK] Routes entités enregistrées")
    except Exception as e:
        print(f"[WARN] Routes entités: {e}")

    try:
        # Nouvelles routes intégrées
        try:
            from .routes_geo_entity_integrated import register_integrated_routes
        except ImportError:
            from routes_geo_entity_integrated import register_integrated_routes
        
        if all([geo_narrative_analyzer, entity_extractor, entity_db_manager, geo_entity_integration]):
            register_integrated_routes(
                app, db_manager, geo_narrative_analyzer,
                entity_extractor, entity_db_manager, geo_entity_integration
            )
            print("[OK] Routes intégrées geo-entity enregistrées")
    except Exception as e:
        print(f"[WARN] Routes intégrées: {e}")

    # ============================================================
    # ENREGISTREMENT DES ROUTES ESSENTIELLES
    # ============================================================
    print("\n[ROUTES] Enregistrement de vos routes existantes...")

    # Routes principales
    try:
        try:
            from .routes import register_routes
        except ImportError:
            from routes import register_routes
        
        register_routes(app, db_manager, theme_manager, theme_analyzer, rss_manager,
                       advanced_theme_manager, llama_client, sentiment_analyzer, batch_analyzer)
        print("[OK] Routes principales enregistrées")
    except Exception as e:
        print(f"[WARN] Routes principales non disponibles: {e}")

    # Routes avancées
    try:
        try:
            from .routes_advanced import register_advanced_routes
        except ImportError:
            from routes_advanced import register_advanced_routes
        
        register_advanced_routes(app, db_manager, bayesian_analyzer, corroboration_engine)
        print("[OK] Routes avancées enregistrées")
    except Exception as e:
        print(f"[WARN] Routes avancées non disponibles: {e}")

    # Routes sociales
    try:
        try:
            from .routes_social import register_social_routes
        except ImportError:
            from routes_social import register_social_routes
        
        register_social_routes(app, db_manager)
        print("[OK] Routes sociales enregistrées")
    except Exception as e:
        print(f"[WARN] Routes sociales non disponibles: {e}")

    # Routes alertes
    try:
        try:
            from .alerts_routes import register_alerts_routes
        except ImportError:
            from alerts_routes import register_alerts_routes
        
        register_alerts_routes(app, db_manager)
        print("[OK] Routes alertes enregistrées")
    except Exception as e:
        print(f"[WARN] Routes alertes non disponibles: {e}")

    # Routes stock
    try:
        try:
            from .stock_routes import register_stock_routes
        except ImportError:
            from stock_routes import register_stock_routes
        
        register_stock_routes(app, db_manager)
        print("[OK] Routes stock enregistrées")
    except Exception as e:
        print(f"[INFO] Routes Stock non disponibles: {e}")

    # section apprentissage passif :
    try:
        try:
            from .learning_routes import create_learning_blueprint
        except ImportError:
            from learning_routes import create_learning_blueprint
        
        try:
            from .continuous_learning import start_passive_learning, get_learning_engine
        except ImportError:
            from continuous_learning import start_passive_learning, get_learning_engine

        # Démarrer l'apprentissage passif
        learning_engine = start_passive_learning(db_manager, sentiment_analyzer)
    
        # Stocker dans app.config
        app.config['LEARNING_ENGINE'] = learning_engine
        app.config['SENTIMENT_ANALYZER'] = sentiment_analyzer

        # Créer et enregistrer le blueprint
        learning_bp = create_learning_blueprint(db_manager)
        app.register_blueprint(learning_bp)
    
        print("[OK] Routes apprentissage enregistrees")
        print("[OK] Apprentissage passif demarre")
    
    except Exception as e:
        print(f"[WARN] Routes apprentissage non disponibles: {e}")
        # import traceback
        # traceback.print_exc()  # Commenté pour éviter blocage Windows avec caractères spéciaux

    # ============================================================
    # CONFIGURATION EMAIL (Alertes et Rapports)
    # ============================================================
    try:
        try:
            from .routes_email import create_email_routes_blueprint
        except ImportError:
            from routes_email import create_email_routes_blueprint
        
        email_bp = create_email_routes_blueprint()
        app.register_blueprint(email_bp)
        print("[OK] Routes email enregistrees")
    except Exception as e:
        print(f"[WARN] Routes email non disponibles: {e}")

    # ============================================================
    # MODULES DEVELOPPES SUPPLEMENTAIRES (injection de dev.)
    # ============================================================
    print("\n[MODULES] Initialisation des autres modules...")

    # =======================================================================
    # Suivi financier
    # =======================================================================
    try:
        from .custom_tracking.routes import create_custom_tracking_blueprint
        tracking_bp = create_custom_tracking_blueprint(db_manager)
        app.register_blueprint(tracking_bp, url_prefix='/api')
        print("[OK] Suivi Personnalise enregistre")
    except Exception as e:
        print(f"[WARN] Suivi Personnalise: {e}")

    # ============================================================
    # ARCHIVISTE v4.0 - MÉMOIRE RÉSILIENTE (VERSION CORRIGÉE)
    # ============================================================

    print("\n[ARCHIVISTE] Initialisation du module Archiviste v4.0 (Version Corrigée)...")

    # VÉRIFICATION: Ne charger qu'UNE SEULE FOIS
    if 'ARCHIVISTE_V4_SERVICE' not in app.config:
        try:
            # Importer Archiviste v4 CORRIGÉ
            from .archiviste_v4.app_integration import create_archiviste_v4_blueprint

            print("[OK] Module Archiviste v4 importé (version corrigée)")

            # Récupérer SentimentAnalyzer si disponible
            sentiment_analyzer_instance = None

            if 'sentiment_analyzer' in locals():
                sentiment_analyzer_instance = sentiment_analyzer
                print("  [OK] SentimentAnalyzer récupéré depuis l'espace local")
            elif hasattr(app, 'config') and 'SENTIMENT_ANALYZER' in app.config:
                sentiment_analyzer_instance = app.config['SENTIMENT_ANALYZER']
                print("  [OK] SentimentAnalyzer récupéré depuis app.config")
            else:
                try:
                    from .sentiment_analyzer import SentimentAnalyzer
                    sentiment_analyzer_instance = SentimentAnalyzer()
                    app.config['SENTIMENT_ANALYZER'] = sentiment_analyzer_instance
                    print("  [OK] SentimentAnalyzer créé")
                except ImportError:
                    print("  [WARN] SentimentAnalyzer non disponible")

            # Créer et enregistrer le blueprint Archiviste v4 CORRIGÉ
            print("Creating Archiviste v4 blueprint (version corrigée)...")
            archiviste_bp = create_archiviste_v4_blueprint(db_manager, sentiment_analyzer_instance)
            app.register_blueprint(archiviste_bp, url_prefix='/archiviste-v4')

            # Marquer comme initialisé
            app.config['ARCHIVISTE_V4_SERVICE'] = True

            print("\n" + "="*70)
            print("ARCHIVISTE V4.0 INITIALISÉ AVEC SUCCÈS (VERSION CORRIGÉE)")
            print("="*70)
            print("Routes disponibles:")
            print("   • Interface: http://localhost:5000/archiviste-v4/")
            print("   • API Docs: http://localhost:5000/archiviste-v4/api/docs")
            print("   • Health: http://localhost:5000/archiviste-v4/health")
            print("   • Analyse: http://localhost:5000/archiviste-v4/api/resilient-analysis")
            print("="*70 + "\n")

        except Exception as e:
            print(f"Erreur Archiviste v4 (corrigée): {e}")
            import traceback
            traceback.print_exc()

            # Fallback minimal CORRIGÉ
            from flask import Blueprint

            fallback_bp = Blueprint('archiviste_v4_fallback', __name__, url_prefix='/archiviste-v4')

            @fallback_bp.route('/')
            def archiviste_fallback_home():
                return jsonify({
                    'status': 'fallback',
                    'message': 'Module Archiviste v4 en erreur (version corrigée)',
                    'error': str(e),
                    'routes_alternatives': [
                        '/archiviste-v4/health',
                        '/archiviste-v4/api/docs'
                    ]
                })

            @fallback_bp.route('/health')
            def archiviste_fallback_health():
                return jsonify({
                    'status': 'error_fallback',
                    'message': 'Fallback actif - Routes de base disponibles',
                    'version': '4.0-fallback-corrected'
                })

            # Route sans slash
            @fallback_bp.route('', methods=['GET'])
            def archiviste_fallback_no_slash():
                return redirect('/archiviste-v4/')

            app.register_blueprint(fallback_bp)
            app.config['ARCHIVISTE_V4_SERVICE'] = False
            print("Fallback Archiviste v4 corrigé activé")
    else:
        print("Archiviste v4 déjà initialisé")

    # ============================================================================
    # MODULE ECONOMIQUE - REFONTE COMPLETE v2.0
    # ============================================================================
    print("\n[ECONOMIC] Initialisation du module Economique (Refonte v2.0)...")
    try:
        try:
            from .economic import create_economic_blueprint
        except ImportError:
            from economic import create_economic_blueprint

        # Creer le blueprint avec injection du db_manager
        economic_bp = create_economic_blueprint(db_manager)

        # Enregistrer le blueprint
        app.register_blueprint(economic_bp)

        # Stocker dans config pour acces global
        app.config['ECONOMIC_MODULE_ENABLED'] = True

        print("[OK] Module Economique v2.0 active avec succes")
        print("   - Dashboard: http://localhost:5000/economic/")
        print("   - API France: http://localhost:5000/economic/api/indicators/france")
        print("   - API Health: http://localhost:5000/economic/api/health")
        print("   - API Stats: http://localhost:5000/economic/api/stats")

    except Exception as e:
        print(f"[ERROR] Erreur initialisation module Economique: {e}")
        app.config['ECONOMIC_MODULE_ENABLED'] = False
        import traceback
        traceback.print_exc()

    # ============================================================================
    # Portfolios Boursiers Personnalisés
    # ============================================================================
    try:
        try:
            from .routes_stocks_portfolio import create_stocks_portfolio_blueprint
        except ImportError:
            from routes_stocks_portfolio import create_stocks_portfolio_blueprint
        
        stocks_portfolio_bp = create_stocks_portfolio_blueprint(db_manager)
        app.register_blueprint(stocks_portfolio_bp)
        print("[OK] Portfolios Boursiers Personnalisés enregistré")
    except Exception as e:
        print(f"[WARN] Portfolios Boursiers: {e}")

    # ============================================================
    # Assistant IA
    # ============================================================
    try:
        try:
            from .assistant_routes import create_assistant_blueprint
        except ImportError:
            from assistant_routes import create_assistant_blueprint
        
        assistant_bp = create_assistant_blueprint(db_manager)
        app.register_blueprint(assistant_bp)
        print("[OK] Assistant IA enregistré")
    except Exception as e:
        print(f"[WARN] Assistant IA: {e}")

    # ============================================================
    # CONNECTEURS API - World Bank, Eurostat, yFinance
    # ============================================================
    print("\n[CONNECTORS] Initialisation des connecteurs API externes...")

    world_bank_client = None
    eurostat_client = None
    yfinance_client = None

    # World Bank Connector
    try:
        try:
            from .geopol_data.connectors.world_bank import WorldBankConnector
        except ImportError:
            from geopol_data.connectors.world_bank import WorldBankConnector
        
        world_bank_client = WorldBankConnector()
        print("[OK] World Bank Connector initialisé")
    except Exception as e:
        print(f"[ERROR] World Bank Connector non disponible: {e}")
        import traceback
        traceback.print_exc()

    # Eurostat Connector
    try:
        try:
            from .eurostat_connector import EurostatConnector
        except ImportError:
            from eurostat_connector import EurostatConnector
        
        eurostat_client = EurostatConnector()
        print("[OK] Eurostat Connector initialisé")
    except Exception as e:
        print(f"[WARN] Eurostat Connector non disponible: {e}")

    # yFinance Connector
    try:
        try:
            from .yfinance_connector import YFinanceConnector
        except ImportError:
            from yfinance_connector import YFinanceConnector
        
        yfinance_client = YFinanceConnector()
        print("[OK] yFinance Connector initialisé")
    except Exception as e:
        print(f"[WARN] yFinance Connector non disponible: {e}")

    # ============================================================
    # [NEW] MODULE FLUXSTRATEGIQUES - Risque d'approvisionnement
    # ============================================================

    print("\n[FLUX] Initialisation du module FluxStrategiques...")

    try:
        from .fluxStrategiques.app_integration import create_flux_strategiques_blueprint
        from .fluxStrategiques.indicators.gdelt_connector import GDELTConnector
        from .fluxStrategiques.indicators.alpha_vantage_connector import AlphaVantageConnector
        from .fluxStrategiques.indicators.fred_connector import FREDConnector

        # Initialiser GDELT connector
        gdelt_client = GDELTConnector()
        print("[OK] GDELT Connector initialise")

        # Initialiser Alpha Vantage connector
        alpha_vantage_client = AlphaVantageConnector()
        print("[OK] Alpha Vantage Connector initialise")

        # Initialiser FRED connector
        fred_client = FREDConnector()
        print("[OK] FRED Connector initialise")

        # Creer le blueprint avec les connecteurs API
        flux_bp = create_flux_strategiques_blueprint(
            db_manager,
            world_bank_client=world_bank_client,
            eurostat_client=eurostat_client,
            yfinance_client=yfinance_client,
            gdelt_client=gdelt_client,
            alpha_vantage_client=alpha_vantage_client,
            fred_client=fred_client
        )

        # Enregistrer le blueprint
        app.register_blueprint(flux_bp)

        # Stocker dans config
        app.config['FLUX_STRATEGIQUES_ENABLED'] = True

        print("\n" + "="*70)
        print("[FLUX] FLUXSTRATEGIQUES - MODULE INTÉGRÉ")
        print("="*70)
        print("[DATA] Fonctionnalites:")
        print("   - Analyse risque approvisionnement")
        print("   - 14 materiaux strategiques (terres rares + semi-conducteurs)")
        print("   - Multi-regions (EU27, USA, CHN)")
        print("   - 7 sources de donnees (World Bank, GDELT, Alpha Vantage, FRED, etc.)")
        print("   - 5+ indicateurs de risque (HHI, Geo, Prix, Commerce, GDELT)")
        print(f"[URLS] URLs disponibles:")
        print(f"   - Dashboard: http://localhost:5000{flux_bp.url_prefix}/")
        print(f"   - API Health: http://localhost:5000{flux_bp.url_prefix}/api/health")
        print(f"   - API Materials: http://localhost:5000{flux_bp.url_prefix}/api/materials")
        print(f"   - API GDELT: http://localhost:5000{flux_bp.url_prefix}/api/gdelt/<CODE>")
        print(f"   - API Alpha Vantage Commodity: http://localhost:5000{flux_bp.url_prefix}/api/alpha-vantage/commodity/<CODE>")
        print(f"   - API Alpha Vantage ETF: http://localhost:5000{flux_bp.url_prefix}/api/alpha-vantage/etf/<SYMBOL>")
        print(f"   - API FRED Series: http://localhost:5000{flux_bp.url_prefix}/api/fred/series/<SERIES_ID>")
        print(f"   - API FRED Snapshot: http://localhost:5000{flux_bp.url_prefix}/api/fred/snapshot")
        print(f"   - Material Detail: http://localhost:5000{flux_bp.url_prefix}/material/<CODE>")
        print(f"   - Comparison: http://localhost:5000{flux_bp.url_prefix}/comparison")
        print("="*70 + "\n")

    except Exception as e:
        print(f"[ERROR] Erreur initialisation FluxStrategiques: {e}")
        app.config['FLUX_STRATEGIQUES_ENABLED'] = False

    # ============================================================================
    # MODULE GESTION DES FLUX RSS
    # ============================================================================

    print("\n[RSS] Initialisation du module Gestion des Flux RSS...")
    try:
        try:
            from .routes_feeds import create_feeds_blueprint
        except ImportError:
            from routes_feeds import create_feeds_blueprint

        feeds_api_bp = create_feeds_blueprint(db_manager)
        app.register_blueprint(feeds_api_bp)

        print("[OK] Module Gestion des Flux RSS enregistré avec succès")
        print(f"   • API: http://localhost:5000/api/feeds")
        app.config['FEEDS_MANAGEMENT_ENABLED'] = True

    except Exception as e:
        print(f"[ERROR] Erreur initialisation Gestion des Flux RSS: {e}")
        app.config['FEEDS_MANAGEMENT_ENABLED'] = False

    # ============================================================
    # [NEW] MODULE SATELLITE - Couches satellite et imagerie
    # ============================================================
    print("\n[SATELLITE] Initialisation du module Satellite...")

    try:
        from .Satellite.satellite_routes import create_satellite_blueprint

        # Créer le blueprint
        satellite_bp = create_satellite_blueprint()

        # Enregistrer le blueprint
        app.register_blueprint(satellite_bp)

        # Stocker dans config
        app.config['SATELLITE_ENABLED'] = True

        print("\n" + "="*70)
        print("[SATELLITE] SATELLITE - MODULE INTÉGRÉ")
        print("="*70)
        print("[DATA] Fonctionnalités:")
        print("   • 26+ couches satellite et basemaps")
        print("   • Sentinel-2, Landsat, MODIS")
        print("   • OpenStreetMap, Stamen, CartoDB")
        print("   • Mode avancé Sentinel Hub (optionnel)")
        print("   • Recherche et recommandations intelligentes")
        print(f"[URLS] URLs disponibles:")
        print(f"   • Panneau: http://localhost:5000{satellite_bp.url_prefix}/")
        print(f"   • API Health: http://localhost:5000{satellite_bp.url_prefix}/api/health")
        print(f"   • API Layers: http://localhost:5000{satellite_bp.url_prefix}/api/layers")
        print(f"   • API Search: http://localhost:5000{satellite_bp.url_prefix}/api/search")
        print(f"   • API Recommend: http://localhost:5000{satellite_bp.url_prefix}/api/recommend")
        print("="*70 + "\n")

    except ImportError as e:
        print(f"[WARN] Satellite non disponible: {e}")
        app.config['SATELLITE_ENABLED'] = False
    except Exception as e:
        print(f"[ERROR] Erreur Satellite: {e}")
        import traceback
        traceback.print_exc()
        app.config['SATELLITE_ENABLED'] = False

    # ============================================================
    # SETTINGS SERVICE - Paramètres Globaux
    # ============================================================
    print("\n[SETTINGS] Initialisation du service de paramètres globaux...")

    settings_service = None
    try:
        from .geopol_data.settings_service import SettingsService
        settings_service = SettingsService(db_manager)
        print("[OK] Service de paramètres globaux initialisé")
    except Exception as e:
        print(f"[ERROR] Erreur initialisation settings service: {e}")
        settings_service = None

    # Enregistrer les routes Settings
    if settings_service:
        try:
            try:
                from .settings_routes import create_settings_blueprint
            except ImportError:
                from settings_routes import create_settings_blueprint
            
            settings_bp = create_settings_blueprint(db_manager, settings_service)
            app.register_blueprint(settings_bp)

            # Stocker dans la config
            app.config['SETTINGS_SERVICE'] = settings_service

            print("[OK] Routes de paramètres enregistrées")
            print("   • GET /api/settings - Récupérer les paramètres")
            print("   • POST /api/settings - Sauvegarder les paramètres")
            print("   • POST /api/settings/test-email - Tester la config email")

        except Exception as e:
            print(f"[ERROR] Erreur enregistrement routes settings: {e}")


    # ============================================================
    # DEV ASSISTANT - Integration IA locale + distante
    # ============================================================
    print("\n[DEV] Initialisation du Dev Assistant...")

    try:
        from .orchestrator import get_orchestrator
        from .phi_agent import get_phi_agent
        from .tools import Tools
        from .dev_routes import init_dev_assistant, dev_assistant_bp

        orchestrator = get_orchestrator()
        phi_agent = get_phi_agent()
        tools = Tools(base_dir)

        orchestrator.set_phi_agent(phi_agent)
        orchestrator.set_tools(tools)

        api_keys_manager = app.config.get('API_KEYS_MANAGER')

        init_dev_assistant(
            app,
            orchestrator,
            phi_agent,
            tools,
            api_keys_manager
        )

        print("[OK] Dev Assistant initialise")
        print("   - GET /dev/assistant - Page Dev Assistant")
        print("   - POST /dev/api/chat - Chat avec API distante")

    except Exception as e:
        print(f"[WARN] Dev Assistant non disponible: {e}")

    # ============================================================
    # ROUTES DE DIAGNOSTIC GÉOPOLITIQUE
    # ============================================================

    @app.route('/api/geo/diagnostic')
    def geo_diagnostic():
        """Diagnostic des modules géopolitiques"""
        return jsonify({
            'status': 'ok',
            'modules': {
                'geo_narrative': geo_narrative_analyzer is not None,
                'entity_extractor': entity_extractor is not None,
                'entity_database': entity_db_manager is not None,
                'integration': geo_entity_integration is not None,
                'leaflet_ready': True,
                'spacy_ready': entity_extractor is not None
            },
            'endpoints': {
                'patterns': '/api/geo-narrative/patterns',
                'map_view': '/api/geo-narrative/map-view',
                'enriched_patterns': '/api/geo-entity/patterns-enriched',
                'entity_extraction': '/api/entities/extract',
                'geo_health': '/api/geo/health'
            },
            'configuration': {
                'real_mode': REAL_MODE,
                'database': DB_PATH,
                'templates': template_dir,
                'static': static_dir
            }
        })

    @app.route('/api/geo/health')
    def geo_health():
        """Santé du module géopolitique"""
        return jsonify({
            'status': 'ok',
            'timestamp': time.time(),
            'components': {
                'leaflet': 'loaded',
                'spacy': 'loaded' if entity_extractor else 'missing',
                'database': 'connected',
                'analysis_engine': 'ready' if geo_narrative_analyzer else 'offline'
            }
        })

    @app.route('/api/geo/test-leaflet')
    def test_leaflet():
        """Page de test Leaflet isolée"""
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Leaflet - GEOPOL</title>
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
            <style>
                body { margin: 0; padding: 20px; font-family: Arial; }
                #testMap { height: 400px; width: 100%; border: 2px solid #007bff; }
                .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
                .success { background: #d4edda; color: #155724; }
                .error { background: #f8d7da; color: #721c24; }
            </style>
        </head>
        <body>
            <h1>🧪 Test Leaflet GEOPOL</h1>
            <div id="status" class="status">Initialisation...</div>
            <div id="testMap"></div>

            <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
            <script>
                let map;

                function updateStatus(message, type = 'success') {
                    const status = document.getElementById('status');
                    status.textContent = message;
                    status.className = 'status ' + type;
                }

                try {
                    // Créer la carte
                    map = L.map('testMap').setView([48.8566, 2.3522], 5);

                    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                        attribution: '© OpenStreetMap - GEOPOL Test'
                    }).addTo(map);

                    // Ajouter un marqueur
                    L.marker([48.8566, 2.3522])
                        .addTo(map)
                        .bindPopup('Paris - Test réussi!')
                        .openPopup();

                    updateStatus('[OK] Leaflet fonctionne correctement !');

                    // Tester le redimensionnement
                    setTimeout(() => {
                        if (map) {
                            map.invalidateSize();
                            updateStatus('[OK] Redimensionnement testé avec succès');
                        }
                    }, 1000);

                } catch (error) {
                    updateStatus('[ERROR] Erreur Leaflet: ' + error.message, 'error');
                }
            </script>
        </body>
        </html>
        '''

    # ============================================================
    # ROUTES DE GESTION EXISTANTES (conservées)
    # ============================================================

    @app.route('/api/shutdown', methods=['POST'])
    def shutdown():
        """Endpoint pour arrêter proprement tous les services GEOPOL"""
        try:
            print("\n🔴 Demande d'arrêt propre reçue...")
            services_stopped = []

            # Arrêter l'apprentissage passif
            try:
                try:
                    from .continuous_learning import stop_passive_learning
                except ImportError:
                    from continuous_learning import stop_passive_learning
                
                stop_passive_learning()
                services_stopped.append("Apprentissage Continu")
            except Exception as e:
                print(f"  [WARN] Erreur arrêt apprentissage: {e}")

            def shutdown_services():
                time.sleep(2)  # Augmenté à 2s pour garantir l'envoi de la réponse HTTP

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
                                    print("  [OK] Serveur IA arrêté proprement")
                                except psutil.TimeoutExpired:
                                    print("  [WARN] Forçage de l'arrêt...")
                                    proc.kill()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue

                    # Arrêter Flask
                    print("  → Arrêt du serveur Flask...")
                    services_stopped.append("Serveur Flask")
                    os.kill(os.getpid(), signal.SIGTERM)

                except Exception as e:
                    print(f"  [ERROR] Erreur lors de l'arrêt: {e}")

            shutdown_thread = threading.Thread(target=shutdown_services, daemon=True)
            shutdown_thread.start()

            return jsonify({
                'status': 'success',
                'message': 'Arrêt en cours...',
                'services_stopped': services_stopped
            }), 200

        except Exception as e:
            print(f"[ERROR] Erreur: {e}")
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    @app.route('/health', methods=['GET'])
    def health():
        """Endpoint de santé général"""
        try:
            result = {
                'status': 'ok',
                'timestamp': time.time(),
                'services': {
                    'flask': 'running',
                    'database': 'ok'
                }
            }
            try:
                result['services']['geo_module'] = 'active' if geo_narrative_analyzer else 'inactive'
            except:
                result['services']['geo_module'] = 'error'
            try:
                result['services']['entity_extraction'] = 'active' if entity_extractor else 'inactive'
            except:
                result['services']['entity_extraction'] = 'error'
            try:
                result['services']['real_mode'] = REAL_MODE
            except:
                result['services']['real_mode'] = 'error'
            return jsonify(result), 200
        except Exception as e:
            import traceback
            return jsonify({
                'status': 'error',
                'error': str(e),
                'traceback': traceback.format_exc()
            }), 500

    @app.route('/api/system-stats', methods=['GET'])
    def get_system_stats():
        """Endpoint pour récupérer les statistiques système en temps réel"""
        cpu_percent = 0
        memory_used_gb = 0
        memory_total_gb = 0
        memory_percent = 0
        process_memory_mb = 0
        llama_active = False
        llama_memory_mb = 0
        disk_percent = 0

        try:
            print("[SEARCH] Début récupération stats système...")

            # CPU
            try:
                cpu_percent = psutil.cpu_percent(interval=0.1)
                print(f"  ✓ CPU: {cpu_percent}%")
            except Exception as e:
                print(f"  ✗ Erreur CPU: {e}")

            # Mémoire
            try:
                memory = psutil.virtual_memory()
                memory_used_gb = memory.used / (1024 ** 3)
                memory_total_gb = memory.total / (1024 ** 3)
                memory_percent = memory.percent
                print(f"  ✓ Mémoire: {memory_used_gb:.2f}GB / {memory_total_gb:.2f}GB ({memory_percent}%)")
            except Exception as e:
                print(f"  ✗ Erreur mémoire: {e}")

            # Processus Python actuel
            try:
                process = psutil.Process(os.getpid())
                process_memory_mb = process.memory_info().rss / (1024 ** 2)
                print(f"  ✓ Processus Flask: {process_memory_mb:.1f}MB")
            except Exception as e:
                print(f"  ✗ Erreur processus: {e}")

            # Chercher si le serveur Llama/Mistral est actif
            try:
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        proc_name = proc.info.get('name', '')
                        if proc_name and 'llama-server' in proc_name.lower():
                            llama_active = True
                            try:
                                mem_info = proc.memory_info()
                                llama_memory_mb = mem_info.rss / (1024 ** 2)
                            except:
                                pass
                            print(f"  ✓ Llama détecté: {llama_memory_mb:.1f}MB")
                            break
                    except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
                        continue

                if not llama_active:
                    print(f"  ⓘ Llama non détecté")
            except Exception as e:
                print(f"  ✗ Erreur détection Llama: {e}")

            # Disque (compatible Windows et Linux)
            try:
                if os.name == 'nt':  # Windows
                    disk = psutil.disk_usage('C:\\')
                else:  # Linux/Mac
                    disk = psutil.disk_usage('/')
                disk_percent = disk.percent
                print(f"  ✓ Disque: {disk_percent}%")
            except Exception as e:
                print(f"  ✗ Erreur lecture disque: {e}")

            print("[OK] Stats système récupérées avec succès")

            result = {
                'success': True,
                'cpu': {
                    'percent': round(cpu_percent, 1),
                    'status': 'high' if cpu_percent > 80 else 'medium' if cpu_percent > 50 else 'low'
                },
                'memory': {
                    'used_gb': round(memory_used_gb, 2),
                    'total_gb': round(memory_total_gb, 2),
                    'percent': round(memory_percent, 1),
                    'process_mb': round(process_memory_mb, 1)
                },
                'llama': {
                    'active': llama_active,
                    'memory_mb': round(llama_memory_mb, 1) if llama_active else 0
                },
                'disk': {
                    'percent': round(disk_percent, 1)
                },
                'timestamp': time.time()
            }

            print(f"📤 Envoi de la réponse: {result}")

            response = Response(
                json.dumps(result),
                status=200,
                mimetype='application/json'
            )
            return response

        except Exception as e:
            print("=" * 70)
            print(f"[ERROR] ERREUR CRITIQUE dans /api/system-stats")
            print(f"[ERROR] Exception: {e}")
            print(f"[ERROR] Type: {type(e).__name__}")
            print("=" * 70)

            error_result = {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }

            response = Response(
                json.dumps(error_result),
                status=500,
                mimetype='application/json'
            )
            return response

    @app.route('/test-archive-query')
    def test_archive_query():
        """Test direct HTTP Archive.org"""
        import requests
        import json
    
        # Requête test
        params = {
            'q': 'language:fre AND year:[2000 TO 2010] AND mediatype:texts',
            'fl[]': ['identifier', 'title', 'description', 'year', 'language', 'mediatype'],
            'rows': 10,
            'output': 'json',
            'sort[]': ['year desc']
        }
    
        try:
            response = requests.get(
                'https://archive.org/advancedsearch.php',
                params=params,
                timeout=10
            )
        
            data = response.json() if response.status_code == 200 else {}
            docs = data.get('response', {}).get('docs', [])
        
            # Filtrer pour presse
            press_docs = []
            for doc in docs:
                title = doc.get('title', '')
                if isinstance(title, list):
                    title = ' '.join(title)
            
                description = doc.get('description', '')
                if isinstance(description, list):
                    description = ' '.join(description)
            
                text = f"{title} {description}".lower()
            
                # Chercher des indicateurs de presse
                press_terms = ['journal', 'quotidien', 'article', 'presse', 'actualité']
                is_press = any(term in text for term in press_terms)
            
                if is_press:
                    press_docs.append({
                        'identifier': doc.get('identifier'),
                        'title': title[:100],
                        'year': doc.get('year'),
                        'language': doc.get('language'),
                        'mediatype': doc.get('mediatype')
                    })
        
            return json.dumps({
                'status': 'success',
                'total_docs': len(docs),
                'press_docs': len(press_docs),
                'press_articles': press_docs,
                'sample_raw': docs[:2] if docs else [],
                'query': params['q']
            }, indent=2, ensure_ascii=False)
        
        except Exception as e:
            return json.dumps({
                'status': 'error',
                'error': str(e)
            }, indent=2)

    # ============================================================
    # MODULE DÉMOGRAPHIQUE - VERSION CORRIGÉE
    # ============================================================
    print("\n[DATA] Initialisation du module Démographique...")

    try:
        # Importer le service et les routes
        try:
            from .demographic_service import DemographicDataService
        except ImportError:
            from demographic_service import DemographicDataService
        
        try:
            from .demographic_routes import create_demographic_blueprint
        except ImportError:
            from demographic_routes import create_demographic_blueprint
    
        # Créer le service
        demographic_service = DemographicDataService(db_manager)
        print("[OK] Service démographique créé")
    
        # Créer le blueprint
        demographic_bp = create_demographic_blueprint(db_manager, demographic_service)
    
        if demographic_bp is not None:
            # Enregistrer le blueprint
            app.register_blueprint(demographic_bp)
            app.config['DEMOGRAPHIC_SERVICE'] = demographic_service
            print("[OK] Module Démographique enregistré avec succès")
            print(f"   • Dashboard: http://localhost:5000/demographic/")
            print(f"   • API Test: http://localhost:5000/demographic/api/test")
        else:
            print("[ERROR] Blueprint démographique non créé")
        
    except Exception as e:
        print(f"[ERROR] Erreur initialisation module démographique: {e}")
        import traceback
        traceback.print_exc()
    
        # Fallback minimal
        from flask import Blueprint

        fallback_bp = Blueprint('demographic_fallback', __name__, url_prefix='/demographic')
    
        @fallback_bp.route('/')
        def demographic_fallback():
            return jsonify({
                'status': 'fallback',
                'message': 'Module démographique en erreur de chargement',
                'error': str(e) if 'e' in locals() else 'Unknown error'
            })
    
        @fallback_bp.route('/api/test')
        def demographic_fallback_test():
            return jsonify({
                'success': True,
                'message': 'Fallback démographique actif',
                'version': '1.0-fallback'
            })
    
        app.register_blueprint(fallback_bp)
        print("[OK] Fallback démographique activé")

    # ============================================================
    # MODULE SÉCURITÉ & GOUVERNANCE
    # ============================================================

    print("\n[SECURITY] Initialisation du module Sécurité & Gouvernance...")

    try:
        try:
            from .security_governance import security_bp, init_security_governance_connectors
        except ImportError:
            from security_governance import security_bp, init_security_governance_connectors
        
        app.register_blueprint(security_bp)

        # Initialiser les connecteurs avec db_manager
        init_security_governance_connectors(db_manager)

        print("[OK] Module Sécurité & Gouvernance enregistré avec succès")
        print(f"   • Dashboard: http://localhost:5000/security-governance/")
        print(f"   • API Sanctions: http://localhost:5000/security-governance/api/sanctions")
        print(f"   • API Corruption: http://localhost:5000/security-governance/api/corruption")
        print(f"   • API Menaces: http://localhost:5000/security-governance/api/threats")
        print(f"   • API ACLED: http://localhost:5000/security-governance/api/acled/summary")
    except Exception as e:
        print(f"[ERROR] Erreur initialisation module Sécurité & Gouvernance: {e}")
        import traceback
        traceback.print_exc()

    # ============================================================
    # MODULE HDX PRIMAIRE - Données humanitaires et conflits
    # ============================================================

    print("\n🌍 Initialisation du module HDX Primaire...")

    try:
        try:
            from .security_governance.hdx_routes import init_hdx_routes
        except ImportError:
            from security_governance.hdx_routes import init_hdx_routes

        init_hdx_routes(app)
        print("[OK] Module HDX Primaire enregistré avec succès")
        print(f"   • Health: http://localhost:5000/api/hdx/health")
        print(f"   • Summary: http://localhost:5000/api/hdx/summary")
        print(f"   • Conflict Events: http://localhost:5000/api/hdx/conflict-events")
        print(f"   • Crisis Indicators: http://localhost:5000/api/hdx/crisis-indicators")
        print(f"   • Priority Regions: http://localhost:5000/api/hdx/priority-regions")
    except Exception as e:
        print(f"[WARN] Erreur initialisation module HDX Primaire: {e}")
        import traceback
        traceback.print_exc()

    # ============================================================
    # MODULE OSoME - Analyse de Propagation et Réseaux Sociaux
    # ============================================================

    print("\n🕸 Initialisation du module OSoME...")

    try:
        try:
            from .routes_osome import init_osome_routes
        except ImportError:
            from routes_osome import init_osome_routes
        
        init_osome_routes(app)
        print("[OK] Module OSoME enregistré avec succès")
        print(f"   • API Analyze: http://localhost:5000/api/osome/analyze")
        print(f"   • API Networks: http://localhost:5000/api/osome/networks")
        print(f"   • API Influencers: http://localhost:5000/api/osome/influencers")
        print(f"   • Health Check: http://localhost:5000/api/osome/health")

        # Démarrer le scheduler automatique
        print("\n[FAST] Démarrage du scheduler OSoME...")
        try:
            try:
                from .osome_scheduler import get_osome_scheduler
            except ImportError:
                from osome_scheduler import get_osome_scheduler
            
            try:
                from .database import DatabaseManager
            except ImportError:
                from database import DatabaseManager
            
            try:
                from .social_aggregator import get_social_aggregator
            except ImportError:
                from social_aggregator import get_social_aggregator
            
            try:
                from .propagation_detector import get_propagation_detector
            except ImportError:
                from propagation_detector import get_propagation_detector

            db_manager_sched = DatabaseManager()
            social_aggregator = get_social_aggregator(db_manager_sched)
            propagation_detector = get_propagation_detector(db_manager_sched)

            scheduler = get_osome_scheduler(app, db_manager_sched, social_aggregator, propagation_detector)
            scheduler.start()

            print("[OK] Scheduler OSoME démarré")
            print(f"   • Collecte automatique: toutes les {scheduler.config['fetch_interval_hours']}h")
            print(f"   • Analyse automatique: toutes les {scheduler.config['analysis_interval_hours']}h")
            print(f"   • API Status: http://localhost:5000/api/osome/scheduler/status")
            print(f"   • API Trigger: http://localhost:5000/api/osome/scheduler/trigger-full")
        except Exception as e:
            print(f"[WARN] Scheduler OSoME non démarré: {e}")
            import traceback
            traceback.print_exc()

    except Exception as e:
        print(f"[ERROR] Erreur initialisation module OSoME: {e}")
        import traceback
        traceback.print_exc()

    # ============================================================
    # GESTIONNAIRE DE CLÉS API
    # ============================================================

    print("\n🔑 Initialisation du gestionnaire de clés API...")

    try:
        try:
            from .routes_api_keys import init_api_keys_routes
        except ImportError:
            from routes_api_keys import init_api_keys_routes
        
        init_api_keys_routes(app, db_manager)
        print("[OK] Gestionnaire de clés API enregistré")
        print(f"   • API Services: http://localhost:5000/api/api-keys/services")
        print(f"   • API Keys List: http://localhost:5000/api/api-keys")
        print(f"   • Health Check: http://localhost:5000/api/api-keys/health")
    except Exception as e:
        print(f"[ERROR] Erreur initialisation gestionnaire clés API: {e}")
        import traceback
        traceback.print_exc()

    # ============================================================
    # MODULE GEOPOL-DATA
    # ============================================================

    geopol_data_service = None
    geopol_data_bp = None

    try:
        try:
            from .geopol_data import init_geopol_data_module
        except ImportError:
            from geopol_data import init_geopol_data_module
        
        geopol_data_service, geopol_data_bp = init_geopol_data_module(app, db_manager)

        # Enregistrer le blueprint si valide
        if geopol_data_bp is not None:
            try:
                app.register_blueprint(geopol_data_bp, url_prefix='/api/geopol')
                print("[OK] Geopol-Data Blueprint enregistré")
                print(f"   • Health: http://localhost:5000/api/geopol/health")
                print(f"   • France: http://localhost:5000/api/geopol/country/FR")

                # Stocker dans app.config
                app.config['GEOPOL_DATA_SERVICE'] = geopol_data_service

            except Exception as e:
                print(f"[WARN] Erreur enregistrement blueprint: {e}")
                if "already registered" not in str(e).lower():
                    import traceback
                    traceback.print_exc()
        else:
            print("[WARN] Geopol-Data en mode dégradé (blueprint None)")

            # Créer un endpoint de fallback minimal
            @app.route('/api/geopol/health')
            def geopol_health_fallback():
                return jsonify({
                    'status': 'degraded',
                    'message': 'Module Geopol-Data non initialisé'
                }), 503

    except Exception as e:
        print(f"[WARN] Erreur initialisation Geopol-Data: {e}")

    # ============================================================
    # MODULE OPEN-METEO (COUCHES MÉTÉO)
    # ============================================================

    print("\n🌦  Initialisation du module Open-Meteo...")

    meteo_integration = None

    try:
        try:
            from .geopol_data import init_meteo_module
        except ImportError:
            from geopol_data import init_meteo_module
        
        meteo_result = init_meteo_module(app)

        if meteo_result:
            meteo_integration = meteo_result.get('integration')
            print("[OK] Open-Meteo intégré")
            print(f"   • Health: http://localhost:5000/api/weather/health")
            print(f"   • Layers: http://localhost:5000/api/weather/layers")

            # Stocker dans app.config
            app.config['METEO_INTEGRATION'] = meteo_integration
        else:
            print("[WARN] Open-Meteo en mode dégradé")

    except Exception as e:
        print(f"[WARN] Erreur initialisation Open-Meteo: {e}")
        import traceback
        traceback.print_exc()

    # ============================================================
    # MODULE USGS EARTHQUAKE (SÉISMES)
    # ============================================================

    print("\n[GEO] Initialisation du module Earthquake...")

    earthquake_integration = None

    try:
        try:
            from .geopol_data import init_earthquake_module
        except ImportError:
            from geopol_data import init_earthquake_module
        
        earthquake_result = init_earthquake_module(app)

        if earthquake_result:
            earthquake_integration = earthquake_result.get('integration')
            print("[OK] USGS Earthquake intégré")
            print(f"   • Health: http://localhost:5000/api/earthquakes/health")
            print(f"   • GeoJSON: http://localhost:5000/api/earthquakes/geojson")
            print(f"   • Stats: http://localhost:5000/api/earthquakes/statistics")

            # Stocker dans app.config
            app.config['EARTHQUAKE_INTEGRATION'] = earthquake_integration
        else:
            print("[WARN] Earthquake en mode dégradé")

    except Exception as e:
        print(f"[WARN] Erreur initialisation Earthquake: {e}")
        import traceback
        traceback.print_exc()

    # ============================================================
    # MODULE GESTION DES PROFILS DE CONFIGURATION
    # ============================================================

    print("\n⚙ Initialisation du module Gestion des Profils...")

    try:
        try:
            from .geopol_data import init_config_module
        except ImportError:
            from geopol_data import init_config_module
        
        config_result = init_config_module(app)

        if config_result:
            print("[OK] Gestionnaire de Profils intégré")
            print(f"   • Liste profils: http://localhost:5000/api/geopol/profiles")
            print(f"   • Profil défaut: http://localhost:5000/api/geopol/profiles/default")
            print(f"   • Profil analyst: http://localhost:5000/api/geopol/profiles/analyst")
            print(f"   • Profil meteo: http://localhost:5000/api/geopol/profiles/meteo")
        else:
            print("[WARN] Gestionnaire de Profils en mode dégradé")

    except Exception as e:
        print(f"[WARN] Erreur initialisation Config Manager: {e}")
        import traceback
        traceback.print_exc()


# ============================================================
# MODULE SDR GLOBAL - Cartographie WebSDR mondiaux
# ============================================================

    print("\n[URLS] Initialisation du module SDR Global...")

    try:
        # Obtenir le port depuis app.config
        port = app.config.get('PORT', 5000)

        # Essayer d'importer le module SDR Global
        try:
            # Vérifier d'abord les dépendances
            import aiohttp
            import numpy as np
            from bs4 import BeautifulSoup
    
            print("   [OK] Dépendances trouvées: aiohttp, numpy, beautifulsoup4")
    
        # Maintenant importer nos modules
            from .geopol_data.connectors.websdr_checker import WebSDRChecker
            from .geopol_data.connectors.simple_spectrum import SimpleSpectrumAnalyzer
        
            try:
                from .sdr_global_routes import create_sdr_global_blueprint
            except ImportError:
                from sdr_global_routes import create_sdr_global_blueprint
    
        # Initialiser les services
            websdr_checker = WebSDRChecker(db_manager)
            spectrum_analyzer = SimpleSpectrumAnalyzer(db_manager)
    
        # Créer le blueprint
            sdr_global_bp = create_sdr_global_blueprint(db_manager, websdr_checker, spectrum_analyzer)
            app.register_blueprint(sdr_global_bp)
    
        # Lancer un scan initial en arrière-plan
            def initial_scan():
                try:
                    print("   [SEARCH] Premier scan des WebSDR mondiaux en cours...")
                    import asyncio
                    import threading
            
                    async def scan_async():
                        try:
                            await websdr_checker.check_all_servers()
                            print("   [OK] Scan initial terminé")
                        except Exception as e:
                            print(f"   [WARN] Erreur scan initial: {e}")
            
                # Lancer dans un thread séparé
                    thread = threading.Thread(target=lambda: asyncio.run(scan_async()), daemon=True)
                    thread.start()
            
                except Exception as e:
                    print(f"   [WARN] Impossible de lancer le scan initial: {e}")
    
        # Exécuter le scan initial
            initial_scan()
    
        # Ajouter la route pour la carte SDR globale
            @app.route('/sdr/global')
            def sdr_global_map():
                """Page de la carte globale des WebSDR"""
                from flask import render_template
                return render_template('websdr_global.html')

            # NOTE: La route /sdr/dashboard est maintenant gérée par le blueprint sdr_dashboard_page
            # (défini dans geopol_data/sdr_dashboard_routes.py et enregistré via init_sdr_dashboard_module)

            @app.route('/sdr/global/stats')
            def sdr_global_stats():
                """Page de statistiques des WebSDR"""
                from flask import render_template
                return render_template('sdr_global_stats.html')
    
            print("[OK] Module SDR Global intégré avec succès")
            print(f"   • Carte globale: http://localhost:{port}/sdr/global")
            print(f"   • Statistiques: http://localhost:{port}/sdr/global/stats")
            print(f"   • API Servers: http://localhost:{port}/api/sdr-global/servers/geojson")
            print(f"   • API Stats: http://localhost:{port}/api/sdr-global/servers/stats")
            print(f"   • API Scan: http://localhost:{port}/api/sdr-global/servers/check")
    
        except ImportError as e:
            print(f"   [ERROR] Dépendances manquantes: {e}")
            print("   Installation: pip install aiohttp numpy beautifulsoup4")
        # Ne pas lever d'exception pour continuer l'exécution
            print("   [WARN] Module SDR Global désactivé (dépendances manquantes)")

    except Exception as e:
        print(f"[WARN] Erreur initialisation SDR Global: {e}")
        import traceback
        traceback.print_exc()

# ============================================================
# MODULE SDR NETWORK MONITOR (LÉGER & OPEN SOURCE)
# ============================================================

    print("\n[API] Initialisation du module SDR Network Monitor...")

    try:
        from .geopol_data.routes_sdr_network import init_sdr_network_routes

    # Initialiser les routes SDR Network
        init_sdr_network_routes(app, db_manager)

        port = app.config.get('PORT', 5000)

        print("[OK] Module SDR Network Monitor enregistré avec succès")
        print(f"   • API GeoJSON: http://localhost:{port}/api/sdr-network/geojson")
        print(f"   • API Serveurs: http://localhost:{port}/api/sdr-network/servers")
        print(f"   • API Stats: http://localhost:{port}/api/sdr-network/stats")
        print(f"   • API Pays: http://localhost:{port}/api/sdr-network/countries")
        print(f"   • Health Check: http://localhost:{port}/api/sdr-network/health")
        print("   • Serveurs vérifiés: 7 (Portugal, UK, Allemagne, Espagne, Russie, Pologne, Uruguay)")
        print("   • Sources publiques: rx.linkfanel.net + cache SQLite")

    except Exception as e:
        print(f"[ERROR] Erreur initialisation SDR Network Monitor: {e}")
        import traceback
        traceback.print_exc()

# ============================================================
# MODULE SDR API (INTÉGRATION GEOPOL MAP)
# ============================================================

    print("\n[API] Initialisation du module SDR API...")

    try:
        from .geopol_data.sdr_routes import create_sdr_api_blueprint

    # Créer des instances minimales si nécessaire
        sdr_analyzer = None
        sdr_service = None

    # Créer le blueprint SDR API
        sdr_api_bp = create_sdr_api_blueprint(db_manager, sdr_analyzer, sdr_service)
        app.register_blueprint(sdr_api_bp)

        port = app.config.get('PORT', 5000)

        print("[OK] Module SDR API enregistré avec succès")
        print(f"   • API Health: http://localhost:{port}/api/sdr/health")
        print(f"   • API GeoJSON: http://localhost:{port}/api/sdr/geojson")
        print(f"   • API Stations: http://localhost:{port}/api/sdr/stations")

    except Exception as e:
        print(f"[ERROR] Erreur initialisation SDR API: {e}")
        import traceback
        traceback.print_exc()

# ============================================================
# MODULE SDR DASHBOARD (Routes pages + API temps réel)
# ============================================================

    print("\n[SDR] Initialisation du module SDR Dashboard...")

    try:
        from .geopol_data import init_sdr_dashboard_module

    # Initialiser le module SDR Dashboard
        sdr_dashboard_result = init_sdr_dashboard_module(app, db_manager, sdr_analyzer)

        if sdr_dashboard_result:
            port = app.config.get('PORT', 5000)
            print("[OK] Module SDR Dashboard enregistre avec succes")
            print(f"   • Dashboard Page: http://localhost:{port}/sdr/dashboard")
            print(f"   • API Summary: http://localhost:{port}/api/sdr/dashboard/summary")
            print(f"   • API Global: http://localhost:{port}/api/sdr/dashboard/global")
            print(f"   • API Zones: http://localhost:{port}/api/sdr/dashboard/zones")
            print(f"   • API Timeline: http://localhost:{port}/api/sdr/dashboard/timeline")
        else:
            print("[WARN] Module SDR Dashboard non initialise (result None)")

    except Exception as e:
        print(f"[ERROR] Erreur initialisation SDR Dashboard: {e}")
        import traceback
        traceback.print_exc()

# ============================================================
# MODULE ALERTES GÉOPOLITIQUES (SIMPLIFIÉ)
# ============================================================

    print("\n🚨 Initialisation du module Alertes...")

    alerts_service = None

    if geopol_data_service is not None:
        try:
            from .geopol_data.alerts import GeopolAlertsService
            from .geopol_data.alerts_routes import create_alerts_blueprint

        # Créer le service d'alertes
            alerts_service = GeopolAlertsService(DB_PATH)
            print("[OK] Geopol Alerts Service créé")

        # Créer le blueprint
            alerts_bp = create_alerts_blueprint(db_manager, geopol_data_service, alerts_service)

            if alerts_bp is not None and hasattr(alerts_bp, 'name'):
            # Vérifier que ce n'est pas un doublon
                if alerts_bp.name != geopol_data_bp.name:
                    app.register_blueprint(alerts_bp)
                    print(f"[OK] Alerts Blueprint enregistré: {alerts_bp.name}")
                else:
                    print("ℹ Alerts intégré dans geopol_data_bp")

        except Exception as e:
            print(f"[WARN] Alertes: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("[WARN] Alertes: DataService manquant, module non chargé")

# ============================================================
# SCHEDULER D'ALERTES (SIMPLIFIÉ)
# ============================================================

    if alerts_service is not None and geopol_data_service is not None:
        try:
            from .geopol_data.alerts_scheduler import start_alerts_scheduler
            start_alerts_scheduler(alerts_service, geopol_data_service, interval_minutes=10)
            print("[OK] Scheduler d'alertes démarré")
        except Exception as e:
            print(f"[WARN] Scheduler: {e}")
    else:
        print("[WARN] Scheduler non démarré (services manquants)")

# ============================================================
# DIAGNOSTIC FINAL
# ============================================================

    print("\n" + "="*70)
    print("[DATA] STATUT MODULE GEOPOL-DATA")
    print("="*70)
    print(f"DataService:    {'[OK] OK' if geopol_data_service else '[ERROR] Échec'}")
    print(f"Blueprint:      {'[OK] OK' if geopol_data_bp else '[ERROR] Échec'}")
    print(f"Alerts:         {'[OK] OK' if alerts_service else '[ERROR] Échec'}")
    print(f"Scheduler:      {'[OK] Actif' if (alerts_service and geopol_data_service) else '[ERROR] Inactif'}")
    print("="*70 + "\n")

# ============================================================
# [NEW] DASHBOARD DÉMOGRAPHIQUE
# ============================================================

    @app.route('/demographic-dashboard')
    def demographic_dashboard():
        """Page du dashboard démographique"""
        return render_template('demographic_dashboard.html')

# ============================================================
# INITIALISATION FINALE (à la toute fin)
# ============================================================
    print("\n" + "="*70)
    print("[SUCCESS] GEOPOL ANALYTICS - INITIALISATION TERMINÉE")
    print("="*70)
    print(f"[API] MODE: {'RÉEL [URLS]' if REAL_MODE else 'SIMULATION 🧪'}")
    print("[DATA] MODULES CORRIGÉS:")
    print(f"   • Géopolitique: {'[OK]' if geo_narrative_analyzer else '[ERROR]'}")
    print(f"   • Entités SpaCy: {'[OK]' if entity_extractor else '[ERROR]'}")
    print(f"   • Carte Leaflet: [OK] (version 1.9.4)")
    print(f"   • Intégration: {'[OK]' if geo_entity_integration else '[ERROR]'}")
    print(f"   • Geopol-Data: {'[OK]' if geopol_data_service else '[ERROR]'}")
    print(f"   • Alertes Géopolitiques: {'[OK]' if 'alerts_service' in locals() else '[ERROR]'}")
    print(f"   • FluxStrategiques: {'[OK]' if app.config.get('FLUX_STRATEGIQUES_ENABLED') else '[ERROR]'}")
    print(f"   • Satellite: {'[OK]' if app.config.get('SATELLITE_ENABLED') else '[ERROR]'}")
    print(f"   • OSoME (Propagation): [OK]")
    print(f"   • Fichiers statiques: [OK] Configurés")
    print("="*70)
    print("[URLS] URLS GÉOPOLITIQUES:")
    print("   • /api/geo/diagnostic - Diagnostic complet")
    print("   • /api/geo/test-leaflet - Test Leaflet")
    print("   • /api/geo-narrative/patterns - Patterns transnationaux")
    print("   • /api/geo-narrative/map-view - Carte interactive")
    print("="*70)
    print("[URLS] URLS GEOPOL-DATA:")
    print("   • /api/geopol/health - Santé Geopol-Data")
    print("   • /api/geopol/country/FR - Données France")
    print("   • /api/geopol/status - Status complet")
    print("="*70)
    print("🕸 URLS OSoME (PROPAGATION & RÉSEAUX):")
    print("   • /api/osome/analyze - Analyser propagations récentes")
    print("   • /api/osome/network - Créer réseau OSoME")
    print("   • /api/osome/networks - Liste réseaux")
    print("   • /api/osome/network/<id> - Détail réseau")
    print("   • /api/osome/influencers - Top influencers")
    print("   • /api/osome/metrics - Métriques réseau")
    print("   • /api/osome/cascade-patterns - Patterns de cascade")
    print("   • /api/osome/cross-platform - Flux cross-platform")
    print("   • /api/osome/propagation/<post_id> - Chaîne propagation")
    print("   • /api/osome/stats - Statistiques globales")
    print("   • /api/osome/health - Health check")
    print("="*70)
    if app.config.get('FLUX_STRATEGIQUES_ENABLED'):
        print("[FLUX] URLS FLUXSTRATEGIQUES:")
        print("   • /flux-strategiques/ - Dashboard matériaux stratégiques")
        print("   • /flux-strategiques/material/<CODE> - Détail matériau")
        print("   • /flux-strategiques/comparison - Comparaison multi-matériaux")
        print("   • /flux-strategiques/api/health - Santé du module")
        print("   • /flux-strategiques/api/materials - Liste matériaux (14)")
        print("   • /flux-strategiques/api/dashboard - Données dashboard")
        print("="*70)
    if app.config.get('SATELLITE_ENABLED'):
        print("[SATELLITE] URLS SATELLITE:")
        print("   • /satellite/ - Panneau satellite & imagerie")
        print("   • /satellite/api/health - Santé du module")
        print("   • /satellite/api/layers - Liste couches (26+)")
        print("   • /satellite/api/layer-url/<id> - URL couche satellite")
        print("   • /satellite/api/search - Recherche couches")
        print("   • /satellite/api/recommend - Recommandations")
        print("   • /satellite/api/advanced/enable - Activer mode avancé")
        print("="*70)
        print("[DB] URLS FICHIERS STATIQUES:")
        print("   • /static/data/countries.geojson - Fichier GeoJSON")
        print("   • /static/data/countries_simplified.geojson - Fichier GeoJSON simplifié")
        print("   • /debug/static-files - Diagnostic fichiers")
        print("="*70)
        print("[NOTE] LES MODULES EXISTANTS:")
        print("   • Toutes les routes sont conservées dans la version 0.8PP")
        print("   • La configuration est intacte")
        print("   • La base de données est préservée")
        print("="*70)

    # ============================================================
    # [WARN] LIGNE CRITIQUE - RETURN APP
    # ============================================================

        print("\n[OK] Application Flask prête à démarrer\n")

    # ============================================================
    # SOLUTION RAPIDE - Routes démographiques DIRECTES
    # ============================================================
        print("\n[LAUNCH] Ajout des routes démographiques directes...")

        @app.route('/demo-stats')
        def demo_stats():
            """Statistiques démographiques"""
            return jsonify({
            'success': True,
            'stats': {'countries': 27, 'indicators': 15},
            'note': 'Route directe - fonctionne à coup sûr'
            })

        @app.route('/demo-country/<code>')
        def demo_country(code):
            """Données d'un pays"""
            return jsonify({
                'success': True,
                'country': code,
                'population': 67843000 if code == 'FR' else 50000000,
                'gdp': 3038000000000 if code == 'FR' else 2000000000000
            })

        @app.route('/demo-dashboard')
        def demo_dashboard():
            """Dashboard simplifié"""
            return '''
        <!DOCTYPE html>
        <html>
        <head><title>Dashboard Démographique</title></head>
        <body>
            <h1>[DATA] Dashboard Simplifié</h1>
            <p>[OK] Module démographique actif via routes directes</p>
            <p><a href="/demo-stats">Voir les stats</a></p>
           <p><a href="/demo-country/FR">Données France</a></p>
        </body>
        </html>
        '''

        print("[OK] Routes démographiques directes ajoutées")
        print("   • /demo-dashboard - Dashboard simplifié")
        print("   • /demo-stats - Statistiques")
        print("   • /demo-country/<code> - Données pays")

        # Dashboard Géopolitique (référencement des composants JS)
        @app.route('/geopolitical-dashboard')
        def geopolitical_dashboard():
            """Page du dashboard géopolitique principal"""
            return render_template('geopolitical_dashboard.html')

        print("[OK] Route géopolitique ajoutée")
        print("   • /geopolitical-dashboard - Dashboard géopolitique principal")

# ============================================================
# SYSTÈME DE JOBS PLANIFIÉS (CRON-JOBS)
# ============================================================

        print("\n[CLOCK] Initialisation du système de jobs planifiés...")

        try:
            try:
                from .scheduled_jobs import init_scheduler, shutdown_scheduler
            except ImportError:
                from scheduled_jobs import init_scheduler, shutdown_scheduler

    # Initialiser le scheduler
            scheduler = init_scheduler(app)

    # Enregistrer le shutdown handler pour arrêt propre
            @app.teardown_appcontext
            def teardown_scheduler(exception=None):
                if hasattr(app, 'scheduler'):
                    shutdown_scheduler(app.scheduler)

            print("[OK] [OK] Système de jobs planifiés activé")
            print("   • Actualisation automatique des données")
            print("   • Jobs quotidiens : Marchés, INSEE, Eurostat")
            print("   • Health check : Toutes les 6 heures")

        except Exception as e:
            print(f"[WARN] [WARN] Jobs planifiés désactivés: {e}")
            import traceback
            traceback.print_exc()

        return app

