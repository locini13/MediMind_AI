"""
MediMind AI - Database Setup
SQLite with SQLAlchemy async for chat memory and session management.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from backend.config import SQLITE_URL


class Base(DeclarativeBase):
    pass


engine = create_async_engine(SQLITE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """Create all database tables on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    """Dependency to get a database session."""
    async with async_session() as session:
        yield session
