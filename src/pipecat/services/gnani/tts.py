#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""Gnani Vachana Text-to-Speech services — delegated to pipecat-gnani package.

Install via: pip install pipecat-gnani
"""

from pipecat_gnani.tts import (  # noqa: F401
    GNANI_TTS_REST_URL,
    GNANI_TTS_WS_URL,
    SUPPORTED_VOICES,
    GnaniHttpTTSService,
    GnaniHttpTTSSettings,
    GnaniTTSService,
    GnaniTTSSettings,
    language_to_gnani_language,
)

__all__ = [
    "GnaniHttpTTSService",
    "GnaniHttpTTSSettings",
    "GnaniTTSService",
    "GnaniTTSSettings",
    "SUPPORTED_VOICES",
    "GNANI_TTS_REST_URL",
    "GNANI_TTS_WS_URL",
    "language_to_gnani_language",
]
