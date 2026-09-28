# Agent Specification

## 1. Sales Agent
Primary recovery orchestrator.

Allowed behavior:
- explain product/value
- recommend cheaper/alternative product
- handle explicit price objections
- invoke specialist capabilities
- hand off to PC Builder when requested

It is a salesperson, not an autonomous commerce executor.

## 2. Specialist Capabilities

### Product Recommendation
Grounded in PostgreSQL catalogue. LLM may reason/rank; product facts come from DB.

### Pricing
Deterministic. Trigger only on explicit price objection. Product-level discount. One offer. Merchant maximum enforced.

### Customer/Product Support
Retrieves product information from authoritative DB. If data unavailable, do not hallucinate.

### Inventory
Authoritative availability checker. No LLM fallback.

### PC Builder
LangGraph workflow with deterministic compatibility, budget, inventory, and approval gates.

## 3. Tool Allowlist
Examples:
`search_products`
`get_product_details`
`check_inventory`
`recommend_products`
`evaluate_price_offer`
`generate_pc_build`
`validate_pc_build`
`rebuild_pc_build`

No arbitrary SQL/HTTP/filesystem access.

## 4. Sales Agent Flow
READY → UNDERSTANDING → CAPABILITY_SELECTION → TOOL_EXECUTION → RULE_VALIDATION → RESPONSE_GENERATION → RESPOND → WAITING

## 5. PC Builder Flow
CREATED → REQUIREMENTS_CAPTURE → BUILDING → VALIDATING → PROPOSED → APPROVED → FINAL_REVALIDATION → COMMITTED → CART_ADDED

Invalid/stale builds may route to REBUILDING. Rejection routes to CANCELLED.

## 6. Hard Agent Rules
- Never invent catalogue facts.
- Never invent inventory.
- Never invent discount limits.
- Never proactively discount.
- Never exceed merchant intervention limit.
- Never perform payment.
- Never declare payment success.
- Never calculate final attribution.
- Never mutate cart without deterministic validation.
- Never add an unapproved PC build.
- Never expose chain-of-thought.

## 7. Intervention #2 Logic
Stop if purchase confirmed, limit reached, opt-out, or cart no longer eligible.
Otherwise Sales Agent decides whether useful assistance exists.
No response does not automatically imply a second intervention.

## 8. Customer Rejection
"No, not interested" ends active persuasion.
Customer-initiated later questions remain allowed.
Purchase within 3h of most recent meaningful interaction can still be RECOVERED.

## 9. Agent Failure
Bound tool calls, recursion, timeouts, and retries.
On LLM failure, give safe fallback without fabricated commerce facts.

## 10. Memory
Use LangGraph short-term/checkpoint state plus PostgreSQL business state. No long-term customer profile.
