# PRD — AI Growth & Agentic Commerce Platform

## 1. Product Definition
An AI-powered merchant growth system whose flagship capability detects potentially abandoned shopping carts and uses an AI Sales Agent to intelligently attempt to recover the lost sale.

A second first-class customer capability is a conversational PC Builder that creates compatible PC configurations within a hard customer budget and, only after explicit approval, adds the build to the cart.

## 2. Goals
- Recover abandoned-cart revenue through contextual, real-time website conversations.
- Give merchants measurable recovery outcomes.
- Ground AI behavior in authoritative catalogue, inventory, pricing, payment, and configuration data.
- Demonstrate agentic commerce without unnecessary enterprise infrastructure.
- Provide a compelling Razorpay Buildathon demo.

## 3. Users
### Customer
Anonymous session. No account, name, or long-term customer profile. Optional phone number exists only for one one-time WhatsApp notification.

### Merchant
Authenticated merchant who views analytics and controls exactly:
1. Maximum Discount
2. Maximum Interventions
3. Minimum Cart Value

## 4. Catalogue
Electronics/PC building catalogue with exactly these categories:
- Headphones
- Mouse
- Keyboard
- Monitor
- CPU
- GPU
- Storage Disks
- RAM Sticks
- PSUs
- PC Cases
- Motherboards

## 5. Recovery Behavior
Cart inactivity starts/resets after meaningful activity. Eligibility requires cart value >= merchant minimum.

Sales Agent may:
- explain product/value
- recommend cheaper/alternative products
- respond to explicit price objections

Specialist capabilities:
- Product Recommendation
- Pricing
- Customer/Product Support
- Inventory

Maximum unsolicited interventions are merchant-configured. Intervention #2 is agent-decided within deterministic guards. Explicit rejection ends active persuasion. Explicit opt-out blocks future unsolicited recovery.

WhatsApp is one-time notification only; it is not a conversational recovery channel.

## 6. Pricing
Pricing is product-level, not cart-level.
One discount offer per recovery session.
Discount occurs only after explicit price objection.
Maximum discount cannot exceed merchant configuration.
Never proactively discount.

## 7. Attribution
Recovered Sale:
- eligible recovery cart
- meaningful Sales Agent interaction
- successful purchase within 3 hours of the most recent meaningful agent interaction.

Organic Sale:
- no qualifying agent interaction, or
- purchase after the 3-hour window.

Rejection does not erase attribution.

## 8. PC Builder
Direct "Build Your PC" entry and Sales Agent handoff.

Core components:
CPU, GPU, Motherboard, RAM, Storage, PSU, Case.

Optional:
Monitor, Keyboard, Mouse, Headphones.

Hard constraints:
- never exceed stated budget
- never commit incompatible build
- inventory must be validated
- explicit approval required
- stale/replaced build requires new approval
- compatible existing cart components may be reused without silent duplication

If no valid build exists, explain why and offer alternatives, including buying components independently through the store.

## 9. Checkout
Razorpay Test Mode. Server-created payment order. Verified payment/webhook state is authoritative. Webhook processing is idempotent.

## 10. Merchant Dashboard
Overview:
- Total Revenue
- Revenue at Risk
- Abandoned Carts
- Recovery-Eligible Carts
- Agent Interventions
- Recovered Carts
- Recovery Rate
- Revenue Recovered
- Average Recovered Cart Value

Product table:
Product | Abandoned | Interventions | Recovered | Revenue Recovered

Daily summary is business-focused, not hidden reasoning.

## 11. MVP Exclusions
No Shopify/WooCommerce integrations, multiple channels, conversational WhatsApp, dynamic pricing, autonomous purchasing, multilingual personas, campaign automation, vector DB/RAG, Redis/Celery/Kubernetes, microservices, or long-term customer profiling.

## 12. Success Criteria
A clean golden demo must complete:
Store → Cart → Abandon → Agent → Product/Price assistance → Razorpay Test Payment → Verified webhook → Recovered attribution → Merchant dashboard.

A second golden demo must complete:
Build Your PC → Requirements → Compatible build → Budget validation → Explicit approval → Cart → Checkout.
