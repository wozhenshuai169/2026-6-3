# Real Model Validation

This directory is for validating the real ASR/TTS/vision providers after backend integration.

It is intentionally separate from `test_data/full_path`:

- `full_path` and `full_path_web` are regression datasets for the current deterministic pipeline.
- `real_model_validation` is content-driven and should be run against the real backend service.

## Prepare Voice Recordings

Create these WAV files under `test_data/real_model_validation/audio/`:

| File | Sentence |
| --- | --- |
| `toilet_sentence.wav` | 我想去厕所 |
| `lost_sentence.wav` | 我找不到队伍了 |
| `route_short_sentence.wav` | 我想换一条少走路的路线 |

Recommended recording format:

- `wav`
- mono
- 16 kHz or 24 kHz
- clear Mandarin, quiet background

Do not use the old generated tone files for real ASR validation.

## Run

如果要验证真实外部 Provider，先按当前环境配置对应 Key / endpoint。主后端已有 ProviderFactory，会在配置齐全时走真实实现，否则自动降级 mock。

常见配置示例：

```bash
set DASHSCOPE_API_KEY=your-dashscope-key
set DEEPSEEK_API_KEY=your-deepseek-key
```

Start the backend first:

```bash
uvicorn ai_algorithm_service.api:app --app-dir src --reload
```

Then run:

```bash
python tools/run_real_model_validation.py
```

If voice recordings are not ready yet, run image/TTS validation and skip missing voice cases:

```bash
python tools/run_real_model_validation.py --skip-missing-audio
```

For another backend address:

```bash
python tools/run_real_model_validation.py --base-url http://127.0.0.1:9000
```

## Pass Criteria

- Image recognition returns one of the allowed names and confidence is at least `minVisionConfidence`.
- ASR text contains the key phrase for the recorded sentence and confidence is at least `minAsrConfidence`.
- Voice orchestration routes to the expected decision.
- TTS returns `success=true` and a non-empty `audioUrl`.
