"""
Settings configuration for the AI Agent
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    
    # LiveKit
    LIVEKIT_URL: str
    LIVEKIT_API_KEY: str
    LIVEKIT_API_SECRET: str
    
    # Deepgram (ASR)
    DEEPGRAM_API_KEY: str
    DEEPGRAM_MODEL: str = "nova-2"
    DEEPGRAM_LANGUAGE: str = "en"
    
    # Groq (LLM)
    GROQ_API_KEY: str
    GROQ_MODEL: str = "qwen/qwen3-32b"
    
    # OpenAI (LLM) - Optional, for switching providers
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    
    # ElevenLabs (TTS)
    ELEVENLABS_API_KEY: str
    ELEVENLABS_VOICE_ID: str = "21m00Tcm4TlvDq8ikWAM"  # Rachel
    
    # Provider selection (plug-and-play)
    LLM_PROVIDER: str = "groq"           # "groq", "openai"
    TTS_PROVIDER: str = "elevenlabs"     # "elevenlabs"
    ASR_PROVIDER: str = "deepgram"       # "deepgram"
    
    # Node.js Backend (for callbacks)
    BACKEND_URL: str = "http://localhost:3000"
    
    # System prompt for the AI agent
    SYSTEM_PROMPT: str = """You are a helpful AI customer care agent for a ride-sharing service. 
You assist drivers with their queries in a friendly and professional manner.
Keep responses concise and natural for voice conversation.
If you cannot help with something, offer to connect them to a human agent."""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra env variables not defined in Settings


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
