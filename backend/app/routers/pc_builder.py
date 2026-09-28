from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Cart, CartItem, CustomerSession, Inventory, PcBuildComponent, PcBuildVersion, PcBuilderSession, Product
from app.schemas import ApproveBuild, BuilderRequirements
from app.services.commerce import recalc_cart
from app.agent.pc_builder import extract_budget, generate_selection, validate_selection

router = APIRouter(prefix="/pc-builder", tags=["pc-builder"])


def serialize(db: Session, session: PcBuilderSession, version: PcBuildVersion | None = None):
    if version is None and session.current_build_version:
        version = (
            db.query(PcBuildVersion)
            .filter(
                PcBuildVersion.pc_builder_session_id == session.id,
                PcBuildVersion.version_number == session.current_build_version,
            )
            .first()
        )
    components = []
    if version:
        for c in db.query(PcBuildComponent).filter(PcBuildComponent.build_version_id == version.id).all():
            product = db.query(Product).filter(Product.id == c.product_id).first()
            inv = db.query(Inventory).filter(Inventory.product_id == c.product_id).first()
            components.append(
                {
                    "id": str(c.product_id),
                    "role": c.component_role,
                    "name": product.name,
                    "price": float(c.unit_price),
                    "available": max(0, (inv.quantity - inv.reserved_qty) if inv else 0),
                    "reused": bool(c.is_reused_from_cart),
                }
            )
    return {
        "id": str(session.id),
        "status": session.status,
        "budget": float(session.budget_max or 0),
        "requirements": session.requirements or {},
        "version": version.version_number if version else None,
        "total": float(version.total_price or 0) if version else 0,
        "validation": {
            "budget": bool(version.budget_valid) if version else False,
            "inventory": bool(version.inventory_valid) if version else False,
            "compatibility": bool(version.compatibility_valid) if version else False,
        },
        "approved": bool(version.customer_approved) if version else False,
        "components": components,
    }


@router.post("/sessions")
def create_session(session_id: str, db: Session = Depends(get_db)):
    if not db.query(CustomerSession).filter(CustomerSession.id == session_id).first():
        raise HTTPException(404, "SESSION_NOT_FOUND")
    session = PcBuilderSession(customer_session_id=session_id, status="CREATED", requirements={})
    db.add(session)
    db.commit()
    db.refresh(session)
    return serialize(db, session)


@router.post("/sessions/{builder_id}/requirements")
def requirements(builder_id: str, payload: BuilderRequirements, db: Session = Depends(get_db)):
    session = db.query(PcBuilderSession).filter(PcBuilderSession.id == builder_id).first()
    if not session:
        raise HTTPException(404, "BUILD_NOT_FOUND")
    authoritative_budget = extract_budget(payload.prompt or "", payload.budget)
    if authoritative_budget <= 0:
        raise HTTPException(400, "BUILD_INVALID")
    session.budget_max = authoritative_budget
    session.requirements = payload.model_dump() | {"budget": authoritative_budget}
    session.status = "REQUIREMENTS_CAPTURE"
    db.commit()
    return serialize(db, session)


@router.post("/sessions/{builder_id}/generate")
def generate(builder_id: str, db: Session = Depends(get_db)):
    session = db.query(PcBuilderSession).filter(PcBuilderSession.id == builder_id).first()
    if not session or not session.budget_max:
        raise HTTPException(400, "BUILD_INVALID")
    prompt = (session.requirements or {}).get("prompt") or "Build me a gaming PC"
    budget = float(session.budget_max)

    selected, total, errors = generate_selection(db, prompt, budget)
    version_number = (session.current_build_version or 0) + 1
    version = PcBuildVersion(
        pc_builder_session_id=session.id,
        version_number=version_number,
        status="PROPOSED" if selected else "INVALID",
        budget_max=session.budget_max,
        total_price=total,
        customer_approved=False,
    )
    db.add(version)
    db.flush()

    if selected:
        validation = validate_selection(db, selected, budget)
        version.total_price = validation["total"]
        version.budget_valid = validation["budget_valid"]
        version.inventory_valid = validation["inventory_valid"]
        version.compatibility_valid = validation["compatibility_valid"]
        for category, product in selected.items():
            role_map = {
                "CPU": "CPU",
                "GPU": "GPU",
                "Motherboards": "MOTHERBOARD",
                "RAM Sticks": "RAM",
                "Storage Disks": "STORAGE",
                "PSUs": "PSU",
                "PC Cases": "CASE",
            }
            db.add(
                PcBuildComponent(
                    build_version_id=version.id,
                    product_id=product.id,
                    component_role=role_map[category],
                    quantity=1,
                    unit_price=product.price,
                )
            )
        errors = validation["errors"]
        if errors:
            version.status = "INVALID"
            session.status = "NO_VALID_BUILD"
        else:
            session.current_build_version = version_number
            session.status = "PROPOSED"
    else:
        version.status = "INVALID"
        version.budget_valid = False
        version.inventory_valid = False
        version.compatibility_valid = False
        session.current_build_version = version_number
        session.status = "NO_VALID_BUILD"

    version_error_text = "; ".join(errors) if errors else None
    version_error_text = version_error_text or ""
    db.commit()
    response = serialize(db, session, version)
    response["validation_errors"] = errors
    response["message"] = (
        "Validated build ready for explicit approval."
        if session.status == "PROPOSED"
        else version_error_text or "No valid build exists within the requested constraints."
    )
    return response


@router.post("/sessions/{builder_id}/validate")
def validate(builder_id: str, db: Session = Depends(get_db)):
    session = db.query(PcBuilderSession).filter(PcBuilderSession.id == builder_id).first()
    if not session or not session.current_build_version:
        raise HTTPException(404, "BUILD_NOT_FOUND")
    version = (
        db.query(PcBuildVersion)
        .filter(PcBuildVersion.pc_builder_session_id == session.id, PcBuildVersion.version_number == session.current_build_version)
        .first()
    )
    if not version:
        raise HTTPException(404, "BUILD_NOT_FOUND")
    selected = {}
    role_to_category = {
        "CPU": "CPU", "GPU": "GPU", "MOTHERBOARD": "Motherboards", "RAM": "RAM Sticks",
        "STORAGE": "Storage Disks", "PSU": "PSUs", "CASE": "PC Cases"
    }
    for c in db.query(PcBuildComponent).filter(PcBuildComponent.build_version_id == version.id).all():
        product = db.query(Product).filter(Product.id == c.product_id).first()
        selected[role_to_category[c.component_role]] = product
    validation = validate_selection(db, selected, float(session.budget_max))
    version.total_price = validation["total"]
    version.budget_valid = validation["budget_valid"]
    version.inventory_valid = validation["inventory_valid"]
    version.compatibility_valid = validation["compatibility_valid"]
    if not validation["errors"]:
        version.status = "PROPOSED"
        session.status = "PROPOSED"
    else:
        version.status = "INVALID"
        session.status = "NO_VALID_BUILD"
    db.commit()
    response = serialize(db, session, version)
    response["validation_errors"] = validation["errors"]
    return response


@router.post("/sessions/{builder_id}/rebuild")
def rebuild(builder_id: str, db: Session = Depends(get_db)):
    session = db.query(PcBuilderSession).filter(PcBuilderSession.id == builder_id).first()
    if not session:
        raise HTTPException(404, "BUILD_NOT_FOUND")
    session.status = "BUILDING"
    db.commit()
    return generate(builder_id, db)


@router.post("/sessions/{builder_id}/approve")
def approve(builder_id: str, payload: ApproveBuild, db: Session = Depends(get_db)):
    session = db.query(PcBuilderSession).filter(PcBuilderSession.id == builder_id).first()
    if not session:
        raise HTTPException(404, "BUILD_NOT_FOUND")
    version = (
        db.query(PcBuildVersion)
        .filter(PcBuildVersion.pc_builder_session_id == session.id, PcBuildVersion.version_number == payload.version_number)
        .first()
    )
    if not version or version.version_number != session.current_build_version or version.status != "PROPOSED":
        raise HTTPException(400, "BUILD_VERSION_STALE")
    # Approval always revalidates the exact version before accepting it.
    validation = validate(builder_id, db)
    if not validation["validation_errors"]:
        version = (
            db.query(PcBuildVersion)
            .filter(PcBuildVersion.pc_builder_session_id == session.id, PcBuildVersion.version_number == payload.version_number)
            .first()
        )
        version.customer_approved = True
        version.approved_at = datetime.now(timezone.utc)
        version.status = "APPROVED"
        session.status = "APPROVED"
        db.commit()
        return serialize(db, session, version)
    raise HTTPException(409, "BUILD_INVALID")


@router.post("/sessions/{builder_id}/commit")
def commit(builder_id: str, db: Session = Depends(get_db)):
    session = db.query(PcBuilderSession).filter(PcBuilderSession.id == builder_id).first()
    if not session:
        raise HTTPException(404, "BUILD_NOT_FOUND")
    version = (
        db.query(PcBuildVersion)
        .filter(PcBuildVersion.pc_builder_session_id == session.id, PcBuildVersion.version_number == session.current_build_version)
        .first()
    )
    if not version or not version.customer_approved or version.status != "APPROVED":
        raise HTTPException(400, "BUILD_NOT_APPROVED")

    # Final authoritative inventory + compatibility + budget check immediately before mutation.
    validation = validate(builder_id, db)
    if validation["validation_errors"]:
        version.customer_approved = False
        version.status = "INVALID"
        session.status = "NO_VALID_BUILD"
        db.commit()
        raise HTTPException(409, "BUILD_OUT_OF_STOCK" if not validation["validation"]["inventory"] else "BUILD_INVALID")

    cart = db.query(Cart).filter(Cart.customer_session_id == session.customer_session_id, Cart.status == "ACTIVE").first()
    if not cart:
        cart = Cart(customer_session_id=session.customer_session_id, status="ACTIVE")
        db.add(cart)
        db.flush()

    for component in db.query(PcBuildComponent).filter(PcBuildComponent.build_version_id == version.id).all():
        item = db.query(CartItem).filter(CartItem.cart_id == cart.id, CartItem.product_id == component.product_id).first()
        if item:
            item.quantity += component.quantity
            component.is_reused_from_cart = True
        else:
            db.add(
                CartItem(
                    cart_id=cart.id,
                    product_id=component.product_id,
                    quantity=component.quantity,
                    unit_price=component.unit_price,
                )
            )

    version.status = "COMMITTED"
    session.status = "CART_ADDED"
    db.commit()
    recalc_cart(db, cart)
    return {"build": serialize(db, session, version), "cart_id": str(cart.id)}
