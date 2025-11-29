# encoding: utf-8
"""
Pure Python mirroring geometry logic for Glyphs scripts.
No Glyphs dependencies - can be unit tested independently.
"""

from collections import namedtuple

Point = namedtuple("Point", ["x", "y", "on_curve"])


class MirrorError(Exception):
    """Base exception for mirroring errors."""
    pass


class SeamAlignmentError(MirrorError):
    """Raised when seam points are not properly aligned."""
    pass


class NoSeamPointsError(MirrorError):
    """Raised when no seam points are found."""
    pass


def almost_equal(a, b, eps=0.01):
    """Check if two float values are equal within tolerance."""
    return abs(a - b) <= eps


def find_seam_points(points, axis_value, center_band=5.0, check_x=True):
    """
    Find on-curve points within center_band distance of the axis.
    
    Args:
        points: List of Point objects
        axis_value: The x or y coordinate of the seam axis
        center_band: Distance tolerance for considering a point "on the seam"
        check_x: If True, check x coordinate; if False, check y coordinate
    
    Returns:
        List of Point objects that are on-curve and within center_band of axis
    """
    seam_points = []
    for p in points:
        if not p.on_curve:
            continue
        coord = p.x if check_x else p.y
        if abs(coord - axis_value) <= center_band:
            seam_points.append(p)
    return seam_points


def validate_seam_alignment(seam_points, check_x=True, eps=0.01):
    """
    Validate that all seam points share the same x or y coordinate.
    
    Args:
        seam_points: List of Point objects on the seam
        check_x: If True, check x coordinate; if False, check y coordinate
        eps: Tolerance for alignment check
    
    Raises:
        SeamAlignmentError: If points are not aligned within tolerance
    
    Returns:
        The aligned coordinate value (average of seam points)
    """
    if not seam_points:
        raise NoSeamPointsError("No seam points found")
    
    coords = [p.x if check_x else p.y for p in seam_points]
    ref_coord = coords[0]
    
    for coord in coords[1:]:
        if not almost_equal(coord, ref_coord, eps):
            raise SeamAlignmentError(
                f"Seam points not aligned: found {ref_coord} and {coord}"
            )
    
    # Return the average for precise alignment
    return sum(coords) / len(coords)


def mirror_horizontal(points, axis_x, source_side="left", eps=0.01, center_band=5.0):
    """
    Mirror points horizontally across a vertical axis.
    
    Args:
        points: List of Point objects (selected half + seam)
        axis_x: X coordinate of the vertical seam line
        source_side: "left" or "right" - which side is the source
        eps: Tolerance for coordinate comparisons
        center_band: Distance tolerance for finding seam points
    
    Returns:
        List of Point objects representing the full mirrored shape
    
    Raises:
        NoSeamPointsError: If no seam points are found
        SeamAlignmentError: If seam points are not aligned
    """
    # Find and validate seam points
    seam_points = find_seam_points(points, axis_x, center_band, check_x=True)
    if not seam_points:
        raise NoSeamPointsError(
            f"No seam points found near x={axis_x} within band={center_band}"
        )
    
    # Validate alignment and get precise axis value
    aligned_x = validate_seam_alignment(seam_points, check_x=True, eps=eps)
    
    # Separate source points (keep as-is)
    if source_side == "left":
        source = [p for p in points if p.x <= aligned_x + eps]
    else:  # right
        source = [p for p in points if p.x >= aligned_x - eps]
    
    # Mirror all source points
    mirrored = []
    for p in source:
        # Mirror x coordinate: x' = axis_x - (x - axis_x) = 2*axis_x - x
        mx = 2 * aligned_x - p.x
        mirrored.append(Point(mx, p.y, p.on_curve))
    
    return source + mirrored


def mirror_vertical(points, axis_y, source_side="top", eps=0.01, center_band=5.0):
    """
    Mirror points vertically across a horizontal axis.
    
    Args:
        points: List of Point objects (selected half + seam)
        axis_y: Y coordinate of the horizontal seam line
        source_side: "top" or "bottom" - which side is the source
        eps: Tolerance for coordinate comparisons
        center_band: Distance tolerance for finding seam points
    
    Returns:
        List of Point objects representing the full mirrored shape
    
    Raises:
        NoSeamPointsError: If no seam points are found
        SeamAlignmentError: If seam points are not aligned
    """
    # Find and validate seam points
    seam_points = find_seam_points(points, axis_y, center_band, check_x=False)
    if not seam_points:
        raise NoSeamPointsError(
            f"No seam points found near y={axis_y} within band={center_band}"
        )
    
    # Validate alignment and get precise axis value
    aligned_y = validate_seam_alignment(seam_points, check_x=False, eps=eps)
    
    # Separate source points (keep as-is)
    # Note: In Glyphs, y increases upward, so "top" has larger y values
    if source_side == "top":
        source = [p for p in points if p.y >= aligned_y - eps]
    else:  # bottom
        source = [p for p in points if p.y <= aligned_y + eps]
    
    # Mirror all source points
    mirrored = []
    for p in source:
        # Mirror y coordinate: y' = 2*axis_y - y
        my = 2 * aligned_y - p.y
        mirrored.append(Point(p.x, my, p.on_curve))
    
    return source + mirrored




