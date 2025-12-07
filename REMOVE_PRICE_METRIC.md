# Remove Stock Price Metric - Use Only Popularity

## 🎯 Objective

Remove the redundant "stock price" metric from the app and use **only the popularity metric** for all artist valuations, trading, and portfolio calculations.

## 📊 Current State (Redundant)

The app currently maintains TWO metrics:
1. **Popularity** (0-100) - Direct from Spotify API
2. **Price** (calculated from popularity) - Redundant duplication

This creates:
- Database redundancy
- Code complexity
- User confusion
- Maintenance overhead

## ✅ Solution

**Use ONLY the Popularity metric (0-100)**

### Benefits:
- ✅ Simpler data model
- ✅ No redundant calculations
- ✅ Clearer user experience
- ✅ Direct Spotify integration
- ✅ Easier to understand

## 🗄️ Database Changes

### artist_history Table
**Before:**
```sql
CREATE TABLE artist_history (
    id SERIAL PRIMARY KEY,
    spotify_id VARCHAR(255),
    popularity INTEGER,
    price NUMERIC(10, 2),  -- ❌ REDUNDANT
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**After:**
```sql
CREATE TABLE artist_history (
    id SERIAL PRIMARY KEY,
    spotify_id VARCHAR(255),
    popularity INTEGER,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Other Tables (No Changes Needed)
- `bets.avg_price` → Rename to `avg_popularity`
- `transactions.price_per_share` → Rename to `popularity_per_share`

## 📝 Code Changes

### App.py Changes
Replace all references:
- `ah.price` → `ah.popularity`
- `price_per_share` → `popularity_per_share`
- `avg_price` → `avg_popularity`
- `current_price` → `current_popularity`

### Template Changes
Replace all display references:
- "Stock Price" → "Popularity"
- "Price" → "Popularity"
- "$X.XX" → "X pts" or "X/100"
- "Avg. Price" → "Avg. Popularity"
- "Current Price" → "Current Popularity"

## 🔄 Migration Strategy

1. **Add new columns** (popularity-based)
2. **Copy data** from price columns
3. **Update all queries** to use new columns
4. **Test thoroughly**
5. **Drop old columns** (price-based)

## 📦 Files to Update

- [x] `/app.py` - All queries and logic
- [x] `/templates/artists.html` - Artist list display
- [x] `/templates/artist_detail.html` - Artist detail page
- [x] `/templates/portfolio.html` - Portfolio holdings
- [x] `/templates/feed.html` - Transaction feed
- [x] `/update_popularity.py` - Popularity update script
- [x] Database migration script

## 🎨 UI/UX Changes

### Before:
```
Stock Price: $72.50
Avg. Price: $68.20
Current Price: $72.50
Value: $1,450.00
```

### After:
```
Popularity: 73/100
Avg. Popularity: 68/100
Current Popularity: 73/100
Value: 1,460 pts
```

## 🧪 Testing Checklist

- [ ] Artist list shows popularity correctly
- [ ] Artist detail shows popularity metrics
- [ ] Buy/sell transactions use popularity
- [ ] Portfolio shows popularity-based holdings
- [ ] Feed displays popularity correctly
- [ ] Charts use popularity values
- [ ] Admin refresh updates popularity

---

*This change will simplify the codebase and improve user understanding while maintaining all functionality.*
