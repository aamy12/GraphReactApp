
import os
import logging
from typing import Dict, List, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.chains import GraphQAChain
from langchain.prompts import ChatPromptTemplate
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = None
        self.embeddings = None
        self.vector_store = None
        self.initialize_components()

    def initialize_components(self):
        """Initialize LLM components with API key"""
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.warning("No OpenAI API key found")
            return False

        try:
            self.model = ChatOpenAI(
                temperature=0.2,
                api_key=self.api_key,
                model="gpt-3.5-turbo"  # Using a more accessible model
            )

            self.embeddings = OpenAIEmbeddings(api_key=self.api_key)
            self.vector_store = Chroma(embedding_function=self.embeddings)
            
            logger.info("Successfully initialized LLM components")
            return True
        except Exception as e:
            logger.error(f"Error initializing LLM components: {e}")
            return False

    def is_available(self) -> bool:
        """Check if LLM service is properly configured and available"""
        return self.model is not None and self.embeddings is not None

    def reinitialize(self) -> bool:
        """Reinitialize the service with current environment variables"""
        return self.initialize_components()

    def process_document(self, text: str) -> Dict[str, Any]:
        """Process document text and extract entities/relationships"""
        if not self.is_available():
            return {"entities": [], "relationships": []}

        try:
            # Split text into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            chunks = text_splitter.split_text(text)

            # Store chunks in vector store
            docs = [Document(page_content=chunk) for chunk in chunks]
            self.vector_store.add_documents(docs)

            # Extract entities and relationships using LLM
            extraction_prompt = """
            Extract key entities and their relationships from the text.
            Format as JSON with "entities" and "relationships" arrays.
            Entity should have "name", "type", and "attributes".
            Relationship should have "source", "target", "type", and "attributes".
            Focus on meaningful connections and important entities.
            """

            response = self.model.invoke([
                {"role": "system", "content": extraction_prompt},
                {"role": "user", "content": text[:4000]}
            ])
            
            return response.content if isinstance(response.content, dict) else {"entities": [], "relationships": []}

        except Exception as e:
            logger.error(f"Error processing document: {e}")
            return {"entities": [], "relationships": []}

    def query_knowledge_graph(self, query: str, graph) -> Dict[str, str]:
        """Query the knowledge graph using GraphRAG approach"""
        if not self.is_available():
            return {
                "query": query,
                "response": "LLM service not available",
                "source": "error"
            }

        try:
            # Create retriever with contextual compression
            retriever = self.vector_store.as_retriever()
            compressor = LLMChainExtractor.from_llm(self.model)
            compression_retriever = ContextualCompressionRetriever(
                base_retriever=retriever,
                doc_compressor=compressor
            )

            # Get relevant context
            context_docs = compression_retriever.get_relevant_documents(query)
            context = "\n".join(doc.page_content for doc in context_docs)

            # Create GraphQA chain
            qa_chain = GraphQAChain.from_llm(
                llm=self.model,
                graph=graph,
                verbose=True
            )

            # Generate response
            response = qa_chain.run(
                query=query,
                context=context
            )

            return {
                "query": query,
                "response": response,
                "source": "llm"
            }

        except Exception as e:
            logger.error(f"Error querying knowledge graph: {e}")
            return {
                "query": query,
                "response": f"Error: {str(e)}",
                "source": "error"
            }

# Create singleton instance
llm_service = LLMService()
