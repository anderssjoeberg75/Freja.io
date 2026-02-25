import os
import logging
import chromadb
import uuid
import httpx
from typing import List, Optional, Any
from pydantic import BaseModel, Field
from app.services.tool_registry import ToolRegistry
from app.core.config import settings, get_credential, BASE_DIR

logger = logging.getLogger(__name__)

# --- Configuration ---
CHROMA_DB_PATH = os.path.join(BASE_DIR, "db", "chroma")
COLLECTION_NAME = "freja_documents"
# Ensure the embedding model is available in Ollama!
# Users should run: `ollama pull nomic-embed-text`
EMBEDDING_MODEL = "nomic-embed-text" 

# --- Schemas ---

class IngestDocumentSchema(BaseModel):
    file_path: str = Field(..., description="Absolute path to the PDF or text file to ingest.")

class QueryKnowledgeBaseSchema(BaseModel):
    query: str = Field(..., description=" The question or topic to search for in the document knowledge base.")
    n_results: int = Field(3, description="Number of relevant chunks to retrieve.")

class ListDocumentsSchema(BaseModel):
    pass

# --- Embedding Function ---

class OllamaEmbeddingFunction(chromadb.EmbeddingFunction):
    def __init__(self, model_name: str = EMBEDDING_MODEL):
        self.model_name = model_name
        self.ollama_url = get_credential("OLLAMA_URL") or settings.OLLAMA_URL
        self.base_url = self.ollama_url.rstrip("/")

    def __call__(self, input: List[str]) -> List[List[float]]:
        embeddings = []
        for text in input:
            try:
                # Synchronous call for compatibility with Chroma protocol using httpx.Client (sync)
                with httpx.Client(timeout=30.0) as client:
                    resp = client.post(
                        f"{self.base_url}/api/embeddings",
                        json={"model": self.model_name, "prompt": text}
                    )
                    if resp.status_code == 200:
                        embeddings.append(resp.json()["embedding"])
                    else:
                        logger.error(f"Ollama embedding failed: {resp.text}")
                        embeddings.append([]) 
            except Exception as e:
                logger.error(f"Embedding error: {e}")
                embeddings.append([])
        return embeddings

def get_collection():
    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    embedding_fn = OllamaEmbeddingFunction()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embedding_fn
    )

async def ingest_document_impl(file_path: str, source_name: str = None) -> str:
    """Reads a file, chunks it, and stores embeddings in ChromaDB."""
    if not os.path.exists(file_path):
        return f"Error: File not found at {file_path}"
    
    # Use provided source_name (e.g. original Telegram filename) or fall back to path
    display_name = source_name or os.path.basename(file_path)
    
    try:
        text_content = ""
        if file_path.lower().endswith(".pdf"):
            from pypdf import PdfReader
            reader = PdfReader(file_path)
            for page in reader.pages:
                text_content += page.extract_text() + "\n"
        else:
            # Assume text
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text_content = f.read()
        
        if not text_content.strip():
            return "Error: Could not extract text from file."

        # Simple chunking (can be improved with langchain later)
        chunk_size = 1000
        overlap = 100
        chunks = []
        start = 0
        while start < len(text_content):
            end = start + chunk_size
            chunk = text_content[start:end]
            chunks.append(chunk)
            start += (chunk_size - overlap)
        
        collection = get_collection()
        
        ids = [str(uuid.uuid4()) for _ in chunks]
        # Store display_name as source so results show the original filename
        metadatas = [{"source": display_name, "chunk_index": i} for i in range(len(chunks))]
        
        collection.add(
            documents=chunks,
            metadatas=metadatas,
            ids=ids
        )
        
        return f"Successfully ingested {display_name}. Created {len(chunks)} chunks."

    except Exception as e:
        logger.error(f"Ingestion error: {e}", exc_info=True)
        return f"Error ingesting document: {str(e)}"


async def query_knowledge_base_impl(query: str, n_results: int = 3) -> str:
    """Searches the knowledge base for relevant context."""
    try:
        collection = get_collection()
        results = collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        output = f"**Search Results for '{query}':**\n\n"
        
        if not results["documents"] or not results["documents"][0]:
            return "No relevant documents found."

        for i, doc in enumerate(results["documents"][0]):
            meta = results["metadatas"][0][i]
            source = meta.get("source", "unknown")
            output += f"--- Source: {os.path.basename(source)} ---\n{doc}\n\n"
            
        return output

    except Exception as e:
        logger.error(f"Query error: {e}", exc_info=True)
        return f"Error querying knowledge base: {str(e)}"

async def list_documents_impl() -> str:
    """Lists ingested documents (by source metadata)."""
    try:
        collection = get_collection()
        # Chroma doesn't have a simple "list all" distinct metadata efficiently without fetching all.
        # limiting to 100 for now or peek.
        # Actually, let's just peek.
        count = collection.count()
        return f"Knowledge Base contains {count} embedded text chunks."
    except Exception as e:
        return f"Error listing documents: {str(e)}"

# --- Registration ---

def register_tools(registry: ToolRegistry) -> None:
    registry.register(
        name="ingest_document",
        description="Reads a PDF or text file, chunks it, and saves it to the local vector database for future searching.",
        args_schema=IngestDocumentSchema,
    )(ingest_document_impl)

    registry.register(
        name="query_knowledge_base",
        description="Searches the local document database for text chunks relevant to the query. Use this to find information in previously ingested files.",
        args_schema=QueryKnowledgeBaseSchema,
    )(query_knowledge_base_impl)

    registry.register(
        name="list_ingested_documents",
        description="Shows statistics about the local document knowledge base.",
        args_schema=ListDocumentsSchema,
    )(list_documents_impl)
