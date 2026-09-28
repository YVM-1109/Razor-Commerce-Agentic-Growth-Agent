from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models import Cart, CartItem, Product, Inventory, CustomerSession


def get_or_create_cart(db: Session, session_id):
    cart = db.query(Cart).filter(Cart.customer_session_id == session_id, Cart.status == "ACTIVE").first()
    if cart: return cart
    if not db.query(CustomerSession).filter(CustomerSession.id == session_id).first(): return None
    cart = Cart(customer_session_id=session_id, status="ACTIVE")
    db.add(cart); db.flush(); return cart


def recalc_cart(db: Session, cart: Cart):
    items = db.query(CartItem).filter(CartItem.cart_id == cart.id).all()
    subtotal = sum((Decimal(str(i.unit_price)) * i.quantity for i in items), Decimal("0"))
    cart.subtotal = subtotal
    cart.total = max(Decimal("0"), subtotal - Decimal(str(cart.discount_total or 0)))
    cart.last_activity_at = datetime.now(timezone.utc)
    db.commit(); db.refresh(cart)
    return cart


def serialize_cart(db: Session, cart: Cart):
    rows=[]
    for item in db.query(CartItem).filter(CartItem.cart_id == cart.id).all():
        p=db.query(Product).filter(Product.id==item.product_id).first()
        inv=db.query(Inventory).filter(Inventory.product_id==item.product_id).first()
        rows.append({"id":str(item.id),"product_id":str(item.product_id),"quantity":item.quantity,"unit_price":float(item.unit_price),"original_price":float(p.price),"line_total":round(float(item.unit_price)*item.quantity,2),"product":{"id":str(p.id),"name":p.name,"slug":p.slug,"brand":p.brand,"price":float(p.price),"description":p.description,"category_id":str(p.category_id),"specifications":p.specifications,"pc_attributes":p.pc_attributes,"available":(inv.quantity-inv.reserved_qty if inv else 0)}})
    return {"id":str(cart.id),"customer_session_id":str(cart.customer_session_id),"status":cart.status,"currency":cart.currency,"subtotal":float(cart.subtotal),"discount_total":float(cart.discount_total),"total":float(cart.total),"items":rows}
