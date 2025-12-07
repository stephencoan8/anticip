# Railway Deployment Checklist ✅

## Pre-Deployment Verification

- [x] All code committed and pushed to GitHub
- [x] `.env` is excluded from git (in `.gitignore`)
- [x] `Procfile` configured for production
- [x] `requirements.txt` up to date
- [x] `runtime.txt` specifies Python 3.12.0
- [x] Security fixes implemented
- [x] Rate limiting enabled
- [x] Error handling in place
- [x] Health check endpoint available (`/health`)

## Railway Deployment Steps

### 1. Create Railway Project

1. Go to https://railway.app
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose: `stephencoan8/anticip`
5. Railway will auto-detect Python app

### 2. Configure Environment Variables

In Railway Dashboard → Variables, add these:

#### Required Variables

```bash
SECRET_KEY=<generate-using-command-below>
SPOTIFY_CLIENT_ID=<from-spotify-developer-dashboard>
SPOTIFY_CLIENT_SECRET=<from-spotify-developer-dashboard>
FLASK_ENV=production
DATABASE_URL=sqlite:///anticip.db
ADMIN_USERNAME=admin
ADMIN_PASSWORD=<create-strong-password>
```

#### Generate SECRET_KEY

Run locally or in Railway shell:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

#### Optional Performance Variables

```bash
WEB_CONCURRENCY=4
MAX_REQUESTS=1000
MAX_REQUESTS_JITTER=50
TIMEOUT=120
RATE_LIMIT_ENABLED=true
LOG_LEVEL=INFO
```

### 3. Spotify API Setup

1. Go to https://developer.spotify.com/dashboard
2. Create an app or use existing one
3. Copy **Client ID** and **Client Secret**
4. Add Railway URL to **Redirect URIs** (after deployment)

### 4. Deploy

1. Click **"Deploy"** in Railway
2. Monitor build logs for errors
3. Wait for deployment to complete (~2-3 minutes)
4. Railway will provide a public URL

### 5. Verify Deployment

1. Visit your Railway URL: `https://your-app.railway.app`
2. Check health endpoint: `https://your-app.railway.app/health`
3. Expected response:
   ```json
   {
     "status": "healthy",
     "database": "connected",
     "timestamp": "2024-01-01T00:00:00Z"
   }
   ```

### 6. Initialize Application

1. Access the Railway URL
2. Register first user or login with admin credentials
3. Add artists via admin panel:
   - Navigate to `/admin` (if admin)
   - Or run seed script in Railway shell:
     ```bash
     python seed_artists.py
     ```

### 7. Setup Automated Tasks

For regular popularity updates:

**Option A: Railway Cron (Recommended)**
1. In Railway Dashboard → Settings
2. Add a Cron Job:
   - Command: `python update_popularity.py`
   - Schedule: `0 */6 * * *` (every 6 hours)

**Option B: External Cron Service**
1. Use a service like cron-job.org or EasyCron
2. Schedule GET request to: `https://your-app.railway.app/update-popularity`
3. Add authentication if needed

### 8. Post-Deployment Configuration

1. **Custom Domain** (Optional):
   - Railway Settings → Domains
   - Add your custom domain
   - Update DNS records as shown

2. **SSL Certificate**:
   - Railway provides automatic HTTPS
   - Verify secure cookies are working

3. **Monitoring**:
   - Set up Railway alerting
   - Consider adding Sentry for error tracking

4. **Database Backups**:
   - Railway doesn't auto-backup SQLite
   - Schedule periodic backups via script
   - Consider PostgreSQL for production

## Troubleshooting

### Build Fails

**Issue**: `No module named 'flask_limiter'`
- **Solution**: Ensure `requirements.txt` includes `Flask-Limiter==3.5.0`
- Redeploy after fixing

**Issue**: `Python version not found`
- **Solution**: Check `runtime.txt` has `python-3.12.0`

### Runtime Errors

**Issue**: `SECRET_KEY not set`
- **Solution**: Add `SECRET_KEY` to Railway environment variables
- Redeploy after adding

**Issue**: `Database locked`
- **Solution**: SQLite has concurrency limits
- Consider upgrading to PostgreSQL for production:
  ```bash
  # Add to requirements.txt
  psycopg2-binary==2.9.9
  
  # Update DATABASE_URL in Railway
  DATABASE_URL=postgresql://user:pass@host:5432/dbname
  ```

**Issue**: Rate limit errors
- **Solution**: Adjust limits in `app.py` or disable temporarily:
  ```bash
  RATE_LIMIT_ENABLED=false
  ```

### Spotify API Issues

**Issue**: `Invalid client credentials`
- **Solution**: Verify `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET`
- Check Spotify Developer Dashboard

**Issue**: `Redirect URI mismatch`
- **Solution**: Add Railway URL to Spotify app settings
- Format: `https://your-app.railway.app/callback`

## Monitoring Checklist

After deployment, monitor these:

- [ ] Application logs (Railway dashboard)
- [ ] Health check endpoint returns 200
- [ ] User registration works
- [ ] Login works (with rate limiting)
- [ ] Artist pages load
- [ ] Buy/sell transactions work
- [ ] Portfolio updates correctly
- [ ] Admin panel accessible
- [ ] Database queries performing well

## Performance Optimization

### If experiencing slow response times:

1. **Enable Database Indexes** (already done):
   ```sql
   -- Verify indexes exist
   SELECT name FROM sqlite_master WHERE type='index';
   ```

2. **Increase Workers**:
   ```bash
   WEB_CONCURRENCY=8  # Railway variable
   ```

3. **Add Caching** (future enhancement):
   - Install Redis on Railway
   - Cache Spotify API responses
   - Cache portfolio calculations

4. **Upgrade Database**:
   - Move to Railway PostgreSQL
   - Better concurrency handling
   - Built-in backups

## Scaling Considerations

### Current Architecture Limits:
- **SQLite**: Good for <100 concurrent users
- **Gunicorn**: Handles multiple workers
- **Railway**: Auto-scales within plan limits

### When to Scale:
- **>100 concurrent users**: Upgrade to PostgreSQL
- **>1000 users**: Add Redis caching
- **>10,000 users**: Consider microservices architecture

## Security Post-Deployment

- [ ] Verify HTTPS is enabled (Railway does this automatically)
- [ ] Test rate limiting on `/login` endpoint
- [ ] Confirm `.env` is not exposed
- [ ] Check security headers in responses
- [ ] Review application logs for suspicious activity
- [ ] Setup log monitoring/alerting

## Support Resources

- **Railway Docs**: https://docs.railway.app
- **Railway Discord**: https://discord.gg/railway
- **Spotify API Docs**: https://developer.spotify.com/documentation/web-api
- **Flask Docs**: https://flask.palletsprojects.com

## Quick Reference Commands

### Railway CLI (Optional)

Install Railway CLI:
```bash
npm install -g @railway/cli
```

Login and link project:
```bash
railway login
railway link
```

View logs:
```bash
railway logs
```

Run commands in Railway environment:
```bash
railway run python update_popularity.py
```

Open Railway shell:
```bash
railway shell
```

### Local Development

Run locally with production settings:
```bash
FLASK_ENV=production python app.py
```

Test with Gunicorn locally:
```bash
gunicorn wsgi:app --workers 4 --bind 0.0.0.0:8000
```

## Success Criteria

Your deployment is successful when:

✅ Health check returns 200 OK
✅ Users can register and login
✅ Artists display with Spotify data
✅ Buy/sell transactions process correctly
✅ Portfolio values update accurately
✅ Admin panel is accessible
✅ No errors in Railway logs
✅ Response times <2 seconds
✅ Rate limiting prevents abuse

---

**Repository**: https://github.com/stephencoan8/anticip
**Status**: Ready for Railway deployment
**Last Updated**: 2024

Happy deploying! 🚀
