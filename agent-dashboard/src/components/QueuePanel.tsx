'use client';

import type { HandoffAlert, QueueStats } from '@/types';
import { AlertCard } from './AlertCard';
import { PriorityBadge } from './Badges';

interface QueuePanelProps {
  alerts: HandoffAlert[];
  stats: QueueStats | null;
  selectedAlertId: string | null;
  onSelectAlert: (alertId: string) => void;
  onAcceptAlert: (alertId: string) => void;
  loading?: boolean;
}

export function QueuePanel({
  alerts,
  stats,
  selectedAlertId,
  onSelectAlert,
  onAcceptAlert,
  loading,
}: QueuePanelProps) {
  return (
    <div className="h-full flex flex-col bg-gray-50 border-r border-gray-200">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 bg-white">
        <h2 className="text-lg font-semibold text-gray-900">Handoff Queue</h2>
        
        {stats && (
          <div className="mt-2 flex items-center gap-4 text-sm">
            <span className="text-gray-600">
              <span className="font-medium text-gray-900">{stats.total}</span> waiting
            </span>
            <div className="flex items-center gap-2">
              {stats.by_priority.urgent > 0 && (
                <span className="flex items-center gap-1">
                  <PriorityBadge priority="urgent" size="sm" />
                  <span className="text-xs text-gray-500">{stats.by_priority.urgent}</span>
                </span>
              )}
              {stats.by_priority.high > 0 && (
                <span className="flex items-center gap-1">
                  <PriorityBadge priority="high" size="sm" />
                  <span className="text-xs text-gray-500">{stats.by_priority.high}</span>
                </span>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Alert List */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {loading ? (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
          </div>
        ) : alerts.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-32 text-gray-500">
            <svg
              className="w-12 h-12 mb-2 text-gray-300"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <span className="text-sm">No pending handoffs</span>
          </div>
        ) : (
          alerts.map((alert) => (
            <AlertCard
              key={alert.id}
              alert={alert}
              isSelected={alert.id === selectedAlertId}
              onClick={() => onSelectAlert(alert.id)}
              onAccept={() => onAcceptAlert(alert.id)}
            />
          ))
        )}
      </div>
    </div>
  );
}
