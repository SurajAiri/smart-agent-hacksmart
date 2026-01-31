"""
Bot Manager - Manages multiple bot instances across rooms

Responsibilities:
- Create and destroy bot instances
- Track active bots per room
- Provide status information
"""
import asyncio
from datetime import datetime
from typing import Dict, Optional
from loguru import logger

from src.bot.agent import VoiceAgent
from src.config.settings import get_settings


class BotInstance:
    """Represents a single bot instance in a room"""
    
    def __init__(self, room_name: str, call_id: str, agent: VoiceAgent):
        self.room_name = room_name
        self.call_id = call_id
        self.agent = agent
        self.joined_at = datetime.now()
        self.state = "joining"
        self._task: Optional[asyncio.Task] = None
    
    def to_dict(self) -> dict:
        return {
            "room_name": self.room_name,
            "call_id": self.call_id,
            "is_active": self.state == "active",
            "state": self.state,
            "joined_at": self.joined_at.isoformat(),
        }


class BotManager:
    """
    Manages all bot instances.
    
    Each room can have one bot at a time.
    """
    
    def __init__(self):
        self.active_bots: Dict[str, BotInstance] = {}
        self._settings = get_settings()
        logger.info("BotManager initialized")
    
    def is_bot_in_room(self, room_name: str) -> bool:
        """Check if a bot is already in the room"""
        return room_name in self.active_bots
    
    async def join_room(
        self,
        room_name: str,
        token: str,
        call_id: str,
        metadata: dict = {},
    ) -> BotInstance:
        """
        Create a new bot and join a room.
        
        Args:
            room_name: LiveKit room name
            token: Access token for the room
            call_id: Unique call identifier
            metadata: Additional metadata
        
        Returns:
            BotInstance for the room
        """
        if self.is_bot_in_room(room_name):
            logger.warning(f"Bot already in room {room_name}")
            return self.active_bots[room_name]
        
        logger.info(f"Creating bot for room: {room_name} (call_id: {call_id})")
        
        # Create voice agent
        agent = VoiceAgent(
            room_name=room_name,
            token=token,
            call_id=call_id,
            livekit_url=self._settings.LIVEKIT_URL,
        )
        
        # Create bot instance
        bot = BotInstance(room_name, call_id, agent)
        self.active_bots[room_name] = bot
        
        # Start the agent in a background task
        bot._task = asyncio.create_task(
            self._run_agent(bot),
            name=f"agent-{room_name}",
        )
        
        return bot
    
    async def _run_agent(self, bot: BotInstance):
        """Run the voice agent in a room"""
        try:
            bot.state = "active"
            logger.info(f"Bot active in room: {bot.room_name}")
            
            # Run the agent (this blocks until the agent stops)
            await bot.agent.run()
            
        except asyncio.CancelledError:
            logger.info(f"Bot task cancelled for room: {bot.room_name}")
        except Exception as e:
            logger.error(f"Bot error in room {bot.room_name}: {e}")
            bot.state = "error"
        finally:
            bot.state = "stopped"
            # Clean up if still in active_bots
            if bot.room_name in self.active_bots:
                del self.active_bots[bot.room_name]
            logger.info(f"Bot removed from room: {bot.room_name}")
    
    async def leave_room(self, room_name: str):
        """
        Stop the bot and leave a room.
        """
        if room_name not in self.active_bots:
            logger.warning(f"No bot in room: {room_name}")
            return
        
        bot = self.active_bots[room_name]
        bot.state = "leaving"
        
        # Stop the agent
        await bot.agent.stop()
        
        # Cancel the task if still running
        if bot._task and not bot._task.done():
            bot._task.cancel()
            try:
                await bot._task
            except asyncio.CancelledError:
                pass
        
        # Clean up
        if room_name in self.active_bots:
            del self.active_bots[room_name]
        
        logger.info(f"Bot left room: {room_name}")
    
    def get_bot_status(self, room_name: str) -> Optional[dict]:
        """Get status of a bot in a room"""
        if room_name not in self.active_bots:
            return None
        return self.active_bots[room_name].to_dict()
    
    def list_active_bots(self) -> list:
        """List all active bots"""
        return [bot.to_dict() for bot in self.active_bots.values()]
    
    async def shutdown(self):
        """Stop all bots on shutdown"""
        logger.info(f"Shutting down {len(self.active_bots)} active bots...")
        
        tasks = []
        for room_name in list(self.active_bots.keys()):
            tasks.append(self.leave_room(room_name))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info("All bots stopped")
