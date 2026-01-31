/**
 * Audio Ingress Service - Phase 5: Incoming Audio Safety
 * 
 * Handles audio input validation, silence detection, and packet monitoring
 * This is a utility service for processing incoming audio from driver
 */
import { EventEmitter } from 'events';
import { AUDIO_CONFIG } from '../../utils/constants.mjs';

// Audio event emitter for downstream processing
class AudioIngressEmitter extends EventEmitter {
  constructor() {
    super();
    this.setMaxListeners(10);
  }
}

export const audioIngressEvents = new AudioIngressEmitter();

// Metrics tracking
const metrics = {
  framesReceived: 0,
  framesDropped: 0,
  silentFrames: 0,
  totalBytes: 0,
  lastFrameTime: null,
  packetLossEvents: 0,
};

/**
 * Validate an audio frame
 * @param {Buffer|ArrayBuffer} frame - Audio frame data
 * @param {object} metadata - Frame metadata
 * @returns {object} Validation result
 */
export const validateFrame = (frame, metadata = {}) => {
  const issues = [];

  // Check frame exists
  if (!frame || frame.length === 0) {
    issues.push('empty_frame');
    metrics.framesDropped++;
    return { valid: false, issues };
  }

  // Check frame size
  const expectedSize = calculateExpectedFrameSize(metadata);
  if (frame.length < expectedSize * 0.5) {
    issues.push('undersized_frame');
  } else if (frame.length > expectedSize * 2) {
    issues.push('oversized_frame');
  }

  // Check for timestamp consistency
  if (metadata.timestamp) {
    const now = Date.now();
    const lag = now - metadata.timestamp;
    if (lag > 500) {
      issues.push('high_latency');
    }
    if (lag < 0) {
      issues.push('future_timestamp');
    }
  }

  metrics.framesReceived++;
  metrics.totalBytes += frame.length;
  metrics.lastFrameTime = Date.now();

  return {
    valid: issues.length === 0,
    issues,
    size: frame.length,
  };
};

/**
 * Detect if a frame is silent
 * @param {Buffer|ArrayBuffer} frame - Audio frame data
 * @param {number} threshold - Silence threshold (0-1)
 * @returns {boolean} True if frame is silent
 */
export const isSilentFrame = (frame, threshold = AUDIO_CONFIG.SILENCE_THRESHOLD) => {
  if (!frame || frame.length === 0) return true;

  // Convert to Float32 if needed
  const samples = getSamples(frame);
  if (samples.length === 0) return true;

  // Calculate RMS (Root Mean Square) energy
  let sumSquares = 0;
  for (let i = 0; i < samples.length; i++) {
    sumSquares += samples[i] * samples[i];
  }
  const rms = Math.sqrt(sumSquares / samples.length);

  const isSilent = rms < threshold;
  if (isSilent) {
    metrics.silentFrames++;
  }

  return isSilent;
};

/**
 * Check for packet loss by monitoring sequence gaps
 * @param {number} currentSeq - Current sequence number
 * @param {number} lastSeq - Last seen sequence number
 * @returns {object} Packet loss info
 */
let lastSequence = null;

export const checkPacketLoss = (currentSeq) => {
  if (lastSequence === null) {
    lastSequence = currentSeq;
    return { lost: 0, detected: false };
  }

  const expected = lastSequence + 1;
  const lost = currentSeq - expected;
  lastSequence = currentSeq;

  if (lost > 0) {
    metrics.packetLossEvents++;
    audioIngressEvents.emit('packet_loss', { lost, currentSeq, expected });
    return { lost, detected: true };
  }

  return { lost: 0, detected: false };
};

/**
 * Process an incoming audio frame
 * @param {Buffer} frame - Audio frame
 * @param {object} metadata - Frame metadata (timestamp, sequence, etc.)
 * @returns {object} Processing result
 */
export const processFrame = (frame, metadata = {}) => {
  // Validate
  const validation = validateFrame(frame, metadata);
  if (!validation.valid) {
    audioIngressEvents.emit('invalid_frame', { issues: validation.issues, metadata });
    return { accepted: false, reason: validation.issues };
  }

  // Check for silence
  const silent = isSilentFrame(frame);

  // Check for packet loss
  let packetLoss = { detected: false };
  if (metadata.sequence !== undefined) {
    packetLoss = checkPacketLoss(metadata.sequence);
  }

  // Emit for downstream processing
  if (!silent) {
    audioIngressEvents.emit('audio_frame', {
      frame,
      metadata,
      timestamp: Date.now(),
    });
  } else {
    audioIngressEvents.emit('silence', { duration: AUDIO_CONFIG.FRAME_SIZE_MS });
  }

  return {
    accepted: true,
    silent,
    packetLoss: packetLoss.detected,
    size: frame.length,
  };
};

/**
 * Create an audio buffer for accumulating frames
 * @param {number} durationMs - Buffer duration in milliseconds
 * @returns {object} Buffer manager
 */
export const createAudioBuffer = (durationMs = 1000) => {
  const frames = [];
  const maxFrames = Math.ceil(durationMs / AUDIO_CONFIG.FRAME_SIZE_MS);

  return {
    add(frame) {
      frames.push(frame);
      if (frames.length > maxFrames) {
        frames.shift();
      }
    },

    getBuffer() {
      if (frames.length === 0) return Buffer.alloc(0);
      return Buffer.concat(frames);
    },

    clear() {
      frames.length = 0;
    },

    get length() {
      return frames.length;
    },

    get durationMs() {
      return frames.length * AUDIO_CONFIG.FRAME_SIZE_MS;
    },
  };
};

/**
 * Get current metrics
 * @returns {object} Current metrics snapshot
 */
export const getMetrics = () => ({
  ...metrics,
  silenceRatio: metrics.framesReceived > 0 
    ? metrics.silentFrames / metrics.framesReceived 
    : 0,
  dropRatio: metrics.framesReceived > 0 
    ? metrics.framesDropped / (metrics.framesReceived + metrics.framesDropped)
    : 0,
});

/**
 * Reset metrics
 */
export const resetMetrics = () => {
  metrics.framesReceived = 0;
  metrics.framesDropped = 0;
  metrics.silentFrames = 0;
  metrics.totalBytes = 0;
  metrics.lastFrameTime = null;
  metrics.packetLossEvents = 0;
  lastSequence = null;
};

// ============ Helper Functions ============

function calculateExpectedFrameSize(metadata) {
  const sampleRate = metadata.sampleRate || AUDIO_CONFIG.SAMPLE_RATE;
  const channels = metadata.channels || AUDIO_CONFIG.CHANNELS;
  const frameSizeMs = metadata.frameSizeMs || AUDIO_CONFIG.FRAME_SIZE_MS;
  const bytesPerSample = 2; // 16-bit PCM

  return (sampleRate * channels * bytesPerSample * frameSizeMs) / 1000;
}

function getSamples(frame) {
  if (frame instanceof Float32Array) {
    return frame;
  }

  // Assume 16-bit PCM
  const samples = new Float32Array(frame.length / 2);
  const view = new DataView(frame.buffer || frame);

  for (let i = 0; i < samples.length; i++) {
    const int16 = view.getInt16(i * 2, true);
    samples[i] = int16 / 32768;
  }

  return samples;
}
