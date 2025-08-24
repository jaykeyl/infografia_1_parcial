import numpy as np
from dataclasses import dataclass
from logging import getLogger

logger = getLogger(__name__)


@dataclass
class ImpulseVector:
    angle: float  # radians
    impulse: float  # magnitude in pixels


@dataclass
class Point2D:
    x: float
    y: float


def get_angle_radians(point_a: Point2D, point_b: Point2D) -> float:
    """Angle (radians) from point_b -> point_a (slingshot opposite to drag)."""
    dx = float(point_a.x) - float(point_b.x)
    dy = float(point_a.y) - float(point_b.y)
    return float(np.arctan2(dy, dx))


def get_distance(point_a: Point2D, point_b: Point2D) -> float:
    """Euclidean distance between two points (pixels)."""
    dx = float(point_a.x) - float(point_b.x)
    dy = float(point_a.y) - float(point_b.y)
    return float(np.hypot(dx, dy))


def get_impulse_vector(start_point: Point2D, end_point: Point2D) -> ImpulseVector:
    """Return ImpulseVector(angle, impulse) computed with NumPy."""
    angle = get_angle_radians(start_point, end_point)
    impulse = get_distance(start_point, end_point)
    logger.debug(f"ImpulseVector(angle={angle:.3f} rad, impulse={impulse:.2f} px)")
    return ImpulseVector(angle, impulse)
