import os
import hashlib
import logging
import uuid
from typing import Optional, Dict, Any, List
from flask import session, g

logger = logging.getLogger(__name__)

# In-memory user storage for demonstration
# In a real app, this would be a database
users = {}

class User:
    """Simple user class for authentication"""
    def __init__(self, id: int, username: str, password_hash: str, email: str):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.email = email
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Create a SHA-256 hash of the password"""
        salt = os.environ.get('PASSWORD_SALT', 'dev-salt')
        return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()
    
    def verify_password(self, password: str) -> bool:
        """Verify the password against the stored hash"""
        password_hash = self.hash_password(password)
        return password_hash == self.password_hash


def register_user(username: str, password: str, email: str) -> Optional[User]:
    """Register a new user"""
    # Check if username or email already exists
    for user in users.values():
        if user.username == username:
            logger.warning(f"Registration failed: Username '{username}' already exists")
            return None
        if user.email == email:
            logger.warning(f"Registration failed: Email '{email}' already exists")
            return None
    
    # Create a new user
    user_id = len(users) + 1  # In a real app, this would be auto-generated by the database
    password_hash = User.hash_password(password)
    
    user = User(user_id, username, password_hash, email)
    users[user_id] = user
    
    logger.info(f"User registered: {username} (ID: {user_id})")
    return user


def login_user(username: str, password: str) -> Optional[User]:
    """Login a user"""
    # For demonstration, auto-create a test user if none exist
    if not users and os.environ.get('FLASK_ENV') == 'development':
        logger.info("Development mode: Creating test user")
        register_user("test", "password", "test@example.com")
    
    # Find user by username
    user = next((u for u in users.values() if u.username == username), None)
    
    if not user:
        logger.warning(f"Login failed: User '{username}' not found")
        return None
    
    # Verify password
    if not user.verify_password(password):
        logger.warning(f"Login failed: Invalid password for user '{username}'")
        return None
    
    logger.info(f"User logged in: {username} (ID: {user.id})")
    return user


def get_current_user() -> Optional[User]:
    """Get the current authenticated user"""
    if hasattr(g, 'user'):
        return g.user
    
    user_id = session.get('user_id')
    if not user_id:
        return None
    
    user = users.get(user_id)
    if user:
        g.user = user
        return user
    
    return None


# For demonstration, auto-create a test user if none exist and we're in development mode
if os.environ.get('FLASK_ENV') == 'development' and not users:
    register_user("test", "password", "test@example.com")
    logger.info("Created test user: test/password")