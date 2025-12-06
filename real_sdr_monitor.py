# Flask/real_sdr_monitor.py
"""
Monitoring SDR RÉEL avec RTL-SDR ou KiwiSDR
"""

import logging
import asyncio
import numpy as np
from datetime import datetime
from typing import Dict, List, Any
import requests
import json

logger = logging.getLogger(__name__)

class RealSDRMonitor:
    """Monitor SDR réel avec possibilité RTL-SDR ou KiwiSDR"""
    
    def __init__(self, db_manager, config):
        self.db_manager = db_manager
        self.config = config
        self.rtl_sdr_available = False
        self.kiwisdr_available = False
        
        # Détecter le matériel disponible
        self._detect_hardware()
        
        # Fréquences géopolitiques à surveiller
        self.geopolitical_frequencies = [
            {'freq': 2182, 'name': 'Maritime Emergency', 'type': 'emergency'},
            {'freq': 4625, 'name': 'UVB-76 "The Buzzer"', 'type': 'military'},
            {'freq': 5732, 'name': 'Diplomatic HF', 'type': 'diplomatic'},
            {'freq': 11175, 'name': 'US Military HFGCS', 'type': 'military'},
            {'freq': 121500, 'name': 'Aviation Emergency', 'type': 'aviation'}
        ]
    
    def _detect_hardware(self):
        """Détecte le matériel SDR disponible"""
        try:
            # Essayer d'importer RTL-SDR
            import rtlsdr
            self.rtl_sdr_available = True
            logger.info("✅ RTL-SDR détecté")
        except ImportError:
            logger.info("ℹ️ RTL-SDR non installé - pip install pyrtlsdr")
        
        # Vérifier KiwiSDR
        try:
            test_response = requests.get('http://kiwisdr.com/', timeout=5)
            if test_response.status_code == 200:
                self.kiwisdr_available = True
                logger.info("✅ KiwiSDR accessible")
        except:
            logger.info("ℹ️ KiwiSDR non accessible")
    
    async def monitor_frequency_rtl(self, frequency_hz: int) -> Dict[str, Any]:
        """Surveille une fréquence avec RTL-SDR réel"""
        if not self.rtl_sdr_available:
            return self._mock_sdr_data(frequency_hz)
        
        try:
            from rtlsdr import RtlSdr
            
            sdr = RtlSdr(device_index=self.config.get('rtl_sdr_device_index', 0))
            sdr.sample_rate = self.config.get('sample_rate', 2400000)
            sdr.center_freq = frequency_hz
            sdr.gain = self.config.get('gain', 40)
            
            # Capturer des échantillons
            samples = sdr.read_samples(1024 * 256)
            sdr.close()
            
            # Analyser le signal
            power = np.mean(np.abs(samples) ** 2)
            power_db = 10 * np.log10(power + 1e-10)
            
            # Détecter des signaux
            fft = np.fft.fft(samples)
            fft_freq = np.fft.fftfreq(len(samples), 1/sdr.sample_rate)
            peaks = self._detect_peaks(np.abs(fft), fft_freq)
            
            return {
                'frequency': frequency_hz,
                'power_db': float(power_db),
                'peaks_detected': len(peaks),
                'signal_present': power_db > -60,
                'timestamp': datetime.utcnow().isoformat(),
                'source': 'rtl_sdr',
                'real_data': True
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur RTL-SDR {frequency_hz}: {e}")
            return self._mock_sdr_data(frequency_hz)
    
    async def monitor_frequency_kiwi(self, frequency_hz: int) -> Dict[str, Any]:
        """Surveille une fréquence avec KiwiSDR"""
        if not self.kiwisdr_available:
            return self._mock_sdr_data(frequency_hz)
        
        try:
            # Utiliser un serveur KiwiSDR public
            kiwi_url = "http://kiwisdr.com/"
            
            # Récupérer le spectre (API KiwiSDR)
            spectrum_url = f"{kiwi_url.rstrip('/')}/~~fft"
            params = {
                'f': frequency_hz / 1000,  # kHz
                'b': 10  # 10 kHz bandwidth
            }
            
            response = requests.get(spectrum_url, params=params, timeout=10)
            
            if response.status_code == 200:
                # Analyser le spectre FFT
                spectrum_data = response.content
                # Convertir bytes en array numpy
                import struct
                fft_values = struct.unpack('<' + 'h' * (len(spectrum_data)//2), spectrum_data)
                
                # Analyser les pics
                peaks = self._detect_peaks(np.array(fft_values), [])
                
                return {
                    'frequency': frequency_hz,
                    'peaks_detected': len(peaks),
                    'activity_level': 'high' if len(peaks) > 5 else 'medium' if len(peaks) > 2 else 'low',
                    'timestamp': datetime.utcnow().isoformat(),
                    'source': 'kiwisdr',
                    'real_data': True
                }
            
        except Exception as e:
            logger.error(f"❌ Erreur KiwiSDR {frequency_hz}: {e}")
        
        return self._mock_sdr_data(frequency_hz)
    
    def _detect_peaks(self, signal, frequencies, threshold=0.1):
        """Détecte les pics dans un signal"""
        peaks = []
        for i in range(1, len(signal) - 1):
            if signal[i] > signal[i-1] and signal[i] > signal[i+1]:
                if signal[i] > np.max(signal) * threshold:
                    peaks.append({
                        'index': i,
                        'magnitude': float(signal[i]),
                        'frequency': frequencies[i] if i < len(frequencies) else 0
                    })
        return peaks
    
    async def monitor_all_geopolitical_frequencies(self) -> Dict[str, List[Dict[str, Any]]]:
        """Surveille toutes les fréquences géopolitiques"""
        results = {'emergency': [], 'military': [], 'diplomatic': [], 'aviation': []}
        
        tasks = []
        for freq_info in self.geopolitical_frequencies:
            if self.rtl_sdr_available:
                task = self.monitor_frequency_rtl(freq_info['freq'])
            elif self.kiwisdr_available:
                task = self.monitor_frequency_kiwi(freq_info['freq'])
            else:
                task = self._mock_sdr_data(freq_info['freq'])
            
            tasks.append((freq_info['type'], freq_info, task))
        
        # Exécuter en parallèle
        for freq_type, freq_info, task in tasks:
            result = await task if asyncio.iscoroutine(task) else task
            result['name'] = freq_info['name']
            results[freq_type].append(result)
        
        return results
    
    def _mock_sdr_data(self, frequency: int) -> Dict[str, Any]:
        """Données SDR simulées (fallback)"""
        import random
        return {
            'frequency': frequency,
            'power_db': random.uniform(-90, -30),
            'peaks_detected': random.randint(0, 10),
            'signal_present': random.random() > 0.7,
            'timestamp': datetime.utcnow().isoformat(),
            'source': 'simulation',
            'real_data': False,
            'note': 'Données simulées - Activer le mode RÉEL'
        }
    
    def save_to_database(self, results: Dict[str, Any]):
        """Sauvegarde les résultats en base"""
        try:
            conn = self.db_manager.get_connection()
            cur = conn.cursor()
            
            for category, frequencies in results.items():
                for freq_data in frequencies:
                    cur.execute("""
                        INSERT INTO sdr_monitoring 
                        (frequency, power_db, peaks_detected, signal_present, source, real_data)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        freq_data['frequency'],
                        freq_data.get('power_db', 0),
                        freq_data.get('peaks_detected', 0),
                        freq_data.get('signal_present', False),
                        freq_data.get('source', 'unknown'),
                        freq_data.get('real_data', False)
                    ))
            
            conn.commit()
            conn.close()
            logger.info(f"✅ Données SDR sauvegardées ({len(results)} catégories)")
            
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde SDR: {e}")