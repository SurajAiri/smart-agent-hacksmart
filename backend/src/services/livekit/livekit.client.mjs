/**
 * LiveKit Client Configuration
 * Centralized SDK client instances for Room, Egress, and Ingress services
 */
import { RoomServiceClient, EgressClient, AccessToken } from 'livekit-server-sdk';

// LiveKit configuration from environment
const LIVEKIT_URL = process.env.LIVEKIT_URL;
const LIVEKIT_API_KEY = process.env.LIVEKIT_API_KEY;
const LIVEKIT_API_SECRET = process.env.LIVEKIT_API_SECRET;

// Validate configuration
if (!LIVEKIT_URL || !LIVEKIT_API_KEY || !LIVEKIT_API_SECRET) {
  console.error('Missing LiveKit configuration. Please set LIVEKIT_URL, LIVEKIT_API_KEY, and LIVEKIT_API_SECRET environment variables.');
}

// Convert WebSocket URL to HTTP URL for API calls
const getHttpUrl = (wsUrl) => {
  if (!wsUrl) return '';
  return wsUrl.replace('wss://', 'https://').replace('ws://', 'http://');
};

const LIVEKIT_HTTP_URL = getHttpUrl(LIVEKIT_URL);

/**
 * Room Service Client - for room management operations
 * Singleton instance
 */
let roomServiceClient = null;

export const getRoomServiceClient = () => {
  if (!roomServiceClient) {
    roomServiceClient = new RoomServiceClient(
      LIVEKIT_HTTP_URL,
      LIVEKIT_API_KEY,
      LIVEKIT_API_SECRET
    );
  }
  return roomServiceClient;
};

/**
 * Egress Client - for recording and streaming operations
 * Singleton instance
 */
let egressClient = null;

export const getEgressClient = () => {
  if (!egressClient) {
    egressClient = new EgressClient(
      LIVEKIT_HTTP_URL,
      LIVEKIT_API_KEY,
      LIVEKIT_API_SECRET
    );
  }
  return egressClient;
};

/**
 * Generate Access Token for participants
 * @param {string} roomName - The room to grant access to
 * @param {string} participantIdentity - Unique identifier for the participant
 * @param {object} options - Token options
 * @param {boolean} options.canPublish - Can publish tracks
 * @param {boolean} options.canSubscribe - Can subscribe to tracks
 * @param {boolean} options.canPublishData - Can publish data messages
 * @param {number} options.ttl - Token time-to-live in seconds
 * @param {object} options.metadata - Participant metadata
 * @returns {Promise<string>} JWT token string
 */
export const generateAccessToken = async (roomName, participantIdentity, options = {}) => {
  const {
    canPublish = true,
    canSubscribe = true,
    canPublishData = true,
    ttl = 3600, // 1 hour default
    metadata = {},
  } = options;

  const token = new AccessToken(LIVEKIT_API_KEY, LIVEKIT_API_SECRET, {
    identity: participantIdentity,
    ttl,
    metadata: JSON.stringify(metadata),
  });

  token.addGrant({
    room: roomName,
    roomJoin: true,
    canPublish,
    canSubscribe,
    canPublishData,
  });

  return await token.toJwt();
};

// Export configuration for use in other modules
export const config = {
  url: LIVEKIT_URL,
  httpUrl: LIVEKIT_HTTP_URL,
  apiKey: LIVEKIT_API_KEY,
  hasValidConfig: !!(LIVEKIT_URL && LIVEKIT_API_KEY && LIVEKIT_API_SECRET),
};
