/**
 * Room Controller - REST API endpoints for room management
 */
import * as roomService from '../services/livekit/room.service.mjs';
import { generateAccessToken } from '../services/livekit/livekit.client.mjs';
import { PARTICIPANT_ROLES } from '../utils/constants.mjs';

/**
 * Create a new room
 * POST /api/rooms
 */
export const createRoom = async (req, res) => {
  try {
    const { callId, metadata } = req.body;

    if (!callId) {
      return res.sendResponse(400, { error: 'callId is required' });
    }

    const room = await roomService.createRoom(callId, metadata);

    res.sendResponse(201, {
      room,
      message: room.isExisting ? 'Room already exists' : 'Room created successfully',
    });
  } catch (error) {
    console.error('[RoomController] Create room error:', error);
    res.sendResponse(500, { error: error.message });
  }
};

/**
 * Get room details
 * GET /api/rooms/:roomName
 */
export const getRoom = async (req, res) => {
  try {
    const { roomName } = req.params;

    const room = await roomService.getRoom(roomName);

    if (!room) {
      return res.sendResponse(404, { error: 'Room not found' });
    }

    res.sendResponse(200, { room });
  } catch (error) {
    console.error('[RoomController] Get room error:', error);
    res.sendResponse(500, { error: error.message });
  }
};

/**
 * List all active rooms
 * GET /api/rooms
 */
export const listRooms = async (req, res) => {
  try {
    const rooms = await roomService.listRooms();

    res.sendResponse(200, { rooms, count: rooms.length });
  } catch (error) {
    console.error('[RoomController] List rooms error:', error);
    res.sendResponse(500, { error: error.message });
  }
};

/**
 * Delete a room
 * DELETE /api/rooms/:roomName
 */
export const deleteRoom = async (req, res) => {
  try {
    const { roomName } = req.params;
    const { force } = req.query;

    const result = await roomService.deleteRoom(roomName, force === 'true');

    if (!result.success) {
      return res.sendResponse(400, result);
    }

    res.sendResponse(200, result);
  } catch (error) {
    console.error('[RoomController] Delete room error:', error);
    res.sendResponse(500, { error: error.message });
  }
};

/**
 * Get participants in a room
 * GET /api/rooms/:roomName/participants
 */
export const getParticipants = async (req, res) => {
  try {
    const { roomName } = req.params;

    const participants = await roomService.getParticipants(roomName);

    res.sendResponse(200, { participants, count: participants.length });
  } catch (error) {
    console.error('[RoomController] Get participants error:', error);
    res.sendResponse(500, { error: error.message });
  }
};

/**
 * Remove a participant from a room
 * DELETE /api/rooms/:roomName/participants/:identity
 */
export const removeParticipant = async (req, res) => {
  try {
    const { roomName, identity } = req.params;

    const result = await roomService.removeParticipant(roomName, identity);

    res.sendResponse(200, result);
  } catch (error) {
    console.error('[RoomController] Remove participant error:', error);
    res.sendResponse(500, { error: error.message });
  }
};

/**
 * Generate access token for a participant
 * POST /api/rooms/:roomName/token
 */
export const generateToken = async (req, res) => {
  try {
    const { roomName } = req.params;
    const { participantId, role, metadata } = req.body;

    if (!participantId) {
      return res.sendResponse(400, { error: 'participantId is required' });
    }

    // Validate role
    const validRoles = Object.values(PARTICIPANT_ROLES);
    const participantRole = role || PARTICIPANT_ROLES.DRIVER;

    if (!validRoles.includes(participantRole)) {
      return res.sendResponse(400, {
        error: `Invalid role. Must be one of: ${validRoles.join(', ')}`,
      });
    }

    // Set permissions based on role
    const permissions = {
      canPublish: true,
      canSubscribe: true,
      canPublishData: true,
      metadata: {
        role: participantRole,
        ...metadata,
      },
    };

    const token = await generateAccessToken(roomName, participantId, permissions);

    res.sendResponse(200, {
      token,
      roomName,
      participantId,
      role: participantRole,
    });
  } catch (error) {
    console.error('[RoomController] Generate token error:', error);
    res.sendResponse(500, { error: error.message });
  }
};
