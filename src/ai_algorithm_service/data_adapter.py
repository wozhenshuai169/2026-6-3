from __future__ import annotations

import json
from functools import cached_property
from pathlib import Path
from typing import Any


class ScenicDataAdapter:
    """Local first-stage scenic data adapter.

    The interface mirrors future scenic management data sources, while the
    implementation uses static demo JSON so the service runs on a laptop.
    """

    def __init__(self, data_dir: str | Path | None = None) -> None:
        self.data_dir = Path(data_dir) if data_dir else Path(__file__).resolve().parents[2] / "data"

    def _load_json(self, name: str) -> Any:
        with (self.data_dir / name).open("r", encoding="utf-8") as f:
            return json.load(f)

    @cached_property
    def chunks(self) -> list[dict[str, Any]]:
        return self._load_json("scenic_chunks.json")

    @cached_property
    def explanations(self) -> list[dict[str, Any]]:
        return self._load_json("explanations.json")

    @cached_property
    def routes(self) -> list[dict[str, Any]]:
        return self._load_json("routes.json")

    @cached_property
    def eval_cases(self) -> list[dict[str, Any]]:
        return self._load_json("eval_cases.json")

    def get_spot_chunks(self, spot_id: str) -> list[dict[str, Any]]:
        return [chunk for chunk in self.chunks if chunk.get("spotId") == spot_id]

    def get_next_segment(self, current_segment_id: str) -> dict[str, Any] | None:
        ordered = sorted(self.explanations, key=lambda item: item["segmentId"])
        for index, segment in enumerate(ordered):
            if segment["segmentId"] == current_segment_id:
                return ordered[min(index + 1, len(ordered) - 1)]
        return ordered[0] if ordered else None

    def get_facility_hint(self, text: str, current_spot_id: str) -> dict[str, Any] | None:
        facility_words = ["厕所", "洗手间", "休息", "出口", "饮水", "水", "服务台"]
        if not any(word in text for word in facility_words):
            return None
        spot_chunks = self.get_spot_chunks(current_spot_id)
        for chunk in spot_chunks + self.chunks:
            if chunk.get("type") == "facility":
                return chunk
        return None

