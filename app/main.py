# import os
# import json
# import asyncio
# from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
# from fastapi.responses import JSONResponse
# from fastapi.middleware.cors import CORSMiddleware
# from typing import Dict
# from .models.model import SubscribeMsg, UnsubscribeMsg, PublishMsg
# from .pubsub_engine.pubsub import manager
# import time
# from .utils.logger_wrapper import log_exceptions,log_async_exceptions
# from .utils.util import make_ack,make_error,make_info,make_event,make_pong

# app = FastAPI(title="pubsub-backend")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_methods=["*"],
#     allow_headers=["*"], 
# )


# @app.on_event("startup")
# async def startup_event():
#     app.state.started_at = time.time()

# # REST endpoints for topics
# @app.post("/topics")
# async def create_topic(payload: dict):
#     name = payload.get("name")
#     if not name:
#         raise HTTPException(status_code=400, detail="name required")
#     ok = await manager.create_topic(name)
#     if not ok:
#         return JSONResponse(status_code=409, content={"detail": "topic exists"})
#     return {"name": name}

# @app.get("/topics")
# @log_async_exceptions
# async def list_topics():
#     topics = await manager.list_topics()
#     return {"topics": topics}

# @app.delete("/topics/{name}")
# @log_async_exceptions
# async def delete_topic(name: str):
#     ok = await manager.delete_topic(name)
#     if not ok:
#         raise HTTPException(status_code=404, detail="topic not found")
#     return {"deleted": name}

# @app.get("/health")
# @log_async_exceptions
# async def health():
#     # uptime
#     started = getattr(app.state, "started_at", time.time())
#     uptime = int(time.time() - started)

#     # get topics and subscriber totals from manager.get_stats()
#     stats = await manager.get_stats()  # returns dict per topic
#     topic_count = len(stats)
#     total_subscribers = sum(v.get("subscribers", 0) for v in stats.values())

#     return JSONResponse(
#         status_code=200,
#         content={
#             "uptime_sec": uptime,
#             "topics": topic_count,
#             "subscribers": total_subscribers,
#         },
#     )

# @app.get("/stats")
# @log_async_exceptions
# async def stats():
#     s = await manager.get_stats()
#     return {"topics": s}

# # --- WebSocket endpoint ---
# # Protocol: JSON messages with types: subscribe, unsubscribe, publish, ping
# @app.websocket("/ws")
# async def websocket_endpoint(ws: WebSocket):
#     await ws.accept()
#     # bookkeeping: map local subscriber id -> (topic, sub.id)
#     my_subscriptions = {}  # subscriber_id -> (topic_name, Subscriber.id)
#     sender_tasks = {}  # subscriber_id -> task

#     async def subscriber_sender_task(sub):
#         """Task that pumps messages from sub.queue to the client's websocket."""
#         try:
#             while True:
#                 item = await sub.queue.get()
#                 if item is None:
#                     break
#                 # item: {"message":..., "timestamp": ...}
#                 out = {
#                     "type": "event",
#                     "topic": sub.ws.topic_name if hasattr(sub.ws,'topic_name') else "unknown",
#                     "message": item["message"],
#                     "timestamp": item["timestamp"],
#                 }
#                 await ws.send_json(out)
#         except WebSocketDisconnect:
#             pass
#         except Exception:
#             pass

#     try:
#         while True:
#             raw = await ws.receive_text()
#             data = json.loads(raw)
#             t = data.get("type")
        
#             if msg.type == "subscribe":
#                 # check topic exists
#                 topics = await manager.list_topics()
#                 if msg.topic not in topics:
#                     await ws.send_json(make_error("TOPIC_NOT_FOUND", "topic does not exist", request_id=msg.request_id, topic=msg.topic))
#                     continue
#                 # use client_id as subscriber identifier
#                 sub = await manager.subscribe(msg.topic, ws, client_id=msg.client_id)
#                 await ws.send_json(make_ack(request_id=msg.request_id, topic=msg.topic))
#                 if msg.last_n:
#                     last = await manager.get_last_n(msg.topic, msg.last_n)
#                     for item in last:
#                         await ws.send_json(make_event(msg.topic, item, request_id=None))

#             elif t == "unsubscribe":
#                 msg = UnsubscribeMsg(**data)
#                 # find subscriber id(s) for this ws for the topic
#                 # we stored subscriber IDs in my_subscriptions
#                 removed = []
#                 for sid, (topic_name, subid) in list(my_subscriptions.items()):
#                     if topic_name == msg.topic:
#                         await manager.unsubscribe(topic_name, subid)
#                         # cancel sender task
#                         task = sender_tasks.pop(subid, None)
#                         if task:
#                             task.cancel()
#                         my_subscriptions.pop(sid, None)
#                         removed.append(subid)
#                 await ws.send_json({"type":"unsubscribed","topic": msg.topic, "removed": removed})

#             elif t == "publish":
#                 msg = PublishMsg(**data)
#                 ok = await manager.publish(msg.topic, msg.payload)
#                 if not ok:
#                     await ws.send_json({"type":"error","detail":"topic not found"})
#                 else:
#                     await ws.send_json({"type":"published","topic":msg.topic})

#             elif t == "ping":
#                 await ws.send_json({"type":"pong"})

#             else:
#                 await ws.send_json({"type":"error","detail":"unknown message type"})

#     except WebSocketDisconnect:
#         # cleanup: unsubscribe all
#         for sid, (topic_name, subid) in list(my_subscriptions.items()):
#             try:
#                 await manager.unsubscribe(topic_name, subid)
#             except Exception:
#                 pass
#         # cancel tasks
#         for t in sender_tasks.values():
#             t.cancel()
#     except Exception:
#         # ensure cleanup even in error case
#         for sid, (topic_name, subid) in list(my_subscriptions.items()):
#             try:
#                 await manager.unsubscribe(topic_name, subid)
#             except Exception:
#                 pass
#         for t in sender_tasks.values():
#             t.cancel()
#         raise

# app/main.py
import os
import json
import asyncio
import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict

from .models.model import SubscribeMsg, UnsubscribeMsg, PublishMsg
from .pubsub_engine.pubsub import manager
from .utils.logger_wrapper import log_async_exceptions
from .utils.util import make_ack, make_error, make_event, make_pong

app = FastAPI(title="pubsub-backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    app.state.started_at = time.time()

@app.post("/topics")
async def create_topic(payload: dict):
    name = payload.get("name")
    if not name:
        raise HTTPException(status_code=400, detail="name required")
    ok = await manager.create_topic(name)
    if not ok:
        return JSONResponse(status_code=409, content={"detail": "topic exists"})
    return {"status": "created", "topic": name}

@app.get("/topics")
@log_async_exceptions
async def list_topics():
    stats = await manager.get_stats()
    topics = [{"name": name, "subscribers": v.get("subscribers", 0)} for name, v in stats.items()]
    return {"topics": topics}

@app.delete("/topics/{name}")
@log_async_exceptions
async def delete_topic(name: str):
    ok = await manager.delete_topic(name)
    if not ok:
        raise HTTPException(status_code=404, detail="topic not found")
    return {"status": "deleted", "topic": name}

@app.get("/health")
@log_async_exceptions
async def health():
    started = getattr(app.state, "started_at", time.time())
    uptime = int(time.time() - started)
    stats = await manager.get_stats()
    topic_count = len(stats)
    total_subscribers = sum(v.get("subscribers", 0) for v in stats.values())
    return JSONResponse(status_code=200, content={
        "uptime_sec": uptime,
        "topics": topic_count,
        "subscribers": total_subscribers,
    })

@app.get("/stats")
@log_async_exceptions
async def stats():
    s = await manager.get_stats()
    return {"topics": s}

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    my_subscriptions: Dict[str, str] = {}
    sender_tasks: Dict[str, asyncio.Task] = {}
    active = True

    async def subscriber_sender_task(sub):
        """Continuously sends messages from sub.queue to the websocket."""
        try:
            while active:
                item = await sub.queue.get()
                if item is None:  # graceful exit signal
                    break
                message = item.get("message", item)
                topic_name = getattr(sub, "topic_name", "unknown")
                await ws.send_json(make_event(topic_name, message))
        except asyncio.CancelledError:
            # Graceful stop, don't raise
            pass
        except WebSocketDisconnect:
            pass
        except Exception:
            pass

    try:
        while True:
            raw = await ws.receive_text()
            data = json.loads(raw)
            t = data.get("type")
            request_id = data.get("request_id")

            if t == "subscribe":
                try:
                    msg = SubscribeMsg(**data)
                except Exception as e:
                    await ws.send_json(make_error("BAD_REQUEST", str(e), request_id))
                    continue

                stats = await manager.get_stats()
                if msg.topic not in stats:
                    await ws.send_json(make_error("TOPIC_NOT_FOUND", "topic does not exist", request_id, topic=msg.topic))
                    continue

                sub = await manager.subscribe(msg.topic, msg.client_id, ws)
                setattr(sub, "topic_name", msg.topic)
                my_subscriptions[msg.client_id] = msg.topic

                if msg.client_id not in sender_tasks:
                    sender_tasks[msg.client_id] = asyncio.create_task(subscriber_sender_task(sub))

                await ws.send_json(make_ack(request_id, msg.topic))

                if getattr(msg, "last_n", 0):
                    last_items = await manager.get_last_n(msg.topic, int(msg.last_n))
                    for item in last_items:
                        await ws.send_json(make_event(msg.topic, item.get("message", item)))
                continue

            elif t == "unsubscribe":
                try:
                    msg = UnsubscribeMsg(**data)
                except Exception as e:
                    await ws.send_json(make_error("BAD_REQUEST", str(e), request_id))
                    continue

                ok = await manager.unsubscribe(msg.topic, msg.client_id)
                topic = my_subscriptions.pop(msg.client_id, None)

                if task := sender_tasks.pop(msg.client_id, None):
                    task.cancel()
                await ws.send_json(make_ack(request_id, topic or msg.topic))
                continue

            elif t == "publish":
                try:
                    msg = PublishMsg(**data)
                except Exception as e:
                    await ws.send_json(make_error("BAD_REQUEST", str(e), request_id))
                    continue

                stats = await manager.get_stats()
                if msg.topic not in stats:
                    await ws.send_json(make_error("TOPIC_NOT_FOUND", "topic does not exist", request_id, topic=msg.topic))
                    continue

                m = {"id": str(msg.message.id), "payload": msg.message.payload}
                ok = await manager.publish(msg.topic, m)
                if not ok:
                    await ws.send_json(make_error("INTERNAL", "publish failed", request_id, topic=msg.topic))
                    continue

                await ws.send_json(make_ack(request_id, msg.topic))
                continue

            elif t == "ping":
                await ws.send_json(make_pong(request_id))
                continue

            else:
                await ws.send_json(make_error("BAD_REQUEST", f"unknown type: {t}", request_id))

    except WebSocketDisconnect:
        pass  # don't raise, let cleanup handle
    finally:
        active = False
        for client_id, topic in list(my_subscriptions.items()):
            try:
                await manager.unsubscribe(topic, client_id)
            except Exception:
                pass
        # send sentinel to queues instead of cancelling to avoid disconnect storms
        for task in sender_tasks.values():
            if not task.done():
                task.cancel()