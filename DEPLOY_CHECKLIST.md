# 🚀 QUICK DEPLOYMENT CHECKLIST

## ✅ Completed Locally

- [x] Database migrated (440 records backed up)
- [x] Code updated (app.py, templates, scripts)
- [x] Tests passed (no errors)
- [x] Git committed (7042923)
- [x] Pushed to GitHub

## ⏳ Railway Deployment

### Auto-Deploy
- [ ] Railway will auto-deploy from GitHub push
- [ ] Wait for build to complete (~2-3 minutes)

### Run Migration on Railway
Choose ONE option:

#### Option A: Railway CLI
```bash
railway run python migrate_remove_price.py
# Type "yes" when prompted
```

#### Option B: Railway Dashboard Console
```bash
python migrate_remove_price.py
# Type "yes" when prompted
```

#### Option C: Direct SQL (Railway Database Console)
```sql
ALTER TABLE bets RENAME COLUMN avg_price TO avg_popularity;
ALTER TABLE transactions RENAME COLUMN price_per_share TO popularity_per_share;
```

### Verify
- [ ] Visit live app URL
- [ ] Check artist list shows "Popularity"
- [ ] Test buy transaction
- [ ] Test sell transaction
- [ ] Check portfolio displays correctly
- [ ] Verify feed shows transactions

## 🎯 That's It!

**Time estimate:** 5-10 minutes total

**If issues occur:**
- Migration creates automatic backups
- Old "price" column is kept (not dropped)
- Safe rollback available if needed

---

**Questions?** Check DEPLOYMENT_SUMMARY.md for details.
