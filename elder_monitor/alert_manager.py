"""Alert timing logic (pure and time-injected, so it is easy to unit-test)."""

from __future__ import annotations

import logging
import time
from typing import Callable, Optional

from .config import MonitorConfig
from .models import SafetyState
from .notifiers import Notifier

logger = logging.getLogger(__name__)


class AlertManager:
    """
    Tracks how long the person has been AT_RISK and decides when to notify.

    - The timer starts on the first AT_RISK observation.
    - NO_PERSON keeps a running timer going, because a person lying on the
      floor may simply be hidden behind the bed.
    - SAFE resets the timer and sends "all clear" if an alert was sent.
    """

    def __init__(self, config: MonitorConfig, notifier: Notifier,
                 clock: Callable[[], float] = time.monotonic) -> None:
        self._cfg = config
        self._notifier = notifier
        self._clock = clock
        self._risk_since: Optional[float] = None
        self._last_alert_at: Optional[float] = None

    @property
    def risk_duration(self) -> float:
        """Seconds the current risk situation has lasted (0 if none)."""
        if self._risk_since is None:
            return 0.0
        return self._clock() - self._risk_since

    def update(self, state: SafetyState) -> None:
        """Feed the latest assessment; may send an alert or all-clear."""
        now = self._clock()

        if state is SafetyState.SAFE:
            self._resolve()
            return

        if state is SafetyState.NO_PERSON and self._risk_since is None:
            return  # nothing pending, nobody seen -> nothing to do

        if state is SafetyState.AT_RISK and self._risk_since is None:
            self._risk_since = now
            logger.info("Person possibly on the floor - timer started")

        self._maybe_alert(now)

    def _maybe_alert(self, now: float) -> None:
        duration = now - self._risk_since
        if duration < self._cfg.alert_after_seconds:
            return
        due = (self._last_alert_at is None or
               now - self._last_alert_at >= self._cfg.reminder_interval_seconds)
        if due:
            minutes = int(duration // 60)
            self._notifier.send(
                "ALERT: person may have fallen",
                f"The person has been on the floor for about {minutes} minutes. "
                "Please check on them immediately.",
            )
            self._last_alert_at = now

    def _resolve(self) -> None:
        if self._last_alert_at is not None:
            self._notifier.send("All clear",
                                "The person is back in a safe position.")
        if self._risk_since is not None:
            logger.info("Risk resolved")
        self._risk_since = None
        self._last_alert_at = None
