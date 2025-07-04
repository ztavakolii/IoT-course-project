from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_number = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    full_name = db.Column(db.String(100))
    point = db.Column(db.Integer, default=0)
    signup_date = db.Column(db.DateTime, default=datetime.utcnow)

class Zone(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))

    temperature_sensor_id = db.Column(db.Integer, db.ForeignKey('device.id'))
    pollution_sensor_id = db.Column(db.Integer, db.ForeignKey('device.id'))
    sound_sensor_id = db.Column(db.Integer, db.ForeignKey('device.id'))

    temperature_sensor = db.relationship('Device', foreign_keys=[temperature_sensor_id])
    pollution_sensor = db.relationship('Device', foreign_keys=[pollution_sensor_id])
    sound_sensor = db.relationship('Device', foreign_keys=[sound_sensor_id])



class Desk(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    zone_id = db.Column(db.Integer, db.ForeignKey('zone.id'))
    zone = db.relationship('Zone', backref='desks')
    status = db.Column(db.String(20))  # e.g., 'free', 'occupied'
    sensor_id = db.Column(db.String(50))
    last_present_time = db.Column(db.DateTime)
    comment = db.Column(db.Text)

class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    desk_id = db.Column(db.Integer, db.ForeignKey('desk.id'))
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    is_qr_scanned = db.Column(db.Boolean, default=False)
    has_alerts = db.Column(db.Boolean, default=False)
    point = db.Column(db.Integer, default=0)
    user = db.relationship('User', backref='sessions')
    desk = db.relationship('Desk', backref='sessions')

class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    alert_type = db.Column(db.String(50))  # e.g., 'motion'
    desk_id = db.Column(db.Integer, db.ForeignKey('desk.id'), nullable=True)
    session_id = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=True)
    zone_id = db.Column(db.Integer, db.ForeignKey('zone.id'))
    time = db.Column(db.DateTime, default=datetime.utcnow)

    desk = db.relationship('Desk', backref='alerts')
    session = db.relationship('Session', backref='alerts')
    zone = db.relationship('Zone', backref='alerts')

class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    kind = db.Column(db.String(50))  
    zone_id = db.Column(db.Integer, db.ForeignKey('zone.id'))
    desk_id = db.Column(db.Integer, db.ForeignKey('desk.id'), nullable=True)
    status = db.Column(db.String(20))  
    last_message = db.Column(db.Text)
    last_message_time = db.Column(db.DateTime)

    zone = db.relationship('Zone', backref='devices', foreign_keys=[zone_id])
    desk = db.relationship('Desk', backref='devices', foreign_keys=[desk_id])
