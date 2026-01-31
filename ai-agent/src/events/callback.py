"""
Event Callback - Send events back to Node.js backend

Responsibilities:
- Emit transcript updates
- Emit turn state changes
- Emit handoff requests
- Emit errors
"""
import httpx
from loguru import logger
from src.config.settings import get_settings


class EventCallback:
    """
    Sends events to the Node.js backend for logging and real-time updates.
    """
    
    def __init__(self, call_id: str):
        self.call_id = call_id
        self._settings = get_settings()
        self._client = httpx.AsyncClient(timeout=5.0)
    
    async def _emit(self, event_type: str, data: dict):
        """Send an event to the backend"""
        url = f"{self._settings.BACKEND_URL}/api/ai-agent/events"
        
        payload = {
            "event": event_type,
            "call_id": self.call_id,
            **data,
        }
        
        try:
            response = await self._client.post(url, json=payload)
            if response.status_code != 200:
                logger.warning(f"Event callback failed: {response.status_code}")
        except httpx.RequestError as e:
            logger.warning(f"Event callback error: {e}")
    
    async def emit_transcript(self, speaker: str, text: str, confidence: float = 1.0):
        """Emit a transcript entry"""
        await self._emit("transcript", {
            "speaker": speaker,
            "text": text,
            "confidence": confidence,
        })
    
    async def emit_turn_state(self, state: str):
        """
        Emit turn state change.
        
        States: 'listening', 'processing', 'speaking'
        """
        await self._emit("turn_state", {
            "state": state,
        })
    
    async def emit_participant_joined(self, identity: str):
        """Emit when a participant joins"""
        await self._emit("participant_joined", {
            "identity": identity,
        })
    
    async def emit_participant_left(self, identity: str):
        """Emit when a participant leaves"""
        await self._emit("participant_left", {
            "identity": identity,
        })
    
    async def emit_handoff_request(self, reason: str):
        """Emit handoff request to human agent"""
        await self._emit("handoff_request", {
            "reason": reason,
        })
        logger.info(f"Handoff requested: {reason}")
    
    async def emit_error(self, error: str):
        """Emit error event"""
        await self._emit("error", {
            "error": error,
        })
        logger.error(f"Error emitted: {error}")
    
    async def emit_bot_ready(self):
        """Emit when bot is ready to handle calls"""
        await self._emit("bot_ready", {})
    
    async def close(self):
        """Close the HTTP client"""
        await self._client.aclose()
