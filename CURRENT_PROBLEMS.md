# Current System Analysis

## Existing Flow

```
Call End Webhook
        │
        ▼
FastAPI Endpoint
        │
        ▼
Celery Task
        │
        ├────────► Wait 45 Seconds
        │
        ▼
Recording Upload
        │
        ▼
LLM Analysis
        │
        ▼
Dashboard Update
        │
        ▼
CRM Push
```

---

# Problems Identified

## Problem 1 – Fixed 45 Second Recording Wait

Current Implementation

```python
await asyncio.sleep(45)
```

Issues

- Wastes time if recording is available early
- Misses recordings available after 45 seconds
- No retry mechanism
- No alerting
- Silent failures

Solution

- Replace with Recording Poller
- Exponential Backoff
- Configurable retry count
- Structured logging

---

## Problem 2 – No LLM Rate Limiting

Current Behaviour

Every completed interaction directly calls the LLM.

Issues

- LLM provider limit ignored
- 429 Too Many Requests
- Retry storm
- Queue backlog

Solution

- Global Token Bucket
- Request Scheduler
- Deferred Queue

---

## Problem 3 – No Customer Budget

Current Behaviour

All customers share one LLM pool.

Issues

- One customer can consume all capacity
- Unfair scheduling

Solution

- Per Customer Budget
- Reserved Capacity
- Borrow Unused Capacity

---

## Problem 4 – Redis Task Loss

Current Behaviour

Celery Broker
Retry Queue

Both depend on Redis.

Issues

- Redis restart loses work
- No durability
- No replay

Solution

- Durable Job Table
- Dead Letter Queue
- Outbox Pattern

---

## Problem 5 – Binary Circuit Breaker

Current Behaviour

90%

↓

Freeze Dialer

↓

1800 Seconds

Issues

- Stops business
- No gradual slowdown

Solution

- Backpressure
- Queue Scheduling
- Rate-aware dispatch

---

## Problem 6 – Fire and Forget Tasks

Current Behaviour

asyncio.create_task()

Issues

- Lost on restart
- No retries
- No tracking

Solution

- Durable Worker
- Audit Logging

---

## Problem 7 – No Audit Trail

Current Behaviour

Basic logging

Issues

- Cannot trace interaction
- Difficult debugging

Solution

- Structured JSON Logs
- Correlation ID
- Audit Events

---

## Problem 8 – No Priority Processing

Current Behaviour

Every interaction treated equally.

Issues

- Urgent calls delayed
- Low-value calls consume quota

Solution

Priority Queue

HIGH
MEDIUM
LOW