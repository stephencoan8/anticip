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
        
        # Check if bets table has avg_popularity (correct) or avg_price (old)
        has_avg_popularity = check_column_exists(cursor, 'bets', 'avg_popularity')
        has_avg_price = check_column_exists(cursor, 'bets', 'avg_price')
        
        if has_avg_popularity and not has_avg_price:
            print("✅ Database schema is correct (has avg_popularity)")
            cursor.close()
            conn.close()
            return True
            
        if has_avg_price and not has_avg_popularity:
            print("🔄 Migrating: Renaming avg_price → avg_popularity...")
            cursor.execute("ALTER TABLE bets RENAME COLUMN avg_price TO avg_popularity;")
            print("✅ Migration complete!")
            
        if has_avg_price and has_avg_popularity:
            print("⚠️  Both columns exist, dropping old avg_price column...")
            cursor.execute("ALTER TABLE bets DROP COLUMN avg_price CASCADE;")
            print("✅ Cleanup complete!")
            
        if not has_avg_price and not has_avg_popularity:
            print("❌ ERROR: bets table missing both avg_price and avg_popularity columns!")
            cursor.close()
            conn.close()
            return False
            
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Migration error: {e}")
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
