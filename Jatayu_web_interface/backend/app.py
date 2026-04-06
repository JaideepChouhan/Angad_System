import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from models import db, Device, Fault, Lineman
from config import Config
from datetime import datetime
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)
db.init_app(app)
socketio = SocketIO(app, cors_allowed_origins="*")

def notify_clients(event, data):
    socketio.emit(event, data, broadcast=True)

with app.app_context():
    db.create_all()

########## Device Management ##########
@app.route('/api/devices', methods=['GET'])
def get_devices():
    status = request.args.get('status')
    query = Device.query
    if status:
        query = query.filter_by(status=status)
    devices = query.all()
    return jsonify([{
        "id": d.id,
        "device_id": d.device_id,
        "latitude": d.latitude,
        "longitude": d.longitude,
        "status": d.status,
        "installation_date": d.installation_date,
        "created_at": d.created_at.isoformat()
    } for d in devices]), 200

@app.route('/api/devices', methods=['POST'])
def register_device():
    data = request.get_json()
    try:
        if not all(k in data for k in ("device_id", "latitude", "longitude", "installation_date")):
            raise ValueError("Missing fields")
        # basic validation
        if type(data["latitude"]) not in [float, int] or type(data["longitude"]) not in [float, int]:
            raise ValueError("Invalid coordinates")
        new_device = Device(
            device_id=data["device_id"],
            latitude=float(data["latitude"]),
            longitude=float(data["longitude"]),
            status="active",
            installation_date=data["installation_date"]
        )
        db.session.add(new_device)
        db.session.commit()
        return jsonify({"message": "Device registered"}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Device ID must be unique"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/devices/<int:id>', methods=['PUT'])
def update_device_status(id):
    data = request.get_json()
    status = data.get("status")
    device = Device.query.get(id)
    if device and status in ["active", "inactive"]:
        device.status = status
        db.session.commit()
        return jsonify({"message": "Device status updated"}), 200
    return jsonify({"error": "Bad request"}), 400

@app.route('/api/devices/<int:id>', methods=['DELETE'])
def delete_device(id):
    device = Device.query.get(id)
    if device:
        db.session.delete(device)
        db.session.commit()
        return jsonify({"message": "Device deleted"}), 200
    return jsonify({"error": "Device not found"}), 404

########## Fault Management ##########
@app.route('/api/faults', methods=['GET'])
def get_faults():
    status = request.args.get('status')
    severity = request.args.get('severity')
    query = Fault.query
    if status:
        query = query.filter_by(status=status)
    if severity:
        query = query.filter_by(severity=severity)
    faults = query.order_by(Fault.timestamp.desc()).all()
    resp = []
    for f in faults:
        device = Device.query.filter_by(device_id=f.device_id).first()
        assigned = Lineman.query.get(f.assigned_to) if f.assigned_to else None
        resp.append({
            "id": f.id,
            "device_id": f.device_id,
            "location": {"lat": device.latitude, "lng": device.longitude} if device else {},
            "fault_type": f.fault_type,
            "severity": f.severity,
            "timestamp": f.timestamp.isoformat(),
            "status": f.status,
            "assigned_to": assigned.name if assigned else None,
            "resolved_at": f.resolved_at.isoformat() if f.resolved_at else None,
        })
    return jsonify(resp), 200

@app.route('/api/faults', methods=['POST'])
def create_fault():
    data = request.get_json()
    try:
        required = ("device_id", "fault_type", "timestamp", "sensor_value")
        if not all(k in data for k in required):
            raise ValueError("Missing fields")
        # Example: Determine severity from sensor_value
        val = float(data["sensor_value"])
        if val > 10: severity = "critical"
        elif val > 7: severity = "high"
        elif val > 4: severity = "medium"
        else: severity = "low"
        new_fault = Fault(
            device_id=data["device_id"],
            fault_type=data["fault_type"],
            severity=severity,
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.utcnow(),
            status="detected"
        )
        db.session.add(new_fault)
        db.session.commit()
        notify_clients("new_fault", {"device_id": new_fault.device_id, "severity": new_fault.severity})
        return jsonify({"message": "Fault recorded"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/faults/<int:id>', methods=['PUT'])
def update_fault_status(id):
    data = request.get_json()
    status = data.get("status")
    fault = Fault.query.get(id)
    if fault and status in ["assigned", "in-progress", "resolved"]:
        fault.status = status
        if status == "resolved":
            fault.resolved_at = datetime.utcnow()
        db.session.commit()
        notify_clients("fault_update", {"id": fault.id, "status": fault.status})
        return jsonify({"message": "Fault status updated"}), 200
    return jsonify({"error": "Bad request"}), 400

@app.route('/api/faults/<int:id>/assign', methods=['POST'])
def assign_fault(id):
    data = request.get_json()
    lineman_id = data.get("assigned_to")
    fault = Fault.query.get(id)
    lineman = Lineman.query.get(lineman_id)
    if fault and lineman:
        fault.assigned_to = lineman_id
        fault.status = "assigned"
        db.session.commit()
        notify_clients("fault_assigned", {"id": fault.id, "assigned_to": lineman_id})
        return jsonify({"message": "Fault assigned"}), 200
    return jsonify({"error": "Bad request"}), 400

########## Lineman Management ##########
@app.route('/api/linemen', methods=['GET'])
def get_linemen():
    linemen = Lineman.query.all()
    return jsonify([{
        "id": l.id,
        "name": l.name,
        "contact": l.contact,
        "assigned_area": l.assigned_area,
        "status": l.status,
        "created_at": l.created_at.isoformat()
    } for l in linemen]), 200

@app.route('/api/linemen', methods=['POST'])
def register_lineman():
    data = request.get_json()
    try:
        required = ("name", "contact", "assigned_area")
        if not all(k in data for k in required):
            raise ValueError("Missing fields")
        new_lineman = Lineman(
            name=data["name"],
            contact=data["contact"],
            assigned_area=data["assigned_area"],
            status="available"
        )
        db.session.add(new_lineman)
        db.session.commit()
        notify_clients("lineman_update", {"id": new_lineman.id, "status": "available"})
        return jsonify({"message": "Lineman registered"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/linemen/<int:id>', methods=['PUT'])
def update_lineman_status(id):
    data = request.get_json()
    status = data.get("status")
    lineman = Lineman.query.get(id)
    if lineman and status in ["available", "busy", "offline"]:
        lineman.status = status
        db.session.commit()
        notify_clients("lineman_update", {"id": lineman.id, "status": lineman.status})
        return jsonify({"message": "Lineman status updated"}), 200
    return jsonify({"error": "Bad request"}), 400

@app.route('/api/linemen/<int:id>', methods=['DELETE'])
def delete_lineman(id):
    lineman = Lineman.query.get(id)
    if lineman:
        db.session.delete(lineman)
        db.session.commit()
        notify_clients("lineman_update", {"id": id, "status": "deleted"})
        return jsonify({"message": "Lineman deleted"}), 200
    return jsonify({"error": "Lineman not found"}), 404

########## ESP8266 Hardware Integration ##########
@app.route('/api/hardware/alert', methods=['POST'])
def hardware_alert():
    data = request.get_json()
    try:
        required = ("device_id", "fault_type", "sensor_value")
        if not all(k in data for k in required):
            raise ValueError("Missing fields")
        data['timestamp'] = data.get('timestamp', datetime.utcnow().isoformat())
        # Forward fault creation to standard endpoint
        with app.test_request_context():
            request_json = request.get_json(force=True)
            return create_fault()
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from models import db, Device, Fault, Lineman
from config import config
from datetime import datetime
import re

app = Flask(__name__)
app.config.from_object(config['default'])

# Initialize extensions
db.init_app(app)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Validation functions
def validate_device_id(device_id):
    return re.match(r'^device\d{4}$', device_id) is not None

def validate_coordinates(lat, lng):
    return -90 <= lat <= 90 and -180 <= lng <= 180

def validate_date(date_str):
    try:
        datetime.strptime(date_str, '%d/%m/%Y')
        return True
    except ValueError:
        return False

def calculate_severity(sensor_value):
    if sensor_value < 2.0:
        return 'low'
    elif 2.0 <= sensor_value < 4.0:
        return 'medium'
    elif 4.0 <= sensor_value < 6.0:
        return 'high'
    else:
        return 'critical'

# API Routes
@app.route('/api/devices', methods=['GET'])
def get_devices():
    try:
        status_filter = request.args.get('status')
        query = Device.query
        if status_filter in ['active', 'inactive']:
            query = query.filter(Device.status == status_filter)
        
        devices = query.all()
        return jsonify([device.to_dict() for device in devices])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/devices', methods=['POST'])
def create_device():
    try:
        data = request.get_json()
        
        if not all(k in data for k in ['device_id', 'latitude', 'longitude', 'installation_date']):
            return jsonify({'error': 'Missing required fields'}), 400
        
        if not validate_device_id(data['device_id']):
            return jsonify({'error': 'Invalid device ID format. Must be like device0001'}), 400
        
        if not validate_coordinates(data['latitude'], data['longitude']):
            return jsonify({'error': 'Invalid coordinates'}), 400
        
        if not validate_date(data['installation_date']):
            return jsonify({'error': 'Invalid date format. Use DD/MM/YYYY'}), 400
        
        if Device.query.filter_by(device_id=data['device_id']).first():
            return jsonify({'error': 'Device ID already exists'}), 400
        
        device = Device(
            device_id=data['device_id'],
            latitude=data['latitude'],
            longitude=data['longitude'],
            installation_date=data['installation_date'],
            status=data.get('status', 'active')
        )
        
        db.session.add(device)
        db.session.commit()
        
        socketio.emit('device_created', device.to_dict())
        return jsonify(device.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/devices/<int:device_id>', methods=['PUT'])
def update_device(device_id):
    try:
        device = Device.query.get_or_404(device_id)
        data = request.get_json()
        
        if 'status' in data and data['status'] in ['active', 'inactive']:
            device.status = data['status']
        
        db.session.commit()
        socketio.emit('device_updated', device.to_dict())
        return jsonify(device.to_dict())
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/devices/<int:device_id>', methods=['DELETE'])
def delete_device(device_id):
    try:
        device = Device.query.get_or_404(device_id)
        db.session.delete(device)
        db.session.commit()
        
        socketio.emit('device_deleted', {'id': device_id})
        return jsonify({'message': 'Device deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/faults', methods=['GET'])
def get_faults():
    try:
        status_filter = request.args.get('status')
        severity_filter = request.args.get('severity')
        
        query = Fault.query
        if status_filter in ['detected', 'assigned', 'in-progress', 'resolved']:
            query = query.filter(Fault.status == status_filter)
        if severity_filter in ['low', 'medium', 'high', 'critical']:
            query = query.filter(Fault.severity == severity_filter)
        
        faults = query.order_by(Fault.timestamp.desc()).all()
        return jsonify([fault.to_dict() for fault in faults])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/faults', methods=['POST'])
def create_fault():
    try:
        data = request.get_json()
        
        if not all(k in data for k in ['device_id', 'fault_type']):
            return jsonify({'error': 'Missing required fields'}), 400
        
        device = Device.query.filter_by(device_id=data['device_id']).first()
        if not device:
            return jsonify({'error': 'Device not found'}), 404
        
        fault = Fault(
            device_id=device.id,
            fault_type=data['fault_type'],
            severity=data.get('severity', calculate_severity(data.get('sensor_value', 0))),
            status='detected'
        )
        
        db.session.add(fault)
        db.session.commit()
        
        fault_data = fault.to_dict()
        socketio.emit('fault_detected', fault_data)
        return jsonify(fault_data), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/faults/<int:fault_id>', methods=['PUT'])
def update_fault(fault_id):
    try:
        fault = Fault.query.get_or_404(fault_id)
        data = request.get_json()
        
        if 'status' in data and data['status'] in ['detected', 'assigned', 'in-progress', 'resolved']:
            fault.status = data['status']
            if data['status'] == 'resolved':
                fault.resolved_at = datetime.utcnow()
        
        db.session.commit()
        
        fault_data = fault.to_dict()
        socketio.emit('fault_updated', fault_data)
        return jsonify(fault_data)
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/faults/<int:fault_id>/assign', methods=['POST'])
def assign_fault(fault_id):
    try:
        fault = Fault.query.get_or_404(fault_id)
        data = request.get_json()
        
        if 'lineman_id' not in data:
            return jsonify({'error': 'Lineman ID required'}), 400
        
        lineman = Lineman.query.get(data['lineman_id'])
        if not lineman:
            return jsonify({'error': 'Lineman not found'}), 404
        
        fault.assigned_to = lineman.id
        fault.status = 'assigned'
        lineman.status = 'busy'
        
        db.session.commit()
        
        fault_data = fault.to_dict()
        socketio.emit('fault_assigned', fault_data)
        socketio.emit('lineman_updated', lineman.to_dict())
        return jsonify(fault_data)
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/linemen', methods=['GET'])
def get_linemen():
    try:
        status_filter = request.args.get('status')
        query = Lineman.query
        
        if status_filter in ['available', 'busy', 'offline']:
            query = query.filter(Lineman.status == status_filter)
        
        linemen = query.all()
        return jsonify([lineman.to_dict() for lineman in linemen])
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/linemen', methods=['POST'])
def create_lineman():
    try:
        data = request.get_json()
        
        if not all(k in data for k in ['name', 'contact', 'assigned_area']):
            return jsonify({'error': 'Missing required fields'}), 400
        
        lineman = Lineman(
            name=data['name'],
            contact=data['contact'],
            assigned_area=data['assigned_area'],
            status=data.get('status', 'available')
        )
        
        db.session.add(lineman)
        db.session.commit()
        
        socketio.emit('lineman_created', lineman.to_dict())
        return jsonify(lineman.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/linemen/<int:lineman_id>', methods=['PUT'])
def update_lineman(lineman_id):
    try:
        lineman = Lineman.query.get_or_404(lineman_id)
        data = request.get_json()
        
        if 'status' in data and data['status'] in ['available', 'busy', 'offline']:
            lineman.status = data['status']
        
        db.session.commit()
        socketio.emit('lineman_updated', lineman.to_dict())
        return jsonify(lineman.to_dict())
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/linemen/<int:lineman_id>', methods=['DELETE'])
def delete_lineman(lineman_id):
    try:
        lineman = Lineman.query.get_or_404(lineman_id)
        
        # Unassign all faults assigned to this lineman
        Fault.query.filter_by(assigned_to=lineman_id).update({'assigned_to': None, 'status': 'detected'})
        
        db.session.delete(lineman)
        db.session.commit()
        
        socketio.emit('lineman_deleted', {'id': lineman_id})
        return jsonify({'message': 'Lineman deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/hardware/alert', methods=['POST'])
def hardware_alert():
    try:
        data = request.get_json()
        
        if not all(k in data for k in ['device_id', 'fault_type']):
            return jsonify({'error': 'Missing required fields'}), 400
        
        device = Device.query.filter_by(device_id=data['device_id']).first()
        if not device:
            return jsonify({'error': 'Device not registered'}), 404
        
        fault = Fault(
            device_id=device.id,
            fault_type=data['fault_type'],
            severity=calculate_severity(data.get('sensor_value', 0)),
            status='detected',
            timestamp=datetime.utcnow()
        )
        
        db.session.add(fault)
        db.session.commit()
        
        fault_data = fault.to_dict()
        socketio.emit('fault_detected', fault_data)
        return jsonify({'message': 'Fault recorded successfully', 'fault_id': fault.id}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/linemen/<int:lineman_id>/faults', methods=['GET'])
def get_lineman_faults(lineman_id):
    try:
        faults = Fault.query.filter_by(assigned_to=lineman_id).order_by(Fault.timestamp.desc()).all()
        return jsonify([fault.to_dict() for fault in faults])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# SocketIO events
@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('connected', {'data': 'Connected to fault detection system'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)