import sqlite3
import json
from datetime import datetime
from werkzeug.security import generate_password_hash

def init_database():
    """Initialize SQLite database with users table"""
    
    conn = sqlite3.connect('ecommerce.db')
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            matrix_user_id INTEGER,
            UNIQUE(username),
            UNIQUE(email)
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
    
    conn.commit()
    
    # Create demo users with specific matrix_user_ids
    demo_users = [
        ('demo', 'demo@example.com', 'demo123', 0),      # Maps to matrix user 0
        ('alice', 'alice@example.com', 'password', 1),   # Maps to matrix user 1
        ('bob', 'bob@example.com', 'password', 2),       # Maps to matrix user 2
        ('charlie', 'charlie@example.com', 'password', 3),
        ('david', 'david@example.com', 'password', 4),
        ('eve', 'eve@example.com', 'password', 5),
        ('frank', 'frank@example.com', 'password', 6),
        ('grace', 'grace@example.com', 'password', 7),
        ('henry', 'henry@example.com', 'password', 8),
        ('iris', 'iris@example.com', 'password', 9),
    ]
    
    for username, email, password, matrix_id in demo_users:
        try:
            cursor.execute('''
                INSERT INTO users (username, email, password_hash, created_at, matrix_user_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, email, generate_password_hash(password), 
                  datetime.now().isoformat(), matrix_id))
            print(f"Created user: {username} (matrix_user_id: {matrix_id})")
        except sqlite3.IntegrityError:
            print(f"  User {username} already exists")
    
    conn.commit()
    
    # Show created users
    cursor.execute('SELECT id, username, email, matrix_user_id FROM users')
    users = cursor.fetchall()
    
    print(f"\n Total users in database: {len(users)}")
    print("\nUser List:")
    print("-" * 60)
    for user_id, username, email, matrix_id in users:
        print(f"DB ID: {user_id:3d} | Username: {username:10s} | Matrix ID: {matrix_id:4d} | Email: {email}")
    
    conn.close()
    print("\n Database initialized successfully!")

if __name__ == "__main__":
    init_database()
