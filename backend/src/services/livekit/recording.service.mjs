/**
 * Recording Service - Phase 7: Call Recording (Egress)
 * 
 * Key invariants:
 * - Exactly one recording per call
 * - Fail-safe: if recording fails, call continues
 * - Recordings stored locally initially, can be configured for S3/GCS
 */
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';
import { getEgressClient } from './livekit.client.mjs';
import CallSession from '../../models/call-session.model.mjs';
import { callEvents } from './call-event.service.mjs';
import { CALL_EVENTS, RECORDING_CONFIG } from '../../utils/constants.mjs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Get recordings directory (relative to project root)
const RECORDINGS_DIR = path.resolve(__dirname, '../../../', RECORDING_CONFIG.OUTPUT_DIR);

// Ensure recordings directory exists
if (!fs.existsSync(RECORDINGS_DIR)) {
  fs.mkdirSync(RECORDINGS_DIR, { recursive: true });
  console.log(`[RecordingService] Created recordings directory: ${RECORDINGS_DIR}`);
}

// Track active recordings (roomName -> egressId)
const activeRecordings = new Map();

/**
 * Start recording for a room
 * @param {string} roomName - Room name to record
 * @param {object} options - Recording options
 * @returns {Promise<object>} Recording info
 */
export const startRecording = async (roomName, options = {}) => {
  console.log(`[RecordingService] Starting recording for room: ${roomName}`);

  // Check for existing recording (exactly-one invariant)
  if (activeRecordings.has(roomName)) {
    const existingId = activeRecordings.get(roomName);
    console.log(`[RecordingService] Recording already active for ${roomName}: ${existingId}`);
    return {
      success: true,
      isExisting: true,
      egressId: existingId,
      roomName,
    };
  }

  const egressClient = getEgressClient();
  const timestamp = Date.now();
  const filename = `${roomName}-${timestamp}.${RECORDING_CONFIG.FILE_TYPE}`;
  const filepath = path.join(RECORDINGS_DIR, filename);

  try {
    // Start room composite egress (records all participants)
    const egressInfo = await egressClient.startRoomCompositeEgress(
      roomName,
      {
        file: {
          filepath,
          disableManifest: true,
        },
      },
      {
        layout: 'speaker',
        audioOnly: true, // Customer care is audio-only
        customBaseUrl: undefined,
      }
    );

    const egressId = egressInfo.egressId;
    activeRecordings.set(roomName, egressId);

    console.log(`[RecordingService] Recording started: ${egressId} -> ${filename}`);

    // Update call session
    await updateCallSessionRecording(roomName, egressId, 'recording');

    // Emit event
    callEvents.emit(CALL_EVENTS.RECORDING_STARTED, {
      roomName,
      egressId,
      filepath,
    });

    return {
      success: true,
      isExisting: false,
      egressId,
      roomName,
      filepath,
      filename,
    };
  } catch (error) {
    console.error(`[RecordingService] Failed to start recording:`, error.message);

    // Fail-safe: don't throw, just return failure
    // The call continues even if recording fails
    callEvents.emit(CALL_EVENTS.RECORDING_FAILED, {
      roomName,
      error: error.message,
    });

    return {
      success: false,
      error: error.message,
      roomName,
    };
  }
};

/**
 * Stop recording for a room
 * @param {string} roomName - Room name
 * @returns {Promise<object>} Stop result
 */
export const stopRecording = async (roomName) => {
  console.log(`[RecordingService] Stopping recording for room: ${roomName}`);

  const egressId = activeRecordings.get(roomName);
  if (!egressId) {
    console.log(`[RecordingService] No active recording for room: ${roomName}`);
    return { success: false, reason: 'No active recording' };
  }

  const egressClient = getEgressClient();

  try {
    await egressClient.stopEgress(egressId);
    activeRecordings.delete(roomName);

    console.log(`[RecordingService] Recording stopped: ${egressId}`);

    // Update call session
    await updateCallSessionRecording(roomName, egressId, 'completed');

    callEvents.emit(CALL_EVENTS.RECORDING_STOPPED, {
      roomName,
      egressId,
    });

    return {
      success: true,
      egressId,
      roomName,
    };
  } catch (error) {
    console.error(`[RecordingService] Failed to stop recording:`, error.message);

    // Clean up tracking even if stop fails
    activeRecordings.delete(roomName);

    return {
      success: false,
      error: error.message,
      egressId,
    };
  }
};

/**
 * Stop recording by egress ID
 * @param {string} egressId - Egress ID
 * @returns {Promise<object>} Stop result
 */
export const stopRecordingById = async (egressId) => {
  console.log(`[RecordingService] Stopping recording by ID: ${egressId}`);

  const egressClient = getEgressClient();

  try {
    await egressClient.stopEgress(egressId);

    // Find and clean up from active recordings
    for (const [roomName, id] of activeRecordings.entries()) {
      if (id === egressId) {
        activeRecordings.delete(roomName);
        await updateCallSessionRecording(roomName, egressId, 'completed');
        break;
      }
    }

    return { success: true, egressId };
  } catch (error) {
    console.error(`[RecordingService] Failed to stop recording:`, error.message);
    return { success: false, error: error.message, egressId };
  }
};

/**
 * Get recording status for a room
 * @param {string} roomName - Room name
 * @returns {Promise<object>} Recording status
 */
export const getRecordingStatus = async (roomName) => {
  const egressId = activeRecordings.get(roomName);

  if (!egressId) {
    return {
      isRecording: false,
      roomName,
    };
  }

  const egressClient = getEgressClient();

  try {
    const egresses = await egressClient.listEgress({ roomName });
    const activeEgress = egresses.find(e => e.egressId === egressId);

    return {
      isRecording: true,
      egressId,
      roomName,
      status: activeEgress?.status,
      startedAt: activeEgress?.startedAt,
    };
  } catch (error) {
    console.error(`[RecordingService] Failed to get status:`, error.message);
    return {
      isRecording: activeRecordings.has(roomName),
      egressId,
      roomName,
      error: error.message,
    };
  }
};

/**
 * List all recordings (egress history)
 * @param {string} roomName - Optional room name filter
 * @returns {Promise<Array>} List of egress info
 */
export const listRecordings = async (roomName = null) => {
  const egressClient = getEgressClient();

  try {
    const options = roomName ? { roomName } : {};
    const egresses = await egressClient.listEgress(options);

    return egresses.map(e => ({
      egressId: e.egressId,
      roomName: e.roomName,
      status: e.status,
      startedAt: e.startedAt ? new Date(Number(e.startedAt) / 1000000) : null,
      endedAt: e.endedAt ? new Date(Number(e.endedAt) / 1000000) : null,
      fileResults: e.fileResults,
    }));
  } catch (error) {
    console.error(`[RecordingService] Failed to list recordings:`, error.message);
    throw error;
  }
};

/**
 * Get list of local recording files
 * @returns {Array} List of recording files
 */
export const getLocalRecordings = () => {
  try {
    const files = fs.readdirSync(RECORDINGS_DIR);
    return files
      .filter(f => f.endsWith(`.${RECORDING_CONFIG.FILE_TYPE}`))
      .map(filename => {
        const filepath = path.join(RECORDINGS_DIR, filename);
        const stats = fs.statSync(filepath);
        return {
          filename,
          filepath,
          size: stats.size,
          createdAt: stats.birthtime,
          modifiedAt: stats.mtime,
        };
      })
      .sort((a, b) => b.createdAt - a.createdAt);
  } catch (error) {
    console.error(`[RecordingService] Failed to list local recordings:`, error.message);
    return [];
  }
};

// ============ Helper Functions ============

/**
 * Update call session with recording info
 */
async function updateCallSessionRecording(roomName, egressId, status) {
  try {
    const session = await CallSession.findActiveByRoom(roomName);
    if (session) {
      session.recordingId = egressId;
      session.recordingStatus = status;
      await session.save();
    }
  } catch (error) {
    console.error(`[RecordingService] Failed to update session:`, error.message);
  }
}

// ============ Auto-start Recording on Call ============

// Optionally start recording when a call becomes active
callEvents.on(CALL_EVENTS.CALL_ACTIVE, async ({ roomName }) => {
  // Uncomment to enable auto-recording
  // console.log(`[RecordingService] Auto-starting recording for ${roomName}`);
  // await startRecording(roomName);
});

// Stop recording when call ends
callEvents.on(CALL_EVENTS.CALL_ENDED, async ({ roomName }) => {
  if (activeRecordings.has(roomName)) {
    console.log(`[RecordingService] Auto-stopping recording for ${roomName}`);
    await stopRecording(roomName);
  }
});
