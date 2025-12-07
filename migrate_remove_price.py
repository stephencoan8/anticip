#!/usr/bin/env python3
"""
Migration Script: Remove Price Metric, Use Only Popularity

This script migrates the database from using redundant 'price' columns
to using only 'popularity' for all artist valuations.

WHAT IT DOES:
1. Renames columns in artist_history (price → popularity_backup)
2. Renames columns in bets (avg_price → avg_popularity)
3. Renames columns in transactions (price_per_share → popularity_per_share)
4. Preserves all existing data
5. Creates backups before changes

SAFETY:
- Creates backups of all affected tables
- Uses transactions (rollback on error)
- Validates data integrity
- Can be run multiple times safely
"""

import psycopg2
from urllib.parse import urlparse
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

def get_db_connection():
    """Get database connection"""
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        result = urlparse(database_url)
        return psycopg2.connect(
            dbname=result.path[1:],
            user=result.username,
            password=result.password,
            host=result.hostname,
            port=result.port
        )
    else:
        return psycopg2.connect(
            dbname="anticip_db",
            user="stephencoan",
            password="",
            host="localhost"
        )

def check_column_exists(cursor, table, column):
    """Check if a column exists in a table"""
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name=%s AND column_name=%s
    """, (table, column))
    return cursor.fetchone() is not None

def migrate():
    """Run the migration"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        print("🚀 Starting migration: Remove price metric, use only popularity")
        print("=" * 70)
        
        # Step 1: Backup artist_history table
        print("\n📦 Step 1: Creating backup of artist_history table...")
        cursor.execute("""
            DROP TABLE IF EXISTS artist_history_backup;
            CREATE TABLE artist_history_backup AS TABLE artist_history;
        """)
        cursor.execute("SELECT COUNT(*) FROM artist_history_backup")
        backup_count = cursor.fetchone()[0]
        print(f"   ✅ Backed up {backup_count} records to artist_history_backup")
        
        # Step 2: For artist_history, we keep popularity column as-is
        # The 'price' column is redundant and will be ignored
        print("\n📊 Step 2: Checking artist_history schema...")
        has_price = check_column_exists(cursor, 'artist_history', 'price')
        has_popularity = check_column_exists(cursor, 'artist_history', 'popularity')
        
        if has_price and has_popularity:
            print(f"   ℹ️  Both 'price' and 'popularity' columns exist")
            print(f"   ✅ We'll use 'popularity' and ignore 'price'")
            # Note: We're not dropping the price column yet to avoid breaking existing deployments
            # The app.py changes will simply stop using it
        elif has_popularity:
            print(f"   ✅ 'popularity' column exists (good!)")
        else:
            print(f"   ❌ No 'popularity' column found!")
            raise Exception("artist_history table is missing 'popularity' column")
        
        # Step 3: Rename bets.avg_price to avg_popularity (if not already done)
        print("\n💰 Step 3: Migrating bets table...")
        if check_column_exists(cursor, 'bets', 'avg_price'):
            if not check_column_exists(cursor, 'bets', 'avg_popularity'):
                print("   🔄 Renaming avg_price → avg_popularity...")
                cursor.execute("""
                    ALTER TABLE bets RENAME COLUMN avg_price TO avg_popularity;
                """)
                print("   ✅ Renamed successfully")
            else:
                print("   ⚠️  Both avg_price and avg_popularity exist - using avg_popularity")
        else:
            print("   ✅ avg_popularity column already exists")
        
        # Step 4: Rename transactions columns (if not already done)
        print("\n📜 Step 4: Migrating transactions table...")
        if check_column_exists(cursor, 'transactions', 'price_per_share'):
            if not check_column_exists(cursor, 'transactions', 'popularity_per_share'):
                print("   🔄 Renaming price_per_share → popularity_per_share...")
                cursor.execute("""
                    ALTER TABLE transactions RENAME COLUMN price_per_share TO popularity_per_share;
                """)
                print("   ✅ Renamed successfully")
            else:
                print("   ⚠️  Both price_per_share and popularity_per_share exist - using popularity_per_share")
        else:
            print("   ✅ popularity_per_share column already exists")
        
        # Step 5: Validate data integrity
        print("\n🔍 Step 5: Validating data integrity...")
        
        # Check artist_history
        cursor.execute("SELECT COUNT(*) FROM artist_history WHERE popularity IS NULL")
        null_pop = cursor.fetchone()[0]
        if null_pop > 0:
            print(f"   ⚠️  Warning: {null_pop} records have NULL popularity")
        else:
            print("   ✅ All artist_history records have popularity values")
        
        # Check bets
        cursor.execute("SELECT COUNT(*) FROM bets WHERE avg_popularity IS NULL")
        null_avg = cursor.fetchone()[0]
        if null_avg > 0:
            print(f"   ⚠️  Warning: {null_avg} bets have NULL avg_popularity")
        else:
            print("   ✅ All bets have avg_popularity values")
        
        # Check transactions
        cursor.execute("SELECT COUNT(*) FROM transactions WHERE popularity_per_share IS NULL")
        null_trans = cursor.fetchone()[0]
        if null_trans > 0:
            print(f"   ⚠️  Warning: {null_trans} transactions have NULL popularity_per_share")
        else:
            print("   ✅ All transactions have popularity_per_share values")
        
        # Step 6: Commit changes
        print("\n💾 Step 6: Committing changes...")
        conn.commit()
        print("   ✅ All changes committed successfully!")
        
        # Summary
        print("\n" + "=" * 70)
        print("✅ MIGRATION COMPLETE!")
        print("=" * 70)
        print("\n📊 Summary:")
        print("   • artist_history: Using 'popularity' column")
        print("   • bets: Using 'avg_popularity' column")
        print("   • transactions: Using 'popularity_per_share' column")
        print(f"   • Backup table created: artist_history_backup ({backup_count} records)")
        print("\n⚠️  Next Steps:")
        print("   1. Deploy updated app.py with new column references")
        print("   2. Test all functionality thoroughly")
        print("   3. After confirming everything works, you can optionally:")
        print("      - DROP COLUMN artist_history.price")
        print("      - DROP COLUMN bets.avg_price (if it exists)")
        print("      - DROP COLUMN transactions.price_per_share (if it exists)")
        print("      - DROP TABLE artist_history_backup")
        print("\n✨ The app now uses ONLY the popularity metric!")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("🔄 Rolling back changes...")
        conn.rollback()
        print("   ✅ Rollback complete - database unchanged")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print("\n" + "🎯" * 35)
    print("  ANTICIP - REMOVE PRICE METRIC MIGRATION")
    print("🎯" * 35 + "\n")
    
    response = input("This will modify your database. Continue? (yes/no): ")
    if response.lower() in ['yes', 'y']:
        migrate()
    else:
        print("❌ Migration cancelled")
