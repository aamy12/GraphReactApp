import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app
import logging
import json
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

def ensure_upload_dir_exists():
    """Ensure the upload directory exists"""
    os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)

def save_uploaded_file(file):
    """Save an uploaded file and return information about it"""
    if not file:
        return None
    
    # Ensure upload directory exists
    ensure_upload_dir_exists()
    
    # Secure the filename and generate a unique name
    filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4()}_{filename}"
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
    
    # Save the file
    file.save(file_path)
    
    # Return file information
    return {
        'filename': unique_filename,
        'original_name': filename,
        'mime_type': file.content_type,
        'size': os.path.getsize(file_path),
        'path': file_path
    }

def parse_file_content(file_path: str) -> str:
    """Parse the content of a file based on its extension"""
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    try:
        if ext in ['.txt']:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        elif ext in ['.json']:
            with open(file_path, 'r', encoding='utf-8') as file:
                return json.dumps(json.load(file))
        else:
            logger.warning(f"Unsupported file type: {ext}")
            return f"Unsupported file type: {ext}"
    except Exception as e:
        logger.error(f"Error parsing file {file_path}: {e}")
        return f"Error parsing file: {str(e)}"

def format_graph_for_visualization(graph_data: Dict[str, List[Dict[str, Any]]]) -> Dict:
    """Format graph data for D3.js visualization"""
    nodes = []
    links = []
    
    # Process nodes
    for node in graph_data.get('nodes', []):
        node_id = node.get('id')
        label = node.get('labels', ['Node'])[0]  # Get first label
        name = node.get('properties', {}).get('name', f"Node {node_id}")
        
        nodes.append({
            'id': str(node_id),
            'label': label,
            'name': name,
            'properties': node.get('properties', {})
        })
    
    # Process relationships
    for rel in graph_data.get('relationships', []):
        links.append({
            'id': str(rel.get('id')),
            'source': str(rel.get('start_node_id')),
            'target': str(rel.get('end_node_id')),
            'type': rel.get('type'),
            'properties': rel.get('properties', {})
        })
    
    return {
        'nodes': nodes,
        'links': links
    }
