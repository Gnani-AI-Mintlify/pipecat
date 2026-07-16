#
# Copyright (c) 2024-2026, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""Voice bot with Gnani Vachana STT + TTS.

Uses REST STT (VAD-segmented) and SSE streaming TTS.

Prerequisites::

    You need a Gnani API key. `Gnani APIs <https://app.gnani.ai/voice>`_ have this.

    Set your credentials as environment variables::

        export GNANI_API_KEY="your-api-key"
        export GROQ_API_KEY="your-groq-api-key"

Install::

    pip install "pipecat-ai[gnani,daily,groq,silero,runner,webrtc,websocket]"

Run::

    python examples/voice/voice-gnani.py -t webrtc
    # open http://localhost:7860/client

Swap service classes for WebSocket variants — see ``foundational/07x-interruptible-gnani.py``.
"""

import os

import aiohttp
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
from pipecat.services.gnani import GnaniHttpSTTService, GnaniSSETTSService
from pipecat.services.groq.llm import GroqLLMService
from pipecat.transcriptions.language import Language
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.transports.daily.transport import DailyParams
from pipecat.transports.websocket.fastapi import FastAPIWebsocketParams
from pipecat.workers.runner import WorkerRunner

load_dotenv(override=True)

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


async def run_bot(
    transport: BaseTransport,
    runner_args: RunnerArguments,
    session: aiohttp.ClientSession,
):
    logger.info("Starting bot with Gnani REST STT + SSE TTS")

    gnani_api_key = os.environ["GNANI_API_KEY"]

    # REST STT — transcribes VAD-segmented utterances via HTTP POST.
    stt = GnaniHttpSTTService(
        api_key=gnani_api_key,
        aiohttp_session=session,
        sample_rate=16000,
        settings=GnaniHttpSTTService.Settings(
            language=Language.EN_IN,
        ),
    )

    # SSE TTS — streams audio chunks over Server-Sent Events (lower latency than REST).
    # timbre-v2.5: 42 voices — model and language are required.
    tts = GnaniSSETTSService(
        api_key=gnani_api_key,
        aiohttp_session=session,
        sample_rate=22050,
        settings=GnaniSSETTSService.Settings(
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
                "You are a helpful assistant in a voice conversation powered by "
                "Gnani Vachana. Your responses will be spoken aloud, so avoid emojis, "
                "bullet points, or other formatting that can't be spoken. "
                "Respond to what the user said in a creative, helpful, and brief way."
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
            {"role": "developer", "content": "Please introduce yourself to the user."}
        )
        await worker.queue_frames([LLMRunFrame()])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info("Client disconnected")
        await worker.cancel()

    runner = WorkerRunner(handle_sigint=runner_args.handle_sigint)

    await runner.add_workers(worker)
    await runner.run()


async def bot(runner_args: RunnerArguments):
    """Main bot entry point compatible with Pipecat Cloud."""
    transport = await create_transport(runner_args, transport_params)
    async with aiohttp.ClientSession() as session:
        await run_bot(transport, runner_args, session)


if __name__ == "__main__":
    from pipecat.runner.run import main

    main()
