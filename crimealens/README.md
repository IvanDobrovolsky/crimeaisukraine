# CrimeaLens

Visual classifier that detects how a map image represents Crimea's sovereignty — does the map show Crimea as part of Ukraine, Russia, or disputed?

## How it works

CrimeaLens uses computer vision to analyze map images without any AI/ML models or cloud APIs. The entire pipeline is deterministic geometry:

1. **Reference contours** — Pre-computed binary masks of Ukraine-with-Crimea and Russia-with-Crimea from known-correct geographic data (Natural Earth, OpenStreetMap)
2. **Map detection** — Identifies country polygons in the input image via color segmentation and contour extraction
3. **Shape matching** — Compares detected contours against reference templates using Hu moments (`cv2.matchShapes`) which are invariant to scale, rotation, and translation
4. **Classification** — Determines which country polygon contains the Crimea peninsula shape

### Classification output

| Result | Meaning |
|--------|---------|
| `ukraine` | Crimea is part of Ukraine's polygon (correct under international law) |
| `russia` | Crimea is part of Russia's polygon (incorrect) |
| `disputed` | Crimea shown with dashed border or separate from both |
| `absent` | Crimea not visible or map doesn't cover the region |
| `uncertain` | Confidence too low to classify |

## Installation

```bash
# Requires uv (https://docs.astral.sh/uv/)
cd crimealens
uv sync

# With API server support
uv sync --extra api
```

## Usage

### CLI

```bash
# Classify a single image
uv run crimealens path/to/map.png

# Classify multiple images
uv run crimealens screenshots/*.png

# Output as JSON
uv run crimealens --json path/to/map.png

# Verbose mode (shows confidence scores)
uv run crimealens -v path/to/map.png
```

### Python API

```python
from crimealens import CrimeaClassifier

classifier = CrimeaClassifier()
result = classifier.classify("map_screenshot.png")

print(result.label)       # "ukraine" | "russia" | "disputed" | "absent" | "uncertain"
print(result.confidence)  # 0.0 - 1.0
print(result.details)     # {"crimea_detected": True, "match_ukraine": 0.92, "match_russia": 0.15}
```

### Web API

```bash
# Start the API server
uv run --extra api crimealens --serve --port 8080

# Upload an image
curl -X POST http://localhost:8080/classify \
  -F "image=@map_screenshot.png"
```

## Algorithm details

### Why Hu moments?

Hu moments are 7 numerical values computed from image moments that are invariant to translation, scale, and rotation. This means CrimeaLens works regardless of:
- Map zoom level
- Map projection (Mercator, Robinson, etc.)
- Image resolution
- Map orientation

### Why not ML?

- **No training data needed** — the ground truth is the geographic shape itself
- **Fully deterministic** — same image always produces same result
- **Explainable** — every step is auditable geometry
- **Zero dependencies on cloud APIs** — runs entirely offline
- **Fast** — classification takes <100ms per image

### Pipeline

```
Input Image
    │
    ├── Color Quantization (reduce to dominant colors)
    ├── Contour Extraction (find country boundaries)
    ├── Crimea Region Crop (focus on Black Sea / 44°N 34°E area)
    │
    ├── Template Matching
    │   ├── Compare vs Ukraine-with-Crimea template
    │   ├── Compare vs Russia-with-Crimea template
    │   └── Compare vs Crimea-standalone template
    │
    └── Classification
        ├── Hu moment distance (primary signal)
        ├── Contour containment test (is Crimea inside UA or RU polygon?)
        └── Border style detection (solid vs dashed line)
```

## Project structure

```
crimealens/
├── pyproject.toml
├── README.md
├── src/
│   └── crimealens/
│       ├── __init__.py        # Public API
│       ├── cli.py             # CLI entry point
│       ├── classifier.py      # Main classification logic
│       ├── contours.py        # Contour extraction and matching
│       ├── templates.py       # Reference template generation
│       └── api.py             # Optional FastAPI server
├── templates/                 # Pre-computed reference contours
│   ├── ukraine_with_crimea.npz
│   ├── russia_with_crimea.npz
│   └── crimea_standalone.npz
└── tests/
    └── test_classifier.py
```

## Use cases

- **Automated audit** — Scan thousands of map screenshots from platforms, textbooks, news articles
- **YouTube monitoring** — Extract frames from videos showing maps, classify Crimea representation
- **Web service** — Upload-and-classify tool for journalists, researchers, diplomats
- **CI/CD integration** — Verify map assets in your codebase show correct borders before deployment

## License

Part of the [crimeaisukraine](https://github.com/IvanDobrovolskyi/crimeaisukraine) research project.
