/**
 * Room Routes - Express router for room management endpoints
 */
import { Router } from 'express';
import * as roomController from '../controllers/room.controller.mjs';

const router = Router();

// Room management
router.post('/', roomController.createRoom);
router.get('/', roomController.listRooms);
router.get('/:roomName', roomController.getRoom);
router.delete('/:roomName', roomController.deleteRoom);

// Participant management
router.get('/:roomName/participants', roomController.getParticipants);
router.delete('/:roomName/participants/:identity', roomController.removeParticipant);

// Token generation
router.post('/:roomName/token', roomController.generateToken);

export default router;
