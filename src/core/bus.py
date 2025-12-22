"""
Message Bus System - Event-Driven Architecture Core

Implements an in-memory asynchronous message bus for agent coordination.
"""

import asyncio
import time
import uuid
import logging
from typing import Dict, List, Any, Callable, Awaitable, Optional
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class Event:
    """Standardized event envelope"""
    topic: str
    payload: Dict[str, Any] = field(default_factory=dict)
    sender: str = "system"
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    timestamp: float = field(default_factory=time.time)


# Type definition for event handlers
EventHandler = Callable[[Event], Awaitable[None]]


class MessageBus:
    """In-Memory Asynchronous Message Bus"""

    def __init__(self):
        self._subscribers: Dict[str, List[EventHandler]] = defaultdict(list)
        self._history: List[Event] = []
        self._lock = asyncio.Lock()

    def subscribe(self, topic: str, handler: EventHandler):
        """
        Subscribe to a specific topic

        Args:
            topic: Event topic string
            handler: Async callback function
        """
        self._subscribers[topic].append(handler)
        logger.debug(f"Subscribed to {topic}: {handler.__name__}")

    async def publish(self, event: Event):
        """
        Publish an event to all subscribers asynchronously (Fire-and-Forget)

        Args:
            event: Event object
        """
        self._history.append(event)

        # Log flow
        logger.info(f"[BUS] {event.sender} -> {event.topic}")

        if event.topic in self._subscribers:
            handlers = self._subscribers[event.topic]
            if not handlers:
                return

            # Execute handlers in background (Fire-and-Forget)
            for handler in handlers:
                # Create a task for each handler
                asyncio.create_task(self._safe_execute(handler, event))

    async def _safe_execute(self, handler: EventHandler, event: Event):
        """Execute handler with error safety"""
        try:
            await handler(event)
        except Exception as e:
            logger.error(f"Error handling event {event.topic} in {handler.__name__}: {e}", exc_info=True)

    @property
    def history(self) -> List[Event]:
        return self._history
