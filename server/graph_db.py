import os
import logging
import networkx as nx
from typing import Dict, List, Any, Optional
from pydantic import BaseModel
from langchain.graphs import NetworkxEntityGraph
from langchain_community.graphs import Neo4jGraph
from datetime import datetime
import re

# Configure logging
logger = logging.getLogger(__name__)

# Data models
class Node(BaseModel):
    id: str
    label: str
    properties: Dict[str, Any] = {}
    name: str = ""

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
    graphData: GraphData
    stats: GraphStats

class InMemoryGraph:
    def __init__(self):
        self.graph = NetworkxEntityGraph()
        self.G = nx.MultiDiGraph()

    def create_node(self, label: str, properties: Dict[str, Any], user_id: int) -> Optional[Node]:
        node_id = str(len(self.G.nodes) + 1)
        properties["id"] = node_id
        properties["label"] = label
        properties["created_by"] = user_id
        properties["created_at"] = datetime.now().isoformat()

        self.G.add_node(node_id, **properties)
        return Node(id=node_id, label=label, properties=properties, name=properties.get("name", ""))

    def create_relationship(self, start_id: str, end_id: str, rel_type: str, 
                          properties: Dict[str, Any], user_id: int) -> Optional[Relationship]:
        rel_id = str(len(self.G.edges) + 1)
        properties["id"] = rel_id
        properties["created_by"] = user_id
        properties["created_at"] = datetime.now().isoformat()

        self.G.add_edge(start_id, end_id, key=rel_id, type=rel_type, **properties)
        return Relationship(
            id=rel_id,
            source=start_id,
            target=end_id,
            type=rel_type,
            properties=properties
        )

    def get_graph_overview(self, user_id: int) -> GraphOverview:
        nodes = []
        relationships = []

        for node_id, data in self.G.nodes(data=True):
            if data.get("created_by") == user_id:
                nodes.append(Node(
                    id=node_id,
                    label=data.get("label", "Node"),
                    properties=data,
                    name=data.get("name", "")
                ))

        for u, v, k, data in self.G.edges(data=True, keys=True):
            if data.get("created_by") == user_id:
                relationships.append(Relationship(
                    id=k,
                    source=u,
                    target=v,
                    type=data.get("type", "RELATED_TO"),
                    properties=data
                ))

        return GraphOverview(
            graphData=GraphData(nodes=nodes, links=relationships),
            stats=GraphStats(
                nodeCount=len(nodes),
                relationshipCount=len(relationships)
            )
        )

    def query_subgraph(self, query: str, params: Dict[str, Any] = None) -> GraphData:
        user_id = params.get("user_id") if params else None
        if not user_id:
            return GraphData()

        # For simplicity, return user's full graph
        overview = self.get_graph_overview(user_id)
        return overview.graphData

    def verify_connectivity(self) -> bool:
        return True


class Neo4jDatabase:
    def __init__(self, uri: str, user: str, password: str):
        self.graph = Neo4jGraph(
            url=uri,
            username=user,
            password=password
        )

    def create_node(self, label: str, properties: Dict[str, Any], user_id: int) -> Optional[Node]:
        properties["created_by"] = user_id
        properties["created_at"] = datetime.now().isoformat()
        query = f"""
        CREATE (n:{label} $props)
        RETURN n
        """
        result = self.graph.query(query, {"props": properties})
        if result:
            node = result[0]["n"]
            return Node(
                id=node.id,
                label=label,
                properties=dict(node),
                name=properties.get("name", "")
            )
        return None

    def create_relationship(self, start_id: str, end_id: str, rel_type: str,
                          properties: Dict[str, Any], user_id: int) -> Optional[Relationship]:
        properties["created_by"] = user_id
        properties["created_at"] = datetime.now().isoformat()
        query = f"""
        MATCH (a), (b)
        WHERE ID(a) = $start_id AND ID(b) = $end_id
        CREATE (a)-[r:{rel_type} $props]->(b)
        RETURN r
        """
        result = self.graph.query(query, {
            "start_id": start_id,
            "end_id": end_id,
            "props": properties
        })
        if result:
            rel = result[0]["r"]
            return Relationship(
                id=rel.id,
                source=start_id,
                target=end_id,
                type=rel_type,
                properties=dict(rel)
            )
        return None

    def get_graph_overview(self, user_id: int) -> GraphOverview:
        query = """
        MATCH (n)
        WHERE n.created_by = $user_id
        OPTIONAL MATCH (n)-[r]-(m)
        WHERE m.created_by = $user_id
        RETURN n, r, m
        """
        result = self.graph.query(query, {"user_id": user_id})

        nodes = {}
        relationships = []

        for row in result:
            if "n" in row:
                node = row["n"]
                nodes[node.id] = Node(
                    id=node.id,
                    label=node.labels[0],
                    properties=dict(node),
                    name=node.get("name", "")
                )

            if "m" in row:
                node = row["m"]
                nodes[node.id] = Node(
                    id=node.id,
                    label=node.labels[0],
                    properties=dict(node),
                    name=node.get("name", "")
                )

            if "r" in row:
                rel = row["r"]
                relationships.append(Relationship(
                    id=rel.id,
                    source=rel.start_node.id,
                    target=rel.end_node.id,
                    type=rel.type,
                    properties=dict(rel)
                ))

        return GraphOverview(
            graphData=GraphData(
                nodes=list(nodes.values()),
                links=relationships
            ),
            stats=GraphStats(
                nodeCount=len(nodes),
                relationshipCount=len(relationships)
            )
        )

    def query_subgraph(self, query: str, params: Dict[str, Any] = None) -> GraphData:
        result = self.graph.query(query, params or {})

        nodes = {}
        relationships = []

        for row in result:
            for value in row.values():
                if hasattr(value, "labels"):  # Node
                    nodes[value.id] = Node(
                        id=value.id,
                        label=value.labels[0],
                        properties=dict(value),
                        name=value.get("name", "")
                    )
                elif hasattr(value, "type"):  # Relationship
                    relationships.append(Relationship(
                        id=value.id,
                        source=value.start_node.id,
                        target=value.end_node.id,
                        type=value.type,
                        properties=dict(value)
                    ))

        return GraphData(
            nodes=list(nodes.values()),
            links=relationships
        )

    def verify_connectivity(self):
        try:
            self.graph.query("RETURN 1")
            return True
        except Exception as e:
            logger.error(f"Neo4j connectivity check failed: {e}")
            return False


class DatabaseManager:
    def __init__(self):
        self.use_neo4j = os.getenv("USE_NEO4J", "false").lower() == "true"
        self.db = None
        self.initialize_connection()

    def initialize_connection(self):
        if self.use_neo4j:
            try:
                uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
                user = os.getenv("NEO4J_USER", "neo4j")
                password = os.getenv("NEO4J_PASSWORD", "password")
                self.db = Neo4jDatabase(uri, user, password)
                logger.info("Connected to Neo4j database")
            except Exception as e:
                logger.error(f"Failed to connect to Neo4j: {e}")
                logger.info("Falling back to in-memory database")
                self.db = InMemoryGraph()
        else:
            logger.info("Using in-memory database")
            self.db = InMemoryGraph()

    def get_database(self):
        return self.db

# Create singleton instance
db_manager = DatabaseManager()