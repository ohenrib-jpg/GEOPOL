"""
Circuit Breaker Pattern pour les connecteurs sécurité et gouvernance
Protège contre les défaillances en cascade des services externes
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable, Tuple
from enum import Enum
import threading

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """États du circuit breaker"""
    CLOSED = "closed"      # Circuit fermé - fonctionnement normal
    OPEN = "open"          # Circuit ouvert - requêtes bloquées
    HALF_OPEN = "half_open"  # Circuit semi-ouvert - test de récupération


class CircuitBreaker:
    """
    Implémentation du pattern Circuit Breaker avec monitoring avancé

    Features:
    - Suivi des échecs/succès
    - Délai de réinitialisation configurable
    - Fallback automatique
    - Monitoring des performances
    - Logging détaillé
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 3,
        reset_timeout: int = 60,  # secondes
        half_open_max_requests: int = 1,
        fallback_func: Optional[Callable] = None,
        failure_timeout: int = 30,  # timeout pour considérer une requête comme échec
    ):
        """
        Args:
            name: Nom du circuit breaker (pour logging)
            failure_threshold: Nombre d'échecs avant ouverture
            reset_timeout: Délai avant tentative de récupération (secondes)
            half_open_max_requests: Nombre max de requêtes en état half-open
            fallback_func: Fonction de fallback à appeler quand circuit ouvert
            failure_timeout: Timeout pour considérer une requête comme échec
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.half_open_max_requests = half_open_max_requests
        self.fallback_func = fallback_func
        self.failure_timeout = failure_timeout

        # État initial
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_success_time = None
        self.half_open_attempts = 0

        # Statistiques
        self.total_requests = 0
        self.total_failures = 0
        self.total_successes = 0
        self.total_fallback_calls = 0

        # Performance tracking
        self.response_times = []
        self.max_response_time_history = 100

        # Lock pour thread safety
        self._lock = threading.RLock()

        logger.info(f"[CIRCUIT BREAKER] Initialisé '{name}': threshold={failure_threshold}, reset={reset_timeout}s")

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Exécute une fonction avec protection circuit breaker

        Args:
            func: Fonction à exécuter
            *args, **kwargs: Arguments pour la fonction

        Returns:
            Résultat de la fonction ou fallback
        """
        with self._lock:
            self.total_requests += 1

            # Vérifier l'état du circuit
            if self.state == CircuitState.OPEN:
                logger.warning(f"[CIRCUIT BREAKER] '{self.name}' ouvert - utilisation fallback")
                self.total_fallback_calls += 1

                # Vérifier si on peut passer en half-open
                if self._should_try_recovery():
                    logger.info(f"[CIRCUIT BREAKER] '{self.name}' tentative récupération -> half-open")
                    self.state = CircuitState.HALF_OPEN
                    self.half_open_attempts = 0
                else:
                    return self._execute_fallback(*args, **kwargs)

            # Exécuter la fonction avec timeout
            start_time = time.time()

            try:
                # Vérifier timeout pour éviter blocage
                import threading
                result = None
                exception = None

                def target():
                    nonlocal result, exception
                    try:
                        result = func(*args, **kwargs)
                    except Exception as e:
                        exception = e

                thread = threading.Thread(target=target)
                thread.daemon = True
                thread.start()
                thread.join(timeout=self.failure_timeout)

                if thread.is_alive():
                    # Timeout dépassé
                    logger.error(f"[CIRCUIT BREAKER] '{self.name}' timeout après {self.failure_timeout}s")
                    self._record_failure(f"Timeout après {self.failure_timeout}s")
                    return self._execute_fallback(*args, **kwargs)

                if exception:
                    raise exception

                # Succès
                response_time = time.time() - start_time
                self._record_success(response_time)
                return result

            except Exception as e:
                # Échec
                response_time = time.time() - start_time
                self._record_failure(str(e))

                # Si circuit ouvert, utiliser fallback
                if self.state == CircuitState.OPEN:
                    return self._execute_fallback(*args, **kwargs)
                else:
                    # Relancer l'exception pour traitement normal
                    raise

    def _should_try_recovery(self) -> bool:
        """Détermine si on peut tenter une récupération"""
        if not self.last_failure_time:
            return False

        elapsed = time.time() - self.last_failure_time
        return elapsed >= self.reset_timeout

    def _record_success(self, response_time: float):
        """Enregistre un succès"""
        with self._lock:
            self.success_count += 1
            self.total_successes += 1
            self.last_success_time = time.time()

            # Réinitialiser le compteur d'échecs
            self.failure_count = 0

            # Mettre à jour les statistiques de performance
            self.response_times.append(response_time)
            if len(self.response_times) > self.max_response_time_history:
                self.response_times.pop(0)

            # Gestion des états
            if self.state == CircuitState.HALF_OPEN:
                self.half_open_attempts += 1

                # Si succès en half-open, fermer le circuit
                if self.half_open_attempts >= self.half_open_max_requests:
                    logger.info(f"[CIRCUIT BREAKER] '{self.name}' récupération réussie -> fermé")
                    self.state = CircuitState.CLOSED
                    self.half_open_attempts = 0

            logger.debug(f"[CIRCUIT BREAKER] '{self.name}' succès - temps: {response_time:.2f}s")

    def _record_failure(self, error_msg: str):
        """Enregistre un échec"""
        with self._lock:
            self.failure_count += 1
            self.total_failures += 1
            self.last_failure_time = time.time()

            # Vérifier si on doit ouvrir le circuit
            if self.failure_count >= self.failure_threshold:
                if self.state != CircuitState.OPEN:
                    logger.error(f"[CIRCUIT BREAKER] '{self.name}' ouvert après {self.failure_count} échecs")
                    self.state = CircuitState.OPEN
            elif self.state == CircuitState.HALF_OPEN:
                # Échec en half-open -> retour à ouvert
                logger.warning(f"[CIRCUIT BREAKER] '{self.name}' échec en half-open -> ouvert")
                self.state = CircuitState.OPEN
                self.half_open_attempts = 0

            logger.warning(f"[CIRCUIT BREAKER] '{self.name}' échec #{self.failure_count}: {error_msg}")

    def _execute_fallback(self, *args, **kwargs) -> Any:
        """Exécute la fonction de fallback si disponible"""
        if self.fallback_func:
            try:
                logger.info(f"[CIRCUIT BREAKER] '{self.name}' exécution fallback")
                return self.fallback_func(*args, **kwargs)
            except Exception as e:
                logger.error(f"[CIRCUIT BREAKER] '{self.name}' échec fallback: {e}")

        # Fallback par défaut
        return {
            'success': False,
            'error': f'Circuit breaker ouvert pour {self.name}',
            'circuit_state': self.state.value,
            'timestamp': datetime.now().isoformat(),
            'fallback_used': self.fallback_func is not None
        }

    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du circuit breaker"""
        with self._lock:
            avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0

            return {
                'name': self.name,
                'state': self.state.value,
                'failure_count': self.failure_count,
                'success_count': self.success_count,
                'total_requests': self.total_requests,
                'total_failures': self.total_failures,
                'total_successes': self.total_successes,
                'total_fallback_calls': self.total_fallback_calls,
                'last_failure_time': datetime.fromtimestamp(self.last_failure_time).isoformat() if self.last_failure_time else None,
                'last_success_time': datetime.fromtimestamp(self.last_success_time).isoformat() if self.last_success_time else None,
                'avg_response_time': avg_response_time,
                'failure_rate': (self.total_failures / self.total_requests * 100) if self.total_requests > 0 else 0,
                'half_open_attempts': self.half_open_attempts,
                'reset_timeout': self.reset_timeout,
                'failure_threshold': self.failure_threshold
            }

    def reset(self):
        """Réinitialise complètement le circuit breaker"""
        with self._lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self.half_open_attempts = 0
            logger.info(f"[CIRCUIT BREAKER] '{self.name}' réinitialisé")

    def is_available(self) -> bool:
        """Vérifie si le circuit est disponible pour les requêtes"""
        with self._lock:
            if self.state == CircuitState.CLOSED:
                return True
            elif self.state == CircuitState.HALF_OPEN:
                return self.half_open_attempts < self.half_open_max_requests
            else:  # OPEN
                return self._should_try_recovery()


class CircuitBreakerManager:
    """
    Gestionnaire centralisé pour les circuit breakers
    """

    _instance = None
    _breakers: Dict[str, CircuitBreaker] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_breaker(
        cls,
        name: str,
        failure_threshold: int = 3,
        reset_timeout: int = 60,
        fallback_func: Optional[Callable] = None
    ) -> CircuitBreaker:
        """
        Obtient ou crée un circuit breaker

        Args:
            name: Nom unique du breaker
            failure_threshold: Seuil d'échecs
            reset_timeout: Délai de réinitialisation
            fallback_func: Fonction de fallback

        Returns:
            Instance CircuitBreaker
        """
        if name not in cls._breakers:
            cls._breakers[name] = CircuitBreaker(
                name=name,
                failure_threshold=failure_threshold,
                reset_timeout=reset_timeout,
                fallback_func=fallback_func
            )

        return cls._breakers[name]

    @classmethod
    def get_all_stats(cls) -> Dict[str, Dict[str, Any]]:
        """Retourne les statistiques de tous les breakers"""
        return {name: breaker.get_stats() for name, breaker in cls._breakers.items()}

    @classmethod
    def reset_all(cls):
        """Réinitialise tous les breakers"""
        for breaker in cls._breakers.values():
            breaker.reset()
        logger.info("[CIRCUIT BREAKER] Tous les breakers réinitialisés")

    @classmethod
    def get_breaker_names(cls) -> list:
        """Retourne la liste des noms de breakers"""
        return list(cls._breakers.keys())


# Fonctions utilitaires pour intégration facile
def with_circuit_breaker(
    breaker_name: str,
    failure_threshold: int = 3,
    reset_timeout: int = 60,
    fallback_func: Optional[Callable] = None
):
    """
    Décorateur pour ajouter un circuit breaker à une fonction

    Usage:
        @with_circuit_breaker('ofac_api', failure_threshold=3, reset_timeout=60)
        def fetch_ofac_data():
            # logique de récupération
            return data
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            breaker = CircuitBreakerManager.get_breaker(
                name=breaker_name,
                failure_threshold=failure_threshold,
                reset_timeout=reset_timeout,
                fallback_func=fallback_func
            )
            return breaker.call(func, *args, **kwargs)
        return wrapper
    return decorator


# Instance globale pour accès facile
circuit_manager = CircuitBreakerManager()