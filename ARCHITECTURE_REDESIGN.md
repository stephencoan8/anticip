# Architecture Redesign Proposal - Anticip Platform

## Proposed Modern Architecture

```
anticip/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py                 # Environment-based configuration
│   │   ├── extensions.py             # Flask extensions initialization
│   │   │
│   │   ├── models/                   # SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── artist.py
│   │   │   ├── transaction.py
│   │   │   ├── portfolio.py
│   │   │   └── social.py
│   │   │
│   │   ├── schemas/                  # Marshmallow/Pydantic schemas
│   │   │   ├── __init__.py
│   │   │   ├── user_schema.py
│   │   │   ├── artist_schema.py
│   │   │   └── transaction_schema.py
│   │   │
│   │   ├── api/                      # API routes (Blueprint-based)
│   │   │   ├── __init__.py
│   │   │   ├── v1/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auth.py
│   │   │   │   ├── artists.py
│   │   │   │   ├── trades.py
│   │   │   │   ├── portfolio.py
│   │   │   │   ├── social.py
│   │   │   │   └── feed.py
│   │   │
│   │   ├── services/                 # Business logic layer
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── trading_service.py
│   │   │   ├── portfolio_service.py
│   │   │   ├── spotify_service.py
│   │   │   └── social_service.py
│   │   │
│   │   ├── repositories/             # Data access layer
│   │   │   ├── __init__.py
│   │   │   ├── user_repository.py
│   │   │   ├── artist_repository.py
│   │   │   └── transaction_repository.py
│   │   │
│   │   ├── middleware/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py               # JWT authentication
│   │   │   ├── rate_limiter.py
│   │   │   ├── error_handler.py
│   │   │   └── request_logger.py
│   │   │
│   │   ├── tasks/                    # Celery background tasks
│   │   │   ├── __init__.py
│   │   │   ├── price_updater.py
│   │   │   ├── portfolio_recorder.py
│   │   │   └── notifications.py
│   │   │
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── validators.py
│   │       ├── helpers.py
│   │       └── decorators.py
│   │
│   ├── migrations/                   # Alembic migrations
│   │   └── versions/
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py               # Pytest fixtures
│   │   ├── unit/
│   │   │   ├── test_models.py
│   │   │   ├── test_services.py
│   │   │   └── test_repositories.py
│   │   ├── integration/
│   │   │   ├── test_api.py
│   │   │   └── test_trading.py
│   │   └── e2e/
│   │       └── test_user_flows.py
│   │
│   ├── alembic.ini
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── wsgi.py                       # Gunicorn entry point
│
├── frontend/                         # React/Next.js application
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── store/                    # Redux/Zustand
│   │   └── utils/
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   └── next.config.js
│
├── nginx/
│   └── nginx.conf                    # Reverse proxy config
│
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── cd.yml
│
├── docs/
│   ├── api/                          # OpenAPI/Swagger
│   ├── deployment.md
│   └── architecture.md
│
├── .env.example
├── .gitignore
├── docker-compose.yml                # Development environment
├── docker-compose.prod.yml           # Production stack
└── README.md
```

---

## Technology Stack Upgrade

### Backend
- **Framework**: Flask → **FastAPI** (async, automatic API docs, better performance)
- **ORM**: psycopg2 raw SQL → **SQLAlchemy 2.0** with async support
- **Migrations**: Manual ALTER → **Alembic**
- **API Docs**: None → **OpenAPI/Swagger** (auto-generated)
- **Validation**: Manual checks → **Pydantic** schemas
- **Authentication**: Session → **JWT** with refresh tokens
- **Task Queue**: None → **Celery** with Redis broker
- **Caching**: None → **Redis** (sessions, API responses, Spotify data)
- **Testing**: None → **pytest** with fixtures and coverage
- **Logging**: print() → **structlog** with JSON formatting

### Frontend
- **Framework**: Vanilla JS + Tailwind CDN → **Next.js 14** + TypeScript
- **State Management**: None → **Zustand** or Redux Toolkit
- **Styling**: Inline styles → **Tailwind CSS** (properly built) + CSS Modules
- **API Client**: fetch → **React Query** (caching, optimistic updates)
- **Forms**: Basic HTML → **React Hook Form** with Zod validation
- **Charts**: Basic Chart.js → **Recharts** or **ApexCharts**
- **Build Tool**: None → **Vite** or **Next.js** bundler

### Infrastructure
- **Web Server**: Flask dev server → **Gunicorn** with async workers + **Nginx**
- **Database**: PostgreSQL (keep) with **connection pooling** (PgBouncer)
- **Containerization**: None → **Docker** + **docker-compose**
- **Monitoring**: None → **Sentry** (errors) + **Prometheus** + **Grafana**
- **CI/CD**: None → **GitHub Actions**
- **Secrets**: .env → **AWS Secrets Manager** or **Vault**

---

## Database Schema Improvements

```sql
-- Add missing indexes
CREATE INDEX idx_artist_history_spotify_id_time ON artist_history(spotify_id, recorded_at DESC);
CREATE INDEX idx_transactions_user_id_time ON transactions(user_id, created_at DESC);
CREATE INDEX idx_bets_user_artist ON bets(user_id, artist_id);
CREATE INDEX idx_follows_follower ON follows(follower_id, status);
CREATE INDEX idx_follows_followed ON follows(followed_id, status);
CREATE INDEX idx_portfolio_history_user_time ON portfolio_history(user_id, recorded_at DESC);

-- Add constraints
ALTER TABLE users ADD CONSTRAINT check_positive_balance CHECK (balance >= 0);
ALTER TABLE bets ADD CONSTRAINT check_positive_shares CHECK (shares > 0);
ALTER TABLE bets ADD CONSTRAINT unique_user_artist UNIQUE (user_id, artist_id);
ALTER TABLE transactions ADD CONSTRAINT check_positive_shares CHECK (shares > 0);

-- Add soft delete support
ALTER TABLE artists ADD COLUMN deleted_at TIMESTAMP DEFAULT NULL;
ALTER TABLE users ADD COLUMN deleted_at TIMESTAMP DEFAULT NULL;

-- Add audit fields
ALTER TABLE artists ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE users ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE transactions ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Optimize portfolio_history with partitioning (for large datasets)
CREATE TABLE portfolio_history_partitioned (
    LIKE portfolio_history INCLUDING ALL
) PARTITION BY RANGE (recorded_at);

-- Add materialized view for leaderboard
CREATE MATERIALIZED VIEW user_leaderboard AS
SELECT 
    u.id,
    u.username,
    u.balance + COALESCE(SUM(b.shares * ah.price), 0) as net_worth,
    COUNT(DISTINCT b.artist_id) as unique_holdings
FROM users u
LEFT JOIN bets b ON u.id = b.user_id
LEFT JOIN artists a ON b.artist_id = a.id
LEFT JOIN LATERAL (
    SELECT price FROM artist_history 
    WHERE spotify_id = a.spotify_id 
    ORDER BY recorded_at DESC LIMIT 1
) ah ON true
GROUP BY u.id
ORDER BY net_worth DESC;

CREATE UNIQUE INDEX idx_leaderboard_user ON user_leaderboard(id);
```

---

## API Design (RESTful)

### Authentication
```
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
POST   /api/v1/auth/logout
GET    /api/v1/auth/me
```

### Artists
```
GET    /api/v1/artists                # List with pagination, filters
GET    /api/v1/artists/:id            # Artist details
GET    /api/v1/artists/:id/history    # Price history with time range
POST   /api/v1/artists                # Add artist (admin only)
DELETE /api/v1/artists/:id            # Delete artist (admin only)
GET    /api/v1/artists/search?q=      # Search artists
```

### Trading
```
GET    /api/v1/trades                 # User's trade history
POST   /api/v1/trades                 # Execute trade (buy/sell)
GET    /api/v1/trades/:id             # Trade details
```

### Portfolio
```
GET    /api/v1/portfolio              # Current holdings
GET    /api/v1/portfolio/history      # Portfolio value over time
GET    /api/v1/portfolio/performance  # Analytics
```

### Social
```
GET    /api/v1/users                  # List users (search)
GET    /api/v1/users/:id              # User profile
GET    /api/v1/users/:id/portfolio    # User's public portfolio

POST   /api/v1/follows/:userId        # Send follow request
DELETE /api/v1/follows/:userId        # Unfollow
GET    /api/v1/follows/pending        # Pending requests
PUT    /api/v1/follows/:requestId     # Accept/reject request

GET    /api/v1/feed                   # Transaction feed
POST   /api/v1/transactions/:id/likes
DELETE /api/v1/transactions/:id/likes
GET    /api/v1/transactions/:id/comments
POST   /api/v1/transactions/:id/comments
```

### Admin
```
GET    /api/v1/admin/stats            # Platform statistics
GET    /api/v1/admin/users            # All users
POST   /api/v1/admin/refresh          # Trigger price refresh
```

---

## Security Enhancements

### 1. Authentication Middleware
```python
from functools import wraps
from flask import request, jsonify
import jwt

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'No token provided'}), 401
        try:
            payload = jwt.decode(token, config.JWT_SECRET, algorithms=['HS256'])
            request.user_id = payload['user_id']
            request.is_admin = payload.get('is_admin', False)
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        return f(*args, **kwargs)
    return decorated

def require_admin(f):
    @wraps(f)
    @require_auth
    def decorated(*args, **kwargs):
        if not request.is_admin:
            return jsonify({'error': 'Admin privileges required'}), 403
        return f(*args, **kwargs)
    return decorated
```

### 2. Rate Limiting
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379",
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/api/v1/auth/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    # Login logic
    pass
```

### 3. Input Validation with Pydantic
```python
from pydantic import BaseModel, validator, conint, confloat
from typing import Literal

class TradeRequest(BaseModel):
    artist_id: int
    shares: conint(gt=0, le=10000)
    action: Literal['buy', 'sell']
    privacy: Literal['public', 'followers', 'private'] = 'public'
    caption: str = ''

    @validator('caption')
    def validate_caption(cls, v):
        if len(v) > 500:
            raise ValueError('Caption too long')
        return v.strip()
```

### 4. CSRF Protection
```python
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect(app)

# For API routes using JWT, disable CSRF
@app.route('/api/v1/trades', methods=['POST'])
@csrf.exempt
@require_auth
def create_trade():
    pass
```

---

## Performance Optimizations

### 1. Async Spotify Integration
```python
import aiohttp
import asyncio

class AsyncSpotifyService:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = None
    
    async def get_token(self):
        # Token refresh logic
        pass
    
    async def get_artist(self, artist_id):
        async with aiohttp.ClientSession() as session:
            headers = {'Authorization': f'Bearer {self.token}'}
            async with session.get(
                f'https://api.spotify.com/v1/artists/{artist_id}',
                headers=headers,
                timeout=5
            ) as response:
                return await response.json()
    
    async def bulk_refresh(self, artist_ids):
        tasks = [self.get_artist(aid) for aid in artist_ids]
        return await asyncio.gather(*tasks, return_exceptions=True)
```

### 2. Database Query Optimization
```python
# Before (N+1)
def get_portfolio(user_id):
    holdings = Bet.query.filter_by(user_id=user_id).all()
    for holding in holdings:
        artist = Artist.query.get(holding.artist_id)  # N queries
        price = ArtistHistory.query.filter_by(
            spotify_id=artist.spotify_id
        ).order_by(ArtistHistory.recorded_at.desc()).first()

# After (1 query)
def get_portfolio(user_id):
    holdings = db.session.query(
        Bet, Artist, ArtistHistory
    ).select_from(Bet)\
     .join(Artist, Bet.artist_id == Artist.id)\
     .join(ArtistHistory, db.and_(
         ArtistHistory.spotify_id == Artist.spotify_id,
         ArtistHistory.id == db.select([
             db.func.max(ArtistHistory.id)
         ]).where(
             ArtistHistory.spotify_id == Artist.spotify_id
         ).correlate(Artist).scalar_subquery()
     ))\
     .filter(Bet.user_id == user_id)\
     .all()
```

### 3. Caching Strategy
```python
from flask_caching import Cache
import redis

cache = Cache(config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_URL': 'redis://localhost:6379/0'
})

@app.route('/api/v1/artists/<int:artist_id>')
@cache.cached(timeout=300, key_prefix='artist')
def get_artist(artist_id):
    # Artist data cached for 5 minutes
    pass

# Invalidate cache on update
@app.route('/api/v1/admin/refresh', methods=['POST'])
@require_admin
def refresh_prices():
    # Refresh logic
    cache.clear()
    return jsonify({'success': True})
```

### 4. Database Connection Pooling
```python
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,   # Recycle connections after 1 hour
    echo_pool=True
)
```

---

## Background Task Processing

### Celery Configuration
```python
# tasks/celery_app.py
from celery import Celery

celery_app = Celery(
    'anticip',
    broker='redis://localhost:6379/1',
    backend='redis://localhost:6379/2'
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    beat_schedule={
        'update-prices': {
            'task': 'tasks.price_updater.update_all_prices',
            'schedule': 3600.0,  # Every hour
        },
        'record-portfolios': {
            'task': 'tasks.portfolio_recorder.record_all',
            'schedule': 1800.0,  # Every 30 minutes
        }
    }
)

# tasks/price_updater.py
@celery_app.task(bind=True, max_retries=3)
def update_all_prices(self):
    try:
        spotify_service = AsyncSpotifyService()
        artist_ids = ArtistRepository.get_all_spotify_ids()
        results = asyncio.run(spotify_service.bulk_refresh(artist_ids))
        # Process results
        return {'updated': len(results)}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
```

---

## Testing Strategy

### Unit Tests
```python
# tests/unit/test_trading_service.py
import pytest
from app.services.trading_service import TradingService

class TestTradingService:
    def test_buy_insufficient_funds(self, db_session, user, artist):
        user.balance = 100
        service = TradingService(db_session)
        
        with pytest.raises(InsufficientFundsError):
            service.execute_trade(
                user_id=user.id,
                artist_id=artist.id,
                shares=1000,
                action='buy'
            )
    
    def test_buy_success(self, db_session, user, artist):
        user.balance = 10000
        service = TradingService(db_session)
        
        trade = service.execute_trade(
            user_id=user.id,
            artist_id=artist.id,
            shares=10,
            action='buy'
        )
        
        assert trade.shares == 10
        assert user.balance == 10000 - (10 * artist.price)
```

### Integration Tests
```python
# tests/integration/test_api.py
def test_create_trade_flow(client, auth_headers):
    # Create trade
    response = client.post(
        '/api/v1/trades',
        json={
            'artist_id': 1,
            'shares': 10,
            'action': 'buy'
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    
    # Verify portfolio updated
    portfolio = client.get('/api/v1/portfolio', headers=auth_headers)
    assert portfolio.json['holdings'][0]['shares'] == 10
```

---

## Monitoring & Observability

### Sentry Integration
```python
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn=config.SENTRY_DSN,
    integrations=[FlaskIntegration()],
    traces_sample_rate=0.1,
    environment=config.ENVIRONMENT
)
```

### Prometheus Metrics
```python
from prometheus_flask_exporter import PrometheusMetrics

metrics = PrometheusMetrics(app)
metrics.info('app_info', 'Application info', version='1.0.0')

# Custom metrics
trade_counter = Counter('trades_total', 'Total trades', ['action', 'status'])
trade_value = Histogram('trade_value_dollars', 'Trade value distribution')

@app.route('/api/v1/trades', methods=['POST'])
def create_trade():
    # Trade logic
    trade_counter.labels(action=data['action'], status='success').inc()
    trade_value.observe(total_value)
```

### Structured Logging
```python
import structlog

logger = structlog.get_logger()

@app.route('/api/v1/trades', methods=['POST'])
@require_auth
def create_trade():
    logger.info(
        'trade_initiated',
        user_id=request.user_id,
        artist_id=data['artist_id'],
        shares=data['shares'],
        action=data['action']
    )
```

---

## Deployment Architecture

### Docker Compose (Production)
```yaml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - api
      - frontend
  
  api:
    build: ./backend
    command: gunicorn -w 4 -k uvicorn.workers.UvicornWorker wsgi:app
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/anticip
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/1
    depends_on:
      - db
      - redis
  
  celery_worker:
    build: ./backend
    command: celery -A tasks.celery_app worker -l info
    depends_on:
      - redis
      - db
  
  celery_beat:
    build: ./backend
    command: celery -A tasks.celery_app beat -l info
    depends_on:
      - redis
  
  frontend:
    build: ./frontend
    environment:
      - NEXT_PUBLIC_API_URL=https://api.anticip.com
  
  db:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=anticip
      - POSTGRES_USER=anticip
      - POSTGRES_PASSWORD=${DB_PASSWORD}
  
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
  
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
  
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:
```

---

## Migration Path (Phased Approach)

### Phase 1: Foundation (Week 1-2)
1. Set up new project structure
2. Implement database migrations with Alembic
3. Add authentication middleware
4. Create base API endpoints with FastAPI
5. Add comprehensive error handling

### Phase 2: Core Features (Week 3-4)
1. Migrate trading logic to service layer
2. Implement async Spotify integration
3. Add caching layer
4. Optimize database queries
5. Add unit tests

### Phase 3: Frontend (Week 5-6)
1. Set up Next.js project
2. Implement authentication flow
3. Migrate artist list and detail pages
4. Implement portfolio view
5. Add real-time updates with WebSockets

### Phase 4: Social Features (Week 7-8)
1. Migrate feed functionality
2. Implement comments/likes
3. Add notifications system
4. Implement search

### Phase 5: Operations (Week 9-10)
1. Add monitoring and logging
2. Implement CI/CD pipeline
3. Set up staging environment
4. Performance testing and optimization
5. Security audit

### Phase 6: Polish (Week 11-12)
1. E2E testing
2. Documentation
3. Load testing
4. Production deployment
5. Post-launch monitoring

---

This redesign transforms the application from a prototype into an enterprise-grade platform capable of handling real-world traffic and complexity.
