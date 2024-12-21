# database.py
import sqlite3
import os

class UserDatabase:
    def __init__(self):
        self.db_path = 'users.db'
        self.init_database()
        
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Create users table
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                face_data_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_user(self, email, password, face_data_path=None):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        try:
            c.execute(
                'INSERT INTO users (email, password, face_data_path) VALUES (?, ?, ?)',
                (email, password, face_data_path)
            )
            user_id = c.lastrowid
            conn.commit()
            return user_id
        except sqlite3.IntegrityError:
            return None
        finally:
            conn.close()
    
    def verify_user(self, email, password):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT user_id, face_data_path FROM users WHERE email = ? AND password = ?', 
                 (email, password))
        result = c.fetchone()
        conn.close()
        return result if result else None
    
    def update_face_path(self, user_id, face_data_path):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('UPDATE users SET face_data_path = ? WHERE user_id = ?', 
                 (face_data_path, user_id))
        conn.commit()
        conn.close()

# File structure manager
class FileManager:
    def __init__(self):
        self.base_path = 'face_data'
        os.makedirs(self.base_path, exist_ok=True)
    
    def create_user_directory(self, user_id):
        user_path = os.path.join(self.base_path, f'user_{user_id}')
        os.makedirs(user_path, exist_ok=True)
        return user_path
    
    def get_user_face_path(self, user_id):
        return os.path.join(self.base_path, f'user_{user_id}')