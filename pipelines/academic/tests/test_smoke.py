"""Smoke test for academic pipeline."""
import sys
from pathlib import Path
PIPE = Path(__file__).parent.parent
sys.path.insert(0, str(PIPE))

def test_scan_imports():
    import scan
    assert hasattr(scan, "main") or hasattr(scan, "API")
