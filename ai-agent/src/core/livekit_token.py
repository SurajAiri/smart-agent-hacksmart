"""
LiveKit Token Generator for Human Agent Handoff

Generates access tokens for human agents to join LiveKit rooms
when accepting a handoff from the AI agent.
"""
import time
import jwt
from typing import Optional
from loguru import logger

from src.config.settings import get_settings


def generate_agent_token(
    room_name: str,
    agent_id: str,
    agent_name: Optional[str] = None,
    ttl_seconds: int = 3600,  # 1 hour default
) -> str:
    """
    Generate a LiveKit access token for a human agent.
    
    Args:
        room_name: The LiveKit room to join
        agent_id: Unique identifier for the agent
        agent_name: Display name for the agent (optional)
        ttl_seconds: Token time-to-live in seconds
        
    Returns:
        JWT token string
    """
    settings = get_settings()
    
    now = int(time.time())
    exp = now + ttl_seconds
    
    # Build the token claims
    claims = {
        "iss": settings.LIVEKIT_API_KEY,
        "sub": agent_id,
        "iat": now,
        "nbf": now,
        "exp": exp,
        "name": agent_name or f"Agent {agent_id}",
        "video": {
            "room": room_name,
            "roomJoin": True,
            "canPublish": True,
            "canSubscribe": True,
            "canPublishData": True,
        },
        "metadata": f'{{"role": "human_agent", "agent_id": "{agent_id}"}}',
    }
    
    # Sign the token
    token = jwt.encode(
        claims,
        settings.LIVEKIT_API_SECRET,
        algorithm="HS256",
    )
    
    logger.info(f"Generated LiveKit token for agent {agent_id} to join room {room_name}")
    
    return token


def get_livekit_url() -> str:
    """Get the LiveKit WebSocket URL."""
    settings = get_settings()
    return settings.LIVEKIT_URL
