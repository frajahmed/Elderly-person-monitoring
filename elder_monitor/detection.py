"""Person detection with a YOLO pose model."""

from __future__ import annotations

from typing import List, Optional

from .models import Detection, Point


class PersonDetector:
    """Wraps an Ultralytics YOLO pose model and returns the main person."""

    KEYPOINT_MIN_CONF = 0.5  # keypoints below this confidence count as hidden

    def __init__(self, model_path: str, min_confidence: float) -> None:
        from ultralytics import YOLO  # imported lazily (heavy dependency)

        self._model = YOLO(model_path)
        self._min_conf = min_confidence

    def detect(self, frame) -> Optional[Detection]:
        """Return the largest (closest) person in the frame, or None."""
        result = self._model(frame, verbose=False)[0]
        if result.boxes is None or len(result.boxes) == 0:
            return None

        best: Optional[Detection] = None
        best_area = 0.0
        for i, box in enumerate(result.boxes):
            conf = float(box.conf[0])
            if conf < self._min_conf:
                continue
            x1, y1, x2, y2 = map(float, box.xyxy[0])
            area = (x2 - x1) * (y2 - y1)
            if area <= best_area:
                continue

            best = Detection((x1, y1, x2, y2), self._keypoints(result, i), conf)
            best_area = area
        return best

    def _keypoints(self, result, index: int) -> List[Optional[Point]]:
        """Extract keypoints of one person; hidden ones become None."""
        xy = result.keypoints.xy[index]
        conf = result.keypoints.conf[index] if result.keypoints.conf is not None else None
        points: List[Optional[Point]] = []
        for k in range(len(xy)):
            visible = conf is None or float(conf[k]) > self.KEYPOINT_MIN_CONF
            points.append((float(xy[k][0]), float(xy[k][1])) if visible else None)
        return points
