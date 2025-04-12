import os
import json
import uuid
from typing import Dict, List, Any, Optional, Union
from neo4j import GraphDatabase, Driver, Record, Session
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

class Node(BaseModel):
    id: str
    label: str
    properties: Dict[str, Any] = {}
    name: str = ""

class Relationship(BaseModel):
    id: str
    source: str
    target: str
    type: str
    properties: Dict[str, Any] = {}

class GraphData(BaseModel):
    nodes: List[Node] = []
    links: List[Relationship] = []

class GraphStats(BaseModel):
    nodeCount: int = 0
    relationshipCount: int = 0

class GraphOverview(BaseModel):
    graphData: GraphData = Field(default_factory=GraphData)
    stats: GraphStats = Field(default_factory=GraphStats)

class InMemoryGraph:
    """In-memory implementation of a graph database for testing"""
    
    def __init__(self):
        self.nodes = {}  # id -> node
        self.relationships = {}  # id -> relationship
        self.user_nodes = {}  # user_id -> [node_ids]
        self.user_relationships = {}  # user_id -> [relationship_ids]
        
    def create_node(self, label: str, properties: Dict[str, Any], user_id: int) -> Node:
        """Create a node in the in-memory graph"""
        node_id = str(uuid.uuid4())
        
        # Extract name from properties or use a default
        name = properties.get("name", "") or properties.get("title", "") or f"{label}_{node_id[:8]}"
        
        node = Node(
            id=node_id,
            label=label,
            properties=properties,
            name=name
        )
        
        self.nodes[node_id] = node
        
        # Track user's nodes
        if user_id not in self.user_nodes:
            self.user_nodes[user_id] = []
        self.user_nodes[user_id].append(node_id)
        
        return node
    
    def create_relationship(self, start_node_id: str, end_node_id: str, 
                           rel_type: str, properties: Dict[str, Any], user_id: int) -> Relationship:
        """Create a relationship in the in-memory graph"""
        rel_id = str(uuid.uuid4())
        
        relationship = Relationship(
            id=rel_id,
            source=start_node_id,
            target=end_node_id,
            type=rel_type,
            properties=properties
        )
        
        self.relationships[rel_id] = relationship
        
        # Track user's relationships
        if user_id not in self.user_relationships:
            self.user_relationships[user_id] = []
        self.user_relationships[user_id].append(rel_id)
        
        return relationship
    
    def get_nodes_by_user(self, user_id: int) -> List[Node]:
        """Get all nodes owned by a user"""
        if user_id not in self.user_nodes:
            return []
        
        return [self.nodes[node_id] for node_id in self.user_nodes[user_id] 
                if node_id in self.nodes]
    
    def get_relationships_by_user(self, user_id: int) -> List[Relationship]:
        """Get all relationships owned by a user"""
        if user_id not in self.user_relationships:
            return []
        
        return [self.relationships[rel_id] for rel_id in self.user_relationships[user_id] 
                if rel_id in self.relationships]
    
    def get_graph_overview(self, user_id: int) -> GraphOverview:
        """Get an overview of the graph for a specific user"""
        nodes = self.get_nodes_by_user(user_id)
        relationships = self.get_relationships_by_user(user_id)
        
        graph_data = GraphData(
            nodes=nodes,
            links=relationships
        )
        
        stats = GraphStats(
            nodeCount=len(nodes),
            relationshipCount=len(relationships)
        )
        
        return GraphOverview(
            graphData=graph_data,
            stats=stats
        )
    
    def clear(self) -> None:
        """Clear all data"""
        self.nodes.clear()
        self.relationships.clear()
        self.user_nodes.clear()
        self.user_relationships.clear()
        
    def verify_connectivity(self) -> bool:
        """Always returns True for in-memory database"""
        return True


class Neo4jDatabase:
    def __init__(self):
        """Initialize the Neo4j database connection"""
        self.use_in_memory = os.getenv("USE_IN_MEMORY_DB", "false").lower() == "true"
        
        if self.use_in_memory:
            logger.info("Using in-memory graph database")
            self.in_memory_db = InMemoryGraph()
            self.driver = None
        else:
            uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
            user = os.getenv("NEO4J_USER", "neo4j")
            password = os.getenv("NEO4J_PASSWORD", "password")
            
            try:
                self.driver = GraphDatabase.driver(uri, auth=(user, password))
                logger.info("Neo4j connection established")
            except Exception as e:
                logger.error(f"Error connecting to Neo4j: {e}")
                logger.info("Falling back to in-memory database")
                self.driver = None
                self.use_in_memory = True
                self.in_memory_db = InMemoryGraph()
    
    def close(self):
        """Close the Neo4j connection"""
        if self.driver:
            self.driver.close()
    
    def verify_connectivity(self):
        """Check if the connection to Neo4j is working"""
        if self.use_in_memory:
            return self.in_memory_db.verify_connectivity()
            
        if not self.driver:
            return False
        
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1 as result")
                return result.single()["result"] == 1
        except Exception as e:
            logger.error(f"Neo4j connectivity check failed: {e}")
            return False
    
    def create_node(self, label: str, properties: Dict[str, Any], user_id: int) -> Optional[Node]:
        """Create a node in the graph database"""
        if self.use_in_memory:
            return self.in_memory_db.create_node(label, properties, user_id)
            
        if not self.driver:
            return None
        
        cypher_query = f"""
        CREATE (n:{label} $properties)
        SET n.created_by = $user_id, n.created_at = datetime()
        RETURN id(n) as id, labels(n) as labels, n
        """
        
        try:
            with self.driver.session() as session:
                result = session.run(cypher_query, properties=properties, user_id=user_id)
                record = result.single()
                
                if record:
                    node_id = str(record["id"])
                    node_labels = record["labels"]
                    node_props = dict(record["n"])
                    name = node_props.get("name", "") or node_props.get("title", "") or f"{label}_{node_id[:8]}"
                    
                    return Node(
                        id=node_id,
                        label=node_labels[0] if node_labels else label,
                        properties=node_props,
                        name=name
                    )
                return None
        except Exception as e:
            logger.error(f"Error creating node: {e}")
            return None
    
    def create_relationship(self, start_node_id: str, end_node_id: str, 
                           rel_type: str, properties: Dict[str, Any], user_id: int) -> Optional[Relationship]:
        """Create a relationship between two nodes"""
        if self.use_in_memory:
            return self.in_memory_db.create_relationship(
                start_node_id, end_node_id, rel_type, properties, user_id
            )
            
        if not self.driver:
            return None
        
        cypher_query = f"""
        MATCH (a), (b)
        WHERE id(a) = $start_id AND id(b) = $end_id
        CREATE (a)-[r:{rel_type} $properties]->(b)
        SET r.created_by = $user_id, r.created_at = datetime()
        RETURN id(r) as id, type(r) as type, startNode(r) as source, endNode(r) as target, r
        """
        
        try:
            with self.driver.session() as session:
                result = session.run(
                    cypher_query,
                    start_id=int(start_node_id),
                    end_id=int(end_node_id),
                    properties=properties,
                    user_id=user_id
                )
                record = result.single()
                
                if record:
                    rel_id = str(record["id"])
                    rel_type = record["type"]
                    source_id = str(record["source"].id)
                    target_id = str(record["target"].id)
                    rel_props = dict(record["r"])
                    
                    return Relationship(
                        id=rel_id,
                        source=source_id,
                        target=target_id,
                        type=rel_type,
                        properties=rel_props
                    )
                return None
        except Exception as e:
            logger.error(f"Error creating relationship: {e}")
            return None
    
    def get_nodes_by_user(self, user_id: int) -> List[Node]:
        """Get all nodes owned by a user"""
        if self.use_in_memory:
            return self.in_memory_db.get_nodes_by_user(user_id)
            
        if not self.driver:
            return []
        
        cypher_query = """
        MATCH (n)
        WHERE n.created_by = $user_id
        RETURN id(n) as id, labels(n) as labels, n
        """
        
        try:
            with self.driver.session() as session:
                result = session.run(cypher_query, user_id=user_id)
                nodes = []
                
                for record in result:
                    node_id = str(record["id"])
                    node_labels = record["labels"]
                    node_props = dict(record["n"])
                    name = node_props.get("name", "") or node_props.get("title", "") or f"{node_labels[0]}_{node_id[:8]}"
                    
                    nodes.append(Node(
                        id=node_id,
                        label=node_labels[0] if node_labels else "Node",
                        properties=node_props,
                        name=name
                    ))
                
                return nodes
        except Exception as e:
            logger.error(f"Error getting user nodes: {e}")
            return []
    
    def get_relationships_by_user(self, user_id: int) -> List[Relationship]:
        """Get all relationships owned by a user"""
        if self.use_in_memory:
            return self.in_memory_db.get_relationships_by_user(user_id)
            
        if not self.driver:
            return []
        
        cypher_query = """
        MATCH (a)-[r]->(b)
        WHERE r.created_by = $user_id
        RETURN id(r) as id, type(r) as type, id(a) as source, id(b) as target, r
        """
        
        try:
            with self.driver.session() as session:
                result = session.run(cypher_query, user_id=user_id)
                relationships = []
                
                for record in result:
                    rel_id = str(record["id"])
                    rel_type = record["type"]
                    source_id = str(record["source"])
                    target_id = str(record["target"])
                    rel_props = dict(record["r"])
                    
                    relationships.append(Relationship(
                        id=rel_id,
                        source=source_id,
                        target=target_id,
                        type=rel_type,
                        properties=rel_props
                    ))
                
                return relationships
        except Exception as e:
            logger.error(f"Error getting user relationships: {e}")
            return []
    
    def get_graph_overview(self, user_id: int) -> GraphOverview:
        """Get an overview of the graph for a specific user"""
        if self.use_in_memory:
            return self.in_memory_db.get_graph_overview(user_id)
        
        nodes = self.get_nodes_by_user(user_id)
        relationships = self.get_relationships_by_user(user_id)
        
        graph_data = GraphData(
            nodes=nodes,
            links=relationships
        )
        
        stats = GraphStats(
            nodeCount=len(nodes),
            relationshipCount=len(relationships)
        )
        
        return GraphOverview(
            graphData=graph_data,
            stats=stats
        )
    
    def query_subgraph(self, cypher_query: str, params: Dict[str, Any] = None) -> GraphData:
        """Execute a Cypher query and return the subgraph"""
        if params is None:
            params = {}
        
        if self.use_in_memory:
            # For in-memory, we'll return a subset of the user's graph as this is just for demo
            user_id = params.get("user_id", 1)
            nodes = self.in_memory_db.get_nodes_by_user(user_id)[:5]  # Limit to 5 nodes
            
            # Get relationships that connect these nodes
            node_ids = {node.id for node in nodes}
            all_rels = self.in_memory_db.get_relationships_by_user(user_id)
            rels = [rel for rel in all_rels if rel.source in node_ids and rel.target in node_ids]
            
            return GraphData(nodes=nodes, links=rels)
            
        if not self.driver:
            return GraphData()
        
        try:
            with self.driver.session() as session:
                result = session.run(cypher_query, **params)
                
                nodes_dict = {}  # id -> node
                relationships = []
                
                for record in result:
                    for key, value in record.items():
                        # Handle nodes
                        if hasattr(value, "id") and hasattr(value, "labels"):
                            node_id = str(value.id)
                            if node_id not in nodes_dict:
                                node_props = dict(value)
                                node_labels = list(value.labels)
                                name = node_props.get("name", "") or node_props.get("title", "") or f"{node_labels[0] if node_labels else 'Node'}_{node_id[:8]}"
                                
                                nodes_dict[node_id] = Node(
                                    id=node_id,
                                    label=node_labels[0] if node_labels else "Node",
                                    properties=node_props,
                                    name=name
                                )
                        
                        # Handle relationships
                        elif hasattr(value, "start_node") and hasattr(value, "end_node") and hasattr(value, "type"):
                            rel_id = str(value.id)
                            rel_type = value.type
                            source_id = str(value.start_node.id)
                            target_id = str(value.end_node.id)
                            rel_props = dict(value)
                            
                            # Create source and target nodes if they don't exist
                            if source_id not in nodes_dict:
                                source_node = value.start_node
                                source_props = dict(source_node)
                                source_labels = list(source_node.labels)
                                source_name = source_props.get("name", "") or source_props.get("title", "") or f"{source_labels[0] if source_labels else 'Node'}_{source_id[:8]}"
                                
                                nodes_dict[source_id] = Node(
                                    id=source_id,
                                    label=source_labels[0] if source_labels else "Node",
                                    properties=source_props,
                                    name=source_name
                                )
                                
                            if target_id not in nodes_dict:
                                target_node = value.end_node
                                target_props = dict(target_node)
                                target_labels = list(target_node.labels)
                                target_name = target_props.get("name", "") or target_props.get("title", "") or f"{target_labels[0] if target_labels else 'Node'}_{target_id[:8]}"
                                
                                nodes_dict[target_id] = Node(
                                    id=target_id,
                                    label=target_labels[0] if target_labels else "Node",
                                    properties=target_props,
                                    name=target_name
                                )
                            
                            # Add relationship
                            relationships.append(Relationship(
                                id=rel_id,
                                source=source_id,
                                target=target_id,
                                type=rel_type,
                                properties=rel_props
                            ))
                
                return GraphData(
                    nodes=list(nodes_dict.values()),
                    links=relationships
                )
        except Exception as e:
            logger.error(f"Error executing Cypher query: {e}")
            return GraphData()