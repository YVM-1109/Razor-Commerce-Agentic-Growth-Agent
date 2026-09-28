# Final Validation Notes

## Changes applied

- Reworked the Sales Agent around a small LangGraph state graph and structured OpenAI decision model.
- Removed process-global sales-agent state so concurrent sessions do not overwrite one another.
- Grounded every recommendation against PostgreSQL product/inventory facts.
- Added explicit product Add actions in the Sales Agent UI instead of autonomous cart mutation.
- Added an explicit Sales Agent → PC Builder UI handoff.
- Made customer-specified PC budget authoritative by parsing explicit budget language on the server.
- Reworked PC Builder selection so the LLM only proposes catalogue IDs; deterministic validation remains authoritative.
- Added deterministic CPU/motherboard socket, RAM/motherboard memory, motherboard/case form-factor, PSU/GPU wattage, inventory and budget checks.
- Added deterministic fallback PC selection when the model is unavailable or proposes an invalid build.
- Revalidated the exact build version before approval and again immediately before cart commit.
- Protected the demo-capture endpoint behind `DEMO_MODE`.
- Removed the browser-generated fake Razorpay webhook path; live checkout now waits for server webhook confirmation.
- Added a payment-status endpoint for live checkout polling.
- Added Docker ignore files and removed dependency on local `node_modules` in the final source package.
- Added lower-cost compatible demo hardware so a ₹100,000 gaming build can be produced from the seeded catalogue.

## Local validation performed in this environment

- Python bytecode compilation: PASS.
- Python AST parsing: PASS.
- Frontend TypeScript project build/type-check stage: PASS.
- Full frontend Vite bundle could not be completed in this Linux review environment because the uploaded Windows `node_modules` did not contain the Linux Rolldown native binding. The final repository intentionally excludes `node_modules`; `npm ci`/Docker build on the target machine should install platform-correct dependencies.
- Full backend runtime/OpenAI/PostgreSQL integration could not be executed in this review environment because external package installation/network access was unavailable. Docker Compose is the authoritative local runtime validation path.

## Final runtime gate

Before publishing the repository, run:

```bash
docker compose down -v --remove-orphans
docker compose up --build
```

Then verify `/health`, the storefront, AI Sales Agent, PC Builder, cart commit, demo checkout and merchant dashboard locally.
