"""LangGraph-backed sales agent with server-authoritative commerce facts.

The LLM is used for intent/recommendation language only. Product identity, price,
stock and discount limits always come from PostgreSQL/application services.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any, TypedDict
from uuid import UUID

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models import (
    AgentConversation,
    AgentEvent,
    AgentMessage,
    Cart,
    CartItem,
    Inventory,
    MerchantConfig,
    Product,
    RecoverySession,
)
from app.services.commerce import recalc_cart


class SalesDecision(BaseModel):
    intent: str = Field(description="shopping, product_support, price_objection, pc_builder, or other")
    product_ids: list[str] = Field(default_factory=list)
    handoff_to_pc_builder: bool = False
    response: str = Field(description="A concise customer-facing response using only the supplied catalogue facts")


class SalesState(TypedDict, total=False):
    session_id: str
    cart_id: str | None
    user_message: str
    history: list[dict[str, str]]
    catalogue: list[dict[str, Any]]
    decision: SalesDecision
    response: str
    suggestions: list[dict[str, Any]]
    discount_offered: float | None
    handoff: bool
    error: str | None


def _catalogue(db: Session) -> list[dict[str, Any]]:
    rows = db.query(Product).filter(Product.is_active.is_(True)).order_by(Product.name).all()
    result: list[dict[str, Any]] = []
    for p in rows:
        inv = db.query(Inventory).filter(Inventory.product_id == p.id).first()
        available = (inv.quantity - inv.reserved_qty) if inv else 0
        result.append(
            {
                "id": str(p.id),
                "name": p.name,
                "brand": p.brand,
                "category": getattr(p.category, "name", None) if hasattr(p, "category") else None,
                "price": float(p.price),
                "available": max(0, available),
                "description": p.description,
            }
        )
    return result


def _price_limit(text: str) -> float | None:
    # Handles ₹100000, ₹1,00,000, 100000, and 1,00,000.
    patterns = [
        r"(?:under|below|less than|upto|up to|budget(?:\s+of)?|within)\s*[₹$]?\s*([\d,]+(?:\.\d+)?)",
        r"[₹$]\s*([\d,]+(?:\.\d+)?)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            try:
                return float(match.group(1).replace(",", ""))
            except ValueError:
                pass
    return None


def _price_objection(text: str) -> bool:
    return bool(
        re.search(
            r"\b(too expensive|too costly|too much|price is high|expensive|discount|cheaper|lower the price|better price)\b",
            text,
            flags=re.IGNORECASE,
        )
    )


def _deterministic_search(catalogue: list[dict[str, Any]], text: str, max_price: float | None) -> list[dict[str, Any]]:
    terms = [t for t in re.findall(r"[a-z0-9]+", text.lower()) if len(t) > 2]
    rows = [p for p in catalogue if p["available"] > 0 and (max_price is None or p["price"] <= max_price)]
    if not terms:
        return rows[:5]
    scored = []
    for p in rows:
        hay = f'{p["name"]} {p["brand"]} {p["category"] or ""} {p["description"]}'.lower()
        score = sum(1 for term in terms if term in hay)
        if score:
            scored.append((score, p))
    scored.sort(key=lambda item: (-item[0], item[1]["price"]))
    return [p for _, p in scored[:5]]


def _fallback_decision(state: SalesState) -> SalesDecision:
    text = state["user_message"]
    if re.search(r"\b(build|configure|custom).*(pc|computer)|\bpc\b.*\b(build|configure)\b", text, re.I):
        return SalesDecision(
            intent="pc_builder",
            handoff_to_pc_builder=True,
            response="Absolutely. I can hand you to the PC Builder so it can work from your budget and requirements.",
        )
    limit = _price_limit(text)
    suggestions = _deterministic_search(state["catalogue"], text, limit)
    if suggestions:
        names = ", ".join(p["name"] for p in suggestions[:3])
        return SalesDecision(
            intent="shopping",
            product_ids=[p["id"] for p in suggestions],
            response=f"I found these catalogue options: {names}.",
        )
    return SalesDecision(
        intent="other",
        response="Tell me the product, category, budget, or PC requirements you have in mind and I’ll search the live catalogue.",
    )


def _llm_node(state: SalesState) -> SalesState:
    if not settings.OPENAI_API_KEY:
        state["decision"] = _fallback_decision(state)
        return state

    try:
        llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            timeout=30,
            max_retries=1,
        )
        structured = llm.with_structured_output(SalesDecision)
        prompt = (
            "You are the RazorCommerce shopping assistant. You are NOT allowed to invent catalogue facts. "
            "Choose products only from the supplied catalogue. Detect explicit PC-building requests and set "
            "handoff_to_pc_builder=true. Detect explicit price objections. Keep the response concise. "
            "The backend will independently validate every product ID, price and stock value.\n\n"
            f"Conversation history: {json.dumps(state.get('history', [])[-6:])}\n"
            f"Customer message: {state['user_message']}\n\n"
            f"Live catalogue: {json.dumps(state['catalogue'])}"
        )
        state["decision"] = structured.invoke([HumanMessage(content=prompt)])
    except Exception as exc:
        state["error"] = f"LLM failure: {type(exc).__name__}"
        state["decision"] = _fallback_decision(state)
    return state


def _graph() -> Any:
    workflow = StateGraph(SalesState)
    workflow.add_node("decide", _llm_node)
    workflow.add_edge(START, "decide")
    workflow.add_edge("decide", END)
    return workflow.compile()


SALES_GRAPH = _graph()


def _apply_discount(db: Session, cart_id: str | None) -> float | None:
    if not cart_id:
        return None
    cart = db.query(Cart).filter(Cart.id == cart_id, Cart.status == "ACTIVE").first()
    if not cart:
        return None
    cfg = db.query(MerchantConfig).first()
    max_pct = float(cfg.maximum_discount_pct if cfg else 0)
    if max_pct <= 0 or float(cart.discount_total or 0) > 0:
        return None
    item = db.query(CartItem).filter(CartItem.cart_id == cart.id).order_by(CartItem.created_at.asc()).first()
    if not item:
        return None
    product = db.query(Product).filter(Product.id == item.product_id, Product.is_active.is_(True)).first()
    if not product:
        return None
    original = float(product.price)
    discounted = round(original * (1 - max_pct / 100), 2)
    item.unit_price = discounted
    cart.discount_total = round(max(0.0, (original - discounted) * item.quantity), 2)
    recalc_cart(db, cart)
    return round(original - discounted, 2)


def handle_message(session_id: str, cart_id: str | None, message: str) -> dict[str, Any]:
    db = SessionLocal()
    try:
        session_uuid = UUID(session_id)
        rs = None
        if cart_id:
            rs = (
                db.query(RecoverySession)
                .filter(
                    RecoverySession.cart_id == cart_id,
                    RecoverySession.status.in_(["ACTIVE", "REJECTED"]),
                )
                .order_by(RecoverySession.created_at.desc())
                .first()
            )
            if rs and not rs.customer_opted_out:
                rs.last_meaningful_agent_interaction_at = datetime.now(timezone.utc)
                if rs.status == "ACTIVE":
                    rs.intervention_count += 1

        conv = (
            db.query(AgentConversation)
            .filter(AgentConversation.customer_session_id == session_uuid, AgentConversation.status == "ACTIVE")
            .order_by(AgentConversation.created_at.desc())
            .first()
        )
        if not conv:
            conv = AgentConversation(
                customer_session_id=session_uuid,
                recovery_session_id=rs.id if rs else None,
                agent_type="SALES",
                status="ACTIVE",
            )
            db.add(conv)
            db.flush()
        db.add(AgentMessage(conversation_id=conv.id, sender_type="USER", content=message))
        db.commit()
        history = (
            db.query(AgentMessage)
            .filter(AgentMessage.conversation_id == conv.id)
            .order_by(AgentMessage.created_at.asc())
            .all()
        )

        catalogue = _catalogue(db)
        state: SalesState = {
            "session_id": session_id,
            "cart_id": cart_id,
            "user_message": message,
            "catalogue": catalogue,
            "history": [
                {"role": "user" if m.sender_type == "USER" else "assistant", "content": m.content}
                for m in history[-6:]
            ],
            "suggestions": [],
            "discount_offered": None,
            "handoff": False,
            "error": None,
        }
        state = SALES_GRAPH.invoke(state)
        decision = state["decision"]

        valid_by_id = {p["id"]: p for p in catalogue}
        max_price = _price_limit(message)
        suggestions: list[dict[str, Any]] = []
        for product_id in decision.product_ids:
            p = valid_by_id.get(str(product_id))
            if not p or p["available"] <= 0:
                continue
            if max_price is not None and p["price"] > max_price:
                continue
            suggestions.append(p)
        if not suggestions and decision.intent in {"shopping", "product_support"}:
            suggestions = _deterministic_search(catalogue, message, max_price)

        discount = None
        response = decision.response
        if _price_objection(message):
            discount = _apply_discount(db, cart_id)
            if discount is not None:
                response += f" I can apply the merchant-approved discount to the current cart item; that saves ₹{discount:,.0f}."
            elif cart_id:
                response += " I can only offer the merchant-approved price adjustment once on an eligible active cart."

        handoff = bool(decision.handoff_to_pc_builder)
        if handoff:
            response += " Open the PC Builder to enter your exact budget and requirements; nothing will be added until you explicitly approve a validated build."

        db.add(
            AgentMessage(
                conversation_id=conv.id,
                sender_type="ASSISTANT",
                content=response,
                metadata_={"handoff": handoff, "product_ids": [p["id"] for p in suggestions]},
            )
        )
        db.add(
            AgentEvent(
                agent_type="SALES",
                event_type="MESSAGE_PROCESSED",
                tool_name="langgraph_sales_agent",
                success=state.get("error") is None,
                metadata_={"session_id": session_id, "llm_fallback": state.get("error") is not None},
            )
        )
        db.commit()

        return {
            "response": response,
            "handoff_to_pc_builder": handoff,
            "product_suggestions": suggestions,
            "discount_offered": discount,
            "recovery_session_id": str(rs.id) if rs else None,
        }
    finally:
        db.close()
