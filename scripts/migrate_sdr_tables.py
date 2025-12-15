# Flask/scripts/migrate_sdr_tables.py
"""
Script de migration pour corriger les tables SDR
"""

import sqlite3
import os
from pathlib import Path

def migrate_sdr_tables():
    """Migre les tables SDR vers le nouveau schéma"""
    
    # Chemin vers la base de données
    db_path = Path(__file__).parent.parent.parent / "instance" / "geopol.db"
    
    if not db_path.exists():
        print(f"❌ Base de données non trouvée: {db_path}")
        return False
    
    print(f"🔄 Migration de la base de données: {db_path}")
    
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    
    try:
        # 1. Vérifier et mettre à jour sdr_spectrum_scans
        cur.execute("PRAGMA table_info(sdr_spectrum_scans)")
        columns = {row[1] for row in cur.fetchall()}
        
        # Liste des colonnes à ajouter
        columns_to_add = [
            ('category', 'TEXT'),
            ('baseline_deviation', 'REAL'),
            ('server_name', 'TEXT'),
            ('signal_type', 'TEXT')
        ]
        
        for col_name, col_type in columns_to_add:
            if col_name not in columns:
                cur.execute(f"ALTER TABLE sdr_spectrum_scans ADD COLUMN {col_name} {col_type}")
                print(f"  ✅ Colonne '{col_name}' ajoutée")
        
        # 2. Vérifier et mettre à jour sdr_health_metrics
        try:
            cur.execute("PRAGMA table_info(sdr_health_metrics)")
            health_columns = {row[1] for row in cur.fetchall()}
            
            health_columns_to_add = [
                ('frequency_coverage', 'REAL'),
                ('signal_stability', 'REAL'),
                ('noise_floor', 'REAL'),
                ('geopolitical_risk', 'REAL'),
                ('communication_health', 'REAL')
            ]
            
            for col_name, col_type in health_columns_to_add:
                if col_name not in health_columns:
                    cur.execute(f"ALTER TABLE sdr_health_metrics ADD COLUMN {col_name} {col_type}")
                    print(f"  ✅ Colonne '{col_name}' ajoutée à sdr_health_metrics")
                    
        except sqlite3.OperationalError:
            # Table n'existe pas encore
            print("  ℹ️  Table sdr_health_metrics n'existe pas encore")
        
        # 3. Vérifier et mettre à jour sdr_frequency_scans
        try:
            cur.execute("PRAGMA table_info(sdr_frequency_scans)")
            freq_columns = {row[1] for row in cur.fetchall()}
            
            freq_columns_to_add = [
                ('modulation', 'TEXT'),
                ('zone_id', 'TEXT'),
                ('server_id', 'TEXT')
            ]
            
            for col_name, col_type in freq_columns_to_add:
                if col_name not in freq_columns:
                    cur.execute(f"ALTER TABLE sdr_frequency_scans ADD COLUMN {col_name} {col_type}")
                    print(f"  ✅ Colonne '{col_name}' ajoutée à sdr_frequency_scans")
                    
        except sqlite3.OperationalError:
            # Table n'existe pas encore
            print("  ℹ️  Table sdr_frequency_scans n'existe pas encore")
        
        conn.commit()
        print("\n✅ Migration terminée avec succès")
        return True
        
    except Exception as e:
        print(f"❌ Erreur migration: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

def drop_and_recreate_tables():
    """Supprime et recrée les tables SDR (en cas d'erreur grave)"""
    
    db_path = Path(__file__).parent.parent.parent / "instance" / "geopol.db"
    
    if not db_path.exists():
        print(f"❌ Base de données non trouvée: {db_path}")
        return False
    
    print(f"⚠️  RECRÉATION COMPLÈTE des tables SDR: {db_path}")
    print("⚠️  Toutes les données SDR seront perdues !")
    
    confirmation = input("Confirmer (oui/non): ")
    if confirmation.lower() != 'oui':
        print("❌ Annulé")
        return False
    
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    
    try:
        # Supprimer les tables SDR
        tables_to_drop = [
            'sdr_spectrum_scans',
            'sdr_health_metrics',
            'sdr_frequency_scans',
            'sdr_anomalies',
            'sdr_websdr_servers',
            'sdr_metrics'
        ]
        
        for table in tables_to_drop:
            try:
                cur.execute(f"DROP TABLE IF EXISTS {table}")
                print(f"  🗑️  Table {table} supprimée")
            except:
                pass
        
        # Recréer avec le bon schéma
        from Flask.geopol_data.connectors.sdr_spectrum_service import SDRSpectrumService
        from Flask.geopol_data.sdr_analyzer import SDRAnalyzer
        
        # Ces imports initialiseront les tables automatiquement
        print("  🔄 Tables recréées automatiquement au prochain démarrage")
        
        conn.commit()
        print("\n✅ Tables recréées avec succès")
        return True
        
    except Exception as e:
        print(f"❌ Erreur recréation: {e}")
        conn.rollback()
        return False
        
    finally:
        conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("OUTIL DE MIGRATION SDR")
    print("=" * 60)
    print("\nOptions:")
    print("1. Migrer les tables (ajouter colonnes manquantes)")
    print("2. Recréer complètement les tables (perte données)")
    print("3. Vérifier le schéma actuel")
    
    choice = input("\nChoix (1-3): ")
    
    if choice == '1':
        migrate_sdr_tables()
    elif choice == '2':
        drop_and_recreate_tables()
    elif choice == '3':
        db_path = Path(__file__).parent.parent.parent / "instance" / "geopol.db"
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        
        try:
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'sdr_%'")
            tables = cur.fetchall()
            
            print("\n📋 Tables SDR existantes:")
            for table in tables:
                print(f"\n{table[0]}:")
                cur.execute(f"PRAGMA table_info({table[0]})")
                for col in cur.fetchall():
                    print(f"  - {col[1]} ({col[2]})")
        
        finally:
            conn.close()
    else:
        print("❌ Choix invalide")