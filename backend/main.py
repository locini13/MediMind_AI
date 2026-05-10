"""
MediMind AI - FastAPI Main Application
Entry point for the backend server.
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.database import init_db
from backend.chat.routes import router as chat_router
from backend.ai.rag import rag_pipeline
from backend.ai.conversational import conversational_ai
from backend.ai.image_analyzer import image_analyzer
from backend.ai.voice import voice_processor
from backend.ai.web_search import web_searcher
from backend.config import UPLOAD_DIR

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# Resolve paths
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("=" * 60)
    logger.info("  MediMind AI - Starting up...")
    logger.info("=" * 60)

    # Initialize database
    await init_db()
    logger.info("✓ Database initialized")

    # Initialize AI modules
    try:
        await conversational_ai.initialize()
        logger.info("✓ Conversational AI ready (Gemini 2.5)")
    except Exception as e:
        logger.error(f"✗ Conversational AI failed: {e}")

    try:
        await rag_pipeline.initialize()
        stats = rag_pipeline.get_stats()
        logger.info(f"✓ RAG pipeline ready ({stats.get('total_chunks', 0)} chunks indexed)")
    except Exception as e:
        logger.error(f"✗ RAG pipeline failed: {e}")

    try:
        await voice_processor.initialize()
        logger.info(f"✓ Voice processor {'ready' if voice_processor.is_available() else 'unavailable (no API key)'}")
    except Exception as e:
        logger.error(f"✗ Voice processor failed: {e}")

    try:
        await web_searcher.initialize()
        logger.info(f"✓ Web search {'ready' if web_searcher.is_available() else 'unavailable (no API key)'}")
    except Exception as e:
        logger.error(f"✗ Web search failed: {e}")

    # BiomedCLIP is loaded lazily on first use (it's large)
    logger.info("○ BiomedCLIP will load on first image analysis request")

    logger.info("=" * 60)
    logger.info("  MediMind AI is ready! Open http://localhost:8000")
    logger.info("=" * 60)

    yield

    logger.info("MediMind AI shutting down...")


# Create FastAPI app
app = FastAPI(
    title="MediMind AI",
    description="AI-Powered Medical Assistant",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(chat_router)

# Serve uploaded files
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# Serve frontend static files
if FRONTEND_DIR.exists():
    app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
    app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")
    if (FRONTEND_DIR / "assets").exists():
        app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR / "assets")), name="assets")


@app.get("/")
async def serve_frontend():
    """Serve the main frontend page."""
    index = FRONTEND_DIR / "index.html"
    if index.exists():
        return FileResponse(str(index))
    return {"message": "MediMind AI Backend is running. Frontend not found."}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "MediMind AI",
        "rag": rag_pipeline.get_stats(),
        "voice": voice_processor.is_available(),
        "web_search": web_searcher.is_available(),
    }
