"""
Module Sécurité & Gouvernance - VERSION ENRICHIE
Surveillance sanctions, corruption et menaces cyber
Intégration complète des 3 plugins newarchi
+ UN OCHA/HDX (crises, conflits, humanitaire)
+ Global Incident Map (terrorisme, cyberattaques, tensions)
"""

from flask import Blueprint, render_template, jsonify, request
import requests
from datetime import datetime
import logging
import json
import sys
import os
import concurrent.futures
import time

# Import des nouveaux connecteurs
try:
    from .ocha_hdx_connector import get_ocha_hdx_connector
    ocha_connector = get_ocha_hdx_connector()
    logger = logging.getLogger(__name__)
    logger.info("[OK] OCHA/HDX Connector chargé")
except Exception as e:
    logger = logging.getLogger(__name__)
    logger.warning(f"[WARN] Erreur chargement OCHA Connector: {e}")
    ocha_connector = None

try:
    from .global_incident_connector import get_global_incident_connector
    incident_connector = get_global_incident_connector()
    logger.info("[OK] Global Incident Connector chargé")
except Exception as e:
    logger.warning(f"[WARN] Erreur chargement Global Incident Connector: {e}")
    incident_connector = None

try:
    from .acled_connector import ACLEDConnector, get_acled_connector
    # Initialiser immédiatement avec les variables d'environnement
    acled_connector = get_acled_connector()
    if acled_connector.email and acled_connector.password:
        logger.info("[OK] ACLED Connector initialise avec credentials .env")
    else:
        logger.warning("[WARN] ACLED Connector initialise SANS credentials (API limitee)")
except Exception as e:
    logger.warning(f"[WARN] Erreur import ACLED Connector: {e}")
    acled_connector = None

# UCDP (Uppsala Conflict Data Program) - remplacement ACLED Archive
try:
    from .ucdp_connector import UCDPConnector
    ucdp_connector = UCDPConnector()
    logger.info("[OK] UCDP Connector initialisé (remplacement ACLED Archive)")
except Exception as e:
    logger.warning(f"[WARN] Erreur import UCDP Connector: {e}")
    ucdp_connector = None

# ACLED Archive désactivé (remplacé par UCDP)
acled_archive_connector = None

# ConflictService - Service unifié pour remplacer ACLED
try:
    from .conflict_service import get_conflict_service
    conflict_service = get_conflict_service()
    if conflict_service.is_available():
        logger.info("[OK] ConflictService initialisé (UCDP comme source)")
    else:
        logger.warning("[WARN] ConflictService initialisé mais aucune source disponible")
except Exception as e:
    logger.warning(f"[WARN] Erreur import ConflictService: {e}")
    conflict_service = None

# AlienVault OTX (Open Threat Exchange) - Threat Intelligence
try:
    from .alienvault_otx_connector import AlienVaultOTXConnector, get_alienvault_otx_connector
    alienvault_connector = get_alienvault_otx_connector()
    # Vérifier la clé API
    if alienvault_connector.api_key:
        logger.info("[OK] AlienVault OTX Connector initialisé avec clé API")
    else:
        logger.warning("[WARN] AlienVault OTX Connector initialisé SANS clé API (fonctionnalités limitées)")
except Exception as e:
    logger.warning(f"[WARN] Erreur import AlienVault OTX Connector: {e}")
    alienvault_connector = None

# OpenSanctions - Sanctions, PEPs, Crime
try:
    from .opensanctions_connector import OpenSanctionsConnector, get_opensanctions_connector
    opensanctions_connector = get_opensanctions_connector()
    if opensanctions_connector.api_key:
        logger.info("[OK] OpenSanctions Connector initialise avec cle API")
    else:
        logger.info("[OK] OpenSanctions Connector initialise (sans cle API - rate limit)")
except Exception as e:
    logger.warning(f"[WARN] Erreur import OpenSanctions Connector: {e}")
    opensanctions_connector = None

# Dashboard Analytics
try:
    from .analytics_dashboard import get_security_analytics_dashboard
    security_analytics_dashboard = get_security_analytics_dashboard()
    logger.info("[OK] Security Analytics Dashboard chargé")
except Exception as e:
    logger.warning(f"[WARN] Erreur chargement Analytics Dashboard: {e}")
    security_analytics_dashboard = None

# Cache Monitoring
try:
    from .cache_monitoring import get_cache_monitor
    cache_monitor = get_cache_monitor()
    logger.info("[OK] Cache Monitor chargé")
except Exception as e:
    logger.warning(f"[WARN] Erreur chargement Cache Monitor: {e}")
    cache_monitor = None

# Report Generator
try:
    from .report_generator import get_report_generator
    report_generator = get_report_generator()
    logger.info("[OK] Report Generator chargé")
except Exception as e:
    logger.warning(f"[WARN] Erreur chargement Report Generator: {e}")
    report_generator = None

# Circuit Breaker Manager
try:
    from .circuit_breaker import CircuitBreakerManager
    circuit_breaker_manager = CircuitBreakerManager()
    logger.info("[OK] Circuit Breaker Manager chargé")
except Exception as e:
    logger.warning(f"[WARN] Erreur chargement Circuit Breaker Manager: {e}")
    circuit_breaker_manager = None

# ============================================================================
# PLUGINS NEWARCHI - CORRECTION TOTALE
# ============================================================================

import sys
import os
import logging

logger = logging.getLogger(__name__)

# Ajouter le chemin des plugins newarchi
current_dir = os.path.dirname(os.path.abspath(__file__))
geo_root = os.path.dirname(os.path.dirname(current_dir))  # Remonter a GEO/
newarchi_dir = os.path.join(geo_root, 'newarchi')
corruption_path = os.path.join(newarchi_dir, 'plugins', 'corruption-monitoring')
sanctions_path = os.path.join(newarchi_dir, 'plugins', 'sanctions-monitor')
threat_path = os.path.join(newarchi_dir, 'plugins', 'threat-intelligence')

logger.info(f"[PLUGIN] Chemin corruption: {corruption_path}")
logger.info(f"[PLUGIN] Chemin sanctions: {sanctions_path}")
logger.info(f"[PLUGIN] Chemin threat: {threat_path}")

# Vérifier l'existence des répertoires
for name, path in [('corruption', corruption_path), ('sanctions', sanctions_path), ('threat', threat_path)]:
    if os.path.exists(path):
        logger.info(f"[PLUGIN] Répertoire {name} trouvé: {path}")
    else:
        logger.warning(f"[PLUGIN] Répertoire {name} introuvable: {path}")

# Import dynamique pour éviter le cache des modules
import importlib.util

def load_plugin_from_path(plugin_path, plugin_name):
    """Charge un plugin depuis son chemin avec importlib pour éviter le cache"""
    plugin_file = os.path.join(plugin_path, 'plugin.py')
    if not os.path.exists(plugin_file):
        logger.warning(f"[PLUGIN] Fichier plugin.py introuvable: {plugin_file}")
        return None

    # Créer un nom de module unique pour éviter les collisions
    module_name = f"newarchi_plugin_{plugin_name}"

    spec = importlib.util.spec_from_file_location(module_name, plugin_file)
    if spec is None:
        logger.warning(f"[PLUGIN] Impossible de créer spec pour: {plugin_file}")
        return None

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    return module.Plugin({})

# CORRUPTION PLUGIN
try:
    logger.info(f"[PLUGIN] Import corruption depuis: {corruption_path}")
    corruption_plugin = load_plugin_from_path(corruption_path, 'corruption')
    if corruption_plugin:
        logger.info("[OK] Plugin Corruption Monitoring chargé")
    else:
        logger.warning("[WARN] Plugin Corruption Monitoring non chargé")
except Exception as e:
    logger.warning(f"[WARN] Erreur chargement Corruption Plugin: {e}", exc_info=True)
    corruption_plugin = None

# SANCTIONS PLUGIN
try:
    logger.info(f"[PLUGIN] Import sanctions depuis: {sanctions_path}")
    sanctions_plugin = load_plugin_from_path(sanctions_path, 'sanctions')
    if sanctions_plugin:
        logger.info("[OK] Plugin Sanctions Monitor chargé")
    else:
        logger.warning("[WARN] Plugin Sanctions Monitor non chargé")
except Exception as e:
    logger.warning(f"[WARN] Erreur chargement Sanctions Plugin: {e}", exc_info=True)
    sanctions_plugin = None

# THREAT PLUGIN
try:
    logger.info(f"[PLUGIN] Import threat depuis: {threat_path}")
    threat_plugin = load_plugin_from_path(threat_path, 'threat')
    if threat_plugin:
        logger.info("[OK] Plugin Threat Intelligence chargé")
    else:
        logger.warning("[WARN] Plugin Threat Intelligence non chargé")
except Exception as e:
    logger.warning(f"[WARN] Erreur chargement Threat Plugin: {e}", exc_info=True)
    threat_plugin = None

# Créer le blueprint
security_bp = Blueprint(
    'security_governance',
    __name__,
    url_prefix='/security-governance',
    template_folder='../templates'
)


@security_bp.route('/')
def dashboard():
    """Page principale du dashboard Sécurité & Gouvernance"""
    return render_template('security_governance.html')


@security_bp.route('/circuit-breakers')
def circuit_breakers_dashboard():
    """Dashboard de monitoring des circuit breakers"""
    return render_template('circuit_breaker_dashboard.html')


@security_bp.route('/api/health')
def health():
    """Endpoint de santé du module"""
    return jsonify({
        'status': 'ok',
        'module': 'security_governance',
        'plugins': {
            'sanctions': 'loaded' if sanctions_plugin else 'error',
            'corruption': 'loaded' if corruption_plugin else 'error',
            'threats': 'loaded' if threat_plugin else 'error'
        },
        'connectors': {
            'ocha_hdx': 'loaded' if ocha_connector else 'error',
            'ucdp': 'loaded' if ucdp_connector else 'error',
            'acled': 'loaded' if (acled_archive_connector or acled_connector) else 'error',
            'acled_archive': 'not_loaded',  # Remplacé par UCDP
            'acled_api': 'loaded' if acled_connector else 'not_loaded',
            'global_incident': 'loaded' if incident_connector else 'error',
            'alienvault_otx': 'loaded' if alienvault_connector else 'not_loaded',
            'alienvault_otx_api_key': 'configured' if (alienvault_connector and alienvault_connector.api_key) else 'missing',
            'opensanctions': 'loaded' if opensanctions_connector else 'not_loaded',
            'opensanctions_api_key': 'configured' if (opensanctions_connector and opensanctions_connector.api_key) else 'missing'
        },
        'timestamp': datetime.now().isoformat()
    })


@security_bp.route('/api/circuit-breakers')
def circuit_breakers():
    """Endpoint pour les statistiques des circuit breakers"""
    if circuit_breaker_manager:
        stats = circuit_breaker_manager.get_all_stats()
        return jsonify({
            'status': 'ok',
            'circuit_breakers': stats,
            'count': len(stats),
            'timestamp': datetime.now().isoformat()
        })
    else:
        return jsonify({
            'status': 'error',
            'message': 'Circuit breaker manager not available',
            'timestamp': datetime.now().isoformat()
        }), 500


@security_bp.route('/api/widget-data')
def get_widget_data():
    """Endpoint pour les données du widget dashboard principal"""
    total_start_time = time.time()
    try:
        widget_data = {
            'active_conflicts': 0,
            'corruption_index': 'N/A',
            'recent_sanctions': 0,
            'timestamp': datetime.now().isoformat()
        }
        sources_used = []
        plugin_results = {}
        plugin_errors = {}

        # ========== EXÉCUTION PARALLÈLE DES PLUGINS AVEC TIMEOUT ==========
        start_time = time.time()

        def run_plugin_with_timeout(plugin_name, plugin_instance, plugin_func):
            """Exécute un plugin avec timeout de 5 secondes"""
            try:
                start_plugin_time = time.time()
                result = plugin_func()
                elapsed = time.time() - start_plugin_time
                logger.info(f"[WIDGET] Plugin {plugin_name} exécuté en {elapsed:.2f}s")
                return plugin_name, result, elapsed
            except Exception as e:
                elapsed = time.time() - start_plugin_time
                logger.warning(f"[WIDGET] Plugin {plugin_name} erreur après {elapsed:.2f}s: {e}")
                return plugin_name, None, elapsed

        # Préparer les tâches pour les plugins disponibles
        tasks = []
        if sanctions_plugin:
            tasks.append(('sanctions', sanctions_plugin, sanctions_plugin.run))
        if corruption_plugin:
            tasks.append(('corruption', corruption_plugin, corruption_plugin.run))

        # Exécuter les plugins en parallèle avec ThreadPoolExecutor
        if tasks:
            with concurrent.futures.ThreadPoolExecutor(max_workers=len(tasks)) as executor:
                # Soumettre toutes les tâches
                future_to_plugin = {
                    executor.submit(run_plugin_with_timeout, name, plugin, func): name
                    for name, plugin, func in tasks
                }

                # Attendre les résultats avec timeout global de 5 secondes
                try:
                    for future in concurrent.futures.as_completed(future_to_plugin, timeout=5):
                        plugin_name = future_to_plugin[future]
                        try:
                            name, result, elapsed = future.result()
                            if result is not None:
                                plugin_results[plugin_name] = result
                            else:
                                plugin_errors[plugin_name] = f"Timeout ou erreur après {elapsed:.2f}s"
                        except concurrent.futures.TimeoutError:
                            plugin_errors[plugin_name] = "Timeout après 5s"
                        except Exception as e:
                            plugin_errors[plugin_name] = f"Erreur: {str(e)}"
                except concurrent.futures.TimeoutError:
                    # Timeout global - certains plugins peuvent encore être en cours
                    logger.warning(f"[WIDGET] Timeout global après 5s, {len(tasks)} plugins en cours")
                    for plugin_name in future_to_plugin.values():
                        if plugin_name not in plugin_results and plugin_name not in plugin_errors:
                            plugin_errors[plugin_name] = "Timeout global après 5s"

        total_plugin_time = time.time() - start_time
        logger.info(f"[WIDGET] Exécution plugins terminée en {total_plugin_time:.2f}s - "
                   f"{len(plugin_results)} succès, {len(plugin_errors)} échecs")

        # ========== TRAITEMENT DES RÉSULTATS DES PLUGINS ==========
        # 1. Sanctions via plugin
        if 'sanctions' in plugin_results:
            sanctions_result = plugin_results['sanctions']
            if sanctions_result.get('status') == 'success':
                sanctions_data = sanctions_result.get('data', [])
                widget_data['recent_sanctions'] = len(sanctions_data)
                sources_used.append('sanctions-plugin')
                logger.info(f"[WIDGET] Sanctions plugin: {widget_data['recent_sanctions']} entrées")
        elif 'sanctions' in plugin_errors:
            logger.warning(f"[WIDGET] Plugin sanctions échoué: {plugin_errors['sanctions']}")

        # 2. Corruption via plugin
        if 'corruption' in plugin_results:
            corruption_result = plugin_results['corruption']
            if corruption_result.get('status') == 'success':
                corruption_data = corruption_result.get('data', [])
                # Calculer score moyen si possible
                scores = [item.get('score', 0) for item in corruption_data if isinstance(item.get('score'), (int, float))]
                if scores:
                    avg_score = sum(scores) / len(scores)
                    widget_data['corruption_index'] = round(avg_score, 1)
                    sources_used.append('corruption-plugin')
                    logger.info(f"[WIDGET] Corruption plugin: score moyen {widget_data['corruption_index']}")
        elif 'corruption' in plugin_errors:
            logger.warning(f"[WIDGET] Plugin corruption échoué: {plugin_errors['corruption']}")

        # ========== FALLBACK: CONNECTEURS EXTERNES ==========
        if security_analytics_dashboard:
            overview = security_analytics_dashboard.get_global_overview()
            if overview.get('success') and overview.get('available'):
                # Conflits actifs (événements des 30 derniers jours)
                conflicts_section = overview.get('sections', {}).get('conflicts', {})
                if conflicts_section.get('status') == 'success' and widget_data['active_conflicts'] == 0:
                    widget_data['active_conflicts'] = conflicts_section.get('statistics', {}).get('total_events', 0)
                    sources_used.append('ucdp')

                # Score corruption moyen (CPI) - seulement si pas déjà défini par plugin
                if widget_data['corruption_index'] == 'N/A':
                    corruption_section = overview.get('sections', {}).get('corruption', {})
                    if corruption_section.get('status') == 'success':
                        cpi_avg = corruption_section.get('cpi', {}).get('average_score', 0)
                        wb_avg = corruption_section.get('world_bank', {}).get('average_score', 0)
                        avg_score = cpi_avg if cpi_avg > 0 else wb_avg
                        if avg_score > 0:
                            widget_data['corruption_index'] = round(avg_score, 1)
                            sources_used.append('cpi-worldbank')

                # Sanctions récentes (total entrées OFAC) - seulement si pas déjà défini par plugin
                if widget_data['recent_sanctions'] == 0:
                    sanctions_section = overview.get('sections', {}).get('sanctions', {})
                    if sanctions_section.get('status') == 'success':
                        widget_data['recent_sanctions'] = sanctions_section.get('total_entries', 0)
                        sources_used.append('ofac')

        # ========== FALLBACK FINAL: DONNÉES FACTICES INTELLIGENTES ==========
        # Si aucune donnée réelle, utiliser des données factices plausibles
        if widget_data['active_conflicts'] == 0:
            widget_data['active_conflicts'] = 15  # Estimation plausible
            sources_used.append('mock-conflicts')

        if widget_data['corruption_index'] == 'N/A':
            widget_data['corruption_index'] = 43  # Score moyen mondial
            sources_used.append('mock-corruption')

        if widget_data['recent_sanctions'] == 0:
            widget_data['recent_sanctions'] = 7  # Nombre plausible
            sources_used.append('mock-sanctions')

        # Préparer réponse
        sources_str = ', '.join(sources_used) if sources_used else 'mock'
        total_time = time.time() - total_start_time

        logger.info(f"[WIDGET] Requête terminée en {total_time:.2f}s - "
                   f"Sources: {sources_str}, Données réelles: {'mock' not in sources_str}")

        return jsonify({
            'success': True,
            'data': widget_data,
            'sources': sources_str,
            'has_real_data': 'mock' not in sources_str,
            'execution_time': round(total_time, 2)
        })
    except Exception as e:
        logger.error(f"Erreur widget data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ============================================================================
# PLUGIN 1: SANCTIONS MONITOR - INTÉGRATION COMPLÈTE
# ============================================================================

@security_bp.route('/api/sanctions')
def get_sanctions():
    """
    Récupère les données de sanctions internationales RÉELLES
    Sources: OFAC, EU, Douanes FR via plugin newarchi
    """
    try:
        if sanctions_plugin:
            logger.info(f"[SANCTIONS] Plugin trouvé: id={id(sanctions_plugin)}, name={getattr(sanctions_plugin, 'name', 'no name attr')}, type={type(sanctions_plugin).__name__}")
            # Utiliser le plugin pour données réelles
            plugin_result = sanctions_plugin.run()
            logger.info(f"[SANCTIONS] Résultat plugin: status={plugin_result.get('status')}, plugin_field={plugin_result.get('plugin')}, data_len={len(plugin_result.get('data', []))}")
            if plugin_result['status'] == 'success':
                return jsonify({
                    'success': True,
                    'timestamp': plugin_result['timestamp'],
                    'data': plugin_result['data'],
                    'metrics': plugin_result['metrics'],
                    'carte_douanes': plugin_result.get('carte_douanes', None),
                    'sources': ['Douanes Françaises', 'OFAC SDN', 'UE Sanctions'],
                    'plugin_status': 'active'
                })

        # Fallback si plugin non disponible
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'data': get_sanctions_fallback(),
            'plugin_status': 'fallback'
        })

    except Exception as e:
        logger.error(f"Erreur récupération sanctions: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'fallback_data': get_sanctions_fallback()
        }), 500


@security_bp.route('/api/sanctions/douanes-map')
def get_douanes_map():
    """Récupère l'iframe de la carte Douanes Françaises"""
    try:
        if sanctions_plugin:
            plugin_result = sanctions_plugin.run()
            carte_data = plugin_result.get('carte_douanes', None)

            if carte_data:
                return jsonify({
                    'success': True,
                    'carte': carte_data
                })

        return jsonify({
            'success': True,
            'carte': {
                'url': 'https://www.google.com/maps/d/embed?mid=198oYCCQQSKzPt7GmXaeWHvBgt-Q&ehbc=2E312F',
                'width': 640,
                'height': 480,
                'titre': 'Carte des sanctions internationales - Douanes Françaises'
            }
        })

    except Exception as e:
        logger.error(f"Erreur carte Douanes: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@security_bp.route('/api/sanctions/ofac')
def get_ofac_data():
    """Récupère spécifiquement les données OFAC SDN"""
    try:
        if sanctions_plugin:
            # Appeler le plugin avec un payload spécifique
            plugin_result = sanctions_plugin.run({'source': 'ofac'})

            # Filtrer uniquement les données OFAC
            ofac_data = [
                d for d in plugin_result.get('data', [])
                if d.get('source') == 'OFAC SDN'
            ]

            return jsonify({
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'source': 'OFAC SDN',
                'data': ofac_data,
                'count': len(ofac_data)
            })

        return jsonify({'success': False, 'error': 'Plugin non disponible'}), 503

    except Exception as e:
        logger.error(f"Erreur OFAC: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


def get_sanctions_fallback():
    """Données de fallback pour les sanctions"""
    return [
        {
            'pays_cible': 'Russie',
            'type': 'pays',
            'sanction_type': 'Économique',
            'secteurs_impactes': 'Énergie, Finance, Défense',
            'date_entree_vigueur': '2022-02-24',
            'statut': 'Actif',
            'source': 'Douanes Françaises',
            'severite': 'Élevée'
        },
        {
            'pays_cible': 'Corée du Nord',
            'type': 'pays',
            'sanction_type': 'Embargo',
            'secteurs_impactes': 'Armement, Luxe',
            'date_entree_vigueur': '2006-10-09',
            'statut': 'Actif',
            'source': 'ONU',
            'severite': 'Élevée'
        }
    ]


# ============================================================================
# PLUGIN 2: CORRUPTION MONITORING - INTÉGRATION COMPLÈTE
# ============================================================================

@security_bp.route('/api/corruption')
def get_corruption():
    """
    Récupère les indices de corruption via plugin newarchi
    Sources: Transparency International CPI, FATF, World Bank
    """
    try:
        if corruption_plugin:
            # Utiliser le plugin pour données enrichies
            plugin_result = corruption_plugin.run()

            if plugin_result['status'] == 'success':
                return jsonify({
                    'success': True,
                    'timestamp': plugin_result['timestamp'],
                    'data': plugin_result['data'],
                    'metrics': plugin_result['metrics'],
                    'sources': ['Transparency International', 'FATF', 'World Bank'],
                    'plugin_status': 'active'
                })

        # Fallback si plugin non disponible
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'data': get_corruption_fallback(),
            'plugin_status': 'fallback'
        })

    except Exception as e:
        logger.error(f"Erreur récupération corruption: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'fallback_data': get_corruption_fallback()
        }), 500


@security_bp.route('/api/corruption/cpi')
def get_cpi_indices():
    """Récupère uniquement les indices CPI (Corruption Perception Index)"""
    try:
        if corruption_plugin:
            plugin_result = corruption_plugin.run({'corruption_type': 'indices'})

            # Filtrer uniquement les indices CPI
            cpi_data = [
                d for d in plugin_result.get('data', [])
                if d.get('type_corruption') == 'Indice Perception'
            ]

            return jsonify({
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'source': 'Transparency International',
                'data': cpi_data,
                'count': len(cpi_data)
            })

        return jsonify({'success': False, 'error': 'Plugin non disponible'}), 503

    except Exception as e:
        logger.error(f"Erreur CPI: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@security_bp.route('/api/corruption/cases')
def get_major_cases():
    """Récupère les affaires de corruption majeures"""
    try:
        if corruption_plugin:
            plugin_result = corruption_plugin.run({'corruption_type': 'cases'})

            # Filtrer uniquement les affaires majeures
            cases_data = [
                d for d in plugin_result.get('data', [])
                if d.get('type_corruption') == 'Affaire Majeure'
            ]

            return jsonify({
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'data': cases_data,
                'count': len(cases_data),
                'note': 'Affaires majeures: 1MDB Malaisie, State Capture Afrique du Sud, etc.'
            })

        return jsonify({'success': False, 'error': 'Plugin non disponible'}), 503

    except Exception as e:
        logger.error(f"Erreur cases: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@security_bp.route('/api/corruption/laundering')
def get_money_laundering():
    """Récupère les données de blanchiment d'argent"""
    try:
        if corruption_plugin:
            plugin_result = corruption_plugin.run({'corruption_type': 'laundering'})

            # Filtrer uniquement le blanchiment
            laundering_data = [
                d for d in plugin_result.get('data', [])
                if d.get('type_corruption') == 'Blanchiment Argent'
            ]

            return jsonify({
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'source': 'FATF',
                'data': laundering_data,
                'count': len(laundering_data),
                'note': 'Panama Papers, listes FATF, surveillance accrue'
            })

        return jsonify({'success': False, 'error': 'Plugin non disponible'}), 503

    except Exception as e:
        logger.error(f"Erreur laundering: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


def get_corruption_fallback():
    """Données de fallback pour la corruption"""
    return [
        {
            'pays': 'Danemark',
            'type_corruption': 'Indice Perception',
            'score_corruption': 90,
            'classement_mondial': 1,
            'tendance': 'Stable',
            'secteurs_risque': 'Aucun secteur majeur',
            'efforts_lutte': 'Institutions fortes, transparence'
        },
        {
            'pays': 'Somalie',
            'type_corruption': 'Indice Perception',
            'score_corruption': 12,
            'classement_mondial': 180,
            'tendance': 'Amélioration lente',
            'secteurs_risque': 'Secteur public, Sécurité, Aide humanitaire',
            'efforts_lutte': 'Débuts institutions anti-corruption'
        }
    ]


# ============================================================================
# PLUGIN 3: THREAT INTELLIGENCE - INTÉGRATION COMPLÈTE
# ============================================================================

@security_bp.route('/api/threats')
def get_threats():
    """
    Récupère les menaces cyber et hybrides via plugin newarchi
    Sources: AlienVault OTX, CVE Database
    """
    try:
        if threat_plugin:
            # Utiliser le plugin pour données en temps réel
            plugin_result = threat_plugin.run()

            if plugin_result['status'] == 'success':
                return jsonify({
                    'success': True,
                    'timestamp': plugin_result['timestamp'],
                    'data': plugin_result['data'],
                    'metrics': plugin_result['metrics'],
                    'sources': ['AlienVault OTX', 'CVE Database'],
                    'plugin_status': 'active'
                })

        # Fallback si plugin non disponible
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'data': get_threats_fallback(),
            'plugin_status': 'fallback'
        })

    except Exception as e:
        logger.error(f"Erreur récupération menaces: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'fallback_data': get_threats_fallback()
        }), 500


@security_bp.route('/api/threats/apt')
def get_apt_threats():
    """Récupère uniquement les menaces APT (Advanced Persistent Threats)"""
    try:
        if threat_plugin:
            plugin_result = threat_plugin.run({'threat_type': 'apt'})

            # Filtrer uniquement les APT
            apt_data = [
                d for d in plugin_result.get('data', [])
                if d.get('type') == 'APT'
            ]

            return jsonify({
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'data': apt_data,
                'count': len(apt_data),
                'note': 'APT28 Fancy Bear, APT29 Cozy Bear, Lazarus Group, etc.'
            })

        return jsonify({'success': False, 'error': 'Plugin non disponible'}), 503

    except Exception as e:
        logger.error(f"Erreur APT: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@security_bp.route('/api/threats/cve')
def get_cve_vulnerabilities():
    """Récupère les vulnérabilités CVE récentes"""
    try:
        if threat_plugin:
            plugin_result = threat_plugin.run({'threat_type': 'cve'})

            # Filtrer uniquement les CVE
            cve_data = [
                d for d in plugin_result.get('data', [])
                if d.get('type') == 'Vulnerabilité'
            ]

            return jsonify({
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'source': 'NVD CVE Database',
                'data': cve_data,
                'count': len(cve_data),
                'critical_count': len([d for d in cve_data if float(d.get('severite', 0)) >= 9.0])
            })

        return jsonify({'success': False, 'error': 'Plugin non disponible'}), 503

    except Exception as e:
        logger.error(f"Erreur CVE: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@security_bp.route('/api/threats/iocs')
def get_iocs():
    """Récupère les Indicateurs de Compromission (IOCs)"""
    try:
        if threat_plugin:
            plugin_result = threat_plugin.run()

            # Extraire les IOCs de chaque menace
            iocs_summary = []
            for threat in plugin_result.get('data', []):
                ioc_count = threat.get('iocs', 0)
                if ioc_count > 0:
                    iocs_summary.append({
                        'menace': threat.get('menace'),
                        'iocs_count': ioc_count,
                        'severite': threat.get('severite'),
                        'type': threat.get('type')
                    })

            return jsonify({
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'data': iocs_summary,
                'total_iocs': sum(d['iocs_count'] for d in iocs_summary),
                'note': 'IOCs incluent: IPs, domaines, hashes, patterns réseau'
            })

        return jsonify({'success': False, 'error': 'Plugin non disponible'}), 503

    except Exception as e:
        logger.error(f"Erreur IOCs: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


def get_threats_fallback():
    """Données de fallback pour les menaces"""
    return [
        {
            'menace': 'APT28 Fancy Bear',
            'type': 'APT',
            'severite': 'High',
            'acteurs': 'APT28, Cozy Bear',
            'cibles': 'Gouvernement, Military, Critical Infrastructure',
            'iocs': 15,
            'premiere_observation': '2024-12-20',
            'derniere_activite': '2024-12-20'
        },
        {
            'menace': 'CVE-2024-1234',
            'type': 'Vulnerabilité',
            'severite': 'High',
            'acteurs': 'N/A',
            'cibles': 'Windows, Linux',
            'iocs': 0,
            'premiere_observation': '2024-12-15',
            'derniere_activite': '2024-12-16'
        }
    ]


# ============================================================================
# ROUTES GLOBALES ET STATISTIQUES
# ============================================================================

@security_bp.route('/api/stats')
def get_global_stats():
    """Récupère les statistiques globales de tous les plugins"""
    try:
        stats = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'modules': {}
        }

        # Stats Sanctions
        if sanctions_plugin:
            sanctions_result = sanctions_plugin.run()
            stats['modules']['sanctions'] = sanctions_result.get('metrics', {})

        # Stats Corruption
        if corruption_plugin:
            corruption_result = corruption_plugin.run()
            stats['modules']['corruption'] = corruption_result.get('metrics', {})

        # Stats Threats
        if threat_plugin:
            threat_result = threat_plugin.run()
            stats['modules']['threats'] = threat_result.get('metrics', {})

        return jsonify(stats)

    except Exception as e:
        logger.error(f"Erreur stats globales: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@security_bp.route('/api/dashboard-data')
def get_dashboard_data():
    """Récupère toutes les données pour le dashboard en une seule requête"""
    try:
        dashboard = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'sanctions': [],
            'corruption': [],
            'threats': []
        }

        # Données Sanctions (top 10)
        if sanctions_plugin:
            sanctions_result = sanctions_plugin.run()
            dashboard['sanctions'] = sanctions_result.get('data', [])[:10]

        # Données Corruption (top 10)
        if corruption_plugin:
            corruption_result = corruption_plugin.run()
            dashboard['corruption'] = corruption_result.get('data', [])[:10]

        # Données Threats (top 10)
        if threat_plugin:
            threat_result = threat_plugin.run()
            dashboard['threats'] = threat_result.get('data', [])[:10]

        return jsonify(dashboard)

    except Exception as e:
        logger.error(f"Erreur dashboard data: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# UN OCHA/HDX - DONNÉES CRISES & CONFLITS
# ============================================================================

@security_bp.route('/api/ocha/crisis')
def get_ocha_crisis():
    """Récupère les données de crises humanitaires (UN OCHA/HDX)"""
    try:
        if ocha_connector:
            result = ocha_connector.get_crisis_data()
            return jsonify(result)

        return jsonify({
            'success': False,
            'error': 'OCHA connector not available'
        }), 503

    except Exception as e:
        logger.error(f"Erreur OCHA crisis: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@security_bp.route('/api/ocha/conflicts')
def get_ocha_conflicts():
    """Récupère les données de conflits armés (UN OCHA/HDX)"""
    try:
        if ocha_connector:
            result = ocha_connector.get_conflict_data()
            return jsonify(result)

        return jsonify({
            'success': False,
            'error': 'OCHA connector not available'
        }), 503

    except Exception as e:
        logger.error(f"Erreur OCHA conflicts: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@security_bp.route('/api/ocha/displacement')
def get_ocha_displacement():
    """Récupère les données de déplacements de population (UN OCHA/HDX)"""
    try:
        if ocha_connector:
            result = ocha_connector.get_displacement_data()
            return jsonify(result)

        return jsonify({
            'success': False,
            'error': 'OCHA connector not available'
        }), 503

    except Exception as e:
        logger.error(f"Erreur OCHA displacement: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@security_bp.route('/api/ocha/humanitarian-access')
def get_ocha_humanitarian():
    """Récupère les données d'accès humanitaire (UN OCHA/HDX)"""
    try:
        if ocha_connector:
            result = ocha_connector.get_humanitarian_access()
            return jsonify(result)

        return jsonify({
            'success': False,
            'error': 'OCHA connector not available'
        }), 503

    except Exception as e:
        logger.error(f"Erreur OCHA humanitarian: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@security_bp.route('/api/ocha/country/<country>')
def get_ocha_country(country):
    """Récupère toutes les données OCHA pour un pays"""
    try:
        if ocha_connector:
            result = ocha_connector.get_country_data(country)
            return jsonify(result)

        return jsonify({
            'success': False,
            'error': 'OCHA connector not available'
        }), 503

    except Exception as e:
        logger.error(f"Erreur OCHA country {country}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@security_bp.route('/api/ocha/summary')
def get_ocha_summary():
    """Résumé global des crises (UN OCHA/HDX)"""
    try:
        if ocha_connector:
            result = ocha_connector.get_summary()
            return jsonify(result)

        return jsonify({
            'success': False,
            'error': 'OCHA connector not available'
        }), 503

    except Exception as e:
        logger.error(f"Erreur OCHA summary: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# ACLED - ARMED CONFLICT LOCATION & EVENT DATA
# ============================================================================

@security_bp.route('/api/acled/recent')
def get_acled_recent():
    """Récupère les événements de conflits récents (UCDP - remplacement ACLED)"""
    try:
        days = int(request.args.get('days', 7))
        limit = int(request.args.get('limit', 100))

        # Priorité: UCDP, fallback: ACLED API si configuré
        if ucdp_connector:
            result = ucdp_connector.get_recent_conflicts(days=days, limit=limit)
            if result.get('success'):
                return jsonify({
                    'success': True,
                    'events': result.get('events', []),
                    'count': len(result.get('events', [])),
                    'period_days': days,
                    'source': 'UCDP (Uppsala Conflict Data Program)',
                    'statistics': result.get('statistics', {}),
                    'total_events': result.get('total_events', 0)
                })

        # Fallback: ACLED API (si configuré)
        if acled_connector:
            events = acled_connector.get_recent_events(days=days, limit=limit)
            return jsonify({
                'success': True,
                'events': events,
                'count': len(events),
                'period_days': days,
                'source': 'ACLED API',
                'note': 'UCDP non disponible, fallback ACLED API'
            })

        return jsonify({
            'success': False,
            'error': 'Connecteurs conflits non disponibles (UCDP & ACLED)',
            'message': 'Données de conflits temporairement indisponibles'
        }), 503

    except Exception as e:
        logger.error(f"Erreur conflits récents: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@security_bp.route('/api/acled/country/<country_code>')
def get_acled_country(country_code):
    """Récupère les événements par pays (ACLED)"""
    try:
        days = int(request.args.get('days', 30))
        limit = int(request.args.get('limit', 100))

        connector = acled_archive_connector or acled_connector
        if connector:
            events = connector.get_events_by_country(
                country_code=country_code.upper(),
                days=days,
                limit=limit
            )
            return jsonify({
                'success': True,
                'country_code': country_code.upper(),
                'events': events,
                'count': len(events),
                'period_days': days,
                'source': 'ACLED Archive' if connector == acled_archive_connector else 'ACLED API'
            })

        return jsonify({
            'success': False,
            'error': 'ACLED connector not available'
        }), 503

    except Exception as e:
        logger.error(f"Erreur ACLED country {country_code}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@security_bp.route('/api/acled/conflicts')
def get_acled_conflicts():
    """Récupère les conflits armés (Battles - ACLED)"""
    try:
        days = int(request.args.get('days', 7))
        limit = int(request.args.get('limit', 50))

        connector = acled_archive_connector or acled_connector
        if connector:
            conflicts = connector.get_conflicts(days=days, limit=limit)
            return jsonify({
                'success': True,
                'conflicts': conflicts,
                'count': len(conflicts),
                'period_days': days,
                'type': 'Battles',
                'source': 'ACLED Archive' if connector == acled_archive_connector else 'ACLED API'
            })

        return jsonify({
            'success': False,
            'error': 'ACLED connector not available'
        }), 503

    except Exception as e:
        logger.error(f"Erreur ACLED conflicts: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@security_bp.route('/api/acled/terrorism')
def get_acled_terrorism():
    """Récupère les événements terroristes (Explosions/Remote violence - ACLED)"""
    try:
        days = int(request.args.get('days', 7))
        limit = int(request.args.get('limit', 50))

        connector = acled_archive_connector or acled_connector
        if connector:
            terrorism = connector.get_terrorism_events(days=days, limit=limit)
            return jsonify({
                'success': True,
                'terrorism_events': terrorism,
                'count': len(terrorism),
                'period_days': days,
                'type': 'Explosions/Remote violence',
                'source': 'ACLED Archive' if connector == acled_archive_connector else 'ACLED API'
            })

        return jsonify({
            'success': False,
            'error': 'ACLED connector not available'
        }), 503

    except Exception as e:
        logger.error(f"Erreur ACLED terrorism: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@security_bp.route('/api/acled/protests')
def get_acled_protests():
    """Récupère les manifestations (Protests - ACLED)"""
    try:
        days = int(request.args.get('days', 7))
        limit = int(request.args.get('limit', 50))

        connector = acled_archive_connector or acled_connector
        if connector:
            protests = connector.get_protests(days=days, limit=limit)
            return jsonify({
                'success': True,
                'protests': protests,
                'count': len(protests),
                'period_days': days,
                'type': 'Protests',
                'source': 'ACLED Archive' if connector == acled_archive_connector else 'ACLED API'
            })

        return jsonify({
            'success': False,
            'error': 'ACLED connector not available'
        }), 503

    except Exception as e:
        logger.error(f"Erreur ACLED protests: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@security_bp.route('/api/acled/violence-civilians')
def get_acled_violence():
    """Récupère les violences contre civils (ACLED)"""
    try:
        days = int(request.args.get('days', 7))
        limit = int(request.args.get('limit', 50))

        connector = acled_archive_connector or acled_connector
        if connector:
            violence = connector.get_violence_civilians(days=days, limit=limit)
            return jsonify({
                'success': True,
                'violence_events': violence,
                'count': len(violence),
                'period_days': days,
                'type': 'Violence against civilians',
                'source': 'ACLED Archive' if connector == acled_archive_connector else 'ACLED API'
            })

        return jsonify({
            'success': False,
            'error': 'ACLED connector not available'
        }), 503

    except Exception as e:
        logger.error(f"Erreur ACLED violence: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@security_bp.route('/api/acled/summary')
def get_acled_summary():
    """Résumé sécuritaire global - Utilise ConflictService (UCDP) en priorité"""
    try:
        days = int(request.args.get('days', 7))
        logger.info(f"[Conflicts] Requête summary, days={days}, conflict_service={conflict_service is not None}")

        # Priorité 1: ConflictService (UCDP - gratuit, sans auth)
        if conflict_service and conflict_service.is_available():
            summary = conflict_service.get_security_summary(days=days)
            logger.info(f"[ConflictService] Résumé récupéré depuis UCDP")
            return jsonify(summary)

        # Priorité 2: ACLED API connector (si configuré avec credentials)
        if acled_connector and acled_connector.email:
            summary = acled_connector.get_security_summary(days=days)
            logger.info(f"[ACLED API] Résumé récupéré depuis API")
            return jsonify(summary)

        # Priorité 3: Archive connector (fallback)
        if acled_archive_connector:
            summary = acled_archive_connector.get_security_summary(days=days)
            logger.info(f"[ACLED Archive] Résumé récupéré depuis archives")
            return jsonify(summary)

        logger.warning("[Conflicts] Aucun connecteur disponible")
        return jsonify({
            'success': False,
            'error': 'Conflict data connector not available',
            'total_events': 0,
            'total_fatalities': 0,
            'by_type': []
        }), 503

    except Exception as e:
        logger.error(f"Erreur conflict summary: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@security_bp.route('/api/acled/hotspots')
def get_acled_hotspots():
    """Identifie les zones de forte activité sécuritaire - Utilise ConflictService (UCDP) en priorité"""
    try:
        days = int(request.args.get('days', 7))
        min_events = int(request.args.get('min_events', 5))

        # Priorité 1: ConflictService (UCDP - gratuit)
        if conflict_service and conflict_service.is_available():
            hotspots = conflict_service.get_hotspots(days=days, min_events=min_events)
            return jsonify({
                'success': True,
                'hotspots': hotspots,
                'count': len(hotspots),
                'period_days': days,
                'source': 'UCDP (ConflictService)'
            })

        # Priorité 2: ACLED connectors
        connector = acled_archive_connector or acled_connector
        if connector:
            hotspots = connector.get_hotspots(days=days, min_events=min_events)
            return jsonify({
                'success': True,
                'hotspots': hotspots,
                'count': len(hotspots),
                'period_days': days,
                'source': 'ACLED Archive' if connector == acled_archive_connector else 'ACLED API'
            })

        return jsonify({
            'success': False,
            'hotspots': [],
            'error': 'Conflict hotspots connector not available'
        }), 503

    except Exception as e:
        logger.error(f"Erreur conflict hotspots: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# GLOBAL INCIDENT MAP - TERRORISME & CYBERATTAQUES
# ============================================================================

@security_bp.route('/api/incidents/recent')
def get_recent_incidents():
    """Récupère les incidents récents (Global Incident Map)"""
    try:
        if incident_connector:
            result = incident_connector.get_recent_incidents(days=7)
            return jsonify(result)

        return jsonify({
            'success': False,
            'error': 'Incident connector not available'
        }), 503

    except Exception as e:
        logger.error(f"Erreur incidents récents: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@security_bp.route('/api/incidents/terrorism')
def get_terrorism_incidents():
    """Récupère les données sur le terrorisme (Global Incident Map)"""
    try:
        if incident_connector:
            result = incident_connector.get_terrorism_data()
            return jsonify(result)

        return jsonify({
            'success': False,
            'error': 'Incident connector not available'
        }), 503

    except Exception as e:
        logger.error(f"Erreur terrorism data: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@security_bp.route('/api/incidents/cyber')
def get_cyber_incidents():
    """Récupère les données sur les cyberattaques (Global Incident Map)"""
    try:
        if incident_connector:
            result = incident_connector.get_cyber_attacks()
            return jsonify(result)

        return jsonify({
            'success': False,
            'error': 'Incident connector not available'
        }), 503

    except Exception as e:
        logger.error(f"Erreur cyber attacks: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@security_bp.route('/api/incidents/political-tensions')
def get_political_tensions_data():
    """Récupère les données sur les tensions politiques (Global Incident Map)"""
    try:
        if incident_connector:
            result = incident_connector.get_political_tensions()
            return jsonify(result)

        return jsonify({
            'success': False,
            'error': 'Incident connector not available'
        }), 503

    except Exception as e:
        logger.error(f"Erreur political tensions: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@security_bp.route('/api/incidents/security-summary')
def get_security_summary_data():
    """Résumé global de la situation sécuritaire (Global Incident Map)"""
    try:
        if incident_connector:
            result = incident_connector.get_security_summary()
            return jsonify(result)

        return jsonify({
            'success': False,
            'error': 'Incident connector not available'
        }), 503

    except Exception as e:
        logger.error(f"Erreur security summary: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@security_bp.route('/api/incidents/maps')
def get_incident_maps():
    """Récupère les infos pour embed des cartes Global Incident Map"""
    try:
        if incident_connector:
            result = incident_connector.get_map_embed_info()
            return jsonify(result)

        return jsonify({
            'success': False,
            'error': 'Incident connector not available'
        }), 503

    except Exception as e:
        logger.error(f"Erreur maps info: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# ALIENVAULT OTX - THREAT INTELLIGENCE
# ============================================================================

@security_bp.route('/api/otx/pulses')
def get_otx_pulses():
    """Récupère les pulses (collections de menaces) depuis AlienVault OTX"""
    try:
        if alienvault_connector:
            days = int(request.args.get('days', 7))
            limit = int(request.args.get('limit', 50))
            result = alienvault_connector.get_subscribed_pulses(limit=limit, days=days)
            return jsonify(result)

        return jsonify({
            'success': False,
            'error': 'AlienVault OTX connector not available'
        }), 503

    except Exception as e:
        logger.error(f"Erreur OTX pulses: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@security_bp.route('/api/otx/search')
def search_otx_pulses():
    """Recherche dans les pulses AlienVault OTX"""
    try:
        if alienvault_connector:
            query = request.args.get('q', 'malware')
            limit = int(request.args.get('limit', 20))
            result = alienvault_connector.search_pulses(query=query, limit=limit)
            return jsonify(result)

        return jsonify({
            'success': False,
            'error': 'AlienVault OTX connector not available'
        }), 503

    except Exception as e:
        logger.error(f"Erreur OTX search: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@security_bp.route('/api/otx/threats')
def get_otx_threats():
    """Récupère les menaces récentes depuis AlienVault OTX"""
    try:
        if alienvault_connector:
            days = int(request.args.get('days', 7))
            limit = int(request.args.get('limit', 50))
            result = alienvault_connector.get_recent_threats(days=days, limit=limit)
            return jsonify(result)

        return jsonify({
            'success': False,
            'error': 'AlienVault OTX connector not available'
        }), 503

    except Exception as e:
        logger.error(f"Erreur OTX threats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@security_bp.route('/api/otx/summary')
def get_otx_summary():
    """Récupère un résumé des menaces depuis AlienVault OTX"""
    try:
        if alienvault_connector:
            result = alienvault_connector.get_threat_summary()
            return jsonify(result)

        return jsonify({
            'success': False,
            'error': 'AlienVault OTX connector not available'
        }), 503

    except Exception as e:
        logger.error(f"Erreur OTX summary: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@security_bp.route('/api/otx/check-ioc')
def check_otx_ioc():
    """Vérifie si un IOC (IP, domaine, hash, etc.) est connu comme malveillant"""
    try:
        if alienvault_connector:
            ioc = request.args.get('ioc', '')
            ioc_type = request.args.get('type', 'auto')

            if not ioc:
                return jsonify({
                    'success': False,
                    'error': 'Paramètre "ioc" requis'
                }), 400

            result = alienvault_connector.check_ioc(ioc=ioc, ioc_type=ioc_type)
            return jsonify(result)

        return jsonify({
            'success': False,
            'error': 'AlienVault OTX connector not available'
        }), 503

    except Exception as e:
        logger.error(f"Erreur OTX check IOC: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@security_bp.route('/api/otx/indicator/<indicator_type>/<path:indicator>')
def get_otx_indicator_details(indicator_type, indicator):
    """Récupère les détails d'un indicateur spécifique"""
    try:
        if alienvault_connector:
            result = alienvault_connector.get_indicator_details(
                indicator_type=indicator_type,
                indicator=indicator
            )
            return jsonify(result)

        return jsonify({
            'success': False,
            'error': 'AlienVault OTX connector not available'
        }), 503

    except Exception as e:
        logger.error(f"Erreur OTX indicator details: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@security_bp.route('/api/otx/verify-key')
def verify_otx_api_key():
    """Vérifie si la clé API AlienVault OTX est valide"""
    try:
        if alienvault_connector:
            result = alienvault_connector.verify_api_key()
            return jsonify(result)

        return jsonify({
            'success': False,
            'error': 'AlienVault OTX connector not available'
        }), 503

    except Exception as e:
        logger.error(f"Erreur OTX verify key: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# OPENSANCTIONS - SANCTIONS, PEPS, CRIME
# ============================================================================

@security_bp.route('/api/opensanctions/search')
def opensanctions_search():
    """Recherche d'entites dans OpenSanctions"""
    try:
        if opensanctions_connector:
            query = request.args.get('q', '')
            dataset = request.args.get('dataset', 'default')
            schema = request.args.get('schema')
            countries = request.args.get('countries', '').split(',') if request.args.get('countries') else None
            limit = int(request.args.get('limit', 50))

            if not query:
                return jsonify({'success': False, 'error': 'Parametre q requis'}), 400

            result = opensanctions_connector.search_entities(
                query=query, dataset=dataset, schema=schema,
                countries=countries, limit=limit
            )
            return jsonify(result)

        return jsonify({'success': False, 'error': 'OpenSanctions connector not available'}), 503
    except Exception as e:
        logger.error(f"Erreur OpenSanctions search: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@security_bp.route('/api/opensanctions/match', methods=['POST'])
def opensanctions_match():
    """Matching d'entite pour screening KYC/AML"""
    try:
        if opensanctions_connector:
            data = request.get_json() or {}
            name = data.get('name', request.args.get('name', ''))
            dataset = data.get('dataset', request.args.get('dataset', 'default'))
            schema = data.get('schema', request.args.get('schema', 'Person'))
            birth_date = data.get('birth_date')
            nationality = data.get('nationality')
            threshold = float(data.get('threshold', 0.7))

            if not name:
                return jsonify({'success': False, 'error': 'Parametre name requis'}), 400

            result = opensanctions_connector.match_entity(
                name=name, dataset=dataset, schema=schema,
                birth_date=birth_date, nationality=nationality, threshold=threshold
            )
            return jsonify(result)

        return jsonify({'success': False, 'error': 'OpenSanctions connector not available'}), 503
    except Exception as e:
        logger.error(f"Erreur OpenSanctions match: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@security_bp.route('/api/opensanctions/sanctions/<country_code>')
def opensanctions_sanctions_country(country_code):
    """Entites sanctionnees pour un pays"""
    try:
        if opensanctions_connector:
            limit = int(request.args.get('limit', 100))
            result = opensanctions_connector.get_sanctions_by_country(country_code, limit=limit)
            return jsonify(result)

        return jsonify({'success': False, 'error': 'OpenSanctions connector not available'}), 503
    except Exception as e:
        logger.error(f"Erreur OpenSanctions sanctions: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@security_bp.route('/api/opensanctions/peps/<country_code>')
def opensanctions_peps_country(country_code):
    """Personnes politiquement exposees pour un pays"""
    try:
        if opensanctions_connector:
            limit = int(request.args.get('limit', 100))
            result = opensanctions_connector.get_peps_by_country(country_code, limit=limit)
            return jsonify(result)

        return jsonify({'success': False, 'error': 'OpenSanctions connector not available'}), 503
    except Exception as e:
        logger.error(f"Erreur OpenSanctions PEPs: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@security_bp.route('/api/opensanctions/crime')
def opensanctions_crime():
    """Entites criminelles (mafias, cartels, trafiquants)"""
    try:
        if opensanctions_connector:
            countries = request.args.get('countries', '').split(',') if request.args.get('countries') else None
            limit = int(request.args.get('limit', 100))
            result = opensanctions_connector.get_crime_entities(countries=countries, limit=limit)
            return jsonify(result)

        return jsonify({'success': False, 'error': 'OpenSanctions connector not available'}), 503
    except Exception as e:
        logger.error(f"Erreur OpenSanctions crime: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@security_bp.route('/api/opensanctions/entity/<entity_id>')
def opensanctions_entity(entity_id):
    """Details d'une entite specifique"""
    try:
        if opensanctions_connector:
            result = opensanctions_connector.get_entity(entity_id)
            return jsonify(result)

        return jsonify({'success': False, 'error': 'OpenSanctions connector not available'}), 503
    except Exception as e:
        logger.error(f"Erreur OpenSanctions entity: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@security_bp.route('/api/opensanctions/catalog')
def opensanctions_catalog():
    """Catalogue des datasets disponibles"""
    try:
        if opensanctions_connector:
            result = opensanctions_connector.get_catalog()
            return jsonify(result)

        return jsonify({'success': False, 'error': 'OpenSanctions connector not available'}), 503
    except Exception as e:
        logger.error(f"Erreur OpenSanctions catalog: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@security_bp.route('/api/opensanctions/summary')
def opensanctions_summary():
    """Resume global des sanctions"""
    try:
        if opensanctions_connector:
            result = opensanctions_connector.get_sanctions_summary()
            return jsonify(result)

        return jsonify({'success': False, 'error': 'OpenSanctions connector not available'}), 503
    except Exception as e:
        logger.error(f"Erreur OpenSanctions summary: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# ROUTE GLOBALE - DASHBOARD COMPLET
# ============================================================================

@security_bp.route('/api/complete-dashboard')
def get_complete_dashboard():
    """
    Récupère TOUTES les données pour le dashboard complet:
    - Sanctions (plugin newarchi)
    - Corruption (plugin newarchi)
    - Threats (plugin newarchi)
    - Crises & Conflits (UN OCHA/HDX)
    - Incidents de sécurité (Global Incident Map)
    """
    try:
        dashboard = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'sources': [],
            'data': {}
        }

        # Sanctions
        if sanctions_plugin:
            sanctions_result = sanctions_plugin.run()
            if sanctions_result.get('status') == 'success':
                dashboard['data']['sanctions'] = {
                    'count': len(sanctions_result.get('data', [])),
                    'data': sanctions_result.get('data', [])[:10],
                    'metrics': sanctions_result.get('metrics', {})
                }
                dashboard['sources'].append('Douanes FR / OFAC / UE Sanctions')

        # Corruption
        if corruption_plugin:
            corruption_result = corruption_plugin.run()
            if corruption_result.get('status') == 'success':
                dashboard['data']['corruption'] = {
                    'count': len(corruption_result.get('data', [])),
                    'data': corruption_result.get('data', [])[:10],
                    'metrics': corruption_result.get('metrics', {})
                }
                dashboard['sources'].append('Transparency International / FATF')

        # Threats
        if threat_plugin:
            threat_result = threat_plugin.run()
            if threat_result.get('status') == 'success':
                dashboard['data']['threats'] = {
                    'count': len(threat_result.get('data', [])),
                    'data': threat_result.get('data', [])[:10],
                    'metrics': threat_result.get('metrics', {})
                }
                dashboard['sources'].append('AlienVault OTX / CVE Database')

        # UN OCHA/HDX - Crises
        if ocha_connector:
            try:
                ocha_summary = ocha_connector.get_summary()
                if ocha_summary.get('success'):
                    dashboard['data']['humanitarian'] = {
                        'statistics': ocha_summary.get('statistics', {}),
                        'latest_updates': ocha_summary.get('latest_updates', [])[:5]
                    }
                    dashboard['sources'].append('UN OCHA / HDX')
            except Exception as e:
                logger.warning(f"OCHA data unavailable: {e}")

        # Global Incident Map
        if incident_connector:
            try:
                incident_summary = incident_connector.get_security_summary()
                if incident_summary.get('success'):
                    dashboard['data']['security_incidents'] = {
                        'status': incident_summary.get('global_security_status', {}),
                        'statistics': incident_summary.get('statistics', {}),
                        'maps': incident_summary.get('maps', {})
                    }
                    dashboard['sources'].append('Global Incident Map / GTD')
            except Exception as e:
                logger.warning(f"Incident data unavailable: {e}")

        logger.info(f"[OK] Complete dashboard: {len(dashboard['sources'])} sources")
        return jsonify(dashboard)

    except Exception as e:
        logger.error(f"Erreur complete dashboard: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# DASHBOARD ANALYTICS API - INTÉGRATION PHASE 1
# ============================================================================

@security_bp.route('/api/analytics/overview')
def get_analytics_overview():
    """Récupère la vue d'ensemble globale du dashboard analytics"""
    try:
        if security_analytics_dashboard:
            overview = security_analytics_dashboard.get_global_overview()
            return jsonify(overview)
        return jsonify({
            'success': False,
            'error': 'Dashboard analytics non disponible',
            'available': False
        }), 503
    except Exception as e:
        logger.error(f"Erreur analytics overview: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@security_bp.route('/api/analytics/country-profile/<country_code>')
def get_analytics_country_profile(country_code):
    """Récupère le profil complet d'un pays"""
    try:
        if security_analytics_dashboard:
            profile = security_analytics_dashboard.get_country_profile(country_code)
            return jsonify(profile)
        return jsonify({
            'success': False,
            'error': 'Dashboard analytics non disponible',
            'available': False
        }), 503
    except Exception as e:
        logger.error(f"Erreur country profile {country_code}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@security_bp.route('/api/analytics/top-risks')
def get_analytics_top_risks():
    """Récupère les principaux risques identifiés"""
    try:
        limit = int(request.args.get('limit', 10))
        if security_analytics_dashboard:
            risks = security_analytics_dashboard.get_top_risks(limit=limit)
            return jsonify(risks)
        return jsonify({
            'success': False,
            'error': 'Dashboard analytics non disponible',
            'available': False
        }), 503
    except Exception as e:
        logger.error(f"Erreur top risks: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@security_bp.route('/api/analytics/trends')
def get_analytics_trends():
    """Récupère l'analyse des tendances"""
    try:
        months = int(request.args.get('months', 6))
        if security_analytics_dashboard:
            trends = security_analytics_dashboard.get_trends_analysis(months=months)
            return jsonify(trends)
        return jsonify({
            'success': False,
            'error': 'Dashboard analytics non disponible',
            'available': False
        }), 503
    except Exception as e:
        logger.error(f"Erreur trends: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@security_bp.route('/api/analytics/report')
def get_analytics_report():
    """Récupère le rapport complet formaté"""
    try:
        if security_analytics_dashboard:
            report = security_analytics_dashboard.generate_comprehensive_report()
            return jsonify({
                'success': True,
                'available': True,
                'timestamp': datetime.now().isoformat(),
                'report': report,
                'length': len(report)
            })
        return jsonify({
            'success': False,
            'error': 'Dashboard analytics non disponible',
            'available': False
        }), 503
    except Exception as e:
        logger.error(f"Erreur report: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@security_bp.route('/api/analytics/export')
def get_analytics_export():
    """Exporte toutes les données analytics en JSON"""
    try:
        format_type = request.args.get('format', 'json')
        if security_analytics_dashboard:
            data = security_analytics_dashboard.export_data(format=format_type)
            if format_type == 'json':
                return jsonify({
                    'success': True,
                    'available': True,
                    'timestamp': datetime.now().isoformat(),
                    'format': 'json',
                    'data': json.loads(data)  # Convertit le JSON string en dict
                })
            else:
                return jsonify({
                    'success': True,
                    'available': True,
                    'timestamp': datetime.now().isoformat(),
                    'format': 'dict',
                    'data': data
                })
        return jsonify({
            'success': False,
            'error': 'Dashboard analytics non disponible',
            'available': False
        }), 503
    except Exception as e:
        logger.error(f"Erreur export: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@security_bp.route('/api/analytics/health')
def get_analytics_health():
    """Vérifie la santé du dashboard analytics"""
    try:
        if security_analytics_dashboard:
            available = security_analytics_dashboard.is_available()
            return jsonify({
                'success': True,
                'available': available,
                'timestamp': datetime.now().isoformat(),
                'dashboard_health': 'healthy' if available else 'unavailable',
                'connectors_count': len(security_analytics_dashboard.connectors) if hasattr(security_analytics_dashboard, 'connectors') else 0
            })
        return jsonify({
            'success': False,
            'available': False,
            'error': 'Dashboard analytics non initialisé'
        }), 503
    except Exception as e:
        logger.error(f"Erreur health check: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# CACHE MONITORING API - PHASE 2
# ============================================================================

@security_bp.route('/api/cache/stats')
def get_cache_statistics():
    """Récupère les statistiques détaillées du cache"""
    try:
        if cache_monitor:
            stats = cache_monitor.get_cache_statistics()
            return jsonify(stats)
        return jsonify({
            'success': False,
            'available': False,
            'error': 'Cache monitor non disponible'
        }), 503
    except Exception as e:
        logger.error(f"Erreur cache stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@security_bp.route('/api/cache/health')
def get_cache_health():
    """Récupère l'état de santé du cache"""
    try:
        if cache_monitor:
            health = cache_monitor.get_cache_health()
            return jsonify(health)
        return jsonify({
            'success': False,
            'healthy': False,
            'error': 'Cache monitor non disponible'
        }), 503
    except Exception as e:
        logger.error(f"Erreur cache health: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@security_bp.route('/api/cache/source/<source_name>')
def get_cache_source_details(source_name):
    """Récupère les détails d'une source spécifique du cache"""
    try:
        if cache_monitor:
            details = cache_monitor.get_source_details(source_name)
            return jsonify(details)
        return jsonify({
            'success': False,
            'available': False,
            'error': 'Cache monitor non disponible'
        }), 503
    except Exception as e:
        logger.error(f"Erreur cache source details {source_name}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@security_bp.route('/api/cache/hit-rate')
def get_cache_hit_rate():
    """Récupère le taux de hit estimé du cache"""
    try:
        source = request.args.get('source', None)
        if cache_monitor:
            hit_rate = cache_monitor.calculate_hit_rate(source=source)
            return jsonify(hit_rate)
        return jsonify({
            'success': False,
            'available': False,
            'error': 'Cache monitor non disponible'
        }), 503
    except Exception as e:
        logger.error(f"Erreur cache hit rate: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@security_bp.route('/api/cache/report')
def get_cache_report():
    """Génère un rapport textuel du cache"""
    try:
        include_details = request.args.get('details', 'false').lower() == 'true'
        if cache_monitor:
            report = cache_monitor.generate_report(include_details=include_details)
            return jsonify({
                'success': True,
                'available': True,
                'timestamp': datetime.now().isoformat(),
                'report': report,
                'length': len(report)
            })
        return jsonify({
            'success': False,
            'available': False,
            'error': 'Cache monitor non disponible'
        }), 503
    except Exception as e:
        logger.error(f"Erreur cache report: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@security_bp.route('/api/cache/cleanup', methods=['POST'])
def cleanup_cache():
    """Nettoie les entrées de cache expirées"""
    try:
        dry_run = request.args.get('dry_run', 'true').lower() == 'true'
        if cache_monitor:
            result = cache_monitor.clear_expired_cache(dry_run=dry_run)
            return jsonify(result)
        return jsonify({
            'success': False,
            'error': 'Cache monitor non disponible'
        }), 503
    except Exception as e:
        logger.error(f"Erreur cache cleanup: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# REPORT GENERATION API - PHASE 3
# ============================================================================

@security_bp.route('/api/reports/generate')
def generate_report():
    """Génère un rapport dans le format spécifié"""
    try:
        format_type = request.args.get('format', 'html').lower()
        include_cache = request.args.get('include_cache', 'true').lower() == 'true'
        save_report = request.args.get('save', 'false').lower() == 'true'

        if not security_analytics_dashboard or not report_generator:
            return jsonify({
                'success': False,
                'error': 'Services requis non disponibles'
            }), 503

        # Récupérer données analytics
        analytics_data = security_analytics_dashboard.export_data(format='dict')

        # Récupérer données cache si demandé
        cache_stats = None
        cache_health = None
        if include_cache and cache_monitor:
            cache_stats = cache_monitor.get_cache_statistics()
            cache_health = cache_monitor.get_cache_health()

        # Générer rapport selon format
        if format_type == 'html':
            report_content = report_generator.generate_html_report(
                analytics_data, cache_stats, cache_health
            )
            saved_path = None
            if save_report:
                saved_path = report_generator.save_report(
                    content=report_content,
                    format='html'
                )
            response = {
                'success': True,
                'format': 'html',
                'content': report_content,
                'length': len(report_content),
                'timestamp': datetime.now().isoformat()
            }
            if saved_path:
                response['saved_path'] = saved_path
                response['filename'] = os.path.basename(saved_path)
            return jsonify(response)

        elif format_type == 'json':
            report_content = report_generator.generate_json_report(
                analytics_data, cache_stats, cache_health
            )
            saved_path = None
            if save_report:
                saved_path = report_generator.save_report(
                    content=report_content,
                    format='json'
                )
            response = {
                'success': True,
                'format': 'json',
                'content': json.loads(report_content),  # Convertir en dict pour JSON response
                'length': len(report_content),
                'timestamp': datetime.now().isoformat()
            }
            if saved_path:
                response['saved_path'] = saved_path
                response['filename'] = os.path.basename(saved_path)
            return jsonify(response)

        elif format_type == 'text' or format_type == 'txt':
            report_content = report_generator.generate_text_report(
                analytics_data, cache_stats, cache_health
            )
            saved_path = None
            if save_report:
                saved_path = report_generator.save_report(
                    content=report_content,
                    format='txt'
                )
            response = {
                'success': True,
                'format': 'text',
                'content': report_content,
                'length': len(report_content),
                'timestamp': datetime.now().isoformat()
            }
            if saved_path:
                response['saved_path'] = saved_path
                response['filename'] = os.path.basename(saved_path)
            return jsonify(response)

        elif format_type == 'pdf':
            # Générer PDF et retourner chemin
            pdf_path = report_generator.generate_pdf_report(
                analytics_data, cache_stats, cache_health
            )
            if pdf_path:
                response = {
                    'success': True,
                    'format': 'pdf',
                    'file_path': pdf_path,
                    'filename': os.path.basename(pdf_path),
                    'timestamp': datetime.now().isoformat()
                }
                # Le PDF est toujours sauvegardé, on indique le chemin
                response['saved_path'] = pdf_path
                return jsonify(response)
            else:
                return jsonify({
                    'success': False,
                    'error': 'Génération PDF non disponible (WeasyPrint requis)'
                }), 503

        else:
            return jsonify({
                'success': False,
                'error': f'Format non supporté: {format_type}',
                'supported_formats': ['html', 'json', 'text', 'pdf']
            }), 400

    except Exception as e:
        logger.error(f"Erreur génération rapport: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@security_bp.route('/api/reports/download/<filename>')
def download_report(filename):
    """Télécharge un rapport précédemment généré"""
    try:
        # Vérifier sécurité du nom de fichier
        if '..' in filename or filename.startswith('/'):
            return jsonify({'success': False, 'error': 'Nom de fichier invalide'}), 400

        # Déterminer chemin du fichier
        reports_dir = os.path.join(os.path.dirname(__file__), '..', 'reports')
        filepath = os.path.join(reports_dir, filename)

        if not os.path.exists(filepath):
            return jsonify({'success': False, 'error': 'Fichier non trouvé'}), 404

        # Déterminer type MIME
        mime_types = {
            '.html': 'text/html',
            '.pdf': 'application/pdf',
            '.json': 'application/json',
            '.txt': 'text/plain'
        }
        ext = os.path.splitext(filename)[1].lower()
        mime_type = mime_types.get(ext, 'application/octet-stream')

        # Lire et retourner fichier
        with open(filepath, 'rb') as f:
            content = f.read()

        from flask import Response
        return Response(
            content,
            mimetype=mime_type,
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )

    except Exception as e:
        logger.error(f"Erreur téléchargement rapport {filename}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@security_bp.route('/api/reports/list')
def list_reports():
    """Liste les rapports disponibles"""
    try:
        reports_dir = os.path.join(os.path.dirname(__file__), '..', 'reports')
        os.makedirs(reports_dir, exist_ok=True)

        reports = []
        for filename in os.listdir(reports_dir):
            filepath = os.path.join(reports_dir, filename)
            if os.path.isfile(filepath) and filename.startswith('security_report_'):
                stats = os.stat(filepath)
                reports.append({
                    'filename': filename,
                    'size': stats.st_size,
                    'modified': datetime.fromtimestamp(stats.st_mtime).isoformat(),
                    'format': os.path.splitext(filename)[1][1:].lower()
                })

        # Trier par date de modification (plus récent d'abord)
        reports.sort(key=lambda x: x['modified'], reverse=True)

        return jsonify({
            'success': True,
            'count': len(reports),
            'reports': reports,
            'directory': reports_dir,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Erreur liste rapports: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


def init_security_governance_connectors(db_manager):
    """
    Initialise les connecteurs du module Sécurité & Gouvernance avec le db_manager
    Permet aux connecteurs de récupérer leurs clés API depuis la base de données
    """
    global acled_connector

    try:
        logger.info(f"[INIT] Initialisation ACLED avec db_manager: {db_manager is not None}")
        if ACLEDConnector:
            acled_connector = ACLEDConnector(db_manager=db_manager)
            logger.info(f"[OK] ACLED Connector initialisé avec DB Manager, connecteur: {acled_connector is not None}")
        else:
            logger.warning("[WARN] ACLEDConnector non disponible")
    except Exception as e:
        logger.error(f"[ERROR] Erreur init ACLED avec DB: {e}")
        acled_connector = None


logger.info("[OK] Module Sécurité & Gouvernance chargé avec 6 sources intégrées (3 plugins + OCHA/HDX + ACLED Archives + Global Incident)")
