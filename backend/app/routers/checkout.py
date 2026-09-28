import hashlib,hmac,json,uuid
from datetime import datetime,timezone
from fastapi import APIRouter,Depends,HTTPException,Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models import Cart,CartItem,Product,Order,OrderItem,Payment,PaymentWebhookEvent
from app.config import settings
from app.services.attribution import calculate_attribution

router=APIRouter(prefix="/checkout",tags=["checkout"])
class CheckoutIn(BaseModel): cart_id:str

def finalize(payment:Payment,provider_payment_id:str,db:Session):
    if payment.status=="SUCCESS": return
    payment.status="SUCCESS";payment.provider_payment_id=provider_payment_id
    order=db.query(Order).filter(Order.id==payment.order_id).first();order.status="COMPLETED"
    cart=db.query(Cart).filter(Cart.id==order.cart_id).first();cart.status="COMPLETED"
    calculate_attribution(order.id,cart.id,db)
    db.commit()

@router.post("/create-order")
def create_order(payload:CheckoutIn,db:Session=Depends(get_db)):
    cart=db.query(Cart).filter(Cart.id==payload.cart_id,Cart.status=="ACTIVE").first()
    if not cart or not cart.total: raise HTTPException(400,"CART_NOT_FOUND")
    order=Order(customer_session_id=cart.customer_session_id,cart_id=cart.id,status="CREATED",currency=cart.currency,subtotal=cart.subtotal,discount_total=cart.discount_total,total=cart.total)
    db.add(order);db.flush()
    for i in db.query(CartItem).filter(CartItem.cart_id==cart.id).all():
        p=db.query(Product).filter(Product.id==i.product_id).first(); line=float(i.unit_price)*i.quantity
        original=float(p.price)*i.quantity; disc=max(0,original-line)
        db.add(OrderItem(order_id=order.id,product_id=p.id,product_name=p.name,quantity=i.quantity,unit_price=i.unit_price,discount_amount=disc,line_total=line))
    demo=settings.DEMO_MODE or not settings.RAZORPAY_KEY_ID
    if demo: provider_id=f"order_demo_{uuid.uuid4().hex}"
    else:
        import razorpay
        client=razorpay.Client(auth=(settings.RAZORPAY_KEY_ID,settings.RAZORPAY_KEY_SECRET)); provider_id=client.order.create({"amount":int(float(order.total)*100),"currency":order.currency,"receipt":str(order.id)})["id"]
    db.add(Payment(order_id=order.id,provider="razorpay",provider_order_id=provider_id,amount=order.total,currency=order.currency,status="CREATED"));cart.status="CHECKOUT";db.commit()
    return {"order_id":str(order.id),"razorpay_order_id":provider_id,"amount":float(order.total),"currency":order.currency,"demo_mode":demo,"key_id":settings.RAZORPAY_KEY_ID}

@router.post("/demo-capture/{order_id}")
def demo_capture(order_id:str,db:Session=Depends(get_db)):
    if not settings.DEMO_MODE:
        raise HTTPException(403,"DEMO_MODE_DISABLED")
    p=db.query(Payment).join(Order,Payment.order_id==Order.id).filter(Order.id==order_id).first()
    if not p: raise HTTPException(404,"ORDER_NOT_FOUND")
    event_id=f"evt_demo_{uuid.uuid4().hex}"; payload={"event":"payment.captured","payload":{"payment":{"entity":{"id":f"pay_demo_{uuid.uuid4().hex}","order_id":p.provider_order_id,"status":"captured"}}},"id":event_id}
    process_event(payload,None,db,signature_verified=True);return {"status":"success","order_id":order_id}

@router.get("/payment-status/{order_id}")
def payment_status(order_id:str,db:Session=Depends(get_db)):
    payment=db.query(Payment).filter(Payment.order_id==order_id).first()
    order=db.query(Order).filter(Order.id==order_id).first()
    if not payment or not order:
        raise HTTPException(404,"ORDER_NOT_FOUND")
    return {"order_id":order_id,"order_status":order.status,"payment_status":payment.status}

async def process_raw(request:Request,db:Session):
    raw=await request.body(); signature=request.headers.get("X-Razorpay-Signature","")
    verified=bool(settings.RAZORPAY_WEBHOOK_SECRET and signature and hmac.compare_digest(hmac.new(settings.RAZORPAY_WEBHOOK_SECRET.encode(),raw,hashlib.sha256).hexdigest(),signature))
    if settings.DEMO_MODE and not settings.RAZORPAY_WEBHOOK_SECRET: verified=True
    payload=json.loads(raw.decode() or "{}")
    return process_event(payload,signature,db,verified)

def process_event(payload,signature,db,signature_verified):
    event_id=payload.get("id") or f"evt_{hashlib.sha256(json.dumps(payload,sort_keys=True).encode()).hexdigest()}"
    existing=db.query(PaymentWebhookEvent).filter(PaymentWebhookEvent.provider_event_id==event_id).first()
    if existing: return {"status":"already_processed"}
    event=PaymentWebhookEvent(provider="razorpay",provider_event_id=event_id,event_type=payload.get("event","unknown"),signature_verified=signature_verified,payload=payload,processed=False);db.add(event);db.flush()
    if not signature_verified: db.rollback();raise HTTPException(400,"WEBHOOK_INVALID")
    if payload.get("event")=="payment.captured":
        ent=payload.get("payload",{}).get("payment",{}).get("entity",{});provider_order_id=ent.get("order_id");p=db.query(Payment).filter(Payment.provider_order_id==provider_order_id).first()
        if p: finalize(p,ent.get("id","unknown"),db)
    event.processed=True;event.processed_at=datetime.now(timezone.utc);db.commit();return {"status":"ok"}

@router.post("/webhook")
async def webhook(request:Request,db:Session=Depends(get_db)): return await process_raw(request,db)
