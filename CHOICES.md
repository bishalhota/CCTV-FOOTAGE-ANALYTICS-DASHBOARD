# Architectural Choices & Tradeoffs

As part of the Store Intelligence system design, several pivotal architectural decisions were made. This document outlines the problem context, considered options, chosen solution, and the resulting tradeoffs.

## 1. Object Detection: YOLOv8n vs. Larger Models
**Problem:** We need real-time, accurate bounding box detection for people within camera frames.
**Options Considered:**
1. YOLOv8x (Extra Large) or YOLOv9
2. YOLOv8n (Nano)
3. Cloud-based Vision APIs (e.g., AWS Rekognition)

**Chosen Solution:** **YOLOv8n (Nano)**
**Tradeoffs:** YOLOv8n sacrifices extreme edge-case accuracy (e.g., heavily occluded individuals in low light) for blazing-fast inference speeds. Because we intend to deploy this on edge devices (like Jetson Nanos) at 2+ FPS, inference latency is our primary bottleneck. Larger models would necessitate expensive GPU infrastructure per store.
**Rejected Alternatives:** Cloud APIs were rejected due to unacceptable bandwidth costs for streaming 24/7 video.

## 2. Multi-Object Tracking: ByteTrack
**Problem:** We must track individual IDs across consecutive video frames to prevent recounting the same person.
**Options Considered:** DeepSORT, StrongSORT, ByteTrack.
**Chosen Solution:** **ByteTrack**
**Tradeoffs:** ByteTrack excels at maintaining tracks even when detection confidence drops, recovering bounding boxes that other trackers discard. The tradeoff is a higher reliance on the base detection model's accuracy, and it can suffer from identity switches during severe occlusions. We mitigate this using the ReID service.

## 3. Asynchronous Event Architecture: Redis Streams
**Problem:** The edge node processes frames and generates high-velocity tracking data. This data needs to be ingested by the backend without blocking the video processing loop.
**Options Considered:** REST API calls, Redis Pub/Sub, Kafka, Redis Streams.
**Chosen Solution:** **Redis Streams**
**Tradeoffs:** 
- REST API would tightly couple the edge and backend, causing dropped frames on network spikes.
- Redis Pub/Sub lacks persistence; if the backend restarts, events are lost forever.
- Kafka is robust but introduces massive operational overhead for a Top-30 submission MVP.
- **Redis Streams** offers a perfect middle ground: it provides persistent, consumer-group based event queuing with sub-millisecond latency, without the operational burden of Kafka.

## 4. Vector Search: PostgreSQL + pgvector
**Problem:** Storing and rapidly querying 512-dimensional ReID vectors to re-identify customers.
**Options Considered:** Pinecone/Milvus (Dedicated Vector DBs), PostgreSQL + pgvector.
**Chosen Solution:** **PostgreSQL + pgvector**
**Tradeoffs:** While dedicated vector databases offer superior scale for millions of vectors, our domain (a single store) typically sees fewer than 10,000 unique visitors a day. Adding a separate vector DB increases infrastructure complexity. `pgvector` allows us to perform exact Nearest Neighbor (KNN) and Cosine Distance searches directly alongside our relational business data (ACID compliance), massively simplifying our data tier.

## 5. Real-Time Frontend Updates: SSE vs. WebSockets
**Problem:** The React dashboard needs real-time metric updates from the FastAPI backend.
**Options Considered:** WebSockets, Server-Sent Events (SSE), Short Polling.
**Chosen Solution:** **Server-Sent Events (SSE)**
**Tradeoffs:** WebSockets allow bidirectional communication, which is overkill since our dashboard only *consumes* analytics. SSE is strictly unidirectional (server-to-client), operates over standard HTTP/1.1 (or HTTP/2 multiplexing), and natively handles automatic reconnections via the browser's `EventSource` API. The only downside is limited concurrent connections over HTTP/1.1 (6 per domain), which is resolved when deploying behind an HTTP/2 proxy like Render/Vercel.

## 6. Sequential Processing Design
**Problem:** Running 5 parallel camera streams locally causes immediate Out-Of-Memory (OOM) crashes on standard developer laptops.
**Options Considered:**
1. Require users to have 16GB+ VRAM GPUs.
2. Process frames sequentially in a round-robin loop.
**Chosen Solution:** **Sequential Round-Robin Processing**
**Tradeoffs:** We sacrifice simultaneous frame-level accuracy for system stability. By processing `cam-1`, then `cam-2`, etc., we dramatically lower the memory footprint. The tradeoff is "choppy" tracking (effectively reducing the FPS per camera), but it ensures the system actually runs and passes the Acceptance Gate on standard hardware.
