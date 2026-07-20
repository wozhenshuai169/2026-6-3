"""Optional validation against a separately deployed, real-provider backend."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "tools" / "run_real_model_validation.py"


@pytest.mark.skipif(
    not os.getenv("REAL_VALIDATION_BASE_URL"),
    reason="REAL_VALIDATION_BASE_URL is not configured",
)
def test_real_model_validation_uses_product_api_path():
    """Do not use TestClient: providers must reach the deployed upload URLs."""
    result = subprocess.run(
        [sys.executable, str(RUNNER), "--base-url", os.environ["REAL_VALIDATION_BASE_URL"]],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
