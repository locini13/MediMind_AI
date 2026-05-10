"""
MediMind AI - Web Search Module
Real-time medical information retrieval using Tavily API.
"""

import logging
from backend.config import TAVILY_API_KEY

logger = logging.getLogger(__name__)


class WebSearcher:
    """Retrieves real-time medical information from the web."""

    def __init__(self):
        self.client = None
        self._initialized = False

    async def initialize(self):
        """Initialize the Tavily search client."""
        if self._initialized:
            return

        if not TAVILY_API_KEY:
            logger.warning("Tavily API key not set. Web search will be unavailable.")
            return

        try:
            from tavily import TavilyClient
            self.client = TavilyClient(api_key=TAVILY_API_KEY)
            self._initialized = True
            logger.info("Tavily web search initialized.")
        except Exception as e:
            logger.error(f"Failed to initialize Tavily: {e}")

    async def search(self, query: str, max_results: int = 5) -> dict:
        """
        Search the web for medical information.
        
        Returns:
            Dictionary with results and formatted context.
        """
        if not self._initialized:
            await self.initialize()

        if not self.client:
            return {
                "results": [],
                "context": "",
                "error": "Web search is not configured. Please set TAVILY_API_KEY.",
            }

        try:
            # Add medical context to the query
            medical_query = f"medical healthcare {query}"

            response = self.client.search(
                query=medical_query,
                search_depth="advanced",
                max_results=max_results,
                include_domains=[
                    "mayoclinic.org",
                    "webmd.com",
                    "nih.gov",
                    "who.int",
                    "cdc.gov",
                    "medlineplus.gov",
                    "healthline.com",
                    "clevelandclinic.org",
                ],
            )

            results = []
            context_parts = []

            for i, result in enumerate(response.get("results", []), 1):
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "content": result.get("content", ""),
                    "score": result.get("score", 0),
                })
                context_parts.append(
                    f"[Web Source {i}: {result.get('title', 'Unknown')}]\n"
                    f"URL: {result.get('url', '')}\n"
                    f"{result.get('content', '')}"
                )

            return {
                "results": results,
                "context": "\n\n---\n\n".join(context_parts),
                "query": query,
            }

        except Exception as e:
            logger.error(f"Web search error: {e}")
            return {
                "results": [],
                "context": "",
                "error": str(e),
            }

    def is_available(self) -> bool:
        """Check if web search is available."""
        return self._initialized and self.client is not None

    @staticmethod
    def should_search_web(query: str) -> bool:
        """Determine if a query would benefit from web search."""
        web_indicators = [
            "latest", "recent", "new", "current", "update",
            "news", "research", "study", "2024", "2025", "2026",
            "drug", "medication", "treatment", "vaccine",
            "outbreak", "pandemic", "epidemic",
            "fda", "who", "cdc",
            "clinical trial", "approval",
            "side effect", "recall",
            "guideline", "recommendation",
        ]
        query_lower = query.lower()
        return any(indicator in query_lower for indicator in web_indicators)


# Singleton instance
web_searcher = WebSearcher()
