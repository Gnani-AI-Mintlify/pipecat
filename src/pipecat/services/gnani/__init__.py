#
# Copyright (c) 2024–2026, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""Gnani Vachana speech AI service integrations for Pipecat.

Re-exports services from the ``pipecat-gnani`` package under the
``pipecat.services.gnani`` namespace.

Prerequisites::

    You need a Gnani API key. `Gnani APIs <https://app.gnani.ai/voice>`_ have this.

    Set your credentials as environment variables::

        export GNANI_API_KEY="your-api-key"

STT services:

- GnaniHttpSTTService — REST-based file transcription (requires VAD)
- GnaniSTTService — WebSocket streaming speech-to-text with VAD

TTS services:

- GnaniHttpTTSService — REST-based text-to-speech
- GnaniSSETTSService — SSE streaming text-to-speech (lower latency)
- GnaniTTSService — WebSocket streaming synthesis with interruption handling

Voices: Pranav (default), Kaveri, Shubhra, Deepak for timbre-v2.0; 42 voices for timbre-v2.5.
See https://docs.gnani.ai/api/TTS/tts-sse#available-voices

API docs: https://docs.gnani.ai/api/introduction/introduction
"""

from pipecat_gnani import (
    DEFAULT_MODEL,
    STT_FORMAT_TRANSCRIBE,
    STT_FORMAT_VERBATIM,
    SUPPORTED_TTS_LANGUAGES,
    SUPPORTED_VOICES,
    TIMBRE_V20_VOICES,
    TIMBRE_V25_VOICES,
    GnaniHttpSTTService,
    GnaniHttpSTTSettings,
    GnaniHttpTTSService,
    GnaniHttpTTSSettings,
    GnaniSSETTSService,
    GnaniSSETTSSettings,
    GnaniSTTService,
    GnaniSTTSettings,
    GnaniTTSService,
    GnaniTTSSettings,
)

__all__ = [
    "DEFAULT_MODEL",
    "STT_FORMAT_TRANSCRIBE",
    "STT_FORMAT_VERBATIM",
    "SUPPORTED_TTS_LANGUAGES",
    "SUPPORTED_VOICES",
    "TIMBRE_V20_VOICES",
    "TIMBRE_V25_VOICES",
    "GnaniHttpSTTService",
    "GnaniHttpSTTSettings",
    "GnaniHttpTTSService",
    "GnaniHttpTTSSettings",
    "GnaniSSETTSService",
    "GnaniSSETTSSettings",
    "GnaniSTTService",
    "GnaniSTTSettings",
    "GnaniTTSService",
    "GnaniTTSSettings",
]
