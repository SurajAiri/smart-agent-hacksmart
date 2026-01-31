/**
 * Call Session Model - MongoDB model for persisting call sessions
 */
import mongoose from 'mongoose';
import { CALL_STATUS, PARTICIPANT_ROLES } from '../utils/constants.mjs';

const participantSchema = new mongoose.Schema({
  identity: {
    type: String,
    required: true,
  },
  role: {
    type: String,
    enum: Object.values(PARTICIPANT_ROLES),
    default: PARTICIPANT_ROLES.DRIVER,
  },
  sid: String,
  joinedAt: {
    type: Date,
    default: Date.now,
  },
  leftAt: Date,
  metadata: mongoose.Schema.Types.Mixed,
});

const eventLogSchema = new mongoose.Schema({
  event: {
    type: String,
    required: true,
  },
  timestamp: {
    type: Date,
    default: Date.now,
  },
  data: mongoose.Schema.Types.Mixed,
});

const callSessionSchema = new mongoose.Schema({
  callId: {
    type: String,
    required: true,
    unique: true,
    index: true,
  },
  roomName: {
    type: String,
    required: true,
    index: true,
  },
  roomSid: String,
  status: {
    type: String,
    enum: Object.values(CALL_STATUS),
    default: CALL_STATUS.CREATED,
  },
  participants: [participantSchema],
  recordingId: String,
  recordingStatus: {
    type: String,
    enum: ['not_started', 'recording', 'completed', 'failed'],
    default: 'not_started',
  },
  recordingUrl: String,
  events: [eventLogSchema],
  metadata: mongoose.Schema.Types.Mixed,
  createdAt: {
    type: Date,
    default: Date.now,
  },
  startedAt: Date,
  endedAt: Date,
  duration: Number, // Duration in seconds
}, {
  timestamps: true,
});

// Index for querying active calls
callSessionSchema.index({ status: 1 });
callSessionSchema.index({ createdAt: -1 });

// Virtual for calculating duration
callSessionSchema.virtual('calculatedDuration').get(function() {
  if (this.endedAt && this.startedAt) {
    return Math.floor((this.endedAt - this.startedAt) / 1000);
  }
  if (this.startedAt) {
    return Math.floor((new Date() - this.startedAt) / 1000);
  }
  return 0;
});

// Method to add event to log
callSessionSchema.methods.logEvent = function(event, data = {}) {
  this.events.push({
    event,
    timestamp: new Date(),
    data,
  });
  return this.save();
};

// Method to add participant
callSessionSchema.methods.addParticipant = function(identity, role, metadata = {}) {
  const existing = this.participants.find(p => p.identity === identity && !p.leftAt);
  if (existing) {
    return this; // Already in call
  }
  
  this.participants.push({
    identity,
    role,
    joinedAt: new Date(),
    metadata,
  });
  return this.save();
};

// Method to remove participant
callSessionSchema.methods.removeParticipant = function(identity) {
  const participant = this.participants.find(p => p.identity === identity && !p.leftAt);
  if (participant) {
    participant.leftAt = new Date();
  }
  return this.save();
};

// Static method to find active call by room name
callSessionSchema.statics.findActiveByRoom = function(roomName) {
  return this.findOne({
    roomName,
    status: { $in: [CALL_STATUS.CREATED, CALL_STATUS.ACTIVE] },
  });
};

const CallSession = mongoose.model('CallSession', callSessionSchema);

export default CallSession;
