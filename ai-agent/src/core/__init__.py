"""
Core module for conversation tracking and handoff management.

This module provides:
- Conversation state tracking
- Escalation confidence scoring
- Handoff queue management
- Agent brief generation
"""

from src.core.models import (
    ConversationTurn,
    ConversationState,
    HandoffAlert,
    HandoffPriority,
    HandoffStatus,
    HandoffTrigger,
    SentimentLabel,
    IntentCategory,
    DriverInfo,
    ActionTaken,
    SuggestedAction,
    ConversationSummary,
)
from src.core.conversation_tracker import ConversationTracker, get_conversation_tracker
from src.core.escalation_engine import EscalationEngine, get_escalation_engine
from src.core.handoff_manager import HandoffManager, get_handoff_manager
from src.core.tracking_processor import ConversationTrackingProcessor

__all__ = [
    # Models
    "ConversationTurn",
    "ConversationState",
    "HandoffAlert",
    "HandoffPriority",
    "HandoffStatus",
    "HandoffTrigger",
    "SentimentLabel",
    "IntentCategory",
    "DriverInfo",
    "ActionTaken",
    "SuggestedAction",
    "ConversationSummary",
    # Trackers and Managers
    "ConversationTracker",
    "get_conversation_tracker",
    "EscalationEngine",
    "get_escalation_engine",
    "HandoffManager",
    "get_handoff_manager",
    # Processors
    "ConversationTrackingProcessor",
]
