# Full-Path Test Dataset

This dataset exercises the current demo pipeline:

- text question -> decision -> RAG answer -> resume text
- image input -> demo vision matcher -> RAG explanation
- voice input -> Mock ASR -> decision/RAG/private assistant -> Mock TTS
- route recommendation with profile memory tags
- unclear voice fallback

The current implementation matches image and voice samples by file name. The image files are valid PNG placeholders whose names contain the same demo keywords used by `VisionRecognizer`. The WAV files are valid 16 kHz mono test tones whose names trigger the current `VoiceAdapter` mock ASR branches.

Run:

```bash
python tools/generate_full_path_test_dataset.py
uvicorn ai_algorithm_service.api:app --app-dir src --reload
```

Then use `manifest.json` as the canonical case list, or copy commands from `curl_examples.txt`.
