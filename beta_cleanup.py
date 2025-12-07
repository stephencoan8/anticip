#!/usr/bin/env python3
"""
BETA CLEANUP: Aggressive Database Optimization

Since the app is in BETA, we can make breaking changes to optimize the database.
This script performs aggressive cleanup that wouldn't be safe in production.

WHAT IT DOES:
1. Drops old redundant columns (price, avg_price, price_per_share)
2. Removes backup tables
3. Optimizes table structure
4. Adds helpful constraints and indexes
5. Cleans up any orphaned data

SAFETY: This is a BETA app, so we can be aggressive!
"""

import psycopg2
from urllib.parse import urlparse
import os
from dotenv import load_dotenv

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

def beta_cleanup():
    """Aggressive beta cleanup"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        print("\n" + "🧹" * 35)
        print("  ANTICIP BETA - AGGRESSIVE DATABASE CLEANUP")
        print("🧹" * 35 + "\n")
        
        # Step 1: Drop old redundant columns
        print("🗑️  Step 1: Removing redundant columns...")
        
        try:
            cursor.execute("ALTER TABLE artist_history DROP COLUMN IF EXISTS price CASCADE;")
            print("   ✅ Dropped artist_history.price")
        except Exception as e:
            print(f"   ⚠️  Could not drop artist_history.price: {e}")
        
        try:
            cursor.execute("ALTER TABLE bets DROP COLUMN IF EXISTS avg_price CASCADE;")
            print("   ✅ Dropped bets.avg_price")
        except Exception as e:
            print(f"   ⚠️  Could not drop bets.avg_price: {e}")
        
        try:
            cursor.execute("ALTER TABLE transactions DROP COLUMN IF EXISTS price_per_share CASCADE;")
            print("   ✅ Dropped transactions.price_per_share")
        except Exception as e:
            print(f"   ⚠️  Could not drop transactions.price_per_share: {e}")
        
        # Step 2: Remove backup tables
        print("\n📦 Step 2: Removing backup tables...")
        cursor.execute("DROP TABLE IF EXISTS artist_history_backup CASCADE;")
        print("   ✅ Dropped artist_history_backup")
        
        # Step 3: Add helpful constraints
        print("\n🔒 Step 3: Adding data integrity constraints...")
        
        # Ensure popularity is in valid range (0-100)
        try:
            cursor.execute("""
                DO $$ 
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.table_constraints 
                        WHERE constraint_name = 'check_popularity_range'
                    ) THEN
                        ALTER TABLE artist_history 
                        ADD CONSTRAINT check_popularity_range 
                        CHECK (popularity >= 0 AND popularity <= 100);
                    END IF;
                END $$;
            """)
            print("   ✅ Added popularity range constraint (0-100)")
        except Exception as e:
            print(f"   ⚠️  Constraint already exists or error: {e}")
        
        # Ensure avg_popularity is valid
        try:
            cursor.execute("""
                DO $$ 
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.table_constraints 
                        WHERE constraint_name = 'check_avg_popularity_range'
                    ) THEN
                        ALTER TABLE bets 
                        ADD CONSTRAINT check_avg_popularity_range 
                        CHECK (avg_popularity >= 0 AND avg_popularity <= 100);
                    END IF;
                END $$;
            """)
            print("   ✅ Added avg_popularity range constraint (0-100)")
        except Exception as e:
            print(f"   ⚠️  Constraint already exists or error: {e}")
        
        # Ensure popularity_per_share is valid
        try:
            cursor.execute("""
                DO $$ 
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.table_constraints 
                        WHERE constraint_name = 'check_popularity_per_share_range'
                    ) THEN
                        ALTER TABLE transactions 
                        ADD CONSTRAINT check_popularity_per_share_range 
                        CHECK (popularity_per_share >= 0 AND popularity_per_share <= 100);
                    END IF;
                END $$;
            """)
            print("   ✅ Added popularity_per_share range constraint (0-100)")
        except Exception as e:
            print(f"   ⚠️  Constraint already exists or error: {e}")
        
        # Step 4: Clean up orphaned data
        print("\n🧽 Step 4: Cleaning up orphaned data...")
        
        # Remove artist history for non-existent artists
        cursor.execute("""
            DELETE FROM artist_history 
            WHERE spotify_id NOT IN (SELECT spotify_id FROM artists);
        """)
        deleted_history = cursor.rowcount
        if deleted_history > 0:
            print(f"   ✅ Removed {deleted_history} orphaned artist_history records")
        else:
            print("   ✅ No orphaned artist_history records")
        
        # Remove spotify_data for non-existent artists
        cursor.execute("""
            DELETE FROM spotify_data 
            WHERE spotify_id NOT IN (SELECT spotify_id FROM artists);
        """)
        deleted_spotify = cursor.rowcount
        if deleted_spotify > 0:
            print(f"   ✅ Removed {deleted_spotify} orphaned spotify_data records")
        else:
            print("   ✅ No orphaned spotify_data records")
        
        # Step 5: Get final stats (before commit)
        print("\n📈 Step 5: Database statistics...")
        
        cursor.execute("SELECT COUNT(*) FROM artists;")
        artist_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM artist_history;")
        history_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM bets;")
        bet_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM transactions;")
        transaction_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users;")
        user_count = cursor.fetchone()[0]
        
        print(f"   • Artists: {artist_count}")
        print(f"   • History records: {history_count}")
        print(f"   • Active bets: {bet_count}")
        print(f"   • Transactions: {transaction_count}")
        print(f"   • Users: {user_count}")
        
        # Commit all changes BEFORE vacuum
        conn.commit()
        
        # Step 6: Optimize database (must be outside transaction)
        print("\n📊 Step 6: Optimizing database...")
        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cursor.execute("VACUUM ANALYZE;")
        print("   ✅ Vacuumed and analyzed all tables")
        
        # Summary
        print("\n" + "=" * 70)
        print("✅ BETA CLEANUP COMPLETE!")
        print("=" * 70)
        print("\n🎯 Summary:")
        print("   • Removed redundant 'price' columns")
        print("   • Deleted backup tables")
        print("   • Added data integrity constraints")
        print("   • Cleaned orphaned data")
        print("   • Optimized database tables")
        print("\n✨ Database is now lean, clean, and optimized!")
        print("\n📊 Current Database:")
        print(f"   • {artist_count} artists")
        print(f"   • {history_count} popularity records")
        print(f"   • {bet_count} holdings")
        print(f"   • {transaction_count} transactions")
        print(f"   • {user_count} users")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("🔄 Rolling back changes...")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print("\n⚠️  WARNING: BETA MODE - AGGRESSIVE CLEANUP")
    print("This will permanently remove redundant columns and data.")
    print("Only safe because app is in BETA with no production users.\n")
    
    response = input("Continue with aggressive cleanup? (yes/no): ")
    if response.lower() in ['yes', 'y']:
        beta_cleanup()
    else:
        print("❌ Cleanup cancelled")
