# Flask/api_monitoring.py
"""
Système de monitoring des APIs pour Geopol Analytics
Surveille les taux de succès, fallbacks et alertes
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict
import json
import os

logger = logging.getLogger(__name__)


class APIMonitor:
    """Moniteur de santé des APIs"""

    def __init__(self, log_file: str = 'logs/api_monitoring.json'):
        self.log_file = log_file
        self.stats = defaultdict(lambda: {
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'fallback_calls': 0,
            'last_success': None,
            'last_failure': None,
            'error_messages': []
        })

        # Seuils d'alerte
        self.ALERT_FALLBACK_THRESHOLD = 0.5  # 50% de fallback
        self.ALERT_FAILURE_THRESHOLD = 0.3   # 30% d'échecs

        # Charger l'historique si disponible
        self._load_stats()

    def _load_stats(self):
        """Charge les statistiques depuis le fichier"""
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r') as f:
                    loaded_stats = json.load(f)
                    self.stats.update(loaded_stats)
                logger.info(f"[OK] Statistiques chargées depuis {self.log_file}")
        except Exception as e:
            logger.warning(f"[WARN] Impossible de charger les stats: {e}")

    def _save_stats(self):
        """Sauvegarde les statistiques"""
        try:
            os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
            with open(self.log_file, 'w') as f:
                json.dump(dict(self.stats), f, indent=2, default=str)
        except Exception as e:
            logger.error(f"[ERROR] Erreur sauvegarde stats: {e}")

    def record_api_call(self, api_name: str, result: Dict[str, Any]):
        """
        Enregistre un appel API

        Args:
            api_name: Nom de l'API (ex: 'Eurostat', 'World Bank', 'yFinance')
            result: Résultat de l'appel avec data_source
        """
        stats = self.stats[api_name]
        stats['total_calls'] += 1

        # Analyser le résultat
        success = result.get('success', False)
        data_source = result.get('data_source', {})
        source_type = data_source.get('type', 'unknown')

        if success and source_type == 'real_api':
            stats['successful_calls'] += 1
            stats['last_success'] = datetime.now().isoformat()

        elif success and source_type == 'fallback':
            stats['fallback_calls'] += 1
            stats['last_success'] = datetime.now().isoformat()

        else:
            stats['failed_calls'] += 1
            stats['last_failure'] = datetime.now().isoformat()

            # Enregistrer le message d'erreur
            error_msg = result.get('error', 'Unknown error')
            if len(stats['error_messages']) < 10:  # Garder les 10 dernières erreurs
                stats['error_messages'].append({
                    'timestamp': datetime.now().isoformat(),
                    'error': error_msg
                })

        # Sauvegarder
        self._save_stats()

        # Vérifier si alerte nécessaire
        self._check_alerts(api_name)

    def _check_alerts(self, api_name: str):
        """Vérifie si des alertes doivent être émises"""
        stats = self.stats[api_name]
        total = stats['total_calls']

        if total == 0:
            return

        # Taux de fallback
        fallback_rate = stats['fallback_calls'] / total
        if fallback_rate > self.ALERT_FALLBACK_THRESHOLD:
            logger.warning(
                f"🔴 ALERTE {api_name}: Taux de fallback élevé "
                f"({fallback_rate * 100:.1f}% > {self.ALERT_FALLBACK_THRESHOLD * 100:.0f}%)"
            )

        # Taux d'échec
        failure_rate = stats['failed_calls'] / total
        if failure_rate > self.ALERT_FAILURE_THRESHOLD:
            logger.error(
                f"🔴 ALERTE {api_name}: Taux d'échec élevé "
                f"({failure_rate * 100:.1f}% > {self.ALERT_FAILURE_THRESHOLD * 100:.0f}%)"
            )

    def get_health_status(self, api_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Récupère le statut de santé

        Args:
            api_name: Nom de l'API (None pour toutes)

        Returns:
            Dict avec statut de santé
        """
        if api_name:
            return self._compute_api_health(api_name)
        else:
            return {
                api: self._compute_api_health(api)
                for api in self.stats.keys()
            }

    def _compute_api_health(self, api_name: str) -> Dict[str, Any]:
        """Calcule le statut de santé d'une API"""
        stats = self.stats[api_name]
        total = stats['total_calls']

        if total == 0:
            return {
                'api': api_name,
                'status': 'unknown',
                'health_score': 0,
                'message': 'Aucun appel enregistré'
            }

        # Calculer les taux
        success_rate = stats['successful_calls'] / total
        fallback_rate = stats['fallback_calls'] / total
        failure_rate = stats['failed_calls'] / total

        # Health score (0-100)
        # 100% si succès API réel, 70% si fallback, 0% si échec
        health_score = (
            success_rate * 100 +
            fallback_rate * 70
        )

        # Déterminer le statut
        if health_score >= 90:
            status = 'excellent'
            emoji = '🟢'
        elif health_score >= 70:
            status = 'good'
            emoji = '🟡'
        elif health_score >= 50:
            status = 'degraded'
            emoji = '🟠'
        else:
            status = 'critical'
            emoji = '🔴'

        return {
            'api': api_name,
            'status': status,
            'emoji': emoji,
            'health_score': round(health_score, 1),
            'total_calls': total,
            'success_rate': round(success_rate * 100, 1),
            'fallback_rate': round(fallback_rate * 100, 1),
            'failure_rate': round(failure_rate * 100, 1),
            'last_success': stats['last_success'],
            'last_failure': stats['last_failure'],
            'recent_errors': stats['error_messages'][-3:]  # 3 dernières erreurs
        }

    def get_dashboard_data(self) -> Dict[str, Any]:
        """Récupère les données pour le dashboard de monitoring"""
        all_health = self.get_health_status()

        # Calculer score global
        if all_health:
            global_score = sum(h['health_score'] for h in all_health.values()) / len(all_health)
        else:
            global_score = 0

        # Déterminer statut global
        if global_score >= 90:
            global_status = 'excellent'
            global_emoji = '🟢'
        elif global_score >= 70:
            global_status = 'good'
            global_emoji = '🟡'
        elif global_score >= 50:
            global_status = 'degraded'
            global_emoji = '🟠'
        else:
            global_status = 'critical'
            global_emoji = '🔴'

        return {
            'global_status': global_status,
            'global_emoji': global_emoji,
            'global_score': round(global_score, 1),
            'apis': all_health,
            'timestamp': datetime.now().isoformat(),
            'alerts': self._get_active_alerts()
        }

    def _get_active_alerts(self) -> List[Dict[str, Any]]:
        """Récupère les alertes actives"""
        alerts = []

        for api_name, stats in self.stats.items():
            total = stats['total_calls']
            if total == 0:
                continue

            fallback_rate = stats['fallback_calls'] / total
            failure_rate = stats['failed_calls'] / total

            if fallback_rate > self.ALERT_FALLBACK_THRESHOLD:
                alerts.append({
                    'api': api_name,
                    'type': 'high_fallback',
                    'severity': 'warning',
                    'rate': round(fallback_rate * 100, 1),
                    'message': f'Taux de fallback élevé ({fallback_rate * 100:.1f}%)'
                })

            if failure_rate > self.ALERT_FAILURE_THRESHOLD:
                alerts.append({
                    'api': api_name,
                    'type': 'high_failure',
                    'severity': 'critical',
                    'rate': round(failure_rate * 100, 1),
                    'message': f'Taux d\'échec élevé ({failure_rate * 100:.1f}%)'
                })

        return alerts

    def reset_stats(self, api_name: Optional[str] = None):
        """Réinitialise les statistiques"""
        if api_name:
            if api_name in self.stats:
                del self.stats[api_name]
                logger.info(f"[OK] Stats {api_name} réinitialisées")
        else:
            self.stats.clear()
            logger.info("[OK] Toutes les stats réinitialisées")

        self._save_stats()


# Instance globale
_monitor = None


def get_monitor() -> APIMonitor:
    """Récupère l'instance singleton du moniteur"""
    global _monitor
    if _monitor is None:
        _monitor = APIMonitor()
    return _monitor


# Export
__all__ = ['APIMonitor', 'get_monitor']


# Test si exécuté directement
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    print("=" * 70)
    print("TEST API MONITORING")
    print("=" * 70)

    monitor = APIMonitor(log_file='logs/test_monitoring.json')

    # Simuler des appels
    print("\n1. Simulation d'appels API...")

    # Eurostat: 70% succès, 30% fallback
    for i in range(10):
        if i < 7:
            monitor.record_api_call('Eurostat', {
                'success': True,
                'data_source': {'type': 'real_api', 'api': 'Eurostat'}
            })
        else:
            monitor.record_api_call('Eurostat', {
                'success': True,
                'data_source': {'type': 'fallback', 'api': 'CRM Act'}
            })

    # World Bank: 95% succès
    for i in range(20):
        if i < 19:
            monitor.record_api_call('World Bank', {
                'success': True,
                'data_source': {'type': 'real_api', 'api': 'World Bank'}
            })
        else:
            monitor.record_api_call('World Bank', {
                'success': False,
                'error': 'Timeout'
            })

    # yFinance: 60% succès, 40% échec (simule marché fermé)
    for i in range(10):
        if i < 6:
            monitor.record_api_call('yFinance', {
                'success': True,
                'data_source': {'type': 'real_api', 'api': 'Yahoo Finance'}
            })
        else:
            monitor.record_api_call('yFinance', {
                'success': False,
                'error': 'Market closed'
            })

    # Afficher le dashboard
    print("\n2. Dashboard de santé:")
    print("-" * 70)

    dashboard = monitor.get_dashboard_data()

    print(f"\nStatut global: {dashboard['global_emoji']} {dashboard['global_status'].upper()}")
    print(f"Score global: {dashboard['global_score']}/100")

    print("\nAPIs:")
    for api, health in dashboard['apis'].items():
        print(f"\n  {health['emoji']} {api}: {health['status'].upper()} ({health['health_score']}/100)")
        print(f"     Succès: {health['success_rate']}%")
        print(f"     Fallback: {health['fallback_rate']}%")
        print(f"     Échecs: {health['failure_rate']}%")

    if dashboard['alerts']:
        print("\n[WARN] ALERTES:")
        for alert in dashboard['alerts']:
            print(f"  - {alert['api']}: {alert['message']}")

    print("\n" + "=" * 70)
    print("TEST TERMINÉ")
    print("=" * 70)
