"""
MediMind AI - Configuration Module
Loads environment variables and provides centralized settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
MEDICAL_DOCS_DIR = BASE_DIR / "medical_docs"
CHROMA_DB_DIR = BASE_DIR / "chroma_db"
UPLOAD_DIR = BASE_DIR / "uploads"
DATABASE_DIR = BASE_DIR / "data"

# Create directories if they don't exist
MEDICAL_DOCS_DIR.mkdir(exist_ok=True)
CHROMA_DB_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)
DATABASE_DIR.mkdir(exist_ok=True)

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

# Database
SQLITE_DB_PATH = DATABASE_DIR / "medimind.db"
SQLITE_URL = f"sqlite+aiosqlite:///{SQLITE_DB_PATH}"

# RAG Configuration
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
RETRIEVAL_TOP_K = 5

# LLM Configuration
GEMINI_MODEL = "gemini-2.5-flash"

# Ollama Vision Model
OLLAMA_VISION_MODEL = "llava"

# System prompts
MEDICAL_SYSTEM_PROMPT = """You are MediMind AI, an intelligent medical assistant designed to help users understand medical information. 

IMPORTANT GUIDELINES:
1. You are NOT a replacement for professional medical advice, diagnosis, or treatment.
2. Always recommend consulting a healthcare professional for serious concerns.
3. Provide evidence-based medical information when possible.
4. Ask clarifying follow-up questions when symptoms are vague or incomplete.
5. Be empathetic and professional in your responses.
6. If you reference information from provided documents, cite the source.
7. For emergency symptoms, always advise calling emergency services immediately.
8. Use clear, simple language that patients can understand.
9. When discussing medications, mention common side effects and interactions.
10. Include a medical disclaimer when providing specific medical information.

When a user describes symptoms:
- Ask about duration, severity, and associated symptoms
- Consider common differential diagnoses
- Suggest when to seek immediate medical attention
- Provide general wellness recommendations

DISCLAIMER: Always include at the end of medical advice responses:
"⚕️ This information is for educational purposes only and should not replace professional medical consultation."
"""
