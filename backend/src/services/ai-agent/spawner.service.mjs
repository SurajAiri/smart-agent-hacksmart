/**
 * AI Agent Service - Spawn and manage Python AI Agent
 * 
 * Responsibilities:
 * - HTTP calls to Python agent to join/leave rooms
 * - Track bot status per room
 */

const AI_AGENT_URL = process.env.AI_AGENT_URL || 'http://localhost:8000';

/**
 * Spawn the AI bot to join a LiveKit room
 * @param {string} roomName - Room name
 * @param {string} token - Access token for the bot
 * @param {string} callId - Unique call identifier
 * @param {object} metadata - Additional metadata
 * @returns {Promise<object>} Result of the join operation
 */
export const spawnBot = async (roomName, token, callId, metadata = {}) => {
  console.log(`[AIAgentService] Spawning bot for room: ${roomName}`);
  
  try {
    const response = await fetch(`${AI_AGENT_URL}/api/bot/join`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        room_name: roomName,
        token,
        call_id: callId,
        metadata,
      }),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to spawn bot');
    }
    
    const result = await response.json();
    console.log(`[AIAgentService] Bot spawn result:`, result);
    return result;
    
  } catch (error) {
    console.error(`[AIAgentService] Error spawning bot:`, error);
    throw error;
  }
};

/**
 * Stop the AI bot and leave a room
 * @param {string} roomName - Room name
 * @returns {Promise<object>} Result of the leave operation
 */
export const stopBot = async (roomName) => {
  console.log(`[AIAgentService] Stopping bot for room: ${roomName}`);
  
  try {
    const response = await fetch(`${AI_AGENT_URL}/api/bot/leave`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        room_name: roomName,
      }),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to stop bot');
    }
    
    const result = await response.json();
    console.log(`[AIAgentService] Bot stop result:`, result);
    return result;
    
  } catch (error) {
    console.error(`[AIAgentService] Error stopping bot:`, error);
    throw error;
  }
};

/**
 * Get bot status for a room
 * @param {string} roomName - Room name
 * @returns {Promise<object>} Bot status
 */
export const getBotStatus = async (roomName) => {
  try {
    const response = await fetch(`${AI_AGENT_URL}/api/bot/status/${roomName}`);
    
    if (!response.ok) {
      return { is_active: false, state: 'unknown' };
    }
    
    return await response.json();
    
  } catch (error) {
    console.error(`[AIAgentService] Error getting bot status:`, error);
    return { is_active: false, state: 'error', error: error.message };
  }
};

/**
 * List all active bots
 * @returns {Promise<object>} List of active bots
 */
export const listBots = async () => {
  try {
    const response = await fetch(`${AI_AGENT_URL}/api/bot/list`);
    
    if (!response.ok) {
      return { bots: [], count: 0 };
    }
    
    return await response.json();
    
  } catch (error) {
    console.error(`[AIAgentService] Error listing bots:`, error);
    return { bots: [], count: 0, error: error.message };
  }
};

/**
 * Health check for AI Agent service
 * @returns {Promise<object>} Health status
 */
export const healthCheck = async () => {
  try {
    const response = await fetch(`${AI_AGENT_URL}/health`);
    return await response.json();
  } catch (error) {
    return { status: 'unhealthy', error: error.message };
  }
};
