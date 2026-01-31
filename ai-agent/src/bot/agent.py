"""
Voice Agent - The AI agent that handles voice conversations

This module contains the Pipecat pipeline configuration using 
pluggable providers for LLM, TTS, and ASR.

Pipeline flow:
LiveKit Audio In → VAD → ASR → LLM → TTS → LiveKit Audio Out
"""
import asyncio
import traceback
from typing import Optional
from loguru import logger

from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.frames.frames import EndFrame, LLMMessagesFrame
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.transports.livekit.transport import LiveKitTransport, LiveKitParams
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams

from src.config.settings import get_settings
from src.events.callback import EventCallback
from src.providers.registry import get_llm_provider, get_tts_provider, get_asr_provider
from src.tools.definitions import get_tools_list
from src.tools.handlers import register_tools


class VoiceAgent:
    """
    AI Voice Agent using Pipecat pipeline with pluggable providers.
    
    Providers are configured via settings:
    - LLM_PROVIDER: LLM service (default: "langchain")
    - TTS_PROVIDER: TTS service (default: "elevenlabs")
    - ASR_PROVIDER: ASR service (default: "deepgram")
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
        logger.info("=" * 60)
        logger.info(f"VoiceAgent.run() STARTED for room: {self.room_name}")
        logger.info("=" * 60)
        logger.info(f"LiveKit URL: {self.livekit_url}")
        logger.info(f"Token length: {len(self.token) if self.token else 0}")
        logger.info(f"Providers - LLM: {self._settings.LLM_PROVIDER}, TTS: {self._settings.TTS_PROVIDER}, ASR: {self._settings.ASR_PROVIDER}")
        
        try:
            # Create LiveKit transport with VAD for interruption detection
            logger.info("Creating LiveKit transport...")
            transport = LiveKitTransport(
                url=self.livekit_url,
                token=self.token,
                room_name=self.room_name,
                params=LiveKitParams(
                    audio_in_enabled=True,
                    audio_out_enabled=True,
                    audio_in_sample_rate=16000,
                    audio_out_sample_rate=24000,
                    vad_analyzer=SileroVADAnalyzer(params=VADParams(
                        min_volume=0.5,       # Higher threshold to filter noise (default 0.6)
                        start_secs=0.2,       # Require 200ms of speech to start (reduces false positives)
                        stop_secs=0.5,        # Wait 500ms of silence before stopping (more natural)
                        confidence=0.7,       # Higher confidence threshold
                    )),
                ),
            )
            logger.info(f"LiveKit transport created: {transport}")
            
            # Create services from providers
            logger.info(f"Creating ASR service with provider: {self._settings.ASR_PROVIDER}")
            asr_provider = get_asr_provider(self._settings.ASR_PROVIDER)
            logger.debug(f"ASR provider: {asr_provider}")
            stt = asr_provider.create_service(self._settings)
            logger.info(f"STT service created: {stt}")
            
            logger.info(f"Creating LLM service with provider: {self._settings.LLM_PROVIDER}")
            llm_provider = get_llm_provider(self._settings.LLM_PROVIDER)
            logger.debug(f"LLM provider: {llm_provider}")
            llm = llm_provider.create_service(self._settings)
            logger.info(f"LLM service created: {llm}")
            
            logger.info(f"Creating TTS service with provider: {self._settings.TTS_PROVIDER}")
            tts_provider = get_tts_provider(self._settings.TTS_PROVIDER)
            logger.debug(f"TTS provider: {tts_provider}")
            tts = tts_provider.create_service(self._settings)
            logger.info(f"TTS service created: {tts}")
            
            # Register tool handlers with the LLM service
            logger.info("Registering tools with LLM service...")
            register_tools(llm)
            
            # Create conversation context with tools
            logger.info("Creating conversation context with tools...")
            messages = [
                {
                    "role": "system",
                    "content": self._settings.SYSTEM_PROMPT,
                },
            ]
            context = OpenAILLMContext(messages, tools=get_tools_list())
            context_aggregator = llm.create_context_aggregator(context)
            logger.info(f"Context aggregator created with {len(get_tools_list())} tools")
            
            # Build the pipeline
            logger.info("Building pipeline...")
            pipeline = Pipeline([
                transport.input(),              # Audio from LiveKit
                stt,                            # Speech to text
                context_aggregator.user(),      # Add user message to context
                llm,                            # Generate response
                tts,                            # Text to speech
                transport.output(),             # Audio to LiveKit
                context_aggregator.assistant(), # Add assistant message to context
            ])
            logger.info(f"Pipeline built: {pipeline}")
            
            # Create pipeline task
            logger.info("Creating pipeline task...")
            self._task = PipelineTask(
                pipeline,
                params=PipelineParams(
                    allow_interruptions=True,
                    enable_metrics=True,
                ),
            )
            logger.info(f"Pipeline task created: {self._task}")
            
            # Set up event handlers
            @transport.event_handler("on_participant_connected")
            async def on_participant_connected(transport, participant):
                logger.info(f"EVENT: Participant connected: {participant.identity}")
                await self._callback.emit_participant_joined(participant.identity)
            
            @transport.event_handler("on_participant_disconnected") 
            async def on_participant_disconnected(transport, participant):
                logger.info(f"EVENT: Participant disconnected: {participant.identity}")
                await self._callback.emit_participant_left(participant.identity)
            
            # Create and run the pipeline
            logger.info("Creating pipeline runner...")
            self._runner = PipelineRunner()
            logger.info(f"Pipeline runner created: {self._runner}")
            
            # Send initial greeting
            logger.info("Preparing initial greeting...")
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
            
            logger.info("Queueing greeting frames...")
            await self._task.queue_frames([
                LLMMessagesFrame(greeting_messages),
            ])
            logger.info("Greeting frames queued")
            
            logger.info(f"Starting pipeline runner for room: {self.room_name}")
            logger.info("Calling self._runner.run(self._task)...")
            
            await self._runner.run(self._task)
            
            logger.info(f"Pipeline runner completed for room: {self.room_name}")
            
        except asyncio.CancelledError:
            logger.info(f"Pipeline cancelled for room: {self.room_name}")
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            logger.error(f"Traceback:\n{traceback.format_exc()}")
            await self._callback.emit_error(str(e))
            raise
        finally:
            logger.info(f"Pipeline stopped for room: {self.room_name}")
    
    async def stop(self):
        """
        Stop the voice pipeline and disconnect from LiveKit.
        """
        logger.info(f"Stopping VoiceAgent for room: {self.room_name}")
        
        try:
            # Queue end frame to signal pipeline to stop
            if self._task:
                await self._task.queue_frames([EndFrame()])
            
            # Wait for runner to stop with a timeout
            if self._runner:
                try:
                    # Use asyncio.wait_for with timeout to prevent hanging
                    await asyncio.wait_for(self._runner.stop_when_done(), timeout=5.0)
                except asyncio.TimeoutError:
                    logger.warning(f"Runner stop timeout for room: {self.room_name}, forcing stop")
                    # Force cancel if timeout
                    if hasattr(self._runner, 'cancel'):
                        self._runner.cancel()
        except Exception as e:
            logger.error(f"Error stopping agent: {e}")
        finally:
            logger.info(f"VoiceAgent stopped for room: {self.room_name}")
