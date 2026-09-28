from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def test_required_categories_and_demo_controls_are_seeded():
    seed = read("backend/app/seed.py")
    for name in ["Headphones", "Mouse", "Keyboard", "Monitor", "CPU", "GPU", "Storage Disks", "RAM Sticks", "PSUs", "PC Cases", "Motherboards"]:
        assert name in seed
    for field in ["maximum_discount_pct", "maximum_interventions", "minimum_cart_value"]:
        assert field in seed


def test_sales_agent_has_grounding_and_no_global_state():
    source = read("backend/app/agent/sales_agent.py")
    assert "StateGraph" in source
    assert "with_structured_output(SalesDecision)" in source
    assert "Inventory" in source
    assert "Product" in source
    assert "CurrentState" not in source
    assert "product_ids" in source


def test_pc_builder_has_deterministic_validation_and_llm_proposal():
    source = read("backend/app/agent/pc_builder.py")
    router = read("backend/app/routers/pc_builder.py")
    assert "with_structured_output(BuildSelection)" in source
    assert "compatibility_errors" in source
    assert "inventory_valid" in source
    assert "budget_valid" in source
    assert "BUILD_NOT_APPROVED" in router
    assert "BUILD_VERSION_STALE" in router
    assert "BUILD_OUT_OF_STOCK" in router
    assert "customer_approved = True" in router


def test_payment_webhook_is_server_authoritative():
    checkout = read("backend/app/routers/checkout.py")
    frontend = read("frontend/src/App.tsx")
    assert "X-Razorpay-Signature" in checkout
    assert "provider_event_id" in checkout
    assert "payment.captured" in checkout
    assert "DEMO_MODE_DISABLED" in checkout
    assert "payment-status" in frontend
    assert "/checkout/webhook" not in frontend


def test_demo_stack_is_wired_and_secrets_are_ignored():
    compose = read("docker-compose.yml")
    gitignore = read(".gitignore")
    frontend = read("frontend/src/App.tsx")
    assert "postgres:16-alpine" in compose
    assert "5173:80" in compose
    assert "/admin" in frontend
    assert "/builder" in frontend
    assert "demo-capture" in frontend
    assert ".env" in gitignore


def test_session_endpoint_supports_stale_browser_session_recovery():
    sessions = read("backend/app/routers/sessions.py")
    frontend = read("frontend/src/App.tsx")
    assert '@router.get("/{session_id}")' in sessions
    assert "api.get(`/sessions/${stored}`)" in frontend
    assert "localStorage.removeItem('ac_session')" in frontend
