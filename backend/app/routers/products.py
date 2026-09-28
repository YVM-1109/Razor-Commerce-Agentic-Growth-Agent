from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Product, Category, Inventory

router=APIRouter(prefix="/products",tags=["products"])
def product_dict(db,p):
    inv=db.query(Inventory).filter(Inventory.product_id==p.id).first()
    return {"id":str(p.id),"category_id":str(p.category_id),"name":p.name,"slug":p.slug,"sku":p.sku,"brand":p.brand,"description":p.description,"price":float(p.price),"currency":p.currency,"specifications":p.specifications or {},"pc_attributes":p.pc_attributes or {},"available":(inv.quantity-inv.reserved_qty if inv else 0)}
@router.get("")
def get_products(category_slug:str|None=None,db:Session=Depends(get_db)):
    q=db.query(Product).filter(Product.is_active==True)
    if category_slug:q=q.join(Category).filter(Category.slug==category_slug)
    return [product_dict(db,p) for p in q.order_by(Product.category_id,Product.name).all()]
@router.get("/categories")
def categories(db:Session=Depends(get_db)): return [{"id":str(c.id),"name":c.name,"slug":c.slug} for c in db.query(Category).filter(Category.is_active==True).order_by(Category.name).all()]
@router.get("/{slug}")
def product(slug:str,db:Session=Depends(get_db)):
    p=db.query(Product).filter(Product.slug==slug,Product.is_active==True).first()
    if not p: raise HTTPException(404,"PRODUCT_NOT_FOUND")
    return product_dict(db,p)
