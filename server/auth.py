from flask import jsonify, request
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
import logging
from models import User

logger = logging.getLogger(__name__)

# Initialize JWT
jwt = JWTManager()

def register_user(username, password, email):
    """Register a new user"""
    try:
        # Check if user already exists
        if User.get_by_username(username):
            return jsonify({"message": "Username already exists"}), 400
        
        if User.get_by_email(email):
            return jsonify({"message": "Email already exists"}), 400
        
        # Hash password
        hashed_password = generate_password_hash(password)
        
        # Create user
        user = User.create(username, hashed_password, email)
        
        # Generate access token
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            "message": "User registered successfully",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            },
            "token": access_token
        }), 201
        
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        return jsonify({"message": "Registration failed"}), 500

def login_user(username, password):
    """Login a user"""
    try:
        # Get user by username
        user = User.get_by_username(username)
        
        if not user:
            return jsonify({"message": "Invalid username or password"}), 401
        
        # Check password
        if not check_password_hash(user.password, password):
            return jsonify({"message": "Invalid username or password"}), 401
        
        # Generate access token
        access_token = create_access_token(identity=user.id)
        
        return jsonify({
            "message": "Login successful",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            },
            "token": access_token
        }), 200
        
    except Exception as e:
        logger.error(f"Error logging in user: {e}")
        return jsonify({"message": "Login failed"}), 500

def get_current_user():
    """Get the current authenticated user"""
    try:
        user_id = get_jwt_identity()
        user = User.get_by_id(user_id)
        
        if not user:
            return jsonify({"message": "User not found"}), 404
        
        return jsonify({
            "id": user.id,
            "username": user.username,
            "email": user.email
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        return jsonify({"message": "Failed to get user information"}), 500
