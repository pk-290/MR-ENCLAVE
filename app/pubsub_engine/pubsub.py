import asyncio
import time
from typing import Dict, Set, Any, Optional
from dataclasses import dataclass, field
from uuid import uuid4
from ..utils.logger_wrapper import log_async_exceptions,log_exceptions

def now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

@dataclass
class Subscriber:
    id: str
    queue: asyncio.Queue
    ws: object  # store websocket reference for cleanup (not used for sending here)

@dataclass
class Topic:
    name: str
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    subscribers: Dict[str, Subscriber] = field(default_factory=dict)
    # optional ring buffer:
    ring: asyncio.Queue = field(default_factory=lambda: asyncio.Queue(100))  # simple bounded buffer for last_n

class PubSubManager:
    def __init__(self):
        self.topics: Dict[str, Topic] = {}
        self.global_lock = asyncio.Lock()
    
    @log_async_exceptions
    async def create_topic(self, name: str):
        async with self.global_lock:
            if name in self.topics:
                return False
            self.topics[name] = Topic(name=name)
            return True

    @log_async_exceptions
    async def delete_topic(self, name: str):
        async with self.global_lock:
            if name not in self.topics:
                return False
            # cleanup subscribers
            topic = self.topics.pop(name)
            for sid, sub in list(topic.subscribers.items()):
                await self._close_subscriber_queue(sub)
            return True
        
    @log_async_exceptions
    async def list_topics(self):
        async with self.global_lock:
            return list(self.topics.keys())

    @log_async_exceptions
    async def subscribe(self, topic_name: str, client_id: str, ws, queue_maxsize: int = 100):
        # ensure topic exists
        if topic_name not in self.topics:
            return None  # or raise/return False depending on your calling convention

        topic = self.topics[topic_name]   # <-- bind the topic here

        # use client_id as subscriber id
        async with topic.lock:
            if client_id in topic.subscribers:
                return topic.subscribers[client_id]   # idempotent
            q = asyncio.Queue(maxsize=queue_maxsize)
            sub = Subscriber(id=client_id, queue=q, ws=ws)
            topic.subscribers[client_id] = sub
            return sub
        
    @log_async_exceptions
    async def unsubscribe(self, topic_name: str, subscriber_id: str):
        if topic_name not in self.topics:
            return False
        topic = self.topics[topic_name]
        async with topic.lock:
            if subscriber_id in topic.subscribers:
                sub = topic.subscribers.pop(subscriber_id)
                await self._close_subscriber_queue(sub)
                return True
            return False
        
    @log_async_exceptions
    async def publish(self, topic_name: str, message: Any):
        if topic_name not in self.topics:
            return False
        topic = self.topics[topic_name]
        timestamped = {"message": message, "timestamp": now_iso()}
        # store in ring (best-effort, non-blocking)
        try:
            topic.ring.put_nowait(timestamped)
        except asyncio.QueueFull:
            # drop oldest: remove one and put
            try:
                _ = topic.ring.get_nowait()
                topic.ring.put_nowait(timestamped)
            except Exception:
                pass
        # fan-out
        async with topic.lock:
            for sid, sub in list(topic.subscribers.items()):
                try:
                    # non-blocking put to subscriber's queue to avoid blocking publisher
                    sub.queue.put_nowait(timestamped)
                except asyncio.QueueFull:
                    # backpressure policy: drop oldest from subscriber queue
                    try:
                        _ = sub.queue.get_nowait()
                        sub.queue.put_nowait(timestamped)
                    except Exception:
                        # as last resort, remove slow subscriber
                        await self._close_subscriber_queue(sub)
                        topic.subscribers.pop(sid, None)
        return True
    
    @log_async_exceptions
    async def get_last_n(self, topic_name: str, n: int):
        if topic_name not in self.topics:
            return []
        topic = self.topics[topic_name]
        items = []
        # queue doesn't support direct slicing; copy to list (non-blocking)
        q = topic.ring
        try:
            items = list(q._queue)[-n:]
        except Exception:
            items = []
        return items

    @log_async_exceptions
    async def _close_subscriber_queue(self, sub: Subscriber):
        # put sentinel for reader to exit
        try:
            sub.queue.put_nowait(None)
        except Exception:
            pass

    @log_async_exceptions
    async def get_stats(self):
        out = {}
        async with self.global_lock:
            for name, topic in self.topics.items():
                async with topic.lock:
                    out[name] = {
                        "subscribers": len(topic.subscribers),
                        "buffer_size": topic.ring.qsize()
                    }
        return out

# singleton
manager = PubSubManager()