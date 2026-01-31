"""
Base classes for AI providers.

Each provider wraps a specific service (LLM, TTS, ASR) and returns
a Pipecat-compatible service or LangChain model.
"""
from abc import ABC, abstractmethod
from typing import Any


class BaseLLMProvider(ABC):
    """Base class for LLM providers."""
    
    name: str = "base"
    
    @abstractmethod
    def create_model(self, settings: Any) -> Any:
        """
        Create and return a LangChain ChatModel.
        
        Args:
            settings: Application settings with API keys and config
            
        Returns:
            A LangChain BaseChatModel instance
        """
        pass
    
    @abstractmethod
    def create_context_aggregator(self, settings: Any) -> Any:
        """
        Create a context aggregator for managing conversation history.
        
        Args:
            settings: Application settings
            
        Returns:
            Context aggregator compatible with Pipecat pipeline
        """
        pass


class BaseTTSProvider(ABC):
    """Base class for Text-to-Speech providers."""
    
    name: str = "base"
    
    @abstractmethod
    def create_service(self, settings: Any) -> Any:
        """
        Create and return a Pipecat TTS service.
        
        Args:
            settings: Application settings with API keys and config
            
        Returns:
            A Pipecat-compatible TTS service
        """
        pass


class BaseASRProvider(ABC):
    """Base class for Automatic Speech Recognition providers."""
    
    name: str = "base"
    
    @abstractmethod
    def create_service(self, settings: Any) -> Any:
        """
        Create and return a Pipecat ASR/STT service.
        
        Args:
            settings: Application settings with API keys and config
            
        Returns:
            A Pipecat-compatible STT service
        """
        pass
