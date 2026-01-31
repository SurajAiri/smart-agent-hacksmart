"""
Provider registry - Factory for getting providers by name.
"""
from typing import Dict, Type
from loguru import logger

from src.providers.base import BaseLLMProvider, BaseTTSProvider, BaseASRProvider


# Provider registries
_llm_providers: Dict[str, Type[BaseLLMProvider]] = {}
_tts_providers: Dict[str, Type[BaseTTSProvider]] = {}
_asr_providers: Dict[str, Type[BaseASRProvider]] = {}


def register_llm_provider(name: str):
    """Decorator to register an LLM provider."""
    def decorator(cls: Type[BaseLLMProvider]):
        _llm_providers[name] = cls
        logger.debug(f"Registered LLM provider: {name}")
        return cls
    return decorator


def register_tts_provider(name: str):
    """Decorator to register a TTS provider."""
    def decorator(cls: Type[BaseTTSProvider]):
        _tts_providers[name] = cls
        logger.debug(f"Registered TTS provider: {name}")
        return cls
    return decorator


def register_asr_provider(name: str):
    """Decorator to register an ASR provider."""
    def decorator(cls: Type[BaseASRProvider]):
        _asr_providers[name] = cls
        logger.debug(f"Registered ASR provider: {name}")
        return cls
    return decorator


def get_llm_provider(name: str) -> BaseLLMProvider:
    """Get an LLM provider instance by name."""
    # Import providers to trigger registration
    from src.providers.llm import langchain_provider  # noqa: F401
    
    if name not in _llm_providers:
        available = list(_llm_providers.keys())
        raise ValueError(f"Unknown LLM provider: {name}. Available: {available}")
    
    return _llm_providers[name]()


def get_tts_provider(name: str) -> BaseTTSProvider:
    """Get a TTS provider instance by name."""
    # Import providers to trigger registration
    from src.providers.tts import elevenlabs_provider  # noqa: F401
    
    if name not in _tts_providers:
        available = list(_tts_providers.keys())
        raise ValueError(f"Unknown TTS provider: {name}. Available: {available}")
    
    return _tts_providers[name]()


def get_asr_provider(name: str) -> BaseASRProvider:
    """Get an ASR provider instance by name."""
    # Import providers to trigger registration
    from src.providers.asr import deepgram_provider  # noqa: F401
    
    if name not in _asr_providers:
        available = list(_asr_providers.keys())
        raise ValueError(f"Unknown ASR provider: {name}. Available: {available}")
    
    return _asr_providers[name]()
