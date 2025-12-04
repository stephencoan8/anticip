# Artist Popularity Auto-Update Setup

This guide explains how to set up automatic daily updates of artist popularity scores from Spotify.

## What Gets Updated

The `update_popularity.py` script:
- Fetches current popularity scores for all artists in your database from Spotify API
- Inserts new price history entries with updated popularity
- Runs safely with rate limiting to respect Spotify API limits
- Provides detailed logs of the update process

## Setup Options

### Option 1: GitHub Actions (Recommended - Free & Easy)

GitHub Actions will run the update automatically every day at 6 AM UTC.

#### Setup Steps:

1. **Add Secrets to GitHub Repository:**
   - Go to your GitHub repo: https://github.com/stephencoan8/anticip
   - Click **Settings** → **Secrets and variables** → **Actions**
   - Click **"New repository secret"** and add:
     - `DATABASE_URL`: Your Railway PostgreSQL URL
     - `SPOTIFY_CLIENT_ID`: Your Spotify client ID
     - `SPOTIFY_CLIENT_SECRET`: Your Spotify client secret

2. **Push the workflow file:**
   ```bash
   git add .github/workflows/daily-update.yml update_popularity.py
   git commit -m "Add daily popularity auto-update"
   git push
   ```

3. **Verify it's scheduled:**
   - Go to your repo → **Actions** tab
   - You should see "Daily Artist Popularity Update" workflow
   - Click on it to see the schedule

4. **Test manually (optional):**
   - Go to **Actions** → **Daily Artist Popularity Update**
   - Click **"Run workflow"** → **"Run workflow"**
   - Watch it execute in real-time

### Option 2: Railway Cron Jobs (Requires Railway Pro)

Railway Pro plan ($20/month) includes cron job support.

#### Setup Steps:

1. In your Railway project dashboard:
   - Click **"+ New"** → **"Cron Job"**
   - Select your repository
   - Set schedule: `0 6 * * *` (daily at 6 AM UTC)
   - Set command: `python update_popularity.py`

2. The same environment variables from your web service will be used automatically

### Option 3: Manual Running

You can run the update script manually anytime:

#### Locally (against production):
```bash
# Set environment variables temporarily
export DATABASE_URL="your_railway_database_url"
export SPOTIFY_CLIENT_ID="your_client_id"
export SPOTIFY_CLIENT_SECRET="your_client_secret"

# Run the script
python update_popularity.py
```

#### On Railway (via CLI):
```bash
railway run python update_popularity.py
```

## Schedule Details

**Current Schedule: Daily at 6 AM UTC**

- 6:00 AM UTC
- 2:00 AM EST
- 11:00 PM PST (previous day)
- 1:00 AM CST

You can adjust the schedule in `.github/workflows/daily-update.yml`:
```yaml
schedule:
  - cron: '0 6 * * *'  # Change this line
```

Cron format: `minute hour day month day-of-week`
Examples:
- `0 6 * * *` - Daily at 6 AM UTC
- `0 */6 * * *` - Every 6 hours
- `0 0 * * 1` - Every Monday at midnight
- `0 12 * * *` - Daily at noon UTC

## Monitoring

### GitHub Actions:
- View logs: Repo → **Actions** → Click on a workflow run
- Email notifications: GitHub will email you if the workflow fails
- Enable notifications: Settings → Notifications → Actions

### Check Last Update:
Query your database to see the latest update:
```sql
SELECT spotify_id, name, popularity, price, timestamp 
FROM artist_history 
ORDER BY timestamp DESC 
LIMIT 10;
```

## Troubleshooting

### Workflow Fails
1. Check GitHub Actions logs for error messages
2. Verify secrets are set correctly in GitHub
3. Ensure DATABASE_URL is accessible from GitHub's servers
4. Check Spotify API rate limits haven't been exceeded

### Database Connection Issues
- Verify DATABASE_URL secret is correct
- Ensure Railway database is public-facing (not private network only)
- Check Railway database is running

### Spotify API Errors
- Verify Spotify credentials are valid
- Check you haven't exceeded API rate limits (rare with proper rate limiting)
- Ensure Spotify Developer app is active

## Cost & Rate Limits

### GitHub Actions (Free Tier):
- 2,000 minutes/month of workflow runtime
- This script takes ~2-5 minutes for 100 artists
- Daily runs = ~150 minutes/month (well within free tier)

### Spotify API:
- Rate limit: ~180 requests/minute
- Script uses 0.3s delay = ~3 requests/second = 180/minute (at the limit)
- For 100+ artists, the script takes ~30-60 seconds

### Railway Database:
- No additional cost for database connections
- Minimal data storage impact (a few KB per day)

## Data Retention

Artist history grows over time. To manage database size:

### Check history size:
```sql
SELECT COUNT(*) FROM artist_history;
SELECT pg_size_pretty(pg_total_relation_size('artist_history'));
```

### Optional cleanup (keep last 365 days):
```sql
DELETE FROM artist_history 
WHERE timestamp < NOW() - INTERVAL '365 days';
```

## Next Steps

1. ✅ Set up GitHub Actions secrets
2. ✅ Push workflow file to GitHub
3. ✅ Test manual workflow run
4. 📊 Monitor daily updates in Actions tab
5. 📈 Add popularity trend charts to your app UI (future enhancement)

---

**Questions?** Check logs in GitHub Actions or Railway dashboard!
