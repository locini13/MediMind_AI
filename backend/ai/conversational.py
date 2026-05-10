"""
MediMind AI - Conversational AI Module
Gemini 2.5 powered conversational medical assistant with context memory.
"""

import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from backend.config import GEMINI_API_KEY, GEMINI_MODEL, MEDICAL_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class ConversationalAI:
    def __init__(self):
        self.llm = None
        self._initialized = False

    async def initialize(self):
        if self._initialized:
            return
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is required.")
        self.llm = ChatGoogleGenerativeAI(
            model=GEMINI_MODEL, google_api_key=GEMINI_API_KEY,
            temperature=0.3, max_output_tokens=2048,
            convert_system_message_to_human=True,
        )
        self._initialized = True
        logger.info(f"Gemini LLM initialized: {GEMINI_MODEL}")

    async def generate_response(self, user_message, conversation_history=None,
                                rag_context="", web_context="", image_analysis=None):
        if not self._initialized:
            await self.initialize()

        messages = [SystemMessage(content=MEDICAL_SYSTEM_PROMPT)]
        context_parts = []

        if rag_context:
            context_parts.append(
                f"RETRIEVED MEDICAL KNOWLEDGE:\n{rag_context}\n"
                "Cite the source when referencing specific information."
            )
        if web_context:
            context_parts.append(f"REAL-TIME WEB INFORMATION:\n{web_context}")
        if image_analysis:
            context_parts.append(
                f"IMAGE ANALYSIS BY EXPERT VLM:\n{image_analysis}\n\n"
                "Based on this visual analysis, provide detailed medical interpretation and recommend next steps."
            )

        if context_parts:
            ctx = "\n\n---\n\n".join(context_parts)
            messages.append(HumanMessage(content=f"[CONTEXT]{ctx}"))
            messages.append(AIMessage(content="I'll use this context to respond."))

        if conversation_history:
            for msg in conversation_history[-10:]:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    messages.append(AIMessage(content=msg["content"]))

        messages.append(HumanMessage(content=user_message))

        try:
            response = await self.llm.ainvoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            return f"I encountered an error. Please try again.\n\nError: {str(e)}"

    async def generate_session_title(self, first_message):
        if not self._initialized:
            await self.initialize()
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content="Generate a concise title (max 6 words) for a medical chat. Return ONLY the title."),
                HumanMessage(content=first_message),
            ])
            return response.content.strip().strip('"')[:80]
        except Exception:
            return first_message[:50] + "..."


conversational_ai = ConversationalAI()
