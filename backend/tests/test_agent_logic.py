from app.agent.pc_builder import extract_budget, compatibility_errors
from app.agent.sales_agent import _price_limit, _price_objection


class FakeProduct:
    def __init__(self, **attrs):
        self.pc_attributes = attrs
        self.price = 100
        self.name = "fake"


def test_budget_extraction_prefers_explicit_customer_budget():
    assert extract_budget("Build a gaming PC under ₹1,00,000", 1_000_000) == 100_000
    assert extract_budget("budget 85000", 100_000) == 100_000
    assert extract_budget("Build something", 125_000) == 125_000


def test_sales_price_limit_and_objection_detection():
    assert _price_limit("GPU under ₹50,000") == 50_000
    assert _price_limit("show me something below 45000") == 45_000
    assert _price_objection("This is too expensive, can you give me a discount?")
    assert not _price_objection("Show me a gaming monitor")


def test_pc_compatibility_rules_are_deterministic():
    selected = {
        "CPU": FakeProduct(socket="AM4"),
        "GPU": FakeProduct(recommended_psu_wattage=650),
        "Motherboards": FakeProduct(socket="AM5", form_factor="ATX", memory_type="DDR5"),
        "RAM Sticks": FakeProduct(memory_type="DDR4"),
        "Storage Disks": FakeProduct(),
        "PSUs": FakeProduct(wattage=550),
        "PC Cases": FakeProduct(form_factor="ATX"),
    }
    errors = compatibility_errors(selected)
    assert any("socket" in e.lower() for e in errors)
    assert any("ram" in e.lower() for e in errors)
    assert any("psu" in e.lower() for e in errors)
