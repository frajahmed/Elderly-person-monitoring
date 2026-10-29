"""Camera / stream input."""

from __future__ import annotations

import logging
import time

logger = logging.getLogger(__name__)


class VideoSource:
    """Thin wrapper around cv2.VideoCapture with automatic reconnect."""

    RECONNECT_DELAY_SECONDS = 2.0

    def __init__(self, source: int | str) -> None:
        import cv2

        self._cv2 = cv2
        self._source = source
        self._cap = cv2.VideoCapture(source)

    def read(self):
        """Return the next frame, or None if the camera is unavailable."""
        ok, frame = self._cap.read()
        if not ok:
            logger.error("Camera read failed - reconnecting")
            self._cap.release()
            time.sleep(self.RECONNECT_DELAY_SECONDS)
            self._cap = self._cv2.VideoCapture(self._source)
            return None
        return frame

    def release(self) -> None:
        self._cap.release()
