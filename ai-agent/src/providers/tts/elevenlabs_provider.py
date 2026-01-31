"""
ElevenLabs TTS Provider.

Wraps Pipecat's ElevenLabsTTSService for plug-and-play TTS.
"""
from typing import Any
from loguru import logger

from pipecat.services.elevenlabs.tts import ElevenLabsTTSService, ElevenLabsOutputFormat

from src.providers.base import BaseTTSProvider
from src.providers.registry import register_tts_provider


@register_tts_provider("elevenlabs")
class ElevenLabsTTSProvider(BaseTTSProvider):
    """ElevenLabs Text-to-Speech provider."""
    
    name = "elevenlabs"
    
    def create_service(self, settings: Any) -> ElevenLabsTTSService:
        """
        Create an ElevenLabs TTS service optimized for low latency.
        
        Args:
            settings: Application settings with ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID
            
        Returns:
            ElevenLabsTTSService instance
        """
        logger.info(f"Creating ElevenLabs TTS service with voice: {settings.ELEVENLABS_VOICE_ID}")
        
        return ElevenLabsTTSService(
            api_key=settings.ELEVENLABS_API_KEY,
            voice_id=settings.ELEVENLABS_VOICE_ID,
            model="eleven_turbo_v2_5",
            output_format="pcm_24000",
        )
