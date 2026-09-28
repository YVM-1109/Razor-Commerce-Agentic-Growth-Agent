# Test Plan

## Test Layers
1. Unit
2. Integration
3. API
4. Agent workflow/behavioral
5. E2E

Deterministic commerce services receive highest coverage.

## Critical Unit Tests
- cart eligibility
- minimum cart value
- product-level discount
- maximum discount
- one discount per recovery
- intervention limit
- opt-out
- rejection
- 3-hour attribution boundary
- most-recent-interaction attribution
- inventory availability
- compatibility
- hard budget
- build version approval
- stale build
- existing cart reuse
- merchant configuration validation

## Security Tests
- anonymous session isolation
- merchant JWT enforcement
- merchant tenant isolation
- client price tampering
- client total tampering
- client discount tampering
- client intervention-count tampering
- client payment-state tampering
- LLM prompt injection against business rules
- tool allowlist enforcement

## Payment Tests
- valid webhook signature
- invalid signature
- duplicate event ID
- out-of-order events
- delayed webhook
- failed payment
- client callback without webhook
- webhook without matching order

## Agent Tests
Do not exact-match prose.
Test behavioral properties:
- facts grounded
- discount only after price objection
- no unsupported promises
- specialist use when needed
- respectful termination
- no autonomous payment
- no bypass of deterministic rules

## PC Builder Tests
- compatible build
- CPU/Motherboard incompatibility
- RAM/Motherboard incompatibility
- GPU/PSU incompatibility
- Case/GPU conflict
- over-budget
- out-of-stock replacement
- replacement requires new approval
- existing cart reuse
- no silent duplicate
- explicit approval required

## Golden E2E A
Store → product → cart → inactivity → recovery → agent → price objection → valid offer → checkout → Razorpay Test → verified webhook → recovered attribution → merchant dashboard.

## Golden E2E B
Build Your PC → requirements → build → compatibility → inventory → budget → proposal → approval → revalidation → cart → checkout.

## Reliability
Test OpenAI timeout, malformed output, inventory failure, payment provider failure, WebSocket reconnect, WhatsApp failure, scheduler duplicate execution.

## Completion
All critical tests pass, no secrets committed, golden paths pass from clean environment.
