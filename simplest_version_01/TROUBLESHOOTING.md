# 🔧 Troubleshooting Guide - Popular Products Issue

## Issue: Popular Products Not Showing

### ✅ FIXED IN LATEST VERSION

The issue has been resolved. Popular products now display **before login** and are always visible.

---

## What Was Fixed:

### 1. **UI Layout Change**
- **Before**: Popular products were inside `mainContent` (hidden when not logged in)
- **After**: Popular products are now outside `mainContent` (always visible)

### 2. **Loading Order**
- **Before**: Popular products only loaded after authentication
- **After**: Popular products load immediately on page load

### 3. **Better Error Handling**
- Added detailed error messages
- Shows API URL in error state
- Console logging for debugging

---

## Testing the Fix:

### Option 1: Use Test Page (Easiest)

1. **Start your Flask server**:
   ```bash
   python app.py
   ```

2. **Open** `test.html` in your browser

3. **Click** "Test /api/popular" button

4. **You should see**:
   ```
   ✅ Found 6 popular products!
   
   1. Product 122 - $633.22 (Books)
      Popularity: 526
   2. Product 274 - $446.69 (Electronics)
      Popularity: 522
   ...
   ```

### Option 2: Use Main Interface

1. **Start server**: `python app.py`
2. **Open**: `index.html` in browser
3. **Popular products should load immediately** (no login required)
4. **After login**: You'll see personalized recommendations too

---

## Verify Files Are Updated:

Check that you have the latest `index.html`:

```bash
# Search for "Popular Products (always visible)"
grep "Popular Products (always visible)" index.html
```

Should return:
```
<!-- Popular Products (always visible) -->
```

---

## API Endpoint Test:

Test the API directly:

```bash
# Test popular products endpoint
curl http://localhost:5000/api/popular?n=5

# Expected response:
{
  "popular_products": [
    {
      "item_id": 122,
      "name": "Product 122",
      "category": "Books",
      "price": 633.22,
      "popularity_score": 526
    },
    ...
  ],
  "timestamp": "2025-02-08T..."
}
```

---

## Common Issues & Solutions:

### Issue 1: API URL Wrong
**Symptom**: "Failed to load popular products"  
**Solution**: Check API URL in the yellow box at top of page
- Local testing: `http://localhost:5000`
- Deployed: `https://your-app.railway.app`

### Issue 2: Server Not Running
**Symptom**: Connection refused error  
**Solution**: 
```bash
# Start the Flask server
cd /path/to/project
python app.py
```

### Issue 3: Port Already in Use
**Symptom**: "Address already in use"  
**Solution**:
```bash
# Kill process on port 5000
lsof -ti:5000 | xargs kill -9

# Or use different port
PORT=5001 python app.py
```

### Issue 4: Model Files Missing
**Symptom**: "Error loading models"  
**Solution**: Ensure these 4 files are in same directory as app.py:
- `item_metadata.pkl`
- `recommendation_model.pkl`
- `user_item_matrix.npz`
- `model_config.json`

### Issue 5: CORS Errors
**Symptom**: "Access-Control-Allow-Origin" errors  
**Solution**: Already configured in app.py with flask-cors

---

## Debug Mode:

### Enable Console Logging

Open browser Developer Tools (F12) → Console tab

You should see:
```
✅ Loaded model config
✅ Loaded 500 items
✅ Loaded recommendation model: NMF
✅ Loaded user-item matrix: (1000, 500)
```

### Check Network Tab

1. Open DevTools → Network tab
2. Reload page
3. Look for request to `/api/popular`
4. Status should be `200 OK`
5. Response should contain `popular_products` array

---

## Current Layout Order:

When you open the page (not logged in):

```
┌────────────────────────────────┐
│   API URL Configuration        │
├────────────────────────────────┤
│   Login/Register Forms         │
├────────────────────────────────┤
│   🔥 POPULAR PRODUCTS          │ ← Always visible!
│   (Loads automatically)        │
└────────────────────────────────┘
```

After login:

```
┌────────────────────────────────┐
│   User Info (Logout button)   │
├────────────────────────────────┤
│   🔥 POPULAR PRODUCTS          │ ← Still visible
├────────────────────────────────┤
│   🎯 RECOMMENDED FOR YOU       │ ← New!
├────────────────────────────────┤
│   📦 BROWSE ALL PRODUCTS       │ ← New!
└────────────────────────────────┘
```

---

## File Versions:

Make sure you're using the updated files:

### index.html - Version 2.0
- Popular products outside mainContent
- Loads immediately on page load
- Better error messages

### app.py - Version 2.0
- Loads your trained NMF model
- Handles 1000 users × 500 items
- Calculates popularity from user-item matrix

---

## Success Indicators:

✅ Popular products visible without login  
✅ Shows 6 products by default  
✅ Each product shows popularity score  
✅ Products are from your actual dataset  
✅ Categories: Clothing, Books, Electronics  

---

## Still Having Issues?

1. **Use test.html** to isolate the problem
2. **Check browser console** for JavaScript errors
3. **Check Flask terminal** for Python errors
4. **Verify API URL** matches your server
5. **Try a different browser** to rule out caching

---

## Expected Behavior:

```javascript
// On page load (index.html):
1. Load popular products immediately ✅
2. Check if user is logged in
3. If logged in:
   - Show user info
   - Load personalized recommendations
   - Load all products catalog
4. If not logged in:
   - Show login/register forms
   - Popular products still visible ✅
```

---

## Quick Test Command:

```bash
# One-line test
curl http://localhost:5000/api/popular | python -m json.tool

# Should show pretty-printed JSON with popular_products array
```

---

**Status**: ✅ FIXED  
**Version**: 2.0  
**Last Updated**: February 8, 2025
