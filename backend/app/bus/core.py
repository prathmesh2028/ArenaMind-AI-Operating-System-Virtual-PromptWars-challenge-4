"""
ArenaMind Event Bus — Core Engine
====================================

Architecture: Publish / Subscribe with async queue processing.

Design:
  ┌──────────────────────────────────────────────────────────────────┐
  │  Publishers (Twin / APIs / Sensors)                              │
  │       ↓ publish(BusEvent)                                        │
  │  ┌──────────────┐                                                │
  │  │  asyncio.Queue │  ← main event queue (unbounded)              │
  │  └──────────────┘                                                │
  │       ↓ _process_loop()                                          │
  │  ┌──────────────────────────────────────────────┐               │
  │  │  Topic Router — match topic patterns          │               │
  │  │  (supports wildcards: "crowd.*", "*")         │               │
  │  └──────────────────────────────────────────────┘               │
  │       ↓ dispatch to matched Subscribers                          │
  │  ┌────────────────────────────────────────────┐                 │
  │  │  Subscriber Handler (async coroutine)       │                 │
  │  │  → success: ack, log, persist               │                 │
  │  │  → failure: retry with exponential backoff  │                 │
  │  │  → max_retries exceeded: → Dead Letter Queue│                 │
  │  └────────────────────────────────────────────┘                 │
  │                                                                  │
  │  Dead Letter Queue (in-memory + persisted to ReplayLog)          │
  └──────────────────────────────────────────────────────────────────┘

Key properties:
  - Fully async: no blocking in the hot path
  - Topic patterns support exact match and prefix wildcard (e.g. "crowd.*")
  - Each subscriber runs in a separate asyncio task (fire-and-forget with shield)
  - Retry uses exponential backoff: 1s, 2s, 4s
  - DLQ entries can be manually retried via the API
  - All processed events are persisted to the DB events table
  - Metrics: total published, processed, failed, DLQ depth
"""

import asyncio
import fnmatch
import logging
import time
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

from app.bus.schemas import BusEvent, DeadLetterEntry, normalize_topic

logger = logging.getLogger("arenamind.bus")

# Type alias for subscriber coroutines
HandlerFn = Callable[[BusEvent], Awaitable[None]]

# Retry backoff schedule (seconds)
RETRY_BACKOFF = [1.0, 2.0, 4.0]


class Subscriber:
    """A registered topic subscription with an async handler."""

    def __init__(self, name: str, topic_pattern: str, handler: HandlerFn) -> None:
        self.name = name
        self.topic_pattern = topic_pattern
        self.handler = handler
        self.processed: int = 0
        self.failed: int = 0

    def matches(self, topic: str) -> bool:
        """
        Check if this subscriber's pattern matches a topic.
        Supports:
          - Exact match:   "crowd.tick"
          - Prefix glob:   "crowd.*"
          - Full wildcard: "*"
        """
        return fnmatch.fnmatch(topic, self.topic_pattern)

    def __repr__(self) -> str:
        return f"Subscriber(name={self.name!r}, pattern={self.topic_pattern!r})"


class EventBus:
    """
    ArenaMind Async Event Bus.

    Usage:
        bus = EventBus()
        bus.subscribe("crowd.*", my_handler, name="my_handler")
        await bus.start()
        await bus.publish(event)
        await bus.stop()
    """

    def __init__(self) -> None:
        self._queue: asyncio.Queue[BusEvent] = asyncio.Queue()
        self._subscribers: list[Subscriber] = []
        self._dlq: list[DeadLetterEntry] = []
        self._is_running: bool = False
        self._process_task: asyncio.Task | None = None
        self._db_persist_task: asyncio.Task | None = None

        # Metrics
        self._stats: dict[str, int] = defaultdict(int)

        # Async queue for DB persistence (decoupled from processing)
        self._persist_queue: asyncio.Queue[BusEvent] = asyncio.Queue()

    # -----------------------------------------------------------------------
    # Lifecycle
    # -----------------------------------------------------------------------

    async def start(self) -> None:
        """Start the event processing loop and DB persistence loop."""
        if self._is_running:
            logger.warning("[BUS] Already running.")
            return

        self._is_running = True
        self._process_task = asyncio.create_task(self._process_loop(), name="bus.process_loop")
        self._db_persist_task = asyncio.create_task(self._persist_loop(), name="bus.persist_loop")
        logger.info(
            f"[BUS] Started — {len(self._subscribers)} subscribers registered | "
            f"Topics: {list(set(s.topic_pattern for s in self._subscribers))}"
        )

    async def stop(self) -> None:
        """Drain remaining events and stop the processing loop."""
        self._is_running = False

        if self._process_task:
            self._process_task.cancel()
            try:
                await self._process_task
            except asyncio.CancelledError:
                pass

        if self._db_persist_task:
            self._db_persist_task.cancel()
            try:
                await self._db_persist_task
            except asyncio.CancelledError:
                pass

        logger.info(
            f"[BUS] Stopped. Stats: published={self._stats['published']}, "
            f"processed={self._stats['processed']}, failed={self._stats['failed']}, "
            f"dlq_depth={len(self._dlq)}"
        )

    # -----------------------------------------------------------------------
    # Subscription
    # -----------------------------------------------------------------------

    def subscribe(
        self,
        topic_pattern: str,
        handler: HandlerFn,
        name: str | None = None,
    ) -> None:
        """
        Register a subscriber for a topic pattern.

        Args:
            topic_pattern: Exact topic or glob pattern (e.g. "crowd.*", "*").
            handler:        Async coroutine called with the BusEvent.
            name:           Human-readable subscriber name for logs and metrics.
        """
        sub_name = name or handler.__name__
        sub = Subscriber(sub_name, topic_pattern, handler)
        self._subscribers.append(sub)
        logger.debug(f"[BUS] Subscribed: {sub_name!r} → pattern={topic_pattern!r}")

    def unsubscribe(self, name: str) -> bool:
        """Remove a subscriber by name."""
        before = len(self._subscribers)
        self._subscribers = [s for s in self._subscribers if s.name != name]
        removed = before - len(self._subscribers)
        if removed:
            logger.info(f"[BUS] Unsubscribed {name!r} ({removed} subscription(s) removed)")
        return removed > 0

    def list_subscribers(self) -> list[dict[str, Any]]:
        return [
            {
                "name": s.name,
                "topic_pattern": s.topic_pattern,
                "processed": s.processed,
                "failed": s.failed,
            }
            for s in self._subscribers
        ]

    # -----------------------------------------------------------------------
    # Publishing
    # -----------------------------------------------------------------------

    async def publish(self, event: BusEvent) -> None:
        """
        Publish an event to the bus. Non-blocking — puts onto the async queue.
        The topic is normalized before queuing.
        """
        event.topic = normalize_topic(event.topic) if not "." in event.topic else event.topic
        await self._queue.put(event)
        self._stats["published"] += 1
        logger.debug(f"[BUS] Published: topic={event.topic} id={event.id[:8]} source={event.source}")

    def publish_sync(self, event: BusEvent) -> None:
        """
        Thread-safe synchronous publish — for use from non-async contexts.
        Uses call_soon_threadsafe if a loop is running.
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.call_soon_threadsafe(self._queue.put_nowait, event)
            else:
                self._queue.put_nowait(event)
            self._stats["published"] += 1
        except Exception as exc:
            logger.warning(f"[BUS] publish_sync failed: {exc}")

    # -----------------------------------------------------------------------
    # Processing Loop
    # -----------------------------------------------------------------------

    async def _process_loop(self) -> None:
        """Main event consumer loop. Runs until stopped."""
        logger.info("[BUS] Processing loop started.")
        while self._is_running:
            try:
                event = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                await self._dispatch_event(event)
                self._queue.task_done()

                # Also forward to persist queue (decoupled)
                await self._persist_queue.put(event)

            except asyncio.TimeoutError:
                continue   # No events — loop back
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error(f"[BUS] Unexpected error in process loop: {exc}", exc_info=True)

        logger.info("[BUS] Processing loop stopped.")

    async def _dispatch_event(self, event: BusEvent) -> None:
        """Route an event to all matching subscribers. Each runs independently."""
        matched = [s for s in self._subscribers if s.matches(event.topic)]

        if not matched:
            logger.debug(f"[BUS] No subscribers for topic={event.topic}")
            return

        # Fire all matched handlers concurrently
        tasks = [
            asyncio.create_task(
                self._call_with_retry(event, sub),
                name=f"bus.handler.{sub.name}",
            )
            for sub in matched
        ]
        # await all but don't let one failure block others
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for sub, result in zip(matched, results):
            if isinstance(result, Exception):
                logger.error(f"[BUS] Handler {sub.name!r} raised unhandled exception: {result}")

        self._stats["processed"] += 1

    async def _call_with_retry(self, event: BusEvent, sub: Subscriber) -> None:
        """
        Call a subscriber handler with exponential backoff retry.
        On exhaustion, move to the Dead Letter Queue.
        """
        current = event
        for attempt_idx in range(event.max_retries + 1):
            try:
                await sub.handler(current)
                sub.processed += 1
                return  # Success
            except Exception as exc:
                delay = RETRY_BACKOFF[min(attempt_idx, len(RETRY_BACKOFF) - 1)]
                sub.failed += 1
                self._stats["failed"] += 1

                if attempt_idx < event.max_retries:
                    logger.warning(
                        f"[BUS] Handler {sub.name!r} failed on attempt {attempt_idx + 1} "
                        f"for topic={event.topic} (retry in {delay}s): {exc}"
                    )
                    await asyncio.sleep(delay)
                    current = current.with_retry()
                else:
                    # Max retries exceeded → DLQ
                    logger.error(
                        f"[BUS] Handler {sub.name!r} exhausted {event.max_retries} retries "
                        f"for topic={event.topic} id={event.id[:8]}. Moving to DLQ."
                    )
                    dlq_entry = DeadLetterEntry(
                        event=current,
                        last_error=str(exc),
                        failed_handler=sub.name,
                    )
                    self._dlq.append(dlq_entry)
                    self._stats["dlq_total"] += 1
                    await self._persist_dlq_entry(dlq_entry)

    # -----------------------------------------------------------------------
    # DB Persistence Loop (decoupled from handler processing)
    # -----------------------------------------------------------------------

    async def _persist_loop(self) -> None:
        """Consume from the persist queue and write events to the database."""
        from app.database import SessionLocal
        from app.models import Event

        logger.info("[BUS] Persistence loop started.")
        while self._is_running:
            try:
                event = await asyncio.wait_for(self._persist_queue.get(), timeout=2.0)
                db = SessionLocal()
                try:
                    db.add(Event(
                        id=event.id,
                        timestamp=event.timestamp,
                        type=event.topic,
                        source=event.source,
                        payload=event.to_dict(),
                    ))
                    db.commit()
                except Exception as exc:
                    db.rollback()
                    logger.warning(f"[BUS] Persistence failed for event {event.id[:8]}: {exc}")
                finally:
                    db.close()
                self._persist_queue.task_done()

            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error(f"[BUS] Persist loop error: {exc}", exc_info=True)

        logger.info("[BUS] Persistence loop stopped.")

    async def _persist_dlq_entry(self, entry: DeadLetterEntry) -> None:
        """Persist a DLQ entry to the ReplayLog table for post-mortem inspection."""
        from app.database import SessionLocal
        from app.models import ReplayLog

        db = SessionLocal()
        try:
            session_id = f"dlq_{datetime.now(timezone.utc).strftime('%Y%m%d')}"
            db.add(ReplayLog(
                id=str(uuid.uuid4()),
                replay_session_id=session_id,
                timestamp=entry.event.timestamp,
                event_type=f"DLQ_{entry.event.topic}",
                payload={
                    "dlq_entry": entry.to_dict(),
                    "reason": "max_retries_exceeded",
                },
                created_at=datetime.now(timezone.utc),
            ))
            db.commit()
        except Exception as exc:
            db.rollback()
            logger.warning(f"[BUS] DLQ persist failed: {exc}")
        finally:
            db.close()

    # -----------------------------------------------------------------------
    # Dead Letter Queue Management
    # -----------------------------------------------------------------------

    def get_dlq(self) -> list[DeadLetterEntry]:
        return list(self._dlq)

    async def retry_dlq_entry(self, event_id: str) -> bool:
        """Manually re-publish a DLQ event back onto the bus."""
        for entry in self._dlq:
            if entry.event.id == event_id:
                entry.retried = True
                entry.retry_count += 1
                retry_event = entry.event.with_retry()
                retry_event.attempt = 0   # Reset attempt counter for fresh retry
                retry_event.max_retries = 3
                await self.publish(retry_event)
                logger.info(f"[BUS] DLQ entry {event_id[:8]} manually re-published.")
                return True
        return False

    def clear_dlq(self) -> int:
        count = len(self._dlq)
        self._dlq.clear()
        logger.info(f"[BUS] DLQ cleared ({count} entries removed).")
        return count

    # -----------------------------------------------------------------------
    # Stats & Introspection
    # -----------------------------------------------------------------------

    def get_stats(self) -> dict[str, Any]:
        return {
            "is_running": self._is_running,
            "queue_depth": self._queue.qsize(),
            "persist_queue_depth": self._persist_queue.qsize(),
            "dlq_depth": len(self._dlq),
            "subscribers": len(self._subscribers),
            "topics": list(set(s.topic_pattern for s in self._subscribers)),
            "metrics": dict(self._stats),
        }


# ---------------------------------------------------------------------------
# Global singleton
# ---------------------------------------------------------------------------
bus = EventBus()
     