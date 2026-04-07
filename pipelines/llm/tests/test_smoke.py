"""Smoke test: classifier import + query function shape."""
import sys
from pathlib import Path

PIPE = Path(__file__).parent.parent
sys.path.insert(0, str(PIPE))


def test_scan_imports():
    import scan
    assert hasattr(scan, "main") or hasattr(scan, "MODELS")


def test_models_list_format():
    import scan
    if hasattr(scan, "MODELS"):
        assert all(isinstance(m, dict) for m in scan.MODELS)
        assert all("id" in m and "name" in m for m in scan.MODELS)
