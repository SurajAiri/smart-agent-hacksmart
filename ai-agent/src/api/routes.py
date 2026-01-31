"""
API Routes for AI Agent Control

Endpoints:
- POST /bot/join - Join a LiveKit room
- POST /bot/leave - Leave a room
- GET /bot/status - Get bot status
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from loguru import logger

router = APIRouter()


class JoinRequest(BaseModel):
    """Request to join a room"""
    room_name: str
    token: str
    call_id: str
    metadata: dict = {}


class LeaveRequest(BaseModel):
    """Request to leave a room"""
    room_name: str


class BotStatus(BaseModel):
    """Bot status response"""
    room_name: str
    is_active: bool
    state: str
    joined_at: str | None = None


@router.post("/bot/join")
async def join_room(request: Request, payload: JoinRequest):
    """
    Join a LiveKit room and start the voice pipeline.
    
    Called by Node.js backend when a call starts.
    """
    bot_manager = request.app.state.bot_manager
    
    logger.info(f"Bot join request for room: {payload.room_name}")
    
    # Check if already in room
    if bot_manager.is_bot_in_room(payload.room_name):
        logger.warning(f"Bot already in room: {payload.room_name}")
        return {
            "success": True,
            "message": "Bot already in room",
            "room_name": payload.room_name,
        }
    
    try:
        # Start the bot
        await bot_manager.join_room(
            room_name=payload.room_name,
            token=payload.token,
            call_id=payload.call_id,
            metadata=payload.metadata,
        )
        
        logger.info(f"Bot joined room: {payload.room_name}")
        return {
            "success": True,
            "message": "Bot joined room successfully",
            "room_name": payload.room_name,
        }
        
    except Exception as e:
        logger.error(f"Failed to join room {payload.room_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bot/leave")
async def leave_room(request: Request, payload: LeaveRequest):
    """
    Leave a LiveKit room and stop the voice pipeline.
    
    Called by Node.js backend when a call ends or handoff occurs.
    """
    bot_manager = request.app.state.bot_manager
    
    logger.info(f"Bot leave request for room: {payload.room_name}")
    
    if not bot_manager.is_bot_in_room(payload.room_name):
        logger.warning(f"Bot not in room: {payload.room_name}")
        return {
            "success": True,
            "message": "Bot not in room",
            "room_name": payload.room_name,
        }
    
    try:
        await bot_manager.leave_room(payload.room_name)
        
        logger.info(f"Bot left room: {payload.room_name}")
        return {
            "success": True,
            "message": "Bot left room successfully",
            "room_name": payload.room_name,
        }
        
    except Exception as e:
        logger.error(f"Failed to leave room {payload.room_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bot/status/{room_name}")
async def get_status(request: Request, room_name: str):
    """
    Get bot status for a room.
    """
    bot_manager = request.app.state.bot_manager
    
    status = bot_manager.get_bot_status(room_name)
    
    if not status:
        return {
            "room_name": room_name,
            "is_active": False,
            "state": "not_found",
        }
    
    return status


@router.get("/bot/list")
async def list_bots(request: Request):
    """
    List all active bots.
    """
    bot_manager = request.app.state.bot_manager
    
    return {
        "bots": bot_manager.list_active_bots(),
        "count": len(bot_manager.active_bots),
    }
