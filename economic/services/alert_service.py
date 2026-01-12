"""
Service de gestion des alertes économiques
"""
import logging
import sqlite3
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from .base_service import BaseEconomicService
from ..models.alert import EconomicAlert, TriggeredAlert
from ..config import EconomicConfig

logger = logging.getLogger(__name__)

class AlertService(BaseEconomicService):
    """Service de gestion des alertes économiques"""

    def __init__(self, db_manager):
        """
        Initialise le service d'alertes

        Args:
            db_manager: Instance du DatabaseManager
        """
        super().__init__(db_manager)
        self.init_alert_tables()

    def init_alert_tables(self):
        """Initialise les tables d'alertes dans la base de données"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()

            # Table des alertes configurées
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS economic_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    indicator_id TEXT NOT NULL,
                    indicator_type TEXT NOT NULL,
                    condition TEXT NOT NULL,
                    threshold REAL NOT NULL,
                    threshold_type TEXT NOT NULL,
                    active BOOLEAN DEFAULT 1,
                    user_id INTEGER,
                    email_notification BOOLEAN DEFAULT 1,
                    dashboard_notification BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Table des alertes déclenchées
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS triggered_economic_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_id INTEGER NOT NULL,
                    indicator_id TEXT NOT NULL,
                    indicator_type TEXT NOT NULL,
                    actual_value REAL NOT NULL,
                    threshold REAL NOT NULL,
                    condition TEXT NOT NULL,
                    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notified BOOLEAN DEFAULT 0,
                    notification_sent_at TIMESTAMP,
                    FOREIGN KEY (alert_id) REFERENCES economic_alerts(id)
                )
            """)

            # Index pour les performances
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_economic_alerts_active
                ON economic_alerts(active)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_triggered_alerts_alert_id
                ON triggered_economic_alerts(alert_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_triggered_alerts_triggered_at
                ON triggered_economic_alerts(triggered_at)
            """)

            conn.commit()
            conn.close()
            logger.info("[ALERTS] Tables d'alertes initialisées")

        except Exception as e:
            logger.error(f"[ALERTS] Erreur initialisation tables: {e}")
            raise

    def create_alert(self, alert: EconomicAlert) -> int:
        """
        Crée une nouvelle alerte

        Args:
            alert: Configuration de l'alerte

        Returns:
            ID de l'alerte créée
        """
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO economic_alerts
                (name, description, indicator_id, indicator_type, condition,
                 threshold, threshold_type, active, user_id, email_notification,
                 dashboard_notification, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alert.name,
                alert.description,
                alert.indicator_id,
                alert.indicator_type,
                alert.condition,
                alert.threshold,
                alert.threshold_type,
                alert.active,
                alert.user_id,
                alert.email_notification,
                alert.dashboard_notification,
                alert.created_at.isoformat(),
                alert.updated_at.isoformat()
            ))

            alert_id = cursor.lastrowid
            conn.commit()
            conn.close()

            logger.info(f"[ALERTS] Alerte créée: {alert.name} (ID: {alert_id})")
            return alert_id

        except Exception as e:
            logger.error(f"[ALERTS] Erreur création alerte: {e}")
            raise

    def get_alert(self, alert_id: int) -> Optional[EconomicAlert]:
        """
        Récupère une alerte par son ID

        Args:
            alert_id: ID de l'alerte

        Returns:
            EconomicAlert ou None si non trouvée
        """
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM economic_alerts WHERE id = ?
            """, (alert_id,))

            row = cursor.fetchone()
            conn.close()

            if row:
                return self._row_to_alert(row)
            return None

        except Exception as e:
            logger.error(f"[ALERTS] Erreur récupération alerte {alert_id}: {e}")
            return None

    def get_all_alerts(self) -> List[EconomicAlert]:
        """
        Récupère toutes les alertes

        Returns:
            Liste des alertes
        """
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM economic_alerts ORDER BY created_at DESC
            """)

            alerts = []
            for row in cursor.fetchall():
                alerts.append(self._row_to_alert(row))

            conn.close()
            return alerts

        except Exception as e:
            logger.error(f"[ALERTS] Erreur récupération alertes: {e}")
            return []

    def get_active_alerts(self) -> List[EconomicAlert]:
        """
        Récupère les alertes actives

        Returns:
            Liste des alertes actives
        """
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT * FROM economic_alerts
                WHERE active = 1
                ORDER BY created_at DESC
            """)

            alerts = []
            for row in cursor.fetchall():
                alerts.append(self._row_to_alert(row))

            conn.close()
            return alerts

        except Exception as e:
            logger.error(f"[ALERTS] Erreur récupération alertes actives: {e}")
            return []

    def update_alert(self, alert_id: int, alert: EconomicAlert) -> bool:
        """
        Met à jour une alerte

        Args:
            alert_id: ID de l'alerte à mettre à jour
            alert: Nouvelles données de l'alerte

        Returns:
            True si mise à jour réussie
        """
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE economic_alerts
                SET name = ?, description = ?, indicator_id = ?, indicator_type = ?,
                    condition = ?, threshold = ?, threshold_type = ?, active = ?,
                    user_id = ?, email_notification = ?, dashboard_notification = ?,
                    updated_at = ?
                WHERE id = ?
            """, (
                alert.name,
                alert.description,
                alert.indicator_id,
                alert.indicator_type,
                alert.condition,
                alert.threshold,
                alert.threshold_type,
                alert.active,
                alert.user_id,
                alert.email_notification,
                alert.dashboard_notification,
                datetime.utcnow().isoformat(),
                alert_id
            ))

            success = cursor.rowcount > 0
            conn.commit()
            conn.close()

            if success:
                logger.info(f"[ALERTS] Alerte mise à jour: {alert_id}")
            return success

        except Exception as e:
            logger.error(f"[ALERTS] Erreur mise à jour alerte {alert_id}: {e}")
            return False

    def delete_alert(self, alert_id: int) -> bool:
        """
        Supprime une alerte

        Args:
            alert_id: ID de l'alerte à supprimer

        Returns:
            True si suppression réussie
        """
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()

            # Supprimer d'abord les alertes déclenchées associées
            cursor.execute("""
                DELETE FROM triggered_economic_alerts WHERE alert_id = ?
            """, (alert_id,))

            # Supprimer l'alerte
            cursor.execute("""
                DELETE FROM economic_alerts WHERE id = ?
            """, (alert_id,))

            success = cursor.rowcount > 0
            conn.commit()
            conn.close()

            if success:
                logger.info(f"[ALERTS] Alerte supprimée: {alert_id}")
            return success

        except Exception as e:
            logger.error(f"[ALERTS] Erreur suppression alerte {alert_id}: {e}")
            return False

    def toggle_alert(self, alert_id: int, active: bool) -> bool:
        """
        Active/désactive une alerte

        Args:
            alert_id: ID de l'alerte
            active: Nouvel état

        Returns:
            True si mise à jour réussie
        """
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE economic_alerts
                SET active = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (active, alert_id))

            success = cursor.rowcount > 0
            conn.commit()
            conn.close()

            if success:
                status = "activée" if active else "désactivée"
                logger.info(f"[ALERTS] Alerte {status}: {alert_id}")
            return success

        except Exception as e:
            logger.error(f"[ALERTS] Erreur changement état alerte {alert_id}: {e}")
            return False

    def evaluate_alert(self, alert: EconomicAlert, current_value: float,
                      previous_value: Optional[float] = None) -> bool:
        """
        Évalue si une alerte doit être déclenchée

        Args:
            alert: Alerte à évaluer
            current_value: Valeur actuelle de l'indicateur
            previous_value: Valeur précédente (pour calcul de variation)

        Returns:
            True si l'alerte doit être déclenchée
        """
        try:
            condition = alert.condition
            threshold = alert.threshold

            if condition == '>':
                return current_value > threshold
            elif condition == '<':
                return current_value < threshold
            elif condition == 'change_abs' and previous_value is not None:
                change = abs(current_value - previous_value)
                return change > threshold
            elif condition == 'change_pct' and previous_value is not None and previous_value != 0:
                change_pct = abs((current_value - previous_value) / previous_value) * 100
                return change_pct > threshold
            elif condition == 'increase_abs' and previous_value is not None:
                return (current_value - previous_value) > threshold
            elif condition == 'decrease_abs' and previous_value is not None:
                return (previous_value - current_value) > threshold
            elif condition == 'increase_pct' and previous_value is not None and previous_value != 0:
                change_pct = ((current_value - previous_value) / previous_value) * 100
                return change_pct > threshold
            elif condition == 'decrease_pct' and previous_value is not None and previous_value != 0:
                change_pct = ((previous_value - current_value) / previous_value) * 100
                return change_pct > threshold

            return False

        except Exception as e:
            logger.error(f"[ALERTS] Erreur évaluation alerte {alert.id}: {e}")
            return False

    def trigger_alert(self, alert: EconomicAlert, current_value: float,
                     previous_value: Optional[float] = None) -> Optional[int]:
        """
        Déclenche une alerte et l'enregistre

        Args:
            alert: Alerte à déclencher
            current_value: Valeur actuelle
            previous_value: Valeur précédente

        Returns:
            ID de l'alerte déclenchée ou None
        """
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO triggered_economic_alerts
                (alert_id, indicator_id, indicator_type, actual_value,
                 threshold, condition, triggered_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                alert.id,
                alert.indicator_id,
                alert.indicator_type,
                current_value,
                alert.threshold,
                alert.condition,
                datetime.utcnow().isoformat()
            ))

            triggered_id = cursor.lastrowid
            conn.commit()
            conn.close()

            logger.info(f"[ALERTS] Alerte déclenchée: {alert.name} (ID: {triggered_id})")

            # Envoyer notification si configuré
            if alert.email_notification:
                self._send_alert_notification(alert, current_value, previous_value)

            # Marquer comme notifié
            self._mark_as_notified(triggered_id)

            return triggered_id

        except Exception as e:
            logger.error(f"[ALERTS] Erreur déclenchement alerte {alert.id}: {e}")
            return None

    def get_recent_triggered_alerts(self, hours: int = 24) -> List[TriggeredAlert]:
        """
        Récupère les alertes récemment déclenchées

        Args:
            hours: Nombre d'heures à remonter

        Returns:
            Liste des alertes déclenchées
        """
        try:
            since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()

            conn = self.db_manager.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT t.*, a.name as alert_name
                FROM triggered_economic_alerts t
                JOIN economic_alerts a ON t.alert_id = a.id
                WHERE t.triggered_at >= ?
                ORDER BY t.triggered_at DESC
            """, (since,))

            alerts = []
            for row in cursor.fetchall():
                alerts.append(self._row_to_triggered_alert(row))

            conn.close()
            return alerts

        except Exception as e:
            logger.error(f"[ALERTS] Erreur récupération alertes déclenchées: {e}")
            return []

    def cleanup_old_triggered_alerts(self, days: int = 30) -> int:
        """
        Nettoie les anciennes alertes déclenchées

        Args:
            days: Nombre de jours à conserver

        Returns:
            Nombre d'alertes supprimées
        """
        try:
            cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()

            conn = self.db_manager.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                DELETE FROM triggered_economic_alerts
                WHERE triggered_at < ?
            """, (cutoff,))

            deleted = cursor.rowcount
            conn.commit()
            conn.close()

            logger.info(f"[ALERTS] Alertes déclenchées nettoyées: {deleted}")
            return deleted

        except Exception as e:
            logger.error(f"[ALERTS] Erreur nettoyage alertes: {e}")
            return 0

    def _row_to_alert(self, row) -> EconomicAlert:
        """Convertit une ligne SQL en objet EconomicAlert"""
        return EconomicAlert(
            id=row[0],
            name=row[1],
            description=row[2],
            indicator_id=row[3],
            indicator_type=row[4],
            condition=row[5],
            threshold=row[6],
            threshold_type=row[7],
            active=bool(row[8]),
            user_id=row[9],
            email_notification=bool(row[10]),
            dashboard_notification=bool(row[11]),
            created_at=datetime.fromisoformat(row[12].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(row[13].replace('Z', '+00:00'))
        )

    def _row_to_triggered_alert(self, row) -> TriggeredAlert:
        """Convertit une ligne SQL en objet TriggeredAlert"""
        return TriggeredAlert(
            id=row[0],
            alert_id=row[1],
            indicator_id=row[2],
            indicator_type=row[3],
            actual_value=row[4],
            threshold=row[5],
            condition=row[6],
            triggered_at=datetime.fromisoformat(row[7].replace('Z', '+00:00')),
            notified=bool(row[8]),
            notification_sent_at=datetime.fromisoformat(row[9].replace('Z', '+00:00')) if row[9] else None
        )

    def _send_alert_notification(self, alert: EconomicAlert, current_value: float,
                                previous_value: Optional[float] = None):
        """
        Envoie une notification d'alerte par email

        Args:
            alert: Alerte déclenchée
            current_value: Valeur actuelle
            previous_value: Valeur précédente
        """
        try:
            # Importer le service d'email depuis geopol_data
            from ...geopol_data.email_service import EmailService
            import os

            # Récupérer la configuration email
            smtp_server = os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = int(os.getenv('EMAIL_SMTP_PORT', 587))
            email_from = os.getenv('EMAIL_FROM', '')
            email_password = os.getenv('EMAIL_PASSWORD', '')

            if not email_from or not email_password:
                logger.warning("[ALERTS] Configuration email manquante, notification non envoyée")
                return

            # Récupérer l'email de l'utilisateur (pour l'instant, utiliser un email par défaut)
            # TODO: Récupérer l'email de l'utilisateur depuis la base de données
            user_email = os.getenv('ALERT_EMAIL_TO', email_from)

            # Créer le service email
            email_service = EmailService(smtp_server, smtp_port, email_from, email_password)

            # Préparer les données de l'alerte
            alert_data = {
                'alert_name': alert.name,
                'indicator': alert.indicator_id,
                'indicator_type': alert.indicator_type,
                'actual_value': current_value,
                'threshold': alert.threshold,
                'condition': alert.condition,
                'previous_value': previous_value,
                'triggered_at': datetime.utcnow().isoformat()
            }

            # Envoyer l'email
            email_service.send_alert_email(user_email, alert_data)
            logger.info(f"[ALERTS] Notification email envoyée pour alerte {alert.id}")

        except ImportError:
            logger.warning("[ALERTS] Service email non disponible, notification non envoyée")
        except Exception as e:
            logger.error(f"[ALERTS] Erreur envoi notification: {e}")

    def _mark_as_notified(self, triggered_id: int):
        """Marque une alerte déclenchée comme notifiée"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE triggered_economic_alerts
                SET notified = 1, notification_sent_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (triggered_id,))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"[ALERTS] Erreur marquage notification {triggered_id}: {e}")