"""
Dev Assistant - Classe principale d orchestration
"""
import logging
from typing import Optional
from .orchestrator import get_orchestrator, DevOrchestrator
from .phi_agent import get_phi_agent, PhiAgent
from .tools import Tools

logger = logging.getLogger(__name__)


class DevAssistant:
    """Classe principale du Dev Assistant"""
    
    def __init__(self, project_root: str = '.'):
        self.project_root = project_root
        self.orchestrator: DevOrchestrator = get_orchestrator()
        self.phi_agent: PhiAgent = get_phi_agent()
        self.tools: Tools = Tools(project_root)
        
        # Configurer l orchestrateur
        self.orchestrator.set_phi_agent(self.phi_agent)
        self.orchestrator.set_tools(self.tools)
        
        self._remote_client = None
        self._error_callback = None
        
    def set_remote_client(self, client):
        self._remote_client = client
        self.orchestrator.set_remote_client(client)
        
    def set_error_callback(self, callback):
        self._error_callback = callback
    
    def analyze(self, context: str) -> dict:
        """Analyse un contexte avec Phi local"""
        try:
            obs = self.phi_agent.observe(context)
            diag = self.phi_agent.diagnose(obs)
            return {'success': True, 'observation': obs, 'diagnosis': diag}
        except Exception as e:
            logger.error(f'Erreur analyse: {e}')
            return {'success': False, 'error': str(e)}
    
    def execute(self, action: dict) -> dict:
        """Execute une action"""
        return self.orchestrator.execute_action(action)
    
    def run_cycle(self, context: str) -> list:
        """Execute un cycle complet"""
        return self.orchestrator.run_cycle(context)
    
    def detect_errors(self, log_content: str) -> dict:
        """Detecte les erreurs et notifie si necessaire"""
        errors = self.orchestrator.detect_errors(log_content)
        if errors and self._error_callback:
            self._error_callback(errors)
        return {'errors': errors, 'count': len(errors)}
    
    def get_file_summary(self, file_path: str) -> str:
        """Obtient un resume d un fichier via Phi"""
        content = self.tools.read_file(file_path)
        if content and not content.startswith('[Erreur'):
            return self.phi_agent.summarize_file(content, file_path)
        return content


# Singleton
_dev_assistant: Optional[DevAssistant] = None

def get_dev_assistant(project_root: str = '.') -> DevAssistant:
    global _dev_assistant
    if _dev_assistant is None:
        _dev_assistant = DevAssistant(project_root)
    return _dev_assistant
