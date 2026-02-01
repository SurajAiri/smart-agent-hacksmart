"""
Conversation Tracking Frame Processor for Pipecat.

This processor intercepts frames in the pipeline to:
1. Track user transcriptions
2. Track assistant responses
3. Monitor tool calls
4. Trigger escalation checks
5. Handle handoff when confidence threshold is reached
"""
import asyncio
from typing import Optional, Callable, Awaitable
from loguru import logger

from pipecat.frames.frames import (
    Frame,
    TranscriptionFrame,
    TextFrame,
    LLMFullResponseStartFrame,
    LLMFullResponseEndFrame,
    FunctionCallInProgressFrame,
    FunctionCallResultFrame,
    EndFrame,
)
from pipecat.processors.frame_processor import FrameProcessor, FrameDirection

from src.core.models import DriverInfo, HandoffTrigger
from src.core.conversation_tracker import ConversationTracker, get_conversation_tracker
from src.core.escalation_engine import EscalationEngine, get_escalation_engine
from src.core.handoff_manager import HandoffManager, get_handoff_manager


class ConversationTrackingProcessor(FrameProcessor):
    """
    Frame processor that tracks conversation state for handoff detection.
    
    Intercepts:
    - TranscriptionFrame: User speech
    - TextFrame: LLM responses (during streaming)
    - FunctionCallInProgressFrame: Tool calls
    - FunctionCallResultFrame: Tool results
    """
    
    def __init__(
        self,
        call_id: str,
        room_name: str,
        driver_info: Optional[DriverInfo] = None,
        on_handoff_triggered: Optional[Callable[..., Awaitable]] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.call_id = call_id
        self.room_name = room_name
        self.driver_info = driver_info
        self.on_handoff_triggered = on_handoff_triggered
        
        # Get singletons
        self._tracker = get_conversation_tracker()
        self._engine = get_escalation_engine()
        self._handoff_manager = get_handoff_manager()
        
        # Create conversation state
        self._state = self._tracker.create_conversation(
            call_id=call_id,
            room_name=room_name,
            driver_info=driver_info,
        )
        
        # Response accumulator
        self._current_response = ""
        self._in_response = False
        self._current_tool_call: Optional[str] = None
        
        # Handoff state
        self._handoff_triggered = False
        self._handoff_message_sent = False
        
        logger.info(f"ConversationTrackingProcessor initialized for call: {call_id}")
    
    async def process_frame(self, frame: Frame, direction: FrameDirection):
        """Process each frame passing through the pipeline."""
        await super().process_frame(frame, direction)
        
        # Handle different frame types
        if isinstance(frame, TranscriptionFrame):
            await self._handle_transcription(frame)
        
        elif isinstance(frame, LLMFullResponseStartFrame):
            self._in_response = True
            self._current_response = ""
        
        elif isinstance(frame, TextFrame) and self._in_response:
            self._current_response += frame.text
        
        elif isinstance(frame, LLMFullResponseEndFrame):
            await self._handle_response_end()
        
        elif isinstance(frame, FunctionCallInProgressFrame):
            await self._handle_tool_call_start(frame)
        
        elif isinstance(frame, FunctionCallResultFrame):
            await self._handle_tool_call_result(frame)
        
        elif isinstance(frame, EndFrame):
            await self._handle_conversation_end()
        
        # Always pass frame through
        await self.push_frame(frame, direction)
    
    async def _handle_transcription(self, frame: TranscriptionFrame):
        """Handle user transcription."""
        text = frame.text.strip()
        if not text:
            return
        
        logger.debug(f"[{self.call_id}] User: {text}")
        
        # Add to tracker (with NLU analysis)
        turn = self._tracker.add_user_turn(self.call_id, text, analyze=True)
        
        if turn and turn.nlu_result:
            logger.debug(
                f"[{self.call_id}] NLU: sentiment={turn.nlu_result.sentiment.value}, "
                f"intent={turn.nlu_result.intent.value}, "
                f"repeat={turn.nlu_result.is_repeat_query}"
            )
        
        # Check escalation confidence
        await self._check_escalation()
    
    async def _handle_response_end(self):
        """Handle end of LLM response."""
        self._in_response = False
        
        if self._current_response:
            logger.debug(f"[{self.call_id}] Assistant: {self._current_response[:100]}...")
            
            # Add to tracker
            self._tracker.add_assistant_turn(
                self.call_id,
                self._current_response,
                tool_calls=None,  # Tool calls handled separately
            )
        
        self._current_response = ""
    
    async def _handle_tool_call_start(self, frame: FunctionCallInProgressFrame):
        """Handle tool call start."""
        tool_name = frame.function_name
        self._current_tool_call = tool_name
        logger.debug(f"[{self.call_id}] Tool call started: {tool_name}")
    
    async def _handle_tool_call_result(self, frame: FunctionCallResultFrame):
        """Handle tool call result."""
        if self._current_tool_call:
            success = frame.result is not None and "error" not in str(frame.result).lower()
            
            self._tracker.record_tool_call(
                self.call_id,
                self._current_tool_call,
                success=success,
                result=frame.result,
            )
            
            logger.debug(
                f"[{self.call_id}] Tool call completed: {self._current_tool_call} "
                f"(success={success})"
            )
            
            self._current_tool_call = None
            
            # Check escalation after tool failures
            if not success:
                await self._check_escalation()
    
    async def _handle_conversation_end(self):
        """Handle conversation end - cleanup."""
        logger.info(f"[{self.call_id}] Conversation ended, cleaning up")
        self._tracker.remove_conversation(self.call_id)
    
    async def _check_escalation(self):
        """Check if escalation should be triggered."""
        if self._handoff_triggered:
            return
        
        state = self._tracker.get_conversation(self.call_id)
        if not state:
            return
        
        # Compute confidence
        confidence, factors, trigger = self._engine.compute_confidence(state)
        
        logger.debug(
            f"[{self.call_id}] Escalation confidence: {confidence:.2f} "
            f"(threshold: {self._engine.AUTO_ESCALATE_THRESHOLD})"
        )
        
        # Check if we should auto-escalate
        if trigger and self._engine.should_escalate(state):
            await self._trigger_handoff(state, trigger)
        
        # Log warning if preparing
        elif self._engine.should_warn(state):
            logger.warning(
                f"[{self.call_id}] Escalation confidence approaching threshold: "
                f"{confidence:.2f}"
            )
    
    async def _trigger_handoff(self, state, trigger: HandoffTrigger):
        """Trigger handoff to human agent."""
        if self._handoff_triggered:
            return
        
        self._handoff_triggered = True
        
        # Get priority
        priority = self._engine.get_priority(state, trigger)
        
        logger.warning(
            f"[{self.call_id}] HANDOFF TRIGGERED: "
            f"trigger={trigger.value}, priority={priority.value}"
        )
        
        # Create handoff alert
        alert = await self._handoff_manager.trigger_handoff(
            state=state,
            trigger=trigger,
            priority=priority,
        )
        
        logger.info(
            f"[{self.call_id}] Handoff alert created: {alert.id}, "
            f"queue position: {alert.queue_position}"
        )
        
        # Call the callback if provided
        if self.on_handoff_triggered:
            try:
                await self.on_handoff_triggered(alert)
            except Exception as e:
                logger.error(f"Error in handoff callback: {e}")
    
    def get_escalation_status(self) -> dict:
        """Get current escalation status for this conversation."""
        state = self._tracker.get_conversation(self.call_id)
        if not state:
            return {"active": False}
        
        return {
            "active": True,
            "confidence": state.escalation_confidence,
            "factors": state.escalation_factors,
            "triggered": self._handoff_triggered,
            "sentiment": state.current_sentiment.value,
            "repeat_count": state.repeat_count,
            "turn_count": state.turn_count,
        }
