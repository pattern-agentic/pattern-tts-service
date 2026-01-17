#!/bin/bash
PA_TTS_DOT_ENV=.env uv run uvicorn pattern_tts.api.main:app --host 0.0.0.0 --port 8205 --reload
