/**
 * Call Event Service - Phase 2: Call Observability
 * 
 * Handles call lifecycle events and provides internal event propagation
 */
import { EventEmitter } from 'events';
import CallSession from '../../models/call-session.model.mjs';
import { CALL_EVENTS, CALL_STATUS, PARTICIPANT_ROLES } from '../../utils/constants.mjs';

// Internal event emitter for cross-service communication
class CallEventEmitter extends EventEmitter {
  constructor() {
    super();
    this.setMaxListeners(20);
  }
}

export const callEvents = new CallEventEmitter();

/**
 * Create a new call session
 * @param {string} callId - Unique call identifier
 * @param {string} roomName - LiveKit room name
 * @param {string} roomSid - LiveKit room SID
 * @param {object} metadata - Additional metadata
 * @returns {Promise<CallSession>}
 */
export const createCallSession = async (callId, roomName, roomSid, metadata = {}) => {
  try {
    // Check if session already exists (idempotent)
    let session = await CallSession.findOne({ callId });
    if (session) {
      console.log(`[CallEventService] Call session ${callId} already exists`);
      return session;
    }

    session = new CallSession({
      callId,
      roomName,
      roomSid,
      status: CALL_STATUS.CREATED,
      metadata,
    });

    await session.logEvent(CALL_EVENTS.CALL_CREATED, { roomName, roomSid });
    
    console.log(`[CallEventService] Created call session: ${callId}`);
    
    // Emit event for other services
    callEvents.emit(CALL_EVENTS.CALL_CREATED, {
      callId,
      roomName,
      roomSid,
      session,
    });

    return session;
  } catch (error) {
    console.error('[CallEventService] Error creating call session:', error);
    throw error;
  }
};

/**
 * Handle room started event from LiveKit webhook
 * @param {object} roomData - Room data from webhook
 */
export const handleRoomStarted = async (roomData) => {
  const { name: roomName, sid: roomSid } = roomData;
  
  console.log(`[CallEventService] Room started: ${roomName}`);

  try {
    // Find or create session
    let session = await CallSession.findActiveByRoom(roomName);
    
    if (!session) {
      // Create a new session if one doesn't exist
      session = await createCallSession(roomName, roomName, roomSid);
    } else {
      // Update existing session
      session.roomSid = roomSid;
      session.status = CALL_STATUS.ACTIVE;
      session.startedAt = new Date();
      await session.logEvent(CALL_EVENTS.CALL_ACTIVE, { roomSid });
    }

    callEvents.emit(CALL_EVENTS.CALL_ACTIVE, {
      callId: session.callId,
      roomName,
      roomSid,
    });

    return session;
  } catch (error) {
    console.error('[CallEventService] Error handling room started:', error);
    throw error;
  }
};

/**
 * Handle room finished event from LiveKit webhook
 * @param {object} roomData - Room data from webhook
 */
export const handleRoomFinished = async (roomData) => {
  const { name: roomName, sid: roomSid } = roomData;
  
  console.log(`[CallEventService] Room finished: ${roomName}`);

  try {
    const session = await CallSession.findActiveByRoom(roomName);
    
    if (!session) {
      console.warn(`[CallEventService] No active session found for room: ${roomName}`);
      return null;
    }

    session.status = CALL_STATUS.ENDED;
    session.endedAt = new Date();
    
    // Calculate duration
    if (session.startedAt) {
      session.duration = Math.floor((session.endedAt - session.startedAt) / 1000);
    }

    await session.logEvent(CALL_EVENTS.CALL_ENDED, {
      roomSid,
      duration: session.duration,
    });

    callEvents.emit(CALL_EVENTS.CALL_ENDED, {
      callId: session.callId,
      roomName,
      roomSid,
      duration: session.duration,
    });

    return session;
  } catch (error) {
    console.error('[CallEventService] Error handling room finished:', error);
    throw error;
  }
};

/**
 * Handle participant joined event from LiveKit webhook
 * @param {object} participantData - Participant data from webhook
 * @param {object} roomData - Room data from webhook
 */
export const handleParticipantJoined = async (participantData, roomData) => {
  const { identity, sid, metadata } = participantData;
  const { name: roomName } = roomData;

  console.log(`[CallEventService] Participant joined: ${identity} in room ${roomName}`);

  try {
    const session = await CallSession.findActiveByRoom(roomName);
    
    if (!session) {
      console.warn(`[CallEventService] No active session found for room: ${roomName}`);
      return null;
    }

    // Parse role from metadata or identity
    const role = resolveParticipantRole(identity, metadata);

    // Update session status to active if this is the first participant
    if (session.status === CALL_STATUS.CREATED) {
      session.status = CALL_STATUS.ACTIVE;
      session.startedAt = new Date();
    }

    await session.addParticipant(identity, role, { sid });
    await session.logEvent(CALL_EVENTS.PARTICIPANT_JOINED, {
      identity,
      role,
      sid,
    });

    callEvents.emit(CALL_EVENTS.PARTICIPANT_JOINED, {
      callId: session.callId,
      roomName,
      participant: { identity, role, sid },
    });

    return session;
  } catch (error) {
    console.error('[CallEventService] Error handling participant joined:', error);
    throw error;
  }
};

/**
 * Handle participant left event from LiveKit webhook
 * @param {object} participantData - Participant data from webhook
 * @param {object} roomData - Room data from webhook
 */
export const handleParticipantLeft = async (participantData, roomData) => {
  const { identity, sid } = participantData;
  const { name: roomName } = roomData;

  console.log(`[CallEventService] Participant left: ${identity} from room ${roomName}`);

  try {
    const session = await CallSession.findActiveByRoom(roomName);
    
    if (!session) {
      console.warn(`[CallEventService] No active session found for room: ${roomName}`);
      return null;
    }

    await session.removeParticipant(identity);
    await session.logEvent(CALL_EVENTS.PARTICIPANT_LEFT, {
      identity,
      sid,
    });

    callEvents.emit(CALL_EVENTS.PARTICIPANT_LEFT, {
      callId: session.callId,
      roomName,
      participant: { identity, sid },
    });

    return session;
  } catch (error) {
    console.error('[CallEventService] Error handling participant left:', error);
    throw error;
  }
};

/**
 * Resolve participant role from identity and metadata
 * @param {string} identity - Participant identity
 * @param {string} metadata - JSON metadata string
 * @returns {string} Participant role
 */
const resolveParticipantRole = (identity, metadata) => {
  // Try to parse role from metadata first
  if (metadata) {
    try {
      const parsed = JSON.parse(metadata);
      if (parsed.role && Object.values(PARTICIPANT_ROLES).includes(parsed.role)) {
        return parsed.role;
      }
    } catch (e) {
      // Metadata is not valid JSON, continue with identity-based resolution
    }
  }

  // Resolve from identity pattern
  const lowerIdentity = identity.toLowerCase();
  
  if (lowerIdentity.includes('bot') || lowerIdentity.includes('ai')) {
    return PARTICIPANT_ROLES.AI_BOT;
  }
  
  if (lowerIdentity.includes('agent') || lowerIdentity.includes('support')) {
    return PARTICIPANT_ROLES.HUMAN_AGENT;
  }

  // Default to driver
  return PARTICIPANT_ROLES.DRIVER;
};

/**
 * Get call session by ID
 * @param {string} callId - Call ID
 * @returns {Promise<CallSession>}
 */
export const getCallSession = async (callId) => {
  return CallSession.findOne({ callId });
};

/**
 * Get active call sessions
 * @returns {Promise<Array<CallSession>>}
 */
export const getActiveCalls = async () => {
  return CallSession.find({
    status: { $in: [CALL_STATUS.CREATED, CALL_STATUS.ACTIVE] },
  }).sort({ createdAt: -1 });
};

/**
 * Get recent call sessions
 * @param {number} limit - Maximum number of calls to return
 * @returns {Promise<Array<CallSession>>}
 */
export const getRecentCalls = async (limit = 50) => {
  return CallSession.find()
    .sort({ createdAt: -1 })
    .limit(limit);
};
