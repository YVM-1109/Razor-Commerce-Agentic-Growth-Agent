"""PC Builder agent primitives.

The LLM proposes component IDs; PostgreSQL and deterministic validators are the
source of truth for budget, inventory and compatibility.
"""
from __future__ import annotations

import itertools
import json
import re
from typing import Any, TypedDict

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import settings
from app.models import Category, Inventory, Product


ROLES = {
    "CPU": "CPU",
    "GPU": "GPU",
    "Motherboards": "MOTHERBOARD",
    "RAM Sticks": "RAM",
    "Storage Disks": "STORAGE",
    "PSUs": "PSU",
    "PC Cases": "CASE",
}


class BuildSelection(BaseModel):
    cpu_id: str
    gpu_id: str
    motherboard_id: str
    ram_id: str
    storage_id: str
    psu_id: str
    case_id: str


class PcBuilderState(TypedDict, total=False):
    prompt: str
    budget: float
    catalog: dict[str, list[dict[str, Any]]]
    selection: BuildSelection | None
    error: str | None


def extract_budget(prompt: str, supplied_budget: float) -> float:
    patterns = [
        r"(?:under|below|less than|upto|up to|budget(?:\s+of)?|within)\s*[₹$]?\s*([\d,]+(?:\.\d+)?)",
        r"[₹$]\s*([\d,]+(?:\.\d+)?)",
    ]
    for pattern in patterns:
        match = re.search(pattern, prompt or "", flags=re.IGNORECASE)
        if match:
            value = float(match.group(1).replace(",", ""))
            if value > 0:
                return value
    return float(supplied_budget)


def build_catalog(db: Session) -> dict[str, list[Product]]:
    result: dict[str, list[Product]] = {}
    for category_name in ROLES:
        category = db.query(Category).filter(Category.name == category_name, Category.is_active.is_(True)).first()
        result[category_name] = (
            db.query(Product)
            .filter(Product.category_id == category.id, Product.is_active.is_(True))
            .order_by(Product.price.asc())
            .all()
            if category
            else []
        )
    return result


def _stock(db: Session, product: Product) -> int:
    inv = db.query(Inventory).filter(Inventory.product_id == product.id).first()
    return max(0, (inv.quantity - inv.reserved_qty) if inv else 0)


def _wattage(product: Product) -> int:
    attrs = product.pc_attributes or {}
    if attrs.get("wattage"):
        return int(attrs["wattage"])
    match = re.search(r"(\d{3,4})\s*W", product.name, flags=re.I)
    return int(match.group(1)) if match else 0


def compatibility_errors(selected: dict[str, Product]) -> list[str]:
    errors: list[str] = []
    cpu = selected.get("CPU")
    gpu = selected.get("GPU")
    mb = selected.get("Motherboards")
    ram = selected.get("RAM Sticks")
    psu = selected.get("PSUs")
    case = selected.get("PC Cases")
    if not all(selected.get(k) for k in ROLES):
        errors.append("A complete build requires CPU, GPU, motherboard, RAM, storage, PSU and case.")
        return errors
    if (cpu.pc_attributes or {}).get("socket") != (mb.pc_attributes or {}).get("socket"):
        errors.append("CPU socket is incompatible with the motherboard socket.")
    if (ram.pc_attributes or {}).get("memory_type") != (mb.pc_attributes or {}).get("memory_type"):
        errors.append("RAM memory type is incompatible with the motherboard.")
    mb_form = (mb.pc_attributes or {}).get("form_factor")
    case_form = (case.pc_attributes or {}).get("form_factor")
    if mb_form and case_form and mb_form != case_form:
        errors.append("Motherboard form factor is incompatible with the selected case.")
    required_psu = int((gpu.pc_attributes or {}).get("recommended_psu_wattage") or 0)
    if _wattage(psu) < required_psu:
        errors.append("Selected PSU does not meet the GPU's recommended wattage.")
    return errors


def _selection_from_ids(db: Session, ids: BuildSelection) -> dict[str, Product] | None:
    mapping = {
        "CPU": ids.cpu_id,
        "GPU": ids.gpu_id,
        "Motherboards": ids.motherboard_id,
        "RAM Sticks": ids.ram_id,
        "Storage Disks": ids.storage_id,
        "PSUs": ids.psu_id,
        "PC Cases": ids.case_id,
    }
    selected: dict[str, Product] = {}
    for category, product_id in mapping.items():
        p = db.query(Product).filter(Product.id == product_id, Product.is_active.is_(True)).first()
        if not p:
            return None
        selected[category] = p
    return selected


def _deterministic_selection(db: Session, budget: float, catalog: dict[str, list[Product]], gaming: bool = True) -> dict[str, Product] | None:
    pools = {
        key: [p for p in values if _stock(db, p) > 0]
        for key, values in catalog.items()
    }
    keys = list(ROLES)
    best = None
    best_score = None
    # The demo catalogue is intentionally small. Exhaustive search gives us a deterministic safety net.
    for combo in itertools.product(*(pools[k] for k in keys)):
        selected = dict(zip(keys, combo))
        total = sum(float(p.price) for p in combo)
        if total > budget:
            continue
        errors = compatibility_errors(selected)
        if errors:
            continue
        gpu_price = float(selected["GPU"].price)
        cpu_price = float(selected["CPU"].price)
        # Prefer stronger gaming parts while still staying under budget.
        score = (gpu_price * (2 if gaming else 1)) + cpu_price
        tie_break = -total
        candidate = (score, tie_break)
        if best_score is None or candidate > best_score:
            best_score = candidate
            best = selected
    return best


def _llm_selection(prompt: str, budget: float, catalog: dict[str, list[Product]]) -> BuildSelection | None:
    if not settings.OPENAI_API_KEY:
        return None
    try:
        llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            timeout=30,
            max_retries=1,
        )
        structured = llm.with_structured_output(BuildSelection)
        catalog_json = {
            key: [
                {"id": str(p.id), "name": p.name, "price": float(p.price), "pc_attributes": p.pc_attributes or {}}
                for p in products
            ]
            for key, products in catalog.items()
        }
        system = (
            "You are a PC configuration planner. Select exactly one product from every required category. "
            "You MUST use only the supplied product IDs. Stay at or below the hard budget. "
            "Prefer compatible parts: CPU socket = motherboard socket, RAM type = motherboard type, "
            "motherboard form factor = case form factor, PSU wattage >= GPU recommended PSU wattage. "
            "Do not invent IDs or products."
        )
        return structured.invoke([
            HumanMessage(content=system + f"\nHard budget: ₹{budget:,.0f}\nCustomer request: {prompt}\nCatalogue: {json.dumps(catalog_json)}")
        ])
    except Exception:
        return None


def generate_selection(db: Session, prompt: str, budget: float) -> tuple[dict[str, Product] | None, float, list[str]]:
    catalog = build_catalog(db)
    extracted_budget = extract_budget(prompt, budget)
    graph_state = PC_BUILDER_GRAPH.invoke({"prompt": prompt, "budget": extracted_budget, "catalog": catalog})
    selection = graph_state.get("selection")
    selected = _selection_from_ids(db, selection) if selection else None
    if selected:
        errors = compatibility_errors(selected)
        total = sum(float(p.price) for p in selected.values())
        inventory_errors = [f"{p.name} is out of stock." for p in selected.values() if _stock(db, p) < 1]
        errors.extend(inventory_errors)
        if total <= extracted_budget and not errors:
            return selected, total, []
    # Never let a bad model proposal bypass deterministic safety; use a grounded fallback.
    selected = _deterministic_selection(db, extracted_budget, catalog, gaming=True)
    if selected:
        return selected, sum(float(p.price) for p in selected.values()), []
    return None, 0.0, ["No compatible in-stock build fits the requested budget."]


def validate_selection(db: Session, selected: dict[str, Product], budget: float) -> dict[str, Any]:
    compatibility_errors_list = compatibility_errors(selected)
    errors = list(compatibility_errors_list)
    total = sum(float(p.price) for p in selected.values())
    budget_valid = total <= budget
    if not budget_valid:
        errors.append(f"Build total ₹{total:,.0f} exceeds hard budget ₹{budget:,.0f}.")
    inventory = all(_stock(db, p) >= 1 for p in selected.values())
    if not inventory:
        errors.append("One or more selected products are out of stock.")
    return {
        "budget_valid": budget_valid,
        "compatibility_valid": not compatibility_errors_list,
        "inventory_valid": inventory,
        "total": total,
        "errors": errors,
    }


# The LLM proposal is an explicit LangGraph node. Deterministic validation remains outside the model.
def _graph() -> Any:
    def propose(state: PcBuilderState) -> PcBuilderState:
        state["selection"] = _llm_selection(state["prompt"], state["budget"], state["catalog"])
        return state

    workflow = StateGraph(PcBuilderState)
    workflow.add_node("propose", propose)
    workflow.add_edge(START, "propose")
    workflow.add_edge("propose", END)
    return workflow.compile()


PC_BUILDER_GRAPH = _graph()
