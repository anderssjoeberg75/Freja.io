"""
document_analysis/tools.py — improved RAG implementation

Improvements over v1:
  - Paragraph-aware semantic chunking (not blind character slicing)
  - SHA-256 deduplication: same file is never indexed twice
  - Relevance threshold: irrelevant chunks are filtered out
  - n_results=8 with relevance % shown to LLM
  - pdfplumber for better PDF text extraction (falls back to pypdf)
  - Meaningful list_documents showing filenames + chunk counts
  - Singleton ChromaDB client (no repeated open/close)
  - Ollama /api/embed endpoint (new API) with /api/embeddings fallback
"""
import os
import re
import hashlib
import logging
import uuid
import httpx
from typing import List, Optional

import chromadb
from pydantic import BaseModel, Field
from app.services.tool_registry import ToolRegistry
from app.core.config import settings, get_credential, BASE_DIR

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CHROMA_DB_PATH = os.path.join(BASE_DIR, "db", "chroma")
COLLECTION_NAME = "freja_documents"
EMBEDDING_MODEL = "nomic-embed-text"

# Chunks are semantically bounded paragraphs; aim for ~600 chars each
# so that embeddings capture a coherent idea.
CHUNK_TARGET_CHARS = 600
CHUNK_MAX_CHARS = 900          # hard ceiling before forced split
RELEVANCE_THRESHOLD = 0.65     # cosine distance; lower = more similar
DEFAULT_N_RESULTS = 8          # retrieve more, filter by threshold

# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class IngestDocumentSchema(BaseModel):
    file_path: str = Field(..., description="Absolute path to the PDF, TXT or MD file to ingest.")

class QueryKnowledgeBaseSchema(BaseModel):
    query: str = Field(..., description="The question or topic to search for in the document knowledge base.")
    n_results: int = Field(DEFAULT_N_RESULTS, description="Max number of relevant chunks to retrieve.")

class ListDocumentsSchema(BaseModel):
    pass

# ---------------------------------------------------------------------------
# Singleton ChromaDB client
# ---------------------------------------------------------------------------

_chroma_client: Optional[chromadb.PersistentClient] = None

def _get_client() -> chromadb.PersistentClient:
    global _chroma_client
    if _chroma_client is None:
        os.makedirs(CHROMA_DB_PATH, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    return _chroma_client

# ---------------------------------------------------------------------------
# Embedding function (Ollama)
# ---------------------------------------------------------------------------

class OllamaEmbeddingFunction(chromadb.EmbeddingFunction):
    """Calls Ollama to compute embeddings. Tries /api/embed (v2), falls back to /api/embeddings (v1)."""

    def __init__(self, model_name: str = EMBEDDING_MODEL):
        self.model_name = model_name
        ollama_url = get_credential("OLLAMA_URL") or settings.OLLAMA_URL
        self.base_url = ollama_url.rstrip("/")

    def _embed_one(self, text: str) -> List[float]:
        with httpx.Client(timeout=60.0) as client:
            # Try new API first
            try:
                resp = client.post(
                    f"{self.base_url}/api/embed",
                    json={"model": self.model_name, "input": text},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    # /api/embed returns {"embeddings": [[...]] }
                    return data.get("embeddings", [[]])[0]
            except Exception:
                pass

            # Fallback to legacy API
            resp = client.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model_name, "prompt": text},
            )
            if resp.status_code == 200:
                return resp.json().get("embedding", [])

            raise RuntimeError(f"Embedding failed: {resp.status_code} {resp.text[:200]}")

    def __call__(self, input: List[str]) -> List[List[float]]:
        embeddings = []
        for text in input:
            try:
                embeddings.append(self._embed_one(text))
            except Exception as e:
                logger.error(f"Embedding error for chunk: {e}")
                embeddings.append([])
        return embeddings


def get_collection() -> chromadb.Collection:
    client = _get_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=OllamaEmbeddingFunction(),
    )

# ---------------------------------------------------------------------------
# Semantic (paragraph-aware) chunking
# ---------------------------------------------------------------------------

def _chunk_text(text: str) -> List[str]:
    """
    Split text into semantically coherent chunks.

    Strategy:
      1. Split on blank lines → paragraphs
      2. Accumulate paragraphs until CHUNK_TARGET_CHARS is reached
      3. If a single paragraph exceeds CHUNK_MAX_CHARS, split it at sentence boundaries
    """
    # Normalise line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Split into paragraphs
    raw_paragraphs = re.split(r"\n{2,}", text)
    paragraphs = [p.strip() for p in raw_paragraphs if p.strip()]

    # Split over-long paragraphs at sentence boundaries
    sentence_end = re.compile(r"(?<=[.!?])\s+")
    split_paragraphs: List[str] = []
    for para in paragraphs:
        if len(para) <= CHUNK_MAX_CHARS:
            split_paragraphs.append(para)
        else:
            sentences = sentence_end.split(para)
            current = ""
            for sent in sentences:
                if len(current) + len(sent) < CHUNK_MAX_CHARS:
                    current = (current + " " + sent).strip()
                else:
                    if current:
                        split_paragraphs.append(current)
                    current = sent
            if current:
                split_paragraphs.append(current)

    # Merge short paragraphs into chunks targeting CHUNK_TARGET_CHARS
    chunks: List[str] = []
    current_chunk = ""
    for para in split_paragraphs:
        if not current_chunk:
            current_chunk = para
        elif len(current_chunk) + len(para) + 2 <= CHUNK_TARGET_CHARS:
            current_chunk += "\n\n" + para
        else:
            chunks.append(current_chunk)
            current_chunk = para
    if current_chunk:
        chunks.append(current_chunk)

    return chunks

# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------

def _extract_text(file_path: str) -> str:
    """Extract text from PDF, TXT or MD files."""
    ext = file_path.lower().rsplit(".", 1)[-1]

    if ext == "pdf":
        # Try pdfplumber first (better layout preservation)
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                pages = []
                for page in pdf.pages:
                    t = page.extract_text(layout=False) or ""
                    pages.append(t)
            return "\n\n".join(pages)
        except ImportError:
            pass
        except Exception as e:
            logger.warning(f"pdfplumber failed ({e}), falling back to pypdf")

        # Fallback: pypdf
        from pypdf import PdfReader
        reader = PdfReader(file_path)
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)

    # Plain text / markdown
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

# ---------------------------------------------------------------------------
# Ingestion
# ---------------------------------------------------------------------------

async def ingest_document_impl(file_path: str, source_name: str = None) -> str:
    """
    Read a file, split into semantic chunks, compute embeddings and store
    in ChromaDB. Skips files that are already indexed (SHA-256 hash check).
    """
    if not os.path.exists(file_path):
        return f"Error: File not found at {file_path}"

    display_name = source_name or os.path.basename(file_path)

    try:
        text_content = _extract_text(file_path)
    except Exception as e:
        logger.error(f"Text extraction failed for {file_path}: {e}", exc_info=True)
        return f"Error extracting text from {display_name}: {e}"

    if not text_content.strip():
        return f"Error: Could not extract any text from {display_name}."

    # Deduplication: skip if same content hash already indexed
    doc_hash = hashlib.sha256(text_content.encode("utf-8", errors="ignore")).hexdigest()[:16]

    try:
        col = get_collection()
        existing = col.get(where={"doc_hash": doc_hash}, limit=1, include=["metadatas"])
        if existing["ids"]:
            return (
                f"'{display_name}' är redan indexerat (hash {doc_hash}). "
                "Ingen åtgärd krävs. Radera och ladda upp igen för att uppdatera."
            )
    except Exception as e:
        logger.warning(f"Hash check failed (continuing): {e}")

    # Chunk
    chunks = _chunk_text(text_content)
    if not chunks:
        return f"Error: No text chunks produced from {display_name}."

    # Store
    try:
        col = get_collection()
        ids = [str(uuid.uuid4()) for _ in chunks]
        metadatas = [
            {
                "source": display_name,
                "doc_hash": doc_hash,
                "chunk_index": i,
                "total_chunks": len(chunks),
            }
            for i in range(len(chunks))
        ]
        col.add(documents=chunks, metadatas=metadatas, ids=ids)
        logger.info(f"Ingested '{display_name}': {len(chunks)} chunks (hash {doc_hash})")
        return f"✅ Indexerade '{display_name}' — {len(chunks)} semantiska chunks sparade."
    except Exception as e:
        logger.error(f"ChromaDB add failed: {e}", exc_info=True)
        return f"Error storing {display_name}: {e}"

# ---------------------------------------------------------------------------
# Query
# ---------------------------------------------------------------------------

async def query_knowledge_base_impl(query: str, n_results: int = DEFAULT_N_RESULTS) -> str:
    """
    Search the knowledge base for chunks relevant to the query.
    Filters out low-relevance results using cosine distance threshold.
    """
    if not query or not query.strip():
        return "Error: query cannot be empty."

    try:
        col = get_collection()
        total = col.count()
        if total == 0:
            return "Kunskapsbasen är tom. Ladda upp ett dokument först."

        actual_n = min(n_results, total)
        results = col.query(
            query_texts=[query],
            n_results=actual_n,
            include=["documents", "metadatas", "distances"],
        )

        docs = results["documents"][0]
        metas = results["metadatas"][0]
        distances = results["distances"][0]

        # Filter by relevance threshold
        relevant = [
            (doc, meta, dist)
            for doc, meta, dist in zip(docs, metas, distances)
            if dist <= RELEVANCE_THRESHOLD
        ]

        if not relevant:
            # No matches above threshold – return best we have with a caveat
            if docs:
                best_dist = distances[0]
                best_relevance = max(0, round((1 - best_dist) * 100))
                return (
                    f"Hittade inga tillräckligt relevanta chunks (bästa relevans: {best_relevance}%). "
                    "Prova att omformulera frågan eller ladda upp fler dokument."
                )
            return "Inga dokument hittades för din fråga."

        # Format output
        lines = [f"## Sökresultat för: \"{query}\"\n"]
        for i, (doc, meta, dist) in enumerate(relevant, 1):
            relevance_pct = max(0, round((1 - dist) * 100))
            source = meta.get("source", "okänd källa")
            lines.append(f"### [{i}] {source} — relevans {relevance_pct}%")
            lines.append(doc.strip())
            lines.append("")

        return "\n".join(lines)

    except Exception as e:
        logger.error(f"Query error: {e}", exc_info=True)
        return f"Error querying knowledge base: {e}"

# ---------------------------------------------------------------------------
# List documents
# ---------------------------------------------------------------------------

async def list_documents_impl() -> str:
    """List indexed documents with source names and chunk counts."""
    try:
        col = get_collection()
        total = col.count()
        if total == 0:
            return "Kunskapsbasen är tom."

        all_meta = col.get(include=["metadatas"])["metadatas"]
        sources: dict[str, int] = {}
        for m in all_meta:
            src = m.get("source", "okänd")
            sources[src] = sources.get(src, 0) + 1

        lines = [f"## Indexerade dokument ({len(sources)} filer, {total} chunks totalt)\n"]
        for src, count in sorted(sources.items()):
            lines.append(f"- **{src}** — {count} chunks")

        return "\n".join(lines)
    except Exception as e:
        return f"Error listing documents: {e}"

# ---------------------------------------------------------------------------
# Tool registration
# ---------------------------------------------------------------------------

def register_tools(registry: ToolRegistry) -> None:
    registry.register(
        name="ingest_document",
        description=(
            "Reads a PDF, TXT or MD file, splits it into semantic chunks, "
            "and saves them to the local vector database for future search. "
            "Skips files that are already indexed."
        ),
        args_schema=IngestDocumentSchema,
    )(ingest_document_impl)

    registry.register(
        name="query_knowledge_base",
        description=(
            "Searches the local document database for text relevant to the query. "
            "Use this to find information in previously ingested files (CVs, reports, "
            "personal letters, notes, etc.). Always pass the user's question verbatim as 'query'."
        ),
        args_schema=QueryKnowledgeBaseSchema,
    )(query_knowledge_base_impl)

    registry.register(
        name="list_ingested_documents",
        description="Shows which documents are indexed in the knowledge base and how many chunks each has.",
        args_schema=ListDocumentsSchema,
    )(list_documents_impl)
