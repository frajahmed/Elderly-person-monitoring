"""Domain types shared across the package."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Optional, Tuple

# A 2D point in image (pixel) coordinates
Point = Tuple[float, float]


class Posture(Enum):
    """Body posture estimated from pose keypoints."""

    STANDING = auto()
    SITTING = auto()
    LYING = auto()
    UNKNOWN = auto()


class SafetyState(Enum):
    """Overall assessment of the current situation."""

    SAFE = auto()
    AT_RISK = auto()
    NO_PERSON = auto()


@dataclass
class Detection:
    """A single detected person (pixel coordinates)."""

    bbox: Tuple[float, float, float, float]        # x1, y1, x2, y2
    keypoints: List[Optional[Point]]               # 17 COCO keypoints (None = not visible)
    confidence: float

    # COCO keypoint indices used by the classifier
    L_SHOULDER, R_SHOULDER = 5, 6
    L_HIP, R_HIP = 11, 12
    L_KNEE, R_KNEE = 13, 14

    def midpoint(self, a: int, b: int) -> Optional[Point]:
        """Midpoint of two keypoints, or the visible one, or None."""
        pa, pb = self.keypoints[a], self.keypoints[b]
        if pa and pb:
            return ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2)
        return pa or pb

    @property
    def hip_center(self) -> Point:
        """Hip center; falls back to the bbox center if hips are not visible."""
        hip = self.midpoint(self.L_HIP, self.R_HIP)
        if hip:
            return hip
        x1, y1, x2, y2 = self.bbox
        return ((x1 + x2) / 2, (y1 + y2) / 2)
