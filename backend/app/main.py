from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import products,sessions,cart,recovery,checkout,admin,chat,pc_builder
from apscheduler.schedulers.background import BackgroundScheduler
from app.database import SessionLocal
from app.services.recovery import scan_abandoned_carts

scheduler=BackgroundScheduler()

def recovery_job():
    db=SessionLocal()
    try: scan_abandoned_carts(db)
    finally: db.close()

app=FastAPI(title="Razorpay Agentic Commerce",version="1.0.0")
@app.on_event("startup")
def start_scheduler():
    scheduler.add_job(recovery_job,"interval",seconds=5,id="recovery-scan",replace_existing=True)
    scheduler.start()
@app.on_event("shutdown")
def stop_scheduler():
    if scheduler.running: scheduler.shutdown()
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
@app.get("/health")
def health(): return {"status":"ok","service":"agentic-commerce"}
for r in [products,sessions,cart,recovery,checkout,admin,chat,pc_builder]: app.include_router(r.router,prefix="/api")
