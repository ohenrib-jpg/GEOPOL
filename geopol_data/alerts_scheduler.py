# Flask/geopol_data/alerts_scheduler.py

import time
import threading
from datetime import datetime
from .alerts import GeopolAlertsService
from .service import get_data_service
from .email_service import EmailService

def start_alerts_scheduler(alerts_service: GeopolAlertsService, data_service, interval_minutes=15):
    """
    Démarre un thread qui vérifie périodiquement les alertes
    """
    def scheduler():
        while True:
            try:
                print(f"⏰ [{datetime.now()}] Vérification des alertes...")
                check_all_alerts(alerts_service, data_service)
            except Exception as e:
                print(f"❌ Erreur vérification alertes: {e}")
            time.sleep(interval_minutes * 60)

    thread = threading.Thread(target=scheduler, daemon=True)
    thread.start()
    print(f"✅ Scheduler d'alertes démarré (intervalle: {interval_minutes} min)")

def check_all_alerts(alerts_service, data_service):
    """Vérifie toutes les alertes actives"""
    active_alerts = alerts_service.get_active_alerts()
    for alert in active_alerts:
        snapshot = data_service.get_country_snapshot(alert.country_code)
        if snapshot:
            value = getattr(snapshot, alert.indicator, None)
            if value is not None:
                triggered = False
                if alert.condition == '>' and value > alert.threshold:
                    triggered = True
                elif alert.condition == '<' and value < alert.threshold:
                    triggered = True

                if triggered:
                    alerts_service.log_triggered_alert(alert, value)
                    print(f"🚨 Alerte déclenchée : {alert.name} ({alert.country_code})")

            # Envoi email (exemple statique - à personnaliser)
            email_service = EmailService(
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            email="votre_email@gmail.com",
            password="votre_mot_de_passe"
        )

        email_service.send_alert_email(
            to_email="destinataire@gmail.com",
            alert_data={
                "alert_name": alert.name,
                "country_code": alert.country_code,
                "indicator": alert.indicator,
                "actual_value": value,
                "threshold": alert.threshold,
                "triggered_at": datetime.now().isoformat()
            }
        )
