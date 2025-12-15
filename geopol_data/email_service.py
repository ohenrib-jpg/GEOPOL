# Flask/geopol_data/email_service.py

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self, smtp_server: str, smtp_port: int, email: str, password: str):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email = email
        self.password = password

    def send_alert_email(self, to_email: str, alert_data: Dict[str, Any]):
        """Envoie une alerte par email"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email
            msg['To'] = to_email
            msg['Subject'] = f"🚨 Alerte géopolitique : {alert_data['alert_name']}"

            body = f"""
            Bonjour,

            Une alerte a été déclenchée :

            🔔 Alerte : {alert_data['alert_name']}
            🌍 Pays : {alert_data['country_code']}
            📊 Indicateur : {alert_data['indicator']}
            📈 Valeur actuelle : {alert_data['actual_value']:.2f}
            📉 Seuil : {alert_data['threshold']}

            Date : {alert_data['triggered_at']}

            ---
            GEOPOL Analytics
            """

            msg.attach(MIMEText(body, 'plain'))

            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email, self.password)
            text = msg.as_string()
            server.sendmail(self.email, to_email, text)
            server.quit()

            logger.info(f"✅ Email envoyé à {to_email}")
        except Exception as e:
            logger.error(f"❌ Erreur envoi email: {e}")
