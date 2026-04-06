from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import sqlite3
import uvicorn
from pydantic import BaseModel

# ------------------------------
# Define data models
# ------------------------------
class FaultRecord(BaseModel):
    device_id: str
    lat: float
    lon: float
    fault_type: str
    risk_level: str

class LinemanAccept(BaseModel):
    fault_id: int
    lineman_id: str

class LinemanComplete(BaseModel):
    fault_id: int
    lineman_id: str

# ------------------------------
# Initialize FastAPI app
# ------------------------------
app = FastAPI(title="Power Line Fault Detection System")

# Enable CORS (allow all for demo)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (UI pages)
app.mount("/static", StaticFiles(directory="."), name="static")

# ------------------------------
# Database initialization
# ------------------------------
def init_db():
    conn = sqlite3.connect('fault_detection.db')
    c = conn.cursor()

    # Create tables
    c.execute('''CREATE TABLE IF NOT EXISTS fault_records
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  device_id TEXT,
                  lat REAL,
                  lon REAL,
                  fault_type TEXT,
                  risk_level TEXT,
                  status TEXT DEFAULT 'Pending',
                  lineman_id TEXT,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')

    c.execute('''CREATE TABLE IF NOT EXISTS device_record
                 (device_id TEXT PRIMARY KEY,
                  location_name TEXT,
                  lat REAL,
                  lon REAL,
                  install_date TEXT,
                  status TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS lineman_record
                 (lineman_id TEXT PRIMARY KEY,
                  name TEXT,
                  area TEXT,
                  contact TEXT,
                  status TEXT)''')

    # Insert sample devices
    if c.execute("SELECT COUNT(*) FROM device_record").fetchone()[0] == 0:
        devices = [
            ('DEV001', 'Downtown Substation', 40.7128, -74.0060, '2023-01-15', 'Active'),
            ('DEV002', 'Uptown Power Station', 40.7812, -73.9665, '2023-02-20', 'Active'),
            ('DEV003', 'Westside Transformer', 40.7589, -73.9851, '2023-03-10', 'Active'),
            ('DEV004', 'Eastside Grid Point', 40.7282, -73.9842, '2023-04-05', 'Inactive'),
            ('DEV005', 'Central Power Hub', 40.7505, -73.9934, '2023-05-12', 'Active')
        ]
        c.executemany('INSERT INTO device_record VALUES (?,?,?,?,?,?)', devices)

    # Insert sample linemen
    if c.execute("SELECT COUNT(*) FROM lineman_record").fetchone()[0] == 0:
        linemen = [
            ('LM001', 'John Smith', 'Downtown', '555-0101', 'Available'),
            ('LM002', 'Mike Johnson', 'Uptown', '555-0102', 'Available'),
            ('LM003', 'Sarah Williams', 'Westside', '555-0103', 'Busy'),
            ('LM004', 'David Brown', 'Eastside', '555-0104', 'Available'),
            ('LM005', 'Emily Davis', 'Central', '555-0105', 'Available')
        ]
        c.executemany('INSERT INTO lineman_record VALUES (?,?,?,?,?)', linemen)

    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# ------------------------------
# API Endpoints
# ------------------------------

@app.get("/")
async def read_root():
    return FileResponse("officer.html")

@app.get("/officer")
async def get_officer_ui():
    return FileResponse("officer.html")

@app.get("/lineman")
async def get_lineman_ui():
    return FileResponse("lineman.html")

@app.post("/api/ingest")
async def ingest_fault_record(record: FaultRecord):
    conn = sqlite3.connect('fault_detection.db')
    c = conn.cursor()

    c.execute('''INSERT INTO fault_records 
                 (device_id, lat, lon, fault_type, risk_level) 
                 VALUES (?, ?, ?, ?, ?)''',
              (record.device_id, record.lat, record.lon,
               record.fault_type, record.risk_level))

    conn.commit()
    fault_id = c.lastrowid
    conn.close()

    return {"message": "Fault record ingested", "fault_id": fault_id}

@app.get("/api/alerts")
async def get_alerts():
    conn = sqlite3.connect('fault_detection.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute('''SELECT * FROM fault_records ORDER BY timestamp DESC''')
    alerts = [dict(row) for row in c.fetchall()]

    conn.close()
    return {"alerts": alerts}

@app.post("/api/lineman_accept")
async def lineman_accept(accept: LinemanAccept):
    conn = sqlite3.connect('fault_detection.db')
    c = conn.cursor()

    # Check if lineman exists
    c.execute('SELECT status FROM lineman_record WHERE lineman_id = ?', (accept.lineman_id,))
    lineman = c.fetchone()

    if not lineman:
        conn.close()
        raise HTTPException(status_code=404, detail="Lineman not found")

    if lineman[0] != 'Available':
        conn.close()
        raise HTTPException(status_code=400, detail="Lineman is not available")

    # Update fault record
    c.execute('''UPDATE fault_records 
                 SET status = 'Accepted', lineman_id = ? 
                 WHERE id = ? AND status = 'Pending' ''',
              (accept.lineman_id, accept.fault_id))

    if c.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=400, detail="Fault not found or already assigned")

    # Mark lineman as busy
    c.execute('UPDATE lineman_record SET status = "Busy" WHERE lineman_id = ?', (accept.lineman_id,))

    conn.commit()
    conn.close()

    return {"message": "Fault accepted by lineman"}

@app.post("/api/lineman_complete")
async def lineman_complete(complete: LinemanComplete):
    conn = sqlite3.connect('fault_detection.db')
    c = conn.cursor()

    # Mark fault as completed
    c.execute('''UPDATE fault_records 
                 SET status = 'Completed' 
                 WHERE id = ? AND lineman_id = ? AND status = 'Accepted' ''',
              (complete.fault_id, complete.lineman_id))

    if c.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=400, detail="Fault not found or not assigned to this lineman")

    # Free up lineman
    c.execute('UPDATE lineman_record SET status = "Available" WHERE lineman_id = ?', (complete.lineman_id,))

    # Auto-reassign: find next pending fault
    c.execute('''SELECT f.id 
                 FROM fault_records f
                 JOIN device_record d ON f.device_id = d.device_id
                 JOIN lineman_record l ON l.lineman_id = ?
                 WHERE f.status = 'Pending' 
                 AND d.location_name LIKE '%' || l.area || '%'
                 ORDER BY f.timestamp ASC LIMIT 1''', (complete.lineman_id,))
    next_fault = c.fetchone()

    if next_fault:
        fault_id = next_fault[0]
        # Assign immediately
        c.execute('''UPDATE fault_records 
                     SET status = 'Accepted', lineman_id = ? 
                     WHERE id = ?''', (complete.lineman_id, fault_id))
        c.execute('UPDATE lineman_record SET status = "Busy" WHERE lineman_id = ?', (complete.lineman_id,))
        msg = f"Lineman reassigned to next fault (ID: {fault_id})"
    else:
        msg = "No pending faults, lineman is now available"

    conn.commit()
    conn.close()

    return {"message": f"Fault completed. {msg}"}

@app.get("/api/linemen")
async def get_linemen():
    conn = sqlite3.connect('fault_detection.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute('SELECT * FROM lineman_record')
    linemen = [dict(row) for row in c.fetchall()]

    conn.close()
    return {"linemen": linemen}

@app.get("/api/devices")
async def get_devices():
    conn = sqlite3.connect('fault_detection.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute('SELECT * FROM device_record')
    devices = [dict(row) for row in c.fetchall()]

    conn.close()
    return {"devices": devices}

# ------------------------------
# Run server
# ------------------------------
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
