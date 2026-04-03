"""
CrimeaLens — Visual classifier for Crimea sovereignty on maps.

Detects whether a map image shows Crimea as part of Ukraine, Russia,
or as disputed territory. Uses pure computer vision (Hu moments,
contour matching) — no ML models or cloud APIs required.
"""

from .classifier import ClassificationResult, CrimeaClassifier

__all__ = ["CrimeaClassifier", "ClassificationResult"]
__version__ = "0.1.0"
