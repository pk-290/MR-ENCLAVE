M.R-EnClaVe 
Here you go — a pure Markdown version of the README, ready to drop into your repo as README.md.
All tables, code blocks, and spacing are fully GitHub-render-safe — no indentation issues, no broken alignment.

⸻

🛰️ Pub/Sub Backend — FastAPI + WebSocket

A real-time Pub/Sub backend built with FastAPI, supporting:
	•	WebSocket endpoint for subscribe, publish, unsubscribe, ping
	•	REST endpoints for topic management, health, and stats
	•	Per-topic ring buffer (last_n message replay)
	•	Per-subscriber asyncio queues (backpressure-aware)
	•	Fully Dockerized for quick local runs

⸻

🧱 Build and Run with Docker

1️⃣ Build the image

docker build -t pubsub-backend:latest .

2️⃣ Run the container

docker run --rm -p 8000:8000 \
  -e PORT=8000 \
  -e RING_SIZE=100 \
  -e QUEUE_SIZE=100 \
  -e LOG_LEVEL=INFO \
  --name pubsub_app \
  pubsub-backend:latest

3️⃣ Verify it’s running

docker logs -f pubsub_app

Expected logs:

INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.

The API and WebSocket are now live at:
	•	REST → http://localhost:8000
	•	WebSocket → ws://localhost:8000/ws

⸻

🧩 API Endpoints Overview

REST Endpoints

Method	Path	Body Example	Response Example	Description
POST	/topics	{ "name": "orders" }	{ "status": "created", "topic": "orders" }	Create a new topic
GET	/topics	—	{ "topics": [ { "name": "orders", "subscribers": 0 } ] }	List topics
DELETE	/topics/{name}	—	{ "status": "deleted", "topic": "orders" }	Delete a topic
GET	/health	—	{ "uptime_sec": 12, "topics": 1, "subscribers": 0 }	Health and uptime
GET	/stats	—	{ "topics": { "orders": { "messages": 10, "subscribers": 2 } } }	Per-topic metrics


⸻

WebSocket Endpoint

Connect at:
ws://localhost:8000/ws

Allowed client → server message types:

Type	Required Fields	                                    Example	Server Response
subscribe	topic, client_id, optional last_n, request_id	{"type":"subscribe","topic":"orders","client_id":"s1","last_n":0,"request_id":"r-sub-1"}	{"type":"ack","request_id":"r-sub-1","status":"ok","topic":"orders"}
unsubscribe	topic, client_id, request_id	{"type":"unsubscribe","topic":"orders","client_id":"s1","request_id":"r-unsub-1"}	{"type":"ack","request_id":"r-unsub-1","status":"ok","topic":"orders"}
publish	topic, message.id (UUID), message.payload, request_id	{"type":"publish","topic":"orders","message":{"id":"550e8400-e29b-41d4-a716-446655440000","payload":{"order_id":101}},"request_id":"r-pub-1"}	Publisher: ack; Subscribers: event
ping	optional request_id	{"type":"ping","request_id":"ping-1"}	{"type":"pong","request_id":"ping-1"}

Server → Client messages:
	•	ack — confirms subscribe/publish/unsubscribe success
	•	event — sent to all subscribers of a topic when a message is published
	•	pong — heartbeat reply
	•	error — structured error (e.g. invalid payload, unknown topic)

⸻

🧪 Quick Tests

Create a Topic

curl -X POST http://localhost:8000/topics \
  -H "Content-Type: application/json" \
  -d '{"name":"orders"}'

Expected:

{ "status": "created", "topic": "orders" }

List Topics

curl http://localhost:8000/topics

Expected:

{ "topics": [ { "name": "orders", "subscribers": 0 } ] }

Health & Stats

curl http://localhost:8000/health
curl http://localhost:8000/stats


⸻

⚡ WebSocket Tests (using wscat)

Install wscat (if not installed):

npm i -g wscat

1️⃣ Subscribe (Terminal A)

wscat -c ws://localhost:8000/ws

Then send:

{"type":"subscribe","topic":"orders","client_id":"s1","last_n":0,"request_id":"r-sub-1"}

Expected response:

{ "type":"ack","request_id":"r-sub-1","status":"ok","topic":"orders" }

2️⃣ Publish (Terminal B)

wscat -c ws://localhost:8000/ws

Then send:

{"type":"publish","topic":"orders","message":{"id":"550e8400-e29b-41d4-a716-446655440000","payload":{"order_id":123,"status":"created"}},"request_id":"r-pub-1"}

Expected:
	•	Publisher receives:

{ "type":"ack","request_id":"r-pub-1","status":"ok","topic":"orders" }


	•	Subscriber receives:

{ "type":"event","topic":"orders","message":{"id":"...","payload":{"order_id":123,"status":"created"}},"ts":"..." }



3️⃣ Unsubscribe

{"type":"unsubscribe","topic":"orders","client_id":"s1","request_id":"r-unsub-1"}

4️⃣ Ping / Pong

{"type":"ping","request_id":"ping-1"}

Expected:

{"type":"pong","request_id":"ping-1","ts":"..."}


⸻

🧰 Troubleshooting

Symptom	Likely Cause	Fix
TOPIC_NOT_FOUND	Topic not created or lost after restart	Run POST /topics again; avoid --reload
Validation error for message.id	Invalid UUID format	Use valid UUID (uuidgen) or change schema to str
WebSocket closes on publish	Shared WS in send task or duplicate client_id	Use per-connection WS and unique client_id
Postman “Invalid protocol: ws:”	Used HTTP tab instead of WebSocket tab	Use Hoppscotch WebSocket or wscat


⸻

🧭 Endpoint Summary

Layer	Endpoint	Direction	Description
REST	POST /topics	Client → Server	Create a topic
REST	GET /topics	Client → Server	List topics
REST	DELETE /topics/{name}	Client → Server	Delete a topic
REST	GET /health	Client → Server	Uptime and counts
REST	GET /stats	Client → Server	Topic metrics
WS	subscribe	Client → Server	Subscribe to topic
WS	ack	Server → Client	Acknowledge subscribe/publish/unsubscribe
WS	publish	Client → Server	Publish message
WS	event	Server → Client	Deliver message to subscribers
WS	unsubscribe	Client → Server	Stop subscription
WS	ping / pong	Both	Connection heartbeat
WS	error	Server → Client	Structured error message


⸻

🧱 Optional — Run with Docker Compose

Create a file named docker-compose.yml:

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

Then run:

docker compose up --build

Stop it with:

docker compose down


⸻

✅ Done

The container exposes:
	•	REST → http://localhost:8000
	•	WebSocket → ws://localhost:8000/ws

Test using curl, wscat, or the Hoppscotch WebSocket tab.

⸻

Would you like me to add .dockerignore and .env.example sections next to keep rebuilds faster and configs clean?