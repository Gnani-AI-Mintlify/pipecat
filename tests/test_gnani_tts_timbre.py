#
# Copyright (c) 2024-2026, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""Timbre v2.0 / v2.5 model-aware voice catalog and payload tests."""

from __future__ import annotations

from unittest.mock import AsyncMock

import aiohttp
import pytest
from gnani.tts import (  # type: ignore[import-untyped]
    DEFAULT_MODEL as SDK_DEFAULT_MODEL,
    TIMBRE_V20_VOICES as SDK_TIMBRE_V20_VOICES,
    TIMBRE_V25_VOICES as SDK_TIMBRE_V25_VOICES,
)
from pipecat_gnani.tts import _build_tts_payload

from pipecat.services.gnani import (
    DEFAULT_MODEL,
    TIMBRE_V20_VOICES,
    TIMBRE_V25_VOICES,
)
from pipecat.services.gnani.tts import (
    GnaniHttpTTSService,
    GnaniHttpTTSSettings,
    GnaniSSETTSService,
    GnaniTTSService,
)

TIMBRE_V20_MODEL = "timbre-v2.0"
TIMBRE_V25_MODEL = "timbre-v2.5"

TIMBRE_V20_VOICES_LIST = sorted(SDK_TIMBRE_V20_VOICES)
TIMBRE_V25_VOICES_LIST = sorted(SDK_TIMBRE_V25_VOICES)
TIMBRE_V20_ONLY_VOICES = sorted(SDK_TIMBRE_V20_VOICES - SDK_TIMBRE_V25_VOICES)

TIMBRE_V25_SAMPLE_VOICES = [
    ("Nalini", "hi-IN"),
    ("Kaveri", "en-IN"),
    ("Asmita", "ta-IN"),
    ("Poorvi", "hi-IN"),
]


def _http_session() -> AsyncMock:
    return AsyncMock(spec=aiohttp.ClientSession)


class TestTimbreSdkReexports:
    def test_default_model_matches_sdk(self):
        assert DEFAULT_MODEL == SDK_DEFAULT_MODEL == TIMBRE_V20_MODEL

    def test_v20_voices_match_sdk(self):
        assert set(TIMBRE_V20_VOICES) == set(TIMBRE_V20_VOICES_LIST)

    def test_v25_voices_match_sdk(self):
        assert set(TIMBRE_V25_VOICES) == set(TIMBRE_V25_VOICES_LIST)


class TestTimbreVoiceCatalog:
    def test_v25_catalog_size(self):
        assert len(TIMBRE_V25_VOICES_LIST) == 42

    def test_v20_only_voices_not_in_v25(self):
        assert "Shubhra" in TIMBRE_V20_ONLY_VOICES


class TestTimbreHttpInit:
    @pytest.mark.parametrize("voice", TIMBRE_V20_VOICES_LIST)
    def test_v20_voices_accepted(self, voice):
        svc = GnaniHttpTTSService(
            api_key="key", aiohttp_session=_http_session(), voice_id=voice
        )
        assert svc._settings.voice == voice
        assert svc._settings.model == TIMBRE_V20_MODEL

    @pytest.mark.parametrize("voice", TIMBRE_V25_VOICES_LIST)
    def test_v25_voices_accepted(self, voice):
        svc = GnaniHttpTTSService(
            api_key="key",
            aiohttp_session=_http_session(),
            voice_id=voice,
            model=TIMBRE_V25_MODEL,
        )
        assert svc._settings.voice == voice

    @pytest.mark.parametrize("voice", TIMBRE_V20_ONLY_VOICES)
    def test_v20_only_voices_rejected_on_v25(self, voice):
        with pytest.raises(ValueError, match="Unsupported voice"):
            GnaniHttpTTSService(
                api_key="key",
                aiohttp_session=_http_session(),
                voice_id=voice,
                model=TIMBRE_V25_MODEL,
            )


class TestTimbreSseInit:
    @pytest.mark.parametrize("voice,language", TIMBRE_V25_SAMPLE_VOICES)
    def test_v25_voice_and_language(self, voice, language):
        svc = GnaniSSETTSService(
            api_key="key",
            aiohttp_session=_http_session(),
            voice_id=voice,
            model=TIMBRE_V25_MODEL,
            settings=GnaniHttpTTSSettings(language=language),
        )
        assert svc._settings.voice == voice
        assert svc._settings.model == TIMBRE_V25_MODEL


class TestTimbreWebsocketInit:
    @pytest.mark.parametrize("voice", ["Nalini", "Asmita", "Poorvi"])
    def test_v25_voices_accepted(self, voice):
        svc = GnaniTTSService(
            api_key="key",
            voice_id=voice,
            model=TIMBRE_V25_MODEL,
        )
        assert svc._settings.voice == voice


class TestTimbrePayload:
    @pytest.mark.parametrize("voice,language", TIMBRE_V25_SAMPLE_VOICES)
    def test_v25_payload_includes_language(self, voice, language):
        svc = GnaniHttpTTSService(
            api_key="key",
            aiohttp_session=_http_session(),
            voice_id=voice,
            model=TIMBRE_V25_MODEL,
            settings=GnaniHttpTTSSettings(language=language),
        )
        payload = _build_tts_payload("Hello", svc._settings, 22050)
        assert payload["model"] == TIMBRE_V25_MODEL
        assert payload["voice"] == voice
        assert payload["language"] == language

    def test_v20_payload_omits_language(self):
        svc = GnaniHttpTTSService(
            api_key="key",
            aiohttp_session=_http_session(),
            voice_id="Pranav",
            model=TIMBRE_V20_MODEL,
        )
        payload = _build_tts_payload("Hello", svc._settings, 22050)
        assert payload["model"] == TIMBRE_V20_MODEL
        assert "language" not in payload
