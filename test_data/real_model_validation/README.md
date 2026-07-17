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

如果要验证真实外部 Provider，先按当前环境配置对应 Key / endpoint。主后端在凭证缺失或外部服务失败时会返回明确错误，不会伪造模型结果。

常见配置示例：

```bash
set DASHSCOPE_API_KEY=your-dashscope-key
set DEEPSEEK_API_KEY=your-deepseek-key
```

Start the main backend first. The deployed service must have a public base URL
when the ASR Provider needs to fetch an uploaded `/uploads/audio/...` file:

```bash
set DASHSCOPE_API_KEY=your-dashscope-key
set PUBLIC_BASE_URL=https://your-public-backend.example
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
```

Then run the product-path validator against that deployed backend:

```bash
python tools/run_real_model_validation.py --base-url https://your-public-backend.example
```

If voice recordings are not ready yet, run image/TTS validation and skip missing voice cases:

```bash
python tools/run_real_model_validation.py --base-url https://your-public-backend.example --skip-missing-audio
```

仅验证已配置的真实文本与视觉模型、暂时跳过语音合成时：

```bash
python tools/run_real_model_validation.py --base-url http://127.0.0.1:8001 --skip-missing-audio --skip-tts
```

每次执行都会写入 `data/real_model_validation_report.json`，标明通过项、跳过项或阻塞原因。

For another backend address:

```bash
python tools/run_real_model_validation.py --base-url http://127.0.0.1:9000
```

## Pass Criteria

- Image recognition returns one of the allowed names and confidence is at least `minVisionConfidence`.
- Text questions return a non-empty DeepSeek answer with the required product-side knowledge citation.
- 当前图片样本用于验证真实多模态识别，不要求景区知识引用；景区图片与知识引用的联动由固定算法评测集覆盖。后续补充灵山现场照片后，再将对应样本设为 `requiresCitation=true`。
- ASR text contains the key phrase for the recorded sentence and confidence is at least `minAsrConfidence`.
- Voice orchestration routes to the expected decision.
- TTS returns `success=true` and a non-empty `audioUrl`.
