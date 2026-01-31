/**
 * AI Agent Controller - REST API for AI bot management
 */
import * as spawnerService from '../services/ai-agent/spawner.service.mjs';
import * as roomService from '../services/livekit/room.service.mjs';
import { generateAccessToken } from '../services/livekit/livekit.client.mjs';
import { PARTICIPANT_ROLES } from '../utils/constants.mjs';
import CallSession from '../models/call-session.model.mjs';

/**
 * Spawn AI bot to join a room
 * POST /api/ai-agent/spawn
 */
export const spawnBot = async (req, res) => {
  try {
    const { roomName, callId } = req.body;
    
    if (!roomName) {
      return res.sendResponse(400, { error: 'roomName is required' });
    }
    
    // Generate token for the bot
    const botIdentity = `ai-bot-${roomName}`;
    const token = await generateAccessToken(roomName, botIdentity, {
      canPublish: true,
      canSubscribe: true,
      canPublishData: true,
      metadata: {
        role: PARTICIPANT_ROLES.AI_BOT,
      },
    });
    
    // Spawn the bot
    const result = await spawnerService.spawnBot(
      roomName,
      token,
      callId || roomName,
      { spawnedBy: 'backend' }
    );
    
    res.sendResponse(200, result);
    
  } catch (error) {
    console.error('[AIAgentController] Spawn bot error:', error);
    res.sendResponse(500, { error: error.message });
  }
};

/**
 * Stop AI bot and leave room
 * POST /api/ai-agent/stop
 */
export const stopBot = async (req, res) => {
  try {
    const { roomName } = req.body;
    
    if (!roomName) {
      return res.sendResponse(400, { error: 'roomName is required' });
    }
    
    const result = await spawnerService.stopBot(roomName);
    res.sendResponse(200, result);
    
  } catch (error) {
    console.error('[AIAgentController] Stop bot error:', error);
    res.sendResponse(500, { error: error.message });
  }
};

/**
 * Get bot status for a room
 * GET /api/ai-agent/status/:roomName
 */
export const getStatus = async (req, res) => {
  try {
    const { roomName } = req.params;
    const status = await spawnerService.getBotStatus(roomName);
    res.sendResponse(200, status);
    
  } catch (error) {
    console.error('[AIAgentController] Get status error:', error);
    res.sendResponse(500, { error: error.message });
  }
};

/**
 * List all active bots
 * GET /api/ai-agent/list
 */
export const listBots = async (req, res) => {
  try {
    const result = await spawnerService.listBots();
    res.sendResponse(200, result);
    
  } catch (error) {
    console.error('[AIAgentController] List bots error:', error);
    res.sendResponse(500, { error: error.message });
  }
};

/**
 * Receive events from Python AI Agent
 * POST /api/ai-agent/events
 */
export const receiveEvent = async (req, res) => {
  try {
    const { event, call_id, ...data } = req.body;
    
    console.log(`[AIAgentController] Received event: ${event} for call: ${call_id}`);
    
    // Handle different event types
    switch (event) {
      case 'transcript':
        await handleTranscriptEvent(call_id, data);
        break;
        
      case 'turn_state':
        await handleTurnStateEvent(call_id, data);
        break;
        
      case 'handoff_request':
        await handleHandoffRequest(call_id, data);
        break;
        
      case 'error':
        console.error(`[AIAgentController] Bot error for ${call_id}:`, data.error);
        break;
        
      case 'bot_ready':
        console.log(`[AIAgentController] Bot ready for call: ${call_id}`);
        break;
        
      default:
        console.log(`[AIAgentController] Unknown event: ${event}`);
    }
    
    res.sendResponse(200, { received: true, event });
    
  } catch (error) {
    console.error('[AIAgentController] Event handler error:', error);
    res.sendResponse(500, { error: error.message });
  }
};

/**
 * Handle transcript events
 */
async function handleTranscriptEvent(callId, data) {
  const { speaker, text, confidence } = data;
  console.log(`[Transcript] ${speaker}: ${text}`);
  
  // TODO: Store transcript in MongoDB
  // const session = await CallSession.findOne({ callId });
  // if (session) {
  //   session.transcripts.push({ speaker, text, confidence, timestamp: new Date() });
  //   await session.save();
  // }
}

/**
 * Handle turn state changes
 */
async function handleTurnStateEvent(callId, data) {
  const { state } = data;
  console.log(`[TurnState] Call ${callId}: ${state}`);
  // TODO: Emit to frontend via WebSocket/SSE
}

/**
 * Handle handoff requests
 */
async function handleHandoffRequest(callId, data) {
  const { reason } = data;
  console.log(`[Handoff] Call ${callId} requested handoff: ${reason}`);
  // TODO: Notify human agent queue
}

/**
 * Health check for AI Agent service
 * GET /api/ai-agent/health
 */
export const healthCheck = async (req, res) => {
  try {
    const health = await spawnerService.healthCheck();
    res.sendResponse(200, health);
    
  } catch (error) {
    res.sendResponse(500, { status: 'unhealthy', error: error.message });
  }
};
