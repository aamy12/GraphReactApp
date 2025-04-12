import os
import logging
from typing import Optional, Any
from pathlib import Path

from flask import Flask, send_from_directory, jsonify, current_app
from flask_cors import CORS

from .routes import register_routes
from .graph_db import Neo4jDatabase
from .llm_service import llm_service
from .knowledge_graph_service import knowledge_graph_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app(config_class=None):
    """Create and configure the Flask application"""
    app = Flask(__name__, static_folder=None)
    
    # Load configuration
    if config_class:
        app.config.from_object(config_class)
    
    # Set default configuration
    app.config.setdefault('SECRET_KEY', os.environ.get('SECRET_KEY', 'dev-secret-key'))
    app.config.setdefault('SESSION_TYPE', 'filesystem')
    app.config.setdefault('SESSION_PERMANENT', False)
    app.config.setdefault('SESSION_USE_SIGNER', True)
    
    # Enable CORS for the Flask app
    CORS(app, supports_credentials=True)
    
    # Initialize upload directory
    upload_folder = os.path.join(os.getcwd(), 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = upload_folder
    
    # Set environment variable for in-memory database if not set
    if 'USE_IN_MEMORY_DB' not in os.environ:
        os.environ['USE_IN_MEMORY_DB'] = 'true'  # Default to in-memory for demo
    
    # Initialize services
    with app.app_context():
        # Check services
        db = Neo4jDatabase()
        neo4j_status = db.verify_connectivity()
        logger.info(f"Neo4j connectivity: {'Connected' if neo4j_status else 'Disconnected'}")
        
        llm_available = llm_service.is_available()
        logger.info(f"LLM service: {'Available' if llm_available else 'Unavailable'}")
        
        if not llm_available:
            logger.warning("LLM service is not available. Set OPENAI_API_KEY environment variable to enable.")
        
        db_type = "in-memory" if os.environ.get('USE_IN_MEMORY_DB', 'false').lower() == 'true' else "Neo4j"
        logger.info(f"Using {db_type} database")
    
    # Register the routes blueprint
    register_routes(app)
    
    # Static file serving route
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve(path):
        """Serve the frontend static files"""
        if path and Path(app.static_folder + '/' + path).exists():
            return send_from_directory(app.static_folder, path)
        else:
            return send_from_directory(app.static_folder, 'index.html')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        """Handle 404 errors"""
        return jsonify({"error": "Resource not found"}), 404
    
    @app.errorhandler(500)
    def server_error(e):
        """Handle 500 errors"""
        return jsonify({"error": "Server error occurred"}), 500
    
    return app