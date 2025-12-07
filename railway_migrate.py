#!/usr/bin/env python3
"""
Railway Migration Script - Run on deployment to ensure database schema is correct
This will be executed automatically by Railway before starting the app.
"""
import psycopg2
import os
import sys

def check_column_exists(cursor, table, column):
    """Check if a column exists in a table"""
    cursor.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_name = %s AND column_name = %s
        );
    """, (table, column))
    return cursor.fetchone()[0]

def run_migration():
    """Ensure database has the correct schema"""
    try:
        # Connect to database
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            print("⚠️  No DATABASE_URL found, skipping migration")
            return True
            
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("🔄 Checking database schema...")
        migration_needed = False
        
        # 1. Check BETS table: avg_popularity (correct) or avg_price (old)
        print("\n📋 Checking BETS table...")
        has_avg_popularity = check_column_exists(cursor, 'bets', 'avg_popularity')
        has_avg_price = check_column_exists(cursor, 'bets', 'avg_price')
        
        if has_avg_price and not has_avg_popularity:
            print("   🔄 Migrating: Renaming avg_price → avg_popularity...")
            cursor.execute("ALTER TABLE bets RENAME COLUMN avg_price TO avg_popularity;")
            print("   ✅ Bets migration complete!")
            migration_needed = True
        elif has_avg_price and has_avg_popularity:
            print("   ⚠️  Both columns exist, dropping old avg_price column...")
            cursor.execute("ALTER TABLE bets DROP COLUMN avg_price CASCADE;")
            print("   ✅ Bets cleanup complete!")
            migration_needed = True
        elif has_avg_popularity:
            print("   ✅ Bets table correct (has avg_popularity)")
        else:
            print("   ❌ ERROR: bets table missing avg_popularity column!")
            return False
        
        # 2. Check TRANSACTIONS table: popularity_per_share (correct) or price_per_share (old)
        print("\n📋 Checking TRANSACTIONS table...")
        has_popularity_per_share = check_column_exists(cursor, 'transactions', 'popularity_per_share')
        has_price_per_share = check_column_exists(cursor, 'transactions', 'price_per_share')
        
        if has_price_per_share and not has_popularity_per_share:
            print("   🔄 Migrating: Renaming price_per_share → popularity_per_share...")
            cursor.execute("ALTER TABLE transactions RENAME COLUMN price_per_share TO popularity_per_share;")
            print("   ✅ Transactions migration complete!")
            migration_needed = True
        elif has_price_per_share and has_popularity_per_share:
            print("   ⚠️  Both columns exist, dropping old price_per_share column...")
            cursor.execute("ALTER TABLE transactions DROP COLUMN price_per_share CASCADE;")
            print("   ✅ Transactions cleanup complete!")
            migration_needed = True
        elif has_popularity_per_share:
            print("   ✅ Transactions table correct (has popularity_per_share)")
        else:
            print("   ❌ ERROR: transactions table missing popularity_per_share column!")
            return False
        
        if not migration_needed:
            print("\n✅ All database schemas are correct - no migration needed")
        else:
            print("\n✅ All migrations completed successfully")
            
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Migration error: {e}")
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
