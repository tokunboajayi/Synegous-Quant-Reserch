from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import json
import asyncio

app = FastAPI(
    title="ANEE Telemetry Server",
    description="Real-time streaming of execution state from ANEE",
    version="0.1.0"
)

# In-memory buffer for streaming data (simulating live execution)
execution_state = {
    "parent_id": None,
    "t": 0,
    "q_star": 0.0,
    "q_exec": 0.0,
    "alpha": 1.0,
    "deviation_pct": 0.0,
    "cum_executed": 0.0,
    "cum_planned": 0.0,
    "trust_region_clipped": False,
    "cliff_risk": 0.0
}

class ExecutionSnapshot(BaseModel):
    parent_id: str
    t: int
    q_star: float
    q_exec: float
    alpha: float
    deviation_pct: float
    cum_executed: float
    cum_planned: float
    trust_region_clipped: bool
    cliff_risk: float

# WebSocket Connections
active_connections: List[WebSocket] = []

async def broadcast(data: dict):
    for conn in active_connections:
        try:
            await conn.send_json(data)
        except:
            pass

@app.websocket("/ws/execution")
async def ws_execution(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            # Echo back any messages (or just keep alive)
            data = await websocket.receive_text()
            await websocket.send_text(f"ACK: {data}")
    except WebSocketDisconnect:
        active_connections.remove(websocket)

@app.post("/execution/update")
async def update_execution_state(snapshot: ExecutionSnapshot):
    """
    Called by ANEE Engine during simulation to push state updates.
    """
    global execution_state
    execution_state = snapshot.dict()
    
    # Broadcast to all connected clients
    await broadcast(execution_state)
    
    return {"status": "ok"}

@app.get("/execution/state")
def get_execution_state():
    return execution_state

@app.get("/health")
def health():
    return {"status": "healthy"}
