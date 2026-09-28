from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Cart,CartItem,Product,Inventory,CustomerSession
from app.schemas import CartItemIn,CartUpdate
from app.services.commerce import get_or_create_cart,recalc_cart,serialize_cart

router=APIRouter(prefix="/cart",tags=["cart"])
@router.get("/{session_id}")
def get_cart(session_id:str,db:Session=Depends(get_db)):
    cart=get_or_create_cart(db,session_id)
    if not cart: raise HTTPException(404,"SESSION_NOT_FOUND")
    db.commit(); return serialize_cart(db,cart)
@router.post("/{session_id}/items")
def add_item(session_id:str,payload:CartItemIn,db:Session=Depends(get_db)):
    cart=get_or_create_cart(db,session_id)
    if not cart: raise HTTPException(404,"SESSION_NOT_FOUND")
    p=db.query(Product).filter(Product.id==payload.product_id,Product.is_active==True).first()
    inv=db.query(Inventory).filter(Inventory.product_id==payload.product_id).first()
    if not p: raise HTTPException(404,"PRODUCT_NOT_FOUND")
    if not inv or inv.quantity-inv.reserved_qty<payload.quantity: raise HTTPException(400,"PRODUCT_OUT_OF_STOCK")
    item=db.query(CartItem).filter(CartItem.cart_id==cart.id,CartItem.product_id==p.id).first()
    if item:
        if inv.quantity-inv.reserved_qty<item.quantity+payload.quantity: raise HTTPException(400,"PRODUCT_OUT_OF_STOCK")
        item.quantity+=payload.quantity
    else: db.add(CartItem(cart_id=cart.id,product_id=p.id,quantity=payload.quantity,unit_price=p.price))
    db.commit(); return serialize_cart(db,recalc_cart(db,cart))
@router.patch("/{session_id}/items/{item_id}")
def update_item(session_id:str,item_id:str,payload:CartUpdate,db:Session=Depends(get_db)):
    cart=get_or_create_cart(db,session_id); item=db.query(CartItem).filter(CartItem.id==item_id,CartItem.cart_id==cart.id).first()
    if not item: raise HTTPException(404,"CART_NOT_FOUND")
    if payload.quantity==0: db.delete(item)
    else:
        inv=db.query(Inventory).filter(Inventory.product_id==item.product_id).first()
        if not inv or inv.quantity-inv.reserved_qty<payload.quantity: raise HTTPException(400,"PRODUCT_OUT_OF_STOCK")
        item.quantity=payload.quantity
    db.commit(); return serialize_cart(db,recalc_cart(db,cart))
@router.delete("/{session_id}/items/{item_id}")
def delete_item(session_id:str,item_id:str,db:Session=Depends(get_db)):
    cart=get_or_create_cart(db,session_id); item=db.query(CartItem).filter(CartItem.id==item_id,CartItem.cart_id==cart.id).first()
    if item: db.delete(item); db.commit()
    return serialize_cart(db,recalc_cart(db,cart))
@router.post("/{session_id}/activity")
def activity(session_id:str,db:Session=Depends(get_db)):
    cart=get_or_create_cart(db,session_id); cart.last_activity_at=datetime.now(timezone.utc); db.commit(); return {"ok":True}
