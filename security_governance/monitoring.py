"""
Monitoring des performances et logging pour le module sécurité
Fournit des métriques, alertes et tableaux de bord pour le circuit breaker et cache
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
import json
import threading
from collections import deque

logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """Collecte et analyse les métriques de performance"""

    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.metrics_history = deque(maxlen=max_history)
        self._lock = threading.RLock()

        # Métriques par source
        self.source_metrics = {}
        self.circuit_breaker_stats = {}
        self.cache_stats = {}

    def record_request(
        self,
        source: str,
        method: str,
        duration: float,
        success: bool,
        cached: bool = False,
        circuit_state: str = None
    ):
        """Enregistre une requête"""
        with self._lock:
            timestamp = datetime.now()
            metric = {
                'timestamp': timestamp.isoformat(),
                'source': source,
                'method': method,
                'duration': duration,
                'success': success,
                'cached': cached,
                'circuit_state': circuit_state
            }

            self.metrics_history.append(metric)

            # Mettre à jour les statistiques par source
            if source not in self.source_metrics:
                self.source_metrics[source] = {
                    'total_requests': 0,
                    'successful_requests': 0,
                    'failed_requests': 0,
                    'cached_requests': 0,
                    'total_duration': 0.0,
                    'avg_duration': 0.0,
                    'last_request': None
                }

            source_metric = self.source_metrics[source]
            source_metric['total_requests'] += 1
            source_metric['total_duration'] += duration

            if success:
                source_metric['successful_requests'] += 1
            else:
                source_metric['failed_requests'] += 1

            if cached:
                source_metric['cached_requests'] += 1

            source_metric['avg_duration'] = source_metric['total_duration'] / source_metric['total_requests']
            source_metric['last_request'] = timestamp.isoformat()

            logger.debug(f"[METRICS] {source}.{method}: {duration:.2f}s, success={success}, cached={cached}")

    def record_circuit_breaker_event(
        self,
        breaker_name: str,
        event_type: str,
        old_state: str = None,
        new_state: str = None,
        failure_count: int = None
    ):
        """Enregistre un événement circuit breaker"""
        with self._lock:
            if breaker_name not in self.circuit_breaker_stats:
                self.circuit_breaker_stats[breaker_name] = {
                    'state_changes': [],
                    'total_failures': 0,
                    'total_successes': 0,
                    'open_count': 0,
                    'last_event': None
                }

            stats = self.circuit_breaker_stats[breaker_name]
            event = {
                'timestamp': datetime.now().isoformat(),
                'event_type': event_type,
                'old_state': old_state,
                'new_state': new_state,
                'failure_count': failure_count
            }

            stats['state_changes'].append(event)
            if len(stats['state_changes']) > 100:  # Limiter l'historique
                stats['state_changes'].pop(0)

            if event_type == 'failure':
                stats['total_failures'] += 1
            elif event_type == 'success':
                stats['total_successes'] += 1
            elif event_type == 'state_change' and new_state == 'open':
                stats['open_count'] += 1

            stats['last_event'] = event['timestamp']

            logger.info(f"[CIRCUIT METRICS] {breaker_name}: {event_type} ({old_state} -> {new_state})")

    def record_cache_event(
        self,
        source: str,
        event_type: str,
        cache_key: str = None,
        hit: bool = False,
        ttl_hours: float = None
    ):
        """Enregistre un événement cache"""
        with self._lock:
            if source not in self.cache_stats:
                self.cache_stats[source] = {
                    'hits': 0,
                    'misses': 0,
                    'sets': 0,
                    'invalidations': 0,
                    'total_size': 0,
                    'avg_ttl': 0.0,
                    'events': []
                }

            stats = self.cache_stats[source]
            event = {
                'timestamp': datetime.now().isoformat(),
                'event_type': event_type,
                'cache_key': cache_key,
                'hit': hit,
                'ttl_hours': ttl_hours
            }

            stats['events'].append(event)
            if len(stats['events']) > 100:
                stats['events'].pop(0)

            if event_type == 'hit':
                stats['hits'] += 1
            elif event_type == 'miss':
                stats['misses'] += 1
            elif event_type == 'set':
                stats['sets'] += 1
                if ttl_hours:
                    # Mettre à jour TTL moyen
                    total_ttl = stats['avg_ttl'] * (stats['sets'] - 1) + ttl_hours
                    stats['avg_ttl'] = total_ttl / stats['sets']
            elif event_type == 'invalidate':
                stats['invalidations'] += 1

            logger.debug(f"[CACHE METRICS] {source}: {event_type} (hit={hit})")

    def get_source_stats(self, source: str = None) -> Dict[str, Any]:
        """Retourne les statistiques par source"""
        with self._lock:
            if source:
                return self.source_metrics.get(source, {}).copy()

            # Statistiques globales
            total_stats = {
                'total_requests': 0,
                'successful_requests': 0,
                'failed_requests': 0,
                'cached_requests': 0,
                'avg_duration': 0.0,
                'sources': {}
            }

            for src, stats in self.source_metrics.items():
                total_stats['total_requests'] += stats['total_requests']
                total_stats['successful_requests'] += stats['successful_requests']
                total_stats['failed_requests'] += stats['failed_requests']
                total_stats['cached_requests'] += stats['cached_requests']
                total_stats['sources'][src] = stats.copy()

            if total_stats['total_requests'] > 0:
                total_stats['success_rate'] = (total_stats['successful_requests'] / total_stats['total_requests']) * 100
                total_stats['cache_hit_rate'] = (total_stats['cached_requests'] / total_stats['total_requests']) * 100
            else:
                total_stats['success_rate'] = 0
                total_stats['cache_hit_rate'] = 0

            return total_stats

    def get_circuit_breaker_stats(self, breaker_name: str = None) -> Dict[str, Any]:
        """Retourne les statistiques circuit breaker"""
        with self._lock:
            if breaker_name:
                return self.circuit_breaker_stats.get(breaker_name, {}).copy()

            # Statistiques globales
            global_stats = {
                'total_breakers': len(self.circuit_breaker_stats),
                'breakers': {},
                'total_failures': 0,
                'total_successes': 0,
                'currently_open': 0
            }

            for name, stats in self.circuit_breaker_stats.items():
                global_stats['breakers'][name] = stats.copy()
                global_stats['total_failures'] += stats['total_failures']
                global_stats['total_successes'] += stats['total_successes']

                # Vérifier état actuel (simplifié)
                if stats['state_changes']:
                    last_event = stats['state_changes'][-1]
                    if last_event.get('new_state') == 'open':
                        global_stats['currently_open'] += 1

            return global_stats

    def get_cache_stats(self, source: str = None) -> Dict[str, Any]:
        """Retourne les statistiques cache"""
        with self._lock:
            if source:
                return self.cache_stats.get(source, {}).copy()

            # Statistiques globales
            global_stats = {
                'total_sources': len(self.cache_stats),
                'sources': {},
                'total_hits': 0,
                'total_misses': 0,
                'total_sets': 0,
                'overall_hit_rate': 0.0
            }

            for src, stats in self.cache_stats.items():
                global_stats['sources'][src] = stats.copy()
                global_stats['total_hits'] += stats['hits']
                global_stats['total_misses'] += stats['misses']
                global_stats['total_sets'] += stats['sets']

            total_accesses = global_stats['total_hits'] + global_stats['total_misses']
            if total_accesses > 0:
                global_stats['overall_hit_rate'] = (global_stats['total_hits'] / total_accesses) * 100

            return global_stats

    def get_recent_metrics(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retourne les métriques récentes"""
        with self._lock:
            return list(self.metrics_history)[-limit:]

    def get_performance_summary(self) -> Dict[str, Any]:
        """Retourne un résumé complet des performances"""
        with self._lock:
            source_stats = self.get_source_stats()
            circuit_stats = self.get_circuit_breaker_stats()
            cache_stats = self.get_cache_stats()

            # Calculer les alertes
            alerts = self._generate_alerts(source_stats, circuit_stats, cache_stats)

            return {
                'timestamp': datetime.now().isoformat(),
                'source_stats': source_stats,
                'circuit_breaker_stats': circuit_stats,
                'cache_stats': cache_stats,
                'alerts': alerts,
                'metrics_count': len(self.metrics_history)
            }

    def _generate_alerts(self, source_stats: Dict, circuit_stats: Dict, cache_stats: Dict) -> List[Dict[str, Any]]:
        """Génère des alertes basées sur les métriques"""
        alerts = []

        # Vérifier les taux d'échec élevés
        for source, stats in source_stats.get('sources', {}).items():
            if stats['total_requests'] > 10:  # Seuil minimum
                failure_rate = (stats['failed_requests'] / stats['total_requests']) * 100
                if failure_rate > 30:  # 30% d'échec
                    alerts.append({
                        'level': 'warning',
                        'source': source,
                        'message': f"Taux d'échec élevé: {failure_rate:.1f}%",
                        'metric': 'failure_rate',
                        'value': failure_rate
                    })

                # Vérifier les temps de réponse lents
                if stats['avg_duration'] > 5.0:  # 5 secondes
                    alerts.append({
                        'level': 'warning',
                        'source': source,
                        'message': f"Temps de réponse élevé: {stats['avg_duration']:.2f}s",
                        'metric': 'response_time',
                        'value': stats['avg_duration']
                    })

        # Vérifier les circuit breakers ouverts
        if circuit_stats.get('currently_open', 0) > 0:
            alerts.append({
                'level': 'error',
                'source': 'circuit_breaker',
                'message': f"{circuit_stats['currently_open']} circuit breaker(s) ouvert(s)",
                'metric': 'open_circuits',
                'value': circuit_stats['currently_open']
            })

        # Vérifier le taux de cache hit bas
        if cache_stats.get('overall_hit_rate', 100) < 20:  # < 20%
            alerts.append({
                'level': 'warning',
                'source': 'cache',
                'message': f"Taux de cache hit bas: {cache_stats['overall_hit_rate']:.1f}%",
                'metric': 'cache_hit_rate',
                'value': cache_stats['overall_hit_rate']
            })

        return alerts

    def clear_metrics(self):
        """Efface toutes les métriques"""
        with self._lock:
            self.metrics_history.clear()
            self.source_metrics.clear()
            self.circuit_breaker_stats.clear()
            self.cache_stats.clear()
            logger.info("[METRICS] Toutes les métriques effacées")


class MonitoringMiddleware:
    """Middleware pour monitorer les appels de fonction"""

    def __init__(self, metrics_collector: PerformanceMetrics):
        self.metrics = metrics_collector

    def monitor_function(self, source: str, func: Callable):
        """Décorateur pour monitorer une fonction"""
        def wrapper(*args, **kwargs):
            start_time = time.time()
            cached = False
            circuit_state = None

            try:
                # Exécuter la fonction
                result = func(*args, **kwargs)

                # Déterminer si c'était un cache hit
                if isinstance(result, dict):
                    cached = result.get('_cached', False)
                    circuit_state = result.get('circuit_state')

                success = True
                return result

            except Exception as e:
                success = False
                raise

            finally:
                duration = time.time() - start_time
                self.metrics.record_request(
                    source=source,
                    method=func.__name__,
                    duration=duration,
                    success=success,
                    cached=cached,
                    circuit_state=circuit_state
                )

        return wrapper

    def monitor_circuit_breaker(self, breaker_name: str, func: Callable):
        """Décorateur pour monitorer un circuit breaker"""
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)

                # Enregistrer succès
                self.metrics.record_circuit_breaker_event(
                    breaker_name=breaker_name,
                    event_type='success'
                )

                return result

            except Exception as e:
                # Enregistrer échec
                self.metrics.record_circuit_breaker_event(
                    breaker_name=breaker_name,
                    event_type='failure',
                    failure_count=1
                )
                raise

        return wrapper


# Instance globale pour monitoring
performance_metrics = PerformanceMetrics()
monitoring_middleware = MonitoringMiddleware(performance_metrics)


def get_performance_dashboard() -> Dict[str, Any]:
    """Retourne un tableau de bord complet des performances"""
    try:
        summary = performance_metrics.get_performance_summary()

        # Ajouter des recommandations
        recommendations = []

        # Recommandations basées sur les alertes
        for alert in summary['alerts']:
            if alert['level'] == 'error':
                if alert['metric'] == 'open_circuits':
                    recommendations.append({
                        'priority': 'high',
                        'action': 'Vérifier la disponibilité des services externes',
                        'details': f"{alert['value']} circuit breaker(s) ouvert(s)"
                    })
            elif alert['level'] == 'warning':
                if alert['metric'] == 'failure_rate':
                    recommendations.append({
                        'priority': 'medium',
                        'action': 'Optimiser les appels à ' + alert['source'],
                        'details': f"Taux d'échec: {alert['value']:.1f}%"
                    })
                elif alert['metric'] == 'response_time':
                    recommendations.append({
                        'priority': 'medium',
                        'action': 'Réduire les timeouts ou optimiser ' + alert['source'],
                        'details': f"Temps de réponse: {alert['value']:.2f}s"
                    })
                elif alert['metric'] == 'cache_hit_rate':
                    recommendations.append({
                        'priority': 'low',
                        'action': 'Ajuster les stratégies de cache',
                        'details': f"Taux de cache hit: {alert['value']:.1f}%"
                    })

        summary['recommendations'] = recommendations
        return summary

    except Exception as e:
        logger.error(f"Erreur génération tableau de bord: {e}")
        return {
            'timestamp': datetime.now().isoformat(),
            'error': str(e),
            'alerts': [],
            'recommendations': []
        }


def export_metrics_to_json(filepath: str):
    """Exporte les métriques au format JSON"""
    try:
        dashboard = get_performance_dashboard()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(dashboard, f, indent=2, ensure_ascii=False)
        logger.info(f"[METRICS] Métriques exportées vers {filepath}")
    except Exception as e:
        logger.error(f"Erreur export métriques: {e}")


# Fonctions utilitaires pour intégration facile
def monitored_function(source: str):
    """Décorateur pour monitorer une fonction"""
    def decorator(func):
        return monitoring_middleware.monitor_function(source, func)
    return decorator


def monitored_circuit_breaker(breaker_name: str):
    """Décorateur pour monitorer un circuit breaker"""
    def decorator(func):
        return monitoring_middleware.monitor_circuit_breaker(breaker_name, func)
    return decorator