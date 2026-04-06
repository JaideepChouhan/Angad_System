from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from datetime import datetime
import json

app = FastAPI(title="Power Fault Detection System")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sample devices with Rajasthan locations
devices = [

    {"id": "head0001", "name": "Head Pole (DP)", "latitude": 28.0229, "longitude": 73.3119},
    {"id": "device0001", "name": "Pole 1", "latitude": 26.9124, "longitude": 75.7873},
    {"id": "device0002", "name": "Pole 2", "latitude": 26.2389, "longitude": 73.0243},
    {"id": "device0003", "name": "Pole 3", "latitude": 24.5854, "longitude": 73.7125},
    {"id": "device0004", "name": "Pole 4", "latitude": 25.2138, "longitude": 75.8648}
]

# Store faults
faults = []

class PowerData(BaseModel):
    device_id: str
    fault_type: str = "power_failure"
    sensor_value: float = 0.0
    timestamp: str = None

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Power Fault Monitoring</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: Arial, sans-serif;
                background: #f0f2f5;
                padding: 20px;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            .header {
                background: #2c3e50;
                color: white;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
                text-align: center;
            }
            .fault-card {
                background: white;
                border-radius: 10px;
                padding: 15px;
                margin: 10px 0;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                border-left: 5px solid #e74c3c;
            }
            .fault-card.resolved {
                border-left-color: #27ae60;
                opacity: 0.7;
            }
            .device-info {
                display: grid;
                grid-template-columns: 1fr 1fr 1fr;
                gap: 10px;
                margin-top: 20px;
            }
            .device-card {
                background: white;
                padding: 15px;
                border-radius: 8px;
                text-align: center;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            .status-online {
                color: #27ae60;
                font-weight: bold;
            }
            .status-offline {
                color: #e74c3c;
                font-weight: bold;
            }
            .fault-list {
                margin-top: 30px;
            }
            .no-faults {
                text-align: center;
                color: #7f8c8d;
                padding: 40px;
                background: white;
                border-radius: 10px;
            }
            .timestamp {
                color: #7f8c8d;
                font-size: 0.9em;
            }
            .severity {
                padding: 2px 8px;
                border-radius: 4px;
                font-size: 0.8em;
                margin-left: 10px;
            }
            .severity-high { background: #e74c3c; color: white; }
            .severity-medium { background: #f39c12; color: white; }
            .severity-low { background: #f1c40f; color: black; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>⚡ Power Fault Monitoring System: JAMWANT</h1>
                <p>Real-time fault detection for Keral power grid</p>
            </div>

            <div class="device-info">
                <div class="device-card">
                    <h3>Jaipur Substation</h3>
                    <p>Device: device0001</p>
                    <p class="status-online">● Online</p>
                </div>
                <div class="device-card">
                    <h3>Jaipur Substation</h3>
                    <p>Device: device0002</p>
                    <p class="status-online">● Online</p>
                </div>
                <div class="device-card">
                    <h3>Jaipur Substation</h3>
                    <p>Device: device0003</p>
                    <p class="status-online">● Online</p>
                </div>
                <div class="device-card">
                    <h3>Jaipur Substation</h3>
                    <p>Device: device0004</p>
                    <p class="status-online">● Online</p>
                </div>
                <div class="device-card">
                    <h3>Jaipur Substation</h3>
                    <p>Device: device0005</p>
                    <p class="status-online">● Online</p>
                </div>
            </div>

            <div class="fault-list">
                <h2>🚨 Active Faults</h2>
                <div id="faults-container">
                    <!-- Faults will be displayed here -->
                </div>
            </div>
        </div>

        <script>
            async function loadFaults() {
                try {
                    const response = await fetch('/api/faults');
                    const faults = await response.json();
                    
                    const container = document.getElementById('faults-container');
                    
                    if (faults.length === 0) {
                        container.innerHTML = `
                            <div class="no-faults">
                                <h3>✅ No Active Faults</h3>
                                <p>All systems are operating normally</p>
                            </div>
                        `;
                        return;
                    }
                    
                    container.innerHTML = faults.map(fault => `
                        <div class="fault-card ${fault.status === 'resolved' ? 'resolved' : ''}">
                            <h3>🚨 Fault Detected: ${fault.device_name}</h3>
                            <p><strong>Device ID:</strong> ${fault.device_id}</p>
                            <p><strong>Location:</strong> ${fault.latitude.toFixed(4)}, ${fault.longitude.toFixed(4)}</p>
                            <p><strong>Type:</strong> ${fault.fault_type} 
                                <span class="severity severity-${fault.severity}">${fault.severity}</span>
                            </p>
                            <p><strong>Sensor Value:</strong> ${fault.sensor_value}</p>
                            <p class="timestamp">Detected: ${new Date(fault.timestamp).toLocaleString()}</p>
                            <p><strong>Status:</strong> ${fault.status}</p>
                        </div>
                    `).join('');
                } catch (error) {
                    console.error('Error loading faults:', error);
                }
            }
            
            // Load faults every 3 seconds
            setInterval(loadFaults, 3000);
            loadFaults(); // Initial load
        </script>
    </body>
    </html>
    """

@app.post("/api/power-data")
async def receive_power_data(data: PowerData):
    """Receive data from ESP8266 devices"""
    
    # Find the device
    device = next((d for d in devices if d["id"] == data.device_id), None)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Determine severity based on sensor value
    if data.sensor_value > 8.0:
        severity = "high"
    elif data.sensor_value > 5.0:
        severity = "medium"
    else:
        severity = "low"
    
    # Create fault entry
    fault = {
        "id": len(faults) + 1,
        "device_id": data.device_id,
        "device_name": device["name"],
        "latitude": device["latitude"],
        "longitude": device["longitude"],
        "fault_type": data.fault_type,
        "sensor_value": data.sensor_value,
        "severity": severity,
        "timestamp": data.timestamp or datetime.now().isoformat(),
        "status": "detected"
    }
    
    faults.append(fault)
    
    print(f"🚨 New fault received: {device['name']} - {data.fault_type} (Severity: {severity})")
    
    return {
        "status": "success",
        "message": f"Fault recorded for {device['name']}",
        "fault_id": fault["id"]
    }

@app.get("/api/faults")
async def get_faults():
    """Get all faults (for the web interface)"""
    return faults

@app.get("/api/devices")
async def get_devices():
    """Get all registered devices"""
    return devices

@app.post("/api/faults/{fault_id}/resolve")
async def resolve_fault(fault_id: int):
    """Mark a fault as resolved"""
    fault = next((f for f in faults if f["id"] == fault_id), None)
    if not fault:
        raise HTTPException(status_code=404, detail="Fault not found")
    
    fault["status"] = "resolved"
    fault["resolved_at"] = datetime.now().isoformat()
    
    return {"status": "success", "message": f"Fault {fault_id} resolved"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)