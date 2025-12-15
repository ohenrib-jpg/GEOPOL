# Flask/sdr_anomaly_detector.py
import numpy as np
from datetime import datetime, timedelta

class SDRAnomalyDetector:
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    def detect_spectral_anomalies(self, frequency_khz: int, current_peaks: int) -> Dict:
        """Détecte les anomalies avec analyse statistique"""
        baseline = self._get_baseline(frequency_khz)
        
        if not baseline:
            return {'anomaly': False, 'confidence': 0}
        
        # Calculer l'écart standardisé (z-score)
        z_score = (current_peaks - baseline['mean']) / (baseline['std'] + 1e-10)
        
        # Détection multi-seuil
        if abs(z_score) > 3.0:
            severity = 'critical'
            anomaly_type = 'extreme_deviation'
        elif abs(z_score) > 2.0:
            severity = 'high'
            anomaly_type = 'significant_deviation'
        elif abs(z_score) > 1.5:
            severity = 'medium'
            anomaly_type = 'moderate_deviation'
        else:
            return {'anomaly': False, 'confidence': 0}
        
        return {
            'anomaly': True,
            'severity': severity,
            'type': anomaly_type,
            'z_score': float(z_score),
            'current_peaks': current_peaks,
            'baseline_mean': baseline['mean'],
            'confidence': min(0.99, abs(z_score) / 5.0)
        }
    
    def _get_baseline(self, frequency_khz: int) -> Dict:
        """Calcule la baseline historique"""
        try:
            conn = self.db_manager.get_connection()
            cur = conn.cursor()
            
            # 7 derniers jours
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            
            cur.execute("""
                SELECT peak_count, timestamp
                FROM sdr_spectrum_scans
                WHERE frequency_khz = ?
                AND timestamp > ?
                ORDER BY timestamp
            """, (frequency_khz, week_ago))
            
            data = cur.fetchall()
            conn.close()
            
            if len(data) < 10:  # Pas assez de données
                return None
            
            peaks = [row[0] for row in data]
            
            return {
                'mean': np.mean(peaks),
                'std': np.std(peaks),
                'min': np.min(peaks),
                'max': np.max(peaks),
                'samples': len(peaks)
            }
            
        except Exception as e:
            print(f"❌ Erreur baseline: {e}")
            return None