import os
import re
import json
import logging
import tempfile
from typing import Dict, List, Any, Optional, Tuple
import uuid
from pathlib import Path
import base64

# PDF processing
try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

# Image processing
try:
    from PIL import Image
    import pytesseract
except ImportError:
    Image = None
    pytesseract = None

# Text processing
try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_openai import OpenAIEmbeddings
    from langchain.docstore.document import Document
except ImportError:
    RecursiveCharacterTextSplitter = None
    OpenAIEmbeddings = None
    Document = None

# Configure logging
logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Service for processing different document types and extracting text content"""
    
    def __init__(self):
        """Initialize the document processor"""
        # Check if components are available
        self.pdf_available = PdfReader is not None
        self.ocr_available = Image is not None and pytesseract is not None
        self.langchain_available = RecursiveCharacterTextSplitter is not None
        
        # Initialize text splitter if available
        self.text_splitter = None
        if self.langchain_available:
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                separators=["\n\n", "\n", ".", " ", ""]
            )
            
        # Check for OpenAI API key for embeddings
        self.embeddings = None
        if OpenAIEmbeddings is not None and os.environ.get("OPENAI_API_KEY"):
            try:
                self.embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI embeddings: {e}")

    def process_file(self, file_path: str, file_type: str = None) -> Dict[str, Any]:
        """
        Process a file and extract its content
        
        Args:
            file_path: Path to the file
            file_type: Optional file type (mime type or extension)
            
        Returns:
            Dict containing extracted text, metadata, and optionally embeddings
        """
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}"}
        
        # Determine file type if not provided
        if not file_type:
            file_name = os.path.basename(file_path)
            extension = file_name.split('.')[-1].lower() if '.' in file_name else ""
            
            if extension in ['pdf']:
                file_type = 'application/pdf'
            elif extension in ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff']:
                file_type = f'image/{extension}'
            elif extension in ['txt', 'md', 'csv', 'json', 'xml']:
                file_type = f'text/{extension}'
        
        # Process based on file type
        try:
            if file_type and 'pdf' in file_type and self.pdf_available:
                return self._process_pdf(file_path)
                
            elif file_type and 'image' in file_type and self.ocr_available:
                return self._process_image(file_path)
                
            else:
                # Default to text processing
                return self._process_text_file(file_path)
                
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {str(e)}")
            return {"error": f"Processing error: {str(e)}"}
    
    def _process_pdf(self, file_path: str) -> Dict[str, Any]:
        """Process a PDF file and extract text"""
        if not self.pdf_available:
            return {"error": "PDF processing not available. Install pypdf package."}
        
        try:
            logger.info(f"Processing PDF file: {file_path}")
            
            # Extract text from PDF
            reader = PdfReader(file_path)
            
            # Get metadata
            metadata = {
                "pageCount": len(reader.pages),
                "title": reader.metadata.title if reader.metadata.title else "",
                "author": reader.metadata.author if reader.metadata.author else "",
                "creator": reader.metadata.creator if reader.metadata.creator else "",
                "producer": reader.metadata.producer if reader.metadata.producer else "",
            }
            
            # Extract text from each page
            text = ""
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text += f"\n\n--- Page {i+1} ---\n\n"
                    text += page_text
            
            # Create document chunks for better processing
            chunks = self._create_document_chunks(text, metadata)
            
            return {
                "text": text,
                "metadata": metadata,
                "chunks": chunks
            }
            
        except Exception as e:
            logger.error(f"Error processing PDF {file_path}: {str(e)}")
            return {"error": f"PDF processing error: {str(e)}"}
    
    def _process_image(self, file_path: str) -> Dict[str, Any]:
        """Process an image file and extract text using OCR"""
        if not self.ocr_available:
            return {"error": "OCR not available. Install Pillow and pytesseract packages."}
        
        try:
            logger.info(f"Processing image file: {file_path}")
            
            # Open image
            image = Image.open(file_path)
            
            # Get metadata
            metadata = {
                "format": image.format,
                "mode": image.mode,
                "width": image.width,
                "height": image.height,
            }
            
            # Get EXIF data if available
            if hasattr(image, '_getexif') and image._getexif():
                exif = image._getexif()
                if exif:
                    for tag, value in exif.items():
                        if isinstance(value, (str, int, float)):
                            metadata[f"exif_{tag}"] = value
            
            # Perform OCR
            text = pytesseract.image_to_string(image)
            
            # Create document chunks
            chunks = self._create_document_chunks(text, metadata)
            
            return {
                "text": text,
                "metadata": metadata,
                "chunks": chunks
            }
            
        except Exception as e:
            logger.error(f"Error processing image {file_path}: {str(e)}")
            return {"error": f"Image processing error: {str(e)}"}
    
    def _process_text_file(self, file_path: str) -> Dict[str, Any]:
        """Process a text file and extract its content"""
        try:
            logger.info(f"Processing text file: {file_path}")
            
            # Get file metadata
            file_stats = os.stat(file_path)
            file_name = os.path.basename(file_path)
            extension = file_name.split('.')[-1].lower() if '.' in file_name else ""
            
            metadata = {
                "filename": file_name,
                "extension": extension,
                "size": file_stats.st_size,
                "modified": file_stats.st_mtime,
            }
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
            
            # Special handling for structured formats
            if extension == 'json':
                try:
                    # Extract JSON structure information
                    json_data = json.loads(text)
                    if isinstance(json_data, dict):
                        metadata["keys"] = list(json_data.keys())
                    elif isinstance(json_data, list):
                        metadata["count"] = len(json_data)
                except Exception as e:
                    logger.warning(f"Failed to parse JSON: {e}")
            
            # Create document chunks
            chunks = self._create_document_chunks(text, metadata)
            
            return {
                "text": text,
                "metadata": metadata,
                "chunks": chunks
            }
            
        except Exception as e:
            logger.error(f"Error processing text file {file_path}: {str(e)}")
            return {"error": f"Text file processing error: {str(e)}"}
    
    def _create_document_chunks(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Split text into chunks and add embeddings if available"""
        chunks = []
        
        if not text or not self.text_splitter:
            # Return a single chunk if no text or splitter available
            return [{"text": text or "", "metadata": metadata}]
        
        try:
            # Create smaller chunks for better processing
            docs = self.text_splitter.create_documents([text])
            
            # Process each chunk
            for i, doc in enumerate(docs):
                chunk = {
                    "id": str(uuid.uuid4()),
                    "text": doc.page_content,
                    "metadata": {**metadata, "chunk": i, "chunk_total": len(docs)}
                }
                
                # Add embeddings if available
                if self.embeddings:
                    try:
                        embedding = self.embeddings.embed_query(doc.page_content)
                        chunk["embedding"] = embedding
                    except Exception as e:
                        logger.warning(f"Failed to create embedding for chunk {i}: {e}")
                
                chunks.append(chunk)
                
            return chunks
            
        except Exception as e:
            logger.error(f"Error creating document chunks: {str(e)}")
            return [{"text": text, "metadata": metadata}]
    
    def extract_entities_and_relationships(self, text: str) -> Dict[str, Any]:
        """
        Extract entities and relationships from text using LLM
        
        This method would normally use an external API or model to extract entities
        and relationships. For now, it provides a basic implementation.
        """
        if not text:
            return {"entities": [], "relationships": []}
        
        # Simple regex-based entity extraction for basic entities
        # This is a simplified implementation and would normally use an NLP model
        entities = []
        relationships = []
        
        # Extract potential entities with simple regex patterns
        # People (capitalized names)
        person_pattern = r'\b([A-Z][a-z]+ [A-Z][a-z]+)\b'
        person_matches = re.findall(person_pattern, text)
        for name in set(person_matches):
            entities.append({
                "name": name,
                "type": "Person",
                "mentions": len(re.findall(re.escape(name), text))
            })
        
        # Organizations (capitalized multi-word phrases)
        org_pattern = r'\b([A-Z][a-z]+ (?:[A-Z][a-z]+ )*(?:Inc\.|Corp\.|LLC|Company|Organization|University))\b'
        org_matches = re.findall(org_pattern, text)
        for org in set(org_matches):
            entities.append({
                "name": org,
                "type": "Organization",
                "mentions": len(re.findall(re.escape(org), text))
            })
        
        # Locations (with simple patterns)
        loc_pattern = r'\b([A-Z][a-z]+ (?:City|County|State|Country|Island|Mountain|River|Lake))\b'
        loc_matches = re.findall(loc_pattern, text)
        for loc in set(loc_matches):
            entities.append({
                "name": loc,
                "type": "Location",
                "mentions": len(re.findall(re.escape(loc), text))
            })
        
        # Concepts (capitalized terms)
        concept_pattern = r'\b([A-Z][a-z]{3,})\b'
        concept_matches = re.findall(concept_pattern, text)
        for concept in set(concept_matches):
            if concept not in ['The', 'This', 'That', 'These', 'Those', 'There', 'They', 'Their']:
                entities.append({
                    "name": concept,
                    "type": "Concept",
                    "mentions": len(re.findall(r'\b' + re.escape(concept) + r'\b', text))
                })
        
        # Extract simple relationships between entities
        # Person-Organization relationships
        for person in [e for e in entities if e["type"] == "Person"]:
            for org in [e for e in entities if e["type"] == "Organization"]:
                # Look for relationship patterns within a window of the text
                person_name = person["name"]
                org_name = org["name"]
                
                # Simple patterns like "Person works for Organization"
                works_pattern = f'{re.escape(person_name)}[^.!?]{{0,40}}(?:work|works|working|worked)\\s+(?:for|at|with|in)[^.!?]{{0,20}}{re.escape(org_name)}'
                works_matches = re.findall(works_pattern, text, re.IGNORECASE)
                
                if works_matches:
                    relationships.append({
                        "source": person_name,
                        "target": org_name,
                        "type": "WORKS_FOR",
                        "sentence": works_matches[0][:100]
                    })
                
                # "Person founded Organization"
                founded_pattern = f'{re.escape(person_name)}[^.!?]{{0,40}}(?:found|founded|created|established|started)[^.!?]{{0,20}}{re.escape(org_name)}'
                founded_matches = re.findall(founded_pattern, text, re.IGNORECASE)
                
                if founded_matches:
                    relationships.append({
                        "source": person_name,
                        "target": org_name,
                        "type": "FOUNDED",
                        "sentence": founded_matches[0][:100]
                    })
        
        # Person-Person relationships
        all_persons = [e for e in entities if e["type"] == "Person"]
        for i, person1 in enumerate(all_persons):
            for person2 in all_persons[i+1:]:
                # "Person is related to Person"
                related_pattern = f'{re.escape(person1["name"])}[^.!?]{{0,30}}(?:and|with)[^.!?]{{0,20}}{re.escape(person2["name"])}'
                related_matches = re.findall(related_pattern, text, re.IGNORECASE)
                
                if related_matches:
                    relationships.append({
                        "source": person1["name"],
                        "target": person2["name"],
                        "type": "RELATED_TO",
                        "sentence": related_matches[0][:100]
                    })
        
        # Return extracted entities and relationships
        return {
            "entities": entities,
            "relationships": relationships
        }

# Create a singleton instance
document_processor = DocumentProcessor()