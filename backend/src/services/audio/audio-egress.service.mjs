/**
 * Audio Egress Service - Phase 6: Outgoing Audio (TTS)
 * 
 * Handles TTS audio publishing with:
 * - Timing preservation
 * - Frame queue to prevent overlapping
 * - Backpressure handling
 */
import { EventEmitter } from 'events';
import { AUDIO_CONFIG } from '../../utils/constants.mjs';

// Audio event emitter
class AudioEgressEmitter extends EventEmitter {
  constructor() {
    super();
    this.setMaxListeners(10);
  }
}

export const audioEgressEvents = new AudioEgressEmitter();

// Active audio queues per room
const audioQueues = new Map();

/**
 * Create an audio queue for a room
 * Ensures no overlapping audio frames
 */
class AudioQueue {
  constructor(roomName) {
    this.roomName = roomName;
    this.queue = [];
    this.isPlaying = false;
    this.currentItem = null;
    this.paused = false;
  }

  /**
   * Add audio to the queue
   * @param {Buffer} audioBuffer - Audio data
   * @param {object} metadata - Audio metadata
   * @returns {string} Queue item ID
   */
  enqueue(audioBuffer, metadata = {}) {
    const id = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    
    this.queue.push({
      id,
      buffer: audioBuffer,
      metadata,
      enqueuedAt: Date.now(),
      duration: calculateDuration(audioBuffer, metadata),
    });

    console.log(`[AudioEgress] Queued audio: ${id} (${this.queue.length} in queue)`);
    
    // Start processing if not already
    if (!this.isPlaying) {
      this.processNext();
    }

    return id;
  }

  /**
   * Process next item in queue
   */
  async processNext() {
    if (this.queue.length === 0 || this.paused) {
      this.isPlaying = false;
      return;
    }

    this.isPlaying = true;
    this.currentItem = this.queue.shift();

    const { id, buffer, metadata, duration } = this.currentItem;
    console.log(`[AudioEgress] Playing audio: ${id} (duration: ${duration}ms)`);

    audioEgressEvents.emit('audio_start', {
      roomName: this.roomName,
      id,
      duration,
      metadata,
    });

    // Simulate playback timing
    // In real implementation, this would publish to LiveKit track
    await this.publishAudio(buffer, metadata);

    // Wait for audio duration to complete
    await this.wait(duration);

    audioEgressEvents.emit('audio_end', {
      roomName: this.roomName,
      id,
      duration,
    });

    this.currentItem = null;

    // Process next in queue
    this.processNext();
  }

  /**
   * Publish audio to LiveKit
   * Note: Actual implementation depends on LiveKit client SDK
   */
  async publishAudio(buffer, metadata) {
    // This would use the LiveKit RTC SDK to publish audio frames
    // For server-side, this requires a LocalAudioTrack
    
    // Placeholder - emit event for actual publisher to handle
    audioEgressEvents.emit('publish_audio', {
      roomName: this.roomName,
      buffer,
      metadata,
    });
  }

  /**
   * Wait helper
   */
  wait(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Clear the queue
   */
  clear() {
    const cleared = this.queue.length;
    this.queue = [];
    console.log(`[AudioEgress] Cleared ${cleared} items from queue`);
    return cleared;
  }

  /**
   * Pause playback
   */
  pause() {
    this.paused = true;
  }

  /**
   * Resume playback
   */
  resume() {
    this.paused = false;
    if (!this.isPlaying) {
      this.processNext();
    }
  }

  /**
   * Get queue status
   */
  getStatus() {
    return {
      roomName: this.roomName,
      queueLength: this.queue.length,
      isPlaying: this.isPlaying,
      isPaused: this.paused,
      currentItem: this.currentItem ? {
        id: this.currentItem.id,
        duration: this.currentItem.duration,
      } : null,
    };
  }
}

/**
 * Get or create audio queue for a room
 * @param {string} roomName - Room name
 * @returns {AudioQueue}
 */
export const getQueue = (roomName) => {
  if (!audioQueues.has(roomName)) {
    audioQueues.set(roomName, new AudioQueue(roomName));
  }
  return audioQueues.get(roomName);
};

/**
 * Queue TTS audio for a room
 * @param {string} roomName - Room to publish to
 * @param {Buffer} audioBuffer - TTS audio data
 * @param {object} metadata - Audio metadata
 * @returns {string} Queue item ID
 */
export const queueAudio = (roomName, audioBuffer, metadata = {}) => {
  const queue = getQueue(roomName);
  return queue.enqueue(audioBuffer, metadata);
};

/**
 * Clear audio queue for a room
 * @param {string} roomName - Room name
 * @returns {number} Number of items cleared
 */
export const clearQueue = (roomName) => {
  const queue = audioQueues.get(roomName);
  if (queue) {
    return queue.clear();
  }
  return 0;
};

/**
 * Pause audio for a room
 * @param {string} roomName - Room name
 */
export const pauseAudio = (roomName) => {
  const queue = audioQueues.get(roomName);
  if (queue) {
    queue.pause();
  }
};

/**
 * Resume audio for a room
 * @param {string} roomName - Room name
 */
export const resumeAudio = (roomName) => {
  const queue = audioQueues.get(roomName);
  if (queue) {
    queue.resume();
  }
};

/**
 * Get audio egress status for a room
 * @param {string} roomName - Room name
 * @returns {object} Status
 */
export const getStatus = (roomName) => {
  const queue = audioQueues.get(roomName);
  if (queue) {
    return queue.getStatus();
  }
  return {
    roomName,
    queueLength: 0,
    isPlaying: false,
    isPaused: false,
    currentItem: null,
  };
};

/**
 * Clean up audio queue for a room
 * @param {string} roomName - Room name
 */
export const cleanup = (roomName) => {
  const queue = audioQueues.get(roomName);
  if (queue) {
    queue.clear();
    audioQueues.delete(roomName);
  }
  console.log(`[AudioEgress] Cleaned up queue for room ${roomName}`);
};

/**
 * Interrupt current audio and play new audio immediately
 * @param {string} roomName - Room name
 * @param {Buffer} audioBuffer - Audio to play
 * @param {object} metadata - Metadata
 * @returns {string} New audio ID
 */
export const interruptAndPlay = (roomName, audioBuffer, metadata = {}) => {
  const queue = getQueue(roomName);
  queue.clear();
  
  audioEgressEvents.emit('audio_interrupted', {
    roomName,
    previousItem: queue.currentItem?.id,
  });

  return queue.enqueue(audioBuffer, { ...metadata, interrupted: true });
};

// ============ Helper Functions ============

/**
 * Calculate audio duration from buffer
 */
function calculateDuration(buffer, metadata = {}) {
  if (metadata.duration) {
    return metadata.duration;
  }

  const sampleRate = metadata.sampleRate || AUDIO_CONFIG.SAMPLE_RATE;
  const channels = metadata.channels || AUDIO_CONFIG.CHANNELS;
  const bytesPerSample = metadata.bytesPerSample || 2;

  const samples = buffer.length / (channels * bytesPerSample);
  return (samples / sampleRate) * 1000;
}

// ============ Event Listeners ============

// Clean up when room ends
import { callEvents } from '../livekit/call-event.service.mjs';
import { CALL_EVENTS } from '../../utils/constants.mjs';

callEvents.on(CALL_EVENTS.CALL_ENDED, ({ roomName }) => {
  cleanup(roomName);
});
