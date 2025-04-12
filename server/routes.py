from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
import json
import logging
from graph_db import neo4j_db
from llm_service import llm_service
from auth import register_user, login_user, get_current_user
from models import User, Query, File
from utils import save_uploaded_file, parse_file_content, format_graph_for_visualization
import os

logger = logging.getLogger(__name__)

# Create blueprint
api = Blueprint('api', __name__)

# Auth routes
@api.route('/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.json
    
    if not data:
        return jsonify({"message": "No input data provided"}), 400
    
    # Extract and validate required fields
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    
    if not username or not password or not email:
        return jsonify({"message": "Missing required fields"}), 400
    
    return register_user(username, password, email)

@api.route('/auth/login', methods=['POST'])
def login():
    """Login a user"""
    data = request.json
    
    if not data:
        return jsonify({"message": "No input data provided"}), 400
    
    # Extract and validate required fields
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"message": "Missing required fields"}), 400
    
    return login_user(username, password)

@api.route('/auth/user', methods=['GET'])
@jwt_required()
def user():
    """Get current user"""
    return get_current_user()

# Graph operations
@api.route('/graph/overview', methods=['GET'])
@jwt_required()
def get_graph_overview():
    """Get an overview of the user's knowledge graph"""
    user_id = get_jwt_identity()
    
    try:
        # Get nodes and relationships
        nodes = neo4j_db.get_nodes_by_user(user_id)
        relationships = neo4j_db.get_relationships_by_user(user_id)
        
        # Format for visualization
        graph_data = {
            "nodes": nodes,
            "relationships": relationships
        }
        
        vis_data = format_graph_for_visualization(graph_data)
        
        return jsonify({
            "graphData": vis_data,
            "stats": {
                "nodeCount": len(nodes),
                "relationshipCount": len(relationships)
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting graph overview: {e}")
        return jsonify({"message": f"Error retrieving graph data: {str(e)}"}), 500

@api.route('/graph/query', methods=['POST'])
@jwt_required()
def query_graph():
    """Query the knowledge graph with natural language"""
    user_id = get_jwt_identity()
    data = request.json
    
    if not data or 'query' not in data:
        return jsonify({"message": "No query provided"}), 400
    
    query_text = data['query']
    
    try:
        # First get the user's knowledge graph
        nodes = neo4j_db.get_nodes_by_user(user_id)
        relationships = neo4j_db.get_relationships_by_user(user_id)
        
        subgraph = {
            "nodes": nodes,
            "relationships": relationships
        }
        
        # Create a query record
        query_record = Query.create(query_text, user_id)
        
        # Process the query with LLM
        llm_response = llm_service.generate_query(query_text, subgraph)
        
        # Format graph data for visualization
        vis_data = format_graph_for_visualization(subgraph)
        
        # Update the query record with the response
        query_record.update_response(llm_response['answer'], vis_data)
        
        return jsonify({
            "id": query_record.id,
            "query": query_text,
            "response": llm_response['answer'],
            "graphData": vis_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        return jsonify({"message": f"Error processing query: {str(e)}"}), 500

@api.route('/history', methods=['GET'])
@jwt_required()
def get_query_history():
    """Get the user's query history"""
    user_id = get_jwt_identity()
    
    try:
        queries = Query.get_by_user_id(user_id)
        
        result = []
        for query in queries:
            result.append({
                "id": query.id,
                "query": query.text,
                "response": query.response,
                "graphData": query.response_graph,
                # Add timestamp if needed
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error getting query history: {e}")
        return jsonify({"message": f"Error retrieving history: {str(e)}"}), 500

# File upload and processing
@api.route('/upload', methods=['POST'])
@jwt_required()
def upload_file():
    """Upload a file to be processed into the knowledge graph"""
    user_id = get_jwt_identity()
    
    if 'file' not in request.files:
        return jsonify({"message": "No file part"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"message": "No selected file"}), 400
    
    try:
        # Save the file
        file_info = save_uploaded_file(file)
        
        if not file_info:
            return jsonify({"message": "Failed to save file"}), 500
        
        # Create a file record
        file_record = File.create(
            file_info['filename'],
            file_info['original_name'],
            file_info['mime_type'],
            file_info['size'],
            user_id
        )
        
        # Parse the file's content
        file_content = parse_file_content(file_info['path'])
        
        # Process file content with LLM to extract entities and relationships
        graph_data = llm_service.parse_document_to_graph(file_content)
        
        # Add extracted entities and relationships to the graph database
        nodes_created = []
        rels_created = []
        
        # Add entities
        for entity in graph_data.get('entities', []):
            node = neo4j_db.create_node(
                entity.get('type', 'Entity'),
                {
                    'name': entity.get('name', 'Unknown'),
                    'source': file_info['original_name'],
                    **entity.get('properties', {})
                },
                user_id
            )
            if node:
                nodes_created.append(node)
        
        # Add relationships
        for rel in graph_data.get('relationships', []):
            # Find the corresponding nodes
            source_node = next(
                (n for n in nodes_created if n['properties'].get('name') == rel.get('source')),
                None
            )
            target_node = next(
                (n for n in nodes_created if n['properties'].get('name') == rel.get('target')),
                None
            )
            
            if source_node and target_node:
                relationship = neo4j_db.create_relationship(
                    source_node['id'],
                    target_node['id'],
                    rel.get('type', 'RELATED_TO'),
                    {
                        'source': file_info['original_name'],
                        **rel.get('properties', {})
                    },
                    user_id
                )
                if relationship:
                    rels_created.append(relationship)
        
        # Mark the file as processed
        file_record.mark_as_processed()
        
        # Format the graph for visualization
        graph_data = {
            "nodes": nodes_created,
            "relationships": rels_created
        }
        vis_data = format_graph_for_visualization(graph_data)
        
        return jsonify({
            "message": "File processed successfully",
            "file": {
                "id": file_record.id,
                "name": file_info['original_name'],
                "size": file_info['size']
            },
            "graph": {
                "nodesCreated": len(nodes_created),
                "relationshipsCreated": len(rels_created),
                "graphData": vis_data
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing uploaded file: {e}")
        return jsonify({"message": f"Error processing file: {str(e)}"}), 500

@api.route('/files', methods=['GET'])
@jwt_required()
def get_user_files():
    """Get all files uploaded by the user"""
    user_id = get_jwt_identity()
    
    try:
        files = File.get_by_user_id(user_id)
        
        result = []
        for file in files:
            result.append({
                "id": file.id,
                "filename": file.original_name,
                "mimeType": file.mime_type,
                "size": file.size,
                "processed": file.processed
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error getting user files: {e}")
        return jsonify({"message": f"Error retrieving files: {str(e)}"}), 500

# Health check
@api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Check Neo4j connection
        neo4j_status = neo4j_db.verify_connectivity()
        
        return jsonify({
            "status": "ok" if neo4j_status else "error",
            "neo4j": "connected" if neo4j_status else "disconnected",
            "llm": "available" if llm_service.model else "unavailable"
        }), 200 if neo4j_status else 500
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
