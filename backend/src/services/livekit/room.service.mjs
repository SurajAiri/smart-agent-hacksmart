/**
 * Room Service - Phase 1: Room Lifecycle Management
 * 
 * Key invariants:
 * - One call → one room (callId === roomName)
 * - Idempotent creation (if room exists, return existing)
 * - Safe teardown (only delete if no participants)
 */
import { v4 as uuidv4 } from 'uuid';
import { getRoomServiceClient, config } from './livekit.client.mjs';
import { ROOM_CONFIG } from '../../utils/constants.mjs';

/**
 * Create a room for a call (idempotent)
 * @param {string} callId - Unique call identifier (becomes room name)
 * @param {object} metadata - Optional room metadata
 * @returns {Promise<object>} Room details
 */
export const createRoom = async (callId, metadata = {}) => {
  if (!config.hasValidConfig) {
    throw new Error('LiveKit configuration is missing');
  }

  const roomName = callId || `call-${uuidv4()}`;
  const roomService = getRoomServiceClient();

  // Check if room already exists (idempotent)
  try {
    const existingRooms = await roomService.listRooms([roomName]);
    if (existingRooms.length > 0) {
      console.log(`[RoomService] Room ${roomName} already exists, returning existing room`);
      return {
        roomName: existingRooms[0].name,
        sid: existingRooms[0].sid,
        numParticipants: existingRooms[0].numParticipants,
        createdAt: new Date(Number(existingRooms[0].creationTime) / 1000000), // Convert from nanoseconds
        metadata: existingRooms[0].metadata,
        isExisting: true,
      };
    }
  } catch (error) {
    // Room doesn't exist, proceed with creation
    console.log(`[RoomService] Room ${roomName} does not exist, creating new room`);
  }

  // Create new room
  const room = await roomService.createRoom({
    name: roomName,
    emptyTimeout: ROOM_CONFIG.EMPTY_TIMEOUT_SECONDS,
    maxParticipants: ROOM_CONFIG.MAX_PARTICIPANTS,
    departureTimeout: ROOM_CONFIG.DEPARTURE_TIMEOUT_SECONDS,
    metadata: JSON.stringify({
      ...metadata,
      callId: roomName,
      createdAt: new Date().toISOString(),
    }),
  });

  console.log(`[RoomService] Created room: ${room.name} (sid: ${room.sid})`);

  return {
    roomName: room.name,
    sid: room.sid,
    numParticipants: room.numParticipants,
    createdAt: new Date(),
    metadata: room.metadata,
    isExisting: false,
  };
};

/**
 * Get room details by name
 * @param {string} roomName - Room name to look up
 * @returns {Promise<object|null>} Room details or null if not found
 */
export const getRoom = async (roomName) => {
  if (!config.hasValidConfig) {
    throw new Error('LiveKit configuration is missing');
  }

  const roomService = getRoomServiceClient();

  try {
    const rooms = await roomService.listRooms([roomName]);
    if (rooms.length === 0) {
      return null;
    }

    const room = rooms[0];
    return {
      roomName: room.name,
      sid: room.sid,
      numParticipants: room.numParticipants,
      maxParticipants: room.maxParticipants,
      createdAt: new Date(Number(room.creationTime) / 1000000),
      metadata: room.metadata ? JSON.parse(room.metadata) : {},
    };
  } catch (error) {
    console.error(`[RoomService] Error getting room ${roomName}:`, error.message);
    throw error;
  }
};

/**
 * List all active rooms
 * @returns {Promise<Array>} List of active rooms
 */
export const listRooms = async () => {
  if (!config.hasValidConfig) {
    throw new Error('LiveKit configuration is missing');
  }

  const roomService = getRoomServiceClient();

  try {
    const rooms = await roomService.listRooms();
    return rooms.map(room => ({
      roomName: room.name,
      sid: room.sid,
      numParticipants: room.numParticipants,
      maxParticipants: room.maxParticipants,
      createdAt: new Date(Number(room.creationTime) / 1000000),
      metadata: room.metadata ? JSON.parse(room.metadata) : {},
    }));
  } catch (error) {
    console.error('[RoomService] Error listing rooms:', error.message);
    throw error;
  }
};

/**
 * Delete a room (safe teardown)
 * Only deletes if room has no participants, unless force=true
 * @param {string} roomName - Room name to delete
 * @param {boolean} force - Force delete even if participants present
 * @returns {Promise<object>} Deletion result
 */
export const deleteRoom = async (roomName, force = false) => {
  if (!config.hasValidConfig) {
    throw new Error('LiveKit configuration is missing');
  }

  const roomService = getRoomServiceClient();

  // Check if room exists and has participants
  const room = await getRoom(roomName);
  if (!room) {
    return { success: false, reason: 'Room not found' };
  }

  if (room.numParticipants > 0 && !force) {
    console.warn(`[RoomService] Cannot delete room ${roomName}: has ${room.numParticipants} participants`);
    return {
      success: false,
      reason: `Room has ${room.numParticipants} active participants`,
      numParticipants: room.numParticipants,
    };
  }

  try {
    await roomService.deleteRoom(roomName);
    console.log(`[RoomService] Deleted room: ${roomName}`);
    return { success: true, roomName };
  } catch (error) {
    console.error(`[RoomService] Error deleting room ${roomName}:`, error.message);
    throw error;
  }
};

/**
 * Get participants in a room
 * @param {string} roomName - Room name
 * @returns {Promise<Array>} List of participants
 */
export const getParticipants = async (roomName) => {
  if (!config.hasValidConfig) {
    throw new Error('LiveKit configuration is missing');
  }

  const roomService = getRoomServiceClient();

  try {
    const participants = await roomService.listParticipants(roomName);
    return participants.map(p => ({
      identity: p.identity,
      sid: p.sid,
      state: p.state,
      joinedAt: new Date(Number(p.joinedAt) / 1000000),
      metadata: p.metadata ? JSON.parse(p.metadata) : {},
      tracks: p.tracks?.length || 0,
      isPublisher: p.permission?.canPublish || false,
    }));
  } catch (error) {
    console.error(`[RoomService] Error getting participants for room ${roomName}:`, error.message);
    throw error;
  }
};

/**
 * Remove a participant from a room
 * @param {string} roomName - Room name
 * @param {string} identity - Participant identity to remove
 * @returns {Promise<object>} Removal result
 */
export const removeParticipant = async (roomName, identity) => {
  if (!config.hasValidConfig) {
    throw new Error('LiveKit configuration is missing');
  }

  const roomService = getRoomServiceClient();

  try {
    await roomService.removeParticipant(roomName, identity);
    console.log(`[RoomService] Removed participant ${identity} from room ${roomName}`);
    return { success: true, roomName, identity };
  } catch (error) {
    console.error(`[RoomService] Error removing participant ${identity} from room ${roomName}:`, error.message);
    throw error;
  }
};
