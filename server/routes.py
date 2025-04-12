import os
import json
import uuid
import logging
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from datetime import datetime

from flask import Blueprint, request, jsonify, current_app, g, session, Response
from flask_cors import cross_origin
from werkzeug.utils import secure_filename

from .auth import register_user, login_user, get_current_user
from .graph_db import Neo4jDatabase
from .llm_service import llm_service
from .knowledge_graph_service import knowledge_graph_service
from .document_processor import document_processor

# Create the blueprint
api = Blueprint('api', __name__)

# Initialize database
db = Neo4jDatabase()

# Configure logging
logger = logging.getLogger(__name__)

# Create upload directory if it doesn't exist
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Helper functions
def get_user_id():
    """Get the current user ID from the session"""
    if 'user_id' in session:
        return session['user_id']
    return None

def allowed_file(filename):
    """Check if the file extension is allowed"""
    allowed_extensions = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'csv', 'json', 'md', 'xml', 'tiff', 'bmp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

# Authentication routes
@api.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid request data"}), 400
        
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        
        if not username or not password or not email:
            return jsonify({"error": "Missing required fields"}), 400
        
        user = register_user(username, password, email)
        
        if user:
            # Create session
            session['user_id'] = user.id
            session['username'] = user.username
            
            return jsonify({
                "message": "User registered successfully",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email
                },
                "token": "session_token"  # In a real app, use JWT or similar
            }), 201
        else:
            return jsonify({"error": "Registration failed"}), 400
    
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@api.route('/login', methods=['POST'])
def login():
    """Login a user"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid request data"}), 400
        
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({"error": "Missing username or password"}), 400
        
        user = login_user(username, password)
        
        if user:
            # Create session
            session['user_id'] = user.id
            session['username'] = user.username
            
            return jsonify({
                "message": "Login successful",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email
                },
                "token": "session_token"  # In a real app, use JWT or similar
            }), 200
        else:
            return jsonify({"error": "Invalid username or password"}), 401
    
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@api.route('/user', methods=['GET'])
def user():
    """Get current user"""
    user = get_current_user()
    
    if user:
        return jsonify({
            "id": user.id,
            "username": user.username,
            "email": user.email
        }), 200
    else:
        return jsonify({"error": "Not authenticated"}), 401

@api.route('/logout', methods=['POST'])
def logout():
    """Logout the current user"""
    session.clear()
    return jsonify({"message": "Logged out successfully"}), 200

# Graph routes
@api.route('/graph/overview', methods=['GET'])
def get_graph_overview():
    """Get an overview of the user's knowledge graph"""
    user_id = get_user_id()
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401
    
    try:
        # Get graph overview for the user
        overview = db.get_graph_overview(user_id)
        
        return jsonify(overview.dict()), 200
    
    except Exception as e:
        logger.error(f"Error getting graph overview: {str(e)}")
        return jsonify({"error": str(e)}), 500

@api.route('/graph/query', methods=['POST'])
def query_graph():
    """Query the knowledge graph with natural language"""
    user_id = get_user_id()
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid request data"}), 400
        
        query_text = data.get('query')
        if not query_text:
            return jsonify({"error": "Query is required"}), 400
        
        # Process the query with the knowledge graph service
        result = knowledge_graph_service.query_knowledge_graph(query_text, user_id)
        
        if "error" in result:
            return jsonify({"error": result["error"]}), 500
        
        # Store the query in history (this would normally be done in a database)
        # In a real app, you would save this to the database
        
        return jsonify({
            "id": uuid.uuid4().hex,
            "query": query_text,
            "response": result["response"],
            "graphData": result["graphData"].dict() if hasattr(result["graphData"], "dict") else result["graphData"],
            "timestamp": datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        return jsonify({"error": str(e)}), 500

@api.route('/history', methods=['GET'])
def get_query_history():
    """Get the user's query history"""
    user_id = get_user_id()
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401
    
    # In a real app, you would fetch this from the database
    # For now, we'll return an empty list
    return jsonify([]), 200

# File upload routes
@api.route('/upload', methods=['POST'])
def upload_file():
    """Upload a file to be processed into the knowledge graph"""
    user_id = get_user_id()
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401
    
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if not file or not allowed_file(file.filename):
            return jsonify({"error": "File type not allowed"}), 400
        
        # Save the file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}_{filename}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        file.save(file_path)
        
        # Get file info
        file_size = os.path.getsize(file_path)
        file_type = file.content_type
        
        # Process the file and create a knowledge graph
        result = knowledge_graph_service.create_document_graph(
            file_path, user_id, filename, file_type
        )
        
        if "error" in result:
            return jsonify({"error": result["error"]}), 500
        
        # Return processing results
        return jsonify({
            "message": "File processed successfully",
            "file": {
                "id": 1,  # This would normally come from the database
                "name": filename,
                "size": file_size
            },
            "graph": {
                "nodesCreated": result.get("document", {}).get("nodeCount", 0),
                "relationshipsCreated": result.get("document", {}).get("relationshipCount", 0),
                "graphData": result.get("graphData", {})
            }
        }), 201
    
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        return jsonify({"error": str(e)}), 500

@api.route('/files', methods=['GET'])
def get_user_files():
    """Get all files uploaded by the user"""
    user_id = get_user_id()
    if not user_id:
        return jsonify({"error": "Not authenticated"}), 401
    
    # In a real app, you would fetch this from the database
    # For now, we'll return an empty list
    return jsonify([]), 200

# System status route
@api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Check Neo4j connectivity
        neo4j_status = "connected" if db.verify_connectivity() else "disconnected"
        
        # Check LLM service availability
        llm_status = "available" if llm_service.is_available() else "unavailable"
        
        return jsonify({
            "status": "ok",
            "neo4j": neo4j_status,
            "llm": llm_status
        }), 200
    
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@api.route('/db-config', methods=['POST'])
def set_db_config():
    """Set database configuration"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid request data"}), 400
        
        use_in_memory = data.get('useInMemory', False)
        
        # Update environment variable
        os.environ['USE_IN_MEMORY_DB'] = str(use_in_memory).lower()
        
        # Reinitialize database connection
        global db
        db = Neo4jDatabase()
        
        return jsonify({
            "message": f"Database configuration updated. Using {'in-memory' if use_in_memory else 'Neo4j'} database.",
            "config": {
                "useInMemory": use_in_memory,
                "connected": db.verify_connectivity()
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error setting DB config: {str(e)}")
        return jsonify({"error": str(e)}), 500

@api.route('/api-config', methods=['POST'])
def set_api_config():
    """Set API configuration like OpenAI key"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Invalid request data"}), 400
        
        api_key = data.get('openaiApiKey')
        
        if api_key:
            # Update environment variable
            os.environ['OPENAI_API_KEY'] = api_key
            
            # Reinitialize the LLM service
            global llm_service
            from .llm_service import LLMService
            llm_service = LLMService()
            
            return jsonify({
                "message": "API key updated successfully",
                "config": {
                    "llm_available": llm_service.is_available()
                }
            }), 200
        else:
            return jsonify({"error": "API key is required"}), 400
    
    except Exception as e:
        logger.error(f"Error setting API config: {str(e)}")
        return jsonify({"error": str(e)}), 500

# Register the blueprint with the Flask app
def register_routes(app):
    app.register_blueprint(api, url_prefix='/api')