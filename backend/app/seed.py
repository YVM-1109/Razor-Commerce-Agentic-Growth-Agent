from app.database import SessionLocal
from app.models import Merchant,MerchantConfig,Category,Product,Inventory,ProductCompatibility
from sqlalchemy import delete

CATEGORIES=["Headphones","Mouse","Keyboard","Monitor","CPU","GPU","Storage Disks","RAM Sticks","PSUs","PC Cases","Motherboards"]
PRODUCTS=[
("CPU","AMD Ryzen 5 5600",12000,"AMD","AM4","ATX","DDR5",None,650),
("CPU","Intel Core i5-13400F",19000,"Intel","LGA1700","ATX","DDR5",None,750),
("GPU","NVIDIA GeForce RTX 4060",30000,"NVIDIA",None,None,None,12,650),
("GPU","AMD Radeon RX 7600",28000,"AMD",None,None,None,16,700),
("Motherboards","MSI PRO B550M-A WIFI",9500,"MSI","AM4","ATX","DDR4",None,None),
("Motherboards","MSI PRO B760-P WIFI",15000,"ASUS","LGA1700","ATX","DDR5",None,None),
("RAM Sticks","Corsair Vengeance 16GB DDR4",5000,"Corsair",None,None,"DDR4",None,None),
("Storage Disks","WD Blue SN580 1TB",5500,"WD",None,None,None,None,None),
("PSUs","Corsair CX550 550W",5000,"Corsair",None,None,None,None,None),
("PSUs","Cooler Master MWE 650 Bronze 650W",6500,"Cooler Master",None,None,None,None,None),
("PC Cases","DeepCool CC560",4500,"DeepCool",None,"ATX",None,None,None),
("PC Cases","Montech Air 100",6000,"Montech",None,"ATX",None,None,None),
("Monitor","LG 27GP850-B 27 inch",32000,"LG",None,None,None,None,None),
("Keyboard","Keychron K8 Pro",9000,"Keychron",None,None,None,None,None),
("Mouse","Logitech G Pro X Superlight",12000,"Logitech",None,None,None,None,None),
("Headphones","HyperX Cloud III",8500,"HyperX",None,None,None,None,None),
]

def slug(s): return ''.join(ch.lower() if ch.isalnum() else '-' for ch in s).strip('-')

def seed():
 db=SessionLocal()
 try:
  m=db.query(Merchant).filter(Merchant.email=="demo@merchant.com").first()
  if not m:
   m=Merchant(email="demo@merchant.com",password_hash="demo");db.add(m);db.flush();db.add(MerchantConfig(merchant_id=m.id,maximum_discount_pct=10,maximum_interventions=2,minimum_cart_value=500))
  cats={}
  for name in CATEGORIES:
   c=db.query(Category).filter(Category.name==name).first()
   if not c:c=Category(name=name,slug=slug(name));db.add(c);db.flush()
   cats[name]=c
  for idx,(cat,name,price,brand,socket,form,memory,vr,psu_req) in enumerate(PRODUCTS,1):
   p=db.query(Product).filter(Product.slug==slug(name)).first()
   attrs={}
   if socket:attrs["socket"]=socket
   if form:attrs["form_factor"]=form
   if memory:attrs["memory_type"]=memory
   if psu_req:attrs["recommended_psu_wattage"]=psu_req
   if cat=="PSUs":
    attrs["wattage"]=int(next((x for x in str(name).split() if x.upper().endswith("W") and x[:-1].isdigit()), "650W")[:-1])
   if vr:attrs["vram_gb"]=vr
   if cat=="GPU": attrs["recommended_psu_wattage"]=psu_req
   specs={"brand":brand,"segment":"demo"}
   if not p:
    p=Product(merchant_id=m.id,category_id=cats[cat].id,sku=f"DEMO-{idx:03d}",name=name,slug=slug(name),description=f"Demo-ready {brand} {cat.lower()} with grounded catalogue data.",brand=brand,price=price,specifications=specs,pc_attributes=attrs)
    db.add(p);db.flush();db.add(Inventory(product_id=p.id,quantity=25,reserved_qty=0))
   else:
    p.pc_attributes=attrs;p.specifications=specs;p.price=price
  db.commit()
  print("Seed complete")
 finally: db.close()
if __name__=="__main__":seed()
