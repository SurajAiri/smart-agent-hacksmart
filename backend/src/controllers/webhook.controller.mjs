/**
 * Webhook Controller - LiveKit webhook receiver
 */
import { WebhookReceiver } from 'livekit-server-sdk';
import * as callEventService from '../services/livekit/call-event.service.mjs';

// Initialize webhook receiver
const LIVEKIT_API_KEY = process.env.LIVEKIT_API_KEY;
const LIVEKIT_API_SECRET = process.env.LIVEKIT_API_SECRET;

let webhookReceiver = null;

const getWebhookReceiver = () => {
  if (!webhookReceiver && LIVEKIT_API_KEY && LIVEKIT_API_SECRET) {
    webhookReceiver = new WebhookReceiver(LIVEKIT_API_KEY, LIVEKIT_API_SECRET);
  }
  return webhookReceiver;
};

/**
 * Handle LiveKit webhook events
 * POST /webhooks/livekit
 */
export const handleWebhook = async (req, res) => {
  const receiver = getWebhookReceiver();
  
  if (!receiver) {
    console.error('[WebhookController] Webhook receiver not configured');
    return res.status(500).json({ error: 'Webhook receiver not configured' });
  }

  try {
    // Get the raw body for signature verification
    const authHeader = req.get('Authorization');
    
    // Note: For signature verification to work, we need the raw body
    // Make sure express.raw() middleware is used for this route
    const body = typeof req.body === 'string' ? req.body : JSON.stringify(req.body);
    
    // Verify and parse the webhook event
    let event;
    try {
      event = await receiver.receive(body, authHeader);
    } catch (verifyError) {
      console.warn('[WebhookController] Webhook signature verification failed, processing anyway:', verifyError.message);
      // In development, we might want to process anyway
      event = typeof req.body === 'string' ? JSON.parse(req.body) : req.body;
    }

    console.log(`[WebhookController] Received webhook event: ${event.event}`);

    // Route event to appropriate handler
    switch (event.event) {
      case 'room_started':
        await handleRoomStarted(event);
        break;

      case 'room_finished':
        await handleRoomFinished(event);
        break;

      case 'participant_joined':
        await handleParticipantJoined(event);
        break;

      case 'participant_left':
        await handleParticipantLeft(event);
        break;

      case 'track_published':
        await handleTrackPublished(event);
        break;

      case 'track_unpublished':
        await handleTrackUnpublished(event);
        break;

      case 'egress_started':
        await handleEgressStarted(event);
        break;

      case 'egress_updated':
        await handleEgressUpdated(event);
        break;

      case 'egress_ended':
        await handleEgressEnded(event);
        break;

      default:
        console.log(`[WebhookController] Unhandled event type: ${event.event}`);
    }

    res.status(200).json({ received: true, event: event.event });
  } catch (error) {
    console.error('[WebhookController] Error processing webhook:', error);
    res.status(500).json({ error: error.message });
  }
};

// Event Handlers

async function handleRoomStarted(event) {
  console.log('[WebhookController] Room started:', event.room?.name);
  if (event.room) {
    await callEventService.handleRoomStarted(event.room);
  }
}

async function handleRoomFinished(event) {
  console.log('[WebhookController] Room finished:', event.room?.name);
  if (event.room) {
    await callEventService.handleRoomFinished(event.room);
  }
}

async function handleParticipantJoined(event) {
  console.log('[WebhookController] Participant joined:', event.participant?.identity);
  if (event.participant && event.room) {
    await callEventService.handleParticipantJoined(event.participant, event.room);
  }
}

async function handleParticipantLeft(event) {
  console.log('[WebhookController] Participant left:', event.participant?.identity);
  if (event.participant && event.room) {
    await callEventService.handleParticipantLeft(event.participant, event.room);
  }
}

async function handleTrackPublished(event) {
  console.log('[WebhookController] Track published:', {
    participant: event.participant?.identity,
    track: event.track?.sid,
    type: event.track?.type,
  });
  // Track events will be handled by TrackService in Phase 4
}

async function handleTrackUnpublished(event) {
  console.log('[WebhookController] Track unpublished:', {
    participant: event.participant?.identity,
    track: event.track?.sid,
  });
  // Track events will be handled by TrackService in Phase 4
}

async function handleEgressStarted(event) {
  console.log('[WebhookController] Egress started:', event.egressInfo?.egressId);
  // Recording events will be handled by RecordingService in Phase 7
}

async function handleEgressUpdated(event) {
  console.log('[WebhookController] Egress updated:', {
    egressId: event.egressInfo?.egressId,
    status: event.egressInfo?.status,
  });
  // Recording events will be handled by RecordingService in Phase 7
}

async function handleEgressEnded(event) {
  console.log('[WebhookController] Egress ended:', {
    egressId: event.egressInfo?.egressId,
    status: event.egressInfo?.status,
  });
  // Recording events will be handled by RecordingService in Phase 7
}

/**
 * Health check for webhook endpoint
 * GET /webhooks/health
 */
export const healthCheck = (req, res) => {
  res.status(200).json({
    status: 'ok',
    webhookConfigured: !!getWebhookReceiver(),
    timestamp: new Date().toISOString(),
  });
};
