from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.models import RecoverySession, Attribution

WINDOW_HOURS=3

def calculate_attribution(order_id, cart_id, db: Session):
    existing=db.query(Attribution).filter(Attribution.order_id==order_id).first()
    if existing: return existing
    rs=db.query(RecoverySession).filter(RecoverySession.cart_id==cart_id).order_by(RecoverySession.created_at.desc()).first()
    now=datetime.now(timezone.utc)
    if rs and rs.last_meaningful_agent_interaction_at:
        end=rs.last_meaningful_agent_interaction_at+timedelta(hours=WINDOW_HOURS)
        kind="RECOVERED" if now<=end else "ORGANIC"
        a=Attribution(order_id=order_id,recovery_session_id=rs.id,attribution_type=kind,meaningful_interaction_at=rs.last_meaningful_agent_interaction_at,attribution_window_ends_at=end)
    else:
        a=Attribution(order_id=order_id,recovery_session_id=(rs.id if rs else None),attribution_type="ORGANIC")
    db.add(a); db.commit(); db.refresh(a); return a
