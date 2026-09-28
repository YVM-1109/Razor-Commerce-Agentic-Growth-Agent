# UX & Interaction Specification

## Surfaces
1. Customer storefront
2. Merchant portal

## Customer
Anonymous session. No account/password/name.

Navigation:
Home, Products, Categories, Cart.

Primary actions:
Browse Products, View Product, Add to Cart, Checkout, Build Your PC, Chat with AI Agent.

## Product
Cards show image, name, category, short information, price, availability, and actions.

## Cart
Show products, quantities, prices, subtotal, discount, total, checkout.
Server is authoritative.

## Recovery Widget
Real-time WebSocket chat. One assistant experience; internal specialist routing is hidden.

Intervention #1 should be concise and useful, not technical.

Intervention #2 is agent-decided within deterministic guards. No generic nagging.

Explicit rejection ends active persuasion. Explicit opt-out blocks future unsolicited intervention.

## Pricing
Only after explicit price objection. Product-level. One offer. Never proactive.

## WhatsApp
One-time reminder only when phone exists. No WhatsApp conversation. Does not count as agent interaction or extend attribution.

## PC Builder
Dedicated Build Your PC entry and Sales Agent handoff.
Conversational requirement gathering.
Hard budget.
Core: CPU/GPU/Motherboard/RAM/Storage/PSU/Case.
Optional peripherals: Monitor/Keyboard/Mouse/Headphones.

Build proposal must show total, budget, compatibility, inventory status, and components.

Explicit approval required before cart mutation.
Stale/replaced build requires new approval.
Existing compatible cart components may be reused and must be shown.

If impossible within budget, explain and offer alternatives, including independent store purchase.

## Checkout
Simple order summary and Razorpay Test Checkout.

Payment UI can show processing, but final authoritative state comes from server verification/webhook.

## Merchant
Login → Dashboard → Configuration → Daily Summary.

Dashboard KPIs:
Total Revenue, Revenue at Risk, Abandoned Carts, Recovery-Eligible Carts, Agent Interventions, Recovered Carts, Recovery Rate, Revenue Recovered, Average Recovered Cart Value.

Product table:
Product | Abandoned | Interventions | Recovered | Revenue Recovered.

Configuration exactly:
Maximum Discount, Maximum Interventions, Minimum Cart Value.

## Error/Loading
Use user-friendly states such as:
Checking availability…
Building your PC…
Validating compatibility…
Payment confirmation pending…

Never expose raw infrastructure errors.

## Responsive
Customer UI: desktop/tablet/mobile.
Chat becomes bottom sheet/full-screen on mobile.
Merchant UI is desktop-first but usable on smaller screens.

## Accessibility
Keyboard navigation, visible focus, readable contrast, meaningful labels, non-color-only status communication.
