import os
import logging
from typing import Dict, List, Any, Optional
import openai
from config import Config

logger = logging.getLogger(__name__)

# Configure OpenAI API key
openai.api_key = Config.OPENAI_API_KEY

class LLMService:
    def __init__(self):
        self.model = "gpt-3.5-turbo"
        if not openai.api_key:
            logger.warning("OpenAI API key not set, LLM functionality will be limited")
    
    def parse_document_to_graph(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Parse a document and extract entities and relationships to create a knowledge graph
        """
        if not openai.api_key:
            raise ValueError("OpenAI API key not set")
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a knowledge graph creation assistant. Extract entities and relationships from the text. Format your response as a JSON with 'entities' and 'relationships' arrays."},
                    {"role": "user", "content": f"Extract entities and relationships from the following text to create a knowledge graph:\n\n{text}\n\nRespond with JSON only."}
                ],
                temperature=0.2,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content
            
            # Try to extract JSON from the content
            import json
            import re
            
            # Look for JSON pattern in the response
            json_pattern = r'```json\s*([\s\S]*?)\s*```|(\{[\s\S]*\})'
            match = re.search(json_pattern, content)
            
            if match:
                json_str = match.group(1) or match.group(2)
                graph_data = json.loads(json_str)
            else:
                # Try direct parsing if no JSON code block is found
                graph_data = json.loads(content)
            
            # Ensure the expected structure
            if 'entities' not in graph_data or 'relationships' not in graph_data:
                raise ValueError("LLM response missing entities or relationships")
                
            return graph_data
            
        except Exception as e:
            logger.error(f"Error parsing document with LLM: {e}")
            # Return a simplified structure with the error
            return {
                "entities": [],
                "relationships": [],
                "error": str(e)
            }
    
    def generate_query(self, user_query: str, subgraph: Dict) -> Dict:
        """
        Process a natural language query against the knowledge graph
        """
        if not openai.api_key:
            raise ValueError("OpenAI API key not set")
        
        # Simplify the subgraph for context
        context = self._prepare_context(subgraph)
            
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a knowledge graph query assistant. Generate detailed answers based on the knowledge graph."},
                    {"role": "user", "content": f"Knowledge Graph Context:\n{context}\n\nUser Query: {user_query}\n\nProvide a detailed answer based on the given context. Include your reasoning process."}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            return {
                "answer": response.choices[0].message.content,
                "query": user_query
            }
            
        except Exception as e:
            logger.error(f"Error processing query with LLM: {e}")
            return {
                "answer": f"Error processing your query: {str(e)}",
                "query": user_query
            }
    
    def _prepare_context(self, subgraph: Dict) -> str:
        """Prepare a text representation of the knowledge graph for context"""
        nodes = subgraph.get("nodes", [])
        relationships = subgraph.get("relationships", [])
        
        context = "Knowledge Graph:\n\n"
        
        # Add nodes information
        context += "Entities:\n"
        for i, node in enumerate(nodes):
            labels = ", ".join(node.get("labels", []))
            props = ", ".join([f"{k}: {v}" for k, v in node.get("properties", {}).items() if k != "user_id"])
            context += f"{i+1}. {labels} ({props})\n"
        
        # Add relationships information
        context += "\nRelationships:\n"
        for i, rel in enumerate(relationships):
            # Find source and target node names
            source_node = next((n for n in nodes if n.get("id") == rel.get("start_node_id")), None)
            target_node = next((n for n in nodes if n.get("id") == rel.get("end_node_id")), None)
            
            source_name = source_node.get("properties", {}).get("name", f"Node {rel.get('start_node_id')}")
            target_name = target_node.get("properties", {}).get("name", f"Node {rel.get('end_node_id')}")
            
            rel_type = rel.get("type", "RELATED")
            props = ", ".join([f"{k}: {v}" for k, v in rel.get("properties", {}).items() if k != "user_id"])
            
            context += f"{i+1}. {source_name} --[{rel_type}]--> {target_name} ({props})\n"
        
        return context

# Initialize the LLM service
llm_service = LLMService()
