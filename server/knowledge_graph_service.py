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
            # Determine file extension
            extension = file_name.split('.')[-1].lower() if '.' in file_name else ""
            
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
                "fileType": file_type or extension
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
            
            # Track created nodes and relationships
            created_nodes = [doc_node]
            if metadata_node:
                created_nodes.append(metadata_node)
                
            created_relationships = []
            
            # Special handling for structured data files
            is_structured_data = extension in ['json', 'csv', 'xml', 'xls', 'xlsx', 'tsv']
            
            if is_structured_data:
                # Process structured data differently depending on the format
                if extension in ['json']:
                    # Create data structure nodes for JSON
                    structure_node = self._create_json_structure_nodes(doc_result, doc_node, user_id)
                    if structure_node:
                        created_nodes.append(structure_node)
                
                elif extension in ['csv', 'tsv']:
                    # Create column and data nodes for tabular data
                    column_nodes = self._create_csv_structure_nodes(doc_result, doc_node, user_id)
                    created_nodes.extend(column_nodes)
                
                elif extension in ['xls', 'xlsx']:
                    # Create sheet and column nodes for Excel data
                    sheet_nodes = self._create_excel_structure_nodes(doc_result, doc_node, user_id)
                    created_nodes.extend(sheet_nodes)
                
                elif extension in ['xml']:
                    # Create element structure nodes for XML
                    element_nodes = self._create_xml_structure_nodes(doc_result, doc_node, user_id)
                    created_nodes.extend(element_nodes)
            
            # Extract entities and relationships from text
            extract_result = self.processor.extract_entities_and_relationships(doc_result.get("text", ""))
            
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
                    "fileType": extension
                },
                "entities": [node.name for node in created_nodes if node.label not in ["Document", "Chunk", "Metadata"]],
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
    
    def _create_json_structure_nodes(self, doc_result: Dict[str, Any], doc_node, user_id: int):
        """Create nodes representing JSON structure"""
        try:
            metadata = doc_result.get("metadata", {})
            structure_type = metadata.get("structure", "")
            
            # Create a structure node based on the JSON structure
            structure_properties = {
                "name": f"JSON Structure ({structure_type})",
                "structure_type": structure_type
            }
            
            # Add keys for objects or count for arrays
            if structure_type == "object" and "keys" in metadata:
                structure_properties["keys"] = ", ".join(metadata["keys"])
                structure_properties["key_count"] = len(metadata["keys"])
            elif structure_type == "array" and "count" in metadata:
                structure_properties["item_count"] = metadata["count"]
                if "sample_keys" in metadata:
                    structure_properties["sample_keys"] = ", ".join(metadata["sample_keys"])
            
            structure_node = self.db.create_node("JSONStructure", structure_properties, user_id)
            
            if structure_node:
                # Link structure to document
                self.db.create_relationship(
                    doc_node.id, structure_node.id,
                    "HAS_STRUCTURE", {}, user_id
                )
                
                # Create nodes for each key in object or columns in array items
                if structure_type == "object" and "keys" in metadata:
                    for key in metadata["keys"]:
                        key_node = self.db.create_node("JSONKey", {
                            "name": key
                        }, user_id)
                        
                        if key_node:
                            self.db.create_relationship(
                                structure_node.id, key_node.id,
                                "HAS_PROPERTY", {}, user_id
                            )
                
                elif structure_type == "array" and "sample_keys" in metadata:
                    for key in metadata["sample_keys"]:
                        key_node = self.db.create_node("JSONKey", {
                            "name": key
                        }, user_id)
                        
                        if key_node:
                            self.db.create_relationship(
                                structure_node.id, key_node.id,
                                "HAS_PROPERTY", {}, user_id
                            )
            
            return structure_node
        except Exception as e:
            logger.error(f"Error creating JSON structure nodes: {str(e)}")
            return None
    
    def _create_csv_structure_nodes(self, doc_result: Dict[str, Any], doc_node, user_id: int):
        """Create nodes representing CSV structure"""
        try:
            metadata = doc_result.get("metadata", {})
            column_names = metadata.get("columns", [])
            row_count = metadata.get("row_count", 0)
            
            # Create structure node for the CSV data
            structure_node = self.db.create_node("CSVStructure", {
                "name": f"CSV Data ({len(column_names)} columns, {row_count} rows)",
                "column_count": len(column_names),
                "row_count": row_count
            }, user_id)
            
            if not structure_node:
                return []
            
            # Link structure to document
            self.db.create_relationship(
                doc_node.id, structure_node.id,
                "HAS_STRUCTURE", {}, user_id
            )
            
            # Create nodes for each column
            column_nodes = []
            for i, column_name in enumerate(column_names):
                column_node = self.db.create_node("CSVColumn", {
                    "name": column_name,
                    "index": i
                }, user_id)
                
                if column_node:
                    column_nodes.append(column_node)
                    
                    # Link column to structure
                    self.db.create_relationship(
                        structure_node.id, column_node.id,
                        "HAS_COLUMN", {"index": i}, user_id
                    )
            
            column_nodes.append(structure_node)
            return column_nodes
        except Exception as e:
            logger.error(f"Error creating CSV structure nodes: {str(e)}")
            return []
    
    def _create_excel_structure_nodes(self, doc_result: Dict[str, Any], doc_node, user_id: int):
        """Create nodes representing Excel workbook structure"""
        try:
            metadata = doc_result.get("metadata", {})
            sheet_names = metadata.get("sheets", [])
            
            # Create workbook structure node
            workbook_node = self.db.create_node("ExcelWorkbook", {
                "name": f"Excel Workbook ({len(sheet_names)} sheets)",
                "sheet_count": len(sheet_names)
            }, user_id)
            
            if not workbook_node:
                return []
            
            # Link workbook to document
            self.db.create_relationship(
                doc_node.id, workbook_node.id,
                "HAS_STRUCTURE", {}, user_id
            )
            
            # Create nodes for each sheet
            created_nodes = [workbook_node]
            
            for sheet_name in sheet_names:
                sheet_node = self.db.create_node("ExcelSheet", {
                    "name": sheet_name
                }, user_id)
                
                if sheet_node:
                    created_nodes.append(sheet_node)
                    
                    # Link sheet to workbook
                    self.db.create_relationship(
                        workbook_node.id, sheet_node.id,
                        "HAS_SHEET", {}, user_id
                    )
            
            return created_nodes
        except Exception as e:
            logger.error(f"Error creating Excel structure nodes: {str(e)}")
            return []
    
    def _create_xml_structure_nodes(self, doc_result: Dict[str, Any], doc_node, user_id: int):
        """Create nodes representing XML structure"""
        try:
            metadata = doc_result.get("metadata", {})
            root_tag = metadata.get("root_tag", "root")
            element_count = metadata.get("element_count", 0)
            attribute_count = metadata.get("attribute_count", 0)
            
            # Create structure node for XML document
            structure_node = self.db.create_node("XMLStructure", {
                "name": f"XML Document <{root_tag}>",
                "root_tag": root_tag,
                "element_count": element_count,
                "attribute_count": attribute_count
            }, user_id)
            
            if not structure_node:
                return []
            
            # Link structure to document
            self.db.create_relationship(
                doc_node.id, structure_node.id,
                "HAS_STRUCTURE", {}, user_id
            )
            
            # Create node for root element
            root_node = self.db.create_node("XMLElement", {
                "name": root_tag,
                "tag": root_tag,
                "is_root": True,
                "child_count": metadata.get("child_count", 0)
            }, user_id)
            
            created_nodes = [structure_node]
            
            if root_node:
                created_nodes.append(root_node)
                
                # Link root element to structure
                self.db.create_relationship(
                    structure_node.id, root_node.id,
                    "HAS_ROOT_ELEMENT", {}, user_id
                )
            
            return created_nodes
        except Exception as e:
            logger.error(f"Error creating XML structure nodes: {str(e)}")
            return []
            
    def get_document_entities(self, document_id: str, user_id: int) -> Dict[str, Any]:
        """Get entities and relationships associated with a document"""
        try:
            # First, get the document type to determine the appropriate query
            doc_type_result = self.db.query_subgraph("""
            MATCH (d:Document)
            WHERE d.id = $document_id AND d.created_by = $user_id
            RETURN d
            """, {
                "document_id": document_id,
                "user_id": user_id
            })
            
            # Default query for text documents
            query = """
            MATCH (d:Document)-[r1:MENTIONS]->(e)
            WHERE d.id = $document_id AND d.created_by = $user_id
            OPTIONAL MATCH (e)-[r2]-(related)
            WHERE related.created_by = $user_id AND related <> d
            RETURN d, r1, e, r2, related
            """
            
            # If we have structure information, include it in the query
            if len(doc_type_result.nodes) > 0:
                doc_node = doc_type_result.nodes[0]
                file_type = getattr(doc_node, "fileType", "")
                
                if file_type in ['json', 'csv', 'tsv', 'xml', 'xls', 'xlsx']:
                    # Query for structured data files
                    query = """
                    MATCH (d:Document)-[r1]->(s)
                    WHERE d.id = $document_id AND d.created_by = $user_id
                    OPTIONAL MATCH (s)-[r2]->(e)
                    WHERE e.created_by = $user_id
                    OPTIONAL MATCH (d)-[r3:MENTIONS]->(m)
                    WHERE m.created_by = $user_id
                    OPTIONAL MATCH (m)-[r4]-(related)
                    WHERE related.created_by = $user_id AND related <> d
                    RETURN d, r1, s, r2, e, r3, m, r4, related
                    """
            
            # Execute the query
            subgraph = self.db.query_subgraph(query, {
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