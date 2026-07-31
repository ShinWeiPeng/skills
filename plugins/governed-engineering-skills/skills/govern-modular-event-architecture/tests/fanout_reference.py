#!/usr/bin/env python3
"""Development-only reference for fan-out failure-isolation tests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable


@dataclass(frozen=True)
class SubscriberFailure:
    index: int
    error: Exception


def publish_all(event: Any, subscribers: Iterable[Callable[[Any], None]]) -> list[SubscriberFailure]:
    """Invoke every subscriber in configured order and aggregate failures."""
    failures: list[SubscriberFailure] = []
    for index, subscriber in enumerate(subscribers):
        try:
            subscriber(event)
        except Exception as exc:  # Subscriber boundaries intentionally isolate failures.
            failures.append(SubscriberFailure(index, exc))
    return failures
