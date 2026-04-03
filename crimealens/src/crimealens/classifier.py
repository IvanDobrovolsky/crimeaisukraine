"""
CrimeaLens Classifier — main classification logic.

Takes an input image and determines whether Crimea is shown as part of
Ukraine, Russia, disputed, absent, or uncertain.
"""

from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np

from .contours import (
    compute_hu_moments,
    contour_contains_point,
    detect_dashed_border,
    extract_all_contours,
    extract_colored_regions,
    extract_contours_from_mask,
    find_crimea_region,
    hu_distance,
    match_shape,
    preprocess_image,
)
from .templates import load_templates


@dataclass
class ClassificationResult:
    """Result of a Crimea sovereignty classification."""

    label: str  # "ukraine" | "russia" | "disputed" | "absent" | "uncertain"
    confidence: float  # 0.0 - 1.0
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "confidence": round(self.confidence, 3),
            "details": self.details,
        }


class CrimeaClassifier:
    """
    Classifies map images based on Crimea sovereignty representation.

    The classifier works in stages:
    1. Extract colored regions and contours from the input image
    2. Find contours that resemble the Crimea peninsula (via Hu moments)
    3. Determine which country polygon contains the Crimea shape
    4. Check for dashed borders (disputed representation)
    """

    def __init__(self, templates_dir: Path | None = None):
        self.templates = load_templates(templates_dir)
        self._crimea_hu = self.templates["crimea"]["hu_moments"]
        self._crimea_contour = self.templates["crimea"]["contour"]
        self._ua_crimea_mask = self.templates["ukraine"].get("crimea_mask")
        self._ru_crimea_mask = self.templates["russia"].get("crimea_mask")

    def classify(self, image_path: str | Path, verbose: bool = False) -> ClassificationResult:
        """
        Classify a map image.

        Args:
            image_path: Path to the image file
            verbose: If True, include extra details in the result

        Returns:
            ClassificationResult with label, confidence, and details
        """
        path = Path(image_path)
        if not path.exists():
            return ClassificationResult("absent", 0.0, {"error": f"File not found: {path}"})

        image = cv2.imread(str(path))
        if image is None:
            return ClassificationResult("absent", 0.0, {"error": f"Could not read image: {path}"})

        return self.classify_image(image, verbose=verbose)

    def classify_image(self, image: np.ndarray, verbose: bool = False) -> ClassificationResult:
        """Classify a map image from a numpy array (BGR format)."""
        image = preprocess_image(image)
        h, w = image.shape[:2]

        details: dict = {
            "image_size": f"{w}x{h}",
            "crimea_detected": False,
        }

        # Stage 1: Extract contours from colored regions
        all_contours = extract_all_contours(image, n_colors=10)
        details["total_contours"] = len(all_contours)

        if not all_contours:
            return ClassificationResult("absent", 0.5, details)

        # Stage 2: Find Crimea-like shapes
        candidates = find_crimea_region(image, all_contours, self._crimea_hu, max_candidates=5)

        if not candidates:
            return ClassificationResult("absent", 0.5, details)

        best_contour, best_distance = candidates[0]
        details["best_match_distance"] = round(best_distance, 4)

        # Threshold: if the best match is too far from the Crimea template, it's absent
        if best_distance > 3.0:
            details["reason"] = "No contour sufficiently matches Crimea shape"
            return ClassificationResult("absent", 0.6, details)

        details["crimea_detected"] = True
        crimea_area = cv2.contourArea(best_contour)
        details["crimea_area_px"] = int(crimea_area)

        # Stage 3: Determine which country "owns" the Crimea contour
        # Strategy: For each large contour in the image, check if Crimea's centroid
        # falls inside it, then match that contour against UA/RU templates

        crimea_moments = cv2.moments(best_contour)
        if crimea_moments["m00"] == 0:
            return ClassificationResult("uncertain", 0.3, details)

        crimea_cx = int(crimea_moments["m10"] / crimea_moments["m00"])
        crimea_cy = int(crimea_moments["m01"] / crimea_moments["m00"])
        details["crimea_centroid"] = [crimea_cx, crimea_cy]

        # Find the parent contour containing Crimea
        parent_contour = self._find_parent_contour(all_contours, best_contour, crimea_cx, crimea_cy)

        if parent_contour is None:
            # Crimea is its own region (standalone / disputed)
            dashedness = detect_dashed_border(image, best_contour)
            details["dashedness"] = round(dashedness, 3)
            if dashedness > 0.3:
                return ClassificationResult("disputed", 0.7, details)
            return ClassificationResult("uncertain", 0.4, details)

        # Stage 4: Match parent contour against country templates
        result = self._classify_parent(parent_contour, best_contour, image, details, verbose)

        # Stage 5: Check for dashed borders (overrides to "disputed")
        dashedness = detect_dashed_border(image, best_contour)
        details["dashedness"] = round(dashedness, 3)
        if dashedness > 0.5 and result.label in ("ukraine", "russia"):
            details["override_reason"] = "Dashed border detected"
            return ClassificationResult("disputed", 0.65, details)

        return result

    def _find_parent_contour(
        self,
        all_contours: list[np.ndarray],
        crimea_contour: np.ndarray,
        cx: int,
        cy: int,
    ) -> np.ndarray | None:
        """Find the country contour that contains the Crimea centroid."""
        crimea_area = cv2.contourArea(crimea_contour)

        for contour in all_contours:
            area = cv2.contourArea(contour)
            # Parent must be significantly larger than Crimea
            if area <= crimea_area * 1.5:
                continue
            if contour_contains_point(contour, (cx, cy)):
                return contour

        # Also check: Crimea contour might BE part of the country contour
        # (same color region). Look for the largest contour from the same mask.
        return None

    def _classify_parent(
        self,
        parent: np.ndarray,
        crimea: np.ndarray,
        image: np.ndarray,
        details: dict,
        verbose: bool,
    ) -> ClassificationResult:
        """Classify the parent contour as Ukraine or Russia."""
        parent_hu = compute_hu_moments(parent)

        ua_hu = self.templates["ukraine"].get("hu_moments")
        ru_hu = self.templates["russia"].get("hu_moments")
        ua_contour = self.templates["ukraine"].get("contour")
        ru_contour = self.templates["russia"].get("contour")

        # Method 1: Hu moment distance to country templates
        ua_dist = hu_distance(parent_hu, ua_hu) if ua_hu is not None else float("inf")
        ru_dist = hu_distance(parent_hu, ru_hu) if ru_hu is not None else float("inf")

        details["match_ukraine_hu"] = round(ua_dist, 4)
        details["match_russia_hu"] = round(ru_dist, 4)

        # Method 2: cv2.matchShapes for direct contour comparison
        if ua_contour is not None:
            ua_shape_dist = match_shape(parent, ua_contour)
            details["match_ukraine_shape"] = round(ua_shape_dist, 4)
        else:
            ua_shape_dist = float("inf")

        if ru_contour is not None:
            ru_shape_dist = match_shape(parent, ru_contour)
            details["match_russia_shape"] = round(ru_shape_dist, 4)
        else:
            ru_shape_dist = float("inf")

        # Method 3: Area ratio heuristic
        # Ukraine-with-Crimea has a specific area ratio to Crimea
        parent_area = cv2.contourArea(parent)
        crimea_area = cv2.contourArea(crimea)
        area_ratio = parent_area / max(crimea_area, 1)
        details["parent_crimea_area_ratio"] = round(area_ratio, 2)

        # Combine signals — weighted vote
        ua_score = 0.0
        ru_score = 0.0

        # Hu moment distance (lower = better match)
        if ua_dist < ru_dist:
            ua_score += 1.0 * (1.0 - ua_dist / (ua_dist + ru_dist + 1e-10))
            ru_score += 1.0 * (1.0 - ru_dist / (ua_dist + ru_dist + 1e-10))
        else:
            ru_score += 1.0 * (1.0 - ru_dist / (ua_dist + ru_dist + 1e-10))
            ua_score += 1.0 * (1.0 - ua_dist / (ua_dist + ru_dist + 1e-10))

        # Shape match distance (lower = better)
        if ua_shape_dist < ru_shape_dist:
            ua_score += 1.5
        elif ru_shape_dist < ua_shape_dist:
            ru_score += 1.5

        # Area ratio: Ukraine is ~5-15x Crimea, Russia is ~600x
        if 3 < area_ratio < 25:
            ua_score += 1.0
        elif area_ratio > 50:
            ru_score += 1.0

        details["score_ukraine"] = round(ua_score, 3)
        details["score_russia"] = round(ru_score, 3)

        total = ua_score + ru_score
        if total == 0:
            return ClassificationResult("uncertain", 0.3, details)

        if ua_score > ru_score:
            confidence = min(0.95, ua_score / total)
            return ClassificationResult("ukraine", confidence, details)
        elif ru_score > ua_score:
            confidence = min(0.95, ru_score / total)
            return ClassificationResult("russia", confidence, details)
        else:
            return ClassificationResult("uncertain", 0.4, details)

    def classify_batch(
        self, image_paths: list[str | Path], verbose: bool = False
    ) -> list[tuple[str, ClassificationResult]]:
        """Classify multiple images."""
        results = []
        for path in image_paths:
            result = self.classify(path, verbose=verbose)
            results.append((str(path), result))
        return results
