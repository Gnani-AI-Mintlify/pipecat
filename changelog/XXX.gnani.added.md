- Added Gnani Vachana speech AI services via the `pipecat-gnani` package:

  **STT (Speech-to-Text):**
  - `GnaniHttpSTTService`: REST-based transcription with VAD-segmented audio
  - `GnaniSTTService`: WebSocket streaming real-time transcription

  **TTS (Text-to-Speech):**
  - `GnaniHttpTTSService`: REST-based single-request synthesis
  - `GnaniSSETTSService`: SSE streaming synthesis (lower latency)
  - `GnaniTTSService`: WebSocket streaming synthesis with interruption handling

  **Features:**
  - Support for 12 Indian languages (Assamese, Bengali, English-India, Gujarati, Hindi, Kannada, Malayalam, Marathi, Odia, Punjabi, Tamil, Telugu)
  - 4 voices: Pranav, Kaveri, Shubhra, Deepak (see https://docs.gnani.ai/api/TTS/tts-sse#available-voices)
  - Dynamic language switching via `set_language()`
  - Built-in metrics (TTFB and processing time)
  - Traced transcription (`@traced_stt`) and synthesis (`@traced_tts`)
  - Complete foundational example at `examples/foundational/07x-interruptible-gnani.py` (WebSocket STT + interruptible WebSocket TTS)
  - Voice provider example at `examples/voice/voice-gnani.py`
  - Smoke integration at `scripts/smoke-gnani/` (boot check, unit tests, eval scenarios)
  - Release eval entry for `voice-gnani.py` in `scripts/release-evals/manifest.yaml`
