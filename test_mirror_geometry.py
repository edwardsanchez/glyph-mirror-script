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
    NoSeamPointsError
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

