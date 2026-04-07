"""Geodata pipeline runner. Calls open-source, map-services, and propagation scans."""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent

def main():
    for script in ["scan_open_source.py", "scan_map_services.py", "scan_propagation.py"]:
        p = HERE / script
        if p.exists():
            print(f"--- Running {script} ---")
            subprocess.run([sys.executable, str(p)], cwd=str(HERE))

if __name__ == "__main__":
    main()
