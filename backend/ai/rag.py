"""
MediMind AI - RAG Pipeline
PDF document processing, embedding generation, ChromaDB storage, and semantic retrieval.
Uses all-MiniLM-L6-v2 for embeddings.
"""

import os
import hashlib
import json
import logging
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from backend.config import (
    MEDICAL_DOCS_DIR,
    CHROMA_DB_DIR,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    EMBEDDING_MODEL,
    RETRIEVAL_TOP_K,
)

logger = logging.getLogger(__name__)


class RAGPipeline:
    """Handles PDF ingestion, embedding, storage, and retrieval."""

    def __init__(self):
        self.embeddings = None
        self.vectorstore = None
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        self._initialized = False
        self._index_record_path = CHROMA_DB_DIR / "indexed_files.json"

    def _get_indexed_files(self) -> dict:
        """Load record of already-indexed files."""
        if self._index_record_path.exists():
            with open(self._index_record_path, "r") as f:
                return json.load(f)
        return {}

    def _save_indexed_files(self, record: dict):
        """Save record of indexed files."""
        with open(self._index_record_path, "w") as f:
            json.dump(record, f, indent=2)

    def _file_hash(self, filepath: Path) -> str:
        """Compute MD5 hash of a file for change detection."""
        hasher = hashlib.md5()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    async def initialize(self):
        """Initialize embeddings model and process any new PDFs."""
        if self._initialized:
            return

        logger.info("Initializing RAG pipeline...")
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")

        # Initialize embedding model (local, no API key needed)
        self.embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )

        # Initialize or load ChromaDB
        self.vectorstore = Chroma(
            collection_name="medical_docs",
            embedding_function=self.embeddings,
            persist_directory=str(CHROMA_DB_DIR),
        )

        # Process PDFs
        await self._process_pdfs()
        self._initialized = True
        logger.info("RAG pipeline initialized successfully.")

    async def _process_pdfs(self):
        """Scan medical_docs directory and process new/changed PDFs."""
        indexed = self._get_indexed_files()
        pdf_files = list(MEDICAL_DOCS_DIR.glob("*.pdf"))

        if not pdf_files:
            logger.info("No PDF files found in medical_docs directory.")
            return

        for pdf_path in pdf_files:
            file_key = pdf_path.name
            file_hash = self._file_hash(pdf_path)

            if file_key in indexed and indexed[file_key] == file_hash:
                logger.info(f"Skipping already indexed: {file_key}")
                continue

            logger.info(f"Processing PDF: {file_key} ({pdf_path.stat().st_size / 1024 / 1024:.1f} MB)")

            try:
                # Load PDF
                loader = PyPDFLoader(str(pdf_path))
                documents = loader.load()
                logger.info(f"  Loaded {len(documents)} pages from {file_key}")

                # Split into chunks
                chunks = self.text_splitter.split_documents(documents)
                logger.info(f"  Split into {len(chunks)} chunks")

                # Add source metadata
                for i, chunk in enumerate(chunks):
                    chunk.metadata["source_file"] = file_key
                    chunk.metadata["chunk_index"] = i

                # Add to vectorstore in batches
                batch_size = 100
                for i in range(0, len(chunks), batch_size):
                    batch = chunks[i:i + batch_size]
                    self.vectorstore.add_documents(batch)
                    logger.info(f"  Indexed batch {i // batch_size + 1}/{(len(chunks) - 1) // batch_size + 1}")

                # Record as indexed
                indexed[file_key] = file_hash
                self._save_indexed_files(indexed)
                logger.info(f"  Successfully indexed: {file_key}")

            except Exception as e:
                logger.error(f"  Error processing {file_key}: {e}")

    async def retrieve(self, query: str, top_k: int = None) -> list:
        """Retrieve relevant document chunks for a query."""
        if not self._initialized:
            await self.initialize()

        k = top_k or RETRIEVAL_TOP_K

        try:
            results = self.vectorstore.similarity_search_with_relevance_scores(query, k=k)

            retrieved = []
            for doc, score in results:
                retrieved.append({
                    "content": doc.page_content,
                    "source": doc.metadata.get("source_file", "Unknown"),
                    "page": doc.metadata.get("page", "N/A"),
                    "relevance_score": round(score, 3),
                })

            return retrieved

        except Exception as e:
            logger.error(f"RAG retrieval error: {e}")
            return []

    async def get_context_string(self, query: str) -> tuple:
        """Get formatted context string and sources for LLM injection."""
        results = await self.retrieve(query)

        if not results:
            return "", []

        context_parts = []
        sources = []
        for i, r in enumerate(results, 1):
            context_parts.append(
                f"[Source {i}: {r['source']}, Page {r['page']}]\n{r['content']}"
            )
            sources.append({
                "source": r["source"],
                "page": r["page"],
                "relevance": r["relevance_score"],
            })

        context = "\n\n---\n\n".join(context_parts)
        return context, sources

    def get_stats(self) -> dict:
        """Get vector store statistics."""
        if not self.vectorstore:
            return {"status": "not_initialized", "total_chunks": 0}

        try:
            collection = self.vectorstore._collection
            return {
                "status": "ready",
                "total_chunks": collection.count(),
                "indexed_files": list(self._get_indexed_files().keys()),
            }
        except Exception:
            return {"status": "error", "total_chunks": 0}


# Singleton instance
rag_pipeline = RAGPipeline()
