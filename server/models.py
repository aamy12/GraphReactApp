from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import sqlite3
import os
import logging
from werkzeug.security import generate_password_hash

logger = logging.getLogger(__name__)

# Simple SQLite database for user authentication
# (Neo4j will handle the graph data)
DB_PATH = "users.db"

def init_db():
    """Initialize the SQLite database for user authentication"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create queries table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS queries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT NOT NULL,
        user_id INTEGER NOT NULL,
        response TEXT,
        response_graph TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    # Create files table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        original_name TEXT NOT NULL,
        mime_type TEXT NOT NULL,
        size INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        processed BOOLEAN DEFAULT 0,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

@dataclass
class User:
    id: int
    username: str
    password: str
    email: str
    
    @staticmethod
    def create(username: str, password: str, email: str) -> 'User':
        """Create a new user"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
            (username, password, email)
        )
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return User(user_id, username, password, email)
    
    @staticmethod
    def get_by_id(user_id: int) -> Optional['User']:
        """Get a user by ID"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        conn.close()
        
        if user:
            return User(user[0], user[1], user[2], user[3])
        return None
    
    @staticmethod
    def get_by_username(username: str) -> Optional['User']:
        """Get a user by username"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        
        conn.close()
        
        if user:
            return User(user[0], user[1], user[2], user[3])
        return None
    
    @staticmethod
    def get_by_email(email: str) -> Optional['User']:
        """Get a user by email"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        
        conn.close()
        
        if user:
            return User(user[0], user[1], user[2], user[3])
        return None

@dataclass
class Query:
    id: int
    text: str
    user_id: int
    response: Optional[str] = None
    response_graph: Optional[Dict] = None
    
    @staticmethod
    def create(text: str, user_id: int) -> 'Query':
        """Create a new query"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO queries (text, user_id) VALUES (?, ?)",
            (text, user_id)
        )
        
        query_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return Query(query_id, text, user_id)
    
    @staticmethod
    def get_by_id(query_id: int) -> Optional['Query']:
        """Get a query by ID"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM queries WHERE id = ?", (query_id,))
        query = cursor.fetchone()
        
        conn.close()
        
        if query:
            response_graph = query[4]
            if response_graph:
                import json
                response_graph = json.loads(response_graph)
            return Query(query[0], query[1], query[2], query[3], response_graph)
        return None
    
    @staticmethod
    def get_by_user_id(user_id: int) -> List['Query']:
        """Get all queries by user ID"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM queries WHERE user_id = ? ORDER BY timestamp DESC", (user_id,))
        queries = cursor.fetchall()
        
        conn.close()
        
        result = []
        for q in queries:
            response_graph = q[4]
            if response_graph:
                import json
                response_graph = json.loads(response_graph)
            result.append(Query(q[0], q[1], q[2], q[3], response_graph))
        
        return result
    
    def update_response(self, response: str, response_graph: Dict) -> None:
        """Update the response for a query"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        import json
        response_graph_json = json.dumps(response_graph)
        
        cursor.execute(
            "UPDATE queries SET response = ?, response_graph = ? WHERE id = ?",
            (response, response_graph_json, self.id)
        )
        
        conn.commit()
        conn.close()
        
        self.response = response
        self.response_graph = response_graph

@dataclass
class File:
    id: int
    filename: str
    original_name: str
    mime_type: str
    size: int
    user_id: int
    processed: bool = False
    
    @staticmethod
    def create(filename: str, original_name: str, mime_type: str, size: int, user_id: int) -> 'File':
        """Create a new file record"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO files (filename, original_name, mime_type, size, user_id) VALUES (?, ?, ?, ?, ?)",
            (filename, original_name, mime_type, size, user_id)
        )
        
        file_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return File(file_id, filename, original_name, mime_type, size, user_id)
    
    @staticmethod
    def get_by_id(file_id: int) -> Optional['File']:
        """Get a file by ID"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM files WHERE id = ?", (file_id,))
        file = cursor.fetchone()
        
        conn.close()
        
        if file:
            return File(file[0], file[1], file[2], file[3], file[4], file[5], bool(file[6]))
        return None
    
    @staticmethod
    def get_by_user_id(user_id: int) -> List['File']:
        """Get all files by user ID"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM files WHERE user_id = ? ORDER BY uploaded_at DESC", (user_id,))
        files = cursor.fetchall()
        
        conn.close()
        
        return [File(f[0], f[1], f[2], f[3], f[4], f[5], bool(f[6])) for f in files]
    
    def mark_as_processed(self) -> None:
        """Mark a file as processed"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE files SET processed = 1 WHERE id = ?",
            (self.id,)
        )
        
        conn.commit()
        conn.close()
        
        self.processed = True
