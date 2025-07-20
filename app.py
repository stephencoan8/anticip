from flask import Flask
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
import os
import psycopg2
from psycopg2 import pool

app = Flask(__name__)

# Load environment variables
load_dotenv()
client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

# Set up Spotipy
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))

# Set up PostgreSQL connection pool
db_pool = psycopg2.pool.SimpleConnectionPool(1, 20, dbname="antici_db", user="stephencoan", password="", host="localhost")

# Ensure tables exist
conn = db_pool.getconn()
try:
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS artists (
            id SERIAL PRIMARY KEY,
            spotify_id VARCHAR(255) UNIQUE,
            name VARCHAR(255)
        );
        CREATE TABLE IF NOT EXISTS artist_history (
            id SERIAL PRIMARY KEY,
            spotify_id VARCHAR(255),
            popularity INTEGER,
            price NUMERIC(10, 2),
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
except Exception as e:
    print(f"Error creating tables: {e}")
    conn.rollback()
finally:
    cursor.close()
    db_pool.putconn(conn)

@app.route('/')
def home():
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        # Get artist data for The Beatles
        artist = sp.artist("3WrFJ7ztbogyGnTHbHJFl2")
        # Insert or update artist
        cursor.execute("INSERT INTO artists (spotify_id, name) VALUES (%s, %s) ON CONFLICT (spotify_id) DO UPDATE SET name = EXCLUDED.name",
                    (artist['id'], artist['name']))
        # Insert popularity and price
        price = artist['popularity']  # Use popularity as price
        cursor.execute("INSERT INTO artist_history (spotify_id, popularity, price) VALUES (%s, %s, %s)",
                    (artist['id'], artist['popularity'], price))
        conn.commit()
        return f"Artist: {artist['name']}, Popularity: {artist['popularity']}, Stock Price: ${price:.2f}"
    except Exception as e:
        conn.rollback()
        return f"Database error: {str(e)}", 500
    finally:
        cursor.close()
        db_pool.putconn(conn)

@app.route('/artists')
def list_artists():
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT a.name, ah.popularity, ah.price, ah.recorded_at FROM artist_history ah JOIN artists a ON ah.spotify_id = a.spotify_id ORDER BY ah.recorded_at DESC")
        records = cursor.fetchall()
        return '<br>'.join([f"{name}: Popularity {popularity}, ${price:.2f} at {recorded_at}" for name, popularity, price, recorded_at in records])
    except Exception as e:
        conn.rollback()
        return f"Database error: {str(e)}", 500
    finally:
        cursor.close()
        db_pool.putconn(conn)

if __name__ == '__main__':
    app.run(debug=True, port=5001)