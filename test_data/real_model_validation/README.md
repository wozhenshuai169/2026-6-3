# Real Model Validation

This directory documents validation cases for real ASR, TTS, vision, voice-question, and RAG behavior.

The live provider tests now target the main backend:

- `/api/audio/asr`
- `/api/audio/tts`
- `/api/vision/recognize`
- `/api/ai/public-voice-question`

`algorithm_service.main` is only used indirectly for the local RAG service tests.

## Environment

Use the same provider variables as the app:

```bash
set RUN_REAL_PROVIDER_TESTS=1
set DASHSCOPE_API_KEY=your-dashscope-key
set DEEPSEEK_API_KEY=your-deepseek-key
```

`DASHSCOPE_API_KEY` is shared by Qwen-VL vision and DashScope audio. `VISION_API_KEY` and `QWEN_VL_API_KEY` are still supported as backwards-compatible overrides.

For real ASR, provide a public audio URL because DashScope Paraformer needs a reachable file URL:

```bash
set REAL_MODEL_AUDIO_URL=https://example.com/toilet_sentence.wav
set REAL_MODEL_AUDIO_FORMAT=wav
set REAL_MODEL_ASR_EXPECTED=厕所
```

## Run

Default tests, including RAG evaluation:

```bash
pytest
```

Real provider validation:

```bash
set RUN_REAL_PROVIDER_TESTS=1
pytest tests/real_model_validation_test.py
```

## Pass Criteria

- Real provider responses expose `provider` and `trace`.
- Real provider tests assert `trace.isMock=false` and provider names do not contain `mock`.
- Vision and audio tests use the main backend `/api` endpoints.
- RAG tests cover citation hit rate, unsupported-question refusal, synonym questions, and multi-chunk synthesis.
