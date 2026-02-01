/**
 * API client for handoff endpoints
 */

const API_BASE = '/api/handoff';

export async function getQueue() {
  const res = await fetch(`${API_BASE}/queue`);
  if (!res.ok) throw new Error('Failed to fetch queue');
  return res.json();
}

export async function getQueueStats() {
  const res = await fetch(`${API_BASE}/queue/stats`);
  if (!res.ok) throw new Error('Failed to fetch queue stats');
  return res.json();
}

export async function getAlertDetails(alertId: string) {
  const res = await fetch(`${API_BASE}/alert/${alertId}`);
  if (!res.ok) throw new Error('Failed to fetch alert details');
  return res.json();
}

export async function getAgentBrief(alertId: string) {
  const res = await fetch(`${API_BASE}/alert/${alertId}/brief`);
  if (!res.ok) throw new Error('Failed to fetch agent brief');
  return res.json();
}

export async function assignAgent(alertId: string, agentId: string) {
  const res = await fetch(`${API_BASE}/assign`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ alert_id: alertId, agent_id: agentId }),
  });
  if (!res.ok) throw new Error('Failed to assign agent');
  return res.json();
}

export async function startHandoffCall(alertId: string) {
  const res = await fetch(`${API_BASE}/start/${alertId}`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to start handoff call');
  return res.json();
}

export async function completeHandoff(alertId: string, resolution?: string) {
  const res = await fetch(`${API_BASE}/complete`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ alert_id: alertId, resolution }),
  });
  if (!res.ok) throw new Error('Failed to complete handoff');
  return res.json();
}

export async function getActiveConversations() {
  const res = await fetch(`${API_BASE}/conversations/active`);
  if (!res.ok) throw new Error('Failed to fetch active conversations');
  return res.json();
}

export async function getConversationStatus(callId: string) {
  const res = await fetch(`${API_BASE}/conversations/${callId}`);
  if (!res.ok) throw new Error('Failed to fetch conversation status');
  return res.json();
}
