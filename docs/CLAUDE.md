# CLAUDE.md — Project Operating Constitution

## 0. Mission
You are implementing the Razorpay Buildathon AI Growth & Agentic Commerce Platform.

The approved specification is authoritative. Your job is to implement it faithfully, not redesign the product while coding.

Primary goal:
Build a working, credible, demo-ready system that recovers abandoned-cart revenue through an AI Sales Agent and provides a first-class conversational PC Builder.

## 1. Authority Hierarchy
When instructions conflict, obey this order:

1. Explicit current user/project decision
2. Approved project specification in `/docs`
3. Architecture invariants
4. Business/security invariants
5. API/data/UX contracts
6. Implementation conventions
7. Your own preference

Never silently override a higher-level decision.

## 2. Anti-Improvisation
Do not invent:
- new product features
- merchant controls
- customer identity/profile fields
- communication channels
- autonomous purchasing
- dynamic pricing
- new agents
- new infrastructure
- hidden business rules
- alternate attribution logic

If a missing decision materially changes product behavior, stop and report the decision needed.

If it is merely an implementation detail, choose the simplest robust solution and document it.

## 3. Required Skills, Plugins, Tools
At session start:
1. Inspect all installed/available skills, plugins, MCP/connectors, and local development tools.
2. Use every relevant working skill/plugin/tool that materially improves the task.
3. Prefer existing project skills/templates/tooling over reinventing workflows.
4. Do not install unnecessary tools.
5. If a required capability is missing, determine whether an available plugin/skill can supply it before creating a manual workaround.
6. Never expose secrets while using external tools.

The principle is:
**use all relevant available capabilities, not every capability indiscriminately.**

## 4. Environment Bootstrap — Mandatory
Never assume prerequisites are installed.

First inspect:
- OS
- Python
- Node.js/npm
- Git
- Docker
- Docker Compose
- PostgreSQL client/tooling

Java/Maven are not required by the approved application architecture unless a specific external dependency proves otherwise.

Then:
1. Install missing required prerequisites where possible.
2. Verify versions.
3. Create/configure `.env`.
4. Initialize backend/frontend.
5. Start PostgreSQL.
6. Run Alembic migrations.
7. Seed catalogue/demo data.
8. Run tests.
9. Only then begin feature implementation.

If automatic installation is impossible, provide the exact missing prerequisite and command needed, then continue only with tasks that do not depend on it.

## 5. Technology Constitution
Locked:
- Python
- FastAPI
- React + Vite
- PostgreSQL
- SQLAlchemy
- Alembic
- LangGraph
- OpenAI API
- JWT merchant authentication
- WebSocket customer agent
- APScheduler
- Docker Compose locally
- Modular monolith

Do not convert this into microservices.

## 6. Agent Constitution
Sales Agent = primary recovery orchestrator.
PC Builder Agent = first-class customer capability.

Specialists:
- Product Recommendation
- Pricing
- Customer/Product Support
- Inventory

Not every specialist must be an autonomous LLM. Prefer deterministic tools/services where appropriate.

## 7. LLM Safety Boundary
LLMs are untrusted with respect to commerce truth.

Never give an LLM:
- DB credentials
- arbitrary SQL
- arbitrary HTTP
- filesystem/infrastructure control
- payment secrets
- merchant secret/config mutation
- unrestricted tool execution

LLM output must be validated before any commerce effect.

## 8. Commerce Invariants
Never violate:
- maximum discount
- minimum cart value
- intervention limit
- one WhatsApp notification
- product-level discount
- one discount offer per recovery session
- no proactive discount
- inventory validation
- compatibility validation
- hard PC budget
- explicit PC build approval
- final build revalidation
- authoritative payment state
- 3-hour attribution rule

## 9. Customer Identity
Anonymous session only.
No customer account/password/name/email profile.
Optional phone is notification-only.
No long-term customer profiling.

## 10. Recovery Rules
Cart activity resets inactivity timing.
Recovery eligibility requires minimum cart value.

Intervention #2:
- never automatic merely because customer ignored #1
- deterministic guards first
- Sales Agent decides whether useful assistance remains

"No, not interested":
- end active persuasion
- customer-initiated interaction remains allowed
- purchase within 3h may still count as recovered

"Don't contact me again":
- block future unsolicited recovery

## 11. Attribution
Recovered:
successful purchase <= 3h after most recent meaningful Sales Agent interaction.

Organic:
no qualifying interaction or purchase after the window.

LLM never calculates final attribution.

## 12. PC Builder
Core:
CPU, GPU, Motherboard, RAM, Storage, PSU, Case.

Optional:
Monitor, Keyboard, Mouse, Headphones.

Hard budget.
No incompatible build.
No silent duplicate of compatible existing cart component.
Replacement/stale version requires new approval.
Explicit approval required before cart mutation.

If no valid configuration:
explain failure and offer independent component purchase through the store.

## 13. Payment
Razorpay Test Mode only for MVP.

Backend creates order.
Frontend opens checkout.
Server verifies client payment signature where applicable.
Webhook is authoritative for asynchronous server state.

Webhook:
- verify raw-body HMAC signature
- use event ID for idempotency
- tolerate duplicate events
- tolerate out-of-order events
- never invoke LLM in webhook handler
- return promptly

Razorpay currently requires publicly reachable webhook URLs and documents `ngrok.io` as blacklisted; use a currently supported public tunnel/staging/deployed HTTPS endpoint instead. Verify current provider documentation during setup.

## 14. OpenAI
Use an adapter/service.
Environment:
`OPENAI_API_KEY`
`OPENAI_MODEL`

Do not hard-code an obsolete model identifier.
At implementation time verify the currently available suitable model through current OpenAI documentation/API and select the simplest cost-effective model that satisfies the agent workflow.

## 15. Database
PostgreSQL is commerce truth.
Use SQLAlchemy + Alembic.
Use exact numeric money.
Use UTC timestamps.
Do not put authoritative business state only in JSON or LangGraph checkpoints.

## 16. Frontend
React/Vite.
Two route/surface groups:
- customer storefront
- merchant portal

Customer agent uses WebSocket.

Never put server secrets in Vite environment variables.

## 17. Scheduler
APScheduler inside FastAPI.
Scheduler evaluates recovery eligibility.
It does not directly generate agent messages or perform commerce mutations.

Business limits must remain correct even if scheduler execution duplicates.

## 18. Observability
Use structured logs with:
timestamp, severity, module, request/correlation ID, session/recovery/order/event ID, error.

Do not log secrets or unnecessary phone data.
Never log chain-of-thought.

Correlate:
React → FastAPI → LangGraph → tools → DB.

## 19. Testing
Required:
- unit
- integration
- API
- agent behavioral/property tests
- E2E

Critical tests:
pricing, intervention limits, attribution boundary, PC Builder compatibility/budget/approval/rebuild, inventory, grounding, webhook signature/idempotency, session isolation, merchant tenant isolation, external failure.

Do not exact-match LLM prose.

## 20. Golden Demo
Golden Recovery:
Store → browse → cart → inactivity → widget → intervention → price objection → pricing → checkout → Razorpay → webhook → recovered attribution → merchant dashboard.

Golden PC Builder:
Build Your PC → requirements → build → compatibility → budget → inventory → proposal → approval → revalidation → cart → checkout.

## 21. Scope Exclusions
Do not add:
Shopify/WooCommerce, email/SMS recovery, conversational WhatsApp, autonomous purchase, dynamic pricing, multilingual personas, campaign automation, vector DB/RAG, Redis, Celery, Kubernetes, microservices, long-term customer profiling.

## 22. Change Control
Before changing approved behavior:
1. identify the affected requirement
2. identify downstream API/data/UX/test effects
3. state the proposed change
4. obtain approval when product behavior changes
5. update relevant docs
6. implement
7. update tests

Never let code become the accidental source of truth.

## 23. Completion Standard
Do not call the project complete until:
- clean environment bootstrap works
- migrations work
- seed works
- tests pass
- customer flow works
- recovery works
- agents work
- PC Builder works
- payment/webhook works
- attribution works
- merchant portal works
- security checks pass
- golden E2E passes
- README works from a clean environment
- deployment/demo is reproducible

## 24. Working Style
Prefer:
- simple
- explicit
- deterministic
- testable
- modular
- demo-reliable

Avoid:
- speculative abstractions
- premature optimization
- unnecessary infrastructure
- hidden behavior
- duplicated business rules

When uncertain, ask:
**“What decision would an implementation agent otherwise have to invent?”**

Resolve that decision before proceeding.
