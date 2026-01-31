"""
LLM Providers using Pipecat's native LLM services.

Supports: Groq, OpenAI
Future: LangChain integration for MCP tool calling
"""
from typing import Any
from loguru import logger

from src.providers.base import BaseLLMProvider
from src.providers.registry import register_llm_provider


@register_llm_provider("groq")
class GroqLLMProvider(BaseLLMProvider):
    """Groq LLM provider using Pipecat's native GroqLLMService."""
    
    name = "groq"
    
    def create_model(self, settings: Any) -> Any:
        """Not used - Pipecat handles model internally."""
        return None
    
    def create_service(self, settings: Any) -> Any:
        """Create a Groq LLM service."""
        from pipecat.services.groq.llm import GroqLLMService
        
        logger.info(f"Creating Groq LLM service with model: {settings.GROQ_MODEL}")
        
        return GroqLLMService(
            api_key=settings.GROQ_API_KEY,
            model=settings.GROQ_MODEL,
        )
    
    def create_context_aggregator(self, settings: Any) -> Any:
        """Not used directly - agent creates context aggregator."""
        return None


@register_llm_provider("openai")
class OpenAILLMProvider(BaseLLMProvider):
    """OpenAI LLM provider using Pipecat's native OpenAILLMService."""
    
    name = "openai"
    
    def create_model(self, settings: Any) -> Any:
        """Not used - Pipecat handles model internally."""
        return None
    
    def create_service(self, settings: Any) -> Any:
        """Create an OpenAI LLM service."""
        from pipecat.services.openai.llm import OpenAILLMService
        
        logger.info(f"Creating OpenAI LLM service with model: {settings.OPENAI_MODEL}")
        
        return OpenAILLMService(
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
        )
    
    def create_context_aggregator(self, settings: Any) -> Any:
        """Not used directly - agent creates context aggregator."""
        return None


@register_llm_provider("google")
class GoogleLLMProvider(BaseLLMProvider):
    """Google Gemini LLM provider - fastest high-quality model."""
    
    name = "google"
    
    def create_model(self, settings: Any) -> Any:
        """Not used - Pipecat handles model internally."""
        return None
    
    def create_service(self, settings: Any) -> Any:
        """Create a Google Gemini LLM service."""
        from pipecat.services.google.llm import GoogleLLMService
        
        model = getattr(settings, 'GOOGLE_MODEL', 'gemini-2.0-flash')
        logger.info(f"Creating Google Gemini LLM service with model: {model}")
        
        return GoogleLLMService(
            api_key=settings.GOOGLE_API_KEY,
            model=model,
        )
    
    def create_context_aggregator(self, settings: Any) -> Any:
        """Not used directly - agent creates context aggregator."""
        return None


# TODO: Future LangChain provider for MCP tool calling
# @register_llm_provider("langchain")
# class LangChainLLMProvider(BaseLLMProvider):
#     """LangChain LLM provider with MCP tool calling support."""
#     
#     def create_service(self, settings: Any) -> Any:
#         from pipecat.processors.frameworks.langchain import LangchainProcessor
#         from langchain_groq import ChatGroq
#         from langchain_core.prompts import ChatPromptTemplate
#         
#         # Build LangChain chain with system prompt
#         llm = ChatGroq(model=settings.GROQ_MODEL, api_key=settings.GROQ_API_KEY)
#         prompt = ChatPromptTemplate.from_messages([
#             ("system", settings.SYSTEM_PROMPT),
#             ("human", "{input}"),
#         ])
#         chain = prompt | llm
#         
#         return LangchainProcessor(chain=chain)
