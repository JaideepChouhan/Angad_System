from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String, unique=True, nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    status = db.Column(db.String, nullable=False)  # "active"/"inactive"
    installation_date = db.Column(db.String, nullable=False)  # DD/MM/YYYY
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Lineman(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    contact = db.Column(db.String, nullable=False)
    assigned_area = db.Column(db.String, nullable=False)
    status = db.Column(db.String, nullable=False)  # "available"/"busy"/"offline"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Fault(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.String, db.ForeignKey('device.device_id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    fault_type = db.Column(db.String, nullable=False)
    severity = db.Column(db.String, nullable=False)  # "low"/"medium"/"high"/"critical"
    status = db.Column(db.String, nullable=False)  # "detected"/"assigned"/"in-progress"/"resolved"
    assigned_to = db.Column(db.Integer, db.ForeignKey('lineman.id'))  # nullable
    resolved_at = db.Column(db.DateTime)
