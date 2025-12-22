"""
Base Agent Class
"""

from abc import ABC, abstractmethod
from typing import Any
import logging

from ..core.bus import MessageBus, Event

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all event-driven agents"""

    def __init__(self, name: str, bus: MessageBus):
        self.name = name
        self.bus = bus
        self.setup_subscriptions()
        logger.debug(f"Agent {name} initialized")

    @abstractmethod
    def setup_subscriptions(self):
        """Register interest in specific topics"""
        pass

    async def publish(self, topic: str, payload: Any = None):
        """Helper to publish events"""
        if payload is None:
            payload = {}

        event = Event(
            topic=topic,
            payload=payload,
            sender=self.name
        )
        await self.bus.publish(event)
