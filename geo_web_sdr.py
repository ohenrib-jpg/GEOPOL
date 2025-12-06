# Flask/geo_web_sdr.py
"""
⚠️ ANALYSE SPECTRALE PASSIVE - PAS D'ÉCOUTE DE CONTENU ⚠️

Ce module effectue une surveillance PASSIVE des bandes de fréquences :
- Analyse du spectre FFT (transformée de Fourier)
- Comptage des PICS d'émission (présence de signaux)
- AUCUNE démodulation ou écoute de contenu audio
- AUCUNE interception de communications

Principe géopolitique :
- Augmentation soudaine de pics = activité inhabituelle = indicateur faible
- Disparition de pics habituels = silence radio = indicateur faible
- Analyse des tendances uniquement, pas du contenu
"""

import logging
import asyncio
import aiohttp
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import requests
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)


class GeoWebSDR:
    """
    Surveillance PASSIVE du spectre radio géopolitique
    
    ⚠️ IMPORTANT : 
    - Analyse spectrale uniquement (FFT)
    - Comptage de pics d'émission
    - Aucune démodulation ni écoute
    - Conformité légale complète
    """
    
    # WebSDR publics pour analyse spectrale
    WEBSDR_SERVERS = [
        "http://websdr.org",
        "http://kiwisdr.com",
        "http://sdr.hu"
    ]
    
    # Fréquences à surveiller (Hz)
    # ⚠️ Surveillance de l'ACTIVITÉ spectrale uniquement, pas du contenu
    GEOPOLITICAL_FREQUENCIES = {
        'maritime_emergency': {
            'freq': 2182000,  # 2182 kHz
            'name': 'Détresse Maritime',
            'description': 'Comptage pics d\'émission MF maritime'
        },
        'aviation_emergency': {
            'freq': 121500000,  # 121.5 MHz
            'name': 'Détresse Aviation',
            'description': 'Surveillance activité urgence aviation'
        },
        'military_rus': {
            'freq': 4625000,  # UVB-76
            'name': 'UVB-76 Buzzer',
            'description': 'Analyse activité station militaire russe'
        },
        'military_nato': {
            'freq': 6998000,
            'name': 'Bande OTAN',
            'description': 'Comptage activité bande militaire'
        },
        'diplomatic': {
            'freq': 5732000,
            'name': 'Diplomatique HF',
            'description': 'Surveillance activité diplomatique'
        },
        'us_military': {
            'freq': 11175000,
            'name': 'HFGCS US',
            'description': 'Activité communications militaires US'
        }
    }
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.active_websdr = []
        self.last_scan = None
        self._init_websdr_database()
        
        logger.info("⚠️ Mode PASSIF : Analyse spectrale uniquement, aucune écoute")
    
    def _init_websdr_database(self):
        """Initialise les tables pour l'analyse spectrale"""
        try:
            conn = self.db_manager.get_connection()
            cur = conn.cursor()
            
            # Table des serveurs WebSDR disponibles
            cur.execute("""
                CREATE TABLE IF NOT EXISTS websdr_servers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE NOT NULL,
                    name TEXT,
                    location TEXT,
                    status TEXT DEFAULT 'unknown',
                    last_check TIMESTAMP,
                    frequency_range TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table du monitoring spectral (comptage pics uniquement)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS frequency_monitoring (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    frequency_hz INTEGER NOT NULL,
                    category TEXT NOT NULL,
                    emission_peak_count INTEGER DEFAULT 0,
                    signal_strength_avg REAL,
                    websdr_server TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    analysis_type TEXT DEFAULT 'passive_spectral',
                    notes TEXT
                )
            """)
            
            # Table des alertes d'activité anormale
            cur.execute("""
                CREATE TABLE IF NOT EXISTS spectral_activity_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    frequency_hz INTEGER NOT NULL,
                    alert_type TEXT NOT NULL,
                    peak_count INTEGER,
                    deviation_from_baseline REAL,
                    description TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Index pour performance
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_freq_monitoring_time 
                ON frequency_monitoring(frequency_hz, timestamp)
            """)
            
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_alerts_time 
                ON spectral_activity_alerts(timestamp DESC)
            """)
            
            conn.commit()
            conn.close()
            logger.info("✅ Tables WebSDR initialisées")
            
        except Exception as e:
            logger.error(f"❌ Erreur initialisation BDD WebSDR: {e}")
            raise
    
    async def scan_active_websdr(self) -> List[Dict]:
        """
        Scan des WebSDR publics accessibles
        Retourne la liste des serveurs disponibles pour analyse spectrale
        """
        active_servers = []
        
        async with aiohttp.ClientSession() as session:
            for server in self.WEBSDR_SERVERS:
                try:
                    async with session.get(server, timeout=10) as response:
                        if response.status == 200:
                            server_info = {
                                'url': server,
                                'status': 'online',
                                'last_check': datetime.utcnow().isoformat(),
                                'name': self._extract_server_name(server),
                                'analysis_capability': 'spectral_fft'
                            }
                            active_servers.append(server_info)
                            logger.info(f"✅ WebSDR accessible: {server}")
                        else:
                            logger.warning(f"⚠️ WebSDR inaccessible: {server}")
                            
                except Exception as e:
                    logger.warning(f"❌ Erreur connexion {server}: {e}")
        
        self._save_websdr_status(active_servers)
        self.active_websdr = active_servers
        
        return active_servers
    
    def _extract_server_name(self, url: str) -> str:
        """Extrait le nom du serveur"""
        try:
            response = requests.get(url, timeout=5)
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.find('title')
            return title.text.strip()[:50] if title else url
        except:
            from urllib.parse import urlparse
            return urlparse(url).netloc
    
    async def analyze_frequency_spectrum(self, frequency_hz: int, category: str) -> Dict:
        """
        ⚠️ ANALYSE SPECTRALE PASSIVE ⚠️
        
        Analyse le spectre FFT pour :
        1. Compter les PICS d'émission présents
        2. Mesurer l'intensité moyenne du signal
        3. Comparer à la baseline historique
        
        AUCUNE démodulation ni écoute de contenu
        
        Args:
            frequency_hz: Fréquence à analyser
            category: Catégorie géopolitique
            
        Returns:
            Dict avec comptage de pics et métriques spectrales
        """
        if not self.active_websdr:
            await self.scan_active_websdr()
        
        if not self.active_websdr:
            return {
                'frequency_hz': frequency_hz,
                'category': category,
                'peak_count': 0,
                'status': 'no_websdr_available',
                'error': 'Aucun WebSDR disponible',
                'timestamp': datetime.utcnow().isoformat()
            }
        
        results = []
        
        for server in self.active_websdr:
            try:
                # Obtenir le spectre FFT du WebSDR
                spectrum_data = await self._get_websdr_fft_spectrum(
                    server['url'], 
                    frequency_hz
                )
                
                if spectrum_data:
                    # ⚠️ Analyser UNIQUEMENT le spectre pour compter les pics
                    peak_count, signal_strength = self._count_emission_peaks(
                        spectrum_data
                    )
                    
                    result = {
                        'frequency_hz': frequency_hz,
                        'frequency_mhz': frequency_hz / 1_000_000,
                        'category': category,
                        'peak_count': peak_count,
                        'signal_strength_avg': signal_strength,
                        'websdr_server': server['url'],
                        'server_name': server['name'],
                        'timestamp': datetime.utcnow().isoformat(),
                        'analysis_type': 'passive_spectral_fft',
                        'status': 'activity_detected' if peak_count > 0 else 'silent'
                    }
                    
                    results.append(result)
                    
                    # Sauvegarder l'analyse
                    self._save_spectral_analysis(result)
                    
                    # Vérifier si activité anormale
                    await self._check_abnormal_activity(
                        frequency_hz, 
                        peak_count, 
                        signal_strength
                    )
                    
            except Exception as e:
                logger.error(f"❌ Erreur analyse spectrale {frequency_hz}: {e}")
                continue
        
        # Retourner le meilleur résultat
        if results:
            best_result = max(results, key=lambda x: x['signal_strength_avg'])
            return best_result
        
        return {
            'frequency_hz': frequency_hz,
            'category': category,
            'peak_count': 0,
            'signal_strength_avg': 0,
            'status': 'no_data',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def _get_websdr_fft_spectrum(self, server_url: str, frequency_hz: int) -> bytes:
        """
        Récupère les données FFT d'un WebSDR
        
        Les WebSDR publics exposent souvent un endpoint FFT
        qui retourne le spectre analysé (pas l'audio)
        """
        try:
            async with aiohttp.ClientSession() as session:
                
                # Endpoints FFT possibles selon le type de WebSDR
                endpoints = [
                    f"{server_url}/~~fft?f={frequency_hz}",
                    f"{server_url}/fft?freq={frequency_hz}",
                    f"{server_url}/spectrum?f={frequency_hz}",
                ]
                
                for endpoint in endpoints:
                    try:
                        async with session.get(endpoint, timeout=10) as response:
                            if response.status == 200:
                                data = await response.read()
                                if len(data) > 100:
                                    return data
                    except:
                        continue
                
                return None
                
        except Exception as e:
            logger.error(f"❌ Erreur récupération FFT {server_url}: {e}")
            return None
    
    def _count_emission_peaks(self, spectrum_data: bytes) -> Tuple[int, float]:
        """
        ⚠️ COMPTAGE DE PICS UNIQUEMENT ⚠️
        
        Analyse les données FFT pour compter les pics d'émission.
        AUCUNE démodulation ni accès au contenu.
        
        Principe :
        1. Convertir les données FFT en array numpy
        2. Normaliser l'amplitude
        3. Détecter les pics au-dessus du seuil
        4. Compter les pics distincts (séparés par un écart minimum)
        
        Returns:
            (nombre_de_pics, intensité_moyenne)
        """
        try:
            import struct
            
            # Convertir les données binaires FFT en array
            try:
                fft_array = np.frombuffer(spectrum_data, dtype=np.int16)
            except:
                fft_array = np.frombuffer(spectrum_data, dtype=np.uint8)
            
            # Normaliser entre 0 et 1
            fft_normalized = fft_array.astype(np.float32) / (np.max(np.abs(fft_array)) + 1e-10)
            
            # Seuil de détection de pic (ajustable)
            PEAK_THRESHOLD = 0.15  # 15% de l'amplitude max
            
            # Trouver tous les points au-dessus du seuil
            above_threshold = np.where(fft_normalized > PEAK_THRESHOLD)[0]
            
            # Compter les pics DISTINCTS (séparés d'au moins 5 bins FFT)
            peak_count = 0
            if len(above_threshold) > 0:
                peak_count = 1
                for i in range(1, len(above_threshold)):
                    # Si le pic est séparé du précédent par au moins 5 bins
                    if above_threshold[i] - above_threshold[i-1] > 5:
                        peak_count += 1
            
            # Calculer l'intensité moyenne des pics détectés
            signal_strength = float(np.mean(fft_normalized[above_threshold])) if len(above_threshold) > 0 else 0.0
            
            logger.debug(f"📊 Analyse spectrale: {peak_count} pics détectés, intensité moy: {signal_strength:.3f}")
            
            return peak_count, signal_strength
            
        except Exception as e:
            logger.error(f"❌ Erreur comptage pics: {e}")
            return 0, 0.0
    
    async def monitor_all_geopolitical_frequencies(self) -> Dict:
        """
        Surveille toutes les fréquences géopolitiques
        
        Retourne un rapport d'activité spectrale pour chaque fréquence
        """
        # Scanner les WebSDR disponibles
        await self.scan_active_websdr()
        
        if not self.active_websdr:
            return {
                'error': 'AUCUN WebSDR disponible',
                'timestamp': datetime.utcnow().isoformat(),
                'recommendation': 'Vérifiez la connectivité réseau'
            }
        
        results = {}
        
        # Analyser chaque fréquence
        for category, freq_info in self.GEOPOLITICAL_FREQUENCIES.items():
            try:
                analysis = await self.analyze_frequency_spectrum(
                    freq_info['freq'], 
                    category
                )
                
                # Enrichir avec les infos de la fréquence
                analysis['name'] = freq_info['name']
                analysis['description'] = freq_info['description']
                
                results[category] = analysis
                
                # Pause pour ne pas surcharger les serveurs
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Erreur surveillance {category}: {e}")
                results[category] = {
                    'frequency_hz': freq_info['freq'],
                    'category': category,
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                }
        
        return {
            'websdr_available': len(self.active_websdr),
            'frequencies_monitored': len(results),
            'analysis_type': 'passive_spectral_only',
            'results': results,
            'timestamp': datetime.utcnow().isoformat(),
            'active_servers': [s['url'] for s in self.active_websdr],
            'legal_compliance': 'Analyse spectrale passive - Aucune interception'
        }
    
    async def _check_abnormal_activity(self, frequency_hz: int, peak_count: int, signal_strength: float):
        """
        Vérifie si l'activité spectrale est anormale
        
        Compare à la baseline historique :
        - Augmentation soudaine = alerte
        - Disparition de pics habituels = alerte
        """
        try:
            # Récupérer la baseline des 7 derniers jours
            conn = self.db_manager.get_connection()
            cur = conn.cursor()
            
            week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
            
            cur.execute("""
                SELECT AVG(emission_peak_count), STDEV(emission_peak_count)
                FROM frequency_monitoring
                WHERE frequency_hz = ?
                AND timestamp > ?
            """, (frequency_hz, week_ago))
            
            result = cur.fetchone()
            avg_baseline = result[0] if result[0] else 5.0
            std_baseline = result[1] if result[1] else 2.0
            
            conn.close()
            
            # Calculer l'écart par rapport à la baseline
            deviation = abs(peak_count - avg_baseline) / (std_baseline + 0.1)
            
            # Alerte si écart > 2 sigma
            if deviation > 2.0:
                alert_type = "SUDDEN_INCREASE" if peak_count > avg_baseline else "UNUSUAL_SILENCE"
                
                await self._generate_spectral_alert(
                    frequency_hz,
                    alert_type,
                    peak_count,
                    deviation
                )
                
        except Exception as e:
            logger.error(f"❌ Erreur vérification activité anormale: {e}")
    
    async def _generate_spectral_alert(self, frequency_hz: int, alert_type: str, 
                                       peak_count: int, deviation: float):
        """Génère une alerte d'activité spectrale anormale"""
        try:
            conn = self.db_manager.get_connection()
            cur = conn.cursor()
            
            description = f"Activité anormale détectée: {peak_count} pics, écart: {deviation:.2f}σ"
            
            cur.execute("""
                INSERT INTO spectral_activity_alerts 
                (frequency_hz, alert_type, peak_count, deviation_from_baseline, description)
                VALUES (?, ?, ?, ?, ?)
            """, (frequency_hz, alert_type, peak_count, deviation, description))
            
            conn.commit()
            conn.close()
            
            logger.warning(f"🚨 Alerte spectrale {alert_type} sur {frequency_hz/1_000_000} MHz")
            
        except Exception as e:
            logger.error(f"❌ Erreur génération alerte: {e}")
    
    def _save_websdr_status(self, servers: List[Dict]):
        """Sauvegarde le statut des WebSDR"""
        try:
            conn = self.db_manager.get_connection()
            cur = conn.cursor()
            
            for server in servers:
                cur.execute("""
                    INSERT OR REPLACE INTO websdr_servers 
                    (url, name, status, last_check)
                    VALUES (?, ?, ?, ?)
                """, (
                    server['url'],
                    server.get('name'),
                    server.get('status', 'unknown'),
                    server.get('last_check')
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde WebSDR: {e}")
    
    def _save_spectral_analysis(self, analysis: Dict):
        """Sauvegarde les résultats d'analyse spectrale"""
        try:
            conn = self.db_manager.get_connection()
            cur = conn.cursor()
            
            cur.execute("""
                INSERT INTO frequency_monitoring 
                (frequency_hz, category, emission_peak_count, signal_strength_avg, 
                 websdr_server, analysis_type)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                analysis['frequency_hz'],
                analysis['category'],
                analysis['peak_count'],
                analysis.get('signal_strength_avg', 0),
                analysis.get('websdr_server'),
                'passive_spectral_fft'
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde analyse: {e}")
    
    def get_recent_spectral_alerts(self, hours: int = 24) -> List[Dict]:
        """Récupère les alertes spectrales récentes"""
        try:
            conn = self.db_manager.get_connection()
            cur = conn.cursor()
            
            cur.execute("""
                SELECT frequency_hz, alert_type, peak_count, 
                       deviation_from_baseline, description, timestamp
                FROM spectral_activity_alerts
                WHERE timestamp > datetime('now', '-? hours')
                ORDER BY timestamp DESC
            """, (hours,))
            
            alerts = []
            for row in cur.fetchall():
                alerts.append({
                    'frequency_hz': row[0],
                    'frequency_mhz': row[0] / 1_000_000,
                    'alert_type': row[1],
                    'peak_count': row[2],
                    'deviation': row[3],
                    'description': row[4],
                    'timestamp': row[5]
                })
            
            conn.close()
            return alerts
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération alertes: {e}")
            return []
    
    def get_frequency_trend(self, frequency_hz: int, days: int = 7) -> Dict:
        """
        Récupère la tendance d'activité spectrale sur N jours
        
        Utile pour détecter des patterns géopolitiques
        """
        try:
            conn = self.db_manager.get_connection()
            cur = conn.cursor()
            
            since_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
            
            cur.execute("""
                SELECT DATE(timestamp) as day,
                       AVG(emission_peak_count) as avg_peaks,
                       MAX(emission_peak_count) as max_peaks,
                       COUNT(*) as samples
                FROM frequency_monitoring
                WHERE frequency_hz = ?
                AND timestamp > ?
                GROUP BY DATE(timestamp)
                ORDER BY day DESC
            """, (frequency_hz, since_date))
            
            trend = []
            for row in cur.fetchall():
                trend.append({
                    'date': row[0],
                    'avg_peak_count': row[1],
                    'max_peak_count': row[2],
                    'sample_count': row[3]
                })
            
            conn.close()
            
            return {
                'frequency_hz': frequency_hz,
                'frequency_mhz': frequency_hz / 1_000_000,
                'period_days': days,
                'trend_data': trend,
                'analysis_type': 'passive_spectral_trend'
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération tendance: {e}")
            return {
                'error': str(e),
                'frequency_hz': frequency_hz
            }
