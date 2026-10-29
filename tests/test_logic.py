"""Unit tests for the camera-independent logic.

Run with:  python -m unittest discover tests
"""

import tempfile
import unittest
from pathlib import Path

from elder_monitor.alert_manager import AlertManager
from elder_monitor.analyzer import SituationAnalyzer
from elder_monitor.config import MonitorConfig
from elder_monitor.models import Detection, Posture, SafetyState
from elder_monitor.notifiers import CompositeNotifier, Notifier
from elder_monitor.posture import PostureClassifier
from elder_monitor.zones import Zone, ZoneRepository

MIN = 60.0


class FakeClock:
    """Manually controlled clock for time-dependent tests."""

    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


class RecordingNotifier(Notifier):
    """Stores sent messages instead of delivering them."""

    def __init__(self) -> None:
        self.messages = []

    def send(self, subject: str, message: str) -> None:
        self.messages.append(subject)


def make_detection(shoulders, hips, knees=None, bbox=(0, 0, 100, 300)) -> Detection:
    keypoints = [None] * 17
    keypoints[5] = keypoints[6] = shoulders
    keypoints[11] = keypoints[12] = hips
    if knees:
        keypoints[13] = keypoints[14] = knees
    return Detection(bbox, keypoints, 0.9)


class AlertManagerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.clock = FakeClock()
        self.notifier = RecordingNotifier()
        self.manager = AlertManager(MonitorConfig(), self.notifier, clock=self.clock)

    def at(self, minutes: float, state: SafetyState) -> None:
        self.clock.now = minutes * MIN
        self.manager.update(state)

    def test_no_alert_before_15_minutes(self):
        self.at(0, SafetyState.AT_RISK)
        self.at(14.9, SafetyState.AT_RISK)
        self.assertEqual(self.notifier.messages, [])

    def test_alert_after_15_minutes(self):
        self.at(0, SafetyState.AT_RISK)
        self.at(15, SafetyState.AT_RISK)
        self.assertEqual(len(self.notifier.messages), 1)

    def test_timer_keeps_running_when_person_hidden(self):
        self.at(0, SafetyState.AT_RISK)
        self.at(15, SafetyState.NO_PERSON)
        self.assertEqual(len(self.notifier.messages), 1)

    def test_reminder_interval(self):
        self.at(0, SafetyState.AT_RISK)
        self.at(15, SafetyState.AT_RISK)
        self.at(20, SafetyState.AT_RISK)   # too early for a reminder
        self.at(25, SafetyState.AT_RISK)   # 10 min after first alert
        self.assertEqual(len(self.notifier.messages), 2)

    def test_safe_resets_timer_without_message(self):
        self.at(0, SafetyState.AT_RISK)
        self.at(10, SafetyState.SAFE)
        self.at(11, SafetyState.AT_RISK)
        self.at(25, SafetyState.AT_RISK)   # only 14 min since restart
        self.assertEqual(self.notifier.messages, [])

    def test_all_clear_after_alert(self):
        self.at(0, SafetyState.AT_RISK)
        self.at(15, SafetyState.AT_RISK)
        self.at(16, SafetyState.SAFE)
        self.assertEqual(self.notifier.messages[-1], "All clear")

    def test_nobody_seen_does_nothing(self):
        self.at(0, SafetyState.NO_PERSON)
        self.at(60, SafetyState.NO_PERSON)
        self.assertEqual(self.notifier.messages, [])


class ZoneTest(unittest.TestCase):
    def setUp(self) -> None:
        self.bed = Zone("bed", [(0, 0), (100, 0), (100, 50), (0, 50)])

    def test_contains(self):
        self.assertTrue(self.bed.contains((50, 25)))
        self.assertFalse(self.bed.contains((150, 25)))

    def test_needs_three_points(self):
        with self.assertRaises(ValueError):
            Zone("bad", [(0, 0), (1, 1)])

    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = ZoneRepository(Path(tmp) / "sub" / "zones.json")
            chair = Zone("safe_1", [(200, 0), (300, 0), (300, 100)])
            repo.save(self.bed, [chair])
            bed, safe = repo.load()
            self.assertEqual(bed.polygon, self.bed.polygon)
            self.assertEqual(safe[0].name, "safe_1")


class PostureClassifierTest(unittest.TestCase):
    def setUp(self) -> None:
        self.classifier = PostureClassifier()

    def test_lying(self):
        det = make_detection((200, 100), (300, 110), bbox=(150, 80, 350, 140))
        self.assertEqual(self.classifier.classify(det), Posture.LYING)

    def test_sitting(self):
        det = make_detection((200, 100), (200, 200), (280, 210), bbox=(180, 90, 290, 260))
        self.assertEqual(self.classifier.classify(det), Posture.SITTING)

    def test_standing(self):
        det = make_detection((200, 100), (200, 200), (205, 300), bbox=(180, 90, 230, 400))
        self.assertEqual(self.classifier.classify(det), Posture.STANDING)


class SituationAnalyzerTest(unittest.TestCase):
    def setUp(self) -> None:
        bed = Zone("bed", [(0, 0), (100, 0), (100, 100), (0, 100)])
        chair = Zone("safe_1", [(400, 0), (500, 0), (500, 100), (400, 100)])
        self.analyzer = SituationAnalyzer(bed, [chair])

    def test_no_person(self):
        self.assertEqual(self.analyzer.analyze(None, Posture.UNKNOWN), SafetyState.NO_PERSON)

    def test_lying_in_bed_is_safe(self):
        det = make_detection((20, 50), (50, 50))
        self.assertEqual(self.analyzer.analyze(det, Posture.LYING), SafetyState.SAFE)

    def test_sitting_in_chair_is_safe(self):
        det = make_detection((450, 20), (450, 50))
        self.assertEqual(self.analyzer.analyze(det, Posture.SITTING), SafetyState.SAFE)

    def test_lying_on_floor_is_risk(self):
        det = make_detection((200, 300), (250, 300))
        self.assertEqual(self.analyzer.analyze(det, Posture.LYING), SafetyState.AT_RISK)

    def test_standing_outside_bed_is_safe(self):
        det = make_detection((200, 100), (200, 200))
        self.assertEqual(self.analyzer.analyze(det, Posture.STANDING), SafetyState.SAFE)


class CompositeNotifierTest(unittest.TestCase):
    def test_failure_does_not_stop_others(self):
        class Broken(Notifier):
            def send(self, subject, message):
                raise RuntimeError("boom")

        recorder = RecordingNotifier()
        CompositeNotifier([Broken(), recorder]).send("Test", "msg")
        self.assertEqual(recorder.messages, ["Test"])


if __name__ == "__main__":
    unittest.main()
