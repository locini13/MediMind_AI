"""
MediMind AI - Medical Image Analyzer
Analyzes medical images using LLaVA (Large Language-and-Vision Assistant) via local Ollama.
"""

import base64
import logging
import asyncio
from io import BytesIO
from PIL import Image
from langchain_community.chat_models import ChatOllama
from langchain_core.messages import HumanMessage
from backend.config import OLLAMA_VISION_MODEL

logger = logging.getLogger(__name__)


class MedicalImageAnalyzer:
    """
    Analyzes medical images using LLaVA (Large Language-and-Vision Assistant) via local Ollama.
    """
    def __init__(self):
        self.llm = ChatOllama(model=OLLAMA_VISION_MODEL)
        self.system_prompt = (
            "You are an expert medical AI assistant. Carefully analyze this medical image. "
            "Describe the visual findings, possible conditions it might represent, and any notable characteristics. "
            "Keep the response highly professional, objective, and clear. Do not provide a definitive medical diagnosis, "
            "but rather an observational analysis. Limit your response to 2-3 concise paragraphs."
        )
        logger.info(f"Initialized Medical Image Analyzer with {OLLAMA_VISION_MODEL}")

    async def analyze_image(self, image_path: str) -> str:
        """
        Analyzes a medical image using LLaVA.
        Accepts a file path string and returns analysis text.
        """
        try:
            # Load image from path
            image = Image.open(image_path)

            # Convert PIL Image to Base64
            buffered = BytesIO()
            if image.mode != 'RGB':
                image = image.convert('RGB')
            # Reduce image size to speed up local processing if it's too large
            image.thumbnail((800, 800))
            image.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

            # Create the message with the image
            message = HumanMessage(
                content=[
                    {"type": "text", "text": self.system_prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{img_str}"},
                    },
                ]
            )

            logger.info("Sending image to LLaVA for analysis...")
            # Run synchronous Ollama call in a thread pool to avoid blocking async loop
            response = await asyncio.to_thread(self.llm.invoke, [message])
            logger.info("Received analysis from LLaVA")

            return response.content

        except Exception as e:
            logger.error(f"Error in LLaVA image analysis: {str(e)}")
            return f"Error analyzing image: {str(e)}"


# Singleton instance
image_analyzer = MedicalImageAnalyzer()
