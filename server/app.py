import os
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from config import Config
from routes import api
from auth import jwt

# Load environment variables
load_dotenv()

def create_app(config_class=Config):
    app = Flask(__name__, static_folder='../dist/public')
    app.config.from_object(config_class)
    
    # Set up CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Initialize JWT
    jwt.init_app(app)
    
    # Register API blueprint
    app.register_blueprint(api, url_prefix='/api')
    
    # Serve static files in production
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve(path):
        if path and os.path.exists(app.static_folder + '/' + path):
            return send_from_directory(app.static_folder, path)
        else:
            return send_from_directory(app.static_folder, 'index.html')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"message": "Route not found"}), 404
    
    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"message": "An internal server error occurred"}), 500
    
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8000, debug=True)
