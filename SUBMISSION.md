Section 1 
# Post-Call Processing Pipeline Redesign

## Author

Mallikarjuna N

---

# Overview

This document describes the redesign of the existing post-call processing pipeline to make it scalable, reliable, observable and rate-limit aware.

The current implementation works correctly for small workloads but fails under production-scale traffic where approximately 100,000 interactions are processed during campaign execution.

The redesign focuses on five primary objectives:

- Respect LLM provider rate limits
- Guarantee that no interaction is permanently lost
- Fairly allocate LLM capacity between customers
- Improve observability and auditability
- Replace brittle synchronous operations with durable background processing

Section 2 — Assumptions

---

# 1. Assumptions

The following assumptions were made while designing the solution.

1. The LLM provider exposes hard Requests Per Minute (RPM) and Tokens Per Minute (TPM) limits.

2. Multiple enterprise customers execute campaigns simultaneously.

3. Every customer has an allocated token budget based on subscription.

4. Some call outcomes require immediate processing while others can tolerate delay.

5. Recordings become available asynchronously through the telephony provider API.

6. PostgreSQL is the system of record and should be considered durable storage.

7. Redis is used only for caching and short-lived coordination, not permanent persistence.

8. Short transcripts (<4 turns) do not require LLM processing.

Section 3 — Existing Architecture

---

# 2. Existing Architecture

Current processing flow

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

## Current Problems

- Fixed recording delay
- No LLM scheduling
- No token budgeting
- Binary circuit breaker
- Fire-and-forget background tasks
- Redis as single point of failure
- Missing audit trail
- No priority processing

Section 4 — Proposed Architecture

---

# 3. Proposed Architecture

```
                    Call End Webhook
                           │
                           ▼
                 FastAPI Endpoint
                           │
                           ▼
               Durable Job (Database)
                           │
                           ▼
                 Priority Classifier
                 /                 \
                /                   \
         High Priority         Deferred Queue
                │                   │
                └──────────┬────────┘
                           ▼
                  LLM Scheduler
         (Rate Limit + Customer Budget)
                           │
                           ▼
                     LLM Processor
                    /             \
                   /               \
          Recording Poller     Audit Logger
                   │               │
                   ▼               ▼
             Dashboard        CRM / Signals
```

## Key Improvements

- Durable processing pipeline
- Rate-limit aware scheduling
- Customer-aware token allocation
- Retryable recording polling
- Structured audit logging
- Priority-based execution

1. Overview ✅

2. Assumptions ✅

3. Existing Architecture ✅

4. Proposed Architecture ✅

5. Rate Limiting ✅

6. Customer Budget ✅

7. Recording Pipeline ✅