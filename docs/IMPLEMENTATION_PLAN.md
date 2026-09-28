# Implementation Plan

## Phase 0 — Environment Bootstrap
1. Inspect OS/tooling.
2. Detect Python, Node/npm, Git, Docker/Compose, PostgreSQL tooling.
3. Install missing required prerequisites where possible.
4. Verify versions.
5. Create `.env.example`.
6. Initialize repository.

Do not assume prerequisites already exist.

## Phase 1 — Foundation
- Docker Compose PostgreSQL
- FastAPI app
- React/Vite app
- SQLAlchemy
- Alembic
- configuration
- logging
- health endpoint

Gate: app starts, DB connects, migrations work.

## Phase 2 — Data
Implement schema and seed all 11 categories/products.
Gate: migrations + seed + unit tests.

## Phase 3 — Commerce
Implement products, inventory, cart, sessions.
Gate: cart and inventory tests.

## Phase 4 — Recovery
Implement inactivity, eligibility, recovery session, interventions, opt-out/rejection, attribution.
Gate: recovery and attribution tests.

## Phase 5 — Agents
Implement OpenAI adapter, LangGraph, Sales Agent, tools, specialist capabilities.
Gate: grounding/behavioral tests.

## Phase 6 — PC Builder
Implement requirements, build versions, deterministic compatibility, budget, inventory, approval, final revalidation, cart commit.
Gate: PC Builder test suite.

## Phase 7 — Payments
Implement order creation, Razorpay Test Checkout, signature verification, webhook idempotency and attribution.
Gate: payment tests.

## Phase 8 — Merchant
Implement JWT login, dashboard, product analytics, daily summary, three configuration fields.
Gate: tenant isolation/dashboard tests.

## Phase 9 — WhatsApp
Research and select easiest currently viable provider. Implement provider-neutral adapter. One notification only.
Gate: notification isolation/failure tests.

## Phase 10 — UX Polish
Responsive customer storefront, chat widget, PC Builder UX, merchant dashboard, error/loading states.

## Phase 11 — Integration
Run both golden E2E flows.

## Phase 12 — Deployment
Research current low-cost platform. Deploy HTTPS backend/frontend/DB as appropriate. Configure Razorpay Test webhook. Do not use ngrok for Razorpay webhook URLs.

## Phase 13 — Final Audit
Run tests, security checks, buildathon demo, README clean-start test.

## Implementation Discipline
- Prefer simple solutions.
- Do not introduce new infrastructure without need.
- Do not change product behavior silently.
- Document consequential implementation decisions as ADRs.
