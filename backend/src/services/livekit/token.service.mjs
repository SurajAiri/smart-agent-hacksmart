/**
 * Token Service - Phase 3: Access Token Generation
 * 
 * Generates LiveKit access tokens with role-based permissions
 */
import { AccessToken } from 'livekit-server-sdk';
import { PARTICIPANT_ROLES } from '../../utils/constants.mjs';

const LIVEKIT_API_KEY = process.env.LIVEKIT_API_KEY;
const LIVEKIT_API_SECRET = process.env.LIVEKIT_API_SECRET;

/**
 * Permission presets for different participant roles
 */
const ROLE_PERMISSIONS = {
  [PARTICIPANT_ROLES.DRIVER]: {
    canPublish: true,
    canSubscribe: true,
    canPublishData: true,
    canUpdateOwnMetadata: true,
  },
  [PARTICIPANT_ROLES.AI_BOT]: {
    canPublish: true,
    canSubscribe: true,
    canPublishData: true,
    canUpdateOwnMetadata: true,
    // Bot has additional room admin capabilities
    roomAdmin: false,
    roomRecord: true,
  },
  [PARTICIPANT_ROLES.HUMAN_AGENT]: {
    canPublish: true,
    canSubscribe: true,
    canPublishData: true,
    canUpdateOwnMetadata: true,
    // Human agent can manage the room
    roomAdmin: true,
  },
};

/**
 * Generate an access token for a participant
 * @param {object} options - Token options
 * @param {string} options.roomName - Room to grant access to
 * @param {string} options.participantId - Unique participant identifier
 * @param {string} options.role - Participant role (driver/ai_bot/human_agent)
 * @param {object} options.metadata - Additional metadata to include
 * @param {number} options.ttl - Token TTL in seconds (default: 6 hours)
 * @returns {Promise<string>} JWT token
 */
export const generateToken = async ({
  roomName,
  participantId,
  role = PARTICIPANT_ROLES.DRIVER,
  metadata = {},
  ttl = 21600, // 6 hours
}) => {
  if (!LIVEKIT_API_KEY || !LIVEKIT_API_SECRET) {
    throw new Error('LiveKit API credentials not configured');
  }

  if (!roomName || !participantId) {
    throw new Error('roomName and participantId are required');
  }

  // Get permissions for role
  const permissions = ROLE_PERMISSIONS[role] || ROLE_PERMISSIONS[PARTICIPANT_ROLES.DRIVER];

  // Build metadata with role info
  const participantMetadata = {
    role,
    joinedAt: new Date().toISOString(),
    ...metadata,
  };

  const token = new AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET, {
    identity: participantId,
    name: metadata.name || participantId,
    ttl,
    metadata: JSON.stringify(participantMetadata),
  });

  token.addGrant({
    room: roomName,
    roomJoin: true,
    ...permissions,
  });

  const jwt = await token.toJwt();

  console.log(`[TokenService] Generated token for ${participantId} (${role}) in room ${roomName}`);

  return jwt;
};

/**
 * Generate token for driver participant
 */
export const generateDriverToken = async (roomName, driverId, metadata = {}) => {
  return generateToken({
    roomName,
    participantId: driverId,
    role: PARTICIPANT_ROLES.DRIVER,
    metadata: { ...metadata, type: 'driver' },
  });
};

/**
 * Generate token for AI bot participant
 */
export const generateBotToken = async (roomName, botId = 'ai-bot', metadata = {}) => {
  return generateToken({
    roomName,
    participantId: botId,
    role: PARTICIPANT_ROLES.AI_BOT,
    metadata: { ...metadata, type: 'bot' },
  });
};

/**
 * Generate token for human agent participant
 */
export const generateAgentToken = async (roomName, agentId, metadata = {}) => {
  return generateToken({
    roomName,
    participantId: agentId,
    role: PARTICIPANT_ROLES.HUMAN_AGENT,
    metadata: { ...metadata, type: 'human_agent' },
  });
};
