#
# Copyright (c) 2024-2026, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

import unittest
from unittest.mock import AsyncMock, MagicMock

import aiohttp

from pipecat.frames.frames import ErrorFrame
from pipecat.services.gnani.tts import GnaniHttpTTSService, GnaniHttpTTSSettings


class TestGnaniHttpTTSService(unittest.IsolatedAsyncioTestCase):
    """Test cases for GnaniHttpTTSService (REST)."""

    def setUp(self):
        self.api_key = "test-api-key"
        self.mock_session = AsyncMock(spec=aiohttp.ClientSession)
        self.service = GnaniHttpTTSService(
            api_key=self.api_key,
            aiohttp_session=self.mock_session,
            settings=GnaniHttpTTSSettings(voice="Pranav"),
        )
        self.service._sample_rate = 16000

    def test_initialization(self):
        self.assertEqual(self.service._api_key, self.api_key)
        self.assertEqual(self.service._settings.voice, "Pranav")

    def test_can_generate_metrics(self):
        self.assertTrue(self.service.can_generate_metrics())

    def test_supported_voices(self):
        from pipecat.services.gnani import SUPPORTED_VOICES

        self.assertIn("Pranav", SUPPORTED_VOICES)
        self.assertIn("Kaveri", SUPPORTED_VOICES)

    async def test_run_tts_success(self):
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.read = AsyncMock(return_value=b"\x00\x01" * 512)
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        self.mock_session.post = MagicMock(return_value=mock_response)

        frames = []
        async for frame in self.service.run_tts("Hello", "ctx-1"):
            if frame is not None:
                frames.append(frame)

        audio_frames = [f for f in frames if type(f).__name__ == "TTSAudioRawFrame"]
        self.assertGreater(len(audio_frames), 0)

    async def test_run_tts_http_error(self):
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_response.text = AsyncMock(return_value="Internal Server Error")
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        self.mock_session.post = MagicMock(return_value=mock_response)

        frames = []
        async for frame in self.service.run_tts("Hello", "ctx-1"):
            if frame is not None:
                frames.append(frame)

        errors = [f for f in frames if isinstance(f, ErrorFrame)]
        self.assertEqual(len(errors), 1)
        self.assertIn("Gnani TTS API error", errors[0].error)

    async def test_run_tts_network_error(self):
        self.mock_session.post = MagicMock(
            side_effect=aiohttp.ClientError("Connection failed"),
        )

        frames = []
        async for frame in self.service.run_tts("Hello", "ctx-1"):
            if frame is not None:
                frames.append(frame)

        errors = [f for f in frames if isinstance(f, ErrorFrame)]
        self.assertEqual(len(errors), 1)
        self.assertIn("Error generating TTS", errors[0].error)


class TestGnaniHttpTTSSettings(unittest.TestCase):
    """Test GnaniHttpTTSSettings fields."""

    def test_voice_field(self):
        settings = GnaniHttpTTSSettings(voice="Kaveri")
        self.assertEqual(settings.voice, "Kaveri")

    def test_default_voice(self):
        service = GnaniHttpTTSService(
            api_key="key",
            aiohttp_session=AsyncMock(spec=aiohttp.ClientSession),
        )
        self.assertEqual(service._settings.voice, "Pranav")


if __name__ == "__main__":
    unittest.main()
