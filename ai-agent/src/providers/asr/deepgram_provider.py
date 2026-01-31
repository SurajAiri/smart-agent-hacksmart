"""
Deepgram ASR Provider.

Wraps Pipecat's DeepgramSTTService for plug-and-play ASR.
"""
from typing import Any
from loguru import logger

from pipecat.services.deepgram.stt import DeepgramSTTService

from src.providers.base import BaseASRProvider
from src.providers.registry import register_asr_provider


@register_asr_provider("deepgram")
class DeepgramASRProvider(BaseASRProvider):
    """Deepgram Automatic Speech Recognition provider."""
    
    name = "deepgram"
    
    def create_service(self, settings: Any) -> DeepgramSTTService:
        """
        Create a Deepgram STT service.
        
        Args:
            settings: Application settings with DEEPGRAM_API_KEY
            
        Returns:
            DeepgramSTTService instance
        """
        model = getattr(settings, "DEEPGRAM_MODEL", "nova-2")
        language = getattr(settings, "DEEPGRAM_LANGUAGE", "en")
        
        logger.info(f"Creating Deepgram STT service with model: {model}, language: {language}")
        
        return DeepgramSTTService(
            api_key=settings.DEEPGRAM_API_KEY,
            language=language,
            model=model,
        )
