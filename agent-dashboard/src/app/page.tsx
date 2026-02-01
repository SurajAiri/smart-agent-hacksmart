'use client';

import { useState, useEffect, useCallback } from 'react';
import { useI18n } from '@/lib/i18n';
import { useHandoffSocket } from '@/hooks/useHandoffSocket';
import { useLiveKitCall } from '@/hooks/useLiveKitCall';
import { getQueue, getQueueStats, getAlertDetails, assignAgent, startHandoffCall, completeHandoff } from '@/lib/api';
import type { HandoffAlert, DetailedAlert, QueueStats, QueueSyncData } from '@/types';
import { formatDistanceToNow } from 'date-fns';
import { clsx } from 'clsx';

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

// Icons as components
const PhoneIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
  </svg>
);

const MicIcon = ({ muted }: { muted?: boolean }) => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    {muted ? (
      <>
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2" />
      </>
    ) : (
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
    )}
  </svg>
);

const CheckIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
  </svg>
);

const XIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
  </svg>
);

const HeadphonesIcon = () => (
  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
  </svg>
);

// Priority Badge Component
function PriorityBadge({ priority }: { priority: string }) {
  const colors: Record<string, string> = {
    urgent: 'bg-red-500/20 text-red-400 border-red-500/50',
    high: 'bg-orange-500/20 text-orange-400 border-orange-500/50',
    medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50',
    low: 'bg-green-500/20 text-green-400 border-green-500/50',
  };
  
  return (
    <span className={clsx(
      'px-2 py-0.5 text-xs font-semibold rounded-full border uppercase',
      colors[priority] || colors.medium
    )}>
      {priority}
    </span>
  );
}

// Trigger Badge Component  
function TriggerBadge({ trigger }: { trigger: string }) {
  const labels: Record<string, { label: string; emoji: string }> = {
    explicit_request: { label: 'Agent Request', emoji: '🙋' },
    sentiment_threshold: { label: 'Negative Sentiment', emoji: '😤' },
    frustration_detected: { label: 'Frustrated', emoji: '😡' },
    loop_detected: { label: 'Stuck in Loop', emoji: '🔄' },
  };
  
  const { label, emoji } = labels[trigger] || { label: trigger, emoji: '❓' };
  
  return (
    <span className="px-2 py-1 text-xs bg-gray-800 text-gray-300 rounded-lg flex items-center gap-1">
      <span>{emoji}</span>
      <span>{label}</span>
    </span>
  );
}

export default function Dashboard() {
  const { t, language, setLanguage } = useI18n();
  
  // Generate agent ID only on client side
  const [agentId, setAgentId] = useState<string>('');
  
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
    onConnected: () => console.log('Human agent joined the call'),
    onDisconnected: () => {
      console.log('Human agent left the call');
      setActiveRoomName(null);
    },
    onError: (error) => setError(`Call error: ${error.message}`),
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
      setError(t('error.failedToLoad'));
    } finally {
      setLoading(false);
    }
  }, [t]);

  // Load alert details
  const loadAlertDetails = useCallback(async (alertId: string) => {
    setLoadingDetails(true);
    try {
      const details = await getAlertDetails(alertId);
      setSelectedAlert(details);
    } catch (e) {
      console.error('Failed to load alert details', e);
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
      loadQueue();
      loadAlertDetails(alertId);
    } catch (e) {
      console.error('Failed to accept alert', e);
      setError('Failed to accept alert');
    }
  }, [agentId, loadQueue, loadAlertDetails]);

  // Handle starting call
  const handleStartCall = useCallback(async () => {
    if (!activeCallId) return;
    try {
      const result = await startHandoffCall(activeCallId);
      
      if (result.livekit_url && result.livekit_token) {
        setActiveRoomName(result.room_name);
        await makeAIAgentLeave(result.room_name);
        await connectToRoom(result.livekit_url, result.livekit_token);
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
  const handleNewAlert = useCallback(() => loadQueue(), [loadQueue]);
  const handleQueueSync = useCallback(() => loadQueue(), [loadQueue]);
  const handleAssignmentConfirmed = useCallback(() => loadQueue(), [loadQueue]);

  // Connect to WebSocket
  const { connected, reconnecting } = useHandoffSocket({
    agentId: agentId || 'loading',
    onNewAlert: handleNewAlert,
    onQueueSync: handleQueueSync,
    onAssignmentConfirmed: handleAssignmentConfirmed,
    onError: (msg) => console.error('WebSocket error', msg),
    enabled: !!agentId,
  });

  // Initial load
  useEffect(() => {
    loadQueue();
    const interval = setInterval(loadQueue, 30000);
    return () => clearInterval(interval);
  }, [loadQueue]);

  return (
    <div className="h-screen flex flex-col bg-gray-950">
      {/* Header */}
      <header className="glass border-b border-gray-800 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl gradient-accent flex items-center justify-center glow-indigo">
              <HeadphonesIcon />
            </div>
            <div>
              <h1 className="text-lg font-bold gradient-text">
                {t('header.title')}
              </h1>
              <p className="text-sm text-gray-500">{t('header.subtitle')}</p>
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            {/* Language Toggle */}
            <div className="flex bg-gray-800 rounded-lg p-1 gap-1">
              <button
                onClick={() => setLanguage('en')}
                className={clsx(
                  'px-3 py-1.5 text-sm font-medium rounded-md transition-all',
                  language === 'en' 
                    ? 'bg-indigo-600 text-white' 
                    : 'text-gray-400 hover:text-white'
                )}
              >
                EN
              </button>
              <button
                onClick={() => setLanguage('hi')}
                className={clsx(
                  'px-3 py-1.5 text-sm font-medium rounded-md transition-all',
                  language === 'hi' 
                    ? 'bg-indigo-600 text-white' 
                    : 'text-gray-400 hover:text-white'
                )}
              >
                हि
              </button>
            </div>
            
            {/* In-call indicator */}
            {isInCall && (
              <div className="flex items-center gap-2 px-3 py-1.5 bg-green-500/20 text-green-400 rounded-lg text-sm font-medium border border-green-500/30">
                <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                {t('header.onCall')}
              </div>
            )}
            
            {/* Connection Status */}
            <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-800 rounded-lg text-sm">
              <div className={clsx(
                'status-dot-animated',
                connected ? 'connected' : reconnecting ? 'reconnecting' : 'disconnected'
              )} />
              <span className="text-gray-400">
                {connected ? t('status.connected') : reconnecting ? t('status.reconnecting') : t('status.disconnected')}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* In-Call Controls Bar */}
      {isInCall && (
        <div className="bg-gray-900 border-b border-gray-800 px-6 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse" />
              <span className="text-gray-300">
                {t('call.connectedTo')}: <span className="font-mono text-white">{activeRoomName}</span>
              </span>
              {participants.length > 0 && (
                <span className="text-gray-500">
                  ({participants.length} {participants.length === 1 ? t('header.participants') : t('header.participantsPlural')})
                </span>
              )}
            </div>
            
            <div className="flex items-center gap-2">
              <button
                onClick={toggleMute}
                className={clsx(
                  'flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm transition-all',
                  isMuted
                    ? 'bg-red-600 text-white hover:bg-red-500'
                    : 'bg-gray-700 text-white hover:bg-gray-600'
                )}
              >
                <MicIcon muted={isMuted} />
                {isMuted ? t('call.unmute') : t('call.mute')}
              </button>
              
              <button
                onClick={handleCompleteHandoff}
                className="btn-success flex items-center gap-2"
              >
                <CheckIcon />
                {t('call.complete')}
              </button>
              
              <button
                onClick={async () => {
                  await disconnectFromRoom();
                  setError('Call disconnected');
                }}
                className="btn-danger flex items-center gap-2"
              >
                <XIcon />
                {t('call.end')}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Joining call indicator */}
      {isJoiningCall && (
        <div className="bg-indigo-500/10 border-b border-indigo-500/30 px-6 py-2 flex items-center gap-2">
          <div className="animate-spin rounded-full h-4 w-4 border-2 border-indigo-500 border-t-transparent" />
          <span className="text-sm text-indigo-400">{t('call.joining')}</span>
        </div>
      )}

      {/* Error Banner */}
      {error && (
        <div className="bg-red-500/10 border-b border-red-500/30 px-6 py-2 flex items-center justify-between">
          <span className="text-sm text-red-400">{error}</span>
          <button onClick={() => setError(null)} className="text-red-400 hover:text-red-300">
            <XIcon />
          </button>
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Queue Panel - Left */}
        <div className="w-96 flex-shrink-0 border-r border-gray-800 flex flex-col">
          {/* Queue Header */}
          <div className="p-4 border-b border-gray-800">
            <h2 className="text-lg font-semibold text-white">{t('queue.title')}</h2>
            {stats && (
              <div className="mt-2 flex items-center gap-4 text-sm">
                <span className="text-gray-400">
                  <span className="font-bold text-white">{stats.total}</span> {t('queue.waiting')}
                </span>
                {stats.by_priority.urgent > 0 && (
                  <span className="flex items-center gap-1">
                    <PriorityBadge priority="urgent" />
                    <span className="text-gray-500">{stats.by_priority.urgent}</span>
                  </span>
                )}
              </div>
            )}
          </div>

          {/* Alert List */}
          <div className="flex-1 overflow-y-auto p-3 space-y-2">
            {loading ? (
              <div className="flex items-center justify-center h-32">
                <div className="animate-spin rounded-full h-8 w-8 border-2 border-indigo-500 border-t-transparent" />
              </div>
            ) : alerts.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-32 text-gray-500">
                <svg className="w-12 h-12 mb-2 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="text-sm">{t('queue.noHandoffs')}</span>
              </div>
            ) : (
              alerts.map((alert) => (
                <div
                  key={alert.id}
                  onClick={() => handleSelectAlert(alert.id)}
                  className={clsx(
                    'p-3 rounded-xl border cursor-pointer transition-all animate-fadeIn',
                    alert.id === selectedAlertId
                      ? 'bg-indigo-500/10 border-indigo-500/50'
                      : 'bg-gray-900/50 border-gray-800 hover:border-gray-700 hover:bg-gray-800/50'
                  )}
                >
                  <div className="flex items-center justify-between mb-2">
                    <PriorityBadge priority={alert.priority} />
                    <span className="text-xs text-gray-500">
                      {formatDistanceToNow(new Date(alert.created_at), { addSuffix: true })}
                    </span>
                  </div>
                  <p className="text-sm text-gray-200 line-clamp-2">{alert.issue_summary}</p>
                  <div className="mt-2 flex items-center justify-between">
                    <TriggerBadge trigger={alert.trigger} />
                    {!alert.assigned_agent && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleAcceptAlert(alert.id);
                        }}
                        className="px-3 py-1 text-xs font-medium bg-indigo-600 text-white rounded-lg hover:bg-indigo-500 transition-all"
                      >
                        {t('alert.accept')}
                      </button>
                    )}
                    {alert.assigned_agent && (
                      <span className="text-xs text-green-400">{t('alert.assigned')}</span>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Context Brief - Right */}
        <div className="flex-1 overflow-y-auto">
          {loadingDetails ? (
            <div className="h-full flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-2 border-indigo-500 border-t-transparent" />
            </div>
          ) : !selectedAlert ? (
            <div className="h-full flex flex-col items-center justify-center text-gray-500">
              <svg className="w-16 h-16 mb-4 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
              <p className="text-sm">{t('brief.selectHandoff')}</p>
            </div>
          ) : (
            <div className="p-6 space-y-6 animate-fadeIn">
              {/* Header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <PriorityBadge priority={selectedAlert.priority} />
                  <TriggerBadge trigger={selectedAlert.trigger} />
                </div>
                <span className="text-sm text-gray-500">
                  {formatDistanceToNow(new Date(selectedAlert.created_at), { addSuffix: true })}
                </span>
              </div>
              
              <p className="text-xl font-semibold text-white">{selectedAlert.issue_summary}</p>

              {/* Action Buttons */}
              {activeCallId === selectedAlert.id && !isInCall && !isJoiningCall && (
                <button
                  onClick={handleStartCall}
                  className="btn-primary flex items-center gap-2 w-full justify-center py-3"
                >
                  <PhoneIcon />
                  {t('call.startCall')}
                </button>
              )}

              {/* Driver Info Card */}
              <div className="card p-4">
                <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">
                  {t('brief.driverInfo')}
                </h3>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <span className="text-gray-500">{t('brief.name')}</span>
                    <p className="text-white font-medium">{selectedAlert.driver_info.name || t('brief.unknown')}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">{t('brief.phone')}</span>
                    <p className="text-white font-mono">****{selectedAlert.driver_info.phone_last_4}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">{t('brief.city')}</span>
                    <p className="text-white">{selectedAlert.driver_info.city || t('brief.unknown')}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">{t('brief.language')}</span>
                    <p className="text-white">{selectedAlert.driver_info.language}</p>
                  </div>
                </div>
              </div>

              {/* Summary Card */}
              <div className="card p-4">
                <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">
                  {t('brief.summary')}
                </h3>
                <p className="text-gray-300 leading-relaxed">{selectedAlert.detailed_summary?.detailed}</p>
                {selectedAlert.detailed_summary?.stuck_on && (
                  <div className="mt-3 p-3 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
                    <span className="text-xs font-medium text-yellow-400">{t('brief.stuckOn')}: </span>
                    <span className="text-sm text-yellow-300">{selectedAlert.detailed_summary.stuck_on}</span>
                  </div>
                )}
              </div>

              {/* Suggested Actions */}
              {selectedAlert.suggested_actions.length > 0 && (
                <div className="card p-4">
                  <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">
                    {t('brief.suggestedActions')}
                  </h3>
                  <div className="space-y-2">
                    {selectedAlert.suggested_actions.map((action, i) => (
                      <div
                        key={i}
                        className={clsx(
                          'p-3 rounded-lg border',
                          action.priority === 'urgent' || action.priority === 'high'
                            ? 'bg-orange-500/10 border-orange-500/30'
                            : 'bg-gray-800/50 border-gray-700'
                        )}
                      >
                        <div className="flex items-center gap-2 mb-1">
                          <span className={clsx(
                            'text-xs font-medium px-2 py-0.5 rounded',
                            action.priority === 'urgent' || action.priority === 'high'
                              ? 'bg-orange-500/20 text-orange-400'
                              : 'bg-gray-700 text-gray-400'
                          )}>
                            {action.priority}
                          </span>
                          <span className="text-sm font-medium text-white">{action.action}</span>
                        </div>
                        <p className="text-sm text-gray-400">{action.description}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Conversation History */}
              <div className="card p-4">
                <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">
                  {t('brief.conversation')} ({selectedAlert.conversation_turns.length} {t('brief.turns')})
                </h3>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {selectedAlert.conversation_turns.map((turn, i) => (
                    <div
                      key={i}
                      className={clsx(
                        'p-3 rounded-lg text-sm',
                        turn.role === 'user'
                          ? 'bg-indigo-500/10 border-l-2 border-indigo-500'
                          : 'bg-gray-800/50 border-l-2 border-gray-600'
                      )}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-medium text-gray-300">
                          {turn.role === 'user' ? `👤 ${t('brief.driver')}` : `🤖 ${t('brief.bot')}`}
                        </span>
                      </div>
                      <p className="text-gray-400">{turn.content}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
