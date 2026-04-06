CREATE TABLE devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT UNIQUE NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    status TEXT NOT NULL,
    installation_date TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE linemen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    contact TEXT NOT NULL,
    assigned_area TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE faults (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT NOT NULL,
    timestamp DATETIME NOT NULL,
    fault_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    status TEXT NOT NULL,
    assigned_to INTEGER,
    resolved_at DATETIME,
    FOREIGN KEY(device_id) REFERENCES devices(device_id),
    FOREIGN KEY(assigned_to) REFERENCES linemen(id)
);
