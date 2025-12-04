"""
Seed script to prepopulate the database with popular Spotify artists.
Run this once to add a large collection of artists to your database.
"""

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
import os
import psycopg2
from urllib.parse import urlparse
import time

# Load environment variables
load_dotenv()
client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

# Set up Spotipy
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))

# Database connection
database_url = os.getenv("DATABASE_URL")
if database_url:
    # Railway uses postgres:// but psycopg2 requires postgresql://
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    result = urlparse(database_url)
    try:
        db_port = int(result.port) if result.port else 5432
    except (ValueError, TypeError):
        db_port = 5432
    
    conn = psycopg2.connect(
        dbname=result.path[1:],
        user=result.username,
        password=result.password,
        host=result.hostname,
        port=db_port
    )
else:
    # Local development
    conn = psycopg2.connect(
        dbname="anticip_db",
        user="stephencoan",
        password="",
        host="localhost"
    )

cursor = conn.cursor()

# List of popular artist searches and genres to get diverse artists
search_queries = [
    # Top genres
    "pop", "hip hop", "rap", "rock", "indie", "electronic", "r&b", "country", 
    "jazz", "metal", "alternative", "edm", "latin", "reggae", "blues", "folk",
    "punk", "soul", "disco", "funk", "techno", "house", "trap",
    
    # Popular artist names to ensure we get major artists
    "drake", "taylor swift", "bad bunny", "the weeknd", "ariana grande",
    "ed sheeran", "post malone", "billie eilish", "dua lipa", "justin bieber",
    "kanye west", "beyonce", "rihanna", "adele", "bruno mars",
    "travis scott", "eminem", "kendrick lamar", "j cole", "cardi b",
    "coldplay", "imagine dragons", "maroon 5", "one direction", "bts",
    "blackpink", "olivia rodrigo", "harry styles", "shawn mendes", "selena gomez",
    "sza", "21 savage", "lil baby", "doja cat", "megan thee stallion",
    "lil uzi vert", "juice wrld", "xxxtentacion", "lil nas x", "roddy ricch",
    "dababy", "gunna", "young thug", "future", "nicki minaj",
    "frank ocean", "tyler the creator", "asap rocky", "playboi carti",
    "the beatles", "led zeppelin", "pink floyd", "queen", "david bowie",
    "nirvana", "radiohead", "arctic monkeys", "the strokes", "tame impala",
    "mac miller", "anderson paak", "calvin harris", "marshmello", "chainsmokers",
    "diplo", "skrillex", "major lazer", "flume", "odesza",
    "bad bunny", "j balvin", "ozuna", "daddy yankee", "maluma",
    "peso pluma", "karol g", "rauw alejandro", "anuel aa", "farruko"
]

added_artists = set()
total_added = 0

print("🎵 Starting to seed artists database...")
print(f"Will search {len(search_queries)} different queries\n")

for query in search_queries:
    try:
        # Search for artists
        results = sp.search(q=query, type='artist', limit=50)
        
        for artist in results['artists']['items']:
            spotify_id = artist['id']
            
            # Skip if we've already added this artist
            if spotify_id in added_artists:
                continue
            
            name = artist['name']
            popularity = artist['popularity']
            image_url = artist['images'][0]['url'] if artist['images'] else None
            followers = artist['followers']['total']
            genres = artist['genres']
            
            # Only add artists with reasonable popularity (at least 20)
            if popularity < 20:
                continue
            
            try:
                # Insert artist
                cursor.execute("""
                    INSERT INTO artists (spotify_id, name, image_url) 
                    VALUES (%s, %s, %s) 
                    ON CONFLICT (spotify_id) DO UPDATE 
                    SET name = EXCLUDED.name, image_url = EXCLUDED.image_url
                """, (spotify_id, name, image_url))
                
                # Insert artist history (current price based on popularity)
                price = float(popularity)
                cursor.execute("""
                    INSERT INTO artist_history (spotify_id, popularity, price)
                    VALUES (%s, %s, %s)
                """, (spotify_id, popularity, price))
                
                # Insert Spotify data
                cursor.execute("""
                    INSERT INTO spotify_data (spotify_id, followers, popularity, genres)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (spotify_id) DO UPDATE
                    SET followers = EXCLUDED.followers, 
                        popularity = EXCLUDED.popularity, 
                        genres = EXCLUDED.genres,
                        last_updated = CURRENT_TIMESTAMP
                """, (spotify_id, followers, popularity, genres))
                
                added_artists.add(spotify_id)
                total_added += 1
                
                print(f"✅ Added: {name} (Popularity: {popularity}, Followers: {followers:,})")
                
            except Exception as e:
                print(f"❌ Error adding {name}: {e}")
                conn.rollback()
                continue
        
        # Commit after each search query
        conn.commit()
        
        # Small delay to avoid rate limiting
        time.sleep(0.5)
        
    except Exception as e:
        print(f"⚠️  Error searching for '{query}': {e}")
        continue

print(f"\n🎉 Finished! Added {total_added} unique artists to the database.")

cursor.close()
conn.close()
