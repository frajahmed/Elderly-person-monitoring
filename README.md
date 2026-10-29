# Alter-Mensch-Beobachten

Überwacht per Kamera, ob eine allein lebende Person länger als 15 Minuten
außerhalb des Bettes liegt oder sitzt (vermutlich am Boden), und schickt dann
einen Alarm an die verantwortliche Person (Telegram).

## Dateien

| Datei | Zweck |
|---|---|
| `main.py` | Einstiegspunkt (Befehlszeile, startet alles) |
| `elder_monitor/` | Das Programm als Paket, eine Datei pro Klasse/Aufgabe |
| `tests/` | Automatische Tests der Logik |
| `requirements.txt` | Python-Pakete |
| `Dockerfile` | Container-Image (CPU, ohne Bildschirm) |
| `docker-compose.yml` | Start mit einem Befehl, Neustart automatisch |
| `.env.example` | Vorlage für Kamera und Telegram-Daten |
| `data/` | Hier liegt `zones.json` (Bett-Zone) |

## Einrichtung

### 1. Konfiguration

`.env.example` nach `.env` kopieren und ausfüllen (Kamera-URL, Telegram).

### 2. Bett-Zone einzeichnen (einmalig, ohne Docker)

Das Einzeichnen braucht ein Fenster und läuft deshalb direkt auf dem PC,
nicht im Container:

```powershell
pip install -r requirements.txt
python main.py --calibrate --source "rtsp://..."
```

Linksklick = Punkt setzen, Enter = Zone fertig (erste Zone = Bett,
weitere = sichere Zonen wie Sessel), Esc = speichern und beenden.

### 3. Mit Docker starten

```powershell
docker compose up -d --build     # bauen und im Hintergrund starten
docker compose logs -f           # Ausgabe ansehen
docker compose down              # stoppen
```

### Ohne Docker starten (zum Testen)

```powershell
python main.py --source "rtsp://..." --preview --minutes 1
```

### Tests ausführen

```powershell
python -m unittest discover tests
```

## Aufbau des Pakets `elder_monitor/`

| Datei | Klasse(n) | Aufgabe |
|---|---|---|
| `config.py` | `MonitorConfig` | alle Einstellungen |
| `models.py` | `Posture`, `SafetyState`, `Detection` | Datentypen |
| `zones.py` | `Zone`, `ZoneRepository` | Bett-/Sicherheitszonen, Speichern/Laden |
| `detection.py` | `PersonDetector` | Person mit KI-Modell finden |
| `posture.py` | `PostureClassifier` | liegt / sitzt / steht |
| `analyzer.py` | `SituationAnalyzer` | sicher oder Risiko |
| `alert_manager.py` | `AlertManager` | Timer, Alarm, Erinnerung, Entwarnung |
| `notifiers.py` | `Notifier` + Unterklassen | Konsole, Telegram, mehrere Kanäle |
| `video.py` | `VideoSource` | Kamera lesen, neu verbinden |
| `monitor.py` | `ElderMonitor` | Hauptschleife |
| `calibrator.py` | `ZoneCalibrator` | Zonen mit der Maus einzeichnen |

Neuer Benachrichtigungsweg (SMS, E-Mail ...): in `notifiers.py` eine
Unterklasse von `Notifier` schreiben und in `build_notifier_from_env()` eintragen.

## Kamera und Docker

- **Windows / macOS (Docker Desktop):** Eine USB-Webcam kann nicht in den
  Container durchgereicht werden. Nimm eine **IP-Kamera mit RTSP**
  (z. B. Tapo, Reolink) und trage die URL in `.env` ein.
- **Linux (z. B. Raspberry Pi 5, Mini-PC):** USB-Webcam geht auch.
  In `docker-compose.yml` den Block `devices` aktivieren und
  `CAMERA_SOURCE=0` setzen.

## Telegram-Bot einrichten

1. In Telegram `@BotFather` anschreiben → `/newbot` → Token kopieren.
2. Die verantwortliche Person schreibt dem Bot eine Nachricht.
3. `https://api.telegram.org/bot<TOKEN>/getUpdates` öffnen → `chat.id` kopieren.
4. Beides in `.env` eintragen.

## Hinweis

Prototyp, kein zertifiziertes Notrufsystem. Vor dem echten Einsatz gründlich
testen; die überwachte Person sollte einverstanden sein.
