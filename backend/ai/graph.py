"""
MediMind AI - LangGraph Multi-Modal Router
Routes user inputs to appropriate processing pipelines based on input type.
"""

import logging
from typing import TypedDict, Literal, Optional
from langgraph.graph import StateGraph, END
from backend.ai.rag import rag_pipeline
from backend.ai.image_analyzer import image_analyzer
from backend.ai.voice import voice_processor
from backend.ai.web_search import web_searcher
from backend.ai.conversational import conversational_ai

logger = logging.getLogger(__name__)


class MediMindState(TypedDict):
    input_type: str  # "text", "image", "voice", "web_search"
    user_message: str
    image_path: Optional[str]
    audio_data: Optional[bytes]
    conversation_history: list
    session_id: int
    # Processing results
    transcribed_text: str
    rag_context: str
    rag_sources: list
    web_context: str
    web_results: list
    image_analysis: Optional[dict]
    ai_response: str
    tts_audio: str
    error: str


async def classify_input(state: MediMindState) -> dict:
    """Already classified by the API layer — just pass through."""
    logger.info(f"Processing input type: {state['input_type']}")
    return {}


async def process_voice(state: MediMindState) -> dict:
    """Convert voice audio to text."""
    try:
        audio = state.get("audio_data")
        if not audio:
            return {"error": "No audio data provided", "transcribed_text": ""}
        text = await voice_processor.speech_to_text(audio)
        return {"transcribed_text": text, "user_message": text, "input_type": "text"}
    except Exception as e:
        logger.error(f"Voice processing error: {e}")
        return {"error": str(e), "transcribed_text": ""}


async def process_image(state: MediMindState) -> dict:
    """Analyze medical image with BiomedCLIP."""
    try:
        path = state.get("image_path")
        if not path:
            return {"error": "No image path provided"}
        analysis = await image_analyzer.analyze_image(path)
        return {"image_analysis": analysis}
    except Exception as e:
        logger.error(f"Image analysis error: {e}")
        return {"error": str(e)}


async def retrieve_rag(state: MediMindState) -> dict:
    """Retrieve relevant medical knowledge from ChromaDB."""
    try:
        query = state.get("user_message", "")
        if not query:
            return {"rag_context": "", "rag_sources": []}
        context, sources = await rag_pipeline.get_context_string(query)
        return {"rag_context": context, "rag_sources": sources}
    except Exception as e:
        logger.error(f"RAG retrieval error: {e}")
        return {"rag_context": "", "rag_sources": []}


async def search_web(state: MediMindState) -> dict:
    """Search the web for real-time medical information."""
    try:
        query = state.get("user_message", "")
        result = await web_searcher.search(query)
        return {
            "web_context": result.get("context", ""),
            "web_results": result.get("results", []),
        }
    except Exception as e:
        logger.error(f"Web search error: {e}")
        return {"web_context": "", "web_results": []}


async def generate_response(state: MediMindState) -> dict:
    """Generate AI response using Gemini with all available context."""
    try:
        response = await conversational_ai.generate_response(
            user_message=state.get("user_message", ""),
            conversation_history=state.get("conversation_history", []),
            rag_context=state.get("rag_context", ""),
            web_context=state.get("web_context", ""),
            image_analysis=state.get("image_analysis"),
        )
        return {"ai_response": response}
    except Exception as e:
        logger.error(f"Response generation error: {e}")
        return {"ai_response": f"Error generating response: {str(e)}"}


async def generate_tts(state: MediMindState) -> dict:
    """Optionally convert response to speech."""
    if state.get("input_type") == "voice" and voice_processor.is_available():
        try:
            resp = state.get("ai_response", "")[:500]
            audio = await voice_processor.text_to_speech(resp)
            return {"tts_audio": audio}
        except Exception as e:
            logger.error(f"TTS error: {e}")
    return {"tts_audio": ""}


def route_input(state: MediMindState) -> str:
    """Route based on input type."""
    t = state.get("input_type", "text")
    if t == "voice":
        return "process_voice"
    elif t == "image":
        return "process_image"
    elif t == "web_search":
        return "search_web_node"
    return "retrieve_rag"


def route_after_voice(state: MediMindState) -> str:
    """After voice transcription, go to RAG."""
    return "retrieve_rag"


def route_after_rag(state: MediMindState) -> str:
    """After RAG, check if web search is also needed."""
    query = state.get("user_message", "")
    if web_searcher.should_search_web(query) and web_searcher.is_available():
        return "search_web_node"
    return "generate_response"


def route_after_image(state: MediMindState) -> str:
    return "generate_response"


def route_after_web(state: MediMindState) -> str:
    return "generate_response"


def build_graph() -> StateGraph:
    """Build the LangGraph processing pipeline."""
    workflow = StateGraph(MediMindState)

    # Add nodes
    workflow.add_node("classify", classify_input)
    workflow.add_node("process_voice", process_voice)
    workflow.add_node("process_image", process_image)
    workflow.add_node("retrieve_rag", retrieve_rag)
    workflow.add_node("search_web_node", search_web)
    workflow.add_node("generate_response", generate_response)
    workflow.add_node("generate_tts", generate_tts)

    # Entry
    workflow.set_entry_point("classify")

    # Conditional routing from classifier
    workflow.add_conditional_edges("classify", route_input, {
        "process_voice": "process_voice",
        "process_image": "process_image",
        "retrieve_rag": "retrieve_rag",
        "search_web_node": "search_web_node",
    })

    # After voice -> RAG
    workflow.add_conditional_edges("process_voice", route_after_voice, {
        "retrieve_rag": "retrieve_rag",
    })

    # After RAG -> maybe web search or generate
    workflow.add_conditional_edges("retrieve_rag", route_after_rag, {
        "search_web_node": "search_web_node",
        "generate_response": "generate_response",
    })

    # After image -> generate
    workflow.add_conditional_edges("process_image", route_after_image, {
        "generate_response": "generate_response",
    })

    # After web search -> generate
    workflow.add_conditional_edges("search_web_node", route_after_web, {
        "generate_response": "generate_response",
    })

    # After response -> TTS -> END
    workflow.add_edge("generate_response", "generate_tts")
    workflow.add_edge("generate_tts", END)

    return workflow.compile()


# Compile the graph once
medimind_graph = build_graph()
