#
# Copyright (c) 2024-2026, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""Interruptible voice bot using Gnani Vachana STT + TTS on Pipecat.

Demonstrates real-time Indian-language speech recognition and synthesis
via the ``pipecat-gnani`` package (``pipecat.services.gnani`` namespace).

Prerequisites::

    You need a Gnani API key. `Gnani APIs <https://app.gnani.ai/voice>`_ have this.

    Set your credentials as environment variables::

        export GNANI_API_KEY="your-api-key"
        export GROQ_API_KEY="your-groq-api-key"

Install::

    pip install "pipecat-ai[gnani,daily,groq,silero,runner,webrtc,websocket]"

Run::

    uv run python examples/foundational/07x-interruptible-gnani.py -t webrtc

TTS / STT variants (swap imports in ``run_bot``):

- ``GnaniHttpSTTService`` — REST STT (requires ``aiohttp_session``)
- ``GnaniSTTService`` — WebSocket streaming STT (default below)
- ``GnaniHttpTTSService`` — REST TTS (requires ``aiohttp_session``)
- ``GnaniSSETTSService`` — SSE streaming TTS (requires ``aiohttp_session``)
- ``GnaniTTSService`` — WebSocket streaming TTS with interruption (default below)

Voices: Pranav, Kaveri, Shubhra, Deepak (timbre-v2.0); 42 voices for timbre-v2.5
Docs: https://docs.gnani.ai/api/introduction/introduction
"""

import os

from dotenv import load_dotenv
from loguru import logger

from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.evals.transport import EvalTransportParams
from pipecat.frames.frames import LLMRunFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.worker import PipelineParams, PipelineWorker
from pipecat.processors.aggregators.llm_context import LLMContext
from pipecat.processors.aggregators.llm_response_universal import (
    LLMContextAggregatorPair,
    LLMUserAggregatorParams,
)
from pipecat.runner.types import RunnerArguments
from pipecat.runner.utils import create_transport
from pipecat.services.gnani import GnaniSTTService, GnaniTTSService
from pipecat.services.groq.llm import GroqLLMService
from pipecat.transcriptions.language import Language
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.transports.daily.transport import DailyParams
from pipecat.transports.websocket.fastapi import FastAPIWebsocketParams
from pipecat.workers.runner import WorkerRunner

load_dotenv(override=True)

# We use lambdas to defer transport parameter creation until the transport
# type is selected at runtime.
transport_params = {
    "eval": lambda: EvalTransportParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
    ),
    "daily": lambda: DailyParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
    ),
    "twilio": lambda: FastAPIWebsocketParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
    ),
    "webrtc": lambda: TransportParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
    ),
}


async def run_bot(transport: BaseTransport, runner_args: RunnerArguments):
    logger.info("Starting interruptible bot with Gnani STT + TTS")

    gnani_api_key = os.environ["GNANI_API_KEY"]

    # ── STT: WebSocket streaming (real-time, built-in VAD events) ──────────
    # language options: Language.AS_IN, BN_IN, EN_IN, GU_IN, HI_IN, KN_IN,
    #   ML_IN, MR_IN, OR_IN, PA_IN, TA_IN, TE_IN
    stt = GnaniSTTService(
        api_key=gnani_api_key,
        sample_rate=16000,
        settings=GnaniSTTService.Settings(
            language=Language.EN_IN,
        ),
    )

    # ── TTS: WebSocket streaming (lowest latency, supports interruption) ───
    # timbre-v2.0 (default): Pranav, Kaveri, Shubhra, Deepak
    # timbre-v2.5: 42 voices — set model and language in Settings (required for v2.5)
    # see https://docs.gnani.ai/api/TTS/tts-sse#available-voices
    tts = GnaniTTSService(
        api_key=gnani_api_key,
        sample_rate=16000,
        settings=GnaniTTSService.Settings(
            voice="Nalini",
            model="timbre-v2.5",
            language=Language.EN_IN,
        ),
    )

    llm = GroqLLMService(
        api_key=os.environ["GROQ_API_KEY"],
        settings=GroqLLMService.Settings(
            model="llama-3.1-8b-instant",
            system_instruction=(
                "You are a helpful voice assistant powered by Gnani Vachana. "
                "Your responses will be spoken aloud, so keep them concise and "
                "conversational. Do not use emojis, markdown, or special characters."
            ),
        ),
    )

    context = LLMContext()
    user_aggregator, assistant_aggregator = LLMContextAggregatorPair(
        context,
        user_params=LLMUserAggregatorParams(vad_analyzer=SileroVADAnalyzer()),
    )

    pipeline = Pipeline(
        [
            transport.input(),
            stt,
            user_aggregator,
            llm,
            tts,
            transport.output(),
            assistant_aggregator,
        ]
    )

    worker = PipelineWorker(
        pipeline,
        params=PipelineParams(
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
        idle_timeout_secs=runner_args.pipeline_idle_timeout_secs,
    )

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info("Client connected")
        context.add_message(
            {
                "role": "developer",
                "content": "Greet the user and offer to help in a friendly way.",
            }
        )
        await worker.queue_frames([LLMRunFrame()])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info("Client disconnected")
        await worker.cancel()

    @stt.event_handler("on_connected")
    async def on_stt_connected(stt):
        logger.debug("Gnani STT WebSocket connected")

    @tts.event_handler("on_connected")
    async def on_tts_connected(tts):
        logger.debug("Gnani TTS WebSocket connected")

    runner = WorkerRunner(handle_sigint=runner_args.handle_sigint)

    await runner.add_workers(worker)
    await runner.run()


async def bot(runner_args: RunnerArguments):
    """Main bot entry point compatible with Pipecat Cloud."""
    transport = await create_transport(runner_args, transport_params)
    await run_bot(transport, runner_args)


if __name__ == "__main__":
    from pipecat.runner.run import main

    main()
