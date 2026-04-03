"""
CrimeaLens CLI — classify map images from the command line.
"""

import argparse
import json
import sys
from pathlib import Path

from .classifier import CrimeaClassifier
from .templates import generate_templates, save_templates, TEMPLATES_DIR


LABELS = {
    "ukraine": "\033[94m\u2713 UKRAINE\033[0m",
    "russia": "\033[91m\u2717 RUSSIA\033[0m",
    "disputed": "\033[93m\u26A0 DISPUTED\033[0m",
    "absent": "\033[90m\u2014 ABSENT\033[0m",
    "uncertain": "\033[90m? UNCERTAIN\033[0m",
}


def main():
    parser = argparse.ArgumentParser(
        prog="crimealens",
        description="Classify map images: does the map show Crimea as Ukraine, Russia, or disputed?",
    )
    parser.add_argument("images", nargs="*", help="Image file(s) to classify")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show detailed scores")
    parser.add_argument(
        "--generate-templates",
        action="store_true",
        help="Generate reference templates from geographic data",
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Start the web API server (requires 'api' extra)",
    )
    parser.add_argument("--port", type=int, default=8080, help="Port for API server")

    args = parser.parse_args()

    if args.generate_templates:
        cache = TEMPLATES_DIR / ".cache"
        templates = generate_templates(cache_dir=cache)
        save_templates(templates)
        return

    if args.serve:
        try:
            from .api import start_server
            start_server(port=args.port)
        except ImportError:
            print("API server requires the 'api' extra: uv sync --extra api", file=sys.stderr)
            sys.exit(1)
        return

    if not args.images:
        parser.print_help()
        sys.exit(1)

    # Check templates exist
    if not (TEMPLATES_DIR / "crimea.npz").exists():
        print("Reference templates not found. Generating...", file=sys.stderr)
        cache = TEMPLATES_DIR / ".cache"
        templates = generate_templates(cache_dir=cache)
        save_templates(templates)

    classifier = CrimeaClassifier()
    results = []

    for image_path in args.images:
        path = Path(image_path)
        if not path.exists():
            if args.json:
                results.append({"file": str(path), "label": "error", "error": "File not found"})
            else:
                print(f"  {path}: File not found", file=sys.stderr)
            continue

        result = classifier.classify(path, verbose=args.verbose)

        if args.json:
            results.append({"file": str(path), **result.to_dict()})
        else:
            label_str = LABELS.get(result.label, result.label)
            conf_str = f"({result.confidence:.0%})"
            print(f"  {path.name:40s} {label_str} {conf_str}")

            if args.verbose and result.details:
                for k, v in result.details.items():
                    print(f"    {k}: {v}")

    if args.json:
        print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
