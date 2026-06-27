# Post-Call Processing Pipeline — System Design & Implementation Challenge

# Post-Call Processing Pipeline — Design Document

**Author:** Mallikarjuna N
**Date:** 27 June 2026

---

## 1. Assumptions

1. The LLM provider enforces strict Requests Per Minute (RPM) and Tokens Per Minute (TPM) limits.
2. Multiple customers execute campaigns concurrently.
3. Every customer has a configurable LLM token allocation based on subscription.
4. Short transcripts (less than four turns) do not require LLM analysis.
5. Call recordings are generated asynchronously by the telephony provider.
6. PostgreSQL is the durable system of record.
7. Redis is used only for caching, coordination and scheduling.
8. Business-critical calls should receive higher processing priority than informational calls.

---

## 2. Problem Diagnosis

The existing implementation works for low traffic but fails at production scale.

The major problems identified are:

* A fixed `asyncio.sleep(45)` delays processing unnecessarily.
* Recording upload failures are silently ignored.
* Celery and Redis together do not provide durable workflow execution.
* Every completed call immediately invokes the LLM without considering provider limits.
* There is no per-customer quota enforcement.
* The circuit breaker completely freezes outbound calling instead of gradually reducing throughput.
* Fire-and-forget tasks may be lost if the API server restarts.
* There is no complete audit trail across the processing pipeline.

---

## 3. Architecture Overview

```
                    Exotel Webhook
                          |
                          v
                  FastAPI Endpoint
                          |
                          v
               Durable Processing Queue
                          |
          +---------------+---------------+
          |                               |
          v                               v
 Recording Poller                 LLM Scheduler
 (Retry + Backoff)          (Rate Limit Aware)
          |                               |
          v                               v
     Upload to S3                Post Call Processor
                                          |
                    +---------------------+----------------------+
                    |                     |                      |
                    v                     v                      v
              Dashboard Update       CRM Push           Lead Stage Update
                                          |
                                          v
                                     Audit Logs
```

### Key design decisions

1. The webhook immediately acknowledges the request and delegates processing.
2. Recording retrieval and LLM analysis are independent.
3. A scheduler controls all LLM traffic.
4. Every interaction receives a correlation ID.
5. Structured audit logs are written throughout the workflow.

---

## 4. Rate Limit Management

The redesigned solution introduces an LLM Scheduler.

Before every LLM request the scheduler verifies:

* Requests Per Minute (RPM)
* Tokens Per Minute (TPM)

If sufficient capacity exists, processing begins immediately.

If capacity is unavailable:

* urgent interactions enter a high-priority queue,
* normal interactions are deferred,
* retries occur automatically after capacity becomes available.

This prevents HTTP 429 errors while keeping provider limits respected.

---

## 5. Per-Customer Token Budgeting

Each customer receives a reserved token allocation.

Example:

* Total Capacity = 90,000 TPM
* Customer A = 20,000 TPM Reserved
* Customer B = 15,000 TPM Reserved
* Remaining capacity becomes a shared pool.

If a customer exceeds their reserved allocation:

* reserved quota is consumed first,
* additional requests use shared capacity if available,
* otherwise requests are queued.

Unused reserved capacity can temporarily be borrowed by other customers.

---

## 6. Differentiated Processing

Calls are divided into two categories.

**High Priority**

* Demo booked
* Callback scheduled
* Sale confirmed
* Customer requested follow-up

These are processed immediately.

**Normal Priority**

* Wrong number
* Spam
* Not interested
* No response

These are processed later whenever capacity becomes available.

This prioritization ensures business-critical interactions are never delayed.

---

## 7. Recording Pipeline

The fixed 45-second delay is replaced with retry polling.

Polling intervals:

* Immediate
* 5 seconds
* 10 seconds
* 20 seconds
* 40 seconds
* 80 seconds

If the recording becomes available, it is uploaded immediately.

If all retries fail:

* structured error log generated,
* retry information stored,
* alert raised for operations.

No recording failure is silently ignored.

---

## 8. Reliability & Durability

The redesigned pipeline guarantees that interactions are never silently lost.

Improvements include:

* Durable task queue
* Retry queue
* Dead-letter queue
* Exponential backoff
* Retry state persistence
* Structured failure logging

Failures remain visible until resolved.

---

## 9. Auditability & Observability

Every interaction receives a unique Correlation ID.

Every processing stage records:

* interaction_id
* correlation_id
* customer_id
* campaign_id
* processing status
* retry count
* token usage
* timestamps
* errors

Alerts are generated for:

* LLM utilization above 80%
* Retry queue growth
* Recording failures
* Dead-letter queue entries
* Persistent processing failures

---

## 10. Data Model

Additional schema objects introduced:

* `customer_llm_budget`
* `analysis_jobs`
* `audit_logs`

Additional interaction fields:

* correlation_id
* processing_priority
* estimated_tokens
* actual_tokens
* analysis_status

These additions support customer budgeting, workflow visibility, and auditing.

---

## 11. Security

Sensitive information includes:

* customer transcripts
* lead PII
* call recordings
* CRM data
* API credentials

Protection measures:

* TLS for all communication
* Encryption at rest
* Restricted IAM access
* Role-based authorization
* Audit logging
* Secret management through environment variables

---

## 12. API Interface

The existing webhook endpoint remains unchanged.

Maintaining backward compatibility avoids changes for the telephony provider while allowing all improvements to be implemented internally.

---

## 13. Trade-offs & Alternatives Considered

| Option                         | Why Considered        | Final Decision                                                |
| ------------------------------ | --------------------- | ------------------------------------------------------------- |
| Immediate LLM processing       | Lowest latency        | Rejected because it violates provider rate limits             |
| Fixed 45-second recording wait | Simple implementation | Replaced with polling and exponential backoff                 |
| Binary circuit breaker         | Easy to implement     | Replaced with gradual scheduling and prioritization           |
| Redis-only retries             | Already available     | Extended with durable retry tracking and dead-letter handling |

---

## 14. Known Weaknesses

Current limitations include:

* Scheduler assumes estimated token usage before actual provider response.
* CRM retry workflow could be further improved.
* Dynamic customer priority adjustment is not yet implemented.

---

## 15. What I Would Do With More Time

1. Implement adaptive token estimation using historical usage.
2. Replace Celery with a workflow engine such as Temporal for stronger durability.
3. Add automatic replay from the dead-letter queue.
4. Build Grafana dashboards for real-time queue and rate-limit monitoring.
5. Add customer-configurable prioritization rules through the admin portal.
