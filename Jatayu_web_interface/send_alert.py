import requests
import random
import time
import sys

# Sample data for generating random alerts
DEVICES = [
    {"device_id": "DEV001", "lat": 40.7128, "lon": -74.0060},
    {"device_id": "DEV002", "lat": 40.7812, "lon": -73.9665},
    {"device_id": "DEV003", "lat": 40.7589, "lon": -73.9851},
    {"device_id": "DEV005", "lat": 40.7505, "lon": -73.9934}
]

FAULT_TYPES = ["Wire Snap", "Sparking", "Overheating", "Voltage Drop", "Transformer Failure"]
RISK_LEVELS = ["Normal", "Intermediate", "Drastic"]

def send_alert():
    """Send a random fault alert to the backend"""
    # Choose random device and fault details
    device = random.choice(DEVICES)
    fault_type = random.choice(FAULT_TYPES)
    risk_level = random.choice(RISK_LEVELS)
    
    # Prepare the alert data
    alert_data = {
        "device_id": device["device_id"],
        "lat": device["lat"] + random.uniform(-0.01, 0.01),  # Add slight variation
        "lon": device["lon"] + random.uniform(-0.01, 0.01),
        "fault_type": fault_type,
        "risk_level": risk_level
    }
    
    try:
        # Send POST request to the backend
        response = requests.post("http://localhost:8000/api/ingest", json=alert_data)
        
        if response.status_code == 200:
            print(f"Alert sent: {device['device_id']} - {fault_type} ({risk_level})")
        else:
            print(f"Failed to send alert: {response.status_code} - {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the server. Make sure the backend is running.")
        sys.exit(1)

def main():
    print("Power Line Fault Detection - Device Simulation")
    print("Sending random alerts to the backend...")
    print("Press Ctrl+C to stop\n")
    
    try:
        while True:
            send_alert()
            # Wait between 5 to 15 seconds before sending next alert
            wait_time = random.randint(5, 15)
            time.sleep(wait_time)
    except KeyboardInterrupt:
        print("\nSimulation stopped.")

if __name__ == "__main__":
    main()