- Synced Gnani integration to `pipecat-gnani` 0.5.9:

  **Fixed:**
  - TTS click/tick at segment start — WAV header-only first chunks are no longer emitted as PCM audio (see `pipecat-gnani` 0.5.9).

- Synced Gnani integration to `pipecat-gnani` 0.5.7:

  **Breaking:**
  - Default TTS model is now `timbre-v2.0` (was `vachana-voice-v3`).

  **Added:**
  - Re-exported `DEFAULT_MODEL`, `SUPPORTED_TTS_LANGUAGES`, `TIMBRE_V20_VOICES`, and `TIMBRE_V25_VOICES` from `pipecat.services.gnani`.
  - Re-exported `settings_language` and `ws_header_kwargs` from internal Gnani helper modules.
  - `timbre-v2.5` support with 42 voices and optional `language` in TTS settings.
  - Unit tests for timbre model voice catalogs and payload validation (`tests/test_gnani_tts_timbre.py`).

  **Removed:**
  - `GnaniHttpSTTSettings.preferred_language` — code-switching is no longer supported in pipecat-gnani 0.5.6+.

  **Changed:**
  - Bumped `[gnani]` extra dependency to `pipecat-gnani>=0.5.7,<1` (requires `gnani-vachana>=0.7.7`).
