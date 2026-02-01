"""
Smart Agent AI - FastAPI Entry Point

This is the main entry point for the Python AI agent that handles
voice conversations via Pipecat and LiveKit.
"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from src.config.settings import get_settings
from src.api.routes import router as api_router
from src.api.handoff_routes import router as handoff_router
from src.bot.manager import BotManager
from src.core.conversation_tracker import get_conversation_tracker
from src.core.handoff_manager import get_handoff_manager

# Global bot manager instance
bot_manager: BotManager | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    global bot_manager
    
    settings = get_settings()
    logger.info("Starting Smart Agent AI...")
    logger.info(f"LiveKit URL: {settings.LIVEKIT_URL}")
    logger.info(f"Backend URL: {settings.BACKEND_URL}")
    logger.info(f"Providers - LLM: {settings.LLM_PROVIDER}, TTS: {settings.TTS_PROVIDER}, ASR: {settings.ASR_PROVIDER}")
    
    # Initialize bot manager
    bot_manager = BotManager()
    app.state.bot_manager = bot_manager
    
    # Initialize conversation tracker and handoff manager
    conversation_tracker = get_conversation_tracker()
    handoff_manager = get_handoff_manager()
    app.state.conversation_tracker = conversation_tracker
    app.state.handoff_manager = handoff_manager
    
    logger.info("Handoff system initialized")
    logger.info("Smart Agent AI started successfully")
    
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down Smart Agent AI...")
    if bot_manager:
        await bot_manager.shutdown()
    logger.info("Shutdown complete")


app = FastAPI(
    title="Smart Agent AI",
    description="AI Customer Care Voice Agent using Pipecat and LiveKit",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware for agent dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to dashboard domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")
app.include_router(handoff_router, prefix="/api")


@app.get("/")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "smart-agent-ai",
        "active_bots": len(bot_manager.active_bots) if bot_manager else 0,
    }


@app.get("/health")
async def health():
    """Detailed health check"""
    settings = get_settings()
    return {
        "status": "healthy",
        "providers": {
            "llm": settings.LLM_PROVIDER,
            "tts": settings.TTS_PROVIDER,
            "asr": settings.ASR_PROVIDER,
        },
        "settings": {
            "livekit_configured": bool(settings.LIVEKIT_URL),
            "deepgram_configured": bool(settings.DEEPGRAM_API_KEY),
            "groq_configured": bool(settings.GROQ_API_KEY),
            "elevenlabs_configured": bool(settings.ELEVENLABS_API_KEY),
        },
    }


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "src.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
