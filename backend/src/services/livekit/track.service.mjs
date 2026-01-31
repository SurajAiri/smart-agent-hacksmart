/**
 * Track Service - Phase 4: Track Management
 * 
 * Key invariants:
 * - Bot subscribes ONLY to driver audio (prevent self-hearing)
 * - Human agent subscribes to both driver and bot
 * - Driver subscribes to bot and human agent
 * - Safe attach/detach of tracks
 */
import { getRoomServiceClient } from './livekit.client.mjs';
import { callEvents } from './call-event.service.mjs';
import { PARTICIPANT_ROLES, CALL_EVENTS } from '../../utils/constants.mjs';

// Track subscriptions state
const trackSubscriptions = new Map(); // roomName -> Map(participantId -> Set(trackSids))

/**
 * Get all tracks published in a room
 * @param {string} roomName - Room name
 * @returns {Promise<Array>} List of tracks with publisher info
 */
export const getTracks = async (roomName) => {
  const roomService = getRoomServiceClient();

  try {
    const participants = await roomService.listParticipants(roomName);
    const tracks = [];

    for (const participant of participants) {
      if (participant.tracks) {
        for (const track of participant.tracks) {
          tracks.push({
            sid: track.sid,
            name: track.name,
            type: track.type, // AUDIO, VIDEO, DATA
            source: track.source, // CAMERA, MICROPHONE, SCREEN_SHARE, etc.
            muted: track.muted,
            width: track.width,
            height: track.height,
            simulcast: track.simulcast,
            publisher: {
              identity: participant.identity,
              sid: participant.sid,
              role: resolveRole(participant.identity, participant.metadata),
            },
          });
        }
      }
    }

    return tracks;
  } catch (error) {
    console.error(`[TrackService] Error getting tracks:`, error.message);
    throw error;
  }
};

/**
 * Get audio tracks only (filtered)
 * @param {string} roomName - Room name
 * @returns {Promise<Array>} Audio tracks
 */
export const getAudioTracks = async (roomName) => {
  const tracks = await getTracks(roomName);
  return tracks.filter(t => 
    t.type === 'AUDIO' || 
    t.source === 'MICROPHONE' || 
    t.source?.toLowerCase().includes('audio')
  );
};

/**
 * Get driver's audio tracks (for bot to subscribe)
 * @param {string} roomName - Room name
 * @returns {Promise<Array>} Driver audio tracks
 */
export const getDriverAudioTracks = async (roomName) => {
  const audioTracks = await getAudioTracks(roomName);
  return audioTracks.filter(t => t.publisher.role === PARTICIPANT_ROLES.DRIVER);
};

/**
 * Get tracks that a participant should subscribe to based on their role
 * This enforces the subscription rules:
 * - Bot: subscribe to driver only (prevent self-hearing)
 * - Human Agent: subscribe to driver and bot
 * - Driver: subscribe to bot and human agent
 * 
 * @param {string} roomName - Room name
 * @param {string} subscriberRole - Role of the subscribing participant
 * @returns {Promise<Array>} Tracks to subscribe to
 */
export const getSubscribableTracks = async (roomName, subscriberRole) => {
  const audioTracks = await getAudioTracks(roomName);

  switch (subscriberRole) {
    case PARTICIPANT_ROLES.AI_BOT:
      // Bot only hears the driver (prevent self-hearing)
      return audioTracks.filter(t => t.publisher.role === PARTICIPANT_ROLES.DRIVER);

    case PARTICIPANT_ROLES.HUMAN_AGENT:
      // Human agent hears everyone except themselves
      return audioTracks.filter(t => t.publisher.role !== PARTICIPANT_ROLES.HUMAN_AGENT);

    case PARTICIPANT_ROLES.DRIVER:
      // Driver hears bot and human agent, not themselves
      return audioTracks.filter(t => t.publisher.role !== PARTICIPANT_ROLES.DRIVER);

    default:
      return audioTracks;
  }
};

/**
 * Check if a track should be subscribed to (self-hearing prevention)
 * @param {string} subscriberIdentity - Who is subscribing
 * @param {string} publisherIdentity - Who published the track
 * @returns {boolean} Whether to subscribe
 */
export const shouldSubscribe = (subscriberIdentity, publisherIdentity) => {
  // Never subscribe to your own tracks
  if (subscriberIdentity === publisherIdentity) {
    return false;
  }

  // Bot should not hear other bots
  const subscriberLower = subscriberIdentity.toLowerCase();
  const publisherLower = publisherIdentity.toLowerCase();

  if (subscriberLower.includes('bot') && publisherLower.includes('bot')) {
    return false;
  }

  return true;
};

/**
 * Mute a track
 * @param {string} roomName - Room name
 * @param {string} participantId - Participant identity
 * @param {string} trackSid - Track SID
 * @returns {Promise<object>}
 */
export const muteTrack = async (roomName, participantId, trackSid) => {
  const roomService = getRoomServiceClient();

  try {
    await roomService.mutePublishedTrack(roomName, participantId, trackSid, true);
    console.log(`[TrackService] Muted track ${trackSid}`);
    return { success: true, trackSid, muted: true };
  } catch (error) {
    console.error(`[TrackService] Error muting track:`, error.message);
    throw error;
  }
};

/**
 * Unmute a track
 * @param {string} roomName - Room name
 * @param {string} participantId - Participant identity
 * @param {string} trackSid - Track SID
 * @returns {Promise<object>}
 */
export const unmuteTrack = async (roomName, participantId, trackSid) => {
  const roomService = getRoomServiceClient();

  try {
    await roomService.mutePublishedTrack(roomName, participantId, trackSid, false);
    console.log(`[TrackService] Unmuted track ${trackSid}`);
    return { success: true, trackSid, muted: false };
  } catch (error) {
    console.error(`[TrackService] Error unmuting track:`, error.message);
    throw error;
  }
};

/**
 * Subscribe to a track (server-side)
 * Note: Actual subscription happens on the client side
 * This tracks intent for monitoring purposes
 */
export const trackSubscription = (roomName, subscriberId, trackSid) => {
  if (!trackSubscriptions.has(roomName)) {
    trackSubscriptions.set(roomName, new Map());
  }

  const roomSubs = trackSubscriptions.get(roomName);
  if (!roomSubs.has(subscriberId)) {
    roomSubs.set(subscriberId, new Set());
  }

  roomSubs.get(subscriberId).add(trackSid);
  console.log(`[TrackService] Tracked subscription: ${subscriberId} -> ${trackSid}`);
};

/**
 * Unsubscribe from a track (server-side tracking)
 */
export const trackUnsubscription = (roomName, subscriberId, trackSid) => {
  const roomSubs = trackSubscriptions.get(roomName);
  if (roomSubs) {
    const subTracks = roomSubs.get(subscriberId);
    if (subTracks) {
      subTracks.delete(trackSid);
    }
  }
  console.log(`[TrackService] Tracked unsubscription: ${subscriberId} -x- ${trackSid}`);
};

/**
 * Get subscription recommendations for a new participant
 * @param {string} roomName - Room name
 * @param {string} participantId - New participant identity
 * @param {string} role - Participant role
 * @returns {Promise<object>} Subscription recommendations
 */
export const getSubscriptionRecommendations = async (roomName, participantId, role) => {
  const subscribableTracks = await getSubscribableTracks(roomName, role);

  return {
    participantId,
    role,
    subscribe: subscribableTracks.map(t => ({
      trackSid: t.sid,
      publisherIdentity: t.publisher.identity,
      type: t.type,
    })),
    avoid: role === PARTICIPANT_ROLES.AI_BOT 
      ? ['self', 'other_bots'] 
      : ['self'],
  };
};

// ============ Helper Functions ============

function resolveRole(identity, metadata) {
  if (metadata) {
    try {
      const parsed = JSON.parse(metadata);
      if (parsed.role) return parsed.role;
    } catch {}
  }

  const lower = (identity || '').toLowerCase();
  if (lower.includes('bot') || lower.includes('ai')) return PARTICIPANT_ROLES.AI_BOT;
  if (lower.includes('agent')) return PARTICIPANT_ROLES.HUMAN_AGENT;
  return PARTICIPANT_ROLES.DRIVER;
}

// ============ Event Cleanup ============

callEvents.on(CALL_EVENTS.CALL_ENDED, ({ roomName }) => {
  trackSubscriptions.delete(roomName);
  console.log(`[TrackService] Cleared subscriptions for room ${roomName}`);
});
