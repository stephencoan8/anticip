# Immediate Critical Fixes - Quick Wins

These changes can be implemented immediately to address the most severe vulnerabilities without full refactoring.

---

## 1. SECURITY PATCHES (Implement Today)

### Fix 1.1: Persistent Secret Key
```python
# app.py - Line 17
# BEFORE:
secret_key = os.getenv("SECRET_KEY", os.urandom(24))

# AFTER:
secret_key = os.getenv("SECRET_KEY")
if not secret_key:
    raise RuntimeError("SECRET_KEY environment variable must be set")
```

### Fix 1.2: Secure Session Configuration
```python
# Add after app.secret_key = secret_key
app.config.update(
    SESSION_COOKIE_SECURE=True,  # HTTPS only
    SESSION_COOKIE_HTTPONLY=True,  # No JS access
    SESSION_COOKIE_SAMESITE='Lax',  # CSRF protection
    PERMANENT_SESSION_LIFETIME=timedelta(days=7)
)
```

### Fix 1.3: Authentication Decorator
```python
# Add to app.py after imports
from functools import wraps

def require_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def require_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if not session.get('is_admin', False):
            return "Access denied. Admin privileges required.", 403
        return f(*args, **kwargs)
    return decorated_function

# Then replace all "if 'user_id' not in session" checks with @require_login decorator
```

### Fix 1.4: Rate Limiting on Login
```python
# Add to requirements.txt:
# Flask-Limiter==3.5.0

# Add to app.py:
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["1000 per day", "100 per hour"],
    storage_uri="memory://"  # Use Redis in production
)

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    # existing logic
```

### Fix 1.5: Password Validation
```python
# Add validator function
import re

def validate_password(password):
    """
    Password must be:
    - At least 8 characters
    - Contain uppercase and lowercase
    - Contain at least one digit
    - Contain at least one special character
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain a digit"
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain special character"
    return True, ""

# Use in register route:
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].lower().strip()
        password = request.form['password']
        
        # Validate username
        if len(username) < 3 or len(username) > 30:
            return render_template('register.html', 
                error="Username must be 3-30 characters")
        if not re.match(r'^[a-z0-9_]+$', username):
            return render_template('register.html', 
                error="Username can only contain letters, numbers, and underscores")
        
        # Validate password
        is_valid, error_msg = validate_password(password)
        if not is_valid:
            return render_template('register.html', error=error_msg)
        
        # Rest of logic...
```

---

## 2. DATABASE INTEGRITY (Implement This Week)

### Fix 2.1: Add Database Constraints
```sql
-- Run these migrations on your database

-- Prevent negative balances
ALTER TABLE users ADD CONSTRAINT check_positive_balance CHECK (balance >= 0);

-- Prevent zero/negative shares
ALTER TABLE bets ADD CONSTRAINT check_positive_shares CHECK (shares > 0);
ALTER TABLE transactions ADD CONSTRAINT check_positive_shares_trans CHECK (shares > 0);

-- Ensure unique user-artist holdings
ALTER TABLE bets ADD CONSTRAINT unique_user_artist UNIQUE (user_id, artist_id);

-- Add critical indexes
CREATE INDEX IF NOT EXISTS idx_artist_history_spotify_time 
    ON artist_history(spotify_id, recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_transactions_user_time 
    ON transactions(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_bets_user_artist 
    ON bets(user_id, artist_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_history_user_time 
    ON portfolio_history(user_id, recorded_at DESC);
```

### Fix 2.2: Atomic Trading with Locks
```python
# Replace buy_artist function with transaction-safe version
@app.route('/buy/<spotify_id>', methods=['POST'])
@require_login  # Use new decorator
def buy_artist(spotify_id):
    user_id = session['user_id']
    shares = int(request.form.get('shares', 0))
    caption = request.form.get('caption', '').strip()
    privacy = request.form.get('privacy', 'public')
    
    if shares <= 0:
        return "Invalid share amount", 400
    if len(caption) > 500:
        return "Caption too long (max 500 characters)", 400
    if privacy not in ['public', 'followers', 'private']:
        privacy = 'public'
        
    conn = db_pool.getconn()
    try:
        cursor = conn.cursor()
        
        # START TRANSACTION WITH LOCK
        cursor.execute("BEGIN")
        
        # Get artist with lock
        cursor.execute(
            "SELECT id FROM artists WHERE spotify_id = %s FOR UPDATE", 
            (spotify_id,)
        )
        artist_row = cursor.fetchone()
        if not artist_row:
            conn.rollback()
            return "Artist not found", 404
        artist_id = artist_row[0]
        
        # Get current price
        cursor.execute(
            "SELECT price FROM artist_history WHERE spotify_id = %s "
            "ORDER BY recorded_at DESC LIMIT 1", 
            (spotify_id,)
        )
        price_row = cursor.fetchone()
        if not price_row:
            conn.rollback()
            return "No price data", 400
        price = float(price_row[0])
        total_cost = shares * price
        
        # Check and update balance with lock
        cursor.execute(
            "SELECT balance FROM users WHERE id = %s FOR UPDATE", 
            (user_id,)
        )
        balance_row = cursor.fetchone()
        balance = float(balance_row[0]) if balance_row else 0.0
        
        if balance < total_cost:
            conn.rollback()
            return "Insufficient funds", 400
            
        # Deduct balance
        cursor.execute(
            "UPDATE users SET balance = balance - %s WHERE id = %s", 
            (total_cost, user_id)
        )
        
        # Update holdings
        cursor.execute(
            "SELECT id, shares, avg_price FROM bets "
            "WHERE user_id = %s AND artist_id = %s FOR UPDATE", 
            (user_id, artist_id)
        )
        bet = cursor.fetchone()
        
        if bet:
            bet_id, current_shares, current_avg = bet
            total_shares = current_shares + shares
            new_avg = ((current_shares * current_avg) + (shares * price)) / total_shares
            cursor.execute(
                "UPDATE bets SET shares = %s, avg_price = %s, timestamp = NOW() "
                "WHERE id = %s", 
                (total_shares, new_avg, bet_id)
            )
        else:
            cursor.execute(
                "INSERT INTO bets (user_id, artist_id, shares, avg_price) "
                "VALUES (%s, %s, %s, %s)", 
                (user_id, artist_id, shares, price)
            )
        
        # Record transaction
        cursor.execute("""
            INSERT INTO transactions 
            (user_id, artist_id, transaction_type, shares, price_per_share, 
             total_amount, caption, privacy)
            VALUES (%s, %s, 'buy', %s, %s, %s, %s, %s)
        """, (user_id, artist_id, shares, price, total_cost, caption, privacy))
        
        # COMMIT TRANSACTION
        conn.commit()
        return redirect(url_for('artist_detail', spotify_id=spotify_id))
        
    except Exception as e:
        conn.rollback()
        app.logger.error(f"Trade error: {str(e)}", exc_info=True)
        return f"Transaction failed: {str(e)}", 500
    finally:
        cursor.close()
        db_pool.putconn(conn)
```

---

## 3. ERROR HANDLING & LOGGING

### Fix 3.1: Proper Logging
```python
# Add at top of app.py
import logging
from logging.handlers import RotatingFileHandler

# Configure logging
if not app.debug:
    # File handler
    file_handler = RotatingFileHandler(
        'logs/anticip.log', 
        maxBytes=10240000, 
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    
    app.logger.setLevel(logging.INFO)
    app.logger.info('Anticip startup')

# Replace all print() statements with app.logger.info() or app.logger.error()
```

### Fix 3.2: Global Error Handler
```python
# Add error handlers
@app.errorhandler(404)
def not_found_error(error):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Not found'}), 404
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db_pool.putconn(conn) if 'conn' in locals() else None
    app.logger.error(f'Server Error: {error}', exc_info=True)
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Internal server error'}), 500
    return render_template('errors/500.html'), 500

@app.errorhandler(403)
def forbidden_error(error):
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Forbidden'}), 403
    return render_template('errors/403.html'), 403
```

---

## 4. PERFORMANCE QUICK WINS

### Fix 4.1: Connection Pool Error Handling
```python
# Add context manager for database connections
from contextlib import contextmanager

@contextmanager
def get_db_connection():
    conn = db_pool.getconn()
    try:
        yield conn
    except Exception as e:
        conn.rollback()
        app.logger.error(f"Database error: {str(e)}", exc_info=True)
        raise
    finally:
        db_pool.putconn(conn)

# Usage example:
@app.route('/artists')
@require_login
def list_artists():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Your queries here
        cursor.close()
```

### Fix 4.2: Add Database Indexes (If Not Done in 2.1)
```python
# Add index creation to table setup
cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_artist_history_lookup 
        ON artist_history(spotify_id, recorded_at DESC);
    CREATE INDEX IF NOT EXISTS idx_transactions_user 
        ON transactions(user_id, created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_follows_lookup 
        ON follows(follower_id, followed_id, status);
""")
```

---

## 5. PRODUCTION READINESS

### Fix 5.1: Environment Configuration
```python
# app.py - Replace hardcoded values
import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY must be set")
    
    DATABASE_URL = os.getenv('DATABASE_URL')
    SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
    SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
    
    # Flask config
    DEBUG = os.getenv('FLASK_ENV') == 'development'
    TESTING = os.getenv('FLASK_ENV') == 'testing'
    
    # Session config
    SESSION_COOKIE_SECURE = not DEBUG
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Database pool
    DB_POOL_MIN = int(os.getenv('DB_POOL_MIN', 1))
    DB_POOL_MAX = int(os.getenv('DB_POOL_MAX', 20))

app.config.from_object(Config)
```

### Fix 5.2: Health Check Endpoint
```python
@app.route('/health')
def health_check():
    """Health check endpoint for load balancers"""
    try:
        # Check database connection
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1')
            cursor.close()
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        app.logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': 'Database connection failed'
        }), 503
```

### Fix 5.3: Proper WSGI Configuration
```python
# Create wsgi.py
from app import app

if __name__ == "__main__":
    # Development only
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5004)),
        debug=os.getenv('FLASK_ENV') == 'development'
    )
```

### Fix 5.4: Update Procfile for Production
```
# Procfile
web: gunicorn --workers=4 --threads=2 --timeout=60 --bind=0.0.0.0:$PORT wsgi:app
```

---

## 6. INPUT VALIDATION

### Fix 6.1: Sanitize User Inputs
```python
# Add input sanitization helper
import bleach
from html import escape

def sanitize_input(text, max_length=None):
    """Sanitize user input to prevent XSS"""
    if not text:
        return ""
    
    # Strip whitespace
    text = text.strip()
    
    # Enforce max length
    if max_length and len(text) > max_length:
        text = text[:max_length]
    
    # Escape HTML
    text = escape(text)
    
    return text

# Use in routes:
@app.route('/buy/<spotify_id>', methods=['POST'])
@require_login
def buy_artist(spotify_id):
    caption = sanitize_input(request.form.get('caption', ''), max_length=500)
    # rest of logic
```

---

## 7. FRONTEND IMPROVEMENTS

### Fix 7.1: Add Client-Side Validation
```html
<!-- In buy/sell forms, add validation -->
<form method="POST" onsubmit="return validateTradeForm(this)">
    <input type="number" name="shares" min="1" max="10000" required>
    <textarea name="caption" maxlength="500"></textarea>
    <button type="submit">Submit</button>
</form>

<script>
function validateTradeForm(form) {
    const shares = parseInt(form.shares.value);
    const caption = form.caption.value;
    
    if (shares < 1 || shares > 10000) {
        alert('Shares must be between 1 and 10,000');
        return false;
    }
    
    if (caption.length > 500) {
        alert('Caption too long (max 500 characters)');
        return false;
    }
    
    return true;
}
</script>
```

### Fix 7.2: Add Loading States
```html
<!-- Add to base.html -->
<script>
// Show loading indicator for form submissions
document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('form[method="POST"]');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const button = form.querySelector('button[type="submit"]');
            if (button) {
                button.disabled = true;
                button.innerHTML = 'Processing...';
            }
        });
    });
});
</script>
```

---

## 8. MONITORING BASICS

### Fix 8.1: Add Request Logging Middleware
```python
from time import time

@app.before_request
def before_request():
    request.start_time = time()

@app.after_request
def after_request(response):
    if hasattr(request, 'start_time'):
        elapsed = time() - request.start_time
        app.logger.info(
            f'{request.method} {request.path} - {response.status_code} - {elapsed:.3f}s'
        )
    return response
```

---

## IMPLEMENTATION CHECKLIST

### Day 1 (Critical Security)
- [ ] Fix secret key configuration
- [ ] Add secure session settings
- [ ] Create authentication decorators
- [ ] Add rate limiting to login
- [ ] Add password validation

### Day 2 (Database Safety)
- [ ] Add database constraints (CHECK, UNIQUE)
- [ ] Add critical indexes
- [ ] Implement transaction locking for trades
- [ ] Add connection pool error handling

### Day 3 (Error Handling)
- [ ] Set up proper logging
- [ ] Add global error handlers
- [ ] Create health check endpoint
- [ ] Add input sanitization

### Day 4 (Production Config)
- [ ] Environment-based configuration
- [ ] Update WSGI setup
- [ ] Add request logging
- [ ] Client-side validation

### Day 5 (Testing & Deployment)
- [ ] Test all critical flows
- [ ] Update deployment configuration
- [ ] Document changes
- [ ] Deploy to staging

---

## Testing the Fixes

```bash
# 1. Test authentication
curl -X POST http://localhost:5004/login \
  -d "username=test&password=wrongpass"
# Should rate limit after 10 attempts

# 2. Test health check
curl http://localhost:5004/health
# Should return {"status": "healthy"}

# 3. Test concurrent trades (race condition)
# Run in separate terminals simultaneously
for i in {1..10}; do
  curl -X POST http://localhost:5004/buy/ARTIST_ID \
    -H "Cookie: session=YOUR_SESSION" \
    -d "shares=100"
done
# Balance should be correctly decremented

# 4. Test input validation
curl -X POST http://localhost:5004/register \
  -d "username=a&password=weak"
# Should reject with validation error
```

---

These fixes can be implemented incrementally without breaking existing functionality. Priority: Security fixes first, then database integrity, then everything else.
