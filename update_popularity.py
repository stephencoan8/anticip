#!/usr/bin/env python3
"""
Daily Artist Popularity Updater
Updates all artist popularity scores and price history from Spotify API
Run this daily via Railway Cron Jobs or GitHub Actions
"""

import os
import psycopg2
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
import time
from datetime import datetime

# Load environment variables
load_dotenv()

# Spotify setup
client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=client_id,
    client_secret=client_secret
))

# Database setup
database_url = os.getenv("DATABASE_URL")
if database_url:
    # Convert postgres:// to postgresql://
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    conn = psycopg2.connect(database_url)
else:
    # Local fallback
    conn = psycopg2.connect(
        dbname="anticip_db",
        user="stephencoan",
        password="",
        host="localhost"
    )

cursor = conn.cursor()

def update_artist_popularity(spotify_id, name):
    """Update a single artist's popularity from Spotify"""
    try:
        # Get current artist info from Spotify
        artist = sp.artist(spotify_id)
        popularity = artist['popularity']
        
        # Insert new popularity history entry
        cursor.execute("""
            INSERT INTO artist_history (spotify_id, popularity, recorded_at) 
            VALUES (%s, %s, NOW())
        """, (spotify_id, popularity))
        
        conn.commit()
        return popularity, True
        
    except Exception as e:
        print(f"✗ Error updating {name} ({spotify_id}): {e}")
        conn.rollback()
        return None, False

# Main execution
print("=" * 70)
print("ANTICIP DAILY POPULARITY UPDATER")
print("=" * 70)
print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
db_target = "Production (Railway)" if database_url and 'railway' in database_url.lower() else "Local Database"
print(f"Target: {db_target}")
print("=" * 70)

# Get all artists from database
cursor.execute("SELECT spotify_id, name FROM artists ORDER BY name")
artists = cursor.fetchall()

print(f"\nFound {len(artists)} artists to update\n")

updated = 0
failed = 0
total_popularity = 0

for i, (spotify_id, name) in enumerate(artists, 1):
    print(f"[{i}/{len(artists)}] Updating {name}...", end=" ")
    
    popularity, success = update_artist_popularity(spotify_id, name)
    
    if success:
        updated += 1
        total_popularity += popularity
        print(f"✓ Popularity: {popularity}")
    else:
        failed += 1
        print("✗ Failed")
    
    # Rate limiting: wait between requests to avoid hitting Spotify API limits
    if i < len(artists):
        time.sleep(0.3)  # 300ms between requests = ~3 requests/second

# Calculate average popularity
avg_popularity = total_popularity / updated if updated > 0 else 0

print("\n" + "=" * 70)
print("UPDATE COMPLETE")
print("=" * 70)
print(f"✓ Successfully updated: {updated} artists")
print(f"✗ Failed: {failed} artists")
print(f"📊 Average popularity: {avg_popularity:.1f}")
print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

# Close database connection
cursor.close()
conn.close()
