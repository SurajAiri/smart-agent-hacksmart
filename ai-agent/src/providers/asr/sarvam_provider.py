"""
Sarvam ASR Provider.

Wraps Pipecat's SarvamSTTService for plug-and-play ASR with Indian language support.
"""
from typing import Any
from loguru import logger

from pipecat.services.sarvam.stt import SarvamSTTService
from pipecat.transcriptions.language import Language

from src.providers.base import BaseASRProvider
from src.providers.registry import register_asr_provider


@register_asr_provider("sarvam")
class SarvamASRProvider(BaseASRProvider):
    """Sarvam Automatic Speech Recognition provider for Indian languages."""
    
    name = "sarvam"
    
    def create_service(self, settings: Any) -> SarvamSTTService:
        """
        Create a Sarvam STT service.
        
        Args:
            settings: Application settings with SARVAM_API_KEY
            
        Returns:
            SarvamSTTService instance
        """
        model = getattr(settings, "SARVAM_ASR_MODEL", "saarika:v2.5")
        language_code = getattr(settings, "SARVAM_LANGUAGE", "hi-IN")
        
        # Map language codes to pipecat Language enum (must use _IN variants for Sarvam)
        language_map = {
            "hi-IN": Language.HI_IN,  # Hindi
            "en-IN": Language.EN_IN,  # English (Indian)
            "ta-IN": Language.TA_IN,  # Tamil
            "te-IN": Language.TE_IN,  # Telugu
            "kn-IN": Language.KN_IN,  # Kannada
            "ml-IN": Language.ML_IN,  # Malayalam
            "mr-IN": Language.MR_IN,  # Marathi
            "gu-IN": Language.GU_IN,  # Gujarati
            "bn-IN": Language.BN_IN,  # Bengali
            "pa-IN": Language.PA_IN,  # Punjabi
        }
        
        language = language_map.get(language_code, Language.HI_IN)
        
        logger.info(f"Creating Sarvam STT service with model: {model}, language: {language_code}")
        
        return SarvamSTTService(
            api_key=settings.SARVAM_API_KEY,
            model=model,
            params=SarvamSTTService.InputParams(
                language=language,
            ),
        )
