'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import { QueuePanel } from '@/components/QueuePanel';
import { ContextBrief } from '@/components/ContextBrief';
import { ConnectionStatus } from '@/components/ConnectionStatus';
import { CallControls } from '@/components/CallControls';
import { useHandoffSocket } from '@/hooks/useHandoffSocket';
import { useLiveKitCall } from '@/hooks/useLiveKitCall';
import { getQueue, getQueueStats, getAlertDetails, assignAgent, startHandoffCall, completeHandoff } from '@/lib/api';
import type { HandoffAlert, DetailedAlert, QueueStats, QueueSyncData } from '@/types';

// API to make AI agent leave
async function makeAIAgentLeave(roomName: string) {
  try {
    const res = await fetch(`/api/bot/leave`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ room_name: roomName }),
    });
    if (!res.ok) {
      console.warn('Failed to make AI agent leave, it may have already left');
    }
  } catch (e) {
    console.error('Error making AI agent leave:', e);
  }
}

export default function Dashboard() {
  // Generate agent ID only on client side to avoid hydration mismatch
  const [agentId, setAgentId] = useState<string>('');
  
  // Initialize agent ID on mount (client-side only)
  useEffect(() => {
    setAgentId(`agent-${Math.random().toString(36).substr(2, 9)}`);
  }, []);
  
  // Queue state
  const [alerts, setAlerts] = useState<HandoffAlert[]>([]);
  const [stats, setStats] = useState<QueueStats | null>(null);
  const [loading, setLoading] = useState(true);
  
  // Selected alert state
  const [selectedAlertId, setSelectedAlertId] = useState<string | null>(null);
  const [selectedAlert, setSelectedAlert] = useState<DetailedAlert | null>(null);
  const [loadingDetails, setLoadingDetails] = useState(false);
  
  // Active call state
  const [activeCallId, setActiveCallId] = useState<string | null>(null);
  const [activeRoomName, setActiveRoomName] = useState<string | null>(null);
  
  // Error state
  const [error, setError] = useState<string | null>(null);

  // LiveKit call hook
  const {
    isConnected: isInCall,
    isConnecting: isJoiningCall,
    isMuted,
    participants,
    connect: connectToRoom,
    disconnect: disconnectFromRoom,
    toggleMute,
  } = useLiveKitCall({
    onConnected: () => {
      console.log('Human agent joined the call');
    },
    onDisconnected: () => {
      console.log('Human agent left the call');
      setActiveRoomName(null);
    },
    onError: (error) => {
      setError(`Call error: ${error.message}`);
    },
  });

  // Load queue data
  const loadQueue = useCallback(async () => {
    try {
      const [queueData, statsData] = await Promise.all([
        getQueue(),
        getQueueStats(),
      ]);
      setAlerts(queueData);
      setStats(statsData);
      setError(null);
    } catch (e) {
      console.error('Failed to load queue', e);
      setError('Failed to load queue');
    } finally {
      setLoading(false);
    }
  }, []);

  // Load alert details
  const loadAlertDetails = useCallback(async (alertId: string) => {
    setLoadingDetails(true);
    try {
      const details = await getAlertDetails(alertId);
      setSelectedAlert(details);
    } catch (e) {
      console.error('Failed to load alert details', e);
      setError('Failed to load alert details');
    } finally {
      setLoadingDetails(false);
    }
  }, []);

  // Handle selecting an alert
  const handleSelectAlert = useCallback((alertId: string) => {
    setSelectedAlertId(alertId);
    loadAlertDetails(alertId);
  }, [loadAlertDetails]);

  // Handle accepting an alert
  const handleAcceptAlert = useCallback(async (alertId: string) => {
    if (!agentId) return;
    try {
      await assignAgent(alertId, agentId);
      setActiveCallId(alertId);
      // Reload queue and details
      loadQueue();
      loadAlertDetails(alertId);
    } catch (e) {
      console.error('Failed to accept alert', e);
      setError('Failed to accept alert');
    }
  }, [agentId, loadQueue, loadAlertDetails]);

  // Handle starting call - joins LiveKit room and makes AI agent leave
  const handleStartCall = useCallback(async () => {
    if (!activeCallId) return;
    try {
      // Get LiveKit token and room info from backend
      const result = await startHandoffCall(activeCallId);
      
      if (result.livekit_url && result.livekit_token) {
        // Store room name for later
        setActiveRoomName(result.room_name);
        
        // First, make the AI agent leave
        await makeAIAgentLeave(result.room_name);
        
        // Then join the room as human agent
        await connectToRoom(result.livekit_url, result.livekit_token);
        
        console.log('Human agent joined room:', result.room_name);
      }
      
      loadAlertDetails(activeCallId);
    } catch (e) {
      console.error('Failed to start call', e);
      setError('Failed to start call');
    }
  }, [activeCallId, loadAlertDetails, connectToRoom]);

  // Handle completing handoff
  const handleCompleteHandoff = useCallback(async () => {
    if (!activeCallId) return;
    try {
      // Disconnect from LiveKit room first
      if (isInCall) {
        await disconnectFromRoom();
      }
      
      await completeHandoff(activeCallId, 'Resolved by agent');
      setActiveCallId(null);
      setActiveRoomName(null);
      setSelectedAlertId(null);
      setSelectedAlert(null);
      loadQueue();
    } catch (e) {
      console.error('Failed to complete handoff', e);
      setError('Failed to complete handoff');
    }
  }, [activeCallId, loadQueue, isInCall, disconnectFromRoom]);

  // WebSocket handlers
  const handleNewAlert = useCallback((data: unknown) => {
    console.log('New alert received', data);
    loadQueue();
  }, [loadQueue]);

  const handleQueueSync = useCallback((data: QueueSyncData[]) => {
    console.log('Queue sync received', data);
    // Could update from WebSocket data directly, but simpler to just refresh
    loadQueue();
  }, [loadQueue]);

  const handleAssignmentConfirmed = useCallback((data: unknown) => {
    console.log('Assignment confirmed', data);
    loadQueue();
  }, [loadQueue]);

  const handleWsError = useCallback((message: string) => {
    console.error('WebSocket error', message);
    // Don't set error state for WS errors, just log
  }, []);

  // Connect to WebSocket (only when agentId is ready)
  const { connected, reconnecting } = useHandoffSocket({
    agentId: agentId || 'loading',
    onNewAlert: handleNewAlert,
    onQueueSync: handleQueueSync,
    onAssignmentConfirmed: handleAssignmentConfirmed,
    onError: handleWsError,
    enabled: !!agentId,
  });

  // Initial load
  useEffect(() => {
    loadQueue();
    
    // Poll every 30 seconds as backup
    const interval = setInterval(loadQueue, 30000);
    return () => clearInterval(interval);
  }, [loadQueue]);

  return (
    <div className="h-screen flex flex-col bg-gray-100">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h1 className="text-xl font-bold text-gray-900">
            🎧 Agent Dashboard
          </h1>
          <span className="text-sm text-gray-500">QuickRide Support</span>
        </div>
        
        <div className="flex items-center gap-4">
          {/* In-call indicator */}
          {isInCall && (
            <div className="flex items-center gap-2 px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-medium">
              <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
              On Call
              {participants.length > 0 && (
                <span className="text-green-600">
                  ({participants.length} participant{participants.length !== 1 ? 's' : ''})
                </span>
              )}
            </div>
          )}
          
          <ConnectionStatus
            connected={connected}
            reconnecting={reconnecting}
            agentId={agentId}
          />
        </div>
      </header>

      {/* In-Call Controls Bar */}
      {isInCall && (
        <div className="bg-gray-800 px-6 py-3 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <span className="text-white text-sm">
              🎙️ Connected to: <span className="font-medium">{activeRoomName}</span>
            </span>
          </div>
          
          <div className="flex items-center gap-3">
            <button
              onClick={toggleMute}
              className={`px-4 py-2 rounded-lg font-medium text-sm transition-colors ${
                isMuted
                  ? 'bg-red-600 text-white hover:bg-red-700'
                  : 'bg-gray-600 text-white hover:bg-gray-700'
              }`}
            >
              {isMuted ? '🔇 Unmute' : '🔊 Mute'}
            </button>
            
            <button
              onClick={handleCompleteHandoff}
              className="px-4 py-2 bg-green-600 text-white rounded-lg font-medium text-sm hover:bg-green-700 transition-colors"
            >
              ✓ Complete Call
            </button>
            
            <button
              onClick={async () => {
                await disconnectFromRoom();
                setError('Call disconnected');
              }}
              className="px-4 py-2 bg-red-600 text-white rounded-lg font-medium text-sm hover:bg-red-700 transition-colors"
            >
              ✕ End Call
            </button>
          </div>
        </div>
      )}

      {/* Joining call indicator */}
      {isJoiningCall && (
        <div className="bg-blue-50 border-b border-blue-200 px-6 py-2 flex items-center gap-2">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600" />
          <span className="text-sm text-blue-700">Joining call...</span>
        </div>
      )}

      {/* Error Banner */}
      {error && (
        <div className="bg-red-50 border-b border-red-200 px-6 py-2 flex items-center justify-between">
          <span className="text-sm text-red-700">{error}</span>
          <button
            onClick={() => setError(null)}
            className="text-red-500 hover:text-red-700"
          >
            ✕
          </button>
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Queue Panel - Left */}
        <div className="w-96 flex-shrink-0">
          <QueuePanel
            alerts={alerts}
            stats={stats}
            selectedAlertId={selectedAlertId}
            onSelectAlert={handleSelectAlert}
            onAcceptAlert={handleAcceptAlert}
            loading={loading}
          />
        </div>

        {/* Context Brief - Right */}
        <div className="flex-1 bg-white">
          <ContextBrief
            alert={selectedAlert}
            loading={loadingDetails}
            onStartCall={handleStartCall}
            onComplete={handleCompleteHandoff}
            isInCall={isInCall}
            isJoiningCall={isJoiningCall}
          />
        </div>
      </div>
    </div>
  );
}
