#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""Tests for GnaniSTTService configuration and WebSocket URL handling."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pipecat.services.gnani.stt import (
    GNANI_STT_WS_URL,
    GnaniSTTService,
    GnaniSTTSettings,
    language_to_gnani_language,
)
from pipecat.transcriptions.language import Language


def test_language_to_gnani_hindi():
    """Hindi language maps to hi-IN."""
    result = language_to_gnani_language(Language.HI_IN)
    assert result == "hi-IN"


def test_language_to_gnani_english():
    """English (India) maps to en-IN."""
    result = language_to_gnani_language(Language.EN_IN)
    assert result == "en-IN"


def test_language_to_gnani_tamil():
    """Tamil maps to ta-IN."""
    result = language_to_gnani_language(Language.TA_IN)
    assert result == "ta-IN"


def test_language_to_gnani_bengali():
    """Bengali maps to bn-IN."""
    result = language_to_gnani_language(Language.BN_IN)
    assert result == "bn-IN"


def test_language_to_gnani_kannada():
    """Kannada maps to kn-IN."""
    result = language_to_gnani_language(Language.KN_IN)
    assert result == "kn-IN"


def test_language_to_gnani_telugu():
    """Telugu maps to te-IN."""
    result = language_to_gnani_language(Language.TE_IN)
    assert result == "te-IN"


def test_language_to_gnani_malayalam():
    """Malayalam maps to ml-IN."""
    result = language_to_gnani_language(Language.ML_IN)
    assert result == "ml-IN"


def test_language_to_gnani_marathi():
    """Marathi maps to mr-IN."""
    result = language_to_gnani_language(Language.MR_IN)
    assert result == "mr-IN"


def test_language_to_gnani_gujarati():
    """Gujarati maps to gu-IN."""
    result = language_to_gnani_language(Language.GU_IN)
    assert result == "gu-IN"


def test_language_to_gnani_punjabi():
    """Punjabi maps to pa-IN."""
    result = language_to_gnani_language(Language.PA_IN)
    assert result == "pa-IN"


def test_gnani_stt_settings_default():
    """GnaniSTTSettings has correct defaults."""
    settings = GnaniSTTSettings()
    assert settings.language is None
    assert settings.model is None
    assert settings.voice is None


def test_gnani_stt_ws_url_constant():
    """WebSocket URL constant is correct."""
    assert GNANI_STT_WS_URL == "wss://api.vachana.ai/stt/v3/stream"


@pytest.mark.asyncio
async def test_gnani_stt_run_stt_yields_none_when_not_connected():
    """run_stt yields None when WebSocket is not connected."""
    service = GnaniSTTService.__new__(GnaniSTTService)
    service._ws = None
    service._name = "GnaniSTTService"

    frames = []
    async for frame in service.run_stt(b"\x00" * 1024):
        frames.append(frame)

    assert frames == [None]


@pytest.mark.asyncio
async def test_gnani_stt_run_stt_sends_audio():
    """run_stt sends audio bytes to WebSocket when connected."""
    service = GnaniSTTService.__new__(GnaniSTTService)
    service._name = "GnaniSTTService"

    mock_ws = MagicMock()
    mock_ws.send = AsyncMock()
    service._ws = mock_ws

    audio = b"\x00\x01" * 512

    frames = []
    async for frame in service.run_stt(audio):
        frames.append(frame)

    mock_ws.send.assert_called_once_with(audio)
    assert frames == [None]


@pytest.mark.asyncio
async def test_gnani_stt_run_stt_handles_send_error():
    """run_stt yields ErrorFrame when send fails."""
    from pipecat.frames.frames import ErrorFrame

    service = GnaniSTTService.__new__(GnaniSTTService)
    service._name = "GnaniSTTService"

    mock_ws = MagicMock()
    mock_ws.send = AsyncMock(side_effect=Exception("connection lost"))
    service._ws = mock_ws

    frames = []
    async for frame in service.run_stt(b"\x00" * 1024):
        frames.append(frame)

    assert len(frames) == 2
    assert isinstance(frames[0], ErrorFrame)
    assert "connection lost" in frames[0].error
