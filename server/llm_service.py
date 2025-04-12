import os
import logging
from typing import Dict, List, Any, Optional, Union
import json

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain.schema.messages import SystemMessage
from langchain.chains import LLMChain

from .graph_db import GraphData, Node, Relationship

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        """Initialize the LLM service"""
        # Check if API key is available
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = None
        
        if self.api_key:
            try:
                self.model = ChatOpenAI(
                    temperature=0.2,
                    api_key=self.api_key,
                    model="gpt-3.5-turbo",
                )
            except Exception as e:
                logger.error(f"Error initializing ChatOpenAI: {e}")
        else:
            logger.warning("No OpenAI API key found. LLM service will not be available.")

    def is_available(self) -> bool:
        """Check if the LLM service is available"""
        return self.model is not None
    
    def parse_document_to_graph(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Parse a document and extract entities and relationships to create a knowledge graph
        
        Args:
            text: The document text to parse
            
        Returns:
            Dict with "entities" and "relationships" lists
        """
        if not self.model:
            # Return a basic implementation if no LLM available
            from .document_processor import document_processor
            return document_processor.extract_entities_and_relationships(text)
        
        # Define the prompt for entity and relationship extraction
        system_prompt = """
        You are an expert at extracting structured information from text. Your task is to identify key entities and their relationships from the provided text.

        For each entity, extract:
        1. The entity name
        2. The entity type (e.g., Person, Organization, Concept, Location, etc.)
        3. Any relevant attributes mentioned in the text

        For relationships, extract:
        1. The source entity
        2. The target entity
        3. The relationship type (e.g., WORKS_FOR, CREATED, LOCATED_IN)
        4. Any attributes of the relationship

        Provide the output as a JSON object with two keys:
        - "entities": a list of entity objects
        - "relationships": a list of relationship objects

        Entity object format:
        {
            "name": "entity name",
            "type": "entity type",
            "attributes": {
                "attribute1": "value1",
                "attribute2": "value2"
            }
        }

        Relationship object format:
        {
            "source": "source entity name",
            "target": "target entity name",
            "type": "relationship type",
            "attributes": {
                "attribute1": "value1"
            }
        }
        """
        
        human_prompt = """
        Extract entities and relationships from the following text:
        
        {text}
        
        Remember to output valid JSON with "entities" and "relationships" keys.
        """
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=system_prompt),
            HumanMessagePromptTemplate.from_template(human_prompt)
        ])
        
        # Create a chain
        chain = LLMChain(llm=self.model, prompt=prompt)
        
        try:
            # Run the chain
            result = chain.invoke({"text": text[:4000]})  # Limit to first 4000 chars for token limits
            
            # Parse the JSON response
            response_text = result.get("text", "")
            
            # Extract JSON from the response (it might contain markdown formatting)
            json_str = response_text.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].strip()
            
            parsed_data = json.loads(json_str)
            
            # Make sure the expected keys are present
            if "entities" not in parsed_data:
                parsed_data["entities"] = []
            if "relationships" not in parsed_data:
                parsed_data["relationships"] = []
                
            return parsed_data
        
        except Exception as e:
            logger.error(f"Error in parse_document_to_graph: {e}")
            # Fall back to basic implementation
            from .document_processor import document_processor
            return document_processor.extract_entities_and_relationships(text)

    def generate_query(self, user_query: str, subgraph: GraphData) -> Dict[str, str]:
        """
        Process a natural language query against the knowledge graph
        
        Args:
            user_query: The user's natural language query
            subgraph: The relevant subgraph data
            
        Returns:
            Dict with the generated response
        """
        if not self.model:
            # Generate a basic response if no LLM available
            return self._generate_basic_response(user_query, subgraph)
        
        # Prepare the context from the subgraph
        context = self._prepare_context(subgraph)
        
        # Define the prompt
        system_prompt = """
        You are a knowledge graph expert assistant. You help users find information in their knowledge graph.
        
        You'll be given:
        1. A query from the user
        2. A subgraph of nodes and relationships that might be relevant to the query
        
        Your task is to analyze the subgraph and provide a clear, informative response that answers the user's query.
        
        When responding:
        - Focus only on the information available in the provided subgraph
        - Explain the connections between entities when relevant
        - If the subgraph doesn't contain enough information to answer the query, acknowledge this limitation
        - Format your response to be readable with headers, bullet points, etc.
        - Keep your response concise and focused on the query
        """
        
        human_prompt = """
        User Query: {query}
        
        Relevant Knowledge Graph Subgraph:
        {context}
        
        Please provide a clear, informative answer based on this subgraph.
        """
        
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=system_prompt),
            HumanMessagePromptTemplate.from_template(human_prompt)
        ])
        
        # Create a chain
        chain = LLMChain(llm=self.model, prompt=prompt)
        
        try:
            # Run the chain
            result = chain.invoke({"query": user_query, "context": context})
            response_text = result.get("text", "")
            
            return {
                "query": user_query,
                "response": response_text,
                "source": "llm"
            }
        
        except Exception as e:
            logger.error(f"Error in generate_query: {e}")
            # Fall back to basic implementation
            return self._generate_basic_response(user_query, subgraph)
    
    def _prepare_context(self, subgraph: GraphData) -> str:
        """Prepare a text representation of the knowledge graph for context"""
        if not subgraph or not subgraph.nodes:
            return "No relevant information found in the knowledge graph."
        
        context = "Nodes (Entities):\n"
        for i, node in enumerate(subgraph.nodes):
            props_str = ", ".join([f"{k}: {v}" for k, v in node.properties.items() 
                                  if k not in ["created_by", "created_at"] and v])
            context += f"{i+1}. {node.label}: {node.name}"
            if props_str:
                context += f" ({props_str})"
            context += "\n"
        
        if subgraph.links:
            context += "\nRelationships:\n"
            for i, rel in enumerate(subgraph.links):
                # Find source and target node names
                source_name = "Unknown"
                target_name = "Unknown"
                
                for node in subgraph.nodes:
                    if node.id == rel.source:
                        source_name = node.name
                    if node.id == rel.target:
                        target_name = node.name
                
                props_str = ", ".join([f"{k}: {v}" for k, v in rel.properties.items() 
                                     if k not in ["created_by", "created_at"] and v])
                
                context += f"{i+1}. {source_name} --[{rel.type}]--> {target_name}"
                if props_str:
                    context += f" ({props_str})"
                context += "\n"
        
        return context
    
    def _generate_basic_response(self, user_query: str, subgraph: GraphData) -> Dict[str, str]:
        """Generate a basic response without using an LLM"""
        if not subgraph or not subgraph.nodes:
            return {
                "query": user_query,
                "response": "I couldn't find any relevant information in your knowledge graph.",
                "source": "basic"
            }
        
        # Count entity types
        entity_types = {}
        for node in subgraph.nodes:
            if node.label not in entity_types:
                entity_types[node.label] = []
            entity_types[node.label].append(node.name)
        
        # Count relationship types
        rel_types = {}
        for rel in subgraph.links:
            if rel.type not in rel_types:
                rel_types[rel.type] = 0
            rel_types[rel.type] += 1
        
        # Build a basic response
        response = f"# Query Results\n\n"
        response += f"I found {len(subgraph.nodes)} entities and {len(subgraph.links)} relationships that might be relevant to your query.\n\n"
        
        # Add entity summary
        response += "## Entities Found\n\n"
        for entity_type, entities in entity_types.items():
            response += f"* **{entity_type}** ({len(entities)}): "
            if len(entities) <= 5:
                response += ", ".join(entities)
            else:
                response += ", ".join(entities[:5]) + f", and {len(entities) - 5} more"
            response += "\n"
        
        # Add relationship summary
        if rel_types:
            response += "\n## Relationships\n\n"
            for rel_type, count in rel_types.items():
                response += f"* **{rel_type}**: {count} instances\n"
        
        # Add a note about the query
        response += f"\n## About Your Query\n\n"
        response += f"Your query was: \"{user_query}\"\n\n"
        response += "To get more specific results, try including entity names in your query."
        
        return {
            "query": user_query,
            "response": response,
            "source": "basic"
        }

# Create a singleton instance
llm_service = LLMService()