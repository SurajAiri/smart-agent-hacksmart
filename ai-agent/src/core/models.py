"""
Core data models for the handoff system.

Defines Pydantic models for:
- Conversation turns and state
- Sentiment and intent analysis
- Handoff alerts and queue management
- Agent briefing structures
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# ============================================================================
# Enums
# ============================================================================

class SentimentLabel(str, Enum):
    """Sentiment classification labels."""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    FRUSTRATED = "frustrated"
    ANGRY = "angry"


class IntentCategory(str, Enum):
    """High-level intent categories for escalation detection."""
    GREETING = "greeting"
    TRIP_INQUIRY = "trip_inquiry"
    FAQ_QUERY = "faq_query"
    COMPLAINT = "complaint"
    PAYMENT_ISSUE = "payment_issue"
    SAFETY_CONCERN = "safety_concern"
    FRAUD_REPORT = "fraud_report"
    HARASSMENT = "harassment"
    ACCOUNT_ISSUE = "account_issue"
    ESCALATION_REQUEST = "escalation_request"
    CONFUSION = "confusion"
    REPEAT_QUERY = "repeat_query"
    APPRECIATION = "appreciation"
    FAREWELL = "farewell"
    OTHER = "other"


class HandoffTrigger(str, Enum):
    """Reasons for triggering a handoff."""
    EXPLICIT_REQUEST = "explicit_request"          # User asked for human
    HIGH_FRUSTRATION = "high_frustration"          # Sentiment dropped critically
    REPEATED_QUERIES = "repeated_queries"          # Same question asked 3+ times
    FRAUD_DETECTION = "fraud_detection"            # Fraud-related intent
    SAFETY_EMERGENCY = "safety_emergency"          # Safety/accident concern
    HARASSMENT_REPORT = "harassment_report"        # Harassment complaint
    TOOL_FAILURES = "tool_failures"                # Multiple tool failures
    CONFIDENCE_THRESHOLD = "confidence_threshold"  # Overall confidence dropped
    BOT_STUCK = "bot_stuck"                        # Bot unable to progress
    LONG_CONVERSATION = "long_conversation"        # Too many turns without resolution


class HandoffPriority(str, Enum):
    """Priority levels for handoff queue."""
    URGENT = "urgent"      # Immediate attention (safety, fraud)
    HIGH = "high"          # High priority (explicit request, high frustration)
    MEDIUM = "medium"      # Medium priority (repeated failures)
    LOW = "low"            # Low priority (general unresolved)


class HandoffStatus(str, Enum):
    """Status of a handoff request."""
    QUEUED = "queued"           # In queue, waiting for agent
    ASSIGNED = "assigned"       # Agent assigned, call pending
    IN_PROGRESS = "in_progress" # Agent on call with user
    COMPLETED = "completed"     # Successfully resolved
    ABANDONED = "abandoned"     # User disconnected before handoff
    CANCELLED = "cancelled"     # Handoff cancelled


# ============================================================================
# Core Data Models
# ============================================================================

class DriverInfo(BaseModel):
    """Information about the driver/user on the call."""
    phone_number: str
    name: Optional[str] = None
    driver_id: Optional[str] = None
    city: Optional[str] = None
    preferred_language: str = "hi-IN"
    subscription_plan: Optional[str] = None
    account_status: str = "active"
    total_trips: int = 0
    rating: Optional[float] = None


class NLUResult(BaseModel):
    """Natural Language Understanding result for a turn."""
    intent: IntentCategory = IntentCategory.OTHER
    intent_confidence: float = 0.5
    sentiment: SentimentLabel = SentimentLabel.NEUTRAL
    sentiment_score: float = 0.0  # -1.0 (very negative) to 1.0 (very positive)
    entities: Dict[str, Any] = Field(default_factory=dict)
    is_repeat_query: bool = False
    similarity_to_previous: float = 0.0


class ConversationTurn(BaseModel):
    """A single turn in the conversation."""
    id: UUID = Field(default_factory=uuid4)
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    nlu_result: Optional[NLUResult] = None
    tool_calls: List[str] = Field(default_factory=list)
    tool_results: Dict[str, Any] = Field(default_factory=dict)
    tool_success: Optional[bool] = None


class ActionTaken(BaseModel):
    """Action taken by the bot during conversation."""
    action: str
    description: str
    success: bool = True
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SuggestedAction(BaseModel):
    """Suggested action for human agent."""
    action: str
    description: str
    priority: str = "medium"  # high, medium, low
    data: Dict[str, Any] = Field(default_factory=dict)


class ConversationSummary(BaseModel):
    """Summary of the conversation for agent handoff."""
    one_line_summary: str
    detailed_summary: str
    primary_issue: str
    secondary_issues: List[str] = Field(default_factory=list)
    stuck_on: Optional[str] = None
    topics_discussed: List[str] = Field(default_factory=list)
    resolution_attempted: bool = False


class ConversationState(BaseModel):
    """
    Complete state of a conversation for tracking.
    
    This is the central data structure that tracks everything
    needed for escalation detection and handoff generation.
    """
    id: UUID = Field(default_factory=uuid4)
    call_id: str
    room_name: str
    
    # Driver/User info
    driver_info: DriverInfo
    
    # Conversation tracking
    turns: List[ConversationTurn] = Field(default_factory=list)
    turn_count: int = 0
    
    # Sentiment tracking
    current_sentiment: SentimentLabel = SentimentLabel.NEUTRAL
    sentiment_score: float = 0.0
    sentiment_history: List[float] = Field(default_factory=list)
    sentiment_trend: str = "stable"  # improving, stable, declining
    
    # Intent tracking
    intent_history: List[IntentCategory] = Field(default_factory=list)
    current_intent: Optional[IntentCategory] = None
    high_risk_intents_detected: List[IntentCategory] = Field(default_factory=list)
    
    # Repetition detection
    query_history: List[str] = Field(default_factory=list)
    repeat_count: int = 0
    last_repeated_query: Optional[str] = None
    
    # Tool usage tracking
    tool_calls_made: List[str] = Field(default_factory=list)
    tool_success_count: int = 0
    tool_failure_count: int = 0
    actions_taken: List[ActionTaken] = Field(default_factory=list)
    
    # Escalation tracking
    escalation_confidence: float = 0.0
    escalation_factors: Dict[str, float] = Field(default_factory=dict)
    escalation_triggered: bool = False
    escalation_trigger: Optional[HandoffTrigger] = None
    
    # Timestamps
    started_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity_at: datetime = Field(default_factory=datetime.utcnow)
    
    def add_turn(self, role: str, content: str, nlu_result: Optional[NLUResult] = None) -> ConversationTurn:
        """Add a new turn to the conversation."""
        turn = ConversationTurn(
            role=role,
            content=content,
            nlu_result=nlu_result,
        )
        self.turns.append(turn)
        self.turn_count += 1
        self.last_activity_at = datetime.utcnow()
        
        if nlu_result:
            self.update_from_nlu(nlu_result)
        
        return turn
    
    def update_from_nlu(self, nlu_result: NLUResult) -> None:
        """Update state based on NLU result."""
        # Update sentiment
        self.sentiment_score = nlu_result.sentiment_score
        self.current_sentiment = nlu_result.sentiment
        self.sentiment_history.append(nlu_result.sentiment_score)
        
        # Calculate trend
        if len(self.sentiment_history) >= 3:
            recent = self.sentiment_history[-3:]
            if recent[-1] < recent[0] - 0.2:
                self.sentiment_trend = "declining"
            elif recent[-1] > recent[0] + 0.2:
                self.sentiment_trend = "improving"
            else:
                self.sentiment_trend = "stable"
        
        # Update intent
        self.current_intent = nlu_result.intent
        self.intent_history.append(nlu_result.intent)
        
        # Track high-risk intents
        high_risk = [
            IntentCategory.FRAUD_REPORT,
            IntentCategory.HARASSMENT,
            IntentCategory.SAFETY_CONCERN,
            IntentCategory.ESCALATION_REQUEST,
        ]
        if nlu_result.intent in high_risk:
            self.high_risk_intents_detected.append(nlu_result.intent)
        
        # Track repetitions
        if nlu_result.is_repeat_query:
            self.repeat_count += 1
    
    def record_tool_call(self, tool_name: str, success: bool, result: Any = None) -> None:
        """Record a tool call."""
        self.tool_calls_made.append(tool_name)
        if success:
            self.tool_success_count += 1
        else:
            self.tool_failure_count += 1
        
        self.actions_taken.append(ActionTaken(
            action=f"tool_call:{tool_name}",
            description=f"Called {tool_name}",
            success=success,
        ))


class HandoffAlert(BaseModel):
    """
    A handoff alert representing a conversation that needs human attention.
    
    This is what gets added to the queue and shown to agents.
    """
    id: UUID = Field(default_factory=uuid4)
    conversation_id: UUID
    call_id: str
    room_name: str
    
    # Trigger info
    trigger: HandoffTrigger
    trigger_description: str
    priority: HandoffPriority
    status: HandoffStatus = HandoffStatus.QUEUED
    
    # Driver info
    driver_info: DriverInfo
    
    # Conversation context
    intent_history: List[IntentCategory] = Field(default_factory=list)
    current_intent: Optional[IntentCategory] = None
    sentiment: SentimentLabel = SentimentLabel.NEUTRAL
    sentiment_score: float = 0.0
    
    # Summary for agent
    issue_summary: str
    detailed_summary: Optional[ConversationSummary] = None
    conversation_turns: List[ConversationTurn] = Field(default_factory=list)
    
    # Bot actions
    actions_taken_by_bot: List[ActionTaken] = Field(default_factory=list)
    next_steps_for_agent: List[SuggestedAction] = Field(default_factory=list)
    
    # Queue info
    queue_position: Optional[int] = None
    estimated_wait_seconds: Optional[int] = None
    
    # Assignment
    assigned_agent_id: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    assigned_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Resolution
    resolution: Optional[str] = None
    notes: Optional[str] = None
