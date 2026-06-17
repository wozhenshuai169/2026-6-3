from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


def post_json(endpoint: str, payload: dict[str, Any], *, timeout: float = 30.0) -> dict[str, Any]:
    headers = {"Content-Type": "application/json"}
    token = os.getenv("AI_PROVIDER_API_KEY") or os.getenv("AI_API_KEY")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(
        endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} from provider: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Cannot reach provider: {exc.reason}") from exc


def load_file_base64(path: str | None) -> str | None:
    if not path:
        return None
    file_path = Path(path)
    if not file_path.exists() or not file_path.is_file():
        return None
    return base64.b64encode(file_path.read_bytes()).decode("ascii")

