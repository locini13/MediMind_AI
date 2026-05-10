"""
MediMind AI - Chat Memory Manager
Handles storing and retrieving chat history from SQLite for context-aware conversations.
"""

import json
import datetime
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.chat.models import ChatSession, ChatMessage


class ChatMemoryManager:
    """Manages chat sessions and messages in SQLite."""

    @staticmethod
    async def create_session(db: AsyncSession, title: str = "New Conversation") -> ChatSession:
        """Create a new chat session."""
        session = ChatSession(title=title)
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    @staticmethod
    async def get_session(db: AsyncSession, session_id: int) -> ChatSession:
        """Get a chat session by ID with messages."""
        result = await db.execute(
            select(ChatSession)
            .options(selectinload(ChatSession.messages))
            .where(ChatSession.id == session_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_sessions(db: AsyncSession, limit: int = 50) -> list:
        """List all chat sessions, most recent first."""
        result = await db.execute(
            select(ChatSession)
            .options(selectinload(ChatSession.messages))
            .order_by(desc(ChatSession.updated_at))
            .limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def delete_session(db: AsyncSession, session_id: int) -> bool:
        """Delete a chat session and all its messages."""
        session = await ChatMemoryManager.get_session(db, session_id)
        if session:
            await db.delete(session)
            await db.commit()
            return True
        return False

    @staticmethod
    async def add_message(
        db: AsyncSession,
        session_id: int,
        role: str,
        content: str,
        message_type: str = "text",
        source_refs: str = "",
        image_url: str = "",
    ) -> ChatMessage:
        """Add a message to a chat session."""
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            message_type=message_type,
            source_refs=source_refs,
            image_url=image_url,
        )
        db.add(message)

        # Update session timestamp and title if first user message
        result = await db.execute(
            select(ChatSession).where(ChatSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if session:
            session.updated_at = datetime.datetime.utcnow()
            if role == "user" and session.title == "New Conversation":
                # Auto-generate title from first message
                session.title = content[:80] + ("..." if len(content) > 80 else "")

        await db.commit()
        await db.refresh(message)
        return message

    @staticmethod
    async def get_conversation_history(
        db: AsyncSession, session_id: int, limit: int = 20
    ) -> list:
        """Get recent messages for a session, formatted for LLM context."""
        result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(desc(ChatMessage.timestamp))
            .limit(limit)
        )
        messages = result.scalars().all()
        messages.reverse()  # Chronological order

        history = []
        for msg in messages:
            history.append({
                "role": msg.role,
                "content": msg.content,
            })
        return history

    @staticmethod
    async def export_session(db: AsyncSession, session_id: int) -> dict:
        """Export a full chat session for download."""
        session = await ChatMemoryManager.get_session(db, session_id)
        if not session:
            return None

        return {
            "session_id": session.id,
            "title": session.title,
            "created_at": session.created_at.isoformat(),
            "messages": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "type": msg.message_type,
                    "sources": msg.source_refs,
                    "timestamp": msg.timestamp.isoformat(),
                }
                for msg in session.messages
            ],
        }
