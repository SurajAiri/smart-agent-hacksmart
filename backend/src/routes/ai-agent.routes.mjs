/**
 * AI Agent Routes
 */
import { Router } from 'express';
import * as aiAgentController from '../controllers/ai-agent.controller.mjs';

const router = Router();

// Spawn AI bot to join a room
router.post('/spawn', aiAgentController.spawnBot);

// Stop AI bot
router.post('/stop', aiAgentController.stopBot);

// Get bot status
router.get('/status/:roomName', aiAgentController.getStatus);

// List all active bots
router.get('/list', aiAgentController.listBots);

// Receive events from Python AI agent
router.post('/events', aiAgentController.receiveEvent);

// Health check
router.get('/health', aiAgentController.healthCheck);

export default router;
