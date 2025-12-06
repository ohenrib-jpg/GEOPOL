# Flask/travel_advisories_manager.py - VERSION AMÉLIORÉE
import logging
import json
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class TravelAdvisoriesManager:
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self._initialized = False
        
        if db_manager:
            try:
                self.init_tables()
                self._initialized = True
                logger.info("✅ TravelAdvisoriesManager initialisé avec db_manager")
            except Exception as e:
                logger.error(f"❌ Erreur initialisation tables: {e}")
                self._initialized = False
        else:
            logger.warning("⚠️ TravelAdvisoriesManager: db_manager est None - utilisation mode mock")
            self._initialized = False
    
    def init_tables(self):
        """Initialise les tables pour les avis aux voyageurs"""
        if not self.db_manager:
            return
            
        try:
            conn = self.db_manager.get_connection()
            cur = conn.cursor()
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS travel_advisories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    country_code TEXT NOT NULL,
                    country_name TEXT,
                    risk_level INTEGER DEFAULT 1,
                    source TEXT NOT NULL,
                    summary TEXT,
                    details TEXT,
                    last_updated DATETIME,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(country_code, source)
                )
            """)
            
            cur.execute("""
                CREATE TABLE IF NOT EXISTS travel_advisory_changes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    country_code TEXT NOT NULL,
                    previous_risk INTEGER,
                    new_risk INTEGER,
                    change_type TEXT,
                    source TEXT,
                    changed_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            conn.close()
            logger.info("✅ Tables travel_advisories initialisées")
        except Exception as e:
            logger.error(f"❌ Erreur initialisation tables: {e}")
            raise
    
    def is_initialized(self):
        """Vérifie si le manager est correctement initialisé"""
        return self._initialized and self.db_manager is not None
    
def scan_all_sources(self, force_refresh=False):
    """Scanne toutes les sources avec données réelles"""
    try:
        if not self.is_initialized():
            logger.info("📡 Utilisation données mockées (db non disponible)")
            return self._get_mock_scan_results()
        
        # Utiliser les vraies données
        from .real_travel_advisories import RealTravelAdvisories
        real_manager = RealTravelAdvisories(self.db_manager)
        results = real_manager.update_all_real_advisories()
        
        if "error" in results:
            logger.error(f"Erreur scan réel: {results['error']}")
            return self._get_mock_scan_results()
        
        return {
            "us_state_department": {
                "success": True, 
                "advisories_processed": results.get("us_state_department", 0)
            },
            "uk_foreign_office": {
                "success": True, 
                "advisories_processed": results.get("uk_foreign_office", 0)
            },
            "canada_travel": {
                "success": True, 
                "advisories_processed": results.get("canada_travel", 0)
            },
            "note": "Données réelles mises à jour"
        }
        
    except Exception as e:
        logger.error(f"Erreur scan_all_sources: {e}")
        return {"error": str(e)}
    
    def _get_mock_scan_results(self):
        """Résultats de scan mockés"""
        return {
            "us_state_department": {
                "success": True, 
                "advisories_processed": 3,
                "note": "Données de démonstration"
            },
            "uk_foreign_office": {
                "success": True, 
                "advisories_processed": 2,
                "note": "Données mockées"
            },
            "canada_travel": {
                "success": True, 
                "advisories_processed": 2, 
                "note": "Données mockées"
            }
        }
    
    def save_advisory(self, advisory):
        """Sauvegarde un avis dans la base"""
        try:
            if not self.is_initialized():
                return False
                
            conn = self.db_manager.get_connection()
            cur = conn.cursor()
            
            # Vérifier l'existence
            cur.execute("""
                SELECT risk_level FROM travel_advisories 
                WHERE country_code = ? AND source = ?
            """, (advisory['country_code'], advisory['source']))
            
            existing = cur.fetchone()
            
            if existing:
                # Mettre à jour
                cur.execute("""
                    UPDATE travel_advisories 
                    SET risk_level = ?, summary = ?, last_updated = ?, country_name = ?
                    WHERE country_code = ? AND source = ?
                """, (
                    advisory['risk_level'],
                    advisory.get('summary'),
                    advisory.get('last_updated', datetime.utcnow().isoformat()),
                    advisory.get('country_name'),
                    advisory['country_code'],
                    advisory['source']
                ))
            else:
                # Insérer
                cur.execute("""
                    INSERT INTO travel_advisories 
                    (country_code, country_name, risk_level, source, summary, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    advisory['country_code'],
                    advisory.get('country_name'),
                    advisory['risk_level'],
                    advisory['source'],
                    advisory.get('summary'),
                    advisory.get('last_updated', datetime.utcnow().isoformat())
                ))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde avis: {e}")
            return False
    
    def get_country_risk_levels(self):
        """Retourne les niveaux de risque consolidés"""
        try:
            if not self.is_initialized():
                logger.info("🌍 Retour données mockées pour get_country_risk_levels")
                return self._get_mock_countries()
                
            conn = self.db_manager.get_connection()
            cur = conn.cursor()
            
            cur.execute("""
                SELECT 
                    country_code,
                    country_name,
                    MAX(risk_level) as consolidated_risk,
                    GROUP_CONCAT(source) as sources,
                    MAX(last_updated) as last_updated
                FROM travel_advisories 
                GROUP BY country_code, country_name
                ORDER BY consolidated_risk DESC, country_name
            """)
            
            countries = []
            for row in cur.fetchall():
                countries.append({
                    "country_code": row[0],
                    "country_name": row[1],
                    "risk_level": row[2] or 1,
                    "sources": row[3].split(',') if row[3] else [],
                    "last_updated": row[4]
                })
            
            conn.close()
            
            if not countries:
                return self._get_mock_countries()
                
            return countries
            
        except Exception as e:
            logger.error(f"Erreur récupération niveaux risque: {e}")
            return self._get_mock_countries()
    
    def _get_mock_countries(self):
        """Données mockées pour les tests"""
        return [
            {
                "country_code": "UA",
                "country_name": "Ukraine", 
                "risk_level": 4,
                "sources": ["us_state_department", "uk_foreign_office"],
                "last_updated": datetime.utcnow().isoformat()
            },
            {
                "country_code": "FR",
                "country_name": "France",
                "risk_level": 1, 
                "sources": ["us_state_department"],
                "last_updated": datetime.utcnow().isoformat()
            },
            {
                "country_code": "CN", 
                "country_name": "China",
                "risk_level": 2,
                "sources": ["us_state_department", "canada_travel"],
                "last_updated": datetime.utcnow().isoformat()
            },
            {
                "country_code": "RU",
                "country_name": "Russia", 
                "risk_level": 3,
                "sources": ["us_state_department"],
                "last_updated": datetime.utcnow().isoformat()
            }
        ]
    
    def get_country_advisory(self, country_code):
        """Détails pour un pays spécifique"""
        try:
            if not self.is_initialized():
                return self._get_mock_country_advisory(country_code)
                
            conn = self.db_manager.get_connection()
            cur = conn.cursor()
            
            cur.execute("""
                SELECT country_code, country_name, risk_level, source, summary, last_updated
                FROM travel_advisories 
                WHERE country_code = ?
                ORDER BY last_updated DESC
            """, (country_code,))
            
            sources = []
            country_name = None
            max_risk = 1
            
            for row in cur.fetchall():
                if not country_name and row[1]:
                    country_name = row[1]
                
                sources.append({
                    "source": row[3],
                    "risk_level": row[2],
                    "summary": row[4],
                    "last_updated": row[5]
                })
                
                if row[2] > max_risk:
                    max_risk = row[2]
            
            conn.close()
            
            if not sources:
                return self._get_mock_country_advisory(country_code)
            
            return {
                "country_code": country_code,
                "country_name": country_name,
                "risk_level": max_risk,
                "sources": sources,
                "last_updated": max([s['last_updated'] for s in sources if s['last_updated']], default=datetime.utcnow().isoformat()),
                "recommendations": self._generate_recommendations(max_risk)
            }
            
        except Exception as e:
            logger.error(f"Erreur récupération avis pays {country_code}: {e}")
            return self._get_mock_country_advisory(country_code)
    
    def _get_mock_country_advisory(self, country_code):
        """Mock data pour un pays"""
        mock_data = {
            "UA": {
                "country_code": "UA",
                "country_name": "Ukraine",
                "risk_level": 4,
                "sources": [
                    {
                        "source": "us_state_department",
                        "risk_level": 4,
                        "summary": "Do not travel due to armed conflict and civil unrest.",
                        "last_updated": datetime.utcnow().isoformat()
                    },
                    {
                        "source": "uk_foreign_office", 
                        "risk_level": 4,
                        "summary": "FCDO advises against all travel to Ukraine.",
                        "last_updated": datetime.utcnow().isoformat()
                    }
                ],
                "last_updated": datetime.utcnow().isoformat(),
                "recommendations": "Éviter tout déplacement. Si sur place, envisagez une évacuation immédiate."
            },
            "FR": {
                "country_code": "FR", 
                "country_name": "France",
                "risk_level": 1,
                "sources": [
                    {
                        "source": "us_state_department",
                        "risk_level": 1,
                        "summary": "Exercise normal precautions in France.",
                        "last_updated": datetime.utcnow().isoformat()
                    }
                ],
                "last_updated": datetime.utcnow().isoformat(),
                "recommendations": "Précautions normales de voyage recommandées."
            }
        }
        return mock_data.get(country_code, {
            "country_code": country_code,
            "risk_level": 1,
            "sources": [],
            "recommendations": "Consultez les avis officiels avant tout déplacement."
        })
    
    def get_recent_changes(self, hours=24):
        """Changements récents"""
        try:
            if not self.is_initialized():
                return []
                
            since_time = datetime.utcnow() - timedelta(hours=hours)
            
            conn = self.db_manager.get_connection()
            cur = conn.cursor()
            
            cur.execute("""
                SELECT country_code, previous_risk, new_risk, change_type, source, changed_at
                FROM travel_advisory_changes 
                WHERE changed_at > ?
                ORDER BY changed_at DESC
            """, (since_time.isoformat(),))
            
            changes = []
            for row in cur.fetchall():
                changes.append({
                    "country_code": row[0],
                    "previous_risk": row[1],
                    "new_risk": row[2],
                    "change_type": row[3],
                    "source": row[4],
                    "changed_at": row[5]
                })
            
            conn.close()
            return changes
            
        except Exception as e:
            logger.error(f"Erreur récupération changements: {e}")
            return []
    
    def generate_alerts(self):
        """Génère des alertes"""
        try:
            # Pour l'instant, retourner des alertes mockées
            return [
                {
                    "level": "critical",
                    "country_code": "UA",
                    "country_name": "Ukraine", 
                    "message": "Nouveau niveau de risque: Éviter tout déplacement",
                    "previous_level": 3,
                    "new_level": 4,
                    "source": "us_state_department",
                    "timestamp": datetime.utcnow().isoformat()
                }
            ]
        except Exception as e:
            logger.error(f"Erreur génération alertes: {e}")
            return []
    
    def _generate_recommendations(self, risk_level):
        """Recommandations basées sur le niveau de risque"""
        recommendations = {
            1: "Précautions normales de voyage recommandées.",
            2: "Soyez vigilant et suivez l'actualité locale.",
            3: "Évitez les déplacements non essentiels. Consultez régulièrement les avis.",
            4: "Évitez tout déplacement. Si sur place, envisagez une évacuation."
        }
        return recommendations.get(risk_level, "Consultez les avis officiels avant tout déplacement.")