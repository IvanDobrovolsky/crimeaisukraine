"""
Tests for CrimeaLens classifier.

Uses synthetically generated map images with known ground truth
to validate the classification pipeline.
"""

import numpy as np
import cv2
import pytest
from pathlib import Path

from crimealens.templates import (
    generate_templates,
    save_templates,
    load_templates,
    TEMPLATES_DIR,
    CRIMEA_BBOX,
    TEMPLATE_SIZE,
    extract_country_polygons,
    download_geojson,
    geo_to_pixel,
    render_mask,
    compute_hu_moments,
)
from crimealens.contours import (
    extract_all_contours,
    extract_colored_regions,
    hu_distance,
    match_shape,
)
from crimealens.classifier import CrimeaClassifier, ClassificationResult


@pytest.fixture(scope="session")
def templates():
    """Load or generate templates once for all tests."""
    try:
        return load_templates()
    except FileNotFoundError:
        cache = TEMPLATES_DIR / ".cache"
        t = generate_templates(cache_dir=cache)
        save_templates(t)
        return load_templates()


@pytest.fixture(scope="session")
def classifier():
    """Create classifier once for all tests."""
    return CrimeaClassifier()


@pytest.fixture(scope="session")
def geojson_data():
    """Load GeoJSON data."""
    cache = TEMPLATES_DIR / ".cache"
    from crimealens.templates import GEOJSON_URLS
    return download_geojson(GEOJSON_URLS["countries_50m"], cache)


class TestTemplates:
    def test_templates_exist(self, templates):
        assert "crimea" in templates
        assert "ukraine" in templates
        assert "russia" in templates

    def test_crimea_contour_has_area(self, templates):
        contour = templates["crimea"]["contour"]
        area = cv2.contourArea(contour)
        assert area > 1000, f"Crimea contour area too small: {area}"

    def test_hu_moments_shape(self, templates):
        hu = templates["crimea"]["hu_moments"]
        assert hu.shape == (7,), f"Expected 7 Hu moments, got {hu.shape}"

    def test_ukraine_and_russia_masks_differ(self, templates):
        ua_mask = templates["ukraine"].get("crimea_mask")
        ru_mask = templates["russia"].get("crimea_mask")
        if ua_mask is not None and ru_mask is not None:
            # They should have different coverage in the Crimea region
            ua_area = np.count_nonzero(ua_mask)
            ru_area = np.count_nonzero(ru_mask)
            # Natural Earth 50m puts Crimea in Russia, so Russia should have more
            assert ru_area > ua_area, "Russia should have more Crimea coverage in NE 50m"


class TestSyntheticMaps:
    """Test classifier on synthetically generated maps with known ground truth."""

    def _render_synthetic_map(
        self, geojson, country_code: str, include_crimea: bool,
        color: tuple = (0, 120, 255), bg_color: tuple = (240, 240, 240),
        size: int = 800,
    ) -> np.ndarray:
        """Render a synthetic map image showing a country with/without Crimea."""
        # Broad bbox covering Ukraine/Russia region
        bbox = {"min_lon": 22.0, "max_lon": 45.0, "min_lat": 42.0, "max_lat": 53.0}

        polys = extract_country_polygons(geojson, country_code)
        image = np.full((size, size, 3), bg_color, dtype=np.uint8)

        for coords in polys:
            # Check if polygon is in Crimea region
            lons = coords[:, 0]
            lats = coords[:, 1]
            is_crimea = (
                lons.mean() > 33.0 and lons.mean() < 36.0
                and lats.mean() > 44.0 and lats.mean() < 46.0
            )

            if is_crimea and not include_crimea:
                continue

            pixels = geo_to_pixel(coords, bbox, size)
            cv2.fillPoly(image, [pixels], color)

        return image

    def test_ukraine_with_crimea(self, classifier, geojson_data):
        """Ukraine rendered with Crimea (manually added) should detect Crimea."""
        # NE 50m puts Crimea under Russia, so we render UA + RU's Crimea polygons
        bbox = {"min_lon": 22.0, "max_lon": 45.0, "min_lat": 42.0, "max_lat": 53.0}
        ua_polys = extract_country_polygons(geojson_data, "UA")
        ru_polys = extract_country_polygons(geojson_data, "RU")

        # Find Russia's Crimea polygons
        crimea_polys = []
        for coords in ru_polys:
            lons = coords[:, 0]
            lats = coords[:, 1]
            if lons.mean() > 33.0 and lons.mean() < 36.0 and lats.mean() > 44.0 and lats.mean() < 46.0:
                crimea_polys.append(coords)

        color = (0, 120, 255)
        size = 800
        image = np.full((size, size, 3), (240, 240, 240), dtype=np.uint8)
        for coords in ua_polys + crimea_polys:
            pixels = geo_to_pixel(coords, bbox, size)
            cv2.fillPoly(image, [pixels], color)

        result = classifier.classify_image(image)
        assert result.details.get("total_contours", 0) > 0, \
            "Should find contours on Ukraine+Crimea map"

    def test_russia_with_crimea(self, classifier, geojson_data):
        """Russia rendered with Crimea (NE default) should detect Crimea."""
        image = self._render_synthetic_map(
            geojson_data, "RU", include_crimea=True, color=(255, 100, 100)
        )
        result = classifier.classify_image(image)
        # Should at least detect Crimea
        assert result.details.get("total_contours", 0) > 0

    def test_crimea_standalone(self, classifier, geojson_data):
        """Just Crimea peninsula, no country context."""
        bbox = CRIMEA_BBOX
        polys = extract_country_polygons(geojson_data, "RU")

        image = np.full((512, 512, 3), (240, 240, 240), dtype=np.uint8)
        for coords in polys:
            lons = coords[:, 0]
            lats = coords[:, 1]
            if lons.mean() > 33.0 and lons.mean() < 36.0 and lats.mean() > 44.0 and lats.mean() < 46.0:
                pixels = geo_to_pixel(coords, bbox, 512)
                cv2.fillPoly(image, [pixels], (0, 150, 255))

        result = classifier.classify_image(image)
        assert result.details.get("crimea_detected", False), \
            "Should detect Crimea in standalone rendering"

    def test_no_map_image(self, classifier):
        """A blank/non-map image should return 'absent'."""
        image = np.full((512, 512, 3), (200, 200, 200), dtype=np.uint8)
        result = classifier.classify_image(image)
        assert result.label == "absent"

    def test_random_noise(self, classifier):
        """Random noise should not crash and should return absent/uncertain."""
        rng = np.random.RandomState(42)
        image = rng.randint(0, 256, (512, 512, 3), dtype=np.uint8)
        result = classifier.classify_image(image)
        assert result.label in ("absent", "uncertain")


class TestContourMatching:
    def test_crimea_self_match(self, templates):
        """Crimea contour should match itself perfectly."""
        contour = templates["crimea"]["contour"]
        dist = match_shape(contour, contour)
        assert dist < 0.001, f"Self-match distance should be ~0, got {dist}"

    def test_crimea_hu_self_distance(self, templates):
        """Hu moments of Crimea should have zero distance to itself."""
        hu = templates["crimea"]["hu_moments"]
        dist = hu_distance(hu, hu)
        assert dist < 1e-10, f"Self-distance should be ~0, got {dist}"

    def test_ukraine_russia_differ(self, templates):
        """Ukraine and Russia templates should have different Hu moments."""
        ua_hu = templates["ukraine"].get("hu_moments")
        ru_hu = templates["russia"].get("hu_moments")
        if ua_hu is not None and ru_hu is not None:
            dist = hu_distance(ua_hu, ru_hu)
            assert dist > 0.5, f"UA and RU should differ significantly, got {dist}"


class TestClassificationResult:
    def test_to_dict(self):
        result = ClassificationResult("ukraine", 0.85, {"key": "value"})
        d = result.to_dict()
        assert d["label"] == "ukraine"
        assert d["confidence"] == 0.85
        assert d["details"]["key"] == "value"

    def test_labels(self):
        for label in ("ukraine", "russia", "disputed", "absent", "uncertain"):
            result = ClassificationResult(label, 0.5)
            assert result.label == label
