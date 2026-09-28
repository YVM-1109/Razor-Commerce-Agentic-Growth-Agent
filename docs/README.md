# AI Growth & Agentic Commerce Platform

Razorpay Buildathon project: an AI-powered merchant growth platform focused on abandoned-cart recovery, with a first-class conversational PC Builder.

## Core Demo
1. Customer browses electronics.
2. Adds products to cart.
3. Cart becomes inactive.
4. Recovery Agent appears.
5. Sales Agent assists through real-time chat.
6. Specialist capabilities handle recommendation, inventory, support, or explicit price objections.
7. Customer checks out through Razorpay Test Mode.
8. Verified payment/webhook updates attribution.
9. Merchant sees recovered revenue.

Second demo:
Build Your PC → requirements → compatible build → budget validation → explicit approval → cart → checkout.

## Stack
Python, FastAPI, React/Vite, PostgreSQL, SQLAlchemy, Alembic, LangGraph, OpenAI, JWT, WebSocket, APScheduler, Docker Compose.

## Repository
- `backend/` API, domain services, agents, integrations
- `frontend/` customer + merchant React UI
- `docs/` approved specifications
- `CLAUDE.md` implementation constitution

## Local Setup
The implementation agent must inspect and install missing prerequisites before setup.

Typical sequence:
```bash
docker compose up -d postgres
cd backend
alembic upgrade head
# seed command defined by implementation
# run backend tests
cd ../frontend
npm install
npm run dev
```

Do not assume exact commands until the repository implementation defines them.

## Environment
Copy `.env.example` to `.env`.

Never commit secrets.

Required categories include:
- database
- JWT
- OpenAI
- Razorpay Test Mode
- selected WhatsApp provider

## Payment Webhooks
Razorpay Test Mode is required for MVP. Webhooks need a public HTTPS endpoint. Do not use ngrok as a Razorpay webhook URL; verify current supported tunneling/staging options.

## Safety
The LLM never owns commerce truth. Prices, inventory, discounts, compatibility, intervention limits, payments, and attribution are deterministic application responsibilities.

## Documentation
See:
- PRD.md
- ARCHITECTURE.md
- DATA_MODEL.md
- API_SPEC.md
- UX_SPEC.md
- AGENT_SPEC.md
- TEST_PLAN.md
- IMPLEMENTATION_PLAN.md
