"""
MediMind AI - Voice Processing
ElevenLabs integration for Speech-to-Text and Text-to-Speech.
"""

import io
import base64
import logging
import tempfile
from pathlib import Path

from backend.config import ELEVENLABS_API_KEY

logger = logging.getLogger(__name__)


class VoiceProcessor:
    """Handles voice input/output using ElevenLabs API."""

    def __init__(self):
        self.client = None
        self._initialized = False

    async def initialize(self):
        """Initialize ElevenLabs client."""
        if self._initialized:
            return

        if not ELEVENLABS_API_KEY:
            logger.warning("ElevenLabs API key not set. Voice features will be limited.")
            return

        try:
            from elevenlabs.client import ElevenLabs
            self.client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
            self._initialized = True
            logger.info("ElevenLabs client initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize ElevenLabs: {e}")

    async def speech_to_text(self, audio_data: bytes, filename: str = "audio.webm") -> str:
        """
        Convert speech audio to text using ElevenLabs Scribe.
        Falls back to a message if API is unavailable.
        """
        if not self._initialized:
            await self.initialize()

        if not self.client:
            return self._fallback_stt(audio_data)

        try:
            # Save audio to temp file for ElevenLabs API
            with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
                tmp.write(audio_data)
                tmp_path = tmp.name

            # Use ElevenLabs transcription
            with open(tmp_path, "rb") as audio_file:
                transcription = self.client.speech_to_text.convert(
                    file=audio_file,
                    model_id="scribe_v1",
                    language_code="en",
                )

            # Clean up temp file
            Path(tmp_path).unlink(missing_ok=True)

            return transcription.text if hasattr(transcription, 'text') else str(transcription)

        except Exception as e:
            logger.error(f"ElevenLabs STT error: {e}")
            return self._fallback_stt(audio_data)

    async def text_to_speech(self, text: str) -> str:
        """
        Convert text to speech audio using ElevenLabs.
        Returns base64-encoded audio data.
        """
        if not self._initialized:
            await self.initialize()

        if not self.client:
            return ""

        try:
            # Generate audio
            audio_generator = self.client.generate(
                text=text[:5000],  # Limit text length
                voice="Rachel",  # Professional female voice
                model="eleven_multilingual_v2",
            )

            # Collect audio bytes
            audio_bytes = b""
            for chunk in audio_generator:
                audio_bytes += chunk

            # Return as base64
            return base64.b64encode(audio_bytes).decode("utf-8")

        except Exception as e:
            logger.error(f"ElevenLabs TTS error: {e}")
            return ""

    def _fallback_stt(self, audio_data: bytes) -> str:
        """Fallback when ElevenLabs is not available."""
        logger.warning("Using fallback STT — ElevenLabs not available")
        return "[Voice input received but ElevenLabs API key is not configured. Please type your query instead.]"

    def is_available(self) -> bool:
        """Check if voice processing is available."""
        return self._initialized and self.client is not None


# Singleton instance
voice_processor = VoiceProcessor()
