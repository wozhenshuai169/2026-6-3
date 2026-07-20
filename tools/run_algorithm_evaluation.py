"""Run the deterministic 60-case acceptance harness and save a shareable report."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ai_algorithm_service.evaluation import EvaluationHarness


def main() -> None:
    metrics = EvaluationHarness().run()
    output = {
        "generatedAt": datetime.now().astimezone().isoformat(timespec="seconds"),
        "scope": "本地固定样本评测，不代表线上真实游客准确率。",
        "metrics": metrics,
    }
    target = Path("data") / "algorithm_evaluation_report.json"
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
