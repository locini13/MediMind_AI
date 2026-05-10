"""
MediMind AI - Chat API Routes
Handles all chat, image, voice, and web search API endpoints.
"""

import os
import json
import uuid
import logging
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.chat.memory import ChatMemoryManager
from backend.ai.graph import medimind_graph, MediMindState
from backend.ai.rag import rag_pipeline
from backend.ai.web_search import web_searcher
from backend.ai.voice import voice_processor
from backend.config import UPLOAD_DIR

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])
memory = ChatMemoryManager()


@router.post("/message")
async def send_message(
    message: str = Form(...),
    session_id: int = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """Send a text message and get AI response."""
    try:
        # Create session if needed
        if not session_id:
            session = await memory.create_session(db)
            session_id = session.id

        # Get conversation history
        history = await memory.get_conversation_history(db, session_id)

        # Save user message
        await memory.add_message(db, session_id, "user", message, "text")

        # Run through LangGraph pipeline
        initial_state: MediMindState = {
            "input_type": "text",
            "user_message": message,
            "image_path": None,
            "audio_data": None,
            "conversation_history": history,
            "session_id": session_id,
            "transcribed_text": "",
            "rag_context": "",
            "rag_sources": [],
            "web_context": "",
            "web_results": [],
            "image_analysis": None,
            "ai_response": "",
            "tts_audio": "",
            "error": "",
        }

        result = await medimind_graph.ainvoke(initial_state)

        # Save AI response
        source_refs = json.dumps(result.get("rag_sources", []))
        await memory.add_message(
            db, session_id, "assistant",
            result["ai_response"], "text", source_refs
        )

        return JSONResponse({
            "response": result["ai_response"],
            "session_id": session_id,
            "sources": result.get("rag_sources", []),
            "web_results": result.get("web_results", []),
        })

    except Exception as e:
        logger.error(f"Chat message error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/image")
async def analyze_image(
    image: UploadFile = File(...),
    message: str = Form("Please analyze this medical image."),
    session_id: int = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """Upload and analyze a medical image."""
    try:
        if not session_id:
            session = await memory.create_session(db)
            session_id = session.id

        # Save uploaded image
        ext = Path(image.filename).suffix or ".jpg"
        filename = f"{uuid.uuid4().hex}{ext}"
        filepath = UPLOAD_DIR / filename
        content = await image.read()
        with open(filepath, "wb") as f:
            f.write(content)

        history = await memory.get_conversation_history(db, session_id)

        # Save user message with image
        await memory.add_message(
            db, session_id, "user", message, "image",
            image_url=f"/uploads/{filename}"
        )

        # Run through LangGraph
        initial_state: MediMindState = {
            "input_type": "image",
            "user_message": message,
            "image_path": str(filepath),
            "audio_data": None,
            "conversation_history": history,
            "session_id": session_id,
            "transcribed_text": "",
            "rag_context": "",
            "rag_sources": [],
            "web_context": "",
            "web_results": [],
            "image_analysis": None,
            "ai_response": "",
            "tts_audio": "",
            "error": "",
        }

        result = await medimind_graph.ainvoke(initial_state)

        await memory.add_message(
            db, session_id, "assistant",
            result["ai_response"], "text"
        )

        return JSONResponse({
            "response": result["ai_response"],
            "session_id": session_id,
            "image_analysis": result.get("image_analysis"),
            "image_url": f"/uploads/{filename}",
        })

    except Exception as e:
        logger.error(f"Image analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/voice")
async def process_voice(
    audio: UploadFile = File(...),
    session_id: int = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """Process voice input — transcribe and respond."""
    try:
        if not session_id:
            session = await memory.create_session(db)
            session_id = session.id

        audio_data = await audio.read()
        history = await memory.get_conversation_history(db, session_id)

        initial_state: MediMindState = {
            "input_type": "voice",
            "user_message": "",
            "image_path": None,
            "audio_data": audio_data,
            "conversation_history": history,
            "session_id": session_id,
            "transcribed_text": "",
            "rag_context": "",
            "rag_sources": [],
            "web_context": "",
            "web_results": [],
            "image_analysis": None,
            "ai_response": "",
            "tts_audio": "",
            "error": "",
        }

        result = await medimind_graph.ainvoke(initial_state)

        transcribed = result.get("transcribed_text", "")
        if transcribed:
            await memory.add_message(db, session_id, "user", transcribed, "voice")
        await memory.add_message(
            db, session_id, "assistant", result["ai_response"], "text"
        )

        return JSONResponse({
            "response": result["ai_response"],
            "session_id": session_id,
            "transcribed_text": transcribed,
            "tts_audio": result.get("tts_audio", ""),
            "sources": result.get("rag_sources", []),
        })

    except Exception as e:
        logger.error(f"Voice processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/web-search")
async def web_search(
    query: str = Form(...),
    session_id: int = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """Search web for real-time medical information."""
    try:
        if not session_id:
            session = await memory.create_session(db)
            session_id = session.id

        history = await memory.get_conversation_history(db, session_id)
        await memory.add_message(db, session_id, "user", query, "text")

        initial_state: MediMindState = {
            "input_type": "web_search",
            "user_message": query,
            "image_path": None,
            "audio_data": None,
            "conversation_history": history,
            "session_id": session_id,
            "transcribed_text": "",
            "rag_context": "",
            "rag_sources": [],
            "web_context": "",
            "web_results": [],
            "image_analysis": None,
            "ai_response": "",
            "tts_audio": "",
            "error": "",
        }

        result = await medimind_graph.ainvoke(initial_state)

        await memory.add_message(
            db, session_id, "assistant", result["ai_response"], "text"
        )

        return JSONResponse({
            "response": result["ai_response"],
            "session_id": session_id,
            "web_results": result.get("web_results", []),
        })

    except Exception as e:
        logger.error(f"Web search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Session Management ────────────────────────────────────────────

@router.get("/sessions")
async def list_sessions(db: AsyncSession = Depends(get_db)):
    """List all chat sessions."""
    sessions = await memory.list_sessions(db)
    return [s.to_dict() for s in sessions]


@router.post("/sessions")
async def create_session(db: AsyncSession = Depends(get_db)):
    """Create a new chat session."""
    session = await memory.create_session(db)
    return session.to_dict()


@router.get("/sessions/{session_id}")
async def get_session(session_id: int, db: AsyncSession = Depends(get_db)):
    """Get a session with all messages."""
    session = await memory.get_session(db, session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    return {
        **session.to_dict(),
        "messages": [m.to_dict() for m in session.messages],
    }


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a chat session."""
    success = await memory.delete_session(db, session_id)
    if not success:
        raise HTTPException(404, "Session not found")
    return {"status": "deleted"}


@router.get("/export/{session_id}")
async def export_session(session_id: int, db: AsyncSession = Depends(get_db)):
    """Export a session as JSON."""
    data = await memory.export_session(db, session_id)
    if not data:
        raise HTTPException(404, "Session not found")
    return data


@router.get("/rag-stats")
async def get_rag_stats():
    """Get RAG pipeline statistics."""
    return rag_pipeline.get_stats()
