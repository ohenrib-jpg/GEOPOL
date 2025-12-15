# Flask/geopol_data/alerts.py
"""
Système d'alertes géopolitiques basé sur les indicateurs World Bank
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
import json
import sqlite3
import os
import logging

if TYPE_CHECKING:
    from .models import CountrySnapshot

@dataclass
class GeopolAlert:
    """Configuration d'une alerte géopolitique"""
    id: Optional[int] = None
    name: str = ""
    description: str = ""
    country_code: str = ""           # Code ISO pays
    indicator: str = ""              # ex: 'inflation', 'military_spending'
    condition: str = ""              # '>', '<', 'increased_by'
    threshold: float = 0.0           # valeur seuil
    active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'country_code': self.country_code,
            'indicator': self.indicator,
            'condition': self.condition,
            'threshold': self.threshold,
            'active': self.active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class GeopolAlertsService:
    """Service de gestion des alertes géopolitiques"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_tables()

    def get_db_connection(self):
        """Connexion à la base de données"""
        return sqlite3.connect(self.db_path)

    def init_tables(self):
        """Initialise les tables d'alertes géopolitiques"""
        conn = self.get_db_connection()
        cur = conn.cursor()

        # Table des alertes
        cur.execute("""
            CREATE TABLE IF NOT EXISTS geopol_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                country_code TEXT NOT NULL,
                indicator TEXT NOT NULL,
                condition TEXT NOT NULL, -- '>', '<', 'increased_by'
                threshold REAL NOT NULL,
                active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Table des alertes déclenchées
        cur.execute("""
            CREATE TABLE IF NOT EXISTS triggered_geopol_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id INTEGER,
                country_code TEXT,
                indicator TEXT,
                actual_value REAL,
                threshold REAL,
                condition TEXT,
                triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(alert_id) REFERENCES geopol_alerts(id)
            )
        """)

        conn.commit()
        conn.close()

    def create_alert(self, alert: GeopolAlert) -> int:
        """Crée une nouvelle alerte"""
        conn = self.get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO geopol_alerts 
            (name, description, country_code, indicator, condition, threshold, active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            alert.name,
            alert.description,
            alert.country_code,
            alert.indicator,
            alert.condition,
            alert.threshold,
            alert.active
        ))
        alert_id = cur.lastrowid
        conn.commit()
        conn.close()
        return alert_id

    def get_all_alerts(self) -> List[GeopolAlert]:
        """Récupère toutes les alertes"""
        conn = self.get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM geopol_alerts ORDER BY created_at DESC")
        rows = cur.fetchall()
        conn.close()

        alerts = []
        for row in rows:
            alert = GeopolAlert(
                id=row[0],
                name=row[1],
                description=row[2],
                country_code=row[3],
                indicator=row[4],
                condition=row[5],
                threshold=row[6],
                active=bool(row[7]),
                created_at=datetime.fromisoformat(row[8]),
                updated_at=datetime.fromisoformat(row[9])
            )
            alerts.append(alert)
        return alerts

    def get_active_alerts(self) -> List[GeopolAlert]:
        """Récupère les alertes actives"""
        conn = self.get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM geopol_alerts WHERE active = 1 ORDER BY created_at DESC")
        rows = cur.fetchall()
        conn.close()

        alerts = []
        for row in rows:
            alert = GeopolAlert(
                id=row[0],
                name=row[1],
                description=row[2],
                country_code=row[3],
                indicator=row[4],
                condition=row[5],
                threshold=row[6],
                active=bool(row[7]),
                created_at=datetime.fromisoformat(row[8]),
                updated_at=datetime.fromisoformat(row[9])
            )
            alerts.append(alert)
        return alerts

    def update_alert(self, alert_id: int, alert: GeopolAlert) -> bool:
        """Met à jour une alerte"""
        conn = self.get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE geopol_alerts 
            SET name = ?, description = ?, country_code = ?, indicator = ?, 
                condition = ?, threshold = ?, active = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            alert.name,
            alert.description,
            alert.country_code,
            alert.indicator,
            alert.condition,
            alert.threshold,
            alert.active,
            alert_id
        ))
        success = cur.rowcount > 0
        conn.commit()
        conn.close()
        return success

    def delete_alert(self, alert_id: int) -> bool:
        """Supprime une alerte"""
        conn = self.get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM geopol_alerts WHERE id = ?", (alert_id,))
        success = cur.rowcount > 0
        conn.commit()
        conn.close()
        return success

    def toggle_alert(self, alert_id: int, active: bool) -> bool:
        """Active/désactive une alerte"""
        conn = self.get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE geopol_alerts SET active = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (active, alert_id))
        success = cur.rowcount > 0
        conn.commit()
        conn.close()
        return success

    def log_triggered_alert(self, alert: GeopolAlert, actual_value: float):
        """Enregistre une alerte déclenchée"""
        conn = self.get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO triggered_geopol_alerts 
            (alert_id, country_code, indicator, actual_value, threshold, condition)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            alert.id,
            alert.country_code,
            alert.indicator,
            actual_value,
            alert.threshold,
            alert.condition
        ))
        conn.commit()
        conn.close()

    def get_recently_triggered(self, hours: int = 24) -> List[dict]:
        """Récupère les alertes récemment déclenchées"""
        from datetime import datetime, timedelta
        since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()

        conn = self.get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT t.*, a.name as alert_name
            FROM triggered_geopol_alerts t
            JOIN geopol_alerts a ON t.alert_id = a.id
            WHERE t.triggered_at >= ?
            ORDER BY t.triggered_at DESC
        """, (since,))
        rows = cur.fetchall()
        conn.close()

        triggered = []
        for row in rows:
            triggered.append({
                'id': row[0],
                'alert_id': row[1],
                'alert_name': row[7],
                'country_code': row[2],
                'indicator': row[3],
                'actual_value': row[4],
                'threshold': row[5],
                'condition': row[6],
                'triggered_at': row[7]
            })
        return triggered
 

    def evaluate_alert(self, alert: GeopolAlert, snapshot: CountrySnapshot, article_entities: dict = None, sentiment: dict = None) -> bool:
        """
        Évalue une alerte en tenant compte :
        - Des indicateurs World Bank
        - Des entités SpaCy
        - Du sentiment des articles
        """
        # Défauts
        article_entities = article_entities or {}
        sentiment = sentiment or {}

    # 1. Vérifier seuil World Bank
        try:
            value = getattr(snapshot, alert.indicator, None)
        except Exception:
            value = None

        if value is None:
            return False

        if alert.condition == '>' and value > alert.threshold:
            return True
        elif alert.condition == '<' and value < alert.threshold:
            return True

    # 2. Vérifier entités (ex: si "Ukraine" est fréquente)
        locations = article_entities.get("locations", []) if isinstance(article_entities, dict) else []
        if "Ukraine" in locations:
            return True

    # 3. Vérifier sentiment (ex: si négatif >70%)
        if isinstance(sentiment, dict) and sentiment.get("negative_ratio",0) >0.7:
            return True

        return False

