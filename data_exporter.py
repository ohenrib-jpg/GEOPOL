# Flask/data_exporter.py 
import json
import sqlite3
import os
import shutil
from datetime import datetime, timedelta
import logging
import threading
import time

logger = logging.getLogger(__name__)

class DataExporter:
    def __init__(self, db_path):
        self.db_path = db_path
        self.exports_dir = "exports"
        os.makedirs(self.exports_dir, exist_ok=True)
        
    def export_daily_analytics(self):
        """Exporte les analyses journalières"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            today = datetime.now().strftime('%Y-%m-%d')
            export_data = {
                "export_date": today,
                "sentiment_analysis": self._get_daily_sentiments(cursor, today),
                "theme_analysis": self._get_daily_themes(cursor, today),
                "alerts_triggered": self._get_daily_alerts(cursor, today),
                "sdr_activity": self._get_daily_sdr_activity(cursor, today),
                "articles_count": self._get_daily_articles_count(cursor, today)
            }
            
            # Sauvegarde locale
            export_dir = os.path.join(self.exports_dir, "daily")
            os.makedirs(export_dir, exist_ok=True)
            filename = f"analytics_{today}.json"
            filepath = os.path.join(export_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Export quotidien créé: {filename}")
            
            # Sauvegarde automatique vers le dossier partagé si configuré
            self._backup_to_shared_folder(filepath)
            
            return filepath
            
        except Exception as e:
            logger.error(f"❌ Erreur export quotidien: {e}")
            return None
        finally:
            conn.close()
    
    def create_weekly_summary(self):
        """Crée un résumé hebdomadaire"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            
            summary = {
                "period": {
                    "start": start_date.strftime('%Y-%m-%d'),
                    "end": end_date.strftime('%Y-%m-%d')
                },
                "articles_analyzed": self._get_weekly_articles_count(cursor, start_date, end_date),
                "sentiment_trends": self._get_weekly_sentiment_trends(cursor, start_date, end_date),
                "top_themes": self._get_weekly_top_themes(cursor, start_date, end_date),
                "alert_statistics": self._get_weekly_alert_stats(cursor, start_date, end_date),
                "sdr_insights": self._get_weekly_sdr_insights(cursor, start_date, end_date),
                "performance_metrics": self._get_performance_metrics(cursor, start_date, end_date)
            }
            
            # Sauvegarde locale
            export_dir = os.path.join(self.exports_dir, "weekly")
            os.makedirs(export_dir, exist_ok=True)
            filename = f"weekly_summary_{end_date.strftime('%Y-%m-%d')}.json"
            filepath = os.path.join(export_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Résumé hebdomadaire créé: {filename}")
            
            # Sauvegarde automatique
            self._backup_to_shared_folder(filepath)
            
            return filepath
            
        except Exception as e:
            logger.error(f"❌ Erreur résumé hebdomadaire: {e}")
            return None
        finally:
            conn.close()
    
    def create_backup(self):
        """Crée une sauvegarde complète de la base"""
        try:
            backup_dir = os.path.join(self.exports_dir, "backups")
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = f"geo_backup_{timestamp}.db"
            backup_path = os.path.join(backup_dir, backup_file)
            
            # Copie de la base de données
            shutil.copy2(self.db_path, backup_path)
            
            # Export des métriques avec la sauvegarde
            self._export_backup_metadata(backup_path)
            
            logger.info(f"✅ Sauvegarde créée: {backup_file}")
            
            # Sauvegarde automatique
            self._backup_to_shared_folder(backup_path)
            
            return backup_path
            
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde: {e}")
            return None
    
    def _backup_to_shared_folder(self, filepath):
        """Sauvegarde automatique vers un dossier partagé"""
        try:
            # Chemin vers votre Google Drive local ou dossier partagé
            shared_folder = os.path.expanduser("~/Google Drive/GEO_Exports")
            
            if os.path.exists(shared_folder):
                filename = os.path.basename(filepath)
                dest_path = os.path.join(shared_folder, filename)
                shutil.copy2(filepath, dest_path)
                logger.info(f"📤 Sauvegarde automatique: {filename}")
            else:
                logger.info("ℹ️ Dossier partagé non trouvé, sauvegarde locale uniquement")
                
        except Exception as e:
            logger.warning(f"⚠️ Erreur sauvegarde automatique: {e}")
    
    def _export_backup_metadata(self, backup_path):
        """Exporte les métadonnées de la sauvegarde"""
        try:
            metadata = {
                "backup_date": datetime.now().isoformat(),
                "backup_file": os.path.basename(backup_path),
                "database_size": os.path.getsize(backup_path),
                "export_stats": self._get_export_stats()
            }
            
            metadata_file = backup_path.replace('.db', '_metadata.json')
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"❌ Erreur métadonnées sauvegarde: {e}")
    
    def _get_export_stats(self):
        """Récupère les statistiques d'export"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            stats = {
                "total_articles": self._count_table(cursor, "articles"),
                "total_themes": self._count_table(cursor, "themes"),
                "total_alerts": self._count_table(cursor, "triggered_alerts"),
                "total_sdr_streams": self._count_table(cursor, "sdr_streams"),
                "export_timestamp": datetime.now().isoformat()
            }
            
            return stats
        except Exception as e:
            logger.error(f"❌ Erreur statistiques export: {e}")
            return {}
        finally:
            conn.close()
    
    def _count_table(self, cursor, table_name):
        """Compte les lignes d'une table"""
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            return cursor.fetchone()[0]
        except:
            return 0

    # Méthodes d'extraction des données (gardées de la version précédente)
    def _get_daily_sentiments(self, cursor, date):
        try:
            cursor.execute("""
                SELECT sentiment_type, COUNT(*) as count
                FROM articles 
                WHERE DATE(pub_date) = ? 
                GROUP BY sentiment_type
            """, (date,))
            return dict(cursor.fetchall())
        except:
            return {}
    
    def _get_daily_themes(self, cursor, date):
        try:
            cursor.execute("""
                SELECT t.name, COUNT(*) as article_count
                FROM article_themes at
                JOIN themes t ON at.theme_id = t.id
                JOIN articles a ON at.article_id = a.id
                WHERE DATE(a.pub_date) = ?
                GROUP BY t.name
                ORDER BY article_count DESC
                LIMIT 10
            """, (date,))
            return dict(cursor.fetchall())
        except:
            return {}
    
    def _get_daily_alerts(self, cursor, date):
        try:
            cursor.execute("""
                SELECT alert_name, COUNT(*) as triggered_count
                FROM triggered_alerts 
                WHERE DATE(created_at) = ?
                GROUP BY alert_name
            """, (date,))
            return dict(cursor.fetchall())
        except:
            return {}
    
    def _get_daily_sdr_activity(self, cursor, date):
        try:
            cursor.execute("""
                SELECT s.name, SUM(a.activity_count) as total_activity
                FROM sdr_daily_activity a
                JOIN sdr_streams s ON a.stream_id = s.id
                WHERE a.date = ?
                GROUP BY s.name
            """, (date,))
            return dict(cursor.fetchall())
        except:
            return {}
    
    def _get_daily_articles_count(self, cursor, date):
        try:
            cursor.execute("""
                SELECT COUNT(*) FROM articles WHERE DATE(pub_date) = ?
            """, (date,))
            return cursor.fetchone()[0] or 0
        except:
            return 0
    
    def _get_weekly_articles_count(self, cursor, start_date, end_date):
        try:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM articles 
                WHERE pub_date BETWEEN ? AND ?
            """, (start_date, end_date))
            return cursor.fetchone()[0] or 0
        except:
            return 0
    
    def _get_weekly_sentiment_trends(self, cursor, start_date, end_date):
        try:
            cursor.execute("""
                SELECT DATE(pub_date) as day, sentiment_type, COUNT(*) as count
                FROM articles 
                WHERE pub_date BETWEEN ? AND ?
                GROUP BY DATE(pub_date), sentiment_type
                ORDER BY day
            """, (start_date, end_date))
            
            trends = {}
            for day, sentiment, count in cursor.fetchall():
                if day not in trends:
                    trends[day] = {}
                trends[day][sentiment] = count
            return trends
        except:
            return {}
    
    def _get_weekly_top_themes(self, cursor, start_date, end_date):
        try:
            cursor.execute("""
                SELECT t.name, COUNT(*) as article_count
                FROM article_themes at
                JOIN themes t ON at.theme_id = t.id
                JOIN articles a ON at.article_id = a.id
                WHERE a.pub_date BETWEEN ? AND ?
                GROUP BY t.name
                ORDER BY article_count DESC
                LIMIT 15
            """, (start_date, end_date))
            return dict(cursor.fetchall())
        except:
            return {}
    
    def _get_weekly_alert_stats(self, cursor, start_date, end_date):
        try:
            cursor.execute("""
                SELECT severity, COUNT(*) as count
                FROM triggered_alerts 
                WHERE created_at BETWEEN ? AND ?
                GROUP BY severity
            """, (start_date, end_date))
            return dict(cursor.fetchall())
        except:
            return {}
    
    def _get_weekly_sdr_insights(self, cursor, start_date, end_date):
        try:
            cursor.execute("""
                SELECT s.name, 
                       AVG(a.activity_count) as avg_activity,
                       MAX(a.activity_count) as max_activity
                FROM sdr_daily_activity a
                JOIN sdr_streams s ON a.stream_id = s.id
                WHERE a.date BETWEEN ? AND ?
                GROUP BY s.name
            """, (start_date, end_date))
            
            insights = {}
            for name, avg, max_val in cursor.fetchall():
                insights[name] = {
                    'average_activity': round(avg, 2) if avg else 0,
                    'peak_activity': max_val or 0
                }
            return insights
        except:
            return {}
    
    def _get_performance_metrics(self, cursor, start_date, end_date):
        """Métriques de performance de l'analyse"""
        try:
            cursor.execute("""
                SELECT COUNT(*) as total_processed,
                       AVG(LENGTH(content)) as avg_content_length,
                       COUNT(DISTINCT feed_url) as unique_sources
                FROM articles 
                WHERE pub_date BETWEEN ? AND ?
            """, (start_date, end_date))
            
            result = cursor.fetchone()
            return {
                "total_articles_processed": result[0] or 0,
                "average_content_length": round(result[1] or 0, 2),
                "unique_news_sources": result[2] or 0
            }
        except:
            return {}