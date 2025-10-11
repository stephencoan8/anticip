from flask import Flask, render_template, request, redirect, url_for, session
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
import os
import psycopg2
from psycopg2 import pool
import bcrypt
import json

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Load environment variables
load_dotenv()
client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

# Set up Spotipy
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret))

# Set up PostgreSQL connection pool
db_pool = psycopg2.pool.SimpleConnectionPool(1, 20, dbname="anticip_db", user="stephencoan", password="", host="localhost")

# Ensure tables exist
conn = db_pool.getconn()
try:
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS artists (
            id SERIAL PRIMARY KEY,
            spotify_id VARCHAR(255) UNIQUE,
            name VARCHAR(255),
            image_url VARCHAR(255)
        );
        CREATE TABLE IF NOT EXISTS artist_history (
            id SERIAL PRIMARY KEY,
            spotify_id VARCHAR(255),
            popularity INTEGER,
            price NUMERIC(10, 2),
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(255) UNIQUE,
            password VARCHAR(255) NOT NULL,
            balance NUMERIC(12, 2) DEFAULT 10000.00
        );
        CREATE TABLE IF NOT EXISTS bets (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            artist_id INTEGER REFERENCES artists(id),
            shares INTEGER NOT NULL,
            avg_price NUMERIC(10, 2) NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS follows (
            id SERIAL PRIMARY KEY,
            follower_id INTEGER REFERENCES users(id),
            followed_id INTEGER REFERENCES users(id),
            status VARCHAR(10) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT unique_follow UNIQUE(follower_id, followed_id)
        );
        CREATE TABLE IF NOT EXISTS spotify_data (
            id SERIAL PRIMARY KEY,
            spotify_id VARCHAR(255) UNIQUE,
            followers INTEGER DEFAULT 0,
            popularity INTEGER DEFAULT 0,
            genres TEXT[] DEFAULT '{}',
            top_tracks JSONB DEFAULT '[]',
            recent_albums JSONB DEFAULT '[]',
            external_urls JSONB DEFAULT '{}',
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS transactions (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            artist_id INTEGER REFERENCES artists(id),
            transaction_type VARCHAR(4) CHECK (transaction_type IN ('buy', 'sell')),
            shares INTEGER NOT NULL,
            price_per_share NUMERIC(10, 2) NOT NULL,
            total_amount NUMERIC(12, 2) NOT NULL,
            caption TEXT,
            privacy VARCHAR(10) DEFAULT 'public' CHECK (privacy IN ('public', 'followers', 'private')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS transaction_likes (
            id SERIAL PRIMARY KEY,
            transaction_id INTEGER REFERENCES transactions(id) ON DELETE CASCADE,
            user_id INTEGER REFERENCES users(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT unique_transaction_like UNIQUE(transaction_id, user_id)
        );
        CREATE TABLE IF NOT EXISTS transaction_comments (
            id SERIAL PRIMARY KEY,
            transaction_id INTEGER REFERENCES transactions(id) ON DELETE CASCADE,
            user_id INTEGER REFERENCES users(id),
            comment TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS portfolio_history (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            total_points NUMERIC(12, 2),
            points_invested NUMERIC(12, 2),
            points_reserve NUMERIC(12, 2),
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
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        artist = sp.artist("3WrFJ7ztbogyGnTHbHJFl2")
        cursor.execute("INSERT INTO artists (spotify_id, name, image_url) VALUES (%s, %s, %s) ON CONFLICT (spotify_id) DO UPDATE SET name = EXCLUDED.name, image_url = EXCLUDED.image_url",
                    (artist['id'], artist['name'], artist['images'][0]['url'] if artist['images'] else None))
        price = artist['popularity']
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
    if 'user_id' not in session:
        return redirect(url_for('login'))
    search_query = request.args.get('search', '').lower()
    order = request.args.get('order', 'alphabetical')
    direction = request.args.get('direction', 'asc')
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        # Get only the latest price for each artist
        query = """
            SELECT a.spotify_id, a.name, ah.popularity, ah.price, ah.recorded_at, a.image_url
            FROM artists a
            JOIN LATERAL (
                SELECT * FROM artist_history ah2
                WHERE ah2.spotify_id = a.spotify_id
                ORDER BY ah2.recorded_at DESC
                LIMIT 1
            ) ah ON true
            WHERE a.name ILIKE %s
        """
        cursor.execute(query, (f'%{search_query}%',))
        records = cursor.fetchall()
        # Sort records based on order and direction
        reverse = direction == 'desc'
        if order == 'alphabetical':
            records.sort(key=lambda x: x[1], reverse=reverse)  # x[1] is name
        elif order == 'popularity':
            records.sort(key=lambda x: x[2], reverse=reverse)  # x[2] is popularity
        return render_template('artists.html', records=records, search_query=search_query, order=order, direction=direction)
    except Exception as e:
        conn.rollback()
        return f"Database error: {str(e)}", 500
    finally:
        cursor.close()
        db_pool.putconn(conn)

# New route for artist detail view
@app.route('/artist/<spotify_id>')
def artist_detail(spotify_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    order = request.args.get('order', 'alphabetical_asc')
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        # Get artist info
        cursor.execute("SELECT id, name, image_url FROM artists WHERE spotify_id = %s", (spotify_id,))
        artist_row = cursor.fetchone()
        if not artist_row:
            return "Artist not found", 404
        artist_id, name, image_url = artist_row
        
        # Fetch additional Spotify data from local storage
        try:
            cursor.execute("SELECT followers, popularity, genres, top_tracks, recent_albums, external_urls FROM spotify_data WHERE spotify_id = %s", (spotify_id,))
            spotify_row = cursor.fetchone()
            if spotify_row:
                spotify_info = {
                    'followers': spotify_row[0] or 0,
                    'popularity': spotify_row[1] or 0,
                    'genres': spotify_row[2] or [],
                    'external_urls': spotify_row[5] if spotify_row[5] else {},  # JSONB already parsed by psycopg2
                    'top_tracks': spotify_row[3] if spotify_row[3] else [],     # JSONB already parsed by psycopg2
                    'recent_albums': spotify_row[4] if spotify_row[4] else []   # JSONB already parsed by psycopg2
                }
            else:
                spotify_info = {
                    'followers': 0,
                    'popularity': 0,
                    'genres': [],
                    'external_urls': {},
                    'top_tracks': [],
                    'recent_albums': []
                }
        except Exception as e:
            print(f"Error fetching local Spotify data: {e}")
            spotify_info = {
                'followers': 0,
                'popularity': 0,
                'genres': [],
                'external_urls': {},
                'top_tracks': [],
                'recent_albums': []
            }
        
        # Get historical prices
        cursor.execute("SELECT recorded_at, price FROM artist_history WHERE spotify_id = %s ORDER BY recorded_at ASC", (spotify_id,))
        history = cursor.fetchall()
        # Get user holdings
        cursor.execute("SELECT shares, avg_price FROM bets WHERE user_id = %s AND artist_id = %s", (user_id, artist_id))
        holdings = cursor.fetchone()
        if holdings:
            shares = int(holdings[0])
            avg_price = float(holdings[1])
            holdings = (shares, avg_price)
        # Get current price
        cursor.execute("SELECT price FROM artist_history WHERE spotify_id = %s ORDER BY recorded_at DESC LIMIT 1", (spotify_id,))
        price_row = cursor.fetchone()
        current_price = float(price_row[0]) if price_row else None
        # For artist detail, just pass order to template for dropdown (no sorting needed)
        return render_template('artist_detail.html', 
                             artist=(name, image_url), 
                             history=history, 
                             holdings=holdings, 
                             current_price=current_price, 
                             order=order,
                             spotify_info=spotify_info)
    except Exception as e:
        conn.rollback()
        return f"Database error: {str(e)}", 500
    finally:
        cursor.close()
        db_pool.putconn(conn)

@app.route('/add_artist', methods=['GET', 'POST'])
def add_artist():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        artist_name = request.form['artist_name']
        try:
            results = sp.search(q=artist_name, type='artist', limit=5)
            artists = results['artists']['items']
            return render_template('add_artist.html', artists=artists, search_query=artist_name)
        except Exception as e:
            return render_template('add_artist.html', error=str(e))
    # If GET, just show the form
    return render_template('add_artist.html')

@app.route('/confirm_add_artist', methods=['POST'])
def confirm_add_artist():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    spotify_id = request.form['spotify_id']
    name = request.form['name']
    image_url = request.form.get('image_url')
    try:
        conn = db_pool.getconn()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO artists (spotify_id, name, image_url) VALUES (%s, %s, %s) ON CONFLICT (spotify_id) DO UPDATE SET name = EXCLUDED.name, image_url = EXCLUDED.image_url", (spotify_id, name, image_url))
        # Fetch popularity for initial price
        artist = sp.artist(spotify_id)
        price = artist['popularity']
        cursor.execute("INSERT INTO artist_history (spotify_id, popularity, price) VALUES (%s, %s, %s)", (spotify_id, artist['popularity'], price))
        conn.commit()
        return redirect(url_for('list_artists'))
    except Exception as e:
        conn.rollback()
        return render_template('add_artist.html', error=str(e))
    finally:
        cursor.close()
        db_pool.putconn(conn)

@app.route('/delete_artist/<spotify_id>', methods=['POST'])
def delete_artist(spotify_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Check if user is admin
    if not session.get('is_admin', False):
        return "Access denied. Admin privileges required.", 403
    
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        
        # First check if artist exists
        cursor.execute("SELECT id, name FROM artists WHERE spotify_id = %s", (spotify_id,))
        artist = cursor.fetchone()
        if not artist:
            return "Artist not found", 404
        
        artist_id, artist_name = artist
        
        # Delete in correct order due to foreign key constraints
        # 1. Delete transaction likes and comments first
        cursor.execute("""
            DELETE FROM transaction_likes 
            WHERE transaction_id IN (
                SELECT id FROM transactions WHERE artist_id = %s
            )
        """, (artist_id,))
        
        cursor.execute("""
            DELETE FROM transaction_comments 
            WHERE transaction_id IN (
                SELECT id FROM transactions WHERE artist_id = %s
            )
        """, (artist_id,))
        
        # 2. Delete transactions
        cursor.execute("DELETE FROM transactions WHERE artist_id = %s", (artist_id,))
        
        # 3. Delete user bets
        cursor.execute("DELETE FROM bets WHERE artist_id = %s", (artist_id,))
        
        # 4. Delete price history
        cursor.execute("DELETE FROM artist_history WHERE spotify_id = %s", (spotify_id,))
        
        # 5. Finally delete the artist
        cursor.execute("DELETE FROM artists WHERE spotify_id = %s", (spotify_id,))
        
        conn.commit()
        return redirect(url_for('list_artists'))
        
    except Exception as e:
        conn.rollback()
        return f"Error deleting artist: {str(e)}", 500
    finally:
        cursor.close()
        db_pool.putconn(conn)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].lower()
        password = request.form['password'].encode('utf-8')
        conn = db_pool.getconn()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, password, username, is_admin FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            if user and bcrypt.checkpw(password, user[1].encode('utf-8')):
                session['user_id'] = user[0]
                session['username'] = user[2]
                session['is_admin'] = user[3] if user[3] is not None else False
                return redirect(url_for('list_artists'))  # Changed from 'artists' to 'list_artists'
            else:
                return render_template('login.html', error="Invalid username or password")
        except Exception as e:
            conn.rollback()
            return render_template('login.html', error=str(e))
        finally:
            cursor.close()
            db_pool.putconn(conn)
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].lower()
        password = request.form['password'].encode('utf-8')
        hashed = bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')
        conn = db_pool.getconn()
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (username, password, balance) VALUES (%s, %s, %s) RETURNING id", (username, hashed, 10000.00))
            user_id = cursor.fetchone()[0]
            conn.commit()
            session['user_id'] = user_id
            session['username'] = username
            session['is_admin'] = False  # New users are not admin by default
            return redirect(url_for('list_artists'))  # Changed from 'artists' to 'list_artists'
        except Exception as e:
            conn.rollback()
            return render_template('register.html', error=str(e))
        finally:
            cursor.close()
            db_pool.putconn(conn)
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('is_admin', None)
    return redirect(url_for('login'))

@app.route('/refresh_data', methods=['POST'])
def refresh_data():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT spotify_id FROM artists")
        artist_ids = [row[0] for row in cursor.fetchall()]
        
        updated_count = 0
        for spotify_id in artist_ids:
            try:
                # Get artist details from Spotify
                artist_data = sp.artist(spotify_id)
                
                # Get top tracks from Spotify
                top_tracks = sp.artist_top_tracks(spotify_id, country='US')
                
                # Get artist albums
                albums = sp.artist_albums(spotify_id, album_type='album', limit=5)
                
                # Update price history (keep this as before)
                price = artist_data['popularity']
                cursor.execute("INSERT INTO artist_history (spotify_id, popularity, price) VALUES (%s, %s, %s)",
                               (spotify_id, artist_data['popularity'], price))
                
                # Update/insert spotify data
                cursor.execute("""
                    INSERT INTO spotify_data (spotify_id, followers, popularity, genres, top_tracks, recent_albums, external_urls, last_updated)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (spotify_id) DO UPDATE SET
                        followers = EXCLUDED.followers,
                        popularity = EXCLUDED.popularity,
                        genres = EXCLUDED.genres,
                        top_tracks = EXCLUDED.top_tracks,
                        recent_albums = EXCLUDED.recent_albums,
                        external_urls = EXCLUDED.external_urls,
                        last_updated = NOW()
                """, (
                    spotify_id,
                    artist_data.get('followers', {}).get('total', 0),
                    artist_data.get('popularity', 0),
                    artist_data.get('genres', []),
                    json.dumps(top_tracks.get('tracks', [])[:10]),  # Convert to JSON string
                    json.dumps(albums.get('items', [])[:5]),  # Convert to JSON string
                    json.dumps(artist_data.get('external_urls', {}))  # Convert to JSON string
                ))
                
                updated_count += 1
                
            except Exception as e:
                print(f"Error refreshing {spotify_id}: {e}")
        
        conn.commit()
        print(f"Successfully updated {updated_count} artists")
        
        # Record portfolio history for all users after data refresh
        record_portfolio_history()
        
    except Exception as e:
        conn.rollback()
        return f"Database error: {str(e)}", 500
    finally:
        cursor.close()
        db_pool.putconn(conn)
    return redirect(url_for('list_artists'))

@app.route('/buy/<spotify_id>', methods=['POST'])
def buy_artist(spotify_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    shares = int(request.form.get('shares', 0))
    caption = request.form.get('caption', '').strip()
    privacy = request.form.get('privacy', 'public')
    
    if shares <= 0:
        return "Invalid share amount", 400
    if privacy not in ['public', 'followers', 'private']:
        privacy = 'public'
        
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM artists WHERE spotify_id = %s", (spotify_id,))
        artist_row = cursor.fetchone()
        if not artist_row:
            return "Artist not found", 404
        artist_id = artist_row[0]
        
        cursor.execute("SELECT price FROM artist_history WHERE spotify_id = %s ORDER BY recorded_at DESC LIMIT 1", (spotify_id,))
        price_row = cursor.fetchone()
        if not price_row:
            return "No price data", 400
        price = float(price_row[0])
        total_cost = shares * price
        
        # Check user balance
        cursor.execute("SELECT balance FROM users WHERE id = %s", (user_id,))
        balance_row = cursor.fetchone()
        balance = float(balance_row[0]) if balance_row else 0.0
        if balance < total_cost:
            return "Insufficient funds", 400
            
        # Deduct balance
        cursor.execute("UPDATE users SET balance = balance - %s WHERE id = %s", (total_cost, user_id))
        
        # Check if user already owns shares
        cursor.execute("SELECT id, shares, avg_price FROM bets WHERE user_id = %s AND artist_id = %s", (user_id, artist_id))
        bet = cursor.fetchone()
        if bet:
            bet_id, current_shares, current_avg = bet
            total_shares = current_shares + shares
            new_avg = ((current_shares * current_avg) + (shares * price)) / total_shares
            cursor.execute("UPDATE bets SET shares = %s, avg_price = %s, timestamp = NOW() WHERE id = %s", (total_shares, new_avg, bet_id))
        else:
            cursor.execute("INSERT INTO bets (user_id, artist_id, shares, avg_price) VALUES (%s, %s, %s, %s)", (user_id, artist_id, shares, price))
        
        # Record the transaction
        cursor.execute("""
            INSERT INTO transactions (user_id, artist_id, transaction_type, shares, price_per_share, total_value, caption, visibility)
            VALUES (%s, %s, 'buy', %s, %s, %s, %s, %s)
        """, (user_id, artist_id, shares, price, total_cost, caption, privacy))
        
        conn.commit()
        return redirect(url_for('artist_detail', spotify_id=spotify_id))
    except Exception as e:
        conn.rollback()
        return f"Database error: {str(e)}", 500
    finally:
        cursor.close()
        db_pool.putconn(conn)

@app.route('/sell/<spotify_id>', methods=['POST'])
def sell_artist(spotify_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    shares = int(request.form.get('shares', 0))
    caption = request.form.get('caption', '').strip()
    privacy = request.form.get('privacy', 'public')
    
    if shares <= 0:
        return "Invalid share amount", 400
    if privacy not in ['public', 'followers', 'private']:
        privacy = 'public'
        
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM artists WHERE spotify_id = %s", (spotify_id,))
        artist_row = cursor.fetchone()
        if not artist_row:
            return "Artist not found", 404
        artist_id = artist_row[0]
        cursor.execute("SELECT price FROM artist_history WHERE spotify_id = %s ORDER BY recorded_at DESC LIMIT 1", (spotify_id,))
        price_row = cursor.fetchone()
        price = float(price_row[0]) if price_row else 0.0
        total_value = shares * price
        cursor.execute("SELECT id, shares, avg_price FROM bets WHERE user_id = %s AND artist_id = %s", (user_id, artist_id))
        bet = cursor.fetchone()
        if not bet or bet[1] < shares:
            return "Not enough shares to sell", 400
        bet_id, current_shares, avg_price = bet
        new_shares = current_shares - shares
        if new_shares > 0:
            cursor.execute("UPDATE bets SET shares = %s, timestamp = NOW() WHERE id = %s", (new_shares, bet_id))
        else:
            cursor.execute("DELETE FROM bets WHERE id = %s", (bet_id,))
        # Add balance
        cursor.execute("UPDATE users SET balance = balance + %s WHERE id = %s", (total_value, user_id))
        
        # Record the transaction
        cursor.execute("""
            INSERT INTO transactions (user_id, artist_id, transaction_type, shares, price_per_share, total_value, caption, visibility)
            VALUES (%s, %s, 'sell', %s, %s, %s, %s, %s)
        """, (user_id, artist_id, shares, price, total_value, caption, privacy))
        
        conn.commit()
        return redirect(url_for('artist_detail', spotify_id=spotify_id))
    except Exception as e:
        conn.rollback()
        return f"Database error: {str(e)}", 500
    finally:
        cursor.close()
        db_pool.putconn(conn)

@app.route('/portfolio')
@app.route('/user/<int:user_id>/portfolio')
def portfolio(user_id=None):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Determine if viewing own portfolio or someone else's
    if user_id is None:
        user_id = session['user_id']
        is_own_portfolio = True
    else:
        is_own_portfolio = (user_id == session['user_id'])
    
    order = request.args.get('order', 'alphabetical')
    direction = request.args.get('direction', 'asc')
    view = request.args.get('view', 'tile')
    
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        
        # Get the user's username and basic info
        cursor.execute("SELECT username FROM users WHERE id = %s", (user_id,))
        user_result = cursor.fetchone()
        if not user_result:
            return "User not found", 404
        username = user_result[0]
        # Get user's balance
        cursor.execute("SELECT balance FROM users WHERE id = %s", (user_id,))
        balance_result = cursor.fetchone()
        if not balance_result or balance_result[0] is None:
            return "User balance not found", 404
        actual_balance = float(balance_result[0])
        
        # For display purposes, only show balance for own portfolio
        balance = actual_balance if is_own_portfolio else 0.0
        
        # Get all user's holdings with current prices
        cursor.execute("""
            WITH latest_prices AS (
                SELECT DISTINCT ON (spotify_id) spotify_id, price
                FROM artist_history
                ORDER BY spotify_id, recorded_at DESC
            )
            SELECT 
                a.name,
                b.shares,
                b.avg_price,
                lp.price as current_price,
                a.spotify_id
            FROM bets b
            JOIN artists a ON b.artist_id = a.id
            JOIN latest_prices lp ON a.spotify_id = lp.spotify_id
            WHERE b.user_id = %s
        """, (user_id,))
        
        raw_holdings = cursor.fetchall()
        
        # Process holdings data into objects for template
        holdings = []
        total_invested = 0
        current_value = 0
        
        if raw_holdings:
            for h in raw_holdings:
                name = h[0]
                shares = float(h[1]) if h[1] is not None else 0
                avg_price = float(h[2]) if h[2] is not None else 0
                current_price = float(h[3]) if h[3] is not None else 0
                spotify_id = h[4]
                
                # Calculate values for this holding
                value = shares * current_price
                cost = shares * avg_price
                gain = value - cost
                percent_gain = ((gain / cost) * 100) if cost > 0 else 0
                
                # Get image URL for this artist
                cursor.execute("SELECT image_url FROM artists WHERE spotify_id = %s", (spotify_id,))
                image_result = cursor.fetchone()
                image_url = image_result[0] if image_result else None
                
                # Get local Spotify data
                cursor.execute("SELECT followers, popularity, genres, top_tracks FROM spotify_data WHERE spotify_id = %s", (spotify_id,))
                spotify_row = cursor.fetchone()
                if spotify_row:
                    # JSONB fields are already parsed by psycopg2, no need for json.loads()
                    top_tracks_data = spotify_row[3] if spotify_row[3] else []
                    spotify_info = {
                        'followers': spotify_row[0] or 0,
                        'popularity': spotify_row[1] or 0,
                        'genres': spotify_row[2] or [],  # TEXT[] array is already a list
                        'top_tracks': top_tracks_data[:3]  # Top 3 for portfolio
                    }
                else:
                    spotify_info = {
                        'followers': 0,
                        'popularity': 0,
                        'genres': [],
                        'top_tracks': []
                    }
                
                # Create holding object
                holding = {
                    'name': name,
                    'shares': shares,
                    'avg_price': avg_price,
                    'current_price': current_price,
                    'value': value,
                    'gain': gain,
                    'percent_gain': percent_gain,
                    'spotify_id': spotify_id,
                    'image_url': image_url,
                    'spotify_info': spotify_info
                }
                holdings.append(holding)
                
                # Add to totals
                total_invested += cost
                current_value += value
            
            # Apply sorting
            if order == 'alphabetical':
                holdings.sort(key=lambda x: x['name'].lower(), reverse=(direction == 'desc'))
            elif order == 'popularity':
                # For now, sort by name as we don't have popularity in this query
                holdings.sort(key=lambda x: x['name'].lower(), reverse=(direction == 'desc'))
            elif order == 'net_holdings':
                holdings.sort(key=lambda x: x['value'], reverse=(direction == 'desc'))
            elif order == 'gain':
                holdings.sort(key=lambda x: x['gain'], reverse=(direction == 'desc'))
            elif order == 'percent_gain':
                holdings.sort(key=lambda x: x['percent_gain'], reverse=(direction == 'desc'))
            
            gain = current_value - total_invested
            net_worth = actual_balance + current_value  # Always calculate total net worth
            
            # Calculate percent of holdings that are profitable
            profitable_holdings = sum(1 for h in holdings if h['gain'] > 0)
            percent_winning = (profitable_holdings / len(holdings) * 100)
        else:
            total_invested = 0.0
            current_value = 0.0
            gain = 0.0
            net_worth = actual_balance  # Always include balance in total
            percent_winning = 0.0
        
        return render_template('portfolio.html',
                            holdings=holdings,
                            balance=balance,
                            total_invested=total_invested,
                            gain=gain,
                            net_worth=net_worth,
                            percent_winning=percent_winning,
                            order=order,
                            direction=direction,
                            view=view,
                            username=username,
                            is_own_portfolio=is_own_portfolio)
    except Exception as e:
        return f"Database error: {str(e)}", 500
    finally:
        cursor.close()
        db_pool.putconn(conn)

# Social Features Routes
@app.route('/all_users')
def all_users():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        # Get all users except current user, with their follow status
        cursor.execute("""
            SELECT u.id, u.username,
                CASE
                    WHEN f.status IS NULL THEN 'none'
                    WHEN f.status = 'pending' THEN 'pending'
                    WHEN f.status = 'accepted' THEN 'following'
                END as follow_status
            FROM users u
            LEFT JOIN follows f ON f.followed_id = u.id AND f.follower_id = %s
            WHERE u.id != %s
            ORDER BY u.username
        """, (session['user_id'], session['user_id']))
        users = [{'id': id, 'username': username, 'follow_status': status} 
                for id, username, status in cursor.fetchall()]
        return render_template('all_users.html', users=users)
    except Exception as e:
        return f"Database error: {str(e)}", 500
    finally:
        cursor.close()
        db_pool.putconn(conn)

@app.route('/followers')
def followers():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        # Get all accepted followers
        cursor.execute("""
            SELECT u.id, u.username 
            FROM follows f 
            JOIN users u ON f.follower_id = u.id 
            WHERE f.followed_id = %s AND f.status = 'accepted'
            ORDER BY u.username
        """, (session['user_id'],))
        followers = cursor.fetchall()
        return render_template('followers.html', followers=followers)
    except Exception as e:
        return f"Database error: {str(e)}", 500
    finally:
        cursor.close()
        db_pool.putconn(conn)

@app.route('/following')
def following():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        # Get all users that the current user follows
        cursor.execute("""
            SELECT u.id, u.username 
            FROM follows f 
            JOIN users u ON f.followed_id = u.id 
            WHERE f.follower_id = %s AND f.status = 'accepted'
            ORDER BY u.username
        """, (session['user_id'],))
        following = cursor.fetchall()
        return render_template('following.html', following=following)
    except Exception as e:
        return f"Database error: {str(e)}", 500
    finally:
        cursor.close()
        db_pool.putconn(conn)

@app.route('/search_users')
def search_users():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    query = request.args.get('query', '').strip()
    if not query:
        return render_template('search_users.html')
    
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        # Search for users and get their follow status
        cursor.execute("""
            SELECT u.id, u.username,
                CASE
                    WHEN f.status IS NULL THEN 'none'
                    WHEN f.status = 'pending' THEN 'pending'
                    WHEN f.status = 'accepted' THEN 'following'
                END as follow_status
            FROM users u
            LEFT JOIN follows f ON f.followed_id = u.id AND f.follower_id = %s
            WHERE u.id != %s AND u.username ILIKE %s
            ORDER BY u.username
        """, (session['user_id'], session['user_id'], f'%{query}%'))
        users = [{'id': id, 'username': username, 'follow_status': status} 
                for id, username, status in cursor.fetchall()]
        return render_template('search_users.html', users=users, query=query)
    except Exception as e:
        return f"Database error: {str(e)}", 500
    finally:
        cursor.close()
        db_pool.putconn(conn)

@app.route('/pending_requests')
def pending_requests():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        # Get all pending follow requests
        cursor.execute("""
            SELECT f.id, u.id as follower_id, u.username
            FROM follows f
            JOIN users u ON f.follower_id = u.id
            WHERE f.followed_id = %s AND f.status = 'pending'
            ORDER BY f.created_at DESC
        """, (session['user_id'],))
        requests = [{'id': req_id, 'follower': {'id': user_id, 'username': username}}
                   for req_id, user_id, username in cursor.fetchall()]
        return render_template('pending_requests.html', requests=requests)
    except Exception as e:
        return f"Database error: {str(e)}", 500
    finally:
        cursor.close()
        db_pool.putconn(conn)

@app.route('/follow/<int:followed_id>', methods=['POST'])
def follow_user(followed_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if followed_id == session['user_id']:
        return "Cannot follow yourself", 400
    
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        # Create follow request
        cursor.execute("""
            INSERT INTO follows (follower_id, followed_id, status)
            VALUES (%s, %s, 'pending')
            ON CONFLICT (follower_id, followed_id) DO NOTHING
        """, (session['user_id'], followed_id))
        conn.commit()
        return redirect(url_for('search_users'))
    except Exception as e:
        conn.rollback()
        return f"Database error: {str(e)}", 500
    finally:
        cursor.close()
        db_pool.putconn(conn)

@app.route('/follow_response/<int:follow_id>', methods=['POST'])
def follow_response(follow_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    action = request.form.get('action')
    if action not in ['accept', 'reject']:
        return "Invalid action", 400
    
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        if action == 'accept':
            cursor.execute("""
                UPDATE follows 
                SET status = 'accepted' 
                WHERE id = %s AND followed_id = %s
            """, (follow_id, session['user_id']))
        else:  # reject
            cursor.execute("""
                DELETE FROM follows 
                WHERE id = %s AND followed_id = %s
            """, (follow_id, session['user_id']))
        conn.commit()
        return redirect(url_for('pending_requests'))
    except Exception as e:
        conn.rollback()
        return f"Database error: {str(e)}", 500
    finally:
        cursor.close()
        db_pool.putconn(conn)

@app.route('/unfollow/<int:followed_id>', methods=['POST'])
def unfollow_user(followed_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            DELETE FROM follows 
            WHERE follower_id = %s AND followed_id = %s
        """, (session['user_id'], followed_id))
        conn.commit()
        return redirect(url_for('following'))
    except Exception as e:
        conn.rollback()
        return f"Database error: {str(e)}", 500
    finally:
        cursor.close()
        db_pool.putconn(conn)

@app.route('/settings')
def settings():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Get user's creation date (if column exists)
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        # Try to get created_at, but handle case where column doesn't exist
        try:
            cursor.execute("SELECT created_at FROM users WHERE id = %s", (session['user_id'],))
            result = cursor.fetchone()
            member_since = result[0] if result else None
        except:
            # If created_at column doesn't exist, set as None
            member_since = None
        
        return render_template('settings.html', member_since=member_since)
    except Exception as e:
        return f"Database error: {str(e)}", 500
    finally:
        cursor.close()
        db_pool.putconn(conn)

@app.route('/feed')
def feed():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    view_mode = request.args.get('view', 'followers')  # followers, public, self
    
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        
        if view_mode == 'public':
            # Show all public transactions
            cursor.execute("""
                SELECT t.id, t.transaction_type, t.shares, t.price_per_share, t.total_value, 
                       t.caption, t.created_at, u.username, a.name, a.image_url, a.spotify_id,
                       COUNT(tl.id) as like_count,
                       COUNT(tc.id) as comment_count,
                       COUNT(CASE WHEN tl.user_id = %s THEN 1 END) as user_liked,
                       t.visibility,
                       COUNT(CASE WHEN tc.user_id = %s THEN 1 END) as user_commented
                FROM transactions t
                JOIN users u ON t.user_id = u.id
                JOIN artists a ON t.artist_id = a.id
                LEFT JOIN transaction_likes tl ON t.id = tl.transaction_id
                LEFT JOIN transaction_comments tc ON t.id = tc.transaction_id
                WHERE t.visibility = 'public'
                GROUP BY t.id, t.transaction_type, t.shares, t.price_per_share, t.total_value, 
                         t.caption, t.created_at, u.username, a.name, a.image_url, a.spotify_id, t.visibility
                ORDER BY t.created_at DESC
                LIMIT 50
            """, (user_id, user_id))
        elif view_mode == 'self':
            # Show only current user's transactions
            cursor.execute("""
                SELECT t.id, t.transaction_type, t.shares, t.price_per_share, t.total_value, 
                       t.caption, t.created_at, u.username, a.name, a.image_url, a.spotify_id,
                       COUNT(tl.id) as like_count,
                       COUNT(tc.id) as comment_count,
                       COUNT(CASE WHEN tl.user_id = %s THEN 1 END) as user_liked,
                       t.visibility,
                       COUNT(CASE WHEN tc.user_id = %s THEN 1 END) as user_commented
                FROM transactions t
                JOIN users u ON t.user_id = u.id
                JOIN artists a ON t.artist_id = a.id
                LEFT JOIN transaction_likes tl ON t.id = tl.transaction_id
                LEFT JOIN transaction_comments tc ON t.id = tc.transaction_id
                WHERE t.user_id = %s
                GROUP BY t.id, t.transaction_type, t.shares, t.price_per_share, t.total_value, 
                         t.caption, t.created_at, u.username, a.name, a.image_url, a.spotify_id, t.visibility
                ORDER BY t.created_at DESC
                LIMIT 50
            """, (user_id, user_id, user_id))
        else:  # followers
            # Show transactions from users the current user follows + their own
            cursor.execute("""
                SELECT t.id, t.transaction_type, t.shares, t.price_per_share, t.total_value, 
                       t.caption, t.created_at, u.username, a.name, a.image_url, a.spotify_id,
                       COUNT(tl.id) as like_count,
                       COUNT(tc.id) as comment_count,
                       COUNT(CASE WHEN tl.user_id = %s THEN 1 END) as user_liked,
                       t.visibility,
                       COUNT(CASE WHEN tc.user_id = %s THEN 1 END) as user_commented
                FROM transactions t
                JOIN users u ON t.user_id = u.id
                JOIN artists a ON t.artist_id = a.id
                LEFT JOIN transaction_likes tl ON t.id = tl.transaction_id
                LEFT JOIN transaction_comments tc ON t.id = tc.transaction_id
                WHERE (t.user_id = %s OR 
                       t.user_id IN (
                           SELECT followed_id FROM follows 
                           WHERE follower_id = %s AND status = 'accepted'
                       ))
                  AND (t.visibility = 'public' OR 
                       (t.visibility = 'followers' AND (t.user_id = %s OR t.user_id IN (
                           SELECT followed_id FROM follows 
                           WHERE follower_id = %s AND status = 'accepted'
                       ))))
                GROUP BY t.id, t.transaction_type, t.shares, t.price_per_share, t.total_value, 
                         t.caption, t.created_at, u.username, a.name, a.image_url, a.spotify_id, t.visibility
                ORDER BY t.created_at DESC
                LIMIT 50
            """, (user_id, user_id, user_id, user_id, user_id, user_id))
        
        transactions = cursor.fetchall()
        
        return render_template('feed.html', transactions=transactions, view_mode=view_mode)
    except Exception as e:
        return f"Database error: {str(e)}", 500
    finally:
        cursor.close()
        db_pool.putconn(conn)

@app.route('/like_transaction/<int:transaction_id>', methods=['POST'])
def like_transaction(transaction_id):
    if 'user_id' not in session:
        return {'success': False, 'error': 'Not logged in'}, 401
    
    user_id = session['user_id']
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        
        # Check if user already liked this transaction
        cursor.execute("SELECT id FROM transaction_likes WHERE transaction_id = %s AND user_id = %s", 
                      (transaction_id, user_id))
        existing_like = cursor.fetchone()
        
        if existing_like:
            # Unlike
            cursor.execute("DELETE FROM transaction_likes WHERE transaction_id = %s AND user_id = %s", 
                          (transaction_id, user_id))
            liked = False
        else:
            # Like
            cursor.execute("INSERT INTO transaction_likes (transaction_id, user_id) VALUES (%s, %s)", 
                          (transaction_id, user_id))
            liked = True
        
        # Get updated like count
        cursor.execute("SELECT COUNT(*) FROM transaction_likes WHERE transaction_id = %s", (transaction_id,))
        like_count = cursor.fetchone()[0]
        
        conn.commit()
        return {'success': True, 'liked': liked, 'like_count': like_count}
    except Exception as e:
        conn.rollback()
        return {'success': False, 'error': str(e)}, 500
    finally:
        cursor.close()
        db_pool.putconn(conn)

@app.route('/comment_transaction/<int:transaction_id>', methods=['POST'])
def comment_transaction(transaction_id):
    if 'user_id' not in session:
        return {'success': False, 'error': 'Not logged in'}, 401
    
    user_id = session['user_id']
    comment_text = request.form.get('comment', '').strip()
    
    if not comment_text:
        return {'success': False, 'error': 'Comment cannot be empty'}, 400
    
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        
        # Insert comment
        cursor.execute("""
            INSERT INTO transaction_comments (transaction_id, user_id, comment) 
            VALUES (%s, %s, %s)
        """, (transaction_id, user_id, comment_text))
        
        # Get updated comment count
        cursor.execute("SELECT COUNT(*) FROM transaction_comments WHERE transaction_id = %s", (transaction_id,))
        comment_count = cursor.fetchone()[0]
        
        conn.commit()
        return {'success': True, 'comment_count': comment_count}
    except Exception as e:
        conn.rollback()
        return {'success': False, 'error': str(e)}, 500
    finally:
        cursor.close()
        db_pool.putconn(conn)

@app.route('/get_comments/<int:transaction_id>')
def get_comments(transaction_id):
    if 'user_id' not in session:
        return {'success': False, 'error': 'Not logged in'}, 401
    
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT tc.comment, tc.created_at, u.username
            FROM transaction_comments tc
            JOIN users u ON tc.user_id = u.id
            WHERE tc.transaction_id = %s
            ORDER BY tc.created_at ASC
        """, (transaction_id,))
        
        comments_data = cursor.fetchall()
        comments = []
        for comment in comments_data:
            comments.append({
                'comment': comment[0],
                'created_at': comment[1].strftime('%m/%d/%y at %H:%M'),
                'username': comment[2]
            })
        
        return {'success': True, 'comments': comments}
    except Exception as e:
        return {'success': False, 'error': str(e)}, 500
    finally:
        cursor.close()
        db_pool.putconn(conn)

@app.route('/portfolio_history/<int:user_id>')
def get_portfolio_history(user_id):
    """Get portfolio history data for charting"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        
        # Get portfolio history for the last 30 days
        cursor.execute("""
            SELECT 
                total_points,
                points_invested,
                points_reserve,
                recorded_at
            FROM portfolio_history
            WHERE user_id = %s 
                AND recorded_at >= NOW() - INTERVAL '30 days'
            ORDER BY recorded_at ASC
        """, (user_id,))
        
        history_data = cursor.fetchall()
        
        # Format data for Chart.js
        chart_data = {
            'labels': [],
            'datasets': [{
                'label': 'Total Points',
                'data': [],
                'borderColor': 'rgb(34, 197, 94)',
                'backgroundColor': 'rgba(34, 197, 94, 0.1)',
                'fill': True,
                'tension': 0.4
            }]
        }
        
        for row in history_data:
            total_points = float(row[0])
            recorded_at = row[3]
            
            # Format date for display
            chart_data['labels'].append(recorded_at.strftime('%m/%d'))
            chart_data['datasets'][0]['data'].append(total_points)
        
        return chart_data
        
    except Exception as e:
        return {"error": str(e)}, 500
    finally:
        cursor.close()
        db_pool.putconn(conn)

def record_portfolio_history():
    """Record current portfolio values for all users"""
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        
        # Get all users
        cursor.execute("SELECT id FROM users")
        user_ids = [row[0] for row in cursor.fetchall()]
        print(f"📊 Recording portfolio history for {len(user_ids)} users")
        
        for user_id in user_ids:
            try:
                # Calculate current portfolio values for this user
                
                # Get user's balance
                cursor.execute("SELECT balance FROM users WHERE id = %s", (user_id,))
                balance_result = cursor.fetchone()
                balance = float(balance_result[0]) if balance_result and balance_result[0] is not None else 0.0
                
                # Get user's holdings with current prices
                cursor.execute("""
                    WITH latest_prices AS (
                        SELECT DISTINCT ON (spotify_id) spotify_id, price
                        FROM artist_history
                        ORDER BY spotify_id, recorded_at DESC
                    )
                    SELECT 
                        b.shares,
                        b.avg_price,
                        lp.price as current_price
                    FROM bets b
                    JOIN artists a ON b.artist_id = a.id
                    JOIN latest_prices lp ON a.spotify_id = lp.spotify_id
                    WHERE b.user_id = %s
                """, (user_id,))
                
                holdings = cursor.fetchall()
                
                # Calculate portfolio totals
                total_invested = 0.0
                current_value = 0.0
                
                for holding in holdings:
                    shares = float(holding[0]) if holding[0] is not None else 0
                    avg_price = float(holding[1]) if holding[1] is not None else 0
                    current_price = float(holding[2]) if holding[2] is not None else 0
                    
                    total_invested += shares * avg_price
                    current_value += shares * current_price
                
                total_points = balance + current_value
                
                print(f"  User {user_id}: Balance={balance}, Invested={current_value}, Total={total_points}")
                
                # Record the portfolio snapshot
                cursor.execute("""
                    INSERT INTO portfolio_history (user_id, total_points, points_invested, points_reserve)
                    VALUES (%s, %s, %s, %s)
                """, (user_id, total_points, current_value, balance))
                
            except Exception as e:
                print(f"Error recording portfolio history for user {user_id}: {e}")
        
        conn.commit()
        print(f"✅ Recorded portfolio history for {len(user_ids)} users")
        
    except Exception as e:
        print(f"Error in record_portfolio_history: {e}")
        conn.rollback()
    finally:
        cursor.close()
        db_pool.putconn(conn)

@app.route('/test_portfolio_history')
def test_portfolio_history():
    """Test route to manually record portfolio history"""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    record_portfolio_history()
    return "Portfolio history recorded successfully! <a href='/portfolio'>View Portfolio</a>"

def main():
    # Initialize Spotify API client and database connection
    app.run(debug=True, port=5004)

if __name__ == '__main__':
    main()

