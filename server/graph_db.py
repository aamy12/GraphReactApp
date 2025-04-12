import os
import logging
import json
import uuid
from typing import Dict, List, Any, Optional, Union
import re

try:
    import neo4j
except ImportError:
    neo4j = None

try:
    from pydantic import BaseModel, Field
except ImportError:
    from typing import NamedTuple
    class BaseModel:
        def dict(self):
            return self.__dict__
            
    def Field(default_factory=None, **kwargs):
        return default_factory() if callable(default_factory) else None

# Configure logging
logger = logging.getLogger(__name__)

# Data models
class Node(BaseModel):
    id: str
    label: str
    properties: Dict[str, Any] = {}
    name: str = ""  # For visualization purposes
    
    def __init__(self, **data):
        super().__init__(**data)
        # Set name from properties if available
        if "name" not in data and "name" in self.properties:
            self.name = self.properties["name"]
        elif "name" not in data and "title" in self.properties:
            self.name = self.properties["title"]

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
        self.nodes = []
        self.relationships = []
        self.id_counter = 0
    
    def create_node(self, label: str, properties: Dict[str, Any], user_id: int) -> Node:
        """Create a node in the in-memory graph"""
        self.id_counter += 1
        node_id = str(self.id_counter)
        
        # Add user ID to properties
        properties["created_by"] = user_id
        
        node = Node(
            id=node_id,
            label=label,
            properties=properties,
            name=properties.get("name", f"{label}-{node_id}")
        )
        
        self.nodes.append(node)
        return node
    
    def create_relationship(self, start_node_id: str, end_node_id: str, 
                           rel_type: str, properties: Dict[str, Any], user_id: int) -> Optional[Relationship]:
        """Create a relationship in the in-memory graph"""
        # Check if both nodes exist
        start_node = next((n for n in self.nodes if n.id == start_node_id), None)
        end_node = next((n for n in self.nodes if n.id == end_node_id), None)
        
        if not start_node or not end_node:
            return None
        
        self.id_counter += 1
        rel_id = str(self.id_counter)
        
        # Add user ID to properties
        properties["created_by"] = user_id
        
        relationship = Relationship(
            id=rel_id,
            source=start_node_id,
            target=end_node_id,
            type=rel_type,
            properties=properties
        )
        
        self.relationships.append(relationship)
        return relationship
    
    def get_nodes_by_user(self, user_id: int) -> List[Node]:
        """Get all nodes owned by a user"""
        return [n for n in self.nodes if n.properties.get("created_by") == user_id]
    
    def get_relationships_by_user(self, user_id: int) -> List[Relationship]:
        """Get all relationships owned by a user"""
        return [r for r in self.relationships if r.properties.get("created_by") == user_id]
    
    def get_graph_overview(self, user_id: int) -> GraphOverview:
        """Get an overview of the graph for a specific user"""
        user_nodes = self.get_nodes_by_user(user_id)
        user_relationships = self.get_relationships_by_user(user_id)
        
        # Limit to a reasonable number for visualization
        visualized_nodes = user_nodes[:100]
        
        # Only include relationships where both nodes are in the visualized set
        visualized_node_ids = {n.id for n in visualized_nodes}
        visualized_relationships = [
            r for r in user_relationships 
            if r.source in visualized_node_ids and r.target in visualized_node_ids
        ][:200]  # Limit to 200 relationships
        
        return GraphOverview(
            graphData=GraphData(
                nodes=visualized_nodes,
                links=visualized_relationships
            ),
            stats=GraphStats(
                nodeCount=len(user_nodes),
                relationshipCount=len(user_relationships)
            )
        )
    
    def clear(self) -> None:
        """Clear all data"""
        self.nodes = []
        self.relationships = []
        self.id_counter = 0
    
    def verify_connectivity(self) -> bool:
        """Always returns True for in-memory database"""
        return True

class Neo4jDatabase:
    def __init__(self):
        """Initialize the Neo4j database connection"""
        # Check if we should use in-memory database
        self.use_in_memory = os.environ.get('USE_IN_MEMORY_DB', 'true').lower() == 'true'
        self.driver = None
        self.in_memory = None
        
        # Connect based on the setting
        self.initialize_connection()
            
    def initialize_connection(self):
        """Initialize or reinitialize the database connection"""
        # Clean up existing connections if any
        if self.driver:
            try:
                self.driver.close()
            except Exception:
                pass
            self.driver = None
        
        self.in_memory = None
        
        # Use in-memory if explicitly requested
        if self.use_in_memory:
            logger.info("Using in-memory graph database (as configured)")
            self.in_memory = InMemoryGraph()
            return
            
        # Check if Neo4j driver is available
        if neo4j is None:
            logger.warning("Neo4j driver not available, falling back to in-memory database")
            self.in_memory = InMemoryGraph()
            return
            
        # Try to connect to Neo4j
        try:
            uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
            user = os.environ.get('NEO4J_USER', 'neo4j')
            password = os.environ.get('NEO4J_PASSWORD', 'password')
            
            logger.info(f"Attempting to connect to Neo4j at {uri}")
            self.driver = neo4j.GraphDatabase.driver(uri, auth=(user, password))
            
            # Test the connection
            with self.driver.session() as session:
                result = session.run("RETURN 1 AS result").single()
                if not result or result.get("result") != 1:
                    raise Exception("Failed to validate Neo4j connection")
            
            logger.info(f"Successfully connected to Neo4j at {uri}")
            
            # Initialize schema with constraints
            self._init_schema()
            
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            logger.warning("Falling back to in-memory database")
            
            if self.driver:
                try:
                    self.driver.close()
                except Exception:
                    pass
                
            self.driver = None
            self.in_memory = InMemoryGraph()
    
    def close(self):
        """Close the Neo4j connection"""
        if self.driver:
            self.driver.close()
    
    def verify_connectivity(self):
        """Check if the connection to Neo4j is working"""
        if self.in_memory:
            return self.in_memory.verify_connectivity()
            
        if not self.driver:
            return False
            
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1 AS result").single()
                return result and result.get("result") == 1
        except Exception as e:
            logger.error(f"Neo4j connectivity check failed: {e}")
            return False
    
    def _init_schema(self):
        """Initialize Neo4j schema with constraints"""
        if not self.driver:
            return
            
        try:
            with self.driver.session() as session:
                # Check if constraints exist
                constraints = session.run("SHOW CONSTRAINTS").data()
                if not any("ON (n:Node)" in constraint.get("description", "") for constraint in constraints):
                    # Create constraint for Node.id
                    session.run("CREATE CONSTRAINT ON (n:Node) ASSERT n.id IS UNIQUE")
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j schema: {e}")
    
    def create_node(self, label: str, properties: Dict[str, Any], user_id: int) -> Optional[Node]:
        """Create a node in the graph database"""
        # Use in-memory if Neo4j is not available
        if self.in_memory:
            return self.in_memory.create_node(label, properties, user_id)
        
        if not self.driver:
            return None
        
        try:
            with self.driver.session() as session:
                # Generate a UUID for the node
                node_id = str(uuid.uuid4())
                
                # Add user ID and current timestamp
                node_props = {
                    "id": node_id,
                    "created_by": user_id,
                    "created_at": neo4j.time.DateTime.now(),
                    **properties
                }
                
                # Clean property keys (Neo4j doesn't allow dots in property names)
                clean_props = {}
                for k, v in node_props.items():
                    clean_key = re.sub(r'[^\w]', '_', k)
                    clean_props[clean_key] = v
                
                # Create the node
                result = session.run(
                    f"CREATE (n:{label}) SET n = $props RETURN n",
                    props=clean_props
                )
                
                record = result.single()
                if not record:
                    return None
                
                # Convert Neo4j node to Node model
                neo4j_node = record["n"]
                return Node(
                    id=node_id,
                    label=label,
                    properties={k: v for k, v in dict(neo4j_node).items() if k != "id"},
                    name=properties.get("name", "")
                )
                
        except Exception as e:
            logger.error(f"Error creating node: {e}")
            return None
    
    def create_relationship(self, start_node_id: str, end_node_id: str, 
                           rel_type: str, properties: Dict[str, Any], user_id: int) -> Optional[Relationship]:
        """Create a relationship between two nodes"""
        # Use in-memory if Neo4j is not available
        if self.in_memory:
            return self.in_memory.create_relationship(start_node_id, end_node_id, rel_type, properties, user_id)
        
        if not self.driver:
            return None
        
        try:
            with self.driver.session() as session:
                # Generate a UUID for the relationship
                rel_id = str(uuid.uuid4())
                
                # Add user ID and current timestamp
                rel_props = {
                    "id": rel_id,
                    "created_by": user_id,
                    "created_at": neo4j.time.DateTime.now(),
                    **properties
                }
                
                # Clean property keys
                clean_props = {}
                for k, v in rel_props.items():
                    clean_key = re.sub(r'[^\w]', '_', k)
                    clean_props[clean_key] = v
                
                # Create the relationship
                query = f"""
                MATCH (a), (b)
                WHERE a.id = $start_id AND b.id = $end_id
                CREATE (a)-[r:{rel_type}]->(b)
                SET r = $props
                RETURN r, a, b
                """
                
                result = session.run(
                    query,
                    start_id=start_node_id,
                    end_id=end_node_id,
                    props=clean_props
                )
                
                record = result.single()
                if not record:
                    return None
                
                # Convert Neo4j relationship to Relationship model
                return Relationship(
                    id=rel_id,
                    source=start_node_id,
                    target=end_node_id,
                    type=rel_type,
                    properties={k: v for k, v in dict(record["r"]).items() if k != "id"}
                )
                
        except Exception as e:
            logger.error(f"Error creating relationship: {e}")
            return None
    
    def get_nodes_by_user(self, user_id: int) -> List[Node]:
        """Get all nodes owned by a user"""
        # Use in-memory if Neo4j is not available
        if self.in_memory:
            return self.in_memory.get_nodes_by_user(user_id)
        
        if not self.driver:
            return []
        
        try:
            with self.driver.session() as session:
                result = session.run(
                    "MATCH (n) WHERE n.created_by = $user_id RETURN n",
                    user_id=user_id
                )
                
                nodes = []
                for record in result:
                    neo4j_node = record["n"]
                    node_props = dict(neo4j_node)
                    node_id = node_props.get("id", str(uuid.uuid4()))
                    
                    # Determine node label
                    labels = list(neo4j_node.labels)
                    label = labels[0] if labels else "Node"
                    
                    nodes.append(Node(
                        id=node_id,
                        label=label,
                        properties={k: v for k, v in node_props.items() if k != "id"},
                        name=node_props.get("name", "")
                    ))
                
                return nodes
                
        except Exception as e:
            logger.error(f"Error getting nodes: {e}")
            return []
    
    def get_relationships_by_user(self, user_id: int) -> List[Relationship]:
        """Get all relationships owned by a user"""
        # Use in-memory if Neo4j is not available
        if self.in_memory:
            return self.in_memory.get_relationships_by_user(user_id)
        
        if not self.driver:
            return []
        
        try:
            with self.driver.session() as session:
                result = session.run(
                    """
                    MATCH (a)-[r]->(b)
                    WHERE r.created_by = $user_id
                    RETURN r, a.id as source, b.id as target, type(r) as rel_type
                    """,
                    user_id=user_id
                )
                
                relationships = []
                for record in result:
                    neo4j_rel = record["r"]
                    rel_props = dict(neo4j_rel)
                    rel_id = rel_props.get("id", str(uuid.uuid4()))
                    
                    relationships.append(Relationship(
                        id=rel_id,
                        source=record["source"],
                        target=record["target"],
                        type=record["rel_type"],
                        properties={k: v for k, v in rel_props.items() if k != "id"}
                    ))
                
                return relationships
                
        except Exception as e:
            logger.error(f"Error getting relationships: {e}")
            return []
    
    def get_graph_overview(self, user_id: int) -> GraphOverview:
        """Get an overview of the graph for a specific user"""
        # Use in-memory if Neo4j is not available
        if self.in_memory:
            return self.in_memory.get_graph_overview(user_id)
        
        if not self.driver:
            return GraphOverview()
        
        try:
            with self.driver.session() as session:
                # Get node count
                node_count_result = session.run(
                    "MATCH (n) WHERE n.created_by = $user_id RETURN count(n) as count",
                    user_id=user_id
                )
                node_count = node_count_result.single()["count"]
                
                # Get relationship count
                rel_count_result = session.run(
                    "MATCH ()-[r]->() WHERE r.created_by = $user_id RETURN count(r) as count",
                    user_id=user_id
                )
                rel_count = rel_count_result.single()["count"]
                
                # Get a sample of nodes and relationships for visualization
                # Limit to 100 nodes and 200 relationships for performance
                graph_result = session.run(
                    """
                    MATCH (n)
                    WHERE n.created_by = $user_id
                    WITH n LIMIT 100
                    OPTIONAL MATCH (n)-[r]-(m)
                    WHERE m.created_by = $user_id
                    RETURN n, r, m
                    LIMIT 200
                    """,
                    user_id=user_id
                )
                
                nodes = {}
                relationships = []
                
                for record in graph_result:
                    # Process start node
                    if record["n"] and record["n"]["id"] not in nodes:
                        neo4j_node = record["n"]
                        node_props = dict(neo4j_node)
                        node_id = node_props.get("id")
                        
                        # Determine node label
                        labels = list(neo4j_node.labels)
                        label = labels[0] if labels else "Node"
                        
                        nodes[node_id] = Node(
                            id=node_id,
                            label=label,
                            properties={k: v for k, v in node_props.items() if k != "id"},
                            name=node_props.get("name", "")
                        )
                    
                    # Process end node
                    if record["m"] and record["m"]["id"] not in nodes:
                        neo4j_node = record["m"]
                        node_props = dict(neo4j_node)
                        node_id = node_props.get("id")
                        
                        # Determine node label
                        labels = list(neo4j_node.labels)
                        label = labels[0] if labels else "Node"
                        
                        nodes[node_id] = Node(
                            id=node_id,
                            label=label,
                            properties={k: v for k, v in node_props.items() if k != "id"},
                            name=node_props.get("name", "")
                        )
                    
                    # Process relationship
                    if record["r"]:
                        neo4j_rel = record["r"]
                        rel_props = dict(neo4j_rel)
                        rel_id = rel_props.get("id", str(uuid.uuid4()))
                        
                        relationships.append(Relationship(
                            id=rel_id,
                            source=record["n"]["id"],
                            target=record["m"]["id"],
                            type=neo4j_rel.type,
                            properties={k: v for k, v in rel_props.items() if k != "id"}
                        ))
                
                return GraphOverview(
                    graphData=GraphData(
                        nodes=list(nodes.values()),
                        links=relationships
                    ),
                    stats=GraphStats(
                        nodeCount=node_count,
                        relationshipCount=rel_count
                    )
                )
                
        except Exception as e:
            logger.error(f"Error getting graph overview: {e}")
            return GraphOverview()
    
    def query_subgraph(self, cypher_query: str, params: Dict[str, Any] = None) -> GraphData:
        """Execute a Cypher query and return the subgraph"""
        if params is None:
            params = {}
            
        # Use in-memory if Neo4j is not available
        if self.in_memory:
            # For in-memory, we'll just return a sample of the graph
            # In a real implementation, we would parse and execute the Cypher query
            user_id = params.get("user_id")
            if user_id:
                overview = self.in_memory.get_graph_overview(user_id)
                return overview.graphData
            return GraphData()
        
        if not self.driver:
            return GraphData()
        
        try:
            with self.driver.session() as session:
                result = session.run(cypher_query, **params)
                
                # Process results and extract nodes and relationships
                nodes = {}
                relationships = []
                
                for record in result:
                    # Process each item in the record
                    for value in record.values():
                        if isinstance(value, neo4j.graph.Node):
                            # Process Neo4j node
                            neo4j_node = value
                            node_props = dict(neo4j_node)
                            node_id = node_props.get("id")
                            
                            if node_id and node_id not in nodes:
                                # Determine node label
                                labels = list(neo4j_node.labels)
                                label = labels[0] if labels else "Node"
                                
                                nodes[node_id] = Node(
                                    id=node_id,
                                    label=label,
                                    properties={k: v for k, v in node_props.items() if k != "id"},
                                    name=node_props.get("name", "")
                                )
                        
                        elif isinstance(value, neo4j.graph.Relationship):
                            # Process Neo4j relationship
                            neo4j_rel = value
                            rel_props = dict(neo4j_rel)
                            rel_id = rel_props.get("id", str(uuid.uuid4()))
                            
                            # Get start and end node IDs
                            start_node = dict(neo4j_rel.start_node)
                            end_node = dict(neo4j_rel.end_node)
                            
                            # Add nodes if they don't exist
                            start_id = start_node.get("id")
                            end_id = end_node.get("id")
                            
                            if start_id and start_id not in nodes:
                                start_labels = list(neo4j_rel.start_node.labels)
                                start_label = start_labels[0] if start_labels else "Node"
                                
                                nodes[start_id] = Node(
                                    id=start_id,
                                    label=start_label,
                                    properties={k: v for k, v in start_node.items() if k != "id"},
                                    name=start_node.get("name", "")
                                )
                            
                            if end_id and end_id not in nodes:
                                end_labels = list(neo4j_rel.end_node.labels)
                                end_label = end_labels[0] if end_labels else "Node"
                                
                                nodes[end_id] = Node(
                                    id=end_id,
                                    label=end_label,
                                    properties={k: v for k, v in end_node.items() if k != "id"},
                                    name=end_node.get("name", "")
                                )
                            
                            # Create relationship
                            relationships.append(Relationship(
                                id=rel_id,
                                source=start_id,
                                target=end_id,
                                type=neo4j_rel.type,
                                properties={k: v for k, v in rel_props.items() if k != "id"}
                            ))
                
                return GraphData(
                    nodes=list(nodes.values()),
                    links=relationships
                )
                
        except Exception as e:
            logger.error(f"Error executing Cypher query: {e}")
            return GraphData()