"""Smoke test: ensure scan.py imports and main() exists."""
import importlib.util
import sys
from pathlib import Path

def test_scan_imports():
    spec = importlib.util.spec_from_file_location(
        "scan", Path(__file__).parent.parent / "scan.py"
    )
    mod = importlib.util.module_from_spec(spec)
    # Don't execute main, just import
    sys.modules["scan"] = mod
    try:
        spec.loader.exec_module(mod)
    except SystemExit:
        pass  # CLI scripts may exit

def test_has_main():
    scan_path = Path(__file__).parent.parent / "scan.py"
    content = scan_path.read_text()
    assert "def main" in content or "if __name__" in content
