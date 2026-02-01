'use client';

import { formatDistanceToNow } from 'date-fns';
import { clsx } from 'clsx';
import type { HandoffAlert } from '@/types';
import {
  PriorityBadge,
  TriggerBadge,
  WaitTime,
  LanguageBadge,
} from './Badges';

interface AlertCardProps {
  alert: HandoffAlert;
  isSelected?: boolean;
  onClick?: () => void;
  onAccept?: () => void;
}

export function AlertCard({ alert, isSelected, onClick, onAccept }: AlertCardProps) {
  const timeAgo = formatDistanceToNow(new Date(alert.created_at), { addSuffix: true });

  return (
    <div
      className={clsx(
        'border rounded-lg p-4 cursor-pointer transition-all hover:shadow-md',
        isSelected
          ? 'border-blue-500 bg-blue-50 shadow-md'
          : 'border-gray-200 bg-white hover:border-gray-300',
        alert.priority === 'urgent' && 'border-red-300 bg-red-50'
      )}
      onClick={onClick}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <PriorityBadge priority={alert.priority} />
          <span className="text-sm text-gray-500">#{alert.queue_position}</span>
        </div>
        <span className="text-xs text-gray-400">{timeAgo}</span>
      </div>

      {/* Trigger */}
      <div className="mb-2">
        <TriggerBadge trigger={alert.trigger} />
      </div>

      {/* Summary */}
      <p className="text-sm text-gray-700 mb-3 line-clamp-2">{alert.issue_summary}</p>

      {/* Footer */}
      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-3">
          <span className="font-mono text-gray-600">
            📞 ****{alert.driver_phone_last_4}
          </span>
          <LanguageBadge language={alert.driver_language} />
          {alert.driver_city && (
            <span className="text-gray-500">📍 {alert.driver_city}</span>
          )}
        </div>
        <WaitTime seconds={alert.estimated_wait_seconds} showLabel={false} />
      </div>

      {/* Accept Button */}
      {onAccept && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            onAccept();
          }}
          className={clsx(
            'mt-3 w-full py-2 rounded-md font-medium text-white transition-colors',
            alert.priority === 'urgent'
              ? 'bg-red-600 hover:bg-red-700'
              : 'bg-blue-600 hover:bg-blue-700'
          )}
        >
          Accept Call
        </button>
      )}
    </div>
  );
}
