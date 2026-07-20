from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def check_json(relative_path: str) -> int:
    path = ROOT / relative_path
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[FAIL] {relative_path}: {exc}")
        return 1
    size = len(value) if hasattr(value, "__len__") else 1
    print(f"[ OK ] {relative_path}: {size} records")
    return 0


def main() -> int:
    sys.path.insert(0, str(ROOT))
    from app.core.config import settings

    failures = 0
    print(f"[INFO] Python {sys.version.split()[0]}")
    if sys.version_info < (3, 10):
        print("[FAIL] Python 3.10 or later is required")
        failures += 1

    for relative_path in (
        "data/scenic_chunks.json",
        "data/routes.json",
        "data/path_nodes.json",
        "data/path_edges.json",
        "data/vision_spots.json",
    ):
        failures += check_json(relative_path)

    chunks = json.loads((ROOT / "data" / "scenic_chunks.json").read_text(encoding="utf-8"))
    missing_provenance = [item["chunkId"] for item in chunks if not item.get("sourceTier")]
    if missing_provenance:
        print(f"[FAIL] Knowledge governance: missing provenance={missing_provenance}")
        failures += 1
    else:
        print("[ OK ] Knowledge governance: Lingshan primary, extended content preserved with provenance")

    features = {
        "LLM问答": settings.llm_enabled,
        "图片识景": settings.vision_enabled,
        "语音识别": settings.asr_provider_enabled,
        "语音合成": settings.tts_provider_enabled,
        "高德地图": settings.map_enabled,
    }
    for name, enabled in features.items():
        print(f"[{' OK ' if enabled else 'WARN'}] {name}: {'enabled' if enabled else 'disabled by configuration'}")

    if not settings.admin_password or settings.admin_password == "change-this-password":
        print("[WARN] ADMIN_PASSWORD is empty or still uses the example value")
    if failures:
        print(f"[FAIL] Preflight found {failures} blocking problem(s)")
        return 1
    print("[PASS] Preflight completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
