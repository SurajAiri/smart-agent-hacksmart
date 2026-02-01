"""
Conversation Tracker - Tracks conversation state for each active call.

Responsibilities:
- Store conversation turns with NLU analysis
- Detect query repetition using semantic similarity
- Track sentiment over time
- Maintain tool call history
- Trigger escalation engine checks
"""
import re
from datetime import datetime
from difflib import SequenceMatcher
from typing import Dict, Optional, List, Any, Callable
from uuid import UUID

from loguru import logger

from src.core.models import (
    ConversationState,
    ConversationTurn,
    NLUResult,
    DriverInfo,
    SentimentLabel,
    IntentCategory,
    ActionTaken,
)


class ConversationTracker:
    """
    Tracks all active conversations and their states.
    
    Each call_id has its own ConversationState that accumulates
    turns, sentiment history, and escalation signals.
    """
    
    # Similarity threshold for detecting repeated queries
    SIMILARITY_THRESHOLD = 0.7
    
    # Keywords for intent classification
    INTENT_KEYWORDS = {
        IntentCategory.ESCALATION_REQUEST: [
            "agent", "human", "person", "manager", "supervisor", "speak to someone",
            "real person", "customer care", "support", "help me", "transfer",
            "connect me", "talk to", "want human", "need human", "real human",
            # Hindi escalation keywords
            "एजेंट", "इंसान", "मैनेजर", "सुपरवाइजर", "कस्टमर केयर",
            "ह्यूमन", "बात करवाओ", "बात कराओ", "किसी से बात", "असली इंसान",
            "सपोर्ट", "मदद करो", "हेल्प", "ट्रांसफर", "कनेक्ट करो",
            "कस्टमर सर्विस", "सर्विस", "किसी को बुलाओ", "मैनेजर से बात"
        ],
        IntentCategory.FRAUD_REPORT: [
            "fraud", "scam", "cheat", "stolen", "hack", "unauthorized", "fake",
            "धोखा", "फ्रॉड", "चोरी", "हैक"
        ],
        IntentCategory.HARASSMENT: [
            "harassment", "harass", "threaten", "abuse", "misbehave", "inappropriate",
            "उत्पीड़न", "धमकी", "गाली", "बदतमीजी"
        ],
        IntentCategory.SAFETY_CONCERN: [
            "accident", "emergency", "unsafe", "danger", "hurt", "injured", "police",
            "दुर्घटना", "इमरजेंसी", "खतरा", "पुलिस", "चोट"
        ],
        IntentCategory.COMPLAINT: [
            "complaint", "complain", "problem", "issue", "wrong", "bad", "terrible",
            "शिकायत", "समस्या", "गलत", "खराब"
        ],
        IntentCategory.PAYMENT_ISSUE: [
            "payment", "refund", "money", "charge", "deduct", "pay", "bill",
            "पेमेंट", "रिफंड", "पैसे", "चार्ज", "बिल"
        ],
        IntentCategory.CONFUSION: [
            "don't understand", "confused", "what", "how", "why", "explain",
            "समझ नहीं", "confused", "क्या", "कैसे", "क्यों"
        ],
        IntentCategory.APPRECIATION: [
            "thank", "thanks", "great", "helpful", "good", "nice", "appreciate",
            "धन्यवाद", "शुक्रिया", "अच्छा", "बढ़िया"
        ],
    }
    
    # Keywords for sentiment classification
    NEGATIVE_KEYWORDS = [
        "angry", "frustrated", "annoyed", "upset", "terrible", "worst", "hate",
        "pathetic", "useless", "stupid", "waste", "never", "disgusted", "bad",
        # Hindi negative keywords
        "गुस्सा", "परेशान", "बकवास", "बेकार", "घटिया", "नाराज़",
        "गुस्से", "निराशा", "खराब", "बुरा", "चिढ़", "तंग", "थक",
        "पागल", "बर्बाद", "झूठ", "धोखा", "फालतू"
    ]
    
    POSITIVE_KEYWORDS = [
        "thank", "thanks", "great", "good", "nice", "helpful", "appreciate",
        "awesome", "excellent", "perfect", "love", "best",
        "धन्यवाद", "शुक्रिया", "अच्छा", "बढ़िया", "शानदार"
    ]
    
    def __init__(self):
        self._conversations: Dict[str, ConversationState] = {}
        self._on_escalation_callbacks: List[Callable] = []
        logger.info("ConversationTracker initialized")
    
    def create_conversation(
        self,
        call_id: str,
        room_name: str,
        driver_info: Optional[DriverInfo] = None,
    ) -> ConversationState:
        """
        Create a new conversation state for a call.
        
        Args:
            call_id: Unique call identifier
            room_name: LiveKit room name
            driver_info: Optional driver information
            
        Returns:
            New ConversationState
        """
        if call_id in self._conversations:
            logger.warning(f"Conversation already exists for call_id: {call_id}")
            return self._conversations[call_id]
        
        state = ConversationState(
            call_id=call_id,
            room_name=room_name,
            driver_info=driver_info or DriverInfo(phone_number="unknown"),
        )
        self._conversations[call_id] = state
        logger.info(f"Created conversation state for call_id: {call_id}")
        return state
    
    def get_conversation(self, call_id: str) -> Optional[ConversationState]:
        """Get conversation state by call_id."""
        return self._conversations.get(call_id)
    
    def add_user_turn(
        self,
        call_id: str,
        content: str,
        analyze: bool = True,
    ) -> Optional[ConversationTurn]:
        """
        Add a user turn to the conversation.
        
        Args:
            call_id: Call identifier
            content: User's message
            analyze: Whether to run NLU analysis
            
        Returns:
            The created ConversationTurn
        """
        state = self.get_conversation(call_id)
        if not state:
            logger.warning(f"No conversation found for call_id: {call_id}")
            return None
        
        # Run NLU analysis
        nlu_result = None
        if analyze:
            nlu_result = self._analyze_turn(state, content)
        
        # Add turn
        turn = state.add_turn("user", content, nlu_result)
        
        # Track query for repetition detection
        state.query_history.append(content.lower().strip())
        
        logger.debug(
            f"Added user turn for {call_id}: "
            f"sentiment={nlu_result.sentiment if nlu_result else 'N/A'}, "
            f"intent={nlu_result.intent if nlu_result else 'N/A'}"
        )
        
        return turn
    
    def add_assistant_turn(
        self,
        call_id: str,
        content: str,
        tool_calls: Optional[List[str]] = None,
    ) -> Optional[ConversationTurn]:
        """
        Add an assistant turn to the conversation.
        
        Args:
            call_id: Call identifier
            content: Assistant's response
            tool_calls: List of tool names called
            
        Returns:
            The created ConversationTurn
        """
        state = self.get_conversation(call_id)
        if not state:
            logger.warning(f"No conversation found for call_id: {call_id}")
            return None
        
        turn = ConversationTurn(
            role="assistant",
            content=content,
            tool_calls=tool_calls or [],
        )
        state.turns.append(turn)
        state.turn_count += 1
        state.last_activity_at = datetime.utcnow()
        
        return turn
    
    def record_tool_call(
        self,
        call_id: str,
        tool_name: str,
        success: bool,
        result: Any = None,
    ) -> None:
        """Record a tool call for the conversation."""
        state = self.get_conversation(call_id)
        if state:
            state.record_tool_call(tool_name, success, result)
            logger.debug(f"Recorded tool call {tool_name} (success={success}) for {call_id}")
    
    def _analyze_turn(self, state: ConversationState, content: str) -> NLUResult:
        """
        Analyze a user turn for intent, sentiment, and repetition.
        
        This uses simple keyword-based analysis. For production,
        you might want to use an LLM or dedicated NLU service.
        """
        content_lower = content.lower()
        
        # Detect intent
        intent = IntentCategory.OTHER
        intent_confidence = 0.5
        
        for category, keywords in self.INTENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in content_lower:
                    intent = category
                    intent_confidence = 0.8
                    break
            if intent != IntentCategory.OTHER:
                break
        
        # Analyze sentiment
        sentiment, sentiment_score = self._analyze_sentiment(content_lower, state)
        
        # Check for repetition
        is_repeat, similarity = self._check_repetition(state, content_lower)
        
        if is_repeat:
            state.repeat_count += 1
            state.last_repeated_query = content
            # If repeating, might be confused
            if intent == IntentCategory.OTHER:
                intent = IntentCategory.REPEAT_QUERY
        
        return NLUResult(
            intent=intent,
            intent_confidence=intent_confidence,
            sentiment=sentiment,
            sentiment_score=sentiment_score,
            is_repeat_query=is_repeat,
            similarity_to_previous=similarity,
        )
    
    def _analyze_sentiment(
        self,
        content: str,
        state: ConversationState,
    ) -> tuple[SentimentLabel, float]:
        """
        Analyze sentiment of the message.
        
        Returns tuple of (sentiment_label, sentiment_score).
        Score ranges from -1.0 (very negative) to 1.0 (very positive).
        """
        # Count sentiment keywords
        negative_count = sum(1 for kw in self.NEGATIVE_KEYWORDS if kw.lower() in content)
        positive_count = sum(1 for kw in self.POSITIVE_KEYWORDS if kw.lower() in content)
        
        # Check for exclamation marks and caps (frustration indicators)
        exclamation_count = content.count('!')
        caps_ratio = sum(1 for c in content if c.isupper()) / max(len(content), 1)
        
        # Calculate base score
        if negative_count > positive_count:
            base_score = -0.3 * negative_count
        elif positive_count > negative_count:
            base_score = 0.3 * positive_count
        else:
            base_score = 0.0
        
        # Adjust for frustration indicators
        if exclamation_count >= 2:
            base_score -= 0.2
        if caps_ratio > 0.5:
            base_score -= 0.3
        
        # Consider historical trend
        if state.sentiment_history:
            avg_history = sum(state.sentiment_history[-5:]) / len(state.sentiment_history[-5:])
            # If consistently negative, amplify
            if avg_history < -0.3:
                base_score -= 0.1
        
        # Clamp score
        score = max(-1.0, min(1.0, base_score))
        
        # Determine label
        if score <= -0.6:
            label = SentimentLabel.ANGRY
        elif score <= -0.3:
            label = SentimentLabel.FRUSTRATED
        elif score < -0.1:
            label = SentimentLabel.NEGATIVE
        elif score <= 0.3:
            label = SentimentLabel.NEUTRAL
        else:
            label = SentimentLabel.POSITIVE
        
        return label, score
    
    def _check_repetition(
        self,
        state: ConversationState,
        content: str,
    ) -> tuple[bool, float]:
        """
        Check if the current query is similar to previous queries.
        
        Returns tuple of (is_repeat, max_similarity).
        """
        if not state.query_history:
            return False, 0.0
        
        # Clean the content
        content_clean = self._clean_for_comparison(content)
        
        max_similarity = 0.0
        for prev_query in state.query_history[-10:]:  # Check last 10 queries
            prev_clean = self._clean_for_comparison(prev_query)
            similarity = SequenceMatcher(None, content_clean, prev_clean).ratio()
            max_similarity = max(max_similarity, similarity)
        
        is_repeat = max_similarity >= self.SIMILARITY_THRESHOLD
        return is_repeat, max_similarity
    
    def _clean_for_comparison(self, text: str) -> str:
        """Clean text for similarity comparison."""
        # Remove punctuation and extra spaces
        text = re.sub(r'[^\w\s]', '', text.lower())
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def get_conversation_summary(self, call_id: str) -> Optional[Dict[str, Any]]:
        """Get a summary of the conversation for handoff."""
        state = self.get_conversation(call_id)
        if not state:
            return None
        
        # Get last 5 user queries
        user_turns = [t for t in state.turns if t.role == "user"]
        last_queries = [t.content for t in user_turns[-5:]]
        
        # Get tool calls made
        tool_summary = {}
        for action in state.actions_taken:
            if action.action.startswith("tool_call:"):
                tool_name = action.action.replace("tool_call:", "")
                if tool_name not in tool_summary:
                    tool_summary[tool_name] = {"count": 0, "success": 0}
                tool_summary[tool_name]["count"] += 1
                if action.success:
                    tool_summary[tool_name]["success"] += 1
        
        return {
            "call_id": call_id,
            "turn_count": state.turn_count,
            "sentiment": state.current_sentiment.value,
            "sentiment_score": state.sentiment_score,
            "sentiment_trend": state.sentiment_trend,
            "current_intent": state.current_intent.value if state.current_intent else None,
            "high_risk_intents": [i.value for i in state.high_risk_intents_detected],
            "repeat_count": state.repeat_count,
            "tool_calls": tool_summary,
            "last_queries": last_queries,
            "escalation_confidence": state.escalation_confidence,
            "duration_seconds": (datetime.utcnow() - state.started_at).total_seconds(),
        }
    
    def remove_conversation(self, call_id: str) -> Optional[ConversationState]:
        """Remove and return a conversation (e.g., when call ends)."""
        return self._conversations.pop(call_id, None)
    
    def get_active_conversations(self) -> List[str]:
        """Get list of all active call_ids."""
        return list(self._conversations.keys())
    
    def register_escalation_callback(self, callback: Callable) -> None:
        """Register a callback to be called when escalation is triggered."""
        self._on_escalation_callbacks.append(callback)


# Singleton instance
_tracker_instance: Optional[ConversationTracker] = None


def get_conversation_tracker() -> ConversationTracker:
    """Get the singleton ConversationTracker instance."""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = ConversationTracker()
    return _tracker_instance
