"""
Escalation Confidence Engine - Calculates likelihood of needing human handoff.

Uses multiple signals to compute a confidence score:
- Query repetition
- Sentiment trend
- High-risk intent detection
- Tool failure rate
- Conversation length
- Explicit escalation requests
"""
from typing import Optional, Tuple, Dict, Any
from loguru import logger

from src.core.models import (
    ConversationState,
    HandoffTrigger,
    HandoffPriority,
    IntentCategory,
    SentimentLabel,
)


class EscalationEngine:
    """
    Computes escalation confidence and determines if handoff is needed.
    
    The engine uses weighted factors to calculate an overall confidence
    score that the conversation needs human intervention.
    """
    
    # Factor weights (must sum to 1.0)
    WEIGHTS = {
        "repetition": 0.20,       # Repeated queries indicate bot stuck
        "sentiment": 0.20,        # Negative sentiment trend
        "high_risk_intent": 0.25, # Fraud, harassment, safety
        "tool_failures": 0.10,    # Tool call failures
        "turn_count": 0.10,       # Long conversations without resolution
        "explicit_request": 0.15, # User explicitly asking for human
    }
    
    # Thresholds
    AUTO_ESCALATE_THRESHOLD = 0.75   # Automatically trigger handoff
    PREPARE_HANDOFF_THRESHOLD = 0.55  # Start preparing handoff
    
    # Configuration
    MAX_REPEATS_BEFORE_ESCALATE = 3
    MAX_TURNS_BEFORE_PENALTY = 10
    MAX_TOOL_FAILURES_BEFORE_PENALTY = 2
    
    # High-risk intents that trigger immediate escalation
    IMMEDIATE_ESCALATION_INTENTS = [
        IntentCategory.SAFETY_CONCERN,
        IntentCategory.HARASSMENT,
        IntentCategory.FRAUD_REPORT,
    ]
    
    # High-risk intents that increase confidence
    HIGH_RISK_INTENTS = [
        IntentCategory.COMPLAINT,
        IntentCategory.PAYMENT_ISSUE,
        IntentCategory.ACCOUNT_ISSUE,
        IntentCategory.ESCALATION_REQUEST,
    ]
    
    def __init__(self):
        logger.info("EscalationEngine initialized")
    
    def compute_confidence(
        self,
        state: ConversationState,
    ) -> Tuple[float, Dict[str, float], Optional[HandoffTrigger]]:
        """
        Compute escalation confidence score.
        
        Args:
            state: Current conversation state
            
        Returns:
            Tuple of (confidence_score, factor_breakdown, trigger_if_any)
        """
        factors = {}
        trigger = None
        
        # 1. Check for immediate escalation (safety, fraud, harassment)
        immediate_trigger = self._check_immediate_escalation(state)
        if immediate_trigger:
            # Immediate escalation needed
            factors = {k: 1.0 for k in self.WEIGHTS.keys()}
            state.escalation_confidence = 1.0
            state.escalation_factors = factors
            return 1.0, factors, immediate_trigger
        
        # 2. Calculate repetition factor
        factors["repetition"] = self._calc_repetition_factor(state)
        
        # 3. Calculate sentiment factor
        factors["sentiment"] = self._calc_sentiment_factor(state)
        
        # 4. Calculate high-risk intent factor
        factors["high_risk_intent"] = self._calc_intent_factor(state)
        
        # 5. Calculate tool failure factor
        factors["tool_failures"] = self._calc_tool_failure_factor(state)
        
        # 6. Calculate turn count factor
        factors["turn_count"] = self._calc_turn_count_factor(state)
        
        # 7. Calculate explicit request factor
        factors["explicit_request"] = self._calc_explicit_request_factor(state)
        
        # Compute weighted score
        confidence = sum(
            factors[key] * weight
            for key, weight in self.WEIGHTS.items()
        )
        
        # Determine trigger if threshold exceeded
        if confidence >= self.AUTO_ESCALATE_THRESHOLD:
            trigger = self._determine_trigger(state, factors)
        
        # Update state
        state.escalation_confidence = confidence
        state.escalation_factors = factors
        
        logger.debug(
            f"Escalation confidence for {state.call_id}: {confidence:.2f} "
            f"(factors: {factors})"
        )
        
        return confidence, factors, trigger
    
    def _check_immediate_escalation(
        self,
        state: ConversationState,
    ) -> Optional[HandoffTrigger]:
        """Check for conditions requiring immediate escalation."""
        # Check for immediate escalation intents
        for intent in state.high_risk_intents_detected:
            if intent == IntentCategory.SAFETY_CONCERN:
                return HandoffTrigger.SAFETY_EMERGENCY
            elif intent == IntentCategory.HARASSMENT:
                return HandoffTrigger.HARASSMENT_REPORT
            elif intent == IntentCategory.FRAUD_REPORT:
                return HandoffTrigger.FRAUD_DETECTION
        
        return None
    
    def _calc_repetition_factor(self, state: ConversationState) -> float:
        """Calculate repetition factor (0.0 to 1.0)."""
        if state.repeat_count == 0:
            return 0.0
        elif state.repeat_count == 1:
            return 0.3
        elif state.repeat_count == 2:
            return 0.6
        else:
            return 1.0  # 3+ repeats = max penalty
    
    def _calc_sentiment_factor(self, state: ConversationState) -> float:
        """Calculate sentiment factor based on current and trend."""
        factor = 0.0
        
        # Current sentiment contribution
        if state.current_sentiment == SentimentLabel.ANGRY:
            factor = 0.8
        elif state.current_sentiment == SentimentLabel.FRUSTRATED:
            factor = 0.6
        elif state.current_sentiment == SentimentLabel.NEGATIVE:
            factor = 0.3
        elif state.current_sentiment == SentimentLabel.NEUTRAL:
            factor = 0.0
        else:
            factor = 0.0  # Positive reduces risk
        
        # Trend adjustment
        if state.sentiment_trend == "declining":
            factor = min(1.0, factor + 0.2)
        elif state.sentiment_trend == "improving":
            factor = max(0.0, factor - 0.1)
        
        # Historical sentiment check
        if len(state.sentiment_history) >= 3:
            negative_ratio = sum(1 for s in state.sentiment_history if s < -0.2) / len(state.sentiment_history)
            if negative_ratio > 0.5:
                factor = min(1.0, factor + 0.2)
        
        return factor
    
    def _calc_intent_factor(self, state: ConversationState) -> float:
        """Calculate high-risk intent factor."""
        if not state.high_risk_intents_detected:
            # Check for complaint/payment/account issues
            if state.current_intent in self.HIGH_RISK_INTENTS:
                return 0.4
            return 0.0
        
        # Has high-risk intents
        count = len(state.high_risk_intents_detected)
        if count >= 2:
            return 1.0
        return 0.7
    
    def _calc_tool_failure_factor(self, state: ConversationState) -> float:
        """Calculate tool failure factor."""
        if state.tool_failure_count == 0:
            return 0.0
        
        total_calls = state.tool_success_count + state.tool_failure_count
        if total_calls == 0:
            return 0.0
        
        failure_rate = state.tool_failure_count / total_calls
        
        if state.tool_failure_count >= self.MAX_TOOL_FAILURES_BEFORE_PENALTY:
            return min(1.0, failure_rate + 0.3)
        
        return failure_rate
    
    def _calc_turn_count_factor(self, state: ConversationState) -> float:
        """Calculate turn count penalty for long conversations."""
        if state.turn_count <= 6:
            return 0.0
        elif state.turn_count <= self.MAX_TURNS_BEFORE_PENALTY:
            # Gradual increase
            return (state.turn_count - 6) / (self.MAX_TURNS_BEFORE_PENALTY - 6) * 0.5
        else:
            # Beyond max, full penalty
            return 1.0
    
    def _calc_explicit_request_factor(self, state: ConversationState) -> float:
        """Calculate explicit escalation request factor."""
        # Check if escalation request intent detected
        if IntentCategory.ESCALATION_REQUEST in state.intent_history:
            return 1.0
        return 0.0
    
    def _determine_trigger(
        self,
        state: ConversationState,
        factors: Dict[str, float],
    ) -> HandoffTrigger:
        """Determine the primary trigger for escalation."""
        # Find the highest factor
        max_factor = max(factors.items(), key=lambda x: x[1])
        
        trigger_map = {
            "explicit_request": HandoffTrigger.EXPLICIT_REQUEST,
            "high_risk_intent": HandoffTrigger.CONFIDENCE_THRESHOLD,  # Will be overridden by specific
            "repetition": HandoffTrigger.REPEATED_QUERIES,
            "sentiment": HandoffTrigger.HIGH_FRUSTRATION,
            "tool_failures": HandoffTrigger.TOOL_FAILURES,
            "turn_count": HandoffTrigger.LONG_CONVERSATION,
        }
        
        return trigger_map.get(max_factor[0], HandoffTrigger.CONFIDENCE_THRESHOLD)
    
    def get_priority(
        self,
        state: ConversationState,
        trigger: HandoffTrigger,
    ) -> HandoffPriority:
        """Determine handoff priority based on trigger and state."""
        # Urgent triggers
        if trigger in [
            HandoffTrigger.SAFETY_EMERGENCY,
            HandoffTrigger.HARASSMENT_REPORT,
            HandoffTrigger.FRAUD_DETECTION,
        ]:
            return HandoffPriority.URGENT
        
        # High priority triggers
        if trigger == HandoffTrigger.EXPLICIT_REQUEST:
            return HandoffPriority.HIGH
        
        if trigger == HandoffTrigger.HIGH_FRUSTRATION:
            if state.current_sentiment == SentimentLabel.ANGRY:
                return HandoffPriority.HIGH
            return HandoffPriority.MEDIUM
        
        # Medium priority
        if trigger in [
            HandoffTrigger.REPEATED_QUERIES,
            HandoffTrigger.TOOL_FAILURES,
        ]:
            return HandoffPriority.MEDIUM
        
        # Default to low
        return HandoffPriority.LOW
    
    def should_warn(self, state: ConversationState) -> bool:
        """Check if we should start preparing for handoff."""
        return state.escalation_confidence >= self.PREPARE_HANDOFF_THRESHOLD
    
    def should_escalate(self, state: ConversationState) -> bool:
        """Check if automatic escalation should be triggered."""
        return state.escalation_confidence >= self.AUTO_ESCALATE_THRESHOLD


# Singleton instance
_engine_instance: Optional[EscalationEngine] = None


def get_escalation_engine() -> EscalationEngine:
    """Get the singleton EscalationEngine instance."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = EscalationEngine()
    return _engine_instance
