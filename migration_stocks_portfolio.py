# Flask/migration_stocks_portfolio.py
"""
Migration pour ajouter les tables de suivi boursier personnalisé
- user_stock_portfolios : Secteurs personnalisés (max 4)
- stock_alerts : Alertes boursières
"""

import sqlite3
import logging

logger = logging.getLogger(__name__)


def run_stocks_portfolio_migration(db_manager):
    """Exécute la migration pour les tables de suivi boursier"""

    try:
        conn = db_manager.get_connection()
        cursor = conn.cursor()

        # ====================================================================
        # TABLE: user_stock_portfolios
        # ====================================================================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_stock_portfolios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER DEFAULT 1,
                sector_name TEXT NOT NULL,
                sector_order INTEGER NOT NULL,
                stock_symbols TEXT,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL
            )
        ''')
        logger.info("✅ Table user_stock_portfolios créée/vérifiée")

        # ====================================================================
        # TABLE: stock_alerts
        # ====================================================================
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_symbol TEXT NOT NULL,
                condition TEXT NOT NULL,
                threshold REAL NOT NULL,
                active INTEGER DEFAULT 1,
                created_at TIMESTAMP NOT NULL,
                triggered_at TIMESTAMP,
                last_check TIMESTAMP
            )
        ''')
        logger.info("✅ Table stock_alerts créée/vérifiée")

        # ====================================================================
        # INDEX pour optimisation
        # ====================================================================
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_portfolios_user_order
            ON user_stock_portfolios(user_id, sector_order)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_alerts_symbol_active
            ON stock_alerts(stock_symbol, active)
        ''')

        logger.info("✅ Index créés/vérifiés")

        conn.commit()
        conn.close()

        print("\n" + "="*70)
        print("✅ MIGRATION STOCKS PORTFOLIO TERMINÉE")
        print("="*70)
        print("Tables créées :")
        print("  • user_stock_portfolios - Secteurs personnalisés")
        print("  • stock_alerts - Alertes boursières")
        print("="*70 + "\n")

        return True

    except Exception as e:
        logger.error(f"❌ Erreur migration stocks portfolio: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    # Test de la migration
    from database import DatabaseManager

    db_manager = DatabaseManager()
    run_stocks_portfolio_migration(db_manager)
