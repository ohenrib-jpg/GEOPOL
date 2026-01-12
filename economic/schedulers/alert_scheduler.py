"""
Scheduler pour la vérification périodique des alertes économiques
"""
import schedule
import time
import logging
import threading
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AlertScheduler:
    """Scheduler pour la vérification des alertes économiques"""

    def __init__(self, alert_service, market_service, commodity_service,
                 international_service, france_service):
        """
        Initialise le scheduler d'alertes

        Args:
            alert_service: Instance de AlertService
            market_service: Instance de MarketService
            commodity_service: Instance de CommodityService
            international_service: Instance de InternationalService
            france_service: Instance de FranceService
        """
        self.alert_service = alert_service
        self.market_service = market_service
        self.commodity_service = commodity_service
        self.international_service = international_service
        self.france_service = france_service

        self.running = False
        self.thread = None

        logger.info("[SCHEDULER] AlertScheduler initialisé")

    def _get_indicator_value(self, indicator_id: str, indicator_type: str) -> Optional[Dict[str, Any]]:
        """
        Récupère la valeur actuelle d'un indicateur selon son type

        Args:
            indicator_id: ID de l'indicateur
            indicator_type: Type d'indicateur

        Returns:
            Dictionnaire avec les données de l'indicateur ou None
        """
        try:
            if indicator_type == 'index':
                # Récupérer depuis market_service
                indices = self.market_service.get_market_indices()
                for idx in indices:
                    if idx.get('id') == indicator_id or idx.get('symbol') == indicator_id:
                        return idx
            elif indicator_type == 'commodity':
                # Récupérer depuis commodity_service
                commodities = self.commodity_service.get_commodity_prices()
                for comm in commodities:
                    if comm.get('id') == indicator_id or comm.get('symbol') == indicator_id:
                        return comm
            elif indicator_type == 'forex':
                # Récupérer depuis international_service
                forex_data = self.international_service.get_forex_data()
                for forex in forex_data:
                    if forex.get('id') == indicator_id:
                        return forex
            elif indicator_type == 'macro':
                # Récupérer depuis international_service
                macro_data = self.international_service.get_macro_data()
                for macro in macro_data:
                    if macro.get('id') == indicator_id:
                        return macro
            elif indicator_type == 'crypto':
                # Récupérer depuis market_service
                crypto_data = self.market_service.get_crypto_data()
                for crypto in crypto_data:
                    if crypto.get('symbol') == indicator_id or crypto.get('id') == indicator_id:
                        return crypto
            elif indicator_type == 'france':
                # Récupérer depuis france_service
                france_data = self.france_service.get_france_indicators()
                for indicator in france_data:
                    if indicator.get('id') == indicator_id or indicator.get('name') == indicator_id:
                        return indicator

            logger.warning(f"[SCHEDULER] Indicateur non trouvé: {indicator_id} ({indicator_type})")
            return None

        except Exception as e:
            logger.error(f"[SCHEDULER] Erreur récupération indicateur {indicator_id}: {e}")
            return None

    def _get_historical_value(self, indicator_id: str, indicator_type: str,
                             hours_ago: int = 24) -> Optional[float]:
        """
        Récupère la valeur historique d'un indicateur

        Args:
            indicator_id: ID de l'indicateur
            indicator_type: Type d'indicateur
            hours_ago: Nombre d'heures à remonter

        Returns:
            Valeur historique ou None
        """
        # Pour l'instant, on retourne None car la récupération d'historique
        # nécessite une implémentation spécifique
        # TODO: Implémenter la récupération d'historique
        return None

    def check_alerts(self):
        """Vérifie toutes les alertes actives"""
        try:
            logger.info("[SCHEDULER] Début vérification des alertes")
            start_time = time.time()

            # Récupérer les alertes actives
            alerts = self.alert_service.get_active_alerts()
            if not alerts:
                logger.info("[SCHEDULER] Aucune alerte active à vérifier")
                return

            logger.info(f"[SCHEDULER] Vérification de {len(alerts)} alerte(s) active(s)")

            triggered_count = 0
            for alert in alerts:
                try:
                    # Récupérer la valeur actuelle
                    current_data = self._get_indicator_value(
                        alert.indicator_id, alert.indicator_type
                    )
                    if not current_data or 'value' not in current_data:
                        logger.warning(f"[SCHEDULER] Données manquantes pour {alert.indicator_id}")
                        continue

                    current_value = float(current_data['value'])

                    # Récupérer la valeur précédente (pour calcul de variation)
                    previous_value = None
                    if alert.condition in ['change_abs', 'change_pct', 'increase_abs',
                                         'decrease_abs', 'increase_pct', 'decrease_pct']:
                        previous_value = self._get_historical_value(
                            alert.indicator_id, alert.indicator_type, hours_ago=24
                        )

                    # Évaluer l'alerte
                    should_trigger = self.alert_service.evaluate_alert(
                        alert, current_value, previous_value
                    )

                    # Déclencher si nécessaire
                    if should_trigger:
                        logger.info(f"[SCHEDULER] Alerte déclenchée: {alert.name}")
                        self.alert_service.trigger_alert(
                            alert, current_value, previous_value
                        )
                        triggered_count += 1

                except Exception as e:
                    logger.error(f"[SCHEDULER] Erreur vérification alerte {alert.id}: {e}")
                    continue

            elapsed = time.time() - start_time
            logger.info(f"[SCHEDULER] Vérification terminée: {triggered_count} alerte(s) déclenchée(s) en {elapsed:.2f}s")

        except Exception as e:
            logger.error(f"[SCHEDULER] Erreur générale vérification alertes: {e}")

    def start(self, interval_minutes: int = 15):
        """
        Démarre le scheduler

        Args:
            interval_minutes: Intervalle de vérification en minutes
        """
        if self.running:
            logger.warning("[SCHEDULER] Déjà en cours d'exécution")
            return

        logger.info(f"[SCHEDULER] Démarrage avec intervalle de {interval_minutes} minutes")

        # Planifier la vérification
        schedule.every(interval_minutes).minutes.do(self.check_alerts)

        # Exécuter une vérification immédiate au démarrage
        self.check_alerts()

        # Démarrer le thread de scheduler
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()

        logger.info("[SCHEDULER] Scheduler démarré")

    def stop(self):
        """Arrête le scheduler"""
        if not self.running:
            return

        logger.info("[SCHEDULER] Arrêt en cours...")
        self.running = False

        if self.thread:
            self.thread.join(timeout=10)

        logger.info("[SCHEDULER] Arrêté")

    def _run_scheduler(self):
        """Boucle d'exécution du scheduler"""
        logger.info("[SCHEDULER] Thread scheduler démarré")
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Vérifier toutes les minutes
            except Exception as e:
                logger.error(f"[SCHEDULER] Erreur dans la boucle scheduler: {e}")
                time.sleep(60)

        logger.info("[SCHEDULER] Thread scheduler terminé")

    def get_status(self) -> Dict[str, Any]:
        """Retourne le statut du scheduler"""
        return {
            'running': self.running,
            'next_run': str(schedule.next_run()) if schedule.jobs else None,
            'job_count': len(schedule.jobs)
        }