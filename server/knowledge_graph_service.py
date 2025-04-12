import os
import logging
import tempfile
from typing import Dict, List, Any, Optional, Tuple, Union
import uuid
from pathlib import Path

from .graph_db import Neo4jDatabase
from .document_processor import document_processor

logger = logging.getLogger(__name__)

class KnowledgeGraphService:
    """Service for building and querying knowledge graphs from documents"""
    
    def __init__(self):
        self.db = Neo4jDatabase()
        self.processor = document_processor
        
    def create_document_graph(self, file_path: str, user_id: int, 
                              file_name: str, file_type: str = None) -> Dict[str, Any]:
        """
        Process a document and create a knowledge graph from its content
        
        Args:
            file_path: Path to the file to process
            user_id: ID of the user who uploaded the file
            file_name: Original name of the file
            file_type: Optional file type (mime type or extension)
            
        Returns:
            Dictionary containing processing results and graph statistics
        """
        logger.info(f"Processing document: {file_name} for user {user_id}")
        
        try:
            # Process the document
            doc_result = self.processor.process_file(file_path, file_type)
            
            if "error" in doc_result:
                logger.error(f"Error processing document: {doc_result['error']}")
                return {"error": doc_result["error"]}
            
            # Create document node
            doc_node = self.db.create_node("Document", {
                "name": file_name,
                "content": doc_result.get("text", "")[:1000],  # Store first 1000 chars as preview
                "filePath": file_path,
                "fileName": file_name,
                "fileType": file_type
            }, user_id)
            
            if not doc_node:
                return {"error": "Failed to create document node"}
            
            # Add metadata as properties to document node
            metadata_node = None
            if doc_result.get("metadata"):
                metadata_properties = {
                    "name": f"Metadata for {file_name}",
                }
                # Add specific metadata as properties
                for key, value in doc_result["metadata"].items():
                    if isinstance(value, (str, int, float, bool)):
                        metadata_properties[key] = value
                
                metadata_node = self.db.create_node("Metadata", metadata_properties, user_id)
                
                if metadata_node:
                    # Link metadata to document
                    self.db.create_relationship(
                        doc_node.id, metadata_node.id,
                        "HAS_METADATA", {}, user_id
                    )
            
            # Extract entities and relationships from text
            extract_result = self.processor.extract_entities_and_relationships(doc_result.get("text", ""))
            
            # Track created nodes and relationships
            created_nodes = [doc_node]
            if metadata_node:
                created_nodes.append(metadata_node)
                
            created_relationships = []
            
            # Create entity nodes
            entity_nodes = {}  # name -> node
            for entity in extract_result.get("entities", []):
                entity_node = self.db.create_node(
                    entity.get("type", "Entity"),
                    {
                        "name": entity["name"],
                        "mentions": entity.get("mentions", 1)
                    },
                    user_id
                )
                
                if entity_node:
                    entity_nodes[entity["name"]] = entity_node
                    created_nodes.append(entity_node)
                    
                    # Link entity to document
                    rel = self.db.create_relationship(
                        doc_node.id, entity_node.id,
                        "MENTIONS", {"count": entity.get("mentions", 1)},
                        user_id
                    )
                    if rel:
                        created_relationships.append(rel)
            
            # Create relationships between entities
            for relationship in extract_result.get("relationships", []):
                source_name = relationship["source"]
                target_name = relationship["target"]
                
                if source_name in entity_nodes and target_name in entity_nodes:
                    source_node = entity_nodes[source_name]
                    target_node = entity_nodes[target_name]
                    
                    rel = self.db.create_relationship(
                        source_node.id, target_node.id,
                        relationship["type"],
                        {"sentence": relationship.get("sentence", "")[:100]},  # First 100 chars of evidence
                        user_id
                    )
                    
                    if rel:
                        created_relationships.append(rel)
            
            # Process chunks if available
            chunk_nodes = []
            for i, chunk in enumerate(doc_result.get("chunks", [])):
                chunk_node = self.db.create_node("Chunk", {
                    "name": f"Chunk {i+1} of {file_name}",
                    "content": chunk["text"],
                    "index": i
                }, user_id)
                
                if chunk_node:
                    chunk_nodes.append(chunk_node)
                    created_nodes.append(chunk_node)
                    
                    # Link chunk to document
                    rel = self.db.create_relationship(
                        doc_node.id, chunk_node.id,
                        "HAS_CHUNK", {"index": i},
                        user_id
                    )
                    if rel:
                        created_relationships.append(rel)
            
            # Get information about the created graph
            graph_overview = self.db.get_graph_overview(user_id)
            
            # Return processing results
            return {
                "success": True,
                "document": {
                    "id": doc_node.id,
                    "name": file_name,
                    "nodeCount": len(created_nodes),
                    "relationshipCount": len(created_relationships),
                },
                "entities": [node.name for node in created_nodes if node.label != "Document" and node.label != "Chunk"],
                "chunks": len(chunk_nodes),
                "graphData": graph_overview.graphData,
                "stats": graph_overview.stats
            }
        
        except Exception as e:
            logger.error(f"Error creating knowledge graph: {str(e)}")
            return {"error": str(e)}
    
    def query_knowledge_graph(self, query: str, user_id: int) -> Dict[str, Any]:
        """
        Query the knowledge graph based on a natural language query
        
        Args:
            query: Natural language query
            user_id: ID of the user making the query
            
        Returns:
            Dict containing query results and subgraph
        """
        logger.info(f"Processing query: '{query}' for user {user_id}")
        
        try:
            # This is where you would use an LLM to translate the natural language
            # query into a Cypher query. For now, we'll use a simplified approach.
            
            # Extract potential entity names from the query
            words = query.split()
            capitalized_words = [word for word in words if word[0].isupper() and len(word) > 3]
            
            cypher_query = """
            MATCH (d:Document)-[:MENTIONS]->(e)
            WHERE e.created_by = $user_id
            RETURN d, e
            LIMIT 10
            """
            
            # If we have potential entities, search for them
            if capitalized_words:
                entity_names = [word.strip(',.!?()[]{};"\'').lower() for word in capitalized_words]
                entity_names = [name for name in entity_names if len(name) > 3]
                
                if entity_names:
                    name_pattern = '|'.join(entity_names)
                    cypher_query = f"""
                    MATCH (e)
                    WHERE e.created_by = $user_id 
                    AND toLower(e.name) CONTAINS toLower($search_term)
                    OPTIONAL MATCH (e)-[r]-(related)
                    WHERE related.created_by = $user_id
                    RETURN e, r, related
                    LIMIT 20
                    """
                    
                    # Execute the query
                    subgraph = self.db.query_subgraph(cypher_query, {
                        "user_id": user_id,
                        "search_term": entity_names[0]  # Use the first entity name
                    })
                
                    # Generate a textual response (this would normally use an LLM)
                    response_text = f"I found {len(subgraph.nodes)} entities related to '{entity_names[0]}' in your knowledge graph."
                    
                    if len(subgraph.nodes) > 0:
                        response_text += f"\n\nHere are some related items:\n"
                        for node in subgraph.nodes[:5]:  # Show top 5
                            response_text += f"- {node.name} ({node.label})\n"
                    
                    if len(subgraph.links) > 0:
                        response_text += f"\nThese entities have {len(subgraph.links)} relationships between them."
                    
                    return {
                        "query": query,
                        "response": response_text,
                        "graphData": subgraph
                    }
            
            # Default query if no entities found
            subgraph = self.db.query_subgraph("""
            MATCH (n)-[r]-(m)
            WHERE n.created_by = $user_id AND m.created_by = $user_id
            RETURN n, r, m
            LIMIT 20
            """, {"user_id": user_id})
            
            response_text = f"I found {len(subgraph.nodes)} nodes and {len(subgraph.links)} relationships in your knowledge graph."
            
            if len(subgraph.nodes) > 0:
                response_text += f"\n\nHere are some items from your knowledge graph:\n"
                for node in subgraph.nodes[:5]:  # Show top 5
                    response_text += f"- {node.name} ({node.label})\n"
            
            return {
                "query": query,
                "response": response_text,
                "graphData": subgraph
            }
        
        except Exception as e:
            logger.error(f"Error querying knowledge graph: {str(e)}")
            return {
                "query": query,
                "response": f"Error processing your query: {str(e)}",
                "graphData": {"nodes": [], "links": []}
            }
    
    def get_document_entities(self, document_id: str, user_id: int) -> Dict[str, Any]:
        """Get entities and relationships associated with a document"""
        try:
            subgraph = self.db.query_subgraph("""
            MATCH (d:Document)-[r1:MENTIONS]->(e)
            WHERE d.id = $document_id AND d.created_by = $user_id
            OPTIONAL MATCH (e)-[r2]-(related)
            WHERE related.created_by = $user_id AND related <> d
            RETURN d, r1, e, r2, related
            """, {
                "document_id": document_id,
                "user_id": user_id
            })
            
            return {
                "documentId": document_id,
                "graphData": subgraph
            }
        except Exception as e:
            logger.error(f"Error getting document entities: {str(e)}")
            return {
                "documentId": document_id,
                "error": str(e),
                "graphData": {"nodes": [], "links": []}
            }

# Singleton instance
knowledge_graph_service = KnowledgeGraphService()