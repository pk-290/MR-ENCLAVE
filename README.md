# 🛰️ MR-Enclave Backend

> A real-time Pub/Sub backend built with **FastAPI** and **WebSocket**

## ✨ Features

- 🔌 **WebSocket** endpoint for `subscribe`, `publish`, `unsubscribe`, `ping`
- 🌐 **REST** endpoints for topic management, health, and stats
- 💾 Per-topic **ring buffer** (last N message replay)
- ⚡ Per-subscriber **asyncio queues** (backpressure-aware)
- 🐳 Fully **Dockerized** for quick local runs

---

## 🚀 Quick Start

### 1. Build the Docker Image

```bash
docker build -t pubsub-backend:latest .
```

### 2. Run the Container

```bash
docker run --rm -p 8000:8000 \
  -e PORT=8000 \
  -e RING_SIZE=100 \
  -e QUEUE_SIZE=100 \
  -e LOG_LEVEL=INFO \
  --name pubsub_app \
  pubsub-backend:latest
```

### 3. Verify It's Running

```bash
docker logs -f pubsub_app
```

**Expected output:**

```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

🎉 **You're live!**
- REST API: `http://localhost:8000`
- WebSocket: `ws://localhost:8000/ws`

---

## 📚 API Reference

### REST Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/topics` | Create a new topic |
| `GET` | `/topics` | List all topics |
| `DELETE` | `/topics/{name}` | Delete a topic |
| `GET` | `/health` | Health check and uptime |
| `GET` | `/stats` | Per-topic metrics |

#### Examples

**Create a Topic**

```bash
curl -X POST http://localhost:8000/topics \
  -H "Content-Type: application/json" \
  -d '{"name":"orders"}'
```

Response:
```json
{
  "status": "created",
  "topic": "orders"
}
```

**List Topics**

```bash
curl http://localhost:8000/topics
```

Response:
```json
{
  "topics": [
    {
      "name": "orders",
      "subscribers": 0
    }
  ]
}
```

**Health Check**

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "uptime_sec": 12,
  "topics": 1,
  "subscribers": 0
}
```

---

## 🔌 WebSocket API

**Connect to:** `ws://localhost:8000/ws`

### Message Types

#### 📥 Subscribe

```json
{
  "type": "subscribe",
  "topic": "orders",
  "client_id": "s1",
  "last_n": 0,
  "request_id": "r-sub-1"
}
```

**Response:**
```json
{
  "type": "ack",
  "request_id": "r-sub-1",
  "status": "ok",
  "topic": "orders"
}
```

#### 📤 Publish

```json
{
  "type": "publish",
  "topic": "orders",
  "message": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "payload": {
      "order_id": 123,
      "status": "created"
    }
  },
  "request_id": "r-pub-1"
}
```

**Publisher receives:**
```json
{
  "type": "ack",
  "request_id": "r-pub-1",
  "status": "ok",
  "topic": "orders"
}
```

**Subscribers receive:**
```json
{
  "type": "event",
  "topic": "orders",
  "message": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "payload": {
      "order_id": 123,
      "status": "created"
    }
  },
  "ts": "2025-01-15T10:30:00Z"
}
```

#### 📤 Unsubscribe

```json
{
  "type": "unsubscribe",
  "topic": "orders",
  "client_id": "s1",
  "request_id": "r-unsub-1"
}
```

#### 💓 Ping/Pong

```json
{
  "type": "ping",
  "request_id": "ping-1"
}
```

**Response:**
```json
{
  "type": "pong",
  "request_id": "ping-1",
  "ts": "2025-01-15T10:30:00Z"
}
```

---

## 🧪 Testing with wscat

### Install wscat

```bash
npm i -g wscat
```

### Test Flow

**Terminal 1 - Subscribe:**

```bash
wscat -c ws://localhost:8000/ws
```

```json
{"type":"subscribe","topic":"orders","client_id":"s1","last_n":0,"request_id":"r-sub-1"}
```

**Terminal 2 - Publish:**

```bash
wscat -c ws://localhost:8000/ws
```

```json
{"type":"publish","topic":"orders","message":{"id":"550e8400-e29b-41d4-a716-446655440000","payload":{"order_id":123,"status":"created"}},"request_id":"r-pub-1"}
```

✅ Watch the subscriber receive the event in real-time!

---

## 🐳 Docker Compose (Optional)

Create `docker-compose.yml`:

```yaml
version: "3.8"

services:
  pubsub:
    build: .
    container_name: pubsub_app
    ports:
      - "8000:8000"
    environment:
      - PORT=8000
      - RING_SIZE=100
      - QUEUE_SIZE=100
      - LOG_LEVEL=INFO
    restart: unless-stopped
```

**Run:**

```bash
docker compose up --build
```

**Stop:**

```bash
docker compose down
```

---

## 🛠️ Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| `TOPIC_NOT_FOUND` | Topic not created | Run `POST /topics` again |
| Validation error for `message.id` | Invalid UUID format | Use valid UUID (try `uuidgen`) |
| WebSocket closes on publish | Shared WS connection | Use unique `client_id` per connection |
| Postman "Invalid protocol: ws:" | Using HTTP tab | Switch to WebSocket tab or use `wscat` |

---

## 📊 Complete API Overview

### REST Layer

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/topics` | POST | Create topic |
| `/topics` | GET | List topics |
| `/topics/{name}` | DELETE | Delete topic |
| `/health` | GET | Health & uptime |
| `/stats` | GET | Topic metrics |

### WebSocket Layer

| Message Type | Direction | Purpose |
|--------------|-----------|---------|
| `subscribe` | Client → Server | Subscribe to topic |
| `publish` | Client → Server | Publish message |
| `unsubscribe` | Client → Server | Unsubscribe from topic |
| `ping` | Client → Server | Heartbeat check |
| `ack` | Server → Client | Acknowledge action |
| `event` | Server → Client | Deliver message |
| `pong` | Server → Client | Heartbeat response |
| `error` | Server → Client | Error notification |

---

## 📝 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 8000 | Server port |
| `RING_SIZE` | 100 | Messages kept per topic |
| `QUEUE_SIZE` | 100 | Max pending messages per subscriber |
| `LOG_LEVEL` | INFO | Logging verbosity |

---

## 🎯 What's Next?

- Add `.dockerignore` for faster rebuilds
- Create `.env.example` for easy configuration
- Implement authentication/authorization
- Add message persistence
- Set up monitoring and metrics

---

## 📄 License

MIT License - Feel free to use this in your projects!

---

**Built with ❤️ using FastAPI and WebSocket**