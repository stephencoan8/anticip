from flask import Flask, render_template, request, redirect, url_for, session
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv
import os
import psycopg2
from psycopg2 import pool
import bcrypt

app = Flask(__name__)
app.secret_key = os.urandom(24)

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
        return render_template('artist_detail.html', artist=(name, image_url), history=history, holdings=holdings, current_price=current_price, order=order)
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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].lower()
        password = request.form['password'].encode('utf-8')
        conn = db_pool.getconn()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, password FROM users WHERE username = %s", (username,))
            user = cursor.fetchone()
            if user and bcrypt.checkpw(password, user[1].encode('utf-8')):
                session['user_id'] = user[0]
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
    return redirect(url_for('login'))

@app.route('/refresh_artists', methods=['POST'])
def refresh_artists():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT spotify_id FROM artists")
        artist_ids = [row[0] for row in cursor.fetchall()]
        for spotify_id in artist_ids:
            try:
                artist = sp.artist(spotify_id)
                price = artist['popularity']
                cursor.execute("INSERT INTO artist_history (spotify_id, popularity, price) VALUES (%s, %s, %s)",
                               (spotify_id, artist['popularity'], price))
            except Exception as e:
                print(f"Error refreshing {spotify_id}: {e}")
        conn.commit()
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
    if shares <= 0:
        return "Invalid share amount", 400
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
    if shares <= 0:
        return "Invalid share amount", 400
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
        conn.commit()
        return redirect(url_for('artist_detail', spotify_id=spotify_id))
    except Exception as e:
        conn.rollback()
        return f"Database error: {str(e)}", 500
    finally:
        cursor.close()
        db_pool.putconn(conn)

@app.route('/portfolio')
def portfolio():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    order = request.args.get('order', 'alphabetical')  # sort type
    direction = request.args.get('direction', 'asc')   # asc or desc
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        # Get user balance
        cursor.execute("SELECT balance FROM users WHERE id = %s", (user_id,))
        balance_row = cursor.fetchone()
        balance = float(balance_row[0]) if balance_row else 0.0
        # Get all holdings for user
        cursor.execute("""
            SELECT b.shares, b.avg_price, a.spotify_id, a.name, a.image_url
            FROM bets b
            JOIN artists a ON b.artist_id = a.id
            WHERE b.user_id = %s
        """, (user_id,))
        rows = cursor.fetchall()
        holdings = []
        total_invested = 0.0
        net_worth = 0.0
        gain = 0.0
        winning_count = 0
        for shares, avg_price, spotify_id, name, image_url in rows:
            cursor.execute("SELECT price FROM artist_history WHERE spotify_id = %s ORDER BY recorded_at DESC LIMIT 1", (spotify_id,))
            price_row = cursor.fetchone()
            current_price = float(price_row[0]) if price_row else 0.0
            value = shares * current_price
            invested = shares * float(avg_price)
            stock_gain = value - invested
            percent_gain = ((stock_gain / invested) * 100) if invested > 0 else 0.0
            if stock_gain > 0:
                winning_count += 1
            holdings.append({
                'shares': shares,
                'avg_price': float(avg_price),
                'spotify_id': spotify_id,
                'name': name,
                'image_url': image_url,
                'current_price': current_price,
                'value': value,
                'gain': stock_gain,
                'percent_gain': percent_gain
            })
            total_invested += invested
            net_worth += value
            gain += stock_gain
        # Sort holdings based on order and direction
        reverse = direction == 'desc'
        if order == 'alphabetical':
            holdings.sort(key=lambda x: x['name'], reverse=reverse)
        elif order == 'popularity':
            holdings.sort(key=lambda x: x['current_price'], reverse=reverse)
        elif order == 'net_holdings':
            holdings.sort(key=lambda x: x['value'], reverse=reverse)
        elif order == 'gain':
            holdings.sort(key=lambda x: x['gain'], reverse=reverse)
        elif order == 'percent_gain':
            holdings.sort(key=lambda x: x['percent_gain'], reverse=reverse)
        percent_winning = (winning_count / len(holdings) * 100) if holdings else 0.0
        return render_template('portfolio.html', holdings=holdings, net_worth=net_worth, total_invested=total_invested, gain=gain, percent_winning=percent_winning, balance=balance, order=order, direction=direction)
    except Exception as e:
        conn.rollback()
        return f"Database error: {str(e)}", 500
    finally:
        cursor.close()
        db_pool.putconn(conn)

@app.route('/delete_artist/<spotify_id>', methods=['POST'])
def delete_artist(spotify_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        # Get artist id
        cursor.execute("SELECT id FROM artists WHERE spotify_id = %s", (spotify_id,))
        artist_row = cursor.fetchone()
        if not artist_row:
            return "Artist not found", 404
        artist_id = artist_row[0]
        # Delete related bets
        cursor.execute("DELETE FROM bets WHERE artist_id = %s", (artist_id,))
        # Delete related history
        cursor.execute("DELETE FROM artist_history WHERE spotify_id = %s", (spotify_id,))
        # Delete artist
        cursor.execute("DELETE FROM artists WHERE id = %s", (artist_id,))
        conn.commit()
        return redirect(url_for('list_artists'))
    except Exception as e:
        conn.rollback()
        return f"Database error: {str(e)}", 500
    finally:
        cursor.close()
        db_pool.putconn(conn)

if __name__ == '__main__':
    app.run(debug=True, port=5001)