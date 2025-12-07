#!/usr/bin/env python3
"""
Quick Database Connection Test

Tests that the database has the correct schema and can query properly.
"""

import psycopg2
from dotenv import load_dotenv

load_dotenv()

def test_connection():
    print("🔍 Testing database connection and schema...")
    
    conn = psycopg2.connect(
        dbname="anticip_db",
        user="stephencoan",
        password="",
        host="localhost"
    )
    cursor = conn.cursor()
    
    try:
        # Test 1: Check bets table
        print("\n1. Testing bets table...")
        cursor.execute("SELECT shares, avg_popularity FROM bets WHERE user_id = 1 LIMIT 1;")
        result = cursor.fetchone()
        if result:
            print(f"   ✅ Success! Found bet: shares={result[0]}, avg_popularity={result[1]}")
        else:
            print("   ℹ️  No bets for user_id=1")
        
        # Test 2: Check transactions table  
        print("\n2. Testing transactions table...")
        cursor.execute("SELECT shares, popularity_per_share FROM transactions LIMIT 1;")
        result = cursor.fetchone()
        if result:
            print(f"   ✅ Success! Found transaction: shares={result[0]}, popularity_per_share={result[1]}")
        else:
            print("   ℹ️  No transactions in database")
        
        # Test 3: Check artist_history table
        print("\n3. Testing artist_history table...")
        cursor.execute("SELECT spotify_id, popularity FROM artist_history LIMIT 1;")
        result = cursor.fetchone()
        if result:
            print(f"   ✅ Success! Found history: spotify_id={result[0]}, popularity={result[1]}")
        else:
            print("   ⚠️  No artist history")
        
        print("\n✅ All database tests passed!")
        print("The schema is correct. If you're getting errors, restart the Flask app.\n")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nThis might mean the migration didn't complete correctly.")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    test_connection()
