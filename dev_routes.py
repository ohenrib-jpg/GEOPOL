"""
Routes Flask pour le Dev Assistant
"""
from flask import Blueprint, request, jsonify, render_template
import logging

logger = logging.getLogger(__name__)
dev_assistant_bp = Blueprint('dev_assistant', __name__)

_orchestrator = None
_phi_agent = None
_tools = None
_api_keys_manager = None
_last_analysis_result = None


def init_dev_assistant(app, orchestrator, phi_agent, tools, api_keys_manager=None):
    global _orchestrator, _phi_agent, _tools, _api_keys_manager
    _orchestrator = orchestrator
    _phi_agent = phi_agent
    _tools = tools
    _api_keys_manager = api_keys_manager
    app.register_blueprint(dev_assistant_bp, url_prefix='/dev')
    logger.info('[OK] Dev Assistant routes initialisees')


@dev_assistant_bp.route('/assistant', methods=['GET'])
def dev_assistant_page():
    return render_template('dev_assistant.html')


@dev_assistant_bp.route('/api/status', methods=['GET'])
def get_status():
    return jsonify({
        'success': True,
        'phi_available': _phi_agent is not None,
        'tools_available': _tools is not None
    })


@dev_assistant_bp.route('/api/analyze', methods=['POST'])
def analyze_context():
    data = request.get_json()
    context = data.get('context', '')
    if not _phi_agent:
        return jsonify({'success': False, 'error': 'Phi non disponible'}), 500
    try:
        obs = _phi_agent.observe(context)
        diag = _phi_agent.diagnose(obs)
        return jsonify({'success': True, 'observation': obs, 'diagnosis': diag})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@dev_assistant_bp.route('/api/execute', methods=['POST'])
def execute_action():
    data = request.get_json()
    action = data.get('action', {})
    if not _orchestrator:
        return jsonify({'success': False, 'error': 'Orchestrator non disponible'}), 500
    try:
        result = _orchestrator.execute_action(action)
        return jsonify({'success': True, 'result': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def _get_api_keys_manager():
    """Récupère le gestionnaire de clés API de manière lazy"""
    global _api_keys_manager
    if _api_keys_manager:
        return _api_keys_manager

    # Essayer de récupérer depuis la config Flask
    from flask import current_app
    try:
        manager = current_app.config.get('API_KEYS_MANAGER')
        if manager:
            _api_keys_manager = manager
            return manager
    except RuntimeError:
        pass

    return None


@dev_assistant_bp.route('/api/chat', methods=['POST'])
def chat_with_remote():
    import requests as req
    data = request.get_json()
    msg = data.get('message', '')
    provider = data.get('provider', 'anthropic')
    files = data.get('include_files', [])

    api_keys_mgr = _get_api_keys_manager()
    if not api_keys_mgr:
        return jsonify({'success': False, 'error': 'API Keys non disponible. Configurez vos clés dans Paramètres.'}), 500

    creds = api_keys_mgr.get_api_key(provider)
    if not creds:
        return jsonify({'success': False, 'error': f'Cle {provider} non configuree'}), 400

    try:
        ctx = ''
        if _tools and files:
            for fp in files[:5]:
                c = _tools.read_file(fp)
                if c and not c.startswith('[Erreur'):
                    ctx += f'=== {fp} ===\n{c[:5000]}\n'

        if provider == 'anthropic':
            resp = req.post('https://api.anthropic.com/v1/messages',
                headers={'x-api-key': creds['api_key'], 'anthropic-version': '2023-06-01', 'content-type': 'application/json'},
                json={'model': 'claude-sonnet-4-20250514', 'max_tokens': 4096,
                      'system': 'Tu es un assistant dev expert. Tu peux créer, modifier et corriger du code. Réponds en français.' + (f'\nContexte:\n{ctx}' if ctx else ''),
                      'messages': [{'role': 'user', 'content': msg}]},
                timeout=90)
            if resp.status_code == 200:
                return jsonify({'success': True, 'response': resp.json()['content'][0]['text']})
            else:
                error_detail = resp.text[:500] if resp.text else 'Pas de détail'
                logger.error(f'[DevChat] Erreur Anthropic {resp.status_code}: {error_detail}')
                return jsonify({'success': False, 'error': f'Erreur Anthropic ({resp.status_code}): {error_detail}'}), resp.status_code
        elif provider == 'deepseek':
            resp = req.post('https://api.deepseek.com/v1/chat/completions',
                headers={'Authorization': f'Bearer {creds["api_key"]}', 'Content-Type': 'application/json'},
                json={'model': 'deepseek-coder', 'max_tokens': 4096,
                      'messages': [{'role': 'system', 'content': 'Tu es un assistant dev expert. Tu peux créer, modifier et corriger du code. Réponds en français.' + (f'\nContexte:\n{ctx}' if ctx else '')},
                                   {'role': 'user', 'content': msg}]},
                timeout=90)
            if resp.status_code == 200:
                return jsonify({'success': True, 'response': resp.json()['choices'][0]['message']['content']})
            else:
                error_detail = resp.text[:500] if resp.text else 'Pas de détail'
                logger.error(f'[DevChat] Erreur DeepSeek {resp.status_code}: {error_detail}')
                return jsonify({'success': False, 'error': f'Erreur DeepSeek ({resp.status_code}): {error_detail}'}), resp.status_code

        return jsonify({'success': False, 'error': f'Provider {provider} non supporté'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@dev_assistant_bp.route('/api/detect-errors', methods=['POST'])
def detect_errors():
    data = request.get_json()
    log = data.get('log', '')
    errors = []
    for i, line in enumerate(log.split('\n')):
        for kw in ['Error', 'Exception', 'Traceback', 'Failed']:
            if kw in line:
                errors.append({'line': i+1, 'content': line[:150], 'type': kw})
                break
    return jsonify({'success': True, 'errors': errors, 'count': len(errors), 'should_show_button': len(errors) > 0})


@dev_assistant_bp.route('/api/providers', methods=['GET'])
def get_providers():
    api_keys_mgr = _get_api_keys_manager()
    if not api_keys_mgr:
        # Retourner une liste vide si pas de manager configuré
        return jsonify({
            'success': True,
            'providers': [
                {'id': 'anthropic', 'configured': False, 'name': 'Claude'},
                {'id': 'deepseek', 'configured': False, 'name': 'Deepseek'},
                {'id': 'openai', 'configured': False, 'name': 'Openai'}
            ],
            'warning': 'Gestionnaire de clés non initialisé'
        })

    providers = []
    for p in ['anthropic', 'deepseek', 'openai']:
        providers.append({'id': p, 'configured': api_keys_mgr.get_api_key(p) is not None,
                         'name': 'Claude' if p == 'anthropic' else p.capitalize()})
    return jsonify({'success': True, 'providers': providers})


@dev_assistant_bp.route('/api/last-analysis', methods=['GET'])
def get_last_analysis():
    """Récupère le dernier résultat d'analyse pour le bouton 'Je souhaite agir'"""
    global _last_analysis_result
    if _last_analysis_result:
        return jsonify({
            'success': True,
            'has_analysis': True,
            'analysis': _last_analysis_result
        })
    return jsonify({
        'success': True,
        'has_analysis': False,
        'analysis': None
    })


@dev_assistant_bp.route('/api/clear-analysis', methods=['POST'])
def clear_last_analysis():
    """Efface le dernier résultat d'analyse après traitement"""
    global _last_analysis_result
    _last_analysis_result = None
    return jsonify({'success': True})


@dev_assistant_bp.route('/api/capture-errors', methods=['POST'])
def capture_errors():
    """Capture les erreurs JavaScript envoyées par le frontend"""
    data = request.get_json()

    if not data:
        return jsonify({'success': False, 'error': 'Données JSON manquantes'}), 400

    errors = data.get('errors', [])
    page_info = data.get('pageInfo', {})

    # Loguer les erreurs pour débogage
    logger.info(f'[ErrorCapture] {len(errors)} erreur(s) JS capturée(s) depuis {page_info.get("url", "inconnu")}')

    # Analyser les erreurs pour décider si une action est nécessaire
    should_analyze = False
    critical_errors = []

    for error in errors:
        error_type = error.get('type', 'unknown')
        message = error.get('message') or error.get('messages') or ''

        # Détecter les erreurs critiques
        is_critical = (
            'SyntaxError' in str(message) or
            'ReferenceError' in str(message) or
            'TypeError' in str(message) or
            'Uncaught' in str(message) or
            error_type == 'unhandledrejection'
        )

        if is_critical:
            critical_errors.append({
                'type': error_type,
                'message': str(message)[:200],
                'timestamp': error.get('timestamp')
            })

    # Suggérer une analyse si erreurs critiques ou nombreuses erreurs
    if len(critical_errors) > 0 or len(errors) >= 3:
        should_analyze = True
        logger.info(f'[ErrorCapture] Analyse suggérée: {len(critical_errors)} erreur(s) critique(s)')

        # Lancer une analyse asynchrone si Phi est disponible
        if _orchestrator and _phi_agent:
            try:
                # Importer threading pour l'analyse asynchrone
                import threading

                def analyze_async():
                    try:
                        logger.info(f'[ErrorCapture] Début analyse asynchrone des erreurs JS')
                        result = _orchestrator.analyze_js_errors(errors, page_info)

                        # Stocker le résultat en mémoire pour le bouton "Je souhaite agir"
                        global _last_analysis_result
                        from datetime import datetime
                        _last_analysis_result = {
                            'result': result,
                            'timestamp': datetime.now().isoformat(),
                            'error_count': len(errors),
                            'critical_errors': critical_errors,
                            'page_info': page_info
                        }
                        logger.info(f'[ErrorCapture] Résultat stocké en mémoire: {len(critical_errors)} erreur(s) critique(s)')

                        if result.get('success'):
                            logger.info(f'[ErrorCapture] Analyse terminée: {len(result.get("actions", []))} action(s) planifiée(s)')
                            # Stocker le résultat pour consultation ultérieure
                            try:
                                import json as json_module
                                import os
                                from datetime import datetime

                                analysis_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs', 'analysis')
                                os.makedirs(analysis_dir, exist_ok=True)

                                analysis_file = os.path.join(analysis_dir, f'js_analysis_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
                                with open(analysis_file, 'w', encoding='utf-8') as f:
                                    json_module.dump({
                                        'timestamp': datetime.now().isoformat(),
                                        'page_info': page_info,
                                        'error_count': len(errors),
                                        'analysis_result': result,
                                        'critical_errors': critical_errors
                                    }, f, ensure_ascii=False, indent=2)

                                logger.info(f'[ErrorCapture] Analyse sauvegardée: {analysis_file}')
                            except Exception as e:
                                logger.error(f'[ErrorCapture] Erreur sauvegarde analyse: {e}')
                        else:
                            logger.warning(f'[ErrorCapture] Analyse échouée: {result.get("error")}')
                    except Exception as e:
                        logger.error(f'[ErrorCapture] Erreur analyse asynchrone: {e}')

                # Démarrer l'analyse dans un thread séparé
                thread = threading.Thread(target=analyze_async, daemon=True)
                thread.start()
                logger.info('[ErrorCapture] Analyse asynchrone lancée en arrière-plan')

            except Exception as e:
                logger.error(f'[ErrorCapture] Erreur lancement analyse asynchrone: {e}')

    # Stocker les erreurs pour consultation ultérieure (dans un fichier log)
    try:
        import json as json_module
        import os
        from datetime import datetime

        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
        os.makedirs(log_dir, exist_ok=True)

        log_file = os.path.join(log_dir, 'js_errors.json')
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'page_info': page_info,
            'error_count': len(errors),
            'critical_errors': critical_errors,
            'all_errors': errors[:10]  # Garder seulement les 10 premières pour éviter la surcharge
        }

        # Ajouter à la fin du fichier log
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json_module.dumps(log_entry, ensure_ascii=False) + '\n')

    except Exception as e:
        logger.error(f'[ErrorCapture] Erreur lors de l\'écriture du log: {e}')

    # Réponse au frontend
    return jsonify({
        'success': True,
        'received': len(errors),
        'critical': len(critical_errors),
        'should_analyze': should_analyze,
        'message': f'{len(errors)} erreur(s) capturée(s), {len(critical_errors)} critique(s)'
    })