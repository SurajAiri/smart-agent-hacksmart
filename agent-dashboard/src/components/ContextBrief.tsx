'use client';

import { formatDistanceToNow } from 'date-fns';
import type { DetailedAlert, Sentiment } from '@/types';
import {
  PriorityBadge,
  TriggerBadge,
  SentimentIndicator,
  ConfidenceMeter,
  LanguageBadge,
} from './Badges';
import { clsx } from 'clsx';

interface ContextBriefProps {
  alert: DetailedAlert | null;
  loading?: boolean;
  onStartCall?: () => void;
  onComplete?: () => void;
  isInCall?: boolean;
  isJoiningCall?: boolean;
}

export function ContextBrief({ alert, loading, onStartCall, onComplete, isInCall, isJoiningCall }: ContextBriefProps) {
  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (!alert) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-gray-500">
        <svg
          className="w-16 h-16 mb-4 text-gray-300"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
          />
        </svg>
        <p className="text-sm">Select a handoff to view details</p>
      </div>
    );
  }

  return (
    <div className="h-full overflow-y-auto">
      {/* Header */}
      <div className="sticky top-0 bg-white border-b border-gray-200 p-4">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-3">
            <PriorityBadge priority={alert.priority} size="lg" />
            <TriggerBadge trigger={alert.trigger} />
          </div>
          <span className="text-sm text-gray-500">
            {formatDistanceToNow(new Date(alert.created_at), { addSuffix: true })}
          </span>
        </div>
        <p className="text-lg font-medium text-gray-900">{alert.issue_summary}</p>
      </div>

      <div className="p-4 space-y-6">
        {/* Driver Info */}
        <section>
          <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-2">
            Driver Info
          </h3>
          <div className="bg-gray-50 rounded-lg p-3 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Name</span>
              <span className="font-medium">{alert.driver_info.name || 'Unknown'}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Phone</span>
              <span className="font-mono">****{alert.driver_info.phone_last_4}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">City</span>
              <span>{alert.driver_info.city || 'Unknown'}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Language</span>
              <LanguageBadge language={alert.driver_info.language} />
            </div>
          </div>
        </section>

        {/* Sentiment & Confidence */}
        <section>
          <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-2">
            Conversation Health
          </h3>
          <div className="bg-gray-50 rounded-lg p-3 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Sentiment</span>
              <SentimentIndicator
                sentiment={alert.sentiment}
                score={alert.sentiment_score}
                showScore
              />
            </div>
            <ConfidenceMeter value={0.75} /> {/* Would come from state */}
          </div>
        </section>

        {/* Summary */}
        <section>
          <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-2">
            Summary
          </h3>
          <div className="bg-gray-50 rounded-lg p-3 space-y-2">
            <p className="text-sm text-gray-700">{alert.detailed_summary?.detailed}</p>
            {alert.detailed_summary?.stuck_on && (
              <div className="mt-2 p-2 bg-yellow-50 border border-yellow-200 rounded">
                <span className="text-xs font-medium text-yellow-800">Stuck on: </span>
                <span className="text-xs text-yellow-700">{alert.detailed_summary.stuck_on}</span>
              </div>
            )}
          </div>
        </section>

        {/* Suggested Actions */}
        <section>
          <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-2">
            Suggested Actions
          </h3>
          <div className="space-y-2">
            {alert.suggested_actions.map((action, i) => (
              <div
                key={i}
                className={clsx(
                  'p-3 rounded-lg border',
                  action.priority === 'urgent' || action.priority === 'high'
                    ? 'bg-orange-50 border-orange-200'
                    : 'bg-gray-50 border-gray-200'
                )}
              >
                <div className="flex items-center gap-2 mb-1">
                  <span
                    className={clsx(
                      'text-xs font-medium px-1.5 py-0.5 rounded',
                      action.priority === 'urgent' || action.priority === 'high'
                        ? 'bg-orange-200 text-orange-800'
                        : 'bg-gray-200 text-gray-700'
                    )}
                  >
                    {action.priority}
                  </span>
                  <span className="text-sm font-medium text-gray-900">{action.action}</span>
                </div>
                <p className="text-sm text-gray-600">{action.description}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Conversation History */}
        <section>
          <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-2">
            Conversation ({alert.conversation_turns.length} turns)
          </h3>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {alert.conversation_turns.map((turn, i) => (
              <div
                key={i}
                className={clsx(
                  'p-2 rounded-lg text-sm',
                  turn.role === 'user'
                    ? 'bg-blue-50 border-l-4 border-blue-400'
                    : 'bg-gray-50 border-l-4 border-gray-300'
                )}
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-medium text-gray-700">
                    {turn.role === 'user' ? '👤 Driver' : '🤖 Bot'}
                  </span>
                  {turn.sentiment && (
                    <SentimentIndicator sentiment={turn.sentiment as Sentiment} />
                  )}
                </div>
                <p className="text-gray-600">{turn.content}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Actions Taken by Bot */}
        <section>
          <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-2">
            Bot Actions
          </h3>
          <div className="space-y-1">
            {alert.actions_taken.map((action, i) => (
              <div
                key={i}
                className="flex items-center gap-2 text-sm"
              >
                <span
                  className={clsx(
                    'w-4 h-4 rounded-full flex items-center justify-center text-xs',
                    action.success ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'
                  )}
                >
                  {action.success ? '✓' : '✗'}
                </span>
                <span className="text-gray-600">{action.description}</span>
              </div>
            ))}
          </div>
        </section>

        {/* Action Buttons */}
        <div className="sticky bottom-0 bg-white pt-4 border-t border-gray-200 flex gap-3">
          {alert.status === 'assigned' && !isInCall && (
            <button
              onClick={onStartCall}
              disabled={isJoiningCall}
              className={clsx(
                'flex-1 py-3 font-medium rounded-lg transition-colors',
                isJoiningCall
                  ? 'bg-gray-400 text-white cursor-not-allowed'
                  : 'bg-green-600 hover:bg-green-700 text-white'
              )}
            >
              {isJoiningCall ? (
                <span className="flex items-center justify-center gap-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
                  Joining Call...
                </span>
              ) : (
                '📞 Start Call'
              )}
            </button>
          )}
          {(alert.status === 'in_progress' || isInCall) && (
            <div className="flex-1 flex gap-2">
              {isInCall && (
                <div className="flex items-center gap-2 px-4 py-3 bg-green-100 text-green-700 rounded-lg text-sm font-medium">
                  <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                  Call Active
                </div>
              )}
              <button
                onClick={onComplete}
                className="flex-1 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
              >
                ✓ Complete Handoff
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
