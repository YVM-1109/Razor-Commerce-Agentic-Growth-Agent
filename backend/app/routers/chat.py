from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.schemas import ChatIn
from app.agent.sales_agent import handle_message

router=APIRouter(prefix="/chat",tags=["chat"])
@router.post("")
def chat(payload:ChatIn): return handle_message(str(payload.session_id),str(payload.cart_id) if payload.cart_id else None,payload.message)
@router.websocket("/ws/{session_id}")
async def ws(websocket:WebSocket,session_id:str):
    await websocket.accept()
    await websocket.send_json({"type":"connection.ready"})
    try:
        while True:
            data=await websocket.receive_json(); result=handle_message(session_id,data.get("cart_id"),data.get("message","") )
            await websocket.send_json({"type":"agent.message",**result})
    except WebSocketDisconnect: pass
