"""
CrimeaLens Web API — upload a map image and get a sovereignty classification.

Start with: uv run --extra api crimealens --serve --port 8080
"""

import io
from pathlib import Path

import cv2
import numpy as np

from .classifier import CrimeaClassifier

_classifier: CrimeaClassifier | None = None


def get_classifier() -> CrimeaClassifier:
    global _classifier
    if _classifier is None:
        _classifier = CrimeaClassifier()
    return _classifier


def create_app():
    from fastapi import FastAPI, File, UploadFile
    from fastapi.responses import JSONResponse

    app = FastAPI(
        title="CrimeaLens",
        description="Visual classifier for Crimea sovereignty on maps. "
        "Upload a map image to detect whether Crimea is shown as Ukraine, Russia, or disputed.",
        version="0.1.0",
    )

    @app.get("/")
    async def root():
        return {
            "service": "CrimeaLens",
            "version": "0.1.0",
            "usage": "POST /classify with an image file",
        }

    @app.get("/health")
    async def health():
        classifier = get_classifier()
        return {"status": "ok", "templates_loaded": classifier is not None}

    @app.post("/classify")
    async def classify(image: UploadFile = File(...), verbose: bool = False):
        contents = await image.read()
        if not contents:
            return JSONResponse(
                status_code=400,
                content={"error": "Empty file"},
            )

        # Decode image from bytes
        arr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            return JSONResponse(
                status_code=400,
                content={"error": "Could not decode image. Supported: PNG, JPG, BMP, WEBP."},
            )

        classifier = get_classifier()
        result = classifier.classify_image(img, verbose=verbose)

        return {
            "filename": image.filename,
            **result.to_dict(),
        }

    return app


def start_server(port: int = 8080):
    import uvicorn
    app = create_app()
    print(f"\nCrimeaLens API running at http://localhost:{port}")
    print(f"  POST /classify  — upload an image for classification")
    print(f"  GET  /health    — health check")
    print(f"  GET  /docs      — interactive API docs\n")
    uvicorn.run(app, host="0.0.0.0", port=port)
