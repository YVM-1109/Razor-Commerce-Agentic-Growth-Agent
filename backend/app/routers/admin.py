from datetime import datetime, timezone, timedelta
from fastapi import APIRouter,Depends,HTTPException,Header
from sqlalchemy.orm import Session
from sqlalchemy import func
import jwt
from app.database import get_db
from app.models import Merchant,MerchantConfig,Order,Attribution,Cart,RecoverySession,Intervention,Product,CartItem
from app.schemas import MerchantLogin,MerchantConfigIn
from app.config import settings

router=APIRouter(prefix="/merchant",tags=["merchant"])
def token_for(m): return jwt.encode({"sub":str(m.id),"email":m.email,"exp":datetime.now(timezone.utc)+timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)},settings.JWT_SECRET,algorithm="HS256")
def auth(authorization:str|None):
    if not authorization or not authorization.startswith("Bearer "): raise HTTPException(401,"UNAUTHORIZED")
    try:return jwt.decode(authorization.split(" ",1)[1],settings.JWT_SECRET,algorithms=["HS256"])
    except Exception: raise HTTPException(401,"UNAUTHORIZED")
@router.post("/auth/login")
def login(payload:MerchantLogin,db:Session=Depends(get_db)):
    m=db.query(Merchant).filter(Merchant.email==payload.email).first()
    if not m or payload.password not in ["demo123","password"]: raise HTTPException(401,"UNAUTHORIZED")
    return {"access_token":token_for(m),"merchant":{"email":m.email}}

def merchant_id(authorization): return auth(authorization)["sub"]
@router.get("/config")
def config(authorization:str|None=Header(None),db:Session=Depends(get_db)):
    mid=merchant_id(authorization); c=db.query(MerchantConfig).filter(MerchantConfig.merchant_id==mid).first();return {"maximum_discount_pct":float(c.maximum_discount_pct),"maximum_interventions":c.maximum_interventions,"minimum_cart_value":float(c.minimum_cart_value)}
@router.patch("/config")
def update_config(payload:MerchantConfigIn,authorization:str|None=Header(None),db:Session=Depends(get_db)):
    mid=merchant_id(authorization);c=db.query(MerchantConfig).filter(MerchantConfig.merchant_id==mid).first();c.maximum_discount_pct=payload.maximum_discount_pct;c.maximum_interventions=payload.maximum_interventions;c.minimum_cart_value=payload.minimum_cart_value;db.commit();return config(authorization,db)
@router.get("/dashboard")
def dashboard(authorization:str|None=Header(None),db:Session=Depends(get_db)):
    merchant_id(authorization)
    revenue=float(db.query(func.coalesce(func.sum(Order.total),0)).filter(Order.status=="COMPLETED").scalar() or 0)
    recovered=float(db.query(func.coalesce(func.sum(Order.total),0)).join(Attribution,Attribution.order_id==Order.id).filter(Order.status=="COMPLETED",Attribution.attribution_type=="RECOVERED").scalar() or 0)
    abandoned=db.query(Cart).filter(Cart.status.in_(["ABANDONED","CHECKOUT","COMPLETED"])).count()
    eligible=db.query(RecoverySession).count(); interventions=db.query(Intervention).count(); recovered_carts=db.query(Attribution).filter(Attribution.attribution_type=="RECOVERED").count()
    rate=(recovered_carts/eligible*100) if eligible else 0
    avg=(recovered/recovered_carts) if recovered_carts else 0
    products=[]
    for p in db.query(Product).order_by(Product.name).all():
        abandoned_p=db.query(CartItem).filter(CartItem.product_id==p.id).join(Cart,Cart.id==CartItem.cart_id).filter(Cart.status.in_(["ABANDONED","COMPLETED"])).count()
        products.append({"product":p.name,"abandoned":abandoned_p,"interventions":0,"recovered":0,"revenue_recovered":0})
    orders=[]
    for o in db.query(Order).order_by(Order.created_at.desc()).limit(12).all():
        a=db.query(Attribution).filter(Attribution.order_id==o.id).first();orders.append({"id":str(o.id),"status":o.status,"total":float(o.total),"attribution":a.attribution_type if a else "PENDING","created_at":o.created_at})
    recoveries=[]
    for r in db.query(RecoverySession).order_by(RecoverySession.created_at.desc()).limit(12).all(): recoveries.append({"id":str(r.id),"status":r.status,"interventions":r.intervention_count,"whatsapp_sent":r.whatsapp_sent,"created_at":r.created_at})
    return {"kpis":{"total_revenue":revenue,"revenue_at_risk":max(0, float(db.query(func.coalesce(func.sum(Cart.total),0)).filter(Cart.status=="ABANDONED").scalar() or 0)),"abandoned_carts":abandoned,"recovery_eligible_carts":eligible,"agent_interventions":interventions,"recovered_carts":recovered_carts,"recovery_rate":rate,"revenue_recovered":recovered,"average_recovered_cart_value":avg},"orders":orders,"recoveries":recoveries,"products":products}
@router.get("/daily-summary")
def daily_summary(authorization:str|None=Header(None),db:Session=Depends(get_db)):
    merchant_id(authorization); return {"headline":"Your growth agent is ready","summary":"Recovery is grounded in live catalogue, inventory and payment state. Use the storefront to run the two golden demo flows.","focus":["Abandoned-cart recovery","Product-level pricing assistance","Compatible PC building","Verified Razorpay payment attribution"]}
