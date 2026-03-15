# 🚀 UPDATED - Setup with Database

## Major Updates:

✅ **SQLite Database** - Persistent user storage  
✅ **User-Matrix Mapping** - Each user mapped to matrix user ID  
✅ **10 Demo Users** - Pre-created with existing data  
✅ **Fixed Recommendations** - No more JSON errors  
✅ **Interaction Tracking** - Stored in database  

---

## 🎯 Quick Setup (3 Steps)

### Step 1: Initialize Database

```bash
# Run the database initialization script
python init_db.py
```

You should see:
```
✅ Created user: demo (matrix_user_id: 0)
✅ Created user: alice (matrix_user_id: 1)
✅ Created user: bob (matrix_user_id: 2)
...

📊 Total users in database: 10

User List:
------------------------------------------------------------
DB ID:   1 | Username: demo       | Matrix ID:    0 | Email: demo@example.com
DB ID:   2 | Username: alice      | Matrix ID:    1 | Email: alice@example.com
DB ID:   3 | Username: bob        | Matrix ID:    2 | Email: bob@example.com
...
```

### Step 2: Start the Server

```bash
python app.py
```

You should see:
```
✅ Loaded model config
✅ Loaded 500 items
✅ Loaded recommendation model: NMF
✅ Loaded user-item matrix: (1000, 500)
 * Running on http://127.0.0.1:5000
```

### Step 3: Test Everything

Open `test.html` in your browser and test all endpoints!

---

## 🔑 Demo User Accounts

| Username | Password | Matrix User ID | Has Interaction Data |
|----------|----------|----------------|---------------------|
| demo | demo123 | 0 | ✅ Yes |
| alice | password | 1 | ✅ Yes |
| bob | password | 2 | ✅ Yes |
| charlie | password | 3 | ✅ Yes |
| david | password | 4 | ✅ Yes |
| eve | password | 5 | ✅ Yes |
| frank | password | 6 | ✅ Yes |
| grace | password | 7 | ✅ Yes |
| henry | password | 8 | ✅ Yes |
| iris | password | 9 | ✅ Yes |

All demo users are mapped to existing users in your 1000×500 user-item matrix, so they have real interaction history and will get personalized recommendations!

---

## 🗄️ Database Schema

### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    matrix_user_id INTEGER  -- Maps to row in user-item matrix
)
```

### Sessions Table
```sql
CREATE TABLE sessions (
    token TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    expires TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
)
```

### Interactions Table
```sql
CREATE TABLE interactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    rating REAL NOT NULL,
    timestamp TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
)
```

---

## 🎯 How User-Matrix Mapping Works

### Registration:
1. New user registers
2. Gets next available `matrix_user_id` (0-999)
3. Recommendations use this matrix row

### Existing Users:
- Demo users (0-9) → Use matrix rows 0-9
- They have **real interaction data** from your matrix
- Get **personalized recommendations** immediately

### New Users:
- Users 10+ → Get next available matrix ID
- Start with popular items
- Build personalization as they interact

---

## 🧪 Testing the Fixes

### Test 1: Health Check
```bash
curl http://localhost:5000/health | python -m json.tool
```

Expected:
```json
{
  "status": "healthy",
  "models_loaded": true,
  "registered_users": 10,
  "database": "connected"
}
```

### Test 2: Login as Demo User
```bash
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"demo","password":"demo123"}' | python -m json.tool
```

Expected:
```json
{
  "message": "Login successful",
  "user": {
    "user_id": 1,
    "username": "demo",
    "email": "demo@example.com",
    "matrix_user_id": 0
  },
  "token": "..."
}
```

### Test 3: Get Recommendations
```bash
# Save token from login
TOKEN="your-token-here"

curl http://localhost:5000/api/recommendations \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
```

Expected:
```json
{
  "user_id": 1,
  "username": "demo",
  "matrix_user_id": 0,
  "recommendations": [
    {
      "item_id": 42,
      "name": "Product 42",
      "category": "Electronics",
      "price": 299.99,
      "predicted_score": 0.876
    },
    ...
  ],
  "algorithm": "NMF Collaborative Filtering"
}
```

**Key**: Check for `predicted_score` - it should be a valid number, not `-Infinity`!

---

## ✅ What's Fixed

### 1. **JSON Error Fixed**
- **Problem**: `-Infinity` values in JSON
- **Solution**: Filter out infinite scores before returning

### 2. **User Mapping**
- **Problem**: New users had no matrix data
- **Solution**: `matrix_user_id` field maps DB users to matrix rows

### 3. **Persistent Storage**
- **Problem**: Data lost on restart
- **Solution**: SQLite database stores everything

### 4. **Interaction Tracking**
- **Problem**: Not persisted
- **Solution**: Stored in database + updates matrix

---

## 📁 File Changes

### New Files:
- `init_db.py` - Database initialization script
- `ecommerce.db` - SQLite database (created on first run)
- `DATABASE_SETUP.md` - This file

### Updated Files:
- `app.py` - Now uses SQLite instead of in-memory storage

### Unchanged:
- `index.html` - Frontend works the same
- Model files (*.pkl, *.npz) - No changes needed

---

## 🔄 Migration from Old Version

If you were using the old in-memory version:

1. **Stop the server**
2. **Run init_db.py** to create database
3. **Restart the server**
4. **Old sessions lost** (users need to login again)
5. **Everything else works the same**

---

## 🚀 Deployment to Railway

The database will be created automatically on first run. No special setup needed!

Just make sure to include `init_db.py` in your deployment files.

Optional: For production, you can pre-populate the database:
```bash
# On Railway, run once after deployment
railway run python init_db.py
```

---

## 🐛 Troubleshooting

### "Database is locked"
- Only one connection at a time
- Restart the server

### "User not found"
- Run `init_db.py` again
- Check `ecommerce.db` exists

### "No such table"
- Database not initialized
- Run `init_db.py`

### Still getting JSON errors?
- Check server logs for traceback
- Verify `predicted_score` is not `-inf`
- Make sure user has `matrix_user_id`

---

## 📊 Database Management

### View all users:
```bash
sqlite3 ecommerce.db "SELECT id, username, matrix_user_id FROM users;"
```

### View all sessions:
```bash
sqlite3 ecommerce.db "SELECT token, user_id, expires FROM sessions;"
```

### View interactions:
```bash
sqlite3 ecommerce.db "SELECT * FROM interactions LIMIT 10;"
```

### Reset database:
```bash
rm ecommerce.db
python init_db.py
```

---

## ✅ Success Checklist

After setup, verify:

- [ ] `ecommerce.db` file exists
- [ ] 10 demo users in database
- [ ] Server starts without errors
- [ ] Health check shows 10 registered users
- [ ] Can login as demo/demo123
- [ ] Recommendations return valid scores (no -Infinity)
- [ ] Popular products display
- [ ] All products catalog works
- [ ] Interactions are tracked

---

**Status**: ✅ DATABASE READY  
**Version**: 2.1  
**Database**: SQLite with 10 demo users  
**Ready for**: February 10 deployment
