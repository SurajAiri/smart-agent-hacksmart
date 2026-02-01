'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import type { WSMessage, QueueSyncData } from '@/types';

interface UseHandoffSocketOptions {
  agentId: string;
  onNewAlert?: (data: unknown) => void;
  onQueueSync?: (data: QueueSyncData[]) => void;
  onAssignmentConfirmed?: (data: unknown) => void;
  onError?: (message: string) => void;
  enabled?: boolean;  // Only connect when enabled
}

export function useHandoffSocket({
  agentId,
  onNewAlert,
  onQueueSync,
  onAssignmentConfirmed,
  onError,
  enabled = true,
}: UseHandoffSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [reconnecting, setReconnecting] = useState(false);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const pingIntervalRef = useRef<NodeJS.Timeout>();

  const connect = useCallback(() => {
    if (!enabled) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    // Use ws:// for local, wss:// for production
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//localhost:8000/api/handoff/dashboard/${agentId}`;

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
        setConnected(true);
        setReconnecting(false);

        // Start ping interval
        pingIntervalRef.current = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }));
          }
        }, 30000);
      };

      ws.onmessage = (event) => {
        try {
          const message: WSMessage = JSON.parse(event.data);

          switch (message.type) {
            case 'queue_sync':
              onQueueSync?.(message.data as QueueSyncData[]);
              break;
            case 'new_alert':
              onNewAlert?.(message.data);
              break;
            case 'assignment_confirmed':
              onAssignmentConfirmed?.(message.data);
              break;
            case 'error':
              onError?.(message.message || 'Unknown error');
              break;
            case 'pong':
              // Keep-alive acknowledged
              break;
          }
        } catch (e) {
          console.error('Failed to parse WebSocket message', e);
        }
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setConnected(false);
        clearInterval(pingIntervalRef.current);

        // Attempt reconnect after 3 seconds
        if (!reconnecting) {
          setReconnecting(true);
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, 3000);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error', error);
        onError?.('WebSocket connection error');
      };
    } catch (e) {
      console.error('Failed to create WebSocket', e);
      setReconnecting(true);
      reconnectTimeoutRef.current = setTimeout(() => {
        connect();
      }, 3000);
    }
  }, [agentId, enabled, onNewAlert, onQueueSync, onAssignmentConfirmed, onError, reconnecting]);

  const disconnect = useCallback(() => {
    clearTimeout(reconnectTimeoutRef.current);
    clearInterval(pingIntervalRef.current);
    wsRef.current?.close();
    wsRef.current = null;
    setConnected(false);
  }, []);

  const acceptAlert = useCallback((alertId: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'accept',
        alert_id: alertId,
      }));
    }
  }, []);

  useEffect(() => {
    if (enabled) {
      connect();
    }
    return () => disconnect();
  }, [connect, disconnect, enabled]);

  return {
    connected,
    reconnecting,
    acceptAlert,
    disconnect,
  };
}
