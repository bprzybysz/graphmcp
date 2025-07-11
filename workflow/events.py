from collections import defaultdict
from typing import Callable, Dict, List


class EventBus:
    """
    A simple synchronous event bus for decoupling components.
    """

    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = defaultdict(list)

    def subscribe(self, event_type: str, callback: Callable):
        """
        Subscribe a callback to a specific event type.
        """
        self._listeners[event_type].append(callback)

    def publish(self, event_type: str, *args, **kwargs):
        """
        Publish an event to all subscribed listeners.
        """
        if event_type in self._listeners:
            for callback in self._listeners[event_type]:
                try:
                    callback(*args, **kwargs)
                except Exception as e:
                    # In a real app, you'd want more robust error handling here
                    print(f"Error in event bus callback for {event_type}: {e}")


# Global event bus instance
event_bus = EventBus()
