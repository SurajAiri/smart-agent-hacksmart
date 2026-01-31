/**
 * Participant Service - Phase 3: Participant Lifecycle Management
 * 
 * Key invariants:
 * - Driver controls call lifetime (call ends when driver leaves)
 * - Bot does not start/end calls
 * - Role resolution from identity and metadata
 */
import { getRoomServiceClient } from './livekit.client.mjs';
import { callEvents } from './call-event.service.mjs';
import * as tokenService from './token.service.mjs';
import { PARTICIPANT_ROLES, CALL_EVENTS } from '../../utils/constants.mjs';

/**
 * Add a participant to a room by generating their access token
 * @param {string} roomName - Room name
 * @param {string} participantId - Participant identity
 * @param {string} role - Participant role
 * @param {object} metadata - Additional metadata
 * @returns {Promise<object>} Token and connection info
 */
export const addParticipant = async (roomName, participantId, role, metadata = {}) => {
  console.log(`[ParticipantService] Adding ${role} participant: ${participantId} to room ${roomName}`);

  const token = await tokenService.generateToken({
    roomName,
    participantId,
    role,
    metadata,
  });

  return {
    token,
    roomName,
    participantId,
    role,
    livekitUrl: process.env.LIVEKIT_URL,
  };
};

/**
 * Remove a participant from a room
 * @param {string} roomName - Room name
 * @param {string} participantId - Participant identity
 * @returns {Promise<object>} Removal result
 */
export const removeParticipant = async (roomName, participantId) => {
  console.log(`[ParticipantService] Removing participant: ${participantId} from room ${roomName}`);

  const roomService = getRoomServiceClient();

  try {
    await roomService.removeParticipant(roomName, participantId);
    return { success: true, roomName, participantId };
  } catch (error) {
    console.error(`[ParticipantService] Error removing participant:`, error.message);
    throw error;
  }
};

/**
 * Get all participants in a room with role information
 * @param {string} roomName - Room name
 * @returns {Promise<Array>} Participants with roles
 */
export const getParticipants = async (roomName) => {
  const roomService = getRoomServiceClient();

  try {
    const participants = await roomService.listParticipants(roomName);

    return participants.map(p => ({
      identity: p.identity,
      sid: p.sid,
      name: p.name,
      role: resolveRole(p.identity, p.metadata),
      state: p.state,
      joinedAt: new Date(Number(p.joinedAt) / 1000000),
      audioTracks: countTracks(p.tracks, 'audio'),
      videoTracks: countTracks(p.tracks, 'video'),
      isSpeaking: p.isSpeaking,
      metadata: parseMetadata(p.metadata),
    }));
  } catch (error) {
    console.error(`[ParticipantService] Error getting participants:`, error.message);
    throw error;
  }
};

/**
 * Get a specific participant by identity
 * @param {string} roomName - Room name
 * @param {string} participantId - Participant identity
 * @returns {Promise<object|null>} Participant info or null
 */
export const getParticipant = async (roomName, participantId) => {
  const participants = await getParticipants(roomName);
  return participants.find(p => p.identity === participantId) || null;
};

/**
 * Check if the driver is present in the room
 * @param {string} roomName - Room name
 * @returns {Promise<boolean>}
 */
export const isDriverPresent = async (roomName) => {
  const participants = await getParticipants(roomName);
  return participants.some(p => p.role === PARTICIPANT_ROLES.DRIVER);
};

/**
 * Check if the AI bot is present in the room
 * @param {string} roomName - Room name
 * @returns {Promise<boolean>}
 */
export const isBotPresent = async (roomName) => {
  const participants = await getParticipants(roomName);
  return participants.some(p => p.role === PARTICIPANT_ROLES.AI_BOT);
};

/**
 * Check if a human agent is present in the room
 * @param {string} roomName - Room name
 * @returns {Promise<boolean>}
 */
export const isHumanAgentPresent = async (roomName) => {
  const participants = await getParticipants(roomName);
  return participants.some(p => p.role === PARTICIPANT_ROLES.HUMAN_AGENT);
};

/**
 * Update participant metadata
 * @param {string} roomName - Room name
 * @param {string} participantId - Participant identity
 * @param {object} metadata - New metadata to set
 * @returns {Promise<object>} Updated participant
 */
export const updateParticipantMetadata = async (roomName, participantId, metadata) => {
  const roomService = getRoomServiceClient();

  try {
    await roomService.updateParticipant(roomName, participantId, {
      metadata: JSON.stringify(metadata),
    });

    console.log(`[ParticipantService] Updated metadata for ${participantId}`);
    return { success: true, participantId, metadata };
  } catch (error) {
    console.error(`[ParticipantService] Error updating metadata:`, error.message);
    throw error;
  }
};

/**
 * Mute/unmute a participant's track
 * @param {string} roomName - Room name
 * @param {string} participantId - Participant identity
 * @param {string} trackSid - Track SID to mute
 * @param {boolean} muted - Whether to mute
 */
export const muteTrack = async (roomName, participantId, trackSid, muted) => {
  const roomService = getRoomServiceClient();

  try {
    await roomService.mutePublishedTrack(roomName, participantId, trackSid, muted);
    console.log(`[ParticipantService] ${muted ? 'Muted' : 'Unmuted'} track ${trackSid} for ${participantId}`);
    return { success: true, participantId, trackSid, muted };
  } catch (error) {
    console.error(`[ParticipantService] Error muting track:`, error.message);
    throw error;
  }
};

// ============ Helper Functions ============

/**
 * Resolve participant role from identity and metadata
 */
function resolveRole(identity, metadata) {
  // Try metadata first
  const parsed = parseMetadata(metadata);
  if (parsed.role && Object.values(PARTICIPANT_ROLES).includes(parsed.role)) {
    return parsed.role;
  }

  // Fall back to identity-based resolution
  const lowerIdentity = (identity || '').toLowerCase();

  if (lowerIdentity.includes('bot') || lowerIdentity.includes('ai')) {
    return PARTICIPANT_ROLES.AI_BOT;
  }

  if (lowerIdentity.includes('agent') || lowerIdentity.includes('support')) {
    return PARTICIPANT_ROLES.HUMAN_AGENT;
  }

  return PARTICIPANT_ROLES.DRIVER;
}

/**
 * Parse metadata JSON safely
 */
function parseMetadata(metadata) {
  if (!metadata) return {};
  try {
    return JSON.parse(metadata);
  } catch {
    return {};
  }
}

/**
 * Count tracks of a specific type
 */
function countTracks(tracks, type) {
  if (!tracks) return 0;
  return tracks.filter(t => t.type === type || t.source?.toLowerCase().includes(type)).length;
}

// ============ Event Listeners ============

// React to participant events
callEvents.on(CALL_EVENTS.PARTICIPANT_LEFT, async ({ roomName, participant }) => {
  // Check if the driver left - this may trigger call end
  if (participant.role === PARTICIPANT_ROLES.DRIVER || 
      participant.identity?.toLowerCase().includes('driver')) {
    console.log(`[ParticipantService] Driver left room ${roomName} - call may end`);
    // The room will automatically close based on empty_timeout configuration
  }
});
