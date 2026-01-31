"""
Smart Agent AI - FastAPI Entry Point

This is the main entry point for the Python AI agent that handles
voice conversations via Pipecat and LiveKit.
"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from loguru import logger

from src.config.settings import get_settings
from src.api.routes import router as api_router
from src.bot.manager import BotManager

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
    
    # Initialize bot manager
    bot_manager = BotManager()
    app.state.bot_manager = bot_manager
    
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

# Include API routes
app.include_router(api_router, prefix="/api")


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
    return {
        "status": "healthy",
        "settings": {
            "livekit_configured": bool(get_settings().LIVEKIT_URL),
            "deepgram_configured": bool(get_settings().DEEPGRAM_API_KEY),
            "openai_configured": bool(get_settings().OPENAI_API_KEY),
            "elevenlabs_configured": bool(get_settings().ELEVENLABS_API_KEY),
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
