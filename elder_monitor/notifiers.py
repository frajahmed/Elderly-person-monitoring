"""Ways to notify the responsible person."""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from typing import List

logger = logging.getLogger(__name__)


class Notifier(ABC):
    """Interface for anything that can deliver a message to a caregiver.

    To add a new channel (SMS, e-mail, ...), subclass this and implement send().
    """

    @abstractmethod
    def send(self, subject: str, message: str) -> None: ...


class ConsoleNotifier(Notifier):
    """Writes alerts to the log (always active, useful for testing)."""

    def send(self, subject: str, message: str) -> None:
        logger.warning("[%s] %s", subject, message)


class TelegramNotifier(Notifier):
    """Sends messages through a Telegram bot."""

    API_URL = "https://api.telegram.org/bot{token}/sendMessage"

    def __init__(self, token: str, chat_id: str) -> None:
        self._token = token
        self._chat_id = chat_id

    def send(self, subject: str, message: str) -> None:
        import requests

        try:
            resp = requests.post(
                self.API_URL.format(token=self._token),
                json={"chat_id": self._chat_id, "text": f"{subject}\n{message}"},
                timeout=10,
            )
            resp.raise_for_status()
        except requests.RequestException as exc:
            logger.error("Telegram notification failed: %s", exc)


class CompositeNotifier(Notifier):
    """Fans a message out to several notifiers; one failure doesn't stop others."""

    def __init__(self, notifiers: List[Notifier]) -> None:
        self._notifiers = notifiers

    def send(self, subject: str, message: str) -> None:
        for notifier in self._notifiers:
            try:
                notifier.send(subject, message)
            except Exception:  # noqa: BLE001 - never let alerting crash the loop
                logger.exception("Notifier %s failed", type(notifier).__name__)


def build_notifier_from_env() -> Notifier:
    """Console always; Telegram if credentials are set in the environment."""
    notifiers: List[Notifier] = [ConsoleNotifier()]
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if token and chat_id:
        notifiers.append(TelegramNotifier(token, chat_id))
        logger.info("Telegram notifications enabled")
    return CompositeNotifier(notifiers)
