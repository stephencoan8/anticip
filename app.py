from flask import Flask
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
import os
import psycopg2

app = Flask(__name__)

# Load environment variables
load_dotenv()
client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

# Set up Spotipy
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))

# Connect to PostgreSQL
conn = psycopg2.connect(dbname="antici_db", user="stephencoan", password="", host="localhost")
cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS artists (
        id SERIAL PRIMARY KEY,
        spotify_id VARCHAR(255),
        name VARCHAR(255),
        listeners INTEGER
    )
""")
conn.commit()

@app.route('/')
def home():
    # Example: Get artist data for The Beatles
    artist = sp.artist("3WrFJ7ztbogyGnTHbHJFl2")
    # Insert into database
    cursor.execute("INSERT INTO artists (spotify_id, name, listeners) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                  (artist['id'], artist['name'], artist['followers']['total']))
    conn.commit()
    return f"Artist: {artist['name']}, Monthly Listeners: {artist['followers']['total']}"

if __name__ == '__main__':
    app.run(debug=True, port=5001)