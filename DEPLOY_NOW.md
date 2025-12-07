# 🚀 Railway Deployment Guide - READY TO DEPLOY

## ✅ Pre-Deployment Checklist - COMPLETED

- [x] Security fixes implemented (rate limiting, session security, authentication)
- [x] Environment configuration set up (config.py, .env.example)
- [x] Root route fixed (proper redirects instead of test code)
- [x] Database constraints and indexes added
- [x] Logging configured
- [x] Code pushed to GitHub
- [x] `.gitignore` properly configured
- [x] `Procfile` configured for Gunicorn
- [x] `requirements.txt` up to date
- [x] `runtime.txt` specifies Python version

---

## 🎯 Deploy to Railway - Step by Step

### Step 1: Create Railway Project

1. Go to [Railway.app](https://railway.app)
2. Sign in with your GitHub account
3. Click **"New Project"**
4. Select **"Deploy from GitHub repo"**
5. Choose your repository: `stephencoan8/anticip`
6. Railway will automatically detect it's a Python app

### Step 2: Add PostgreSQL Database

1. In your Railway project dashboard, click **"New"**
2. Select **"Database"** → **"PostgreSQL"**
3. Railway will automatically create a database and set the `DATABASE_URL` environment variable

### Step 3: Configure Environment Variables

In Railway project settings → **Variables**, add these **EXACT VALUES**:

```bash
# Security (REQUIRED)
SECRET_KEY=1a01b4dad74201254f6b0a720957b2f7aced438101b5af46

# Spotify API (REQUIRED)
SPOTIFY_CLIENT_ID=20724827563d42e4b04a569304caf912
SPOTIFY_CLIENT_SECRET=a759c8a251eb48898d3d7a644c398265

# Flask Environment (REQUIRED)
FLASK_ENV=production

# Database (Railway auto-sets this - DO NOT MANUALLY SET)
# DATABASE_URL will be automatically populated by Railway PostgreSQL

# Logging (OPTIONAL)
LOG_LEVEL=INFO
LOG_FILE=logs/anticip.log
```

### Step 4: Deploy

1. Railway will automatically deploy when you push to `main` branch
2. You can also manually trigger deployment by clicking **"Deploy"** in Railway dashboard
3. Watch the build logs in real-time to ensure everything installs correctly
4. Wait for the deployment to complete (usually 2-3 minutes)

### Step 5: Configure Custom Domain

1. In Railway project settings → **Settings** → **Domains**
2. Click **"Generate Domain"** to get a free Railway URL (e.g., `anticip-production.up.railway.app`)
3. Test this URL first before adding custom domain

#### To use `anticip.store` custom domain:

1. In Railway, click **"Custom Domain"**
2. Enter: `anticip.store`
3. Railway will provide DNS instructions
4. In your domain registrar (where you bought anticip.store):
   - Add CNAME record:
     ```
     Type: CNAME
     Name: @ (or use A record if required)
     Value: [provided by Railway]
     ```
   - Add CNAME for www:
     ```
     Type: CNAME
     Name: www
     Value: [provided by Railway]
     ```
5. DNS propagation takes 5-60 minutes

### Step 6: Verify Deployment

Visit your Railway URL and test:

- ✅ Login page loads (not plain text!)
- ✅ User registration works
- ✅ Login works
- ✅ Viewing artists list
- ✅ Artist detail pages
- ✅ Making buy/sell trades
- ✅ Portfolio displays correctly
- ✅ Activity feed shows transactions
- ✅ Following/unfollowing users
- ✅ Admin features (if admin user)

---

## 🔧 Post-Deployment Tasks

### 1. Seed Initial Artists
Once deployed, run the artist seeding script:
```bash
# In Railway dashboard → Service → Settings → Deploy
# Or SSH into your Railway container and run:
python seed_artists_safe.py
```

### 2. Create Admin User
Create your first admin user by registering normally, then update in Railway PostgreSQL:
```sql
UPDATE users SET is_admin = TRUE WHERE username = 'yourusername';
```

### 3. Set Up Popularity Updates
- Use Railway Cron Jobs or external cron service
- Schedule `update_popularity.py` to run daily
- See `POPULARITY_UPDATE_SETUP.md` for details

---

## 🐛 Troubleshooting

### Build Fails
- Check Railway logs for Python/dependency errors
- Ensure `requirements.txt` is properly formatted
- Verify `runtime.txt` has correct Python version

### App Crashes on Start
- Check environment variables are set correctly
- Verify `DATABASE_URL` is automatically set by Railway PostgreSQL
- Check logs for database connection errors

### Database Connection Issues
- Ensure PostgreSQL service is running in Railway
- Check that Railway has automatically linked the database
- Verify no manual `DATABASE_URL` override

### 500 Errors After Deployment
- Check Railway logs for stack traces
- Verify all environment variables are set
- Check database tables were created (see startup logs)

### Custom Domain Not Working
- Verify DNS records are correct
- Wait for DNS propagation (up to 60 minutes)
- Check Railway domain settings show "Active"

---

## 📊 Monitoring

### Railway Dashboard
- View real-time logs
- Monitor CPU/Memory usage
- Track deployments
- Check build times

### Application Logs
- Logs stored in `logs/anticip.log`
- View in Railway dashboard or download

### Database
- Access PostgreSQL directly in Railway
- Run queries to check data integrity
- Monitor database size

---

## 🚨 Important Security Notes

1. **Never commit `.env` file** - Already in `.gitignore` ✅
2. **Use Railway environment variables** - Configured ✅
3. **HTTPS enforced** - Railway provides SSL automatically ✅
4. **Session security** - Configured with secure cookies ✅
5. **Rate limiting active** - Flask-Limiter configured ✅

---

## 🎉 You're Ready!

Your app is **production-ready** and **secure**. The root route issue is fixed, environment variables are properly loaded, and all critical security features are in place.

### Next Steps:
1. Go to Railway.app
2. Click "New Project"
3. Connect your GitHub repo
4. Add PostgreSQL
5. Set environment variables (copy from above)
6. Deploy!

Your app will be live at `https://your-app.up.railway.app` and then at `https://anticip.store` once DNS is configured.

---

## 📝 Quick Reference

**GitHub Repo:** `stephencoan8/anticip`
**Branch:** `main`
**Entry Point:** `wsgi.py` (via Procfile)
**Python Version:** See `runtime.txt`
**Web Server:** Gunicorn (production-ready)

**Required Services:**
- Web Service (your Flask app)
- PostgreSQL Database

**Environment Variables:** 3 required (SECRET_KEY, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)
