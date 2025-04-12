import json
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable
import logging
from config import Config

logger = logging.getLogger(__name__)

class Neo4jDatabase:
    def __init__(self):
        self.uri = Config.NEO4J_URI
        self.user = Config.NEO4J_USER
        self.password = Config.NEO4J_PASSWORD
        self.driver = None
        try:
            self.driver = GraphDatabase.driver(
                self.uri, 
                auth=(self.user, self.password)
            )
            logger.info("Connected to Neo4j database")
        except ServiceUnavailable as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise

    def close(self):
        if self.driver:
            self.driver.close()
            logger.info("Closed Neo4j connection")

    def verify_connectivity(self):
        with self.driver.session() as session:
            result = session.run("RETURN 1 AS num")
            return result.single()["num"] == 1

    def create_node(self, label, properties, user_id):
        """Create a node in the graph database"""
        with self.driver.session() as session:
            result = session.run(
                f"CREATE (n:{label} $properties) "
                "SET n.user_id = $user_id "
                "RETURN id(n) as id, labels(n) as labels, properties(n) as props",
                properties=properties,
                user_id=user_id
            )
            record = result.single()
            if record:
                return {
                    "id": record["id"],
                    "labels": record["labels"],
                    "properties": record["props"]
                }
            return None

    def create_relationship(self, start_node_id, end_node_id, rel_type, properties, user_id):
        """Create a relationship between two nodes"""
        with self.driver.session() as session:
            result = session.run(
                "MATCH (a), (b) "
                "WHERE id(a) = $start_id AND id(b) = $end_id "
                "CREATE (a)-[r:" + rel_type + " $properties]->(b) "
                "SET r.user_id = $user_id "
                "RETURN id(r) as id, type(r) as type, properties(r) as props, "
                "id(a) as start_id, id(b) as end_id",
                start_id=start_node_id,
                end_id=end_node_id,
                properties=properties,
                user_id=user_id
            )
            record = result.single()
            if record:
                return {
                    "id": record["id"],
                    "type": record["type"],
                    "properties": record["props"],
                    "start_node_id": record["start_id"],
                    "end_node_id": record["end_id"]
                }
            return None

    def get_nodes_by_user(self, user_id):
        """Get all nodes owned by a user"""
        with self.driver.session() as session:
            result = session.run(
                "MATCH (n) WHERE n.user_id = $user_id "
                "RETURN id(n) as id, labels(n) as labels, properties(n) as props",
                user_id=user_id
            )
            return [
                {
                    "id": record["id"],
                    "labels": record["labels"],
                    "properties": record["props"]
                }
                for record in result
            ]

    def get_relationships_by_user(self, user_id):
        """Get all relationships owned by a user"""
        with self.driver.session() as session:
            result = session.run(
                "MATCH (a)-[r]-(b) WHERE r.user_id = $user_id "
                "RETURN id(r) as id, type(r) as type, properties(r) as props, "
                "id(a) as start_id, id(b) as end_id",
                user_id=user_id
            )
            return [
                {
                    "id": record["id"],
                    "type": record["type"],
                    "properties": record["props"],
                    "start_node_id": record["start_id"],
                    "end_node_id": record["end_id"]
                }
                for record in result
            ]

    def query_subgraph(self, cypher_query, params=None):
        """Execute a Cypher query and return the subgraph"""
        if params is None:
            params = {}
            
        with self.driver.session() as session:
            result = session.run(cypher_query, params)
            nodes = []
            relationships = []
            node_ids = set()
            
            for record in result:
                # Extract nodes and relationships from the record
                for key, value in record.items():
                    if hasattr(value, "id") and hasattr(value, "labels"):  # Node
                        if value.id not in node_ids:
                            node_ids.add(value.id)
                            nodes.append({
                                "id": value.id,
                                "labels": list(value.labels),
                                "properties": dict(value)
                            })
                    elif hasattr(value, "id") and hasattr(value, "type"):  # Relationship
                        relationships.append({
                            "id": value.id,
                            "type": value.type,
                            "properties": dict(value),
                            "start_node_id": value.start_node.id,
                            "end_node_id": value.end_node.id
                        })
            
            return {
                "nodes": nodes,
                "relationships": relationships
            }

    def generate_graph_from_text(self, text, user_id):
        """Generate a knowledge graph from text (simplified approach)"""
        # In a real implementation, this would use NLP to extract entities and relationships
        # For this example, we'll use a simple approach
        
        words = text.split()
        entities = [word for word in words if len(word) > 5][:10]  # Get long words as entities
        
        nodes = []
        relationships = []
        
        # Create nodes for entities
        for i, entity in enumerate(entities[:5]):  # Limit to 5 entities
            node = self.create_node("Entity", {"name": entity, "source": "text"}, user_id)
            if node:
                nodes.append(node)
        
        # Create relationships between nodes
        for i in range(len(nodes) - 1):
            if i < len(nodes) - 1:
                rel = self.create_relationship(
                    nodes[i]["id"], 
                    nodes[i+1]["id"], 
                    "RELATED_TO", 
                    {"source": "text"}, 
                    user_id
                )
                if rel:
                    relationships.append(rel)
        
        return {
            "nodes": nodes,
            "relationships": relationships
        }

# Initialize the database
neo4j_db = Neo4jDatabase()
