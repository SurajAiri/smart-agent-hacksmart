/**
 * Webhook Routes - Express router for LiveKit webhook endpoints
 */
import { Router } from 'express';
import express from 'express';
import * as webhookController from '../controllers/webhook.controller.mjs';

const router = Router();

// Use raw body parser for webhook signature verification
// Note: This middleware must be applied before the route handler
router.use('/livekit', express.text({ type: '*/*' }));

// LiveKit webhook endpoint
router.post('/livekit', webhookController.handleWebhook);

// Health check
router.get('/health', webhookController.healthCheck);

export default router;
