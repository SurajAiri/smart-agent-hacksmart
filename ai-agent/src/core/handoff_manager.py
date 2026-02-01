"""
Handoff Manager - Manages the handoff queue and agent assignments.

Responsibilities:
- Priority queue for handoff requests
- Agent brief generation
- Call transfer coordination
- WebSocket notifications for agent dashboard
"""
from datetime import datetime
from typing import Optional, Dict, List, Any, Callable
from uuid import UUID
import asyncio

from loguru import logger

from src.core.models import (
    ConversationState,
    ConversationTurn,
    ConversationSummary,
    HandoffAlert,
    HandoffTrigger,
    HandoffPriority,
    HandoffStatus,
    SuggestedAction,
    IntentCategory,
    SentimentLabel,
)


class HandoffQueue:
    """
    Priority queue for handoff alerts.
    
    Alerts are sorted by:
    1. Priority (urgent > high > medium > low)
    2. Creation time (FIFO within same priority)
    """
    
    PRIORITY_ORDER = {
        HandoffPriority.URGENT: 0,
        HandoffPriority.HIGH: 1,
        HandoffPriority.MEDIUM: 2,
        HandoffPriority.LOW: 3,
    }
    
    def __init__(self):
        self._queue: List[HandoffAlert] = []
        self._by_id: Dict[UUID, HandoffAlert] = {}
        self._by_call_id: Dict[str, HandoffAlert] = {}
    
    def add(self, alert: HandoffAlert) -> int:
        """Add alert to queue and return its position."""
        self._queue.append(alert)
        self._by_id[alert.id] = alert
        self._by_call_id[alert.call_id] = alert
        
        # Sort by priority and time
        self._queue.sort(key=lambda a: (
            self.PRIORITY_ORDER.get(a.priority, 99),
            a.created_at
        ))
        
        # Update positions
        for i, a in enumerate(self._queue):
            a.queue_position = i + 1
        
        position = self._queue.index(alert) + 1
        logger.info(f"Added handoff alert {alert.id} at position {position}")
        return position
    
    def remove(self, alert_id: UUID) -> Optional[HandoffAlert]:
        """Remove alert from queue."""
        alert = self._by_id.pop(alert_id, None)
        if alert:
            self._queue = [a for a in self._queue if a.id != alert_id]
            self._by_call_id.pop(alert.call_id, None)
            self._update_positions()
            logger.info(f"Removed handoff alert {alert_id}")
        return alert
    
    def get_by_id(self, alert_id: UUID) -> Optional[HandoffAlert]:
        """Get alert by ID."""
        return self._by_id.get(alert_id)
    
    def get_by_call_id(self, call_id: str) -> Optional[HandoffAlert]:
        """Get alert by call ID."""
        return self._by_call_id.get(call_id)
    
    def get_next(self) -> Optional[HandoffAlert]:
        """Get next alert in queue (highest priority, oldest)."""
        for alert in self._queue:
            if alert.status == HandoffStatus.QUEUED:
                return alert
        return None
    
    def get_all(self) -> List[HandoffAlert]:
        """Get all alerts in queue."""
        return list(self._queue)
    
    def _update_positions(self) -> None:
        """Update queue positions after changes."""
        for i, alert in enumerate(self._queue):
            alert.queue_position = i + 1
    
    def __len__(self) -> int:
        return len(self._queue)


class HandoffNotifier:
    """
    Manages WebSocket notifications for agent dashboards.
    """
    
    def __init__(self):
        self._handlers: List[Callable] = []
    
    def register_websocket_handler(self, handler: Callable) -> None:
        """Register a WebSocket handler for notifications."""
        self._handlers.append(handler)
    
    async def notify_new_alert(self, alert: HandoffAlert) -> None:
        """Notify all registered handlers of new alert."""
        for handler in self._handlers:
            try:
                await handler(alert)
            except Exception as e:
                logger.error(f"Error notifying handler: {e}")
    
    async def notify_update(self, alert: HandoffAlert, event: str) -> None:
        """Notify handlers of alert update."""
        for handler in self._handlers:
            try:
                await handler(alert, event)
            except Exception as e:
                logger.error(f"Error notifying handler: {e}")


class HandoffManager:
    """
    Central manager for handoff operations.
    
    Coordinates:
    - Queue management
    - Brief generation for agents
    - Agent assignment
    - Call transfer
    """
    
    # Estimated wait time per position (seconds)
    WAIT_TIME_PER_POSITION = 60
    
    def __init__(self):
        self.queue = HandoffQueue()
        self.notifier = HandoffNotifier()
        self._active_handoffs: Dict[str, HandoffAlert] = {}  # call_id -> alert
        self._completed_handoffs: List[HandoffAlert] = []
        logger.info("HandoffManager initialized")
    
    async def trigger_handoff(
        self,
        state: ConversationState,
        trigger: HandoffTrigger,
        priority: HandoffPriority,
    ) -> HandoffAlert:
        """
        Trigger a handoff for a conversation.
        
        Args:
            state: Conversation state
            trigger: What triggered the handoff
            priority: Handoff priority
            
        Returns:
            Created HandoffAlert
        """
        # Generate summary
        summary = self._generate_summary(state, trigger)
        
        # Generate suggested actions
        suggestions = self._generate_suggestions(state, trigger)
        
        # Create alert
        alert = HandoffAlert(
            conversation_id=state.id,
            call_id=state.call_id,
            room_name=state.room_name,
            trigger=trigger,
            trigger_description=self._get_trigger_description(trigger, state),
            priority=priority,
            driver_info=state.driver_info,
            intent_history=state.intent_history,
            current_intent=state.current_intent,
            sentiment=state.current_sentiment,
            sentiment_score=state.sentiment_score,
            issue_summary=summary.one_line_summary,
            detailed_summary=summary,
            conversation_turns=state.turns,
            actions_taken_by_bot=state.actions_taken,
            next_steps_for_agent=suggestions,
        )
        
        # Add to queue
        position = self.queue.add(alert)
        alert.estimated_wait_seconds = position * self.WAIT_TIME_PER_POSITION
        
        # Mark state as escalated
        state.escalation_triggered = True
        state.escalation_trigger = trigger
        
        # Notify dashboards
        await self.notifier.notify_new_alert(alert)
        
        logger.info(
            f"Handoff triggered for call {state.call_id}: "
            f"trigger={trigger.value}, priority={priority.value}, position={position}"
        )
        
        return alert
    
    def _generate_summary(
        self,
        state: ConversationState,
        trigger: HandoffTrigger,
    ) -> ConversationSummary:
        """Generate conversation summary for agent."""
        # Get user turns
        user_turns = [t for t in state.turns if t.role == "user"]
        
        # Identify primary issue
        primary_issue = self._identify_primary_issue(state, trigger)
        
        # Get topics discussed
        topics = self._extract_topics(state)
        
        # One-line summary
        one_line = f"{trigger.value.replace('_', ' ').title()}: {primary_issue}"
        
        # Detailed summary
        detailed_parts = []
        
        if user_turns:
            detailed_parts.append(f"User started with: \"{user_turns[0].content[:100]}...\"" if len(user_turns[0].content) > 100 else f"User started with: \"{user_turns[0].content}\"")
        
        if state.repeat_count > 0:
            detailed_parts.append(f"User repeated similar queries {state.repeat_count} times.")
        
        if state.sentiment_trend == "declining":
            detailed_parts.append("User sentiment has been declining throughout the conversation.")
        
        if state.tool_failure_count > 0:
            detailed_parts.append(f"Bot encountered {state.tool_failure_count} tool failures.")
        
        detailed = " ".join(detailed_parts)
        
        # What's the bot stuck on?
        stuck_on = None
        if trigger == HandoffTrigger.REPEATED_QUERIES and state.last_repeated_query:
            stuck_on = state.last_repeated_query
        elif trigger == HandoffTrigger.BOT_STUCK:
            stuck_on = "Unable to resolve user's request after multiple attempts"
        
        return ConversationSummary(
            one_line_summary=one_line,
            detailed_summary=detailed,
            primary_issue=primary_issue,
            secondary_issues=[],
            stuck_on=stuck_on,
            topics_discussed=topics,
            resolution_attempted=state.tool_success_count > 0,
        )
    
    def _identify_primary_issue(
        self,
        state: ConversationState,
        trigger: HandoffTrigger,
    ) -> str:
        """Identify the primary issue from conversation."""
        # Map trigger to issue
        trigger_issues = {
            HandoffTrigger.EXPLICIT_REQUEST: "User requested human agent",
            HandoffTrigger.HIGH_FRUSTRATION: "User is frustrated with bot responses",
            HandoffTrigger.REPEATED_QUERIES: "Bot unable to answer user's question",
            HandoffTrigger.FRAUD_DETECTION: "Potential fraud reported",
            HandoffTrigger.SAFETY_EMERGENCY: "Safety or emergency situation",
            HandoffTrigger.HARASSMENT_REPORT: "Harassment incident reported",
            HandoffTrigger.TOOL_FAILURES: "Technical issues with service",
            HandoffTrigger.LONG_CONVERSATION: "Extended unresolved conversation",
        }
        
        # Check for specific intents
        if IntentCategory.PAYMENT_ISSUE in state.high_risk_intents_detected:
            return "Payment or refund issue"
        if IntentCategory.ACCOUNT_ISSUE in state.high_risk_intents_detected:
            return "Account related problem"
        
        return trigger_issues.get(trigger, "Unresolved query")
    
    def _extract_topics(self, state: ConversationState) -> List[str]:
        """Extract main topics discussed."""
        topics = set()
        
        intent_topics = {
            IntentCategory.TRIP_INQUIRY: "Trip Status",
            IntentCategory.FAQ_QUERY: "FAQs",
            IntentCategory.PAYMENT_ISSUE: "Payment",
            IntentCategory.COMPLAINT: "Complaint",
            IntentCategory.SAFETY_CONCERN: "Safety",
            IntentCategory.ACCOUNT_ISSUE: "Account",
        }
        
        for intent in state.intent_history:
            if intent in intent_topics:
                topics.add(intent_topics[intent])
        
        return list(topics)
    
    def _generate_suggestions(
        self,
        state: ConversationState,
        trigger: HandoffTrigger,
    ) -> List[SuggestedAction]:
        """Generate suggested actions for the agent."""
        suggestions = []
        
        # Based on trigger
        if trigger == HandoffTrigger.FRAUD_DETECTION:
            suggestions.append(SuggestedAction(
                action="verify_identity",
                description="Verify caller's identity with security questions",
                priority="high",
            ))
            suggestions.append(SuggestedAction(
                action="escalate_fraud_team",
                description="Escalate to fraud investigation team if confirmed",
                priority="high",
            ))
        
        elif trigger == HandoffTrigger.SAFETY_EMERGENCY:
            suggestions.append(SuggestedAction(
                action="check_safety",
                description="Immediately confirm caller's safety status",
                priority="urgent",
            ))
            suggestions.append(SuggestedAction(
                action="emergency_services",
                description="Offer to contact emergency services if needed",
                priority="urgent",
            ))
        
        elif trigger == HandoffTrigger.HARASSMENT_REPORT:
            suggestions.append(SuggestedAction(
                action="document_incident",
                description="Document harassment details for investigation",
                priority="high",
            ))
            suggestions.append(SuggestedAction(
                action="safety_measures",
                description="Explain safety measures and block options",
                priority="high",
            ))
        
        elif trigger == HandoffTrigger.HIGH_FRUSTRATION:
            suggestions.append(SuggestedAction(
                action="empathize",
                description="Start with empathy and acknowledge frustration",
                priority="high",
            ))
            suggestions.append(SuggestedAction(
                action="resolve_quickly",
                description="Focus on quick resolution to rebuild trust",
                priority="medium",
            ))
        
        # Based on intent history
        if IntentCategory.PAYMENT_ISSUE in state.high_risk_intents_detected:
            suggestions.append(SuggestedAction(
                action="check_payment",
                description="Review payment history and pending issues",
                priority="high",
                data={"check": "payment_history"},
            ))
        
        # General suggestions
        if state.last_repeated_query:
            suggestions.append(SuggestedAction(
                action="address_query",
                description=f"Address repeated question: '{state.last_repeated_query[:50]}...'",
                priority="high",
            ))
        
        return suggestions
    
    def _get_trigger_description(
        self,
        trigger: HandoffTrigger,
        state: ConversationState,
    ) -> str:
        """Get human-readable trigger description."""
        descriptions = {
            HandoffTrigger.EXPLICIT_REQUEST: "User explicitly requested to speak with a human agent",
            HandoffTrigger.HIGH_FRUSTRATION: f"User sentiment dropped to {state.current_sentiment.value}",
            HandoffTrigger.REPEATED_QUERIES: f"User repeated similar query {state.repeat_count} times",
            HandoffTrigger.FRAUD_DETECTION: "Potential fraud activity detected in conversation",
            HandoffTrigger.SAFETY_EMERGENCY: "Safety or emergency concern raised by user",
            HandoffTrigger.HARASSMENT_REPORT: "User reported harassment incident",
            HandoffTrigger.TOOL_FAILURES: f"Bot encountered {state.tool_failure_count} failures",
            HandoffTrigger.CONFIDENCE_THRESHOLD: f"Escalation confidence reached {state.escalation_confidence:.0%}",
            HandoffTrigger.BOT_STUCK: "Bot unable to progress conversation",
            HandoffTrigger.LONG_CONVERSATION: f"Conversation reached {state.turn_count} turns without resolution",
        }
        return descriptions.get(trigger, "Escalation triggered")
    
    def get_agent_brief(self, alert_id: UUID) -> Optional[Dict[str, Any]]:
        """
        Get the micro-brief for agent display.
        
        This is the quick-glance view shown to agents.
        """
        alert = self.queue.get_by_id(alert_id)
        if not alert:
            # Check active handoffs
            for active in self._active_handoffs.values():
                if active.id == alert_id:
                    alert = active
                    break
        
        if not alert:
            return None
        
        # Calculate confidence trend from sentiment history
        confidence_trend = "stable"
        if alert.detailed_summary:
            if "declining" in alert.detailed_summary.detailed_summary.lower():
                confidence_trend = "declining"
        
        # Get top entities from turns
        top_entities = {}
        for turn in alert.conversation_turns[-5:]:
            if turn.nlu_result and turn.nlu_result.entities:
                top_entities.update(turn.nlu_result.entities)
        
        return {
            "driver_name": alert.driver_info.name,
            "driver_phone_last_4": alert.driver_info.phone_number[-4:] if len(alert.driver_info.phone_number) >= 4 else "****",
            "driver_city": alert.driver_info.city,
            "language": alert.driver_info.preferred_language,
            "top_entities": top_entities,
            "summary": alert.issue_summary,
            "escalation_reason": alert.trigger.value.replace("_", " ").title(),
            "escalation_description": alert.trigger_description,
            "sentiment": alert.sentiment.value,
            "sentiment_score": alert.sentiment_score,
            "suggested_actions": [
                {"action": a.action, "description": a.description, "priority": a.priority}
                for a in alert.next_steps_for_agent
            ],
            "confidence_trend": confidence_trend,
        }
    
    async def assign_agent(
        self,
        alert_id: UUID,
        agent_id: str,
    ) -> Optional[HandoffAlert]:
        """Assign an agent to handle a handoff."""
        alert = self.queue.remove(alert_id)
        if not alert:
            return None
        
        alert.status = HandoffStatus.ASSIGNED
        alert.assigned_agent_id = agent_id
        alert.assigned_at = datetime.utcnow()
        
        self._active_handoffs[alert.call_id] = alert
        
        await self.notifier.notify_update(alert, "assigned")
        
        logger.info(f"Agent {agent_id} assigned to handoff {alert_id}")
        return alert
    
    async def start_handoff_call(self, alert_id: UUID) -> Dict[str, Any]:
        """
        Start the actual call transfer to agent.
        
        This generates a LiveKit token for the human agent to join the room,
        and signals the AI agent to leave.
        """
        from src.core.livekit_token import generate_agent_token, get_livekit_url
        
        # Find the alert
        alert = None
        for active in self._active_handoffs.values():
            if active.id == alert_id:
                alert = active
                break
        
        if not alert:
            raise ValueError(f"Handoff alert {alert_id} not found in active handoffs")
        
        if alert.status != HandoffStatus.ASSIGNED:
            raise ValueError(f"Handoff {alert_id} is not in assigned state")
        
        alert.status = HandoffStatus.IN_PROGRESS
        alert.started_at = datetime.utcnow()
        
        # Generate LiveKit token for the human agent
        agent_token = generate_agent_token(
            room_name=alert.room_name,
            agent_id=alert.assigned_agent_id,
            agent_name=f"Support Agent",
        )
        
        await self.notifier.notify_update(alert, "started")
        
        logger.info(f"Handoff call started for {alert_id}")
        
        return {
            "status": "started",
            "alert_id": str(alert.id),
            "call_id": alert.call_id,
            "room_name": alert.room_name,
            "agent_id": alert.assigned_agent_id,
            # LiveKit connection info for human agent
            "livekit_url": get_livekit_url(),
            "livekit_token": agent_token,
        }
    
    async def complete_handoff(
        self,
        alert_id: UUID,
        resolution: Optional[str] = None,
    ) -> None:
        """Mark a handoff as completed."""
        # Find and remove from active
        alert = None
        for call_id, active in list(self._active_handoffs.items()):
            if active.id == alert_id:
                alert = self._active_handoffs.pop(call_id)
                break
        
        if not alert:
            logger.warning(f"Handoff {alert_id} not found in active handoffs")
            return
        
        alert.status = HandoffStatus.COMPLETED
        alert.completed_at = datetime.utcnow()
        alert.resolution = resolution
        
        self._completed_handoffs.append(alert)
        
        await self.notifier.notify_update(alert, "completed")
        
        logger.info(f"Handoff {alert_id} completed: {resolution}")
    
    def get_handoff_status(self, call_id: str) -> Optional[Dict[str, Any]]:
        """Get handoff status for a call."""
        # Check queue
        alert = self.queue.get_by_call_id(call_id)
        if alert:
            return {
                "status": alert.status.value,
                "queue_position": alert.queue_position,
                "estimated_wait": alert.estimated_wait_seconds,
            }
        
        # Check active
        if call_id in self._active_handoffs:
            alert = self._active_handoffs[call_id]
            return {
                "status": alert.status.value,
                "agent_id": alert.assigned_agent_id,
                "started_at": alert.started_at.isoformat() if alert.started_at else None,
            }
        
        return None
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        alerts = self.queue.get_all()
        
        by_priority = {}
        for p in HandoffPriority:
            by_priority[p.value] = sum(1 for a in alerts if a.priority == p)
        
        # Calculate average wait
        wait_times = [
            (datetime.utcnow() - a.created_at).total_seconds()
            for a in alerts
            if a.status == HandoffStatus.QUEUED
        ]
        avg_wait = sum(wait_times) / len(wait_times) if wait_times else 0
        
        return {
            "total": len(alerts),
            "by_priority": by_priority,
            "avg_wait_seconds": avg_wait,
        }


# Singleton instance
_manager_instance: Optional[HandoffManager] = None


def get_handoff_manager() -> HandoffManager:
    """Get the singleton HandoffManager instance."""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = HandoffManager()
    return _manager_instance
