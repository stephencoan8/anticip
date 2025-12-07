# PRODUCTION DEPLOYMENT - Column Name Fix

**Date:** 2025-12-07  
**Target:** anticip.store (Railway)  
**Priority:** 🔴 CRITICAL - Fixes app-breaking error

---

## 🐛 Problem Being Fixed

Users getting error on anticip.store:
```
Database error: column "avg_popularity" does not exist
```

This error appears when clicking into any page (portfolio, artist details, etc.)

---

## ✅ Root Cause Identified

**Backend/Template Mismatch:**
- Database had correct column: `avg_popularity` ✅
- Backend was using wrong dictionary keys: `avg_price`, `current_price` ❌
- Templates expected the wrong keys: `avg_price`, `current_price` ❌

---

## 🔧 Changes Being Deployed

### 1. **app.py** - Portfolio Route (Line ~1103)
Changed holding dictionary to use correct keys:
```python
# BEFORE (❌ Wrong)
holding = {
    'avg_price': avg_popularity,
    'current_price': current_popularity,
    ...
}

# AFTER (✅ Correct)
holding = {
    'avg_popularity': avg_popularity,
    'current_popularity': current_popularity,
    ...
}
```

### 2. **templates/portfolio.html** - Display Values
Changed template references:
```html
<!-- BEFORE (❌ Wrong) -->
{{ holding.avg_price }}
{{ holding.current_price }}

<!-- AFTER (✅ Correct) -->
{{ holding.avg_popularity }}
{{ holding.current_popularity }}
```

### 3. **railway_migrate.py** - NEW
Auto-migration script that runs on Railway deployment:
- Checks if database has correct schema
- Renames `avg_price` → `avg_popularity` if needed
- Ensures smooth deployment

### 4. **railway.json** - Updated
Added migration step to startup command:
```json
"startCommand": "python railway_migrate.py && gunicorn ..."
```

---

## 📦 Files Changed in This Deployment

- ✅ `app.py` - Fixed portfolio route dictionary keys
- ✅ `templates/portfolio.html` - Fixed template variable references  
- ✅ `railway_migrate.py` - NEW: Auto-migration script
- ✅ `railway.json` - Added migration to startup
- ✅ `COLUMN_NAME_FIX.md` - Documentation
- ✅ `RAILWAY_DEPLOY.md` - This file

---

## 🚀 Deployment Steps

### Automatic (Railway):
1. Push to GitHub (main branch)
2. Railway auto-detects changes
3. Runs migration script (`railway_migrate.py`)
4. Starts Gunicorn with updated code
5. App should be live with fixes

### Git Commands:
```bash
git add -A
git commit -m "Production fix: Column name consistency + Railway migration"
git push origin main
```

---

## ✅ Expected Results After Deploy

- ✅ No more "column does not exist" errors
- ✅ Portfolio page loads correctly
- ✅ Artist detail pages work
- ✅ Holdings display avg/current popularity correctly
- ✅ All database queries succeed

---

## 🧪 Testing Checklist (Post-Deploy)

Visit https://anticip.store and test:

- [ ] Login works
- [ ] Navigate to portfolio page - should load without errors
- [ ] Click on any artist - should show details without errors
- [ ] View holdings - should display avg/current popularity
- [ ] Check feed - should load properly
- [ ] Try buying/selling shares - should work correctly

---

## 🔄 Rollback Plan

If deployment fails:
```bash
git revert HEAD
git push origin main
```

Railway will auto-deploy the previous version.

---

## 📊 Deployment Timeline

- **Code Fixed:** 2025-12-07 14:00 PST
- **Committed to Git:** 2025-12-07 14:01 PST (commit: bc61214)
- **Migration Added:** 2025-12-07 14:17 PST
- **Ready to Deploy:** NOW
- **Expected Deploy Time:** ~2-3 minutes after push

---

## 🎯 Success Criteria

Deploy is successful when:
1. Railway build completes without errors
2. Migration script runs successfully  
3. App starts and responds to requests
4. No "column does not exist" errors in logs
5. Users can access portfolio and artist pages

---

## 📝 Related Documentation

- `COLUMN_NAME_FIX.md` - Technical details of the fix
- `BETA_CLEANUP_COMPLETE.md` - Original database migration
- `DATABASE_ERROR_FIX.md` - Previous troubleshooting
- `PRICE_METRIC_REMOVED.md` - Original migration plan

---

## ⚠️ Notes

- Migration is **idempotent** - safe to run multiple times
- If database already has `avg_popularity`, migration skips
- Zero downtime - Railway handles graceful restart
- All users logged in will stay logged in

---

**Status:** 🟢 READY TO DEPLOY  
**Git Commit:** bc61214 + new changes  
**Deploy Method:** `git push origin main`

---

*Prepared: December 7, 2025*  
*Priority: P0 - Critical Bug Fix*
