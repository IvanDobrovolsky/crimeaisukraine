"""
Contour extraction and shape matching for CrimeaLens.

Handles the core CV pipeline: color segmentation, contour detection,
and Hu moment-based shape comparison.
"""

import cv2
import numpy as np


def preprocess_image(image: np.ndarray, max_dim: int = 1024) -> np.ndarray:
    """Resize image if too large, keeping aspect ratio."""
    h, w = image.shape[:2]
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        image = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    return image


def extract_colored_regions(image: np.ndarray, n_colors: int = 8) -> list[np.ndarray]:
    """
    Extract distinct colored regions from an image via k-means color quantization.

    Returns a list of binary masks, one per dominant color cluster.
    """
    h, w = image.shape[:2]
    pixels = image.reshape(-1, 3).astype(np.float32)

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    _, labels, centers = cv2.kmeans(
        pixels, n_colors, None, criteria, 3, cv2.KMEANS_PP_CENTERS
    )

    labels = labels.flatten().reshape(h, w)
    masks = []
    for i in range(n_colors):
        mask = (labels == i).astype(np.uint8) * 255
        # Filter out very small or very large regions (background)
        area = np.count_nonzero(mask)
        total = h * w
        if 0.005 * total < area < 0.6 * total:
            masks.append(mask)

    return masks


def extract_contours_from_mask(
    mask: np.ndarray, min_area: int = 500
) -> list[np.ndarray]:
    """Extract contours from a binary mask, filtering by minimum area."""
    # Clean up mask with morphological operations
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    return [c for c in contours if cv2.contourArea(c) >= min_area]


def extract_all_contours(image: np.ndarray, n_colors: int = 8) -> list[np.ndarray]:
    """Extract all significant contours from an image."""
    masks = extract_colored_regions(image, n_colors)
    all_contours = []
    for mask in masks:
        contours = extract_contours_from_mask(mask)
        all_contours.extend(contours)
    return all_contours


def compute_hu_moments(contour: np.ndarray) -> np.ndarray:
    """Compute log-transformed Hu moments for a contour."""
    moments = cv2.moments(contour)
    hu = cv2.HuMoments(moments).flatten()
    return -np.sign(hu) * np.log10(np.abs(hu) + 1e-30)


def match_shape(contour: np.ndarray, template_contour: np.ndarray) -> float:
    """
    Compare two contours using cv2.matchShapes with Hu moments.

    Returns a distance score (lower = more similar).
    Uses method I2 (log-chi-squared) which is most robust.
    """
    return cv2.matchShapes(contour, template_contour, cv2.CONTOURS_MATCH_I2, 0.0)


def hu_distance(hu1: np.ndarray, hu2: np.ndarray) -> float:
    """Compute Euclidean distance between two Hu moment vectors."""
    return float(np.linalg.norm(hu1 - hu2))


def cosine_similarity(hu1: np.ndarray, hu2: np.ndarray) -> float:
    """Compute cosine similarity between two Hu moment vectors."""
    dot = np.dot(hu1, hu2)
    norm1 = np.linalg.norm(hu1)
    norm2 = np.linalg.norm(hu2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(dot / (norm1 * norm2))


def contour_contains_point(contour: np.ndarray, point: tuple[int, int]) -> bool:
    """Check if a point is inside a contour."""
    result = cv2.pointPolygonTest(contour, point, False)
    return result >= 0


def find_crimea_region(
    image: np.ndarray, contours: list[np.ndarray], template_hu: np.ndarray,
    max_candidates: int = 10,
) -> list[tuple[np.ndarray, float]]:
    """
    Find contours that most resemble the Crimea peninsula shape.

    Returns list of (contour, distance) tuples, sorted by match quality.
    """
    scored = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < 200:
            continue
        hu = compute_hu_moments(contour)
        dist = hu_distance(hu, template_hu)
        scored.append((contour, dist))

    scored.sort(key=lambda x: x[1])
    return scored[:max_candidates]


def detect_dashed_border(
    image: np.ndarray, contour: np.ndarray, sample_points: int = 20
) -> float:
    """
    Detect if a border around a contour is dashed (indicating disputed territory).

    Returns a "dashedness" score between 0.0 (solid) and 1.0 (dashed).
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image

    # Sample points along the contour
    total_points = len(contour)
    if total_points < sample_points:
        return 0.0

    step = total_points // sample_points
    border_values = []

    for i in range(0, total_points, step):
        pt = contour[i][0]
        x, y = int(pt[0]), int(pt[1])
        # Sample a small neighborhood around the border point
        y1, y2 = max(0, y - 2), min(gray.shape[0], y + 3)
        x1, x2 = max(0, x - 2), min(gray.shape[1], x + 3)
        patch = gray[y1:y2, x1:x2]
        if patch.size > 0:
            border_values.append(float(np.std(patch)))

    if not border_values:
        return 0.0

    # High variance in border intensities suggests dashing
    overall_variance = np.std(border_values)
    # Normalize to 0-1 range (empirical thresholds)
    dashedness = min(1.0, overall_variance / 40.0)
    return dashedness
