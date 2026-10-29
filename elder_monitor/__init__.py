"""
Elder Monitor - floor-time watchdog for elderly people living alone.

A camera watches the bedroom. If the person lies or sits outside the bed
(most likely on the floor) for longer than the configured time, the
responsible person is notified.

Package layout
--------------
    config.py         MonitorConfig - all tunable parameters
    models.py         Domain types: Posture, SafetyState, Detection
    zones.py          Zone (polygon) and ZoneRepository (JSON storage)
    detection.py      PersonDetector - YOLO pose model wrapper
    posture.py        PostureClassifier - lying / sitting / standing
    analyzer.py       SituationAnalyzer - posture + location -> SafetyState
    alert_manager.py  AlertManager - timer, alerts, reminders, all-clear
    notifiers.py      Notifier interface and implementations
    video.py          VideoSource - camera capture with reconnect
    monitor.py        ElderMonitor - main processing loop
    calibrator.py     ZoneCalibrator - draw bed/safe zones with the mouse

NOTE: This is a prototype, not a certified medical/emergency device.
"""

__version__ = "0.2.0"
