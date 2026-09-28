# Architecture Specification

## 1. Architecture
Modular monolith.

```text
React + Vite
    |
 HTTP/WebSocket
    v
FastAPI
 |---- PostgreSQL
 |---- Deterministic domain services
 |---- LangGraph agent workflows
 |          |
 |          v
 |       OpenAI API
 |
 |---- Razorpay adapter/webhook
 |---- WhatsApp adapter
 `---- APScheduler
```

## 2. Locked Technology Choices
- Backend: Python + FastAPI
- Frontend: React + Vite
- Database: PostgreSQL
- ORM: SQLAlchemy
- Migrations: Alembic
- Agents: LangGraph
- LLM: OpenAI API
- Auth: JWT for merchant portal
- Customer communication: WebSocket
- Scheduler: APScheduler inside FastAPI
- Local DB: Docker Compose PostgreSQL
- Deployment: open decision; verify current low-cost option during implementation

## 3. Agent Architecture
Hybrid architecture:
- Sales Agent: LLM/LangGraph orchestrator
- PC Builder Agent: LLM/LangGraph workflow
- Recommendation/Support: grounded tool + constrained reasoning
- Pricing, Inventory, compatibility, eligibility, intervention guards, attribution, payment state: deterministic services

## 4. Hard Architecture Invariants
- LLMs never directly access DB.
- LLMs never mutate payments.
- LLMs never modify merchant config.
- LLMs cannot bypass inventory.
- LLMs cannot bypass compatibility.
- LLMs cannot bypass discount limits.
- LLMs cannot bypass intervention limits.
- LLMs cannot determine final attribution.
- PC builds require explicit customer approval.
- Commerce mutations go through deterministic services.
- Client totals are never authoritative.
- Razorpay webhook signatures are verified.
- Webhooks are idempotent.

## 5. LLM Boundary
LLM receives only allowlisted context/tools. No arbitrary SQL, HTTP, filesystem, credentials, or infrastructure access.

LLM output is untrusted until validated.

## 6. Memory
Hybrid:
- LangGraph short-term execution/checkpoint state
- PostgreSQL durable business state
No long-term customer profiling.

## 7. Scheduler
APScheduler triggers recovery evaluation only. It does not directly generate messages or mutate commerce.

## 8. Payments
Backend creates Razorpay order. Frontend launches checkout. Backend verifies client signature where applicable. Razorpay webhook is the server-side event authority. Duplicate/out-of-order events are tolerated.

## 9. Local Development
Docker Compose supplies PostgreSQL. React/FastAPI may run locally. Public webhook testing must use a currently supported public endpoint/tunnel; do not assume ngrok works for Razorpay webhooks.

## 10. Deferred Decisions
- WhatsApp provider
- deployment platform
- exact OpenAI model identifier

These must be resolved by current implementation-time verification, not guessed.
