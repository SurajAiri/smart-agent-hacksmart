/**
 * Shared constants for the AI Customer Care Agent
 */

// Call Event Types
export const CALL_EVENTS = {
  CALL_CREATED: 'CALL_CREATED',
  CALL_ACTIVE: 'CALL_ACTIVE',
  CALL_ENDED: 'CALL_ENDED',
  PARTICIPANT_JOINED: 'PARTICIPANT_JOINED',
  PARTICIPANT_LEFT: 'PARTICIPANT_LEFT',
  RECORDING_STARTED: 'RECORDING_STARTED',
  RECORDING_STOPPED: 'RECORDING_STOPPED',
  RECORDING_FAILED: 'RECORDING_FAILED',
};

// Participant Roles
export const PARTICIPANT_ROLES = {
  DRIVER: 'driver',
  AI_BOT: 'ai_bot',
  HUMAN_AGENT: 'human_agent',
};

// Call Status
export const CALL_STATUS = {
  CREATED: 'created',
  ACTIVE: 'active',
  ENDED: 'ended',
};

// Room Configuration
export const ROOM_CONFIG = {
  EMPTY_TIMEOUT_SECONDS: 300, // 5 minutes
  MAX_PARTICIPANTS: 10,
  DEPARTURE_TIMEOUT_SECONDS: 20,
};

// Audio Configuration
export const AUDIO_CONFIG = {
  SAMPLE_RATE: 48000,
  CHANNELS: 1,
  FRAME_SIZE_MS: 20,
  SILENCE_THRESHOLD: 0.01,
};

// Recording Configuration
export const RECORDING_CONFIG = {
  OUTPUT_DIR: 'recordings',
  FILE_TYPE: 'mp4',
  AUDIO_BITRATE: 128,
};
