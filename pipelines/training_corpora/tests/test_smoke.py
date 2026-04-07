"""Smoke test for training corpora pipeline."""
import sys
from pathlib import Path
PIPE = Path(__file__).parent.parent
sys.path.insert(0, str(PIPE))


def test_scan_imports():
    import scan
    assert hasattr(scan, "main") or hasattr(scan, "CORPORA")


def test_corpora_list():
    import scan
    if hasattr(scan, "CORPORA"):
        assert len(scan.CORPORA) >= 5
        for c in scan.CORPORA:
            assert "name" in c
            assert "hf" in c
