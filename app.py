from flask import Flask
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
import os

app = Flask(__name__)

# Load environment variables
load_dotenv()
client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

# Set up Spotipy
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))

@app.route('/')
def home():
    # Example: Get artist data for The Beatles
    artist = sp.artist("3WrFJ7ztbogyGnTHbHJFl2")
    return f"Artist: {artist['name']}, Monthly Listeners: {artist['followers']['total']}"

if __name__ == '__main__':
    app.run(debug=True, port=5001)