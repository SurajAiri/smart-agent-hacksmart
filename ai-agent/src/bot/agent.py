"""
Voice Agent - The AI agent that handles voice conversations

This module contains the Pipecat pipeline configuration for:
- LiveKit transport (audio in/out)
- Deepgram ASR (speech-to-text)
- OpenAI LLM (conversation)
- ElevenLabs TTS (text-to-speech)
"""
import asyncio
from typing import Optional
from loguru import logger

from livekit import rtc
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.frames.frames import EndFrame, LLMMessagesFrame
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.services.deepgram import DeepgramSTTService
from pipecat.services.openai import OpenAILLMService
from pipecat.services.elevenlabs import ElevenLabsTTSService
from pipecat.transports.services.livekit import LiveKitTransport, LiveKitParams

from src.config.settings import get_settings
from src.events.callback import EventCallback


class VoiceAgent:
    """
    AI Voice Agent using Pipecat pipeline.
    
    Pipeline flow:
    LiveKit Audio In → Deepgram ASR → OpenAI LLM → ElevenLabs TTS → LiveKit Audio Out
    """
    
    def __init__(
        self,
        room_name: str,
        token: str,
        call_id: str,
        livekit_url: str,
    ):
        self.room_name = room_name
        self.token = token
        self.call_id = call_id
        self.livekit_url = livekit_url
        
        self._settings = get_settings()
        self._runner: Optional[PipelineRunner] = None
        self._task: Optional[PipelineTask] = None
        self._callback = EventCallback(call_id)
        
        logger.info(f"VoiceAgent created for room: {room_name}")
    
    async def run(self):
        """
        Start the voice pipeline and run until stopped.
        """
        logger.info(f"Starting VoiceAgent for room: {self.room_name}")
        
        # Create LiveKit transport
        transport = LiveKitTransport(
            url=self.livekit_url,
            token=self.token,
            params=LiveKitParams(
                audio_in_enabled=True,
                audio_out_enabled=True,
                audio_in_sample_rate=16000,
                audio_out_sample_rate=24000,
            ),
        )
        
        # Create ASR service (Deepgram)
        stt = DeepgramSTTService(
            api_key=self._settings.DEEPGRAM_API_KEY,
            language="en",
            model="nova-2",
        )
        
        # Create LLM service (Groq via OpenAI-compatible API)
        llm = OpenAILLMService(
            api_key=self._settings.GROQ_API_KEY,
            model=self._settings.GROQ_MODEL,
            base_url=self._settings.GROQ_BASE_URL,
        )
        
        # Create TTS service (ElevenLabs)
        tts = ElevenLabsTTSService(
            api_key=self._settings.ELEVENLABS_API_KEY,
            voice_id=self._settings.ELEVENLABS_VOICE_ID,
        )
        
        # Create conversation context
        messages = [
            {
                "role": "system",
                "content": self._settings.SYSTEM_PROMPT,
            },
        ]
        context = OpenAILLMContext(messages)
        context_aggregator = llm.create_context_aggregator(context)
        
        # Build the pipeline
        pipeline = Pipeline([
            transport.input(),      # Audio from LiveKit
            stt,                    # Speech to text
            context_aggregator.user(),   # Add user message to context
            llm,                    # Generate response
            tts,                    # Text to speech
            transport.output(),     # Audio to LiveKit
            context_aggregator.assistant(),  # Add assistant message to context
        ])
        
        # Create pipeline task
        self._task = PipelineTask(
            pipeline,
            params=PipelineParams(
                allow_interruptions=True,
                enable_metrics=True,
            ),
        )
        
        # Set up event handlers
        @transport.event_handler("on_participant_connected")
        async def on_participant_connected(transport, participant):
            logger.info(f"Participant connected: {participant.identity}")
            await self._callback.emit_participant_joined(participant.identity)
        
        @transport.event_handler("on_participant_disconnected") 
        async def on_participant_disconnected(transport, participant):
            logger.info(f"Participant disconnected: {participant.identity}")
            await self._callback.emit_participant_left(participant.identity)
        
        # Create and run the pipeline
        self._runner = PipelineRunner()
        
        # Send initial greeting
        greeting_messages = [
            {
                "role": "system", 
                "content": self._settings.SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": "The call has just started. Introduce yourself briefly.",
            },
        ]
        
        await self._task.queue_frames([
            LLMMessagesFrame(greeting_messages),
        ])
        
        logger.info(f"Pipeline running for room: {self.room_name}")
        
        try:
            await self._runner.run(self._task)
        except asyncio.CancelledError:
            logger.info(f"Pipeline cancelled for room: {self.room_name}")
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            await self._callback.emit_error(str(e))
            raise
        finally:
            logger.info(f"Pipeline stopped for room: {self.room_name}")
    
    async def stop(self):
        """
        Stop the voice pipeline.
        """
        logger.info(f"Stopping VoiceAgent for room: {self.room_name}")
        
        if self._task:
            await self._task.queue_frames([EndFrame()])
        
        if self._runner:
            await self._runner.stop_when_done()
