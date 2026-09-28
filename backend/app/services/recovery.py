from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.models import Cart, RecoverySession, MerchantConfig, CustomerSession, RecoveryEvent
from app.config import settings
from app.services.whatsapp import whatsapp_client


def evaluate_cart(db: Session, cart: Cart):
    if cart.status not in ("ACTIVE","ABANDONED"): return None
    existing=db.query(RecoverySession).filter(RecoverySession.cart_id==cart.id, RecoverySession.status.in_(["ACTIVE","PENDING"])).first()
    if existing: return existing
    cfg=db.query(MerchantConfig).first()
    if not cfg or float(cart.total)<float(cfg.minimum_cart_value): return None
    cutoff=datetime.now(timezone.utc)-timedelta(seconds=settings.RECOVERY_INACTIVITY_SECONDS)
    if cart.last_activity_at and cart.last_activity_at>cutoff: return None
    cart.status="ABANDONED"
    rs=RecoverySession(cart_id=cart.id,customer_session_id=cart.customer_session_id,status="ACTIVE",eligible_at=datetime.now(timezone.utc),started_at=datetime.now(timezone.utc))
    db.add(rs); db.flush()
    customer=db.query(CustomerSession).filter(CustomerSession.id==cart.customer_session_id).first()
    if customer and customer.phone_number and whatsapp_client.send_notification(customer.phone_number, "Your cart is still waiting. Reply on the storefront if you want help finishing your purchase."):
        rs.whatsapp_sent=1
    db.add(RecoveryEvent(recovery_session_id=rs.id,event_type="RECOVERY_STARTED",metadata_={"demo":settings.DEMO_MODE,"whatsapp_sent":bool(rs.whatsapp_sent)}))
    db.commit(); db.refresh(rs); return rs


def scan_abandoned_carts(db: Session):
    carts=db.query(Cart).filter(Cart.status=="ACTIVE").all(); found=[]
    for c in carts:
        rs=evaluate_cart(db,c)
        if rs: found.append(rs)
    return found
