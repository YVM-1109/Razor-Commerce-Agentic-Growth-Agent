# RazorCommerce

### AI-Powered Agentic Commerce — Concept Prototype

RazorCommerce is a functional concept prototype exploring what an e-commerce platform could look like when **AI agents become an active part of the customer journey**, rather than simply sitting alongside a traditional storefront as a chatbot.

The idea is fairly simple:

A customer shouldn't always have to know exactly what product they want, browse through dozens of listings, compare specifications, build a configuration manually, and figure everything out themselves.

Instead, they should be able to **talk to the store**.

RazorCommerce experiments with that idea through a combination of an AI Sales Agent, a dedicated PC Builder Agent, a conventional e-commerce storefront, and a merchant dashboard.

The project is primarily intended to demonstrate the **concept and technical architecture of agentic commerce**. It is a prototype rather than a production-ready commercial platform.

---

## What is RazorCommerce?

Traditional e-commerce generally follows a predictable flow:

```text
Customer
   ↓
Browse Products
   ↓
Select Product
   ↓
Add to Cart
   ↓
Checkout
   ↓
Purchase
```

RazorCommerce adds an agentic layer to that journey:

```text
                         ┌──────────────────┐
                         │   AI Sales Agent │
                         └────────┬─────────┘
                                  │
                                  │
Customer → Storefront ────────────┼──────────→ Cart → Checkout
                                  │
                                  │
                                  ▼
                         ┌──────────────────┐
                         │   PC Builder     │
                         │      Agent       │
                         └──────────────────┘
```

The customer can interact with the store conversationally, receive product recommendations, ask questions, raise objections, or request a completely custom PC configuration.

The important architectural principle is that **the LLM does not get unrestricted control over commerce operations**.

AI handles reasoning and conversation.

The backend handles the operations that actually change commerce state.

---

# Core Features

## 1. AI Sales Agent

The Sales Agent acts as a conversational shopping assistant.

Instead of forcing a customer to navigate the catalogue manually, the customer can describe what they are looking for in natural language.

For example:

> "I need a graphics card for gaming under ₹50,000."

The agent can interpret the request, work with the available catalogue, and provide relevant recommendations.

It can also handle common purchasing conversations such as:

* Product discovery
* Product recommendations
* Budget requirements
* Product comparisons
* Customer questions
* Purchase hesitation
* Price objections
* Cart recovery interactions
* Requests to build a custom PC

The Sales Agent is designed to operate within deterministic backend rules rather than being allowed to directly manipulate the database.

---

# 2. PC Builder Agent

One of the main ideas behind RazorCommerce is that some purchases are too complicated for a conventional product page.

A customer looking for a gaming PC might say:

> "I want a gaming PC under ₹1,00,000 for 1440p gaming."

Instead of making the customer manually select every component, the PC Builder Agent can work through the requirements conversationally and produce a complete configuration.

The builder considers things such as:

* Budget
* CPU
* GPU
* Motherboard
* RAM
* Storage
* PSU
* Case
* Component compatibility
* Product availability

The generated configuration is then validated by deterministic backend logic.

The AI can **propose** a build.

The backend decides whether that build is actually valid.

---

# 3. Agent-to-Agent Handoff

The Sales Agent and PC Builder are not completely isolated experiences.

If a customer is talking to the Sales Agent and says something like:

> "I want to build a PC."

the Sales Agent can hand the customer over to the dedicated PC Builder experience.

The storefront also provides a direct **Build Your PC** entry point for customers who already know what they want.

This creates two paths:

```text
Customer
   │
   ├── "I want a GPU"
   │        ↓
   │    Sales Agent
   │
   └── "I want to build a PC"
            ↓
        PC Builder Agent
```

---

# 4. Conventional E-Commerce Storefront

RazorCommerce still behaves like a normal online store.

The AI layer does not replace the traditional shopping experience.

Customers can:

* Browse products
* View product information
* Add products to their cart
* Review their cart
* Proceed toward checkout

This is intentional.

The project explores **agentic commerce as an additional layer over conventional e-commerce**, rather than assuming that every customer wants to interact with an AI agent.

---

# 5. Merchant Dashboard

The merchant side provides visibility into the activity taking place across the platform.

The prototype includes statistics related to areas such as:

* Sales
* Cart activity
* Agent interactions
* Recovery activity
* Customer conversions
* Revenue-related metrics

The idea is to eventually give merchants a clearer picture of whether their AI agents are actually contributing to business growth.

---

# 6. Recovery-Oriented Agent Interactions

RazorCommerce also explores the idea of an AI agent intervening when a customer appears likely to abandon a purchase.

The prototype uses merchant-configurable controls around recovery behavior, including:

* Maximum discount
* Maximum interventions
* Minimum cart value

The intention is not to have the AI endlessly message customers.

Instead, intervention is bounded by explicit merchant-defined rules.

A simplified recovery flow looks like:

```text
Customer adds products
        ↓
Potential abandonment
        ↓
Sales Agent intervention
        ↓
Customer responds?
    ┌───────┴───────┐
   Yes              No
    ↓                ↓
Continue        Agent evaluates
conversation    whether another
                intervention is
                appropriate
```

---

# Recovery vs Organic Sales

One of the concepts explored by the prototype is distinguishing between purchases influenced by the agent and purchases that would likely have happened naturally.

A **Recovered Sale** is associated with an agent interaction that occurred within the defined recovery attribution window.

An **Organic Sale** represents a purchase that occurs without qualifying agent influence.

The prototype uses the most recent meaningful Sales Agent interaction when determining the attribution window.

This allows the merchant dashboard to eventually answer a more useful question than simply:

> "How many sales happened?"

It can instead ask:

> "How many sales happened after the agent became involved?"

---

# Discount Philosophy

RazorCommerce intentionally avoids allowing the AI to randomly discount products.

Discounts are governed by deterministic business rules.

The prototype follows the principle:

> **Never proactively discount unless the customer explicitly raises price as an objection.**

When a price objection is explicitly raised, the agent can consider an eligible discount within the merchant-configured limits.

There is also a limit of **one discount offer per product/cart recovery session**.

This keeps the AI from turning every conversation into an uncontrolled negotiation.

---

# Architecture

RazorCommerce is structured as a **modular monolith**.

The high-level architecture is:

```text
┌───────────────────────────────────────────────┐
│                  React / Vite                 │
│                                               │
│ Storefront │ Sales Agent │ PC Builder │ Admin │
└───────────────────────┬───────────────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────┐
│                  FastAPI                      │
│                                               │
│ API Routes                                    │
│ ├── Catalogue                                 │
│ ├── Cart                                      │
│ ├── Checkout                                  │
│ ├── Sales Agent                               │
│ ├── PC Builder                                │
│ └── Merchant Dashboard                        │
│                                               │
│ Deterministic Commerce Services               │
└───────────────┬───────────────────┬───────────┘
                │                   │
                ▼                   ▼
        ┌──────────────┐     ┌──────────────┐
        │ PostgreSQL   │     │ LangGraph    │
        │              │     │ Agent Layer  │
        └──────────────┘     └──────┬───────┘
                                    │
                                    ▼
                              ┌───────────┐
                              │  OpenAI   │
                              └───────────┘

Additional integrations:
        │
        ├── Razorpay
        ├── WhatsApp adapter
        └── APScheduler
```

The application deliberately avoids splitting the MVP into multiple microservices.

For a prototype, keeping the system together makes the architecture easier to develop, understand, test, and demonstrate.

---

# AI vs Deterministic Logic

This is one of the most important design decisions in the project.

The AI agent is responsible for things like:

* Understanding natural language
* Interpreting customer intent
* Generating conversational responses
* Suggesting products
* Proposing PC configurations
* Deciding when a conversational handoff is appropriate

The backend remains responsible for things like:

* Inventory
* Cart mutations
* Product prices
* Discount limits
* Compatibility validation
* Merchant configuration
* Build validation
* Payment state
* Attribution

In other words:

```text
AI proposes / reasons
        ↓
Backend validates
        ↓
Backend performs mutation
```

This separation is intentional.

An LLM should not be able to simply decide that a product exists, change its price, bypass inventory, or declare a PC build compatible.

---

# Technology Stack

### Frontend

* React
* Vite
* TypeScript
* Modern CSS

### Backend

* Python
* FastAPI
* SQLAlchemy
* Alembic
* PostgreSQL

### AI

* OpenAI API
* LangGraph
* Structured agent workflows

### Infrastructure

* Docker
* Docker Compose
* PostgreSQL

### Payments

* Razorpay architecture / Test Mode integration

### Scheduling

* APScheduler

---

# Database

PostgreSQL acts as the application's primary source of persistent state.

The data model covers concepts including:

* Merchants
* Merchant configuration
* Product categories
* Products
* Inventory
* Product compatibility
* Customer sessions
* Carts
* Cart items
* Recovery sessions
* Agent conversations
* Agent messages
* Agent events
* PC Builder sessions
* PC build versions
* PC build components
* Orders
* Payments
* Payment webhook events
* Sales attribution

Money values are represented using decimal database types rather than floating-point values, and timestamps are stored consistently in UTC.

---

# Anonymous Customer Sessions

The prototype does not require customers to create an account before interacting with the store.

Instead, customers can be represented through anonymous sessions.

This keeps the shopping experience lightweight and also makes the prototype suitable for demonstrating an agentic storefront without requiring a full customer identity system.

Long-term customer profiling is intentionally outside the scope of this prototype.

---

# Payment Architecture

RazorCommerce is structured around the idea that payment state should ultimately be determined by the payment provider rather than by the browser.

The intended flow is:

```text
Customer
   ↓
Checkout
   ↓
Razorpay
   ↓
Payment
   ↓
Razorpay Webhook
   ↓
Backend verification
   ↓
Order / Payment state
```

The repository should therefore be viewed as demonstrating the **integration architecture and prototype flow**, rather than as a production payment implementation.

For production deployment, webhook configuration, signature verification, secrets management, failure handling, reconciliation, and operational monitoring would all need to be fully configured and tested against a live Razorpay environment.

---

# Running the Project Locally

## Requirements

You will need:

* Docker
* Docker Compose
* Node.js
* Python
* An OpenAI API key

Clone the repository:

```bash
git clone <repository-url>
cd RazorCommerce
```

Create your environment file:

```bash
cp .env.example .env
```

Add the required configuration, including your OpenAI API key and selected model.

Then start the application:

```bash
docker compose up --build
```

Once the containers are running, open the frontend at:

```text
http://localhost:5173
```

The FastAPI backend runs separately inside the Docker network.

---

# Project Structure

A simplified view of the repository:

```text
RazorCommerce/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── agents/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── ...
│   │
│   ├── alembic/
│   ├── requirements.txt
│   └── ...
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── ...
│   └── ...
│
├── docs/
│   ├── PRD.md
│   ├── ARCHITECTURE.md
│   ├── DATA_MODEL.md
│   └── IMPLEMENTATION_PLAN.md
│
├── docker-compose.yml
├── .env.example
└── README.md
```

The `docs/` directory contains the project's original product, architecture, data-model, and implementation specifications.

---

# What This Prototype Demonstrates

The main objective of RazorCommerce is not simply to build another online store.

It is to demonstrate a different interaction model:

### Traditional

> Customer searches → Customer compares → Customer decides → Customer purchases

### Agentic

> Customer describes intent → Agent understands → Agent assists → Backend validates → Customer approves → Purchase

The PC Builder demonstrates this particularly well.

A customer does not need to know which motherboard works with which processor or whether a particular PSU is sufficient.

They can describe the outcome they want.

The agent handles the conversational reasoning while the deterministic backend protects the actual commerce rules.

---

# Current Prototype Scope

### Working / Demonstrated

* E-commerce storefront
* Product catalogue
* Shopping cart
* AI Sales Agent
* Custom PC Builder Agent
* Conversational PC configuration
* Product/component recommendations
* Compatibility validation
* Inventory-aware build validation
* Agent handoff between Sales Agent and PC Builder
* Merchant dashboard
* Docker-based local development
* PostgreSQL persistence
* OpenAI integration

### Prototype / Integration Scope

Some areas remain intentionally at the **concept/prototype level**, including:

* Production Razorpay webhook deployment
* WhatsApp production integration
* Production hosting
* Production authentication and authorization hardening
* Observability and monitoring
* High-scale infrastructure
* Security hardening
* Automated production test suites
* Production-grade payment reconciliation

These would be addressed as part of a future production implementation.

---

# Why This Project Exists

The interesting question behind RazorCommerce is not:

> "Can we put an AI chatbot on an online store?"

That's already fairly straightforward.

The more interesting question is:

> **"What happens when the AI becomes part of the actual purchasing workflow?"**

Can an agent understand what a customer is trying to buy?

Can it recommend products based on real catalogue data?

Can it recover a hesitant customer without aggressively discounting everything?

Can one agent hand a customer over to another specialized agent?

Can an AI build something as complicated as a complete PC while deterministic software still controls the actual commerce rules?

RazorCommerce is an attempt to explore those questions through a working prototype.

---

# Prototype Disclaimer

RazorCommerce is a **concept prototype built for experimentation, demonstration, and evaluation of agentic-commerce ideas**.

It should not be treated as a production-ready e-commerce or payment platform.

Before deploying a system based on this project commercially, additional work would be required around security, authentication, payment infrastructure, webhook configuration, privacy, compliance, observability, scalability, testing, deployment, and operational reliability.

---

# Author

**Yashovardhan Mishra**

B.Tech — Computer Science & Engineering 

This project was developed as an exploration of **AI agents, agentic commerce, full-stack engineering, and AI-assisted customer experiences**.

---

