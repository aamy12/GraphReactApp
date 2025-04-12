import os
import logging
import tempfile
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
import json

from pypdf import PdfReader
from PIL import Image
import pytesseract
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain.docstore.document import Document

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Service for processing different document types and extracting text content"""
    
    def __init__(self):
        """Initialize the document processor"""
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
        )
        
        # Initialize embeddings if OpenAI API key is available
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key:
            self.embeddings = OpenAIEmbeddings(api_key=openai_api_key)
        else:
            self.embeddings = None
            logger.warning("No OpenAI API key found. Embeddings will not be available.")
    
    def process_file(self, file_path: str, file_type: str = None) -> Dict[str, Any]:
        """
        Process a file and extract its content
        
        Args:
            file_path: Path to the file
            file_type: Optional file type (mime type or extension)
            
        Returns:
            Dict containing extracted text, metadata, and optionally embeddings
        """
        if not file_type:
            # Try to determine file type from extension
            file_type = Path(file_path).suffix.lower()
        
        # Process based on file type
        if file_type in ['.pdf', 'application/pdf']:
            return self._process_pdf(file_path)
        elif file_type in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp', 
                          'image/png', 'image/jpeg', 'image/tiff', 'image/bmp']:
            return self._process_image(file_path)
        elif file_type in ['.txt', '.md', '.csv', '.json', '.xml', 
                          'text/plain', 'text/markdown', 'text/csv', 'application/json', 'application/xml']:
            return self._process_text_file(file_path)
        else:
            logger.warning(f"Unsupported file type: {file_type}")
            # Try to process as text file
            return self._process_text_file(file_path)
    
    def _process_pdf(self, file_path: str) -> Dict[str, Any]:
        """Process a PDF file and extract text"""
        try:
            pdf_reader = PdfReader(file_path)
            text = ""
            
            # Extract metadata from PDF
            metadata = {}
            if pdf_reader.metadata:
                for key, value in pdf_reader.metadata.items():
                    if key and value:
                        # Strip the leading slash in PDF metadata keys
                        clean_key = str(key)
                        if clean_key.startswith('/'):
                            clean_key = clean_key[1:]
                        metadata[clean_key] = str(value)
            
            # Extract text from each page
            pages_text = []
            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
                    pages_text.append({
                        "page_num": page_num + 1,
                        "text": page_text
                    })
            
            # Create document chunks
            doc_chunks = self._create_document_chunks(text, metadata)
            
            return {
                "text": text,
                "metadata": metadata,
                "pages": pages_text,
                "chunks": doc_chunks
            }
        except Exception as e:
            logger.error(f"Error processing PDF file: {e}")
            return {"error": str(e)}
    
    def _process_image(self, file_path: str) -> Dict[str, Any]:
        """Process an image file and extract text using OCR"""
        try:
            # Open image
            with Image.open(file_path) as img:
                # Extract metadata
                metadata = {
                    "format": img.format,
                    "mode": img.mode,
                    "width": img.width,
                    "height": img.height,
                }
                
                # Extract EXIF data if available
                if hasattr(img, '_getexif') and img._getexif():
                    exif = img._getexif()
                    if exif:
                        for tag_id, value in exif.items():
                            metadata[f"exif_{tag_id}"] = str(value)
                
                # Perform OCR
                text = pytesseract.image_to_string(img)
                
                # Create document chunks
                doc_chunks = self._create_document_chunks(text, metadata)
                
                return {
                    "text": text,
                    "metadata": metadata,
                    "chunks": doc_chunks
                }
        except Exception as e:
            logger.error(f"Error processing image file: {e}")
            return {"error": str(e)}
    
    def _process_text_file(self, file_path: str) -> Dict[str, Any]:
        """Process a text file and extract its content"""
        try:
            # Extract metadata
            file_stat = os.stat(file_path)
            metadata = {
                "size": file_stat.st_size,
                "created": file_stat.st_ctime,
                "modified": file_stat.st_mtime,
                "filename": os.path.basename(file_path),
            }
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
            
            # Create document chunks
            doc_chunks = self._create_document_chunks(text, metadata)
            
            # Check if it's JSON and extract structured data
            structured_data = None
            if file_path.endswith('.json'):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        structured_data = json.load(f)
                except json.JSONDecodeError:
                    pass
            
            result = {
                "text": text,
                "metadata": metadata,
                "chunks": doc_chunks
            }
            
            if structured_data:
                result["structured_data"] = structured_data
                
            return result
        except Exception as e:
            logger.error(f"Error processing text file: {e}")
            return {"error": str(e)}
    
    def _create_document_chunks(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Split text into chunks and add embeddings if available"""
        if not text:
            return []
        
        # Split text into chunks
        documents = self.text_splitter.create_documents([text])
        
        # Add metadata to all chunks
        for doc in documents:
            doc.metadata.update(metadata)
        
        # Process each chunk
        chunks = []
        for i, doc in enumerate(documents):
            chunk = {
                "id": i,
                "text": doc.page_content,
                "metadata": doc.metadata
            }
            
            # Add embeddings if available
            if self.embeddings:
                try:
                    embedding = self.embeddings.embed_query(doc.page_content)
                    chunk["embedding"] = embedding
                except Exception as e:
                    logger.error(f"Error creating embedding: {e}")
            
            chunks.append(chunk)
        
        return chunks
    
    def extract_entities_and_relationships(self, text: str) -> Dict[str, Any]:
        """
        Extract entities and relationships from text using LLM
        
        This method would normally use an external API or model to extract entities
        and relationships. For now, it's a placeholder.
        """
        # This would normally use a proper NLP pipeline or LLM
        # As a fallback, we can use some basic pattern matching
        
        # Dummy implementation for demonstration - this would be replaced with a proper NLP solution
        import re
        
        # Extract potential entities (capitalized words)
        entity_matches = re.findall(r'\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)\b', text)
        entities = []
        seen = set()
        
        for match in entity_matches:
            if match not in seen and len(match) > 3:  # Avoid short names and duplicates
                seen.add(match)
                entity_type = "Person" if match.count(" ") > 0 else "Concept"  # Simple heuristic
                entities.append({
                    "name": match,
                    "type": entity_type,
                    "mentions": text.count(match)
                })
        
        # Simple relationship detection (entities appearing in same sentence)
        sentences = re.split(r'[.!?]', text)
        relationships = []
        
        for sentence in sentences:
            sentence_entities = []
            for entity in entities:
                if entity["name"] in sentence:
                    sentence_entities.append(entity["name"])
            
            # Create relationships between entities in same sentence
            for i in range(len(sentence_entities)):
                for j in range(i+1, len(sentence_entities)):
                    ent1 = sentence_entities[i]
                    ent2 = sentence_entities[j]
                    # Don't create duplicate relationships
                    if not any(r for r in relationships 
                              if (r["source"] == ent1 and r["target"] == ent2) 
                              or (r["source"] == ent2 and r["target"] == ent1)):
                        relationships.append({
                            "source": ent1,
                            "target": ent2,
                            "type": "MENTIONED_WITH",
                            "sentence": sentence.strip()
                        })
        
        return {
            "entities": entities,
            "relationships": relationships
        }

# Singleton instance
document_processor = DocumentProcessor()