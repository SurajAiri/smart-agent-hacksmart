'use client';

import { clsx } from 'clsx';
import type { Priority, Sentiment } from '@/types';

// Priority Badge
interface PriorityBadgeProps {
  priority: Priority;
  size?: 'sm' | 'md' | 'lg';
}

export function PriorityBadge({ priority, size = 'md' }: PriorityBadgeProps) {
  const sizeClasses = {
    sm: 'px-1.5 py-0.5 text-xs',
    md: 'px-2 py-1 text-sm',
    lg: 'px-3 py-1.5 text-base',
  };

  return (
    <span
      className={clsx(
        'inline-flex items-center rounded-full font-medium uppercase',
        sizeClasses[size],
        `priority-${priority}`
      )}
    >
      {priority === 'urgent' && (
        <span className="mr-1 h-2 w-2 rounded-full bg-red-500 animate-pulse" />
      )}
      {priority}
    </span>
  );
}

// Sentiment Indicator
interface SentimentIndicatorProps {
  sentiment: Sentiment;
  score?: number;
  showScore?: boolean;
}

export function SentimentIndicator({ sentiment, score, showScore = false }: SentimentIndicatorProps) {
  const icons: Record<Sentiment, string> = {
    positive: '😊',
    neutral: '😐',
    negative: '😕',
    frustrated: '😤',
    angry: '😠',
  };

  return (
    <span className={clsx('inline-flex items-center gap-1', `sentiment-${sentiment}`)}>
      <span className="text-lg">{icons[sentiment]}</span>
      <span className="capitalize">{sentiment}</span>
      {showScore && score !== undefined && (
        <span className="text-xs text-gray-400">({score.toFixed(2)})</span>
      )}
    </span>
  );
}

// Wait Time Display
interface WaitTimeProps {
  seconds: number | null;
  showLabel?: boolean;
}

export function WaitTime({ seconds, showLabel = true }: WaitTimeProps) {
  if (seconds === null) return <span className="text-gray-400">-</span>;

  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;

  return (
    <span className="text-sm">
      {showLabel && <span className="text-gray-500">Est. wait: </span>}
      <span className="font-medium">
        {mins > 0 ? `${mins}m ` : ''}{secs}s
      </span>
    </span>
  );
}

// Trigger Badge
interface TriggerBadgeProps {
  trigger: string;
}

export function TriggerBadge({ trigger }: TriggerBadgeProps) {
  const formatTrigger = (t: string) => t.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

  const colorMap: Record<string, string> = {
    safety_emergency: 'bg-red-100 text-red-800 border-red-300',
    harassment_report: 'bg-red-100 text-red-800 border-red-300',
    fraud_detection: 'bg-purple-100 text-purple-800 border-purple-300',
    explicit_request: 'bg-blue-100 text-blue-800 border-blue-300',
    high_frustration: 'bg-orange-100 text-orange-800 border-orange-300',
    repeated_queries: 'bg-yellow-100 text-yellow-800 border-yellow-300',
    tool_failures: 'bg-gray-100 text-gray-800 border-gray-300',
    long_conversation: 'bg-gray-100 text-gray-800 border-gray-300',
  };

  return (
    <span
      className={clsx(
        'inline-block rounded px-2 py-0.5 text-xs font-medium border',
        colorMap[trigger] || 'bg-gray-100 text-gray-800 border-gray-300'
      )}
    >
      {formatTrigger(trigger)}
    </span>
  );
}

// Confidence Meter
interface ConfidenceMeterProps {
  value: number;
  label?: string;
}

export function ConfidenceMeter({ value, label = 'Escalation Confidence' }: ConfidenceMeterProps) {
  const percentage = Math.round(value * 100);
  
  const getColor = (pct: number) => {
    if (pct >= 75) return 'bg-red-500';
    if (pct >= 55) return 'bg-orange-500';
    if (pct >= 35) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  return (
    <div className="w-full">
      <div className="flex justify-between text-xs mb-1">
        <span className="text-gray-500">{label}</span>
        <span className="font-medium">{percentage}%</span>
      </div>
      <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
        <div
          className={clsx('h-full transition-all duration-300', getColor(percentage))}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

// Language Badge
interface LanguageBadgeProps {
  language: string;
}

export function LanguageBadge({ language }: LanguageBadgeProps) {
  const langMap: Record<string, string> = {
    'hi-IN': '🇮🇳 Hindi',
    'en-IN': '🇮🇳 English',
    'ta-IN': '🇮🇳 Tamil',
    'te-IN': '🇮🇳 Telugu',
    'kn-IN': '🇮🇳 Kannada',
    'mr-IN': '🇮🇳 Marathi',
    'gu-IN': '🇮🇳 Gujarati',
    'bn-IN': '🇮🇳 Bengali',
    'pa-IN': '🇮🇳 Punjabi',
    'en': '🌐 English',
  };

  return (
    <span className="inline-flex items-center text-sm text-gray-600">
      {langMap[language] || language}
    </span>
  );
}
