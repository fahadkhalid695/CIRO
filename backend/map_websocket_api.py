from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import asyncio
import json
import random

app = FastAPI()

# ------------------------------------------------------------------
# Simulation Logic: Real-time Vehicle & Zone Coordinates
# ------------------------------------------------------------------
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_text(json.dumps(message))

manager = ConnectionManager()

@app.websocket("/ws/map-stream")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Push initial emergency zones (e.g., G-10 Fire)
        await manager.broadcast({
            "type": "ZONE_UPDATE",
            "payload": [
                {
                    "id": "zone-fire-g10", 
                    "latitude": 33.6844, 
                    "longitude": 73.0479, 
                    "radius": 800, # 800 meter blast/evac radius 
                    "severity": 8
                }
            ]
        })
        
        # Simulate 2 emergency vehicles driving towards the crisis zone
        v1_lat, v1_lon = 33.6600, 73.0200
        v2_lat, v2_lon = 33.7000, 73.0600
        
        while True:
            # Random coordinate jitter to simulate driving forward
            v1_lat += random.uniform(0.0001, 0.0003)
            v1_lon += random.uniform(0.0001, 0.0003)
            
            v2_lat -= random.uniform(0.0001, 0.0003)
            v2_lon -= random.uniform(0.0001, 0.0003)
            
            # Broadcast Vehicle 1 (Fire Engine)
            await manager.broadcast({
                "type": "VEHICLE_UPDATE",
                "payload": {
                    "id": "unit-fire-1",
                    "type": "fire",
                    "latitude": v1_lat,
                    "longitude": v1_lon,
                    "heading": 45
                }
            })
            
            # Broadcast Vehicle 2 (Police)
            await manager.broadcast({
                "type": "VEHICLE_UPDATE",
                "payload": {
                    "id": "unit-police-1",
                    "type": "police",
                    "latitude": v2_lat,
                    "longitude": v2_lon,
                    "heading": 225
                }
            })
            
            # Broadcast updates every 1 second
            await asyncio.sleep(1) 
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
