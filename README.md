# Anticip 🎵📈

A real-time music popularity trading platform where users buy and sell shares in artists based on their Spotify monthly listener counts.

## 🚀 Features

- **Artist Trading**: Buy and sell shares in your favorite artists
- **Real-time Pricing**: Dynamic pricing based on Spotify monthly listener data
- **Portfolio Management**: Track your investments and net worth
- **Social Features**: Follow other traders and view their portfolios
- **Price Charts**: Visualize artist popularity trends
- **Secure Authentication**: Production-ready security with rate limiting
- **Admin Panel**: Manage artists, users, and approve new artists

## 📋 Tech Stack

- **Backend**: Flask (Python 3.12)
- **Database**: SQLite with WAL mode
- **Authentication**: Flask-Login with bcrypt
- **Rate Limiting**: Flask-Limiter
- **API**: Spotify Web API
- **Frontend**: Jinja2 templates with Art Deco CSS
- **Deployment**: Gunicorn + Railway

## 🔒 Security Features

- Persistent secret key management
- Password hashing with bcrypt
- Input validation and XSS sanitization
- Rate limiting on sensitive endpoints
- Atomic database transactions
- Secure session cookies (HTTPOnly, Secure, SameSite)
- Environment-based configuration
- Structured logging

## 🏃 Quick Start (Local Development)

### Prerequisites

- Python 3.12+
- Spotify Developer Account (for API credentials)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/stephencoan8/anticip.git
cd anticip
```

2. Run the automated setup script:
```bash
chmod +x install_updates.sh
./install_updates.sh
```

3. Configure environment variables in `.env`:
```bash
# Required variables (see .env.example for full list)
SECRET_KEY=your-secret-key-here
SPOTIFY_CLIENT_ID=your-spotify-client-id
SPOTIFY_CLIENT_SECRET=your-spotify-client-secret
FLASK_ENV=development
DATABASE_URL=sqlite:///anticip.db
```

4. Run the verification script:
```bash
python verify_setup.py
```

5. Start the development server:
```bash
python app.py
```

Visit http://localhost:5000 to access the app.

## 🚢 Railway Deployment

### Step 1: Prepare Railway Project

1. Go to [Railway.app](https://railway.app) and sign in
2. Click **"New Project"** → **"Deploy from GitHub repo"**
3. Select your repository: `stephencoan8/anticip`
4. Railway will auto-detect the Python app

### Step 2: Configure Environment Variables

In Railway's dashboard, add these environment variables:

**Required Variables:**
```
SECRET_KEY=<generate-strong-secret-key>
SPOTIFY_CLIENT_ID=<your-spotify-client-id>
SPOTIFY_CLIENT_SECRET=<your-spotify-client-secret>
FLASK_ENV=production
DATABASE_URL=sqlite:///anticip.db
ADMIN_USERNAME=admin
ADMIN_PASSWORD=<strong-admin-password>
```

**Optional Performance Variables:**
```
WEB_CONCURRENCY=4
MAX_REQUESTS=1000
RATE_LIMIT_ENABLED=true
```

To generate a strong `SECRET_KEY`:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Step 3: Deploy

1. Railway will automatically deploy using the `Procfile`
2. Monitor the build logs in the Railway dashboard
3. Once deployed, Railway will provide a public URL
4. Visit the `/health` endpoint to verify deployment

### Step 4: Initialize Database

After first deployment:
1. Access the Railway shell or use the provided URL
2. The database will auto-initialize on first run
3. Login with your `ADMIN_USERNAME` and `ADMIN_PASSWORD`
4. Add artists via the admin panel or run:
```bash
python seed_artists.py
```

### Step 5: Setup Automated Popularity Updates

For production, set up a cron job or Railway schedule to update artist popularity:
```bash
# In Railway shell or local environment connected to production
python update_popularity.py
```

See `POPULARITY_UPDATE_SETUP.md` for detailed instructions.

## 📁 Project Structure

```
anticip/
├── app.py                      # Main Flask application
├── config.py                   # Configuration management
├── middleware.py               # Authentication decorators
├── validators.py               # Input validation
├── db_utils.py                 # Database utilities
├── wsgi.py                     # WSGI entry point
├── requirements.txt            # Python dependencies
├── Procfile                    # Railway/Gunicorn config
├── runtime.txt                 # Python version
├── .env.example               # Environment template
├── .gitignore                 # Git ignore rules
├── static/                    # CSS and assets
├── templates/                 # Jinja2 templates
└── logs/                      # Application logs
```

## 🔧 Configuration Files

- **Procfile**: Gunicorn production server config
- **requirements.txt**: Python dependencies
- **runtime.txt**: Python version (3.12.0)
- **.env**: Environment variables (not in git)
- **.env.example**: Environment template
- **railway.json**: Railway deployment config

## 📊 Database Schema

The app uses SQLite with the following main tables:
- `users`: User accounts and authentication
- `artists`: Artist information and Spotify data
- `transactions`: Buy/sell transaction history
- `portfolios`: User holdings per artist
- `follows`: Social follow relationships
- `admin_requests`: Pending artist approval requests

## 🛠️ Development Scripts

- `verify_setup.py`: Verify environment configuration
- `install_updates.sh`: Automated setup script
- `seed_artists.py`: Populate initial artist data
- `update_popularity.py`: Update Spotify listener counts
- `test_admin_access.py`: Test admin authentication

## 📚 Documentation

- `QUICK_START.md`: Detailed setup guide
- `TECHNICAL_AUDIT.md`: Security and performance audit
- `IMMEDIATE_FIXES.md`: Critical fixes implemented
- `IMPLEMENTATION_SUMMARY.md`: Change log
- `COMPLETION_REPORT.md`: Executive summary
- `SETUP_COMPLETE.md`: Final setup instructions
- `DEPLOYMENT.md`: Deployment documentation
- `POPULARITY_UPDATE_SETUP.md`: Popularity update guide

## 🐛 Troubleshooting

### Common Issues

**"Invalid credentials" on login:**
- Ensure password meets requirements (8+ chars, uppercase, lowercase, number)
- Check admin credentials in environment variables

**Database locked errors:**
- SQLite is in WAL mode for better concurrency
- Ensure only one process writes at a time
- Consider PostgreSQL for high-traffic production

**Spotify API errors:**
- Verify `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET`
- Check Spotify Developer Dashboard for API quotas

**Rate limiting issues:**
- Adjust rate limits in `app.py` if needed
- Set `RATE_LIMIT_ENABLED=false` to disable (not recommended)

### Health Check

Visit `/health` to verify:
- App is running
- Database connectivity
- Environment configuration

## 🔐 Security Best Practices

1. **Never commit `.env` to git** (already in `.gitignore`)
2. **Use strong passwords** for admin accounts
3. **Rotate SECRET_KEY** periodically
4. **Keep dependencies updated**: `pip list --outdated`
5. **Monitor logs** for suspicious activity
6. **Enable HTTPS** in production (Railway provides this)
7. **Review rate limits** for your traffic patterns

## 📈 Performance Tips

1. **Database**: Consider PostgreSQL for production scaling
2. **Caching**: Add Redis for session storage and API caching
3. **CDN**: Use CDN for static assets
4. **Monitoring**: Set up Sentry or similar for error tracking
5. **Background Jobs**: Use Celery for async tasks (Spotify updates)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📝 License

This project is private and proprietary.

## 👤 Author

**Stephen Coan**
- GitHub: [@stephencoan8](https://github.com/stephencoan8)

## 🙏 Acknowledgments

- Spotify Web API for artist data
- Flask and Python community
- Railway for deployment platform

---

**Status**: ✅ Production-ready after security and scalability overhaul
**Last Updated**: 2024
**Version**: 2.0.0