from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from datetime import datetime
import json
from typing import List, Optional
import random

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
    {"id": "head0001", "name": "Head Pole (DP)", "latitude": 28.0229, "longitude": 73.3119, "status": "online", "voltage": 230.5},
    {"id": "device0001", "name": "Pole 1", "latitude": 26.9124, "longitude": 75.7873, "status": "online", "voltage": 228.7},
    {"id": "device0002", "name": "Pole 2", "latitude": 26.2389, "longitude": 73.0243, "status": "online", "voltage": 231.2},
    {"id": "device0003", "name": "Pole 3", "latitude": 24.5854, "longitude": 73.7125, "status": "online", "voltage": 229.8},
    {"id": "device0004", "name": "Pole 4", "latitude": 25.2138, "longitude": 75.8648, "status": "online", "voltage": 230.1}
]

# Store faults
faults = []

class PowerData(BaseModel):
    device_id: str
    fault_msg: str
    timestamp: str
    sensor_reading: float

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Power Grid Monitoring - JAMWANT</title>
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            :root {
                --primary: #2563eb;
                --primary-dark: #1d4ed8;
                --primary-light: #3b82f6;
                --secondary: #64748b;
                --success: #10b981;
                --success-dark: #059669;
                --warning: #f59e0b;
                --warning-dark: #d97706;
                --danger: #ef4444;
                --danger-dark: #dc2626;
                --dark: #1e293b;
                --darker: #0f172a;
                --light: #f8fafc;
                --gray: #94a3b8;
                --card-bg: #ffffff;
                --sidebar-bg: #1e293b;
                --gradient-primary: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                --gradient-dark: linear-gradient(135deg, #1e293b 0%, #334155 100%);
                --gradient-success: linear-gradient(135deg, #10b981 0%, #059669 100%);
                --gradient-danger: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
                --gradient-warning: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
            }
            
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Inter', sans-serif;
                background: var(--gradient-primary);
                min-height: 100vh;
                color: var(--dark);
                overflow-x: hidden;
            }
            
            .dashboard {
                display: grid;
                grid-template-columns: 280px 1fr;
                min-height: 100vh;
            }
            
            /* Sidebar */
            .sidebar {
                background: var(--gradient-dark);
                color: white;
                padding: 2rem 1.5rem;
                box-shadow: 4px 0 20px rgba(0,0,0,0.2);
                position: relative;
                z-index: 10;
            }
            
            .logo {
                display: flex;
                align-items: center;
                gap: 12px;
                margin-bottom: 3rem;
                padding: 1rem;
                background: rgba(255,255,255,0.1);
                border-radius: 16px;
                backdrop-filter: blur(10px);
            }
            
            .logo-icon {
                font-size: 2rem;
                background: var(--gradient-primary);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            
            .logo-text {
                font-size: 1.5rem;
                font-weight: 700;
                background: linear-gradient(135deg, #fff, #cbd5e1);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            
            .nav-links {
                display: flex;
                flex-direction: column;
                gap: 0.5rem;
            }
            
            .nav-link {
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 1rem 1.5rem;
                border-radius: 12px;
                color: var(--gray);
                text-decoration: none;
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
            }
            
            .nav-link::before {
                content: '';
                position: absolute;
                left: 0;
                top: 0;
                height: 100%;
                width: 0;
                background: var(--gradient-primary);
                transition: width 0.3s ease;
                z-index: -1;
            }
            
            .nav-link:hover, .nav-link.active {
                color: white;
                transform: translateX(5px);
            }
            
            .nav-link:hover::before, .nav-link.active::before {
                width: 100%;
            }
            
            .nav-link i {
                width: 20px;
                text-align: center;
                transition: transform 0.3s ease;
            }
            
            .nav-link:hover i, .nav-link.active i {
                transform: scale(1.2);
            }
            
            /* Main Content */
            .main-content {
                padding: 2rem;
                background: rgba(255,255,255,0.95);
                backdrop-filter: blur(20px);
                position: relative;
            }
            
            .main-content::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 1px;
                background: linear-gradient(90deg, transparent, rgba(37, 99, 235, 0.3), transparent);
            }
            
            .header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 2rem;
                padding: 1.5rem;
                background: white;
                border-radius: 20px;
                box-shadow: 0 8px 25px -8px rgba(0,0,0,0.1);
                border: 1px solid rgba(255,255,255,0.8);
            }
            
            .header h1 {
                font-size: 2rem;
                font-weight: 700;
                background: var(--gradient-dark);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            
            .time-display {
                background: var(--gradient-primary);
                color: white;
                padding: 0.75rem 1.5rem;
                border-radius: 12px;
                font-weight: 600;
                box-shadow: 0 4px 15px rgba(37, 99, 235, 0.3);
            }
            
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
                gap: 1.5rem;
                margin-bottom: 2rem;
            }
            
            .stat-card {
                background: white;
                padding: 2rem;
                border-radius: 20px;
                box-shadow: 0 8px 25px -8px rgba(0,0,0,0.1);
                border: 1px solid rgba(255,255,255,0.8);
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
            }
            
            .stat-card::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: var(--gradient-primary);
            }
            
            .stat-card.danger::before {
                background: var(--gradient-danger);
            }
            
            .stat-card.warning::before {
                background: var(--gradient-warning);
            }
            
            .stat-card.success::before {
                background: var(--gradient-success);
            }
            
            .stat-card:hover {
                transform: translateY(-8px);
                box-shadow: 0 20px 40px -10px rgba(0,0,0,0.15);
            }
            
            .stat-icon {
                width: 60px;
                height: 60px;
                border-radius: 16px;
                display: flex;
                align-items: center;
                justify-content: center;
                margin-bottom: 1.5rem;
                font-size: 1.8rem;
                box-shadow: 0 8px 20px rgba(0,0,0,0.1);
            }
            
            .stat-icon.primary { background: var(--gradient-primary); color: white; }
            .stat-icon.danger { background: var(--gradient-danger); color: white; }
            .stat-icon.warning { background: var(--gradient-warning); color: white; }
            .stat-icon.success { background: var(--gradient-success); color: white; }
            
            .stat-value {
                font-size: 2.5rem;
                font-weight: 800;
                margin-bottom: 0.5rem;
                background: var(--gradient-dark);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            
            .stat-label {
                color: var(--secondary);
                font-size: 0.95rem;
                font-weight: 500;
            }
            
            /* Devices Grid */
            .devices-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
                gap: 1.5rem;
                margin-bottom: 2rem;
            }
            
            .device-card {
                background: white;
                padding: 1.5rem;
                border-radius: 20px;
                box-shadow: 0 8px 25px -8px rgba(0,0,0,0.1);
                border: 1px solid rgba(255,255,255,0.8);
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
            }
            
            .device-card::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 3px;
                background: var(--gradient-success);
            }
            
            .device-card.warning::before {
                background: var(--gradient-warning);
            }
            
            .device-card.danger::before {
                background: var(--gradient-danger);
            }
            
            .device-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 15px 35px -10px rgba(0,0,0,0.15);
            }
            
            .device-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 1rem;
            }
            
            .device-name {
                font-weight: 700;
                font-size: 1.2rem;
                color: var(--dark);
            }
            
            .device-status {
                padding: 0.5rem 1rem;
                border-radius: 20px;
                font-size: 0.8rem;
                font-weight: 600;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            }
            
            .status-online { background: var(--gradient-success); color: white; }
            .status-offline { background: var(--gradient-danger); color: white; }
            .status-warning { background: var(--gradient-warning); color: white; }
            
            .device-info {
                display: grid;
                gap: 0.75rem;
            }
            
            .info-row {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 0.5rem 0;
                border-bottom: 1px solid rgba(0,0,0,0.05);
            }
            
            .info-row:last-child {
                border-bottom: none;
            }
            
            .info-label {
                color: var(--secondary);
                font-size: 0.9rem;
                font-weight: 500;
            }
            
            .info-value {
                font-weight: 600;
                color: var(--dark);
            }
            
            .voltage-indicator {
                padding: 0.25rem 0.75rem;
                border-radius: 12px;
                font-size: 0.8rem;
                font-weight: 600;
            }
            
            .voltage-normal { background: rgba(16, 185, 129, 0.1); color: var(--success); }
            .voltage-warning { background: rgba(245, 158, 11, 0.1); color: var(--warning); }
            .voltage-danger { background: rgba(239, 68, 68, 0.1); color: var(--danger); }
            
            /* Faults Section */
            .faults-section {
                background: white;
                border-radius: 20px;
                box-shadow: 0 8px 25px -8px rgba(0,0,0,0.1);
                overflow: hidden;
                border: 1px solid rgba(255,255,255,0.8);
            }
            
            .section-header {
                padding: 1.5rem 2rem;
                border-bottom: 1px solid rgba(0,0,0,0.05);
                display: flex;
                justify-content: space-between;
                align-items: center;
                background: var(--gradient-dark);
                color: white;
            }
            
            .section-title {
                font-size: 1.25rem;
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }
            
            .fault-count {
                background: rgba(255,255,255,0.2);
                padding: 0.5rem 1rem;
                border-radius: 12px;
                font-weight: 600;
            }
            
            .faults-list {
                max-height: 400px;
                overflow-y: auto;
            }
            
            .fault-item {
                padding: 1.5rem 2rem;
                border-bottom: 1px solid rgba(0,0,0,0.05);
                display: grid;
                grid-template-columns: auto 1fr auto;
                gap: 1.5rem;
                align-items: start;
                transition: all 0.3s ease;
            }
            
            .fault-item:hover {
                background: rgba(0,0,0,0.02);
            }
            
            .fault-item:last-child {
                border-bottom: none;
            }
            
            .fault-icon {
                width: 56px;
                height: 56px;
                border-radius: 16px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1.5rem;
                box-shadow: 0 8px 20px rgba(0,0,0,0.1);
            }
            
            .fault-icon.danger { background: var(--gradient-danger); color: white; }
            .fault-icon.warning { background: var(--gradient-warning); color: white; }
            .fault-icon.success { background: var(--gradient-success); color: white; }
            
            .fault-content {
                display: grid;
                gap: 0.75rem;
            }
            
            .fault-title {
                font-weight: 700;
                font-size: 1.1rem;
                color: var(--dark);
            }
            
            .fault-details {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
                gap: 1rem;
                font-size: 0.9rem;
            }
            
            .fault-meta {
                text-align: right;
                font-size: 0.85rem;
                color: var(--secondary);
                display: grid;
                gap: 0.5rem;
            }
            
            .severity-badge {
                padding: 0.5rem 1rem;
                border-radius: 12px;
                font-size: 0.8rem;
                font-weight: 700;
                display: inline-block;
                margin-left: 0.5rem;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            }
            
            .severity-high { background: var(--gradient-danger); color: white; }
            .severity-medium { background: var(--gradient-warning); color: white; }
            .severity-low { background: var(--gradient-success); color: white; }
            
            .no-faults {
                padding: 4rem 2rem;
                text-align: center;
                color: var(--secondary);
            }
            
            .no-faults i {
                font-size: 4rem;
                margin-bottom: 1.5rem;
                background: var(--gradient-success);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            
            .no-faults h3 {
                font-size: 1.5rem;
                margin-bottom: 0.5rem;
                color: var(--dark);
            }
            
            .resolve-btn {
                padding: 0.5rem 1rem;
                background: var(--gradient-success);
                color: white;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-size: 0.85rem;
                font-weight: 600;
                transition: all 0.3s ease;
                box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
            }
            
            .resolve-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);
            }
            
            /* Responsive */
            @media (max-width: 1024px) {
                .dashboard {
                    grid-template-columns: 1fr;
                }
                
                .sidebar {
                    display: none;
                }
                
                .stats-grid {
                    grid-template-columns: repeat(2, 1fr);
                }
                
                .devices-grid {
                    grid-template-columns: 1fr;
                }
            }
            
            @media (max-width: 768px) {
                .main-content {
                    padding: 1rem;
                }
                
                .stats-grid {
                    grid-template-columns: 1fr;
                }
                
                .header {
                    flex-direction: column;
                    gap: 1rem;
                    text-align: center;
                }
                
                .fault-item {
                    grid-template-columns: 1fr;
                    text-align: center;
                    gap: 1rem;
                }
                
                .fault-meta {
                    text-align: center;
                }
            }
            
            /* Animations */
            @keyframes pulse {
                0% { transform: scale(1); }
                50% { transform: scale(1.05); }
                100% { transform: scale(1); }
            }
            
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(20px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            @keyframes slideIn {
                from { transform: translateX(-100%); }
                to { transform: translateX(0); }
            }
            
            .pulse {
                animation: pulse 2s infinite;
            }
            
            .fade-in {
                animation: fadeIn 0.6s ease-out;
            }
            
            .slide-in {
                animation: slideIn 0.5s ease-out;
            }
            
            /* Custom Scrollbar */
            .faults-list::-webkit-scrollbar {
                width: 6px;
            }
            
            .faults-list::-webkit-scrollbar-track {
                background: rgba(0,0,0,0.05);
                border-radius: 3px;
            }
            
            .faults-list::-webkit-scrollbar-thumb {
                background: var(--gradient-primary);
                border-radius: 3px;
            }
            
            .faults-list::-webkit-scrollbar-thumb:hover {
                background: var(--primary-dark);
            }
        </style>
    </head>
    <body>
        <div class="dashboard">
            <!-- Sidebar -->
            <div class="sidebar">
                <div class="logo">
                    <i class="fas fa-bolt logo-icon"></i>
                    <div class="logo-text">JAMWANT</div>
                </div>
                
                <div class="nav-links">
                    <a href="#" class="nav-link active">
                        <i class="fas fa-tachometer-alt"></i>
                        <span>Dashboard</span>
                    </a>
                    <a href="#" class="nav-link">
                        <i class="fas fa-map-marker-alt"></i>
                        <span>Map View</span>
                    </a>
                    <a href="#" class="nav-link">
                        <i class="fas fa-history"></i>
                        <span>History</span>
                    </a>
                    <a href="#" class="nav-link">
                        <i class="fas fa-chart-bar"></i>
                        <span>Analytics</span>
                    </a>
                    <a href="#" class="nav-link">
                        <i class="fas fa-cog"></i>
                        <span>Settings</span>
                    </a>
                    <a href="#" class="nav-link">
                        <i class="fas fa-question-circle"></i>
                        <span>Help & Support</span>
                    </a>
                </div>
            </div>
            
            <!-- Main Content -->
            <div class="main-content">
                <div class="header">
                    <h1>Power Grid Monitoring Dashboard</h1>
                    <div class="time-display" id="current-time"></div>
                </div>
                
                <!-- Statistics -->
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-icon primary">
                            <i class="fas fa-plug"></i>
                        </div>
                        <div class="stat-value" id="total-devices">5</div>
                        <div class="stat-label">Total Devices</div>
                    </div>
                    
                    <div class="stat-card danger">
                        <div class="stat-icon danger">
                            <i class="fas fa-exclamation-triangle"></i>
                        </div>
                        <div class="stat-value" id="active-faults">0</div>
                        <div class="stat-label">Active Faults</div>
                    </div>
                    
                    <div class="stat-card warning">
                        <div class="stat-icon warning">
                            <i class="fas fa-bolt"></i>
                        </div>
                        <div class="stat-value" id="avg-voltage">230V</div>
                        <div class="stat-label">Grid Voltage</div>
                    </div>
                    
                    <div class="stat-card success">
                        <div class="stat-icon success">
                            <i class="fas fa-check-circle"></i>
                        </div>
                        <div class="stat-value" id="uptime">100%</div>
                        <div class="stat-label">System Uptime</div>
                    </div>
                </div>
                
                <!-- Devices -->
                <h2 style="margin-bottom: 1.5rem; font-weight: 700; color: var(--dark); font-size: 1.5rem;">
                    <i class="fas fa-microchip" style="margin-right: 0.5rem; color: var(--primary);"></i>
                    Connected Devices
                </h2>
                <div class="devices-grid" id="devices-container">
                    <!-- Devices will be loaded here -->
                </div>
                
                <!-- Faults -->
                <div class="faults-section">
                    <div class="section-header">
                        <h2 class="section-title">
                            <i class="fas fa-exclamation-triangle"></i>
                            Active Faults
                        </h2>
                        <div class="fault-count" id="fault-count">0 Faults</div>
                    </div>
                    
                    <div class="faults-list" id="faults-container">
                        <!-- Faults will be loaded here -->
                    </div>
                </div>
            </div>
        </div>

        <script>
            // Update current time
            function updateTime() {
                const now = new Date();
                const options = { 
                    weekday: 'long', 
                    year: 'numeric', 
                    month: 'long', 
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit'
                };
                document.getElementById('current-time').textContent = 
                    now.toLocaleDateString('en-US', options);
            }
            setInterval(updateTime, 1000);
            updateTime();
            
            // Load devices
            async function loadDevices() {
                try {
                    const response = await fetch('/api/devices');
                    const devices = await response.json();
                    
                    const container = document.getElementById('devices-container');
                    container.innerHTML = devices.map(device => {
                        const voltage = device.voltage || 230;
                        let voltageClass = 'voltage-normal';
                        if (voltage < 220) voltageClass = 'voltage-warning';
                        if (voltage < 210 || voltage > 250) voltageClass = 'voltage-danger';
                        
                        return `
                        <div class="device-card fade-in">
                            <div class="device-header">
                                <div class="device-name">${device.name}</div>
                                <div class="device-status status-online">● Online</div>
                            </div>
                            <div class="device-info">
                                <div class="info-row">
                                    <span class="info-label">Device ID:</span>
                                    <span class="info-value">${device.id}</span>
                                </div>
                                <div class="info-row">
                                    <span class="info-label">Location:</span>
                                    <span class="info-value">${device.latitude.toFixed(4)}, ${device.longitude.toFixed(4)}</span>
                                </div>
                                <div class="info-row">
                                    <span class="info-label">Voltage:</span>
                                    <span class="info-value">
                                        ${voltage}V 
                                        <span class="voltage-indicator ${voltageClass}">
                                            ${voltageClass === 'voltage-normal' ? 'Normal' : voltageClass === 'voltage-warning' ? 'Warning' : 'Critical'}
                                        </span>
                                    </span>
                                </div>
                                <div class="info-row">
                                    <span class="info-label">Last Update:</span>
                                    <span class="info-value">${new Date().toLocaleTimeString()}</span>
                                </div>
                            </div>
                        </div>
                    `}).join('');
                    
                    document.getElementById('total-devices').textContent = devices.length;
                    
                    // Calculate average voltage
                    const avgVoltage = devices.reduce((sum, device) => sum + (device.voltage || 230), 0) / devices.length;
                    document.getElementById('avg-voltage').textContent = avgVoltage.toFixed(1) + 'V';
                    
                } catch (error) {
                    console.error('Error loading devices:', error);
                }
            }
            
            // Load faults
            async function loadFaults() {
                try {
                    const response = await fetch('/api/faults');
                    const faults = await response.json();
                    
                    const container = document.getElementById('faults-container');
                    const activeFaults = faults.filter(f => f.status === 'detected');
                    
                    document.getElementById('active-faults').textContent = activeFaults.length;
                    document.getElementById('fault-count').textContent = `${activeFaults.length} Active Fault${activeFaults.length !== 1 ? 's' : ''}`;
                    
                    if (activeFaults.length === 0) {
                        container.innerHTML = `
                            <div class="no-faults">
                                <i class="fas fa-check-circle"></i>
                                <h3>All Systems Operational</h3>
                                <p>No active faults detected in the power grid</p>
                            </div>
                        `;
                        return;
                    }
                    
                    container.innerHTML = activeFaults.map(fault => `
                        <div class="fault-item fade-in">
                            <div class="fault-icon ${fault.severity === 'high' ? 'danger' : fault.severity === 'medium' ? 'warning' : 'success'}">
                                <i class="fas ${fault.severity === 'high' ? 'fa-bolt' : 'fa-exclamation-triangle'}"></i>
                            </div>
                            <div class="fault-content">
                                <div class="fault-title">
                                    ${fault.device_name}
                                    <span class="severity-badge severity-${fault.severity}">${fault.severity.toUpperCase()}</span>
                                </div>
                                <div class="fault-details">
                                    <div><strong>Type:</strong> ${fault.fault_type}</div>
                                    <div><strong>Sensor Reading:</strong> ${fault.sensor_value}V</div>
                                    <div><strong>Location:</strong> ${fault.latitude.toFixed(4)}, ${fault.longitude.toFixed(4)}</div>
                                </div>
                            </div>
                            <div class="fault-meta">
                                <div>${new Date(fault.timestamp).toLocaleDateString()}</div>
                                <div>${new Date(fault.timestamp).toLocaleTimeString()}</div>
                                <button onclick="resolveFault(${fault.id})" class="resolve-btn">
                                    <i class="fas fa-check"></i> Mark Resolved
                                </button>
                            </div>
                        </div>
                    `).join('');
                    
                } catch (error) {
                    console.error('Error loading faults:', error);
                }
            }
            
            // Resolve fault
            async function resolveFault(faultId) {
                try {
                    const response = await fetch(`/api/faults/${faultId}/resolve`, {
                        method: 'POST'
                    });
                    
                    if (response.ok) {
                        loadFaults();
                    }
                } catch (error) {
                    console.error('Error resolving fault:', error);
                }
            }
            
            // Initialize dashboard
            loadDevices();
            loadFaults();
            
            // Refresh data every 5 seconds
            setInterval(() => {
                loadDevices();
                loadFaults();
            }, 5000);
        </script>
    </body>
    </html>
    """

@app.post("/api/power-data")
async def receive_power_data(data: PowerData):
    """Receive data from ESP8266 devices"""
    
    # Parse the fault message to extract type and device info
    fault_type = "Unknown"
    if "ALERT" in data.fault_msg:
        fault_type = "Power Fault"
    elif "RECOVERY" in data.fault_msg:
        fault_type = "Power Recovery"
    
    # Extract device ID from fault message or use provided device_id
    device_id = data.device_id
    if "ALERT:" in data.fault_msg or "RECOVERY:" in data.fault_msg:
        parts = data.fault_msg.split(":")
        if len(parts) > 1:
            device_id = parts[1].split("->")[0] if "->" in parts[1] else parts[1]
    
    # Find the device
    device = next((d for d in devices if d["id"] == device_id), None)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Update device voltage
    device["voltage"] = data.sensor_reading
    
    # Determine severity based on sensor value
    if data.sensor_reading > 250.0 or data.sensor_reading < 210.0:
        severity = "high"
    elif data.sensor_reading > 240.0 or data.sensor_reading < 220.0:
        severity = "medium"
    else:
        severity = "low"
    
    # Check if this is a recovery message
    is_recovery = "RECOVERY" in data.fault_msg
    
    # Create fault entry
    fault = {
        "id": len(faults) + 1,
        "device_id": device_id,
        "device_name": device["name"],
        "latitude": device["latitude"],
        "longitude": device["longitude"],
        "fault_type": fault_type,
        "sensor_value": data.sensor_reading,
        "severity": severity,
        "timestamp": data.timestamp or datetime.now().isoformat(),
        "status": "resolved" if is_recovery else "detected"
    }
    
    # If it's a recovery, mark any existing faults for this device as resolved
    if is_recovery:
        for f in faults:
            if f["device_id"] == device_id and f["status"] == "detected":
                f["status"] = "resolved"
                f["resolved_at"] = datetime.now().isoformat()
    else:
        # Only add new fault if it's not a recovery
        faults.append(fault)
    
    print(f"📡 Data received: {device['name']} - {fault_type} - {data.sensor_reading}V")
    
    return {
        "status": "success",
        "message": f"Data processed for {device['name']}",
        "fault_id": fault["id"] if not is_recovery else None
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

@app.get("/api/stats")
async def get_stats():
    """Get dashboard statistics"""
    total_devices = len(devices)
    active_faults = len([f for f in faults if f["status"] == "detected"])
    online_devices = len([d for d in devices if d.get("status") == "online"])
    
    return {
        "total_devices": total_devices,
        "active_faults": active_faults,
        "online_devices": online_devices,
        "uptime_percentage": 100.0
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)