# encoding: utf-8
"""
Unit tests for mirror_geometry module.
Run with: pytest test_mirror_geometry.py
"""

import pytest
from mirror_geometry import (
    Point,
    mirror_horizontal,
    mirror_vertical,
    find_seam_points,
    validate_seam_alignment,
    almost_equal,
    MirrorError,
    SeamAlignmentError,
    NoSeamPointsError,
    calculate_axis_from_bounds,
)


def assert_points_close(actual, expected, tol=0.01):
    """Compare two lists of points with tolerance."""
    assert len(actual) == len(expected), \
        f"Point count mismatch: {len(actual)} vs {len(expected)}"
    
    for i, (a, e) in enumerate(zip(actual, expected)):
        assert almost_equal(a.x, e.x, tol), \
            f"Point {i} x mismatch: {a.x} vs {e.x}"
        assert almost_equal(a.y, e.y, tol), \
            f"Point {i} y mismatch: {a.y} vs {e.y}"
        assert a.on_curve == e.on_curve, \
            f"Point {i} on_curve mismatch: {a.on_curve} vs {e.on_curve}"


class TestAlmostEqual:
    def test_equal_values(self):
        assert almost_equal(1.0, 1.0)
    
    def test_within_tolerance(self):
        assert almost_equal(1.0, 1.005, eps=0.01)
    
    def test_outside_tolerance(self):
        assert not almost_equal(1.0, 1.02, eps=0.01)


class TestFindSeamPoints:
    def test_find_horizontal_seam(self):
        points = [
            Point(0.0, 10.0, True),    # on seam
            Point(0.5, 5.0, True),     # on seam
            Point(-0.5, 0.0, True),    # on seam
            Point(10.0, 5.0, True),    # far from seam
            Point(0.0, 8.0, False),    # off-curve, should be ignored
        ]
        seam = find_seam_points(points, axis_value=0.0, center_band=1.0, check_x=True)
        assert len(seam) == 3
        assert all(p.on_curve for p in seam)
    
    def test_find_vertical_seam(self):
        points = [
            Point(10.0, 100.0, True),   # on seam
            Point(5.0, 99.5, True),     # on seam
            Point(0.0, 110.0, True),    # far from seam
            Point(8.0, 100.0, False),   # off-curve, should be ignored
        ]
        seam = find_seam_points(points, axis_value=100.0, center_band=1.0, check_x=False)
        assert len(seam) == 2
        assert all(p.on_curve for p in seam)
    
    def test_no_seam_points(self):
        points = [Point(10.0, 10.0, True), Point(20.0, 20.0, True)]
        seam = find_seam_points(points, axis_value=0.0, center_band=1.0, check_x=True)
        assert len(seam) == 0


class TestValidateSeamAlignment:
    def test_aligned_seam(self):
        points = [
            Point(10.0, 0.0, True),
            Point(10.0, 5.0, True),
            Point(10.0, 10.0, True),
        ]
        aligned_x = validate_seam_alignment(points, check_x=True, eps=0.01)
        assert almost_equal(aligned_x, 10.0, eps=0.001)
    
    def test_slightly_misaligned_within_tolerance(self):
        points = [
            Point(10.0, 0.0, True),
            Point(10.005, 5.0, True),
        ]
        # Should pass with eps=0.01
        aligned_x = validate_seam_alignment(points, check_x=True, eps=0.01)
        assert almost_equal(aligned_x, 10.0025, eps=0.01)
    
    def test_misaligned_seam_raises_error(self):
        points = [
            Point(10.0, 0.0, True),
            Point(11.0, 5.0, True),  # Too far off
        ]
        with pytest.raises(SeamAlignmentError):
            validate_seam_alignment(points, check_x=True, eps=0.01)
    
    def test_empty_seam_raises_error(self):
        with pytest.raises(NoSeamPointsError):
            validate_seam_alignment([], check_x=True)


class TestCalculateAxisFromBounds:
    def test_calculates_x_axis_center(self):
        points = [
            Point(-50.0, 0.0, True),
            Point(50.0, 0.0, True),
            Point(20.0, 10.0, False),
        ]
        axis = calculate_axis_from_bounds(points, check_x=True)
        assert almost_equal(axis, 0.0, eps=0.001)

    def test_calculates_y_axis_center(self):
        points = [
            Point(0.0, 10.0, True),
            Point(0.0, 30.0, True),
        ]
        axis = calculate_axis_from_bounds(points, check_x=False)
        assert almost_equal(axis, 20.0, eps=0.001)

    def test_empty_points_raise_error(self):
        with pytest.raises(MirrorError):
            calculate_axis_from_bounds([], check_x=True)


class TestMirrorHorizontal:
    def test_simple_triangle_left_source(self):
        """Mirror a simple left-side triangle to the right."""
        points = [
            Point(-10.0, 0.0, True),   # left bottom
            Point(0.0, 10.0, True),    # seam top
            Point(0.0, 0.0, True),     # seam bottom
        ]
        
        result = mirror_horizontal(points, axis_x=0.0, source_side="left", center_band=1.0)
        
        # Should have original + mirrored
        assert len(result) == 6
        
        # Check the mirrored left bottom point
        assert any(almost_equal(p.x, 10.0) and almost_equal(p.y, 0.0) for p in result)
    
    def test_simple_triangle_right_source(self):
        """Mirror a simple right-side triangle to the left."""
        points = [
            Point(0.0, 0.0, True),     # seam bottom
            Point(0.0, 10.0, True),    # seam top
            Point(10.0, 0.0, True),    # right bottom
        ]
        
        result = mirror_horizontal(points, axis_x=0.0, source_side="right", center_band=1.0)
        
        # Should have original + mirrored
        assert len(result) == 6
        
        # Check the mirrored right bottom point
        assert any(almost_equal(p.x, -10.0) and almost_equal(p.y, 0.0) for p in result)
    
    def test_with_off_curve_handles(self):
        """Ensure off-curve points (handles) are mirrored correctly."""
        points = [
            Point(-10.0, 0.0, True),    # on-curve left
            Point(-5.0, 5.0, False),    # off-curve handle
            Point(0.0, 10.0, True),     # on-curve seam
            Point(0.0, 0.0, True),      # on-curve seam
        ]
        
        result = mirror_horizontal(points, axis_x=0.0, source_side="left")
        
        # Check that off-curve points are mirrored
        mirrored_handle = [p for p in result if almost_equal(p.x, 5.0) and almost_equal(p.y, 5.0)]
        assert len(mirrored_handle) == 1
        assert mirrored_handle[0].on_curve == False
    
    def test_non_zero_axis(self):
        """Mirror around an axis that's not at x=0."""
        points = [
            Point(90.0, 0.0, True),    # left of axis
            Point(100.0, 10.0, True),  # seam
            Point(100.0, 0.0, True),   # seam
        ]
        
        result = mirror_horizontal(points, axis_x=100.0, source_side="left")
        
        # Original point at 90 should mirror to 110
        assert any(almost_equal(p.x, 110.0) and almost_equal(p.y, 0.0) for p in result)
    
    def test_misaligned_seam_raises_error(self):
        """Should raise error when seam points are not aligned."""
        points = [
            Point(-10.0, 0.0, True),
            Point(0.0, 0.0, True),     # seam at x=0
            Point(1.0, 10.0, True),    # seam at x=1 - misaligned!
        ]
        
        with pytest.raises(SeamAlignmentError):
            mirror_horizontal(points, axis_x=0.0, source_side="left")
    
    def test_no_seam_points_raises_error(self):
        """Should raise error when no seam points are found."""
        points = [
            Point(-10.0, 0.0, True),
            Point(-5.0, 10.0, True),
        ]
        
        with pytest.raises(NoSeamPointsError):
            mirror_horizontal(points, axis_x=0.0, source_side="left", center_band=1.0)

    def test_bounds_fallback_no_seam_horizontal(self):
        """Mirror using bounds when no seam nodes are selected."""
        selected = [
            Point(10.0, 0.0, True),
            Point(20.0, 40.0, True),
        ]
        whole_path = selected + [
            Point(190.0, 0.0, True),
            Point(180.0, 40.0, True),
        ]

        result = mirror_horizontal(
            selected,
            axis_x=0.0,
            source_side="left",
            all_path_points=whole_path,
        )

        # Expect two mirrored points on the right half
        assert len(result) == 4
        assert any(almost_equal(p.x, 190.0) and almost_equal(p.y, 0.0) for p in result)
        assert any(almost_equal(p.x, 180.0) and almost_equal(p.y, 40.0) for p in result)

    def test_seam_points_take_precedence_over_bounds(self):
        """When seam nodes exist, ignore bounds-only axis."""
        selected = [
            Point(-10.0, 0.0, True),
            Point(0.0, 5.0, True),  # seam
            Point(0.0, 0.0, True),  # seam
        ]
        whole_path = selected + [
            Point(30.0, 0.0, True),  # far right point -> different bounds center
        ]

        result = mirror_horizontal(
            selected,
            axis_x=0.0,
            source_side="left",
            all_path_points=whole_path,
        )

        # Seam-based axis (x=0) should be used, so left point mirrors to x=10
        assert any(almost_equal(p.x, 10.0) and almost_equal(p.y, 0.0) for p in result)

class TestMirrorVertical:
    def test_simple_trapezoid_top_source(self):
        """Mirror a top trapezoid downward."""
        points = [
            Point(0.0, 100.0, True),   # seam left
            Point(10.0, 100.0, True),  # seam right
            Point(5.0, 110.0, True),   # top middle
        ]
        
        result = mirror_vertical(points, axis_y=100.0, source_side="top")
        
        # Should have original + mirrored
        assert len(result) == 6
        
        # Top middle at y=110 should mirror to y=90
        assert any(almost_equal(p.x, 5.0) and almost_equal(p.y, 90.0) for p in result)
    
    def test_simple_trapezoid_bottom_source(self):
        """Mirror a bottom trapezoid upward."""
        points = [
            Point(5.0, 90.0, True),    # bottom middle
            Point(0.0, 100.0, True),   # seam left
            Point(10.0, 100.0, True),  # seam right
        ]
        
        result = mirror_vertical(points, axis_y=100.0, source_side="bottom")
        
        # Should have original + mirrored
        assert len(result) == 6
        
        # Bottom middle at y=90 should mirror to y=110
        assert any(almost_equal(p.x, 5.0) and almost_equal(p.y, 110.0) for p in result)
    
    def test_with_handles_vertical(self):
        """Ensure off-curve points are handled correctly in vertical mirror."""
        points = [
            Point(0.0, 100.0, True),   # seam
            Point(5.0, 105.0, False),  # off-curve handle above seam
            Point(10.0, 110.0, True),  # on-curve above seam
        ]
        
        result = mirror_vertical(points, axis_y=100.0, source_side="top")
        
        # Handle at y=105 should mirror to y=95
        mirrored_handle = [p for p in result if almost_equal(p.y, 95.0)]
        assert len(mirrored_handle) == 1
        assert mirrored_handle[0].on_curve == False
    
    def test_non_zero_axis_vertical(self):
        """Mirror around a non-zero y axis."""
        points = [
            Point(0.0, 500.0, True),   # seam
            Point(10.0, 500.0, True),  # seam
            Point(5.0, 510.0, True),   # above seam
        ]
        
        result = mirror_vertical(points, axis_y=500.0, source_side="top")
        
        # Point at y=510 should mirror to y=490
        assert any(almost_equal(p.y, 490.0) for p in result)
    
    def test_misaligned_vertical_seam_raises_error(self):
        """Should raise error when vertical seam is not aligned."""
        points = [
            Point(0.0, 100.0, True),   # seam at y=100
            Point(10.0, 101.0, True),  # seam at y=101 - misaligned!
            Point(5.0, 110.0, True),
        ]
        
        with pytest.raises(SeamAlignmentError):
            mirror_vertical(points, axis_y=100.0, source_side="top")

    def test_bounds_fallback_no_seam_vertical(self):
        """Mirror vertically using bounds fallback."""
        selected = [
            Point(0.0, 120.0, True),
            Point(10.0, 110.0, True),
        ]
        whole_path = selected + [
            Point(0.0, 80.0, True),
            Point(10.0, 70.0, True),
        ]

        result = mirror_vertical(
            selected,
            axis_y=0.0,
            source_side="top",
            all_path_points=whole_path,
        )

        # Total bounds center is (70 + 120)/2 = 95, so mirrored y should be 70 and 80
        assert any(almost_equal(p.y, 70.0) for p in result)
        assert any(almost_equal(p.y, 80.0) for p in result)


class TestToleranceBoundaries:
    def test_point_exactly_on_seam(self):
        """Point exactly on the seam should be included in both halves."""
        points = [
            Point(0.0, 0.0, True),
            Point(0.0, 10.0, True),
        ]
        
        result = mirror_horizontal(points, axis_x=0.0, source_side="left")
        
        # Seam points should be in both source and mirrored (so duplicated)
        seam_points = [p for p in result if almost_equal(p.x, 0.0)]
        assert len(seam_points) >= 2
    
    def test_center_band_edge_case(self):
        """Points near the seam within center_band."""
        points = [
            Point(-10.0, 0.0, True),   # far from seam
            Point(0.0, 5.0, True),     # on seam
            Point(0.0, 10.0, True),    # on seam
        ]
        
        # With center_band=1.0, both seam points should be found and aligned
        result = mirror_horizontal(points, axis_x=0.0, source_side="left", center_band=1.0)
        # Should not raise an error
        assert len(result) > 0
        # Far point should be mirrored
        assert any(almost_equal(p.x, 10.0) and almost_equal(p.y, 0.0) for p in result)


class TestNodeCountValidation:
    """Test that mirroring produces correct node counts."""
    
    def test_seam_aligned_node_count(self):
        """
        With perfectly aligned seam: final = selected * 2 - seam_count
        Seam nodes should not be duplicated.
        """
        # 5 selected nodes, 2 are on seam (x=0)
        selected = [
            Point(-10.0, 0.0, True),   # left
            Point(-5.0, 5.0, False),   # handle
            Point(0.0, 10.0, True),    # SEAM
            Point(0.0, 0.0, True),     # SEAM
            Point(-5.0, -5.0, False),  # handle
        ]
        
        result = mirror_horizontal(
            selected,
            axis_x=0.0,
            source_side="left",
            center_band=1.0,
        )
        
        # Expected: 5 * 2 - 2 = 8 nodes (2 seam nodes not duplicated)
        # But our function returns source + mirrored (including seam duplicates)
        # The Glyphs script handles deduplication, geometry module just mirrors
        assert len(result) == 10  # 5 source + 5 mirrored
        
        # Check that seam nodes appear twice (will be deduplicated by Glyphs)
        seam_nodes = [p for p in result if almost_equal(p.x, 0.0)]
        assert len(seam_nodes) == 4  # 2 original + 2 mirrored at same position
    
    def test_no_seam_node_count(self):
        """
        Without seam nodes: final = selected * 2
        All nodes get mirrored.
        """
        # 4 selected nodes, none on seam
        selected = [
            Point(10.0, 0.0, True),
            Point(15.0, 5.0, False),
            Point(20.0, 10.0, True),
            Point(15.0, -5.0, False),
        ]
        
        # Full path bounds: x=[10, 100], so axis = 55
        all_path = selected + [
            Point(80.0, 0.0, True),
            Point(100.0, 10.0, True),
        ]
        
        result = mirror_horizontal(
            selected,
            axis_x=50.0,  # Will be overridden by bounds since no seam at 50
            source_side="left",
            center_band=1.0,
            all_path_points=all_path,
        )
        
        # Expected: 4 * 2 = 8 nodes
        assert len(result) == 8
        
        # Verify mirrored positions (axis = 55, so x' = 110 - x)
        # Original (10, 0) -> mirrored (100, 0)
        assert any(almost_equal(p.x, 100.0) and almost_equal(p.y, 0.0) for p in result)


class TestRoundedRectangleCase:
    """Test the specific rounded rectangle case from the user."""
    
    def test_left_half_to_full_rounded_rect(self):
        """
        Mirror a left half of a rounded rectangle to create the full shape.
        
        Original (left half, open path):
        - (202, 0) on-curve (top)
        - (71, 0) handle
        - (0, 70) handle
        - (0, 202) on-curve
        - (0, 1170) on-curve
        - (0, 1301) handle
        - (71, 1372) handle
        - (202, 1372) on-curve (bottom)
        
        Full bounds would be x=[0, 1372], so axis = 686
        Mirror formula: x' = 1372 - x
        """
        # The selected left half
        selected = [
            Point(202.0, 0.0, True),      # top endpoint
            Point(71.0, 0.0, False),      # handle
            Point(0.0, 70.0, False),      # handle
            Point(0.0, 202.0, True),      # on-curve
            Point(0.0, 1170.0, True),     # on-curve
            Point(0.0, 1301.0, False),    # handle
            Point(71.0, 1372.0, False),   # handle
            Point(202.0, 1372.0, True),   # bottom endpoint
        ]
        
        # Full path bounds (including the other half we want to create)
        # Left side goes 0-202, right side would go 1170-1372
        # Total: 0-1372
        all_path_points = selected + [
            Point(1170.0, 0.0, True),
            Point(1372.0, 202.0, True),
            Point(1372.0, 1170.0, True),
            Point(1170.0, 1372.0, True),
        ]
        
        # No seam points at axis (axis=686, but no points near 686)
        result = mirror_horizontal(
            selected,
            axis_x=686.0,  # Will be ignored since no seam, uses bounds
            source_side="left",
            center_band=5.0,
            all_path_points=all_path_points,
        )
        
        # Axis from bounds: (0 + 1372) / 2 = 686
        # Check mirrored points exist (x' = 1372 - x)
        
        # Original (202, 0) -> mirrored (1170, 0)
        assert any(almost_equal(p.x, 1170.0) and almost_equal(p.y, 0.0) and p.on_curve for p in result), \
            "Missing mirrored point (1170, 0)"
        
        # Original handle (71, 0) -> mirrored (1301, 0)
        assert any(almost_equal(p.x, 1301.0) and almost_equal(p.y, 0.0) and not p.on_curve for p in result), \
            "Missing mirrored handle (1301, 0)"
        
        # Original handle (0, 70) -> mirrored (1372, 70)
        assert any(almost_equal(p.x, 1372.0) and almost_equal(p.y, 70.0) and not p.on_curve for p in result), \
            "Missing mirrored handle (1372, 70)"
        
        # Original (0, 202) -> mirrored (1372, 202)
        assert any(almost_equal(p.x, 1372.0) and almost_equal(p.y, 202.0) and p.on_curve for p in result), \
            "Missing mirrored point (1372, 202)"
        
        # Original (0, 1170) -> mirrored (1372, 1170)
        assert any(almost_equal(p.x, 1372.0) and almost_equal(p.y, 1170.0) and p.on_curve for p in result), \
            "Missing mirrored point (1372, 1170)"
        
        # Original handle (0, 1301) -> mirrored (1372, 1301)
        assert any(almost_equal(p.x, 1372.0) and almost_equal(p.y, 1301.0) and not p.on_curve for p in result), \
            "Missing mirrored handle (1372, 1301)"
        
        # Original handle (71, 1372) -> mirrored (1301, 1372)
        assert any(almost_equal(p.x, 1301.0) and almost_equal(p.y, 1372.0) and not p.on_curve for p in result), \
            "Missing mirrored handle (1301, 1372)"
        
        # Original (202, 1372) -> mirrored (1170, 1372)
        assert any(almost_equal(p.x, 1170.0) and almost_equal(p.y, 1372.0) and p.on_curve for p in result), \
            "Missing mirrored point (1170, 1372)"
        
        # Also verify original points are preserved
        assert any(almost_equal(p.x, 202.0) and almost_equal(p.y, 0.0) for p in result), \
            "Original point (202, 0) should be preserved"
        assert any(almost_equal(p.x, 71.0) and almost_equal(p.y, 0.0) for p in result), \
            "Original handle (71, 0) should be preserved"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

