'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import {
  Room,
  RoomEvent,
  ConnectionState,
  LocalParticipant,
  RemoteParticipant,
  Track,
  LocalAudioTrack,
  RemoteTrack,
} from 'livekit-client';

interface UseLiveKitCallOptions {
  onConnected?: () => void;
  onDisconnected?: () => void;
  onError?: (error: Error) => void;
  onParticipantJoined?: (participant: RemoteParticipant) => void;
  onParticipantLeft?: (participant: RemoteParticipant) => void;
}

interface UseLiveKitCallReturn {
  isConnected: boolean;
  isConnecting: boolean;
  isMuted: boolean;
  participants: RemoteParticipant[];
  connect: (url: string, token: string) => Promise<void>;
  disconnect: () => Promise<void>;
  toggleMute: () => void;
}

export function useLiveKitCall(options: UseLiveKitCallOptions = {}): UseLiveKitCallReturn {
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [participants, setParticipants] = useState<RemoteParticipant[]>([]);
  
  const roomRef = useRef<Room | null>(null);
  const localAudioRef = useRef<LocalAudioTrack | null>(null);
  const audioElementRef = useRef<HTMLAudioElement | null>(null);

  const {
    onConnected,
    onDisconnected,
    onError,
    onParticipantJoined,
    onParticipantLeft,
  } = options;

  // Handle participant track subscriptions
  const handleTrackSubscribed = useCallback((
    track: RemoteTrack,
    _publication: any,
    participant: RemoteParticipant
  ) => {
    if (track.kind === Track.Kind.Audio) {
      // Create audio element to play remote audio
      if (!audioElementRef.current) {
        audioElementRef.current = document.createElement('audio');
        audioElementRef.current.autoplay = true;
        document.body.appendChild(audioElementRef.current);
      }
      track.attach(audioElementRef.current);
      console.log(`Audio track attached from ${participant.identity}`);
    }
  }, []);

  const handleTrackUnsubscribed = useCallback((track: RemoteTrack) => {
    if (track.kind === Track.Kind.Audio && audioElementRef.current) {
      track.detach(audioElementRef.current);
    }
  }, []);

  const connect = useCallback(async (url: string, token: string) => {
    if (roomRef.current) {
      console.warn('Already connected to a room');
      return;
    }

    setIsConnecting(true);
    
    try {
      const room = new Room({
        adaptiveStream: true,
        dynacast: true,
      });

      // Set up event handlers
      room.on(RoomEvent.Connected, () => {
        console.log('Connected to room');
        setIsConnected(true);
        setIsConnecting(false);
        onConnected?.();
      });

      room.on(RoomEvent.Disconnected, () => {
        console.log('Disconnected from room');
        setIsConnected(false);
        setIsConnecting(false);
        onDisconnected?.();
      });

      room.on(RoomEvent.ParticipantConnected, (participant: RemoteParticipant) => {
        console.log(`Participant connected: ${participant.identity}`);
        setParticipants(prev => [...prev, participant]);
        onParticipantJoined?.(participant);
      });

      room.on(RoomEvent.ParticipantDisconnected, (participant: RemoteParticipant) => {
        console.log(`Participant disconnected: ${participant.identity}`);
        setParticipants(prev => prev.filter(p => p.identity !== participant.identity));
        onParticipantLeft?.(participant);
      });

      room.on(RoomEvent.TrackSubscribed, handleTrackSubscribed);
      room.on(RoomEvent.TrackUnsubscribed, handleTrackUnsubscribed);

      room.on(RoomEvent.ConnectionStateChanged, (state: ConnectionState) => {
        console.log(`Connection state: ${state}`);
      });

      // Connect to the room
      await room.connect(url, token);
      roomRef.current = room;

      // Publish local audio track
      const audioTrack = await room.localParticipant.setMicrophoneEnabled(true);
      if (audioTrack) {
        localAudioRef.current = audioTrack as LocalAudioTrack;
      }

      // Subscribe to existing participants
      const existingParticipants = Array.from(room.remoteParticipants.values());
      setParticipants(existingParticipants);

      // Subscribe to existing audio tracks
      for (const participant of existingParticipants) {
        for (const publication of participant.audioTrackPublications.values()) {
          if (publication.track) {
            handleTrackSubscribed(publication.track as RemoteTrack, publication, participant);
          }
        }
      }

    } catch (error) {
      console.error('Failed to connect to room:', error);
      setIsConnecting(false);
      onError?.(error as Error);
      throw error;
    }
  }, [handleTrackSubscribed, handleTrackUnsubscribed, onConnected, onDisconnected, onError, onParticipantJoined, onParticipantLeft]);

  const disconnect = useCallback(async () => {
    if (roomRef.current) {
      await roomRef.current.disconnect();
      roomRef.current = null;
      localAudioRef.current = null;
    }

    // Clean up audio element
    if (audioElementRef.current) {
      audioElementRef.current.remove();
      audioElementRef.current = null;
    }

    setIsConnected(false);
    setParticipants([]);
  }, []);

  const toggleMute = useCallback(() => {
    if (localAudioRef.current) {
      const newMuted = !isMuted;
      localAudioRef.current.mute = newMuted;
      setIsMuted(newMuted);
    }
  }, [isMuted]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    isConnected,
    isConnecting,
    isMuted,
    participants,
    connect,
    disconnect,
    toggleMute,
  };
}
