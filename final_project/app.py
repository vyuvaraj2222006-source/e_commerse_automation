from flask import Flask, request, jsonify, session, g
from flask_cors import CORS
import pandas as pd
import numpy as np
import pickle
import json
import os
import sqlite3
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True
app.config['DATABASE'] = 'ecommerce.db'

CORS(app, supports_credentials=True, origins=['*'])

# ==================== DATABASE FUNCTIONS ====================

def get_db():
    """Get database connection"""
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    """Close database connection"""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """Initialize database tables"""
    db = get_db()
    cursor = db.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            matrix_user_id INTEGER
        )
    ''')
    
    # Create sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            expires TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create interactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            rating REAL NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    db.commit()

# Initialize database on startup
with app.app_context():
    init_db()

# ==================== MODEL LOADING ====================

class ModelLoader:
    def __init__(self):
        self.model = None
        self.item_metadata = None
        self.user_item_matrix = None
        self.config = None
        self.load_models()
    
    def load_models(self):
        """Load trained models and metadata"""
        try:
            # Load model config
            with open('model_config.json', 'r') as f:
                self.config = json.load(f)
            print(" Loaded model config")
            
            # Load item metadata
            with open('item_metadata.pkl', 'rb') as f:
                self.item_metadata = pickle.load(f)
            print(f" Loaded {len(self.item_metadata)} items")
            
            # Load recommendation model (NMF)
            with open('recommendation_model.pkl', 'rb') as f:
                self.model = pickle.load(f)
            print(f" Loaded recommendation model: {type(self.model).__name__}")
            
            # Load user-item matrix
            data = np.load('user_item_matrix.npz')
            self.user_item_matrix = data['matrix']
            print(f" Loaded user-item matrix: {self.user_item_matrix.shape}")
            
        except Exception as e:
            print(f" Error loading models: {e}")
            print("Using fallback mode")
            self.create_fallback_data()
    
    def create_fallback_data(self):
        """Create fallback data if models can't be loaded"""
        self.item_metadata = pd.DataFrame({
            'item_id': range(10),
            'name': [f'Product {i}' for i in range(10)],
            'category': ['Electronics', 'Clothing', 'Books'] * 3 + ['Home'],
            'price': np.random.uniform(10, 1000, 10)
        })
        self.user_item_matrix = np.random.rand(100, 10)

def get_product_image_url(item_id, category):
    """Generate product image URL based on category"""
    # Using placeholder image service with category-specific images
    category_mapping = {
        'Electronics': 'tech',
        'Clothing': 'fashion',
        'Books': 'books',
        'Home': 'home'
    }
    
    theme = category_mapping.get(category, 'product')
    # Using picsum.photos for random images with a seed based on item_id
    return f"https://picsum.photos/seed/{theme}{item_id}/400/300"

model_loader = ModelLoader()

# ==================== USER DATABASE FUNCTIONS ====================

def create_user(username, email, password):
    """Create a new user account"""
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Assign next available matrix_user_id
        cursor.execute('SELECT MAX(matrix_user_id) FROM users')
        result = cursor.fetchone()
        next_matrix_id = (result[0] or -1) + 1
        
        # Ensure matrix_user_id is within bounds
        if next_matrix_id >= model_loader.user_item_matrix.shape[0]:
            next_matrix_id = None  # Will use popular items fallback
        
        cursor.execute('''
            INSERT INTO users (username, email, password_hash, created_at, matrix_user_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, email, generate_password_hash(password), 
              datetime.now().isoformat(), next_matrix_id))
        
        db.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None

def authenticate_user(username, password):
    """Authenticate user credentials"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('SELECT id, password_hash FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    
    if user and check_password_hash(user[1], password):
        return user[0]
    return None

def get_user_by_id(user_id):
    """Get user data by ID"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT id, username, email, created_at, matrix_user_id 
        FROM users WHERE id = ?
    ''', (user_id,))
    
    user = cursor.fetchone()
    if user:
        return {
            'id': user[0],
            'username': user[1],
            'email': user[2],
            'created_at': user[3],
            'matrix_user_id': user[4]
        }
    return None

def get_user_by_username(username):
    """Get user data by username"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT id, username, email, created_at, matrix_user_id 
        FROM users WHERE username = ?
    ''', (username,))
    
    user = cursor.fetchone()
    if user:
        return {
            'id': user[0],
            'username': user[1],
            'email': user[2],
            'created_at': user[3],
            'matrix_user_id': user[4]
        }
    return None

def create_session(user_id):
    """Create a session token"""
    db = get_db()
    cursor = db.cursor()
    
    token = secrets.token_hex(32)
    expires = (datetime.now() + timedelta(days=7)).isoformat()
    
    cursor.execute('''
        INSERT INTO sessions (token, user_id, expires)
        VALUES (?, ?, ?)
    ''', (token, user_id, expires))
    
    db.commit()
    return token

def get_session(token):
    """Get session data from token"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT user_id, expires FROM sessions WHERE token = ?
    ''', (token,))
    
    session = cursor.fetchone()
    if session:
        expires = datetime.fromisoformat(session[1])
        if datetime.now() < expires:
            return {'user_id': session[0]}
    return None

def delete_session(token):
    """Delete a session"""
    db = get_db()
    cursor = db.cursor()
    cursor.execute('DELETE FROM sessions WHERE token = ?', (token,))
    db.commit()

def track_interaction_db(user_id, item_id, rating):
    """Track user interaction in database"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        INSERT INTO interactions (user_id, item_id, rating, timestamp)
        VALUES (?, ?, ?, ?)
    ''', (user_id, item_id, rating, datetime.now().isoformat()))
    
    db.commit()

def get_user_interactions(user_id):
    """Get all interactions for a user"""
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT item_id, rating, timestamp 
        FROM interactions 
        WHERE user_id = ?
        ORDER BY timestamp DESC
    ''', (user_id,))
    
    return cursor.fetchall()

# ==================== RECOMMENDATION ENGINE ====================

class RecommendationEngine:
    def __init__(self, model_loader):
        self.loader = model_loader
    
    def get_user_recommendations(self, user_id, matrix_user_id=None, n=10):
        """Get personalized recommendations using trained NMF model"""
        try:
            # Use matrix_user_id if provided, otherwise use user_id
            lookup_id = matrix_user_id if matrix_user_id is not None else user_id
            
            # Check if user exists in matrix
            if lookup_id is None or lookup_id >= self.loader.user_item_matrix.shape[0]:
                print(f"User {lookup_id} not in matrix, returning popular items")
                return self.get_popular_items(n)
            
            # Get user's latent factors from the trained model
            user_factors = self.loader.model.transform(
                self.loader.user_item_matrix[lookup_id:lookup_id+1]
            )
            
            # Get item factors
            item_factors = self.loader.model.components_
            
            # Calculate predicted ratings
            predicted_ratings = user_factors.dot(item_factors)[0]
            
            # Get user's already rated items
            rated_items = np.where(self.loader.user_item_matrix[lookup_id] > 0)[0]
            
            # Set already rated items to -inf so they won't be recommended
            predicted_ratings[rated_items] = -np.inf
            
            # Get top N recommendations
            top_indices = np.argsort(predicted_ratings)[::-1][:n]
            
            # Get item details
            recommendations = []
            for idx in top_indices:
                if idx < len(self.loader.item_metadata):
                    item = self.loader.item_metadata.iloc[idx]
                    score = float(predicted_ratings[idx])
                    
                    # Skip if score is -inf
                    if np.isinf(score):
                        continue
                    
                    recommendations.append({
                        'item_id': int(item['item_id']),
                        'name': str(item['name']),
                        'category': str(item['category']),
                        'price': float(item['price']),
                        'predicted_score': score,
                        'image_url': get_product_image_url(int(item['item_id']), str(item['category']))
                    })
            
            return recommendations
            
        except Exception as e:
            print(f"Error in recommendations: {e}")
            import traceback
            traceback.print_exc()
            return self.get_popular_items(n)
    
    def get_similar_items(self, item_id, n=5):
        """Get similar items based on item factors"""
        try:
            if self.loader.model is None:
                return self.get_items_by_category(item_id, n)
            
            item_factors = self.loader.model.components_
            
            if item_id >= item_factors.shape[1]:
                return []
            
            # Calculate cosine similarity
            item_vector = item_factors[:, item_id].reshape(1, -1)
            similarities = np.dot(item_factors.T, item_vector.T).flatten()
            
            # Set self-similarity to -inf
            similarities[item_id] = -np.inf
            
            # Get top N similar items
            top_indices = np.argsort(similarities)[::-1][:n]
            
            similar_items = []
            for idx in top_indices:
                if idx < len(self.loader.item_metadata):
                    item = self.loader.item_metadata.iloc[idx]
                    similar_items.append({
                        'item_id': int(item['item_id']),
                        'name': item['name'],
                        'category': item['category'],
                        'price': float(item['price']),
                        'similarity_score': float(similarities[idx]),
                        'image_url': get_product_image_url(int(item['item_id']), item['category'])
                    })
            
            return similar_items
            
        except Exception as e:
            print(f"Error in similar items: {e}")
            return self.get_items_by_category(item_id, n)
    
    def get_items_by_category(self, item_id, n=5):
        """Fallback: Get items from same category"""
        if item_id >= len(self.loader.item_metadata):
            return []
        
        item = self.loader.item_metadata.iloc[item_id]
        category = item['category']
        
        similar = self.loader.item_metadata[
            (self.loader.item_metadata['category'] == category) &
            (self.loader.item_metadata['item_id'] != item_id)
        ].head(n)
        
        return similar.to_dict('records')
    
    def get_popular_items(self, n=10):
        """Get popular items based on interaction counts"""
        try:
            # Calculate popularity from user-item matrix
            popularity = self.loader.user_item_matrix.sum(axis=0)
            top_indices = np.argsort(popularity)[::-1][:n]
            
            popular_items = []
            for idx in top_indices:
                if idx < len(self.loader.item_metadata):
                    item = self.loader.item_metadata.iloc[idx]
                    popular_items.append({
                        'item_id': int(item['item_id']),
                        'name': item['name'],
                        'category': item['category'],
                        'price': float(item['price']),
                        'popularity_score': float(popularity[idx]),
                        'image_url': get_product_image_url(int(item['item_id']), item['category'])
                    })
            
            return popular_items
            
        except Exception as e:
            print(f"Error getting popular items: {e}")
            return self.loader.item_metadata.head(n).to_dict('records')

engine = RecommendationEngine(model_loader)

# ==================== API ENDPOINTS ====================

@app.route('/')
def home():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    user_count = cursor.fetchone()[0]
    
    return jsonify({
        "message": "E-Commerce Recommendation API with User Authentication",
        "version": "2.0",
        "model_info": {
            "type": model_loader.config.get('model_type') if model_loader.config else "unknown",
            "n_users": model_loader.user_item_matrix.shape[0] if model_loader.user_item_matrix is not None else 0,
            "n_items": len(model_loader.item_metadata) if model_loader.item_metadata is not None else 0
        },
        "database": {
            "registered_users": user_count,
            "type": "SQLite"
        },
        "endpoints": {
            "auth": ["/api/register", "/api/login", "/api/logout", "/api/me"],
            "recommendations": ["/api/recommendations", "/api/similar/<item_id>", "/api/popular"],
            "items": ["/api/items", "/api/items/<item_id>"],
            "interactions": ["/api/track"]
        }
    })

@app.route('/health')
def health():
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    user_count = cursor.fetchone()[0]
    
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "models_loaded": model_loader.model is not None,
        "registered_users": user_count,
        "database": "connected"
    })

# ==================== AUTHENTICATION ENDPOINTS ====================

@app.route('/api/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.json
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not all([username, email, password]):
            return jsonify({"error": "Missing required fields"}), 400
        
        if len(password) < 6:
            return jsonify({"error": "Password must be at least 6 characters"}), 400
        
        user_id = create_user(username, email, password)
        
        if not user_id:
            return jsonify({"error": "Username or email already exists"}), 400
        
        # Create session
        token = create_session(user_id)
        user = get_user_by_id(user_id)
        
        return jsonify({
            "message": "User registered successfully",
            "user": {
                "user_id": user['id'],
                "username": user['username'],
                "email": user['email'],
                "matrix_user_id": user['matrix_user_id']
            },
            "token": token
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """User login"""
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if not all([username, password]):
            return jsonify({"error": "Missing username or password"}), 400
        
        user_id = authenticate_user(username, password)
        
        if not user_id:
            return jsonify({"error": "Invalid credentials"}), 401
        
        # Create session
        token = create_session(user_id)
        user = get_user_by_id(user_id)
        
        return jsonify({
            "message": "Login successful",
            "user": {
                "user_id": user['id'],
                "username": user['username'],
                "email": user['email'],
                "matrix_user_id": user['matrix_user_id']
            },
            "token": token
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    """User logout"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if token:
        delete_session(token)
    
    return jsonify({"message": "Logged out successfully"})

@app.route('/api/me', methods=['GET'])
def get_current_user():
    """Get current user info"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    session_data = get_session(token)
    
    if not session_data:
        return jsonify({"error": "Not authenticated"}), 401
    
    user = get_user_by_id(session_data['user_id'])
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Get user stats
    interactions = get_user_interactions(user['id'])
    
    return jsonify({
        "user_id": user['id'],
        "username": user['username'],
        "email": user['email'],
        "created_at": user['created_at'],
        "matrix_user_id": user['matrix_user_id'],
        "interaction_count": len(interactions)
    })

# ==================== ITEM ENDPOINTS ====================

@app.route('/api/items', methods=['GET'])
def get_items():
    """Get all items with pagination"""
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    category = request.args.get('category')
    
    items = model_loader.item_metadata.copy()
    
    if category:
        items = items[items['category'] == category]
    
    # Pagination
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    paginated_items = items.iloc[start_idx:end_idx]
    
    # Add image URLs
    items_with_images = []
    for _, item in paginated_items.iterrows():
        item_dict = item.to_dict()
        item_dict['image_url'] = get_product_image_url(int(item['item_id']), item['category'])
        items_with_images.append(item_dict)
    
    return jsonify({
        "items": items_with_images,
        "total": len(items),
        "page": page,
        "per_page": per_page,
        "total_pages": (len(items) + per_page - 1) // per_page,
        "categories": items['category'].unique().tolist()
    })

@app.route('/api/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    """Get specific item details"""
    if item_id >= len(model_loader.item_metadata):
        return jsonify({"error": "Item not found"}), 404
    
    item = model_loader.item_metadata.iloc[item_id]
    item_dict = item.to_dict()
    item_dict['image_url'] = get_product_image_url(int(item['item_id']), item['category'])
    
    return jsonify({
        "item": item_dict,
        "similar_items": engine.get_similar_items(item_id, 5)
    })

# ==================== RECOMMENDATION ENDPOINTS ====================

@app.route('/api/recommendations', methods=['GET'])
def get_recommendations():
    """Get personalized recommendations for logged-in user"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    session_data = get_session(token)
    
    if not session_data:
        return jsonify({"error": "Authentication required"}), 401
    
    n = int(request.args.get('n', 10))
    
    user = get_user_by_id(session_data['user_id'])
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    recommendations = engine.get_user_recommendations(
        user['id'], 
        matrix_user_id=user['matrix_user_id'],
        n=n
    )
    
    return jsonify({
        "user_id": user['id'],
        "username": user['username'],
        "matrix_user_id": user['matrix_user_id'],
        "recommendations": recommendations,
        "algorithm": "NMF Collaborative Filtering",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/similar/<int:item_id>', methods=['GET'])
def get_similar(item_id):
    """Get similar items"""
    n = int(request.args.get('n', 5))
    similar_items = engine.get_similar_items(item_id, n)
    
    return jsonify({
        "item_id": item_id,
        "similar_items": similar_items,
        "algorithm": "Item-based Collaborative Filtering",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/popular', methods=['GET'])
def get_popular():
    """Get popular items"""
    n = int(request.args.get('n', 10))
    popular_items = engine.get_popular_items(n)
    
    return jsonify({
        "popular_products": popular_items,  # Changed from popular_items to popular_products
        "timestamp": datetime.now().isoformat()
    })

# ==================== INTERACTION TRACKING ====================

@app.route('/api/track', methods=['POST'])
def track_interaction():
    """Track user-item interaction"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    session_data = get_session(token)
    
    if not session_data:
        return jsonify({"error": "Authentication required"}), 401
    
    try:
        data = request.json
        item_id = data.get('item_id')
        rating = data.get('rating', 1)  # 1: view, 3: cart, 5: purchase
        
        user = get_user_by_id(session_data['user_id'])
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        # Track in database
        track_interaction_db(user['id'], item_id, rating)
        
        # Update user-item matrix if user has matrix_user_id
        if user['matrix_user_id'] is not None and \
           user['matrix_user_id'] < model_loader.user_item_matrix.shape[0] and \
           item_id < model_loader.user_item_matrix.shape[1]:
            model_loader.user_item_matrix[user['matrix_user_id'], item_id] = rating
        
        return jsonify({
            "message": "Interaction tracked successfully",
            "interaction": {
                "user_id": user['id'],
                "item_id": item_id,
                "rating": rating,
                "timestamp": datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
