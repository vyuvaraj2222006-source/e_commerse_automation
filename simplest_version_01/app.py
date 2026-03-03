from flask import Flask, request, jsonify, session
from flask_cors import CORS
import pandas as pd
import numpy as np
import pickle
import json
import os
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True

CORS(app, supports_credentials=True, origins=['*'])

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

model_loader = ModelLoader()

# ==================== USER DATABASE (In-Memory) ====================

users_db = {}  # {username: {password_hash, email, user_id, created_at}}
sessions_db = {}  # {session_token: {user_id, username, expires}}
user_interactions = {}  # {user_id: [{item_id, rating, timestamp}]}

def create_user(username, email, password):
    """Create a new user account"""
    if username in users_db:
        return None
    
    user_id = len(users_db) + 1
    users_db[username] = {
        'user_id': user_id,
        'password_hash': generate_password_hash(password),
        'email': email,
        'created_at': datetime.now().isoformat()
    }
    user_interactions[user_id] = []
    return user_id

def authenticate_user(username, password):
    """Authenticate user credentials"""
    user = users_db.get(username)
    if user and check_password_hash(user['password_hash'], password):
        return user['user_id']
    return None

def create_session(user_id, username):
    """Create a session token"""
    token = secrets.token_hex(32)
    sessions_db[token] = {
        'user_id': user_id,
        'username': username,
        'expires': (datetime.now() + timedelta(days=7)).isoformat()
    }
    return token

def get_session(token):
    """Get session data from token"""
    session_data = sessions_db.get(token)
    if session_data:
        expires = datetime.fromisoformat(session_data['expires'])
        if datetime.now() < expires:
            return session_data
    return None

# Create demo users
create_user('demo', 'demo@example.com', 'demo123')
create_user('alice', 'alice@example.com', 'password')
create_user('bob', 'bob@example.com', 'password')

# ==================== RECOMMENDATION ENGINE ====================

class RecommendationEngine:
    def __init__(self, model_loader):
        self.loader = model_loader
    
    def get_user_recommendations(self, user_id, n=10):
        """Get personalized recommendations using trained NMF model"""
        try:
            # Check if user exists in matrix
            if user_id >= self.loader.user_item_matrix.shape[0]:
                return self.get_popular_items(n)
            
            # Get user's latent factors from the trained model
            user_factors = self.loader.model.transform(
                self.loader.user_item_matrix[user_id:user_id+1]
            )
            
            # Get item factors
            item_factors = self.loader.model.components_
            
            # Calculate predicted ratings
            predicted_ratings = user_factors.dot(item_factors)[0]
            
            # Get user's already rated items
            rated_items = np.where(self.loader.user_item_matrix[user_id] > 0)[0]
            
            # Set already rated items to -inf so they won't be recommended
            predicted_ratings[rated_items] = -np.inf
            
            # Get top N recommendations
            top_indices = np.argsort(predicted_ratings)[::-1][:n]
            
            # Get item details
            recommendations = []
            for idx in top_indices:
                if idx < len(self.loader.item_metadata):
                    item = self.loader.item_metadata.iloc[idx]
                    recommendations.append({
                        'item_id': int(item['item_id']),
                        'name': item['name'],
                        'category': item['category'],
                        'price': float(item['price']),
                        'predicted_score': float(predicted_ratings[idx])
                    })
            
            return recommendations
            
        except Exception as e:
            print(f"Error in recommendations: {e}")
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
                        'similarity_score': float(similarities[idx])
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
                        'popularity_score': float(popularity[idx])
                    })
            
            return popular_items
            
        except Exception as e:
            print(f"Error getting popular items: {e}")
            return self.loader.item_metadata.head(n).to_dict('records')

engine = RecommendationEngine(model_loader)

# ==================== API ENDPOINTS ====================

@app.route('/')
def home():
    return jsonify({
        "message": "E-Commerce Recommendation API with User Authentication",
        "version": "2.0",
        "model_info": {
            "type": model_loader.config.get('model_type') if model_loader.config else "unknown",
            "n_users": model_loader.user_item_matrix.shape[0] if model_loader.user_item_matrix is not None else 0,
            "n_items": len(model_loader.item_metadata) if model_loader.item_metadata is not None else 0
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
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "models_loaded": model_loader.model is not None,
        "registered_users": len(users_db)
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
            return jsonify({"error": "Username already exists"}), 400
        
        # Create session
        token = create_session(user_id, username)
        
        return jsonify({
            "message": "User registered successfully",
            "user": {
                "user_id": user_id,
                "username": username,
                "email": email
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
        token = create_session(user_id, username)
        user = users_db[username]
        
        return jsonify({
            "message": "Login successful",
            "user": {
                "user_id": user_id,
                "username": username,
                "email": user['email']
            },
            "token": token
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    """User logout"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if token in sessions_db:
        del sessions_db[token]
    
    return jsonify({"message": "Logged out successfully"})

@app.route('/api/me', methods=['GET'])
def get_current_user():
    """Get current user info"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    session_data = get_session(token)
    
    if not session_data:
        return jsonify({"error": "Not authenticated"}), 401
    
    username = session_data['username']
    user = users_db[username]
    
    # Get user stats
    interaction_count = len(user_interactions.get(session_data['user_id'], []))
    
    return jsonify({
        "user_id": session_data['user_id'],
        "username": username,
        "email": user['email'],
        "created_at": user['created_at'],
        "interaction_count": interaction_count
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
    
    return jsonify({
        "items": paginated_items.to_dict('records'),
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
    
    return jsonify({
        "item": item.to_dict(),
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
    user_id = session_data['user_id']
    
    recommendations = engine.get_user_recommendations(user_id, n)
    
    return jsonify({
        "user_id": user_id,
        "username": session_data['username'],
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
    popular_products = engine.get_popular_items(n)

    return jsonify({
        "popular_products": popular_products,  # ✅ MUST be this
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
        
        user_id = session_data['user_id']
        
        interaction = {
            "item_id": item_id,
            "rating": rating,
            "timestamp": datetime.now().isoformat()
        }
        
        if user_id not in user_interactions:
            user_interactions[user_id] = []
        
        user_interactions[user_id].append(interaction)
        
        # Update user-item matrix if within bounds
        if user_id < model_loader.user_item_matrix.shape[0] and \
           item_id < model_loader.user_item_matrix.shape[1]:
            model_loader.user_item_matrix[user_id, item_id] = rating
        
        return jsonify({
            "message": "Interaction tracked successfully",
            "interaction": interaction
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
