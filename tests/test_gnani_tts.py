#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""Tests for Gnani Vachana TTS services."""

import asyncio
import base64
import json
import unittest

import aiohttp
import pytest
from aiohttp import web

from pipecat.frames.frames import (
    AggregatedTextFrame,
    ErrorFrame,
    TTSAudioRawFrame,
    TTSSpeakFrame,
    TTSStartedFrame,
    TTSStoppedFrame,
    TTSTextFrame,
)
from pipecat.services.gnani.tts import (
    SUPPORTED_VOICES,
    GnaniHttpTTSService,
    GnaniTTSService,
    language_to_gnani_language,
)
from pipecat.tests.utils import run_test
from pipecat.transcriptions.language import Language


def test_supported_voices_contains_all():
    """All documented voices are in SUPPORTED_VOICES."""
    expected = {"sia", "raju", "kanika", "nikita", "ravan", "simran", "karan", "neha"}
    assert SUPPORTED_VOICES == expected


def test_language_to_gnani_hindi():
    """Hindi maps to hi-IN."""
    assert language_to_gnani_language(Language.HI_IN) == "hi-IN"


def test_language_to_gnani_english():
    """English maps to en-IN."""
    assert language_to_gnani_language(Language.EN_IN) == "en-IN"


def test_language_to_gnani_tamil():
    """Tamil maps to ta-IN."""
    assert language_to_gnani_language(Language.TA_IN) == "ta-IN"


def test_language_to_gnani_base_hindi():
    """Base Hindi (HI) also maps to hi-IN."""
    assert language_to_gnani_language(Language.HI) == "hi-IN"


def test_language_to_gnani_base_english():
    """Base English (EN) also maps to en-IN."""
    assert language_to_gnani_language(Language.EN) == "en-IN"


def test_gnani_http_tts_rejects_invalid_voice():
    """GnaniHttpTTSService rejects unsupported voice."""
    with pytest.raises(ValueError, match="not supported"):
        GnaniHttpTTSService(
            api_key="test-key",
            aiohttp_session=aiohttp.ClientSession(),
            voice_id="nonexistent",
        )


@pytest.mark.asyncio
async def test_gnani_http_tts_success(aiohttp_client):
    """GnaniHttpTTSService should POST to /api/v1/tts/inference and emit audio frames."""

    request_bodies = []

    async def handler(request):
        body = await request.read()
        request_bodies.append(body)

        # WAV header (44 bytes) + PCM data
        wav_header = b"RIFF" + b"\x00" * 40
        pcm_data = b"\x00\x01\x02\x03" * 6000
        audio_data = wav_header + pcm_data

        return web.Response(
            status=200,
            body=audio_data,
            content_type="audio/wav",
        )

    app = web.Application()
    app.router.add_post("/api/v1/tts/inference", handler)
    client = await aiohttp_client(app)
    base_url = str(client.make_url("/api/v1/tts/inference"))

    import pipecat_gnani.tts as gnani_tts_mod

    original_url = gnani_tts_mod.GNANI_TTS_REST_URL
    gnani_tts_mod.GNANI_TTS_REST_URL = base_url

    try:
        async with aiohttp.ClientSession() as session:
            tts_service = GnaniHttpTTSService(
                api_key="test-key",
                aiohttp_session=session,
                sample_rate=24000,
            )

            down_frames, _ = await run_test(
                tts_service,
                frames_to_send=[TTSSpeakFrame(text="Hello from Gnani.")],
            )

        frame_types = [type(f) for f in down_frames]

        assert AggregatedTextFrame in frame_types
        assert TTSStartedFrame in frame_types
        assert TTSStoppedFrame in frame_types
        assert TTSTextFrame in frame_types

        audio_frames = [f for f in down_frames if isinstance(f, TTSAudioRawFrame)]
        assert len(audio_frames) >= 1
        assert all(f.sample_rate == 24000 for f in audio_frames)
        assert all(f.num_channels == 1 for f in audio_frames)

    finally:
        gnani_tts_mod.GNANI_TTS_REST_URL = original_url


@pytest.mark.asyncio
async def test_gnani_http_tts_error(aiohttp_client):
    """GnaniHttpTTSService should emit ErrorFrame on API error."""

    async def handler(_request):
        return web.Response(status=500, text="Internal Server Error")

    app = web.Application()
    app.router.add_post("/api/v1/tts/inference", handler)
    client = await aiohttp_client(app)
    base_url = str(client.make_url("/api/v1/tts/inference"))

    import pipecat_gnani.tts as gnani_tts_mod

    original_url = gnani_tts_mod.GNANI_TTS_REST_URL
    gnani_tts_mod.GNANI_TTS_REST_URL = base_url

    try:
        async with aiohttp.ClientSession() as session:
            tts_service = GnaniHttpTTSService(
                api_key="test-key",
                aiohttp_session=session,
                sample_rate=24000,
            )

            expected_down = [AggregatedTextFrame, TTSStartedFrame, TTSStoppedFrame, TTSTextFrame]
            expected_up = [ErrorFrame]

            _, up_frames = await run_test(
                tts_service,
                frames_to_send=[
                    TTSSpeakFrame(text="Error case.", append_to_context=False),
                ],
                expected_down_frames=expected_down,
                expected_up_frames=expected_up,
            )

        assert isinstance(up_frames[0], ErrorFrame)
        assert "500" in up_frames[0].error or "Internal Server Error" in up_frames[0].error

    finally:
        gnani_tts_mod.GNANI_TTS_REST_URL = original_url


if __name__ == "__main__":
    unittest.main()
