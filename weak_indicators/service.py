# Flask/weak_indicators/service.py
"""Service principal des indicateurs faibles avec persistance"""

import logging
from typing import List
from datetime import datetime, timedelta
import threading
import time

from .models import DashboardData, TravelAdvisory, FinancialInstrument, SDRActivity
from .database import WeakIndicatorsDB
from .connectors.travel_connector import TravelConnector
from .connectors.financial_connector import FinancialConnector
from .utils import CacheManager
from .alerts import AlertManager

logger = logging.getLogger(__name__)

class BackgroundScheduler(threading.Thread):
    """Scheduler en arrière-plan pour les mises à jour"""
    
    def __init__(self, service, interval_minutes: int = 5):
        super().__init__(daemon=True)
        self.service = service
        self.interval = interval_minutes * 60  # Convertir en secondes
        self.running = True
    
    def run(self):
        """Exécute le scheduler en arrière-plan"""
        logger.info(f"Scheduler démarré (intervalle: {self.interval/60} min)")
        
        while self.running:
            try:
                # Mise à jour des données
                self.service.update_all_data()
                
                # Nettoyage des anciennes données
                self.service.db.cleanup_old_data()
                
                logger.debug(f"Mise à jour complétée à {datetime.utcnow()}")
                
            except Exception as e:
                logger.error(f"Erreur dans le scheduler: {e}")
            
            # Attendre jusqu'à la prochaine mise à jour
            for _ in range(self.interval):
                if not self.running:
                    break
                time.sleep(1)
    
    def stop(self):
        """Arrête le scheduler"""
        self.running = False

class WeakIndicatorsService:
    """Service principal des indicateurs faibles avec persistance"""
    
    def __init__(self, db_path: str = None, use_scraping: bool = True):
        # Initialiser la base de données
        self.db = WeakIndicatorsDB(db_path)
        
        # Initialiser les connecteurs
        self.travel_connector = TravelConnector(use_scraping=use_scraping)
        self.financial_connector = FinancialConnector()
        
        # Initialiser le cache
        self.cache = CacheManager()
        
        # Initialiser le scheduler
        self.scheduler = BackgroundScheduler(self, interval_minutes=5)
        self.scheduler.start()
        
        logger.info("WeakIndicatorsService initialisé avec persistance")
    
    def update_all_data(self):
        """Met à jour toutes les données (appelé par le scheduler)"""
        try:
            # Mettre à jour les avis de voyage
            self._update_travel_data()
            
            # Mettre à jour les données financières
            self._update_financial_data()
            
            # Mettre à jour l'activité SDR
            self._update_sdr_data()
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des données: {e}")
    
    def _update_travel_data(self):
        """Met à jour les avis de voyage"""
        try:
            advisories = self.travel_connector.fetch_all_advisories()
            
            for advisory in advisories:
                self.db.save_travel_advisory(advisory)
            
            # Mettre à jour le cache
            self.cache.set('travel_advisories', advisories, expire_minutes=60)
            
            logger.info(f"{len(advisories)} avis de voyage mis à jour")
            
        except Exception as e:
            logger.error(f"Erreur mise à jour voyage: {e}")
    
    def _update_financial_data(self):
        """Met à jour les données financières"""
        try:
            instruments = self.financial_connector.fetch_all_data()
            
            for instrument in instruments:
                self.db.save_financial_instrument(instrument)
            
            # Mettre à jour le cache
            self.cache.set('financial_data', instruments, expire_minutes=5)
            
            logger.info(f"{len(instruments)} instruments financiers mis à jour")
            
        except Exception as e:
            logger.error(f"Erreur mise à jour financière: {e}")
    
    def _update_sdr_data(self):
        """Met à jour l'activité SDR (simulation pour l'instant)"""
        try:
            activities = self._get_sdr_activities_real()
            
            for activity in activities:
                self.db.save_sdr_activity(activity)
            
            logger.info(f"{len(activities)} activités SDR mises à jour")
            
        except Exception as e:
            logger.error(f"Erreur mise à jour SDR: {e}")
    
    async def get_dashboard_data(self) -> DashboardData:
        """Récupère toutes les données pour le dashboard"""
        try:
            # Récupérer depuis la base de données
            travel_data = self._get_travel_advisories_db()
            financial_data = self._get_financial_data_db()
            sdr_data = self._get_sdr_activities_db()
            
            return DashboardData(
                travel_advisories=travel_data,
                financial_data=financial_data,
                sdr_activities=sdr_data,
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Erreur service dashboard: {e}")
            # Retourner des données de fallback
            return self._get_fallback_data()
    
    def _get_travel_advisories_db(self) -> List[TravelAdvisory]:
        """Récupère les avis de voyage depuis la base de données"""
        cached = self.cache.get('travel_advisories')
        if cached and not self.cache.is_expired('travel_advisories'):
            return cached
        
        try:
            db_rows = self.db.get_travel_advisories(max_age_hours=24, limit=50)
            
            advisories = []
            for row in db_rows:
                advisory = TravelAdvisory(
                    country_code=row['country_code'],
                    country_name=row['country_name'],
                    risk_level=row['risk_level'],
                    source=row['source'],
                    summary=row['summary'],
                    last_updated=datetime.fromisoformat(row['last_updated']),
                    raw_data=eval(row['raw_data']) if row['raw_data'] else None
                )
                advisories.append(advisory)
            
            self.cache.set('travel_advisories', advisories, expire_minutes=60)
            return advisories
            
        except Exception as e:
            logger.error(f"Erreur lecture DB voyage: {e}")
            return self._get_fallback_travel()
    
    def _get_financial_data_db(self) -> List[FinancialInstrument]:
        """Récupère les données financières depuis la base de données"""
        cached = self.cache.get('financial_data')
        if cached and not self.cache.is_expired('financial_data'):
            return cached
        
        try:
            db_rows = self.db.get_financial_data(max_age_minutes=10, limit=30)
            
            instruments = []
            for row in db_rows:
                instrument = FinancialInstrument(
                    symbol=row['symbol'],
                    name=row['name'],
                    current_price=row['current_price'],
                    change_percent=row['change_percent'],
                    volume=row['volume'],
                    timestamp=datetime.fromisoformat(row['timestamp']),
                    source=row['source'],
                    category=row['category']
                )
                instruments.append(instrument)
            
            self.cache.set('financial_data', instruments, expire_minutes=5)
            return instruments
            
        except Exception as e:
            logger.error(f"Erreur lecture DB financière: {e}")
            return self._get_fallback_financial()
    
    def _get_sdr_activities_db(self) -> List[SDRActivity]:
        """Récupère l'activité SDR depuis la base de données"""
        try:
            db_rows = self.db.get_sdr_activities(max_age_hours=1, limit=20)
            
            if db_rows:
                activities = []
                for row in db_rows:
                    activity = SDRActivity(
                        frequency_khz=row['frequency_khz'],
                        name=row['name'],
                        activity_count=row['activity_count'],
                        last_seen=datetime.fromisoformat(row['last_seen']),
                        is_anomaly=bool(row['is_anomaly']),
                        source=row['source']
                    )
                    activities.append(activity)
                return activities
            else:
                # Si pas de données en base, générer des données simulées
                return self._get_sdr_activities_simulated()
                
        except Exception as e:
            logger.error(f"Erreur lecture DB SDR: {e}")
            return self._get_sdr_activities_simulated()
    
    def _get_sdr_activities_real(self) -> List[SDRActivity]:
        """Version réelle à implémenter avec les SDR"""
        # Pour l'instant, retourne des données simulées
        return self._get_sdr_activities_simulated()
    
    def _get_sdr_activities_simulated(self) -> List[SDRActivity]:
        """Simulation d'activité SDR"""
        import random
        from datetime import timedelta
        
        activities = []
        frequencies = [
            {'khz': 2182, 'name': 'Maritime Distress'},
            {'khz': 4625, 'name': 'UVB-76'},
            {'khz': 5732, 'name': 'Diplomatic HF'},
            {'khz': 14313, 'name': 'Maritime Service'},
            {'khz': 8992, 'name': 'USB Aero'},
            {'khz': 11175, 'name': 'USAF High Freq'},
            {'khz': 15016, 'name': 'Russian Navy'},
            {'khz': 18500, 'name': 'Air Rescue'}
        ]
        
        for freq in frequencies:
            activity = SDRActivity(
                frequency_khz=freq['khz'],
                name=freq['name'],
                activity_count=random.randint(0, 100),
                last_seen=datetime.utcnow() - timedelta(minutes=random.randint(0, 60)),
                is_anomaly=random.random() > 0.8,
                source='kiwisdr_simulation'
            )
            activities.append(activity)
        
        return activities
    
    def get_scraping_stats(self):
        """Récupère les statistiques de scraping"""
        return self.db.get_scraping_stats()
    
    def _get_fallback_travel(self) -> List[TravelAdvisory]:
        """Données de voyage de fallback"""
        return [
            TravelAdvisory(
                country_code='FR',
                country_name='France',
                risk_level=1,
                source='fallback',
                summary='Normal precautions',
                last_updated=datetime.utcnow()
            )
        ]
    
    def _get_fallback_financial(self) -> List[FinancialInstrument]:
        """Données financières de fallback"""
        return [
            FinancialInstrument(
                symbol='^FCHI',
                name='CAC 40',
                current_price=7345.67,
                change_percent=1.2,
                volume=123456789,
                timestamp=datetime.utcnow(),
                source='fallback',
                category='index'
            )
        ]
    
    def _get_fallback_data(self) -> DashboardData:
        """Données de fallback complètes"""
        return DashboardData(
            travel_advisories=self._get_fallback_travel(),
            financial_data=self._get_fallback_financial(),
            sdr_activities=self._get_sdr_activities(),
            timestamp=datetime.utcnow()
        )

    def get_travel_for_export(self):
        """Récupère les données pour export (sans cache)"""
        try:
            db_rows = self.db.get_travel_advisories(max_age_hours=240, limit=1000)  # Plus de données
            advisories = []
            for row in db_rows:
                advisory = TravelAdvisory(
                    country_code=row['country_code'],
                    country_name=row['country_name'],
                    risk_level=row['risk_level'],
                    source=row['source'],
                    summary=row['summary'],
                    last_updated=datetime.fromisoformat(row['last_updated']),
                    raw_data=eval(row['raw_data']) if row['raw_data'] else None
                )
                advisories.append(advisory)
            return advisories
        except Exception as e:
            logger.error(f"Erreur export voyage: {e}")
            return []

    def get_financial_for_export(self):
        """Récupère les données financières pour export"""
        try:
            db_rows = self.db.get_financial_data(max_age_minutes=1440, limit=1000)  # 24h
            instruments = []
            for row in db_rows:
                instrument = FinancialInstrument(
                    symbol=row['symbol'],
                    name=row['name'],
                    current_price=row['current_price'],
                    change_percent=row['change_percent'],
                    volume=row['volume'],
                    timestamp=datetime.fromisoformat(row['timestamp']),
                    source=row['source'],
                    category=row['category']
                )
                instruments.append(instrument)
            return instruments
        except Exception as e:
            logger.error(f"Erreur export financier: {e}")
            return []

    def get_sdr_for_export(self):
        """Récupère les activités SDR pour export"""
        try:
            db_rows = self.db.get_sdr_activities(max_age_hours=720, limit=1000)  # 30 jours
            activities = []
            for row in db_rows:
                activity = SDRActivity(
                    frequency_khz=row['frequency_khz'],
                    name=row['name'],
                    activity_count=row['activity_count'],
                    last_seen=datetime.fromisoformat(row['last_seen']),
                    is_anomaly=bool(row['is_anomaly']),
                    source=row['source']
                )
                activities.append(activity)
            return activities
        except Exception as e:
            logger.error(f"Erreur export SDR: {e}")
            return []

          # Ajouter le gestionnaire d'alertes
        self.alert_manager = AlertManager(db_path)
        
        # Historique pour détection des changements
        self.previous_data = {
            'financial': {},  # symbol -> data
            'travel': {}      # country_code -> data
        }
    
    async def get_dashboard_data(self) -> DashboardData:
        """Récupère toutes les données pour le dashboard"""
        try:
            # Récupérer les données
            travel_data = self._get_travel_advisories_db()
            financial_data = self._get_financial_data_db()
            sdr_data = self._get_sdr_activities_db()
            
            # Vérifier les alertes
            alerts = self._check_for_alerts(travel_data, financial_data)
            
            # Mettre à jour l'historique
            self._update_previous_data(travel_data, financial_data)
            
            return DashboardData(
                travel_advisories=travel_data,
                financial_data=financial_data,
                sdr_activities=sdr_data,
                alerts=alerts,  # Nouveau champ
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Erreur service dashboard: {e}")
            return self._get_fallback_data()
    
    def _check_for_alerts(self, travel_data, financial_data):
        """Vérifie les alertes sur nouvelles données"""
        try:
            alerts = []
            
            # Vérifier données financières
            fin_alerts = self.alert_manager.check_financial_data(
                [inst.__dict__ for inst in financial_data],
                self.previous_data['financial']
            )
            alerts.extend(fin_alerts)
            
            # Vérifier données voyage
            travel_alerts = self.alert_manager.check_travel_data(
                [adv.__dict__ for adv in travel_data],
                self.previous_data['travel']
            )
            alerts.extend(travel_alerts)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Erreur vérification alertes: {e}")
            return []
    
    def _update_previous_data(self, travel_data, financial_data):
        """Met à jour l'historique des données"""
        # Mise à jour données financières
        for inst in financial_data:
            self.previous_data['financial'][inst.symbol] = inst.__dict__
        
        # Mise à jour données voyage
        for adv in travel_data:
            self.previous_data['travel'][adv.country_code] = adv.__dict__
    
    #    Méthodes pour l'API
    def get_active_alerts(self):
        """Retourne les alertes actives"""
        return self.alert_manager.get_active_alerts()
    
    def acknowledge_alert(self, alert_id):
        """Marque une alerte comme lue"""
        return self.alert_manager.acknowledge_alert(alert_id)
    
    def get_alert_stats(self):
        """Retourne les statistiques d'alertes"""
        return self.alert_manager.get_stats()
    
    def get_alert_rules(self):
        """Retourne les règles d'alertes"""
        return self.alert_manager.get_rules()

