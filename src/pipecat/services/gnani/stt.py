#
# SPDX-License-Identifier: BSD 2-Clause License
#

"""Gnani Vachana Speech-to-Text service — delegated to pipecat-gnani package.

Install via: pip install pipecat-gnani
"""

from pipecat_gnani.stt import (  # noqa: F401
    GNANI_STT_WS_URL,
    STREAM_CHUNK_BYTES,
    SUPPORTED_SAMPLE_RATES,
    GnaniSTTService,
    GnaniSTTSettings,
    language_to_gnani_language,
)

__all__ = [
    "GnaniSTTService",
    "GnaniSTTSettings",
    "GNANI_STT_WS_URL",
    "SUPPORTED_SAMPLE_RATES",
    "STREAM_CHUNK_BYTES",
    "language_to_gnani_language",
]
