# anticip Deployment Guide

This guide will walk you through deploying the anticip app to Railway and connecting your anticip.store domain.

## Prerequisites

- [x] GitHub account
- [x] Railway account (sign up at https://railway.app)
- [x] anticip.store domain purchased via Squarespace
- [x] Spotify Developer credentials

## Step 1: Prepare Your Repository

### 1.1 Create a GitHub Repository

1. Go to https://github.com/new
2. Create a new repository named `anticip`
3. Keep it **public** (required for Railway free tier)
4. Don't initialize with README (we already have one)

### 1.2 Push Code to GitHub

Run these commands in your terminal from the `/Users/stephencoan/anticip` directory:

```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Commit
git commit -m "Initial deployment setup for anticip.store"

# Add your GitHub repository as remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/anticip.git

# Push to GitHub
git branch -M main
git push -u origin main
```

## Step 2: Set Up Railway

### 2.1 Create New Project

1. Go to https://railway.app
2. Click **"Start a New Project"**
3. Select **"Deploy from GitHub repo"**
4. Authorize Railway to access your GitHub account
5. Select your `anticip` repository

### 2.2 Add PostgreSQL Database

1. In your Railway project, click **"+ New"**
2. Select **"Database"**
3. Choose **"PostgreSQL"**
4. Railway will automatically provision a PostgreSQL database

### 2.3 Configure Environment Variables

1. Click on your web service (not the database)
2. Go to the **"Variables"** tab
3. Click **"+ New Variable"** and add the following:

```
SPOTIFY_CLIENT_ID=your_spotify_client_id_here
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret_here
SECRET_KEY=your_random_secret_key_here
FLASK_ENV=production
```

**Important Notes:**
- Get your Spotify credentials from https://developer.spotify.com/dashboard
- Generate a random SECRET_KEY (you can use: `python -c 'import os; print(os.urandom(24).hex())'`)
- **DATABASE_URL** is automatically set by Railway when you add PostgreSQL - don't add it manually!

### 2.4 Deploy

1. Railway will automatically deploy when you push to GitHub
2. Wait for the build to complete (check the **"Deployments"** tab)
3. Once deployed, click **"Settings"** → **"Generate Domain"** to get a Railway URL
4. Test your app at the Railway URL (e.g., `your-app.up.railway.app`)

## Step 3: Initialize Database Schema

After your first deployment:

1. In Railway, click on your PostgreSQL database
2. Go to the **"Data"** tab or **"Connect"** tab
3. Click **"Connect"** and copy the connection command
4. Run the connection command in your local terminal
5. The app will automatically create tables on first connection, OR
6. You can manually run your SQL schema if needed

**Note:** The app creates tables automatically on startup via the `CREATE TABLE IF NOT EXISTS` statements in `app.py`.

## Step 4: Connect Your Domain (anticip.store)

### 4.1 Get Railway Domain Info

1. In Railway, go to your web service
2. Click **"Settings"**
3. Scroll to **"Domains"**
4. Click **"+ Custom Domain"**
5. Enter `anticip.store`
6. Railway will show you the CNAME record you need to add

### 4.2 Configure DNS in Squarespace

1. Log in to your Squarespace account
2. Go to **Domains** → **anticip.store**
3. Click **"DNS Settings"** or **"Advanced Settings"**
4. Add a new **CNAME record**:
   - **Host/Name:** `www`
   - **Value/Points to:** The Railway CNAME (e.g., `your-app.up.railway.app`)
   - **TTL:** 3600 (or leave default)

5. Add an **A record** for the root domain (if Squarespace allows):
   - **Host/Name:** `@`
   - **Value:** Railway's IP address (Railway will provide this)
   
   **OR** add a **redirect** from `anticip.store` to `www.anticip.store`

### 4.3 Wait for DNS Propagation

- DNS changes can take 24-48 hours to fully propagate
- You can check status at: https://www.whatsmydns.net
- Test both `anticip.store` and `www.anticip.store`

## Step 5: Enable SSL/HTTPS

1. In Railway, go to your web service **"Settings"**
2. Under **"Domains"**, Railway automatically provisions SSL certificates
3. Wait a few minutes for the certificate to be issued
4. Your site will automatically redirect HTTP to HTTPS

## Step 6: Set Up Continuous Deployment

Railway automatically redeploys when you push to GitHub:

```bash
# Make changes to your code
git add .
git commit -m "Your change description"
git push

# Railway will automatically detect the push and redeploy
```

## Monitoring & Maintenance

### View Logs
1. In Railway, click on your web service
2. Go to **"Deployments"**
3. Click on a deployment to view logs

### Database Backups
1. Railway Pro plan includes automatic backups
2. Free tier: manually export data periodically from the **"Data"** tab

### Scaling
- Railway auto-scales based on traffic
- Monitor usage in the **"Metrics"** tab
- Upgrade to Pro if you exceed free tier limits

## Troubleshooting

### Build Fails
- Check **"Deployments"** tab for error messages
- Verify `requirements.txt` includes all dependencies
- Ensure Python version in `runtime.txt` is supported

### Database Connection Issues
- Verify `DATABASE_URL` is set automatically by Railway
- Check PostgreSQL service is running
- Review connection logs

### Domain Not Working
- Verify DNS settings in Squarespace
- Check Railway domain configuration
- Wait for DNS propagation (up to 48 hours)
- Use `dig anticip.store` or `nslookup anticip.store` to check DNS

### App Crashes
- Check logs in Railway **"Deployments"** tab
- Verify all environment variables are set
- Test locally first with `gunicorn app:app`

## Cost Estimates

### Railway Free Tier
- $5 worth of free usage per month
- ~500 hours of runtime
- 1GB storage
- Upgrades available as needed

### Domain
- anticip.store: ~$15-20/year via Squarespace

## Next Steps

Once deployed:
1. ✅ Test all features (login, portfolio, trading, admin)
2. ✅ Monitor initial user signups
3. 📱 Plan modern frontend migration (Next.js/React)
4. 🎨 Design new UI in Figma
5. 📈 Add analytics (Google Analytics, PostHog, etc.)

## Support

- Railway: https://docs.railway.app
- Squarespace DNS: https://support.squarespace.com
- GitHub Issues: (create issues in your repo)

---

**Ready to deploy? Start with Step 1!**
