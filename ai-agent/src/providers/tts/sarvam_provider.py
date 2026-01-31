"""
Sarvam AI TTS Provider.

Wraps Pipecat's SarvamTTSService for Indian language TTS.
"""
from typing import Any
from loguru import logger

from pipecat.services.sarvam.tts import SarvamTTSService

from src.providers.base import BaseTTSProvider
from src.providers.registry import register_tts_provider


@register_tts_provider("sarvam")
class SarvamTTSProvider(BaseTTSProvider):
    """Sarvam AI Text-to-Speech provider for Indian languages."""
    
    name = "sarvam"
    
    def create_service(self, settings: Any) -> SarvamTTSService:
        """
        Create a Sarvam TTS service.
        
        Args:
            settings: Application settings with SARVAM_API_KEY and SARVAM_TTS_SPEAKER
            
        Returns:
            SarvamTTSService instance
        """
        voice_id = getattr(settings, 'SARVAM_TTS_SPEAKER', 'anushka')
        logger.info(f"Creating Sarvam TTS service with voice: {voice_id}")
        
        return SarvamTTSService(
            api_key=settings.SARVAM_API_KEY,
            voice_id=voice_id,
            model="bulbul:v2",
            sample_rate=24000,
        )
