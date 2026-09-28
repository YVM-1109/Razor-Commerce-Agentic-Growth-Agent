from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import CustomerSession
from app.schemas import SessionCreate

router=APIRouter(prefix="/sessions",tags=["sessions"])
@router.post("")
def create_session(payload:SessionCreate,db:Session=Depends(get_db)):
    s=CustomerSession(phone_number=payload.phone_number,status="ACTIVE",expires_at=datetime.now(timezone.utc)+timedelta(days=1))
    db.add(s); db.commit(); db.refresh(s); return {"id":str(s.id),"status":s.status,"phone_number":s.phone_number}
@router.get("/{session_id}")
def get_session(session_id:str,db:Session=Depends(get_db)):
    s=db.query(CustomerSession).filter(CustomerSession.id==session_id).first()
    if not s: raise HTTPException(404,"SESSION_NOT_FOUND")
    return {"id":str(s.id),"status":s.status,"phone_number":s.phone_number}

@router.patch("/{session_id}")
def update_session(session_id:str,payload:SessionCreate,db:Session=Depends(get_db)):
    s=db.query(CustomerSession).filter(CustomerSession.id==session_id).first()
    if not s: raise HTTPException(404,"SESSION_NOT_FOUND")
    if payload.phone_number is not None: s.phone_number=payload.phone_number
    s.last_activity_at=datetime.now(timezone.utc); db.commit(); return {"id":str(s.id),"status":s.status}
