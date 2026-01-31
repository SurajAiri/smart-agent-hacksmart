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
    
    # Google Gemini (LLM) - Fastest high-quality model
    GOOGLE_API_KEY: str = ""
    GOOGLE_MODEL: str = "gemini-2.0-flash"
    
    # ElevenLabs (TTS)
    ELEVENLABS_API_KEY: str
    ELEVENLABS_VOICE_ID: str = "21m00Tcm4TlvDq8ikWAM"  # Rachel
    
    # Sarvam AI (TTS & ASR for Indian languages)
    SARVAM_API_KEY: str = ""
    SARVAM_TTS_SPEAKER: str = "anushka"
    SARVAM_ASR_MODEL: str = "saarika:v2.5"
    SARVAM_LANGUAGE: str = "hi-IN"  # Hindi, can be: hi-IN, en-IN, ta-IN, te-IN, kn-IN, ml-IN, mr-IN, gu-IN, bn-IN, pa-IN
    
    # Provider selection (plug-and-play)
    LLM_PROVIDER: str = "groq"           # "groq", "openai", "google"
    TTS_PROVIDER: str = "elevenlabs"     # "elevenlabs", "sarvam"
    ASR_PROVIDER: str = "deepgram"       # "deepgram", "sarvam"
    
    # Node.js Backend (for callbacks)
    BACKEND_URL: str = "http://localhost:3000"
    
    # System prompt for the AI agent
    SYSTEM_PROMPT: str = """You are a helpful AI customer care agent for a ride-sharing service called "QuickRide".
You assist drivers and passengers with their queries in a friendly and professional manner.

IMPORTANT GUIDELINES:
1. Keep responses concise and natural for voice conversation (1-2 sentences when possible)
2. Use the available tools to look up real information - don't make up data
3. When users ask about trips, fares, drivers, or policies, ALWAYS use the appropriate tool first
4. Speak in a warm, helpful tone as if talking to a friend
5. If you cannot help with something, use escalate_to_support tool

AVAILABLE TOOLS:
- get_trip_status: Get current ride status, ETA, fare info
- get_driver_info: Get driver details, vehicle info, contact
- lookup_faq: Search FAQs about pricing, policies, safety, etc.
- get_trip_history: Get past ride history
- escalate_to_support: Connect to human support for urgent issues

Always greet warmly and ask how you can help. Use Hindi/Hinglish if the user speaks in Hindi."""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra env variables not defined in Settings


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
