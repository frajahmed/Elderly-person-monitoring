"""Combines posture and location into a safety assessment."""

from __future__ import annotations

from typing import List, Optional

from .models import Detection, Posture, SafetyState
from .zones import Zone


class SituationAnalyzer:
    """Decides whether the current situation is safe or at risk."""

    LOW_POSTURES = (Posture.LYING, Posture.SITTING)

    def __init__(self, bed: Zone, safe_zones: List[Zone]) -> None:
        self.bed = bed
        self.safe_zones = safe_zones

    def analyze(self, det: Optional[Detection], posture: Posture) -> SafetyState:
        if det is None:
            return SafetyState.NO_PERSON

        position = det.hip_center
        if self.bed.contains(position):
            return SafetyState.SAFE
        if any(zone.contains(position) for zone in self.safe_zones):
            return SafetyState.SAFE
        if posture in self.LOW_POSTURES:
            return SafetyState.AT_RISK   # low posture outside bed -> floor
        return SafetyState.SAFE
