from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from datetime import datetime
import json
import asyncio
import uvicorn
from typing import List, Dict
import serial
import threading

app = FastAPI(title="Power Monitoring System", version="1.0.0")

# Enable CORS for web interface and ESP8266
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for messages
messages = []

class PowerData(BaseModel):
    device: str
    status: str
    voltage: float

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.append(connection)
        
        for connection in disconnected:
            self.disconnect(connection)

manager = ConnectionManager()

@app.post("/api/power-data")
async def receive_power_data(data: PowerData):
    """Endpoint for ESP8266 to send data via HTTP POST"""
    message = {
        "device": data.device,
        "status": data.status,
        "voltage": data.voltage,
        "timestamp": datetime.now().isoformat()
    }
    
    # Add to message history
    messages.append(message)
    
    # Keep last 100 messages
    if len(messages) > 100:
        messages.pop(0)
    
    # Broadcast to WebSocket clients
    await manager.broadcast(message)
    
    print(f"📡 Received from {data.device}: {data.status} (Voltage: {data.voltage}V)")
    
    return {
        "status": "success", 
        "message": "Data received successfully",
        "received_data": message
    }

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve a simple web interface"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Power Monitoring Dashboard</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            :root {
                --primary: #2c3e50;
                --success: #27ae60;
                --warning: #f39c12;
                --danger: #e74c3c;
                --info: #3498db;
            }
            
            * {
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            
            .header {
                background: var(--primary);
                color: white;
                padding: 30px;
                border-radius: 15px;
                margin-bottom: 20px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                text-align: center;
            }
            
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 20px;
            }
            
            .stat-card {
                background: white;
                padding: 20px;
                border-radius: 10px;
                text-align: center;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            
            .stat-number {
                font-size: 2em;
                font-weight: bold;
                margin: 10px 0;
            }
            
            .status-connected { color: var(--success); }
            .status-disconnected { color: var(--danger); }
            
            .messages-container {
                background: white;
                border-radius: 15px;
                padding: 20px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                max-height: 600px;
                overflow-y: auto;
            }
            
            .message {
                padding: 15px;
                border-left: 5px solid var(--info);
                margin-bottom: 10px;
                background: #f8f9fa;
                border-radius: 5px;
                animation: fadeIn 0.5s;
            }
            
            .status-POWER_CUT { 
                border-left-color: var(--danger);
                background: #fed7d7;
            }
            
            .status-NORMAL { 
                border-left-color: var(--success);
                background: #d4edda;
            }
            
            .status-UNKNOWN {
                border-left-color: var(--warning);
                background: #fff3cd;
            }
            
            .message-header {
                display: flex;
                justify-content: between;
                align-items: center;
                margin-bottom: 5px;
            }
            
            .device-badge {
                background: var(--primary);
                color: white;
                padding: 2px 8px;
                border-radius: 12px;
                font-size: 0.8em;
                font-weight: bold;
            }
            
            .status-badge {
                padding: 2px 8px;
                border-radius: 12px;
                font-size: 0.8em;
                font-weight: bold;
                margin-left: 10px;
            }
            
            .timestamp {
                color: #666;
                font-size: 0.9em;
                margin-left: auto;
            }
            
            .voltage {
                font-weight: bold;
                color: #2c3e50;
            }
            
            .websocket-status {
                background: #34495e;
                color: white;
                padding: 15px;
                border-radius: 10px;
                margin-bottom: 20px;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            .connection-dot {
                width: 10px;
                height: 10px;
                border-radius: 50%;
                display: inline-block;
            }
            
            .connected { background: var(--success); }
            .disconnected { background: var(--danger); }
            .connecting { background: var(--warning); }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>⚡ Power Monitoring System</h1>
                <p>Real-time power cut detection dashboard</p>
            </div>
            
            <div class="websocket-status">
                <span class="connection-dot connecting" id="status-dot"></span>
                <span id="status-text">Connecting to server...</span>
            </div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div>Total Messages</div>
                    <div class="stat-number" id="total-messages">0</div>
                </div>
                <div class="stat-card">
                    <div>Connected Devices</div>
                    <div class="stat-number" id="connected-devices">0</div>
                </div>
                <div class="stat-card">
                    <div>Power Cut Events</div>
                    <div class="stat-number" id="power-cuts">0</div>
                </div>
                <div class="stat-card">
                    <div>Last Update</div>
                    <div class="stat-number" id="last-update">-</div>
                </div>
            </div>
            
            <div class="messages-container">
                <h2>📨 Real-time Messages</h2>
                <div id="messages-list"></div>
            </div>
        </div>

        <script>
            const messagesList = document.getElementById('messages-list');
            const statusDot = document.getElementById('status-dot');
            const statusText = document.getElementById('status-text');
            const totalMessages = document.getElementById('total-messages');
            const connectedDevices = document.getElementById('connected-devices');
            const powerCuts = document.getElementById('power-cuts');
            const lastUpdate = document.getElementById('last-update');
            
            let messageCount = 0;
            let devices = new Set();
            let powerCutCount = 0;
            
            function updateStats() {
                totalMessages.textContent = messageCount;
                connectedDevices.textContent = devices.size;
                powerCuts.textContent = powerCutCount;
                lastUpdate.textContent = new Date().toLocaleTimeString();
            }
            
            function addMessage(data) {
                messageCount++;
                devices.add(data.device);
                if (data.status === 'POWER_CUT') powerCutCount++;
                
                const messageDiv = document.createElement('div');
                messageDiv.className = `message status-${data.status}`;
                
                const statusClass = data.status === 'POWER_CUT' ? 'status-POWER_CUT' : 
                                  data.status === 'NORMAL' ? 'status-NORMAL' : 'status-UNKNOWN';
                
                messageDiv.innerHTML = `
                    <div class="message-header">
                        <span class="device-badge">${data.device}</span>
                        <span class="status-badge ${statusClass}">${data.status}</span>
                        <span class="timestamp">${new Date(data.timestamp).toLocaleString()}</span>
                    </div>
                    <div>
                        <span class="voltage">Voltage: ${data.voltage.toFixed(2)}V</span>
                    </div>
                `;
                
                messagesList.prepend(messageDiv);
                updateStats();
                
                // Limit displayed messages to 50
                if (messagesList.children.length > 50) {
                    messagesList.removeChild(messagesList.lastChild);
                }
            }
            
            // WebSocket connection
            const ws = new WebSocket('ws://' + window.location.host + '/ws');
            
            ws.onopen = function() {
                statusDot.className = 'connection-dot connected';
                statusText.textContent = 'Connected to server ✅';
            };
            
            ws.onmessage = function(event) {
                const data = JSON.parse(event.data);
                addMessage(data);
            };
            
            ws.onclose = function() {
                statusDot.className = 'connection-dot disconnected';
                statusText.textContent = 'Disconnected from server ❌';
            };
            
            ws.onerror = function() {
                statusDot.className = 'connection-dot connecting';
                statusText.textContent = 'Connection error ⚠️';
            };
            
            // Initial stats update
            updateStats();
        </script>
    </body>
    </html>
    """

@app.get("/api/messages")
async def get_messages(limit: int = 50):
    """Get recent messages"""
    return messages[-limit:]

@app.get("/api/messages/{device}")
async def get_device_messages(device: str, limit: int = 20):
    """Get messages from a specific device"""
    device_messages = [msg for msg in messages if msg.get('device') == device]
    return device_messages[-limit:]

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    try:
        # Send recent messages to new connection
        recent_messages = messages[-10:]
        for message in recent_messages:
            await websocket.send_json(message)
        
        # Keep connection alive
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "message_count": len(messages),
        "connected_clients": len(manager.active_connections),
        "devices": list(set(msg['device'] for msg in messages))
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)