from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Cart,RecoverySession,Intervention,MerchantConfig,RecoveryEvent
from app.services.recovery import evaluate_cart

router=APIRouter(prefix="/recovery",tags=["recovery"])
@router.post("/evaluate")
def evaluate(cart_id:str,db:Session=Depends(get_db)):
    cart=db.query(Cart).filter(Cart.id==cart_id).first()
    if not cart: raise HTTPException(404,"CART_NOT_FOUND")
    rs=evaluate_cart(db,cart)
    return {"eligible":bool(rs),"recovery_session_id":str(rs.id) if rs else None,"status":rs.status if rs else None}
@router.get("/sessions/{recovery_id}")
def get_recovery(recovery_id:str,db:Session=Depends(get_db)):
    r=db.query(RecoverySession).filter(RecoverySession.id==recovery_id).first()
    if not r: raise HTTPException(404,"SESSION_NOT_FOUND")
    return {"id":str(r.id),"cart_id":str(r.cart_id),"status":r.status,"intervention_count":r.intervention_count,"customer_opted_out":r.customer_opted_out,"customer_rejected":r.customer_rejected,"last_meaningful_agent_interaction_at":r.last_meaningful_agent_interaction_at}
@router.post("/{recovery_id}/intervene")
def intervene(recovery_id:str,reason:str="useful_assistance",db:Session=Depends(get_db)):
    r=db.query(RecoverySession).filter(RecoverySession.id==recovery_id).first()
    cfg=db.query(MerchantConfig).first()
    if not r: raise HTTPException(404,"SESSION_NOT_FOUND")
    if r.status!="ACTIVE": raise HTTPException(400,"RECOVERY_NOT_ELIGIBLE")
    if r.intervention_count>=cfg.maximum_interventions: raise HTTPException(400,"INTERVENTION_LIMIT_REACHED")
    r.intervention_count+=1; now=datetime.now(timezone.utc); r.last_meaningful_agent_interaction_at=now
    db.add(Intervention(recovery_session_id=r.id,sequence_number=r.intervention_count,status="COMPLETED",reason=reason,authorized_at=now,sent_at=now,completed_at=now))
    db.add(RecoveryEvent(recovery_session_id=r.id,event_type="INTERVENTION_SENT",metadata_={"sequence":r.intervention_count,"reason":reason})); db.commit()
    return {"ok":True,"intervention_count":r.intervention_count}
@router.post("/{recovery_id}/opt-out")
def opt_out(recovery_id:str,db:Session=Depends(get_db)):
    r=db.query(RecoverySession).filter(RecoverySession.id==recovery_id).first()
    if not r: raise HTTPException(404,"SESSION_NOT_FOUND")
    r.customer_opted_out=True;r.status="OPTED_OUT";r.ended_at=datetime.now(timezone.utc);db.commit();return {"ok":True}
@router.post("/{recovery_id}/reject")
def reject(recovery_id:str,db:Session=Depends(get_db)):
    r=db.query(RecoverySession).filter(RecoverySession.id==recovery_id).first()
    if not r: raise HTTPException(404,"SESSION_NOT_FOUND")
    r.customer_rejected=True;r.status="REJECTED";r.ended_at=datetime.now(timezone.utc);db.commit();return {"ok":True}
