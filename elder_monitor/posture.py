"""Rule-based posture classification."""

from __future__ import annotations

import math

from .models import Detection, Point, Posture


class PostureClassifier:
    """Estimates lying / sitting / standing from pose keypoints."""

    LYING_TORSO_ANGLE = 60.0     # torso tilt from vertical (degrees)
    LYING_BBOX_RATIO = 1.3       # width / height of the bounding box
    SITTING_THIGH_ANGLE = 45.0   # thigh tilt from horizontal (degrees)

    def classify(self, det: Detection) -> Posture:
        shoulders = det.midpoint(det.L_SHOULDER, det.R_SHOULDER)
        hips = det.midpoint(det.L_HIP, det.R_HIP)
        knees = det.midpoint(det.L_KNEE, det.R_KNEE)

        if self._is_lying(det, shoulders, hips):
            return Posture.LYING

        # Sitting: upright torso, but thighs roughly horizontal
        if hips and knees:
            thigh_from_vertical = self._angle_from_vertical(hips, knees)
            if thigh_from_vertical > 90.0 - self.SITTING_THIGH_ANGLE:
                return Posture.SITTING
            return Posture.STANDING

        return Posture.UNKNOWN

    def _is_lying(self, det: Detection, shoulders, hips) -> bool:
        """Lying: torso close to horizontal, or very wide bounding box."""
        if shoulders and hips:
            if self._angle_from_vertical(shoulders, hips) > self.LYING_TORSO_ANGLE:
                return True
        x1, y1, x2, y2 = det.bbox
        height = y2 - y1
        return height > 0 and (x2 - x1) / height > self.LYING_BBOX_RATIO

    @staticmethod
    def _angle_from_vertical(a: Point, b: Point) -> float:
        """Angle of the line a->b measured from the vertical axis (0..90°)."""
        dx, dy = b[0] - a[0], b[1] - a[1]
        return math.degrees(math.atan2(abs(dx), abs(dy) + 1e-6))
