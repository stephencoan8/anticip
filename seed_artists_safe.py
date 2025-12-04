#!/usr/bin/env python3
"""
Safe Artist Database Seeder with Rate Limiting
Adds popular artists to the anticip database with Spotify API rate limit handling
"""

import os
import psycopg2
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Spotify setup
client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=client_id,
    client_secret=client_secret
))

# Database setup - use Railway's production DATABASE_URL
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

# Top 100+ popular artists to seed
# These are well-known Spotify IDs across various genres
ARTIST_IDS = [
    # Pop/Mainstream
    "06HL4z0CvFAxyc27GXpf02",  # Taylor Swift
    "3TVXtAsR1Inumwj472S9r4",  # Drake
    "1Xyo4u8uXC1ZmMpatF05PJ",  # The Weeknd
    "66CXWjxzNUsdJxJ2JdwvnR",  # Ariana Grande
    "6eUKZXaKkcviH0Ku9w2n3V",  # Ed Sheeran
    "1dfeR4HaWDbWqFHLkxsg1d",  # Queen
    "3WrFJ7ztbogyGnTHbHJFl2",  # The Beatles
    "0du5cEVh5yTK9QJze8zA0C",  # Bruno Mars
    "4gzpq5DPGxSnKTe4SA8HAU",  # Coldplay
    "7dGJo4pcD2V6oG8kP0tJRR",  # Eminem
    "1HY2Jd0NmPuamShAr6KMms",  # Lady Gaga
    "6M2wZ9GZgrQXHCFfjv46we",  # Dua Lipa
    "04gDigrS5kc9YWfZHwBETP",  # Maroon 5
    "5pKCCKE2ajJHZ9KAiaK11H",  # Rihanna
    "181bsRPaVXVlUKXrxwZfHK",  # Megan Thee Stallion
    "7tYKF4w9nC0nq9CsPZTHyP",  # SZA
    "6LuN9FCkKOj5PcnpouEgny",  # Khalid
    "7n2Ycct7Beij7Dj7new7xy",  # Lukas Graham
    "6S2OmqARrzebs0tKUEyXyp",  # Doja Cat
    "4r63FhuTkUYltbVAg5TQnk",  # Cardi B
    
    # Hip Hop/Rap
    "0Y5tJX1MQlPlqiwlOH1tJY",  # Travis Scott
    "1URnnhqYAYcrqrcwql10ft",  # 21 Savage
    "2YZyLoL8N0Wb9xBt1NhZWg",  # Kendrick Lamar
    "5K4W6rqBFWDnAN6FQUkS6x",  # Kanye West
    "137W8MRPWKqSmrBGDBFSop",  # Wiz Khalifa
    "1uNFoZAHBGtllmzznpCI3s",  # Justin Bieber
    "6LqNN22kT3074XbTVUrhzX",  # Katy Perry
    "15UsOTVnJzReFVN1VCnxy4",  # XXXTENTACION
    "2o5jDhtHVPhrJdv3cEQ99Z",  # Lil Uzi Vert
    "360IAlyVv4PCEVjgyMZrxK",  # Miguel
    "3Nrfpe0tUJi4K4DXYWgMUX",  # BTS
    "0iEtIxbK0KxaSlF7G42ZOp",  # Metro Boomin
    "5f7VJjfbwm532GiveGC0ZK",  # Lil Baby
    "6l3HvQ5sa6mXTsMTB19rO5",  # J. Cole
    "1Cs0zKBU1kc0i8ypK3B9ai",  # David Guetta
    "3qm84nBOXUEQ2vnTfUTTFC",  # Gunna
    "4O15NlyKLIASxsJ0PrXPfz",  # Lil Durk
    "7c0XG5cIJTrrAgEC3ULPiq",  # Ty Dolla $ign
    
    # Rock/Alternative
    "53XhwfbYqKCa1cC15pYq2q",  # Imagine Dragons
    "7Ln80lUS6He07XvHI8qqHH",  # Arctic Monkeys
    "0C0XlULifJtAgn6ZNCW2eu",  # The Killers
    "6olE6TJLqED3rqDCT0FyPh",  # Nirvana
    "0oSGxfWSnnOXhD2fKuz2Gy",  # David Bowie
    "5INjqkS1o8h1imAzPqGZBb",  # Tame Impala
    "2CIMQHirSU0MQqyYHq0eOx",  # Linkin Park
    "6FBDaR13swtiWwGhX1WQsP",  # blink-182
    "0k17h0D3J5VfsdmQ1iZtE9",  # Pink Floyd
    "3fMbdgg4jU18AjLCKBhRSm",  # Michael Jackson
    "4Z8W4fKeB5YxbusRsdQVPb",  # Radiohead
    "5Pwc4xIPtQLFEnJriah9YJ",  # OneRepublic
    "3AA28KZvwAUcZuOKwyblJQ",  # Gorillaz
    "74ASZWbe4lXaubB36ztrGX",  # Bob Marley & The Wailers
    "4tZwfgrHOc3mvqYlEYSvVi",  # Daft Punk
    "1vCWHaC5f2uS3yhpwWbIA6",  # Avicii
    
    # R&B/Soul
    "00FQb4jTyendYWaN8pK0wa",  # Lana Del Rey
    "26dSoYclwsYLMAKD3tpOr4",  # Britney Spears
    "6vWDO969PvNqNYHIOW5v0m",  # Beyoncé
    "1McMsnEElThX1knmY4oliG",  # Olivia Rodrigo
    "6qqNVTkY8uBg9cP3Jd7DAH",  # Billie Eilish
    "3TVXtAsR1Inumwj472S9r4",  # Drake
    "1Xyo4u8uXC1ZmMpatF05PJ",  # The Weeknd
    "2wY79sveU1sp5g7SokKOiI",  # Sam Smith
    "4V8Sr092TqfHkfAA5fXXqG",  # Frank Ocean
    "6vXTefBL93Dj5IqAWq6OTv",  # French Montana
    
    # Latin/Global
    "4q3ewBCX7sLwd24euuV69X",  # Bad Bunny
    "0EmeFodog0BfCgMzAIvKQp",  # Shakira
    "1vyhD5VmyZ7KMfW5gqLgo5",  # J Balvin
    "790FomKkXshlbRYZFtlgla",  # Karol G
    "4VMYDCV2IEDYJArk749S6m",  # Daddy Yankee
    "5lwmRuXgjX8xIwlnauTZIP",  # Ozuna
    "0C8ZW7ezQVs4URX5aX7Kqx",  # Selena Gomez
    "4dpARuHxo51G3z768sgnrY",  # Adele
    "1l7ZsJRRS8wlW3WfJfPfNS",  # Christina Aguilera
    "6Ff53KvcvAj5U7Z1vojB5o",  # Pitbull
    
    # Electronic/Dance
    "1McMsnEElThX1knmY4oliG",  # Calvin Harris
    "1RyvyyTE3xzB2ZywiAwp0i",  # Future
    "5cj0lLjcoR7YOSnhnX0Po5",  # Dillon Francis
    "4DYFVNKZ1uixa6SQTvzQwJ",  # Roddy Ricch
    "3hv9jJF3adDNsBSIQDqcjp",  # Tiësto
    "66262794-f3e5-4456-8c11-c89bb94623ea",  # Marshmello
    "2qxJFvFYMEDqd7ui6kSAcq",  # Zara Larsson
    
    # Country
    "06HL4z0CvFAxyc27GXpf02",  # Taylor Swift
    "5K4W6rqBFWDnAN6FQUkS6x",  # Luke Bryan
    "0umv21W3hDEXPzLRkLmWvj",  # Luke Combs
    "4xRYI6VqpWRAVkx1z7KLfg",  # Morgan Wallen
    "26T3LtbuGT1Fu9m0eRq5X3",  # Carrie Underwood
    "35l9BRT7MXmM8bv2WDQiyB",  # Blake Shelton
    "4frLdHi3IRxRCBRZUDS9P6",  # Kane Brown
    
    # Classic/Legacy
    "3WrFJ7ztbogyGnTHbHJFl2",  # The Beatles
    "1dfeR4HaWDbWqFHLkxsg1d",  # Queen
    "3fMbdgg4jU18AjLCKBhRSm",  # Michael Jackson
    "6tbjWDEIzxoDsBA1FuhfPW",  # Madonna
    "22bE4uQ6baNwSHPVcDxLCe",  # The Rolling Stones
    "7dGJo4pcD2V6oG8kP0tJRR",  # Eminem
    "4MXUO7sVCaFgFjoTI5ox5c",  # Juice WRLD
    "12Chz98pHFMPJEknJQMWvI",  # Muse
    "53A0W3U0s8diEn9RhXQhVz",  # Keane
    "5INjqkS1o8h1imAzPqGZBb",  # Tame Impala
    "2yEwvVSSSUkcLeSTNyHKh8",  # WALK THE MOON
    
    # Additional Popular Artists
    "6KImCVD70vtIoJWnq6nGn3",  # Harry Styles
    "1URnnhqYAYcrqrcwql10ft",  # Post Malone
    "0hCNtLu0JehylgoiP8L4Gh",  # Nicki Minaj
    "7jy3rLJdDQY21OgRLCZ9sD",  # Foo Fighters
    "1mcTU81TzQhprhouKaTkpq",  # Troye Sivan
    "1anyVhU62p31KFi8MEzkbf",  # Chance the Rapper
    "3q7HBObVc0L8jNeTe5Gofh",  # Miley Cyrus
    "5cj0lLjcoR7YOSnhnX0Po5",  # Shawn Mendes
    "6eUKZXaKkcviH0Ku9w2n3V",  # Ed Sheeran
    "13ubrt8QOOCPljQ2FL1Kca",  # A$AP Rocky
    "7tYKF4w9nC0nq9CsPZTHyP",  # Blackpink
]

def add_artist(spotify_id):
    """Add a single artist to the database"""
    try:
        # Get artist info from Spotify
        artist = sp.artist(spotify_id)
        
        # Insert artist
        cursor.execute("""
            INSERT INTO artists (spotify_id, name, image_url) 
            VALUES (%s, %s, %s) 
            ON CONFLICT (spotify_id) DO UPDATE 
            SET name = EXCLUDED.name, image_url = EXCLUDED.image_url
        """, (
            artist['id'],
            artist['name'],
            artist['images'][0]['url'] if artist['images'] else None
        ))
        
        # Insert price history
        price = float(artist['popularity'])
        cursor.execute("""
            INSERT INTO artist_history (spotify_id, popularity, price) 
            VALUES (%s, %s, %s)
        """, (artist['id'], artist['popularity'], price))
        
        conn.commit()
        print(f"✓ Added: {artist['name']} (Popularity: {artist['popularity']})")
        return True
        
    except Exception as e:
        print(f"✗ Error adding artist {spotify_id}: {e}")
        conn.rollback()
        return False

# Main execution
print("=" * 60)
print("ANTICIP ARTIST DATABASE SEEDER")
print("=" * 60)
db_target = "Production (Railway)" if database_url and 'railway' in database_url.lower() else "Local Database"
print(f"Target: {db_target}")
print(f"Artists to add: {len(ARTIST_IDS)}")
print("=" * 60)

added = 0
failed = 0

for i, artist_id in enumerate(ARTIST_IDS, 1):
    print(f"\n[{i}/{len(ARTIST_IDS)}] Processing artist {artist_id}...")
    
    if add_artist(artist_id):
        added += 1
    else:
        failed += 1
    
    # Rate limiting: wait between requests
    if i < len(ARTIST_IDS):
        time.sleep(0.5)  # Wait 500ms between artists

print("\n" + "=" * 60)
print("SEEDING COMPLETE")
print("=" * 60)
print(f"✓ Successfully added: {added} artists")
print(f"✗ Failed: {failed} artists")
print("=" * 60)

cursor.close()
conn.close()
