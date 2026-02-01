/**
 * Type definitions for the Agent Dashboard
 */

export type Priority = 'urgent' | 'high' | 'medium' | 'low';
export type Status = 'queued' | 'assigned' | 'in_progress' | 'completed' | 'abandoned' | 'cancelled';
export type Sentiment = 'positive' | 'neutral' | 'negative' | 'frustrated' | 'angry';

export interface HandoffAlert {
  id: string;
  conversation_id: string;
  call_id: string;
  trigger: string;
  priority: Priority;
  status: Status;
  driver_phone_last_4: string;
  driver_city: string | null;
  driver_language: string;
  issue_summary: string;
  queue_position: number | null;
  estimated_wait_seconds: number | null;
  assigned_agent_id: string | null;
  created_at: string;
}

export interface DetailedAlert extends HandoffAlert {
  trigger_description: string;
  driver_info: {
    phone_last_4: string;
    name: string | null;
    city: string | null;
    language: string;
    subscription_plan: string | null;
  };
  intent_history: string[];
  current_intent: string | null;
  sentiment: Sentiment;
  sentiment_score: number;
  detailed_summary: {
    one_line: string;
    detailed: string;
    primary_issue: string;
    secondary_issues: string[];
    stuck_on: string | null;
    topics_discussed: string[];
  };
  actions_taken: Array<{
    action: string;
    description: string;
    success: boolean;
  }>;
  suggested_actions: Array<{
    action: string;
    description: string;
    priority: string;
  }>;
  conversation_turns: Array<{
    role: string;
    content: string;
    timestamp: string;
    intent: string | null;
    sentiment: Sentiment | null;
  }>;
  assigned_at: string | null;
}

export interface AgentBrief {
  driver_name: string | null;
  driver_phone_last_4: string;
  driver_city: string | null;
  language: string;
  top_entities: Record<string, unknown>;
  summary: string;
  escalation_reason: string;
  escalation_description: string;
  sentiment: Sentiment;
  sentiment_score: number;
  suggested_actions: Array<{
    action: string;
    description: string;
    priority: string;
  }>;
  confidence_trend: string;
}

export interface QueueStats {
  total: number;
  by_priority: Record<Priority, number>;
  avg_wait_seconds: number;
}

export interface ConversationSummary {
  call_id: string;
  turn_count: number;
  sentiment: Sentiment;
  sentiment_score: number;
  sentiment_trend: string;
  current_intent: string | null;
  high_risk_intents: string[];
  repeat_count: number;
  tool_calls: Record<string, { count: number; success: number }>;
  escalation_confidence: number;
  duration_seconds: number;
}

// WebSocket message types
export interface WSMessage {
  type: 'queue_sync' | 'new_alert' | 'assignment_confirmed' | 'pong' | 'error';
  data?: unknown;
  timestamp: string;
  message?: string;
}

export interface QueueSyncData {
  id: string;
  priority: Priority;
  trigger: string;
  summary: string;
  queue_position: number;
}
