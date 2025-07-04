from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
from models import db, User, Desk, Session as UserSession, Alert, Zone
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from Qr_code_reader import read_qr, read_qr_opencv
import os
from werkzeug.utils import secure_filename
import json
import threading
import paho.mqtt.client as mqtt

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'SECRETE'
db.init_app(app)
CORS(app)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

BROKER = "mqtt.thingsboard.cloud"
PORT = 1883
ACCESS_TOKEN = "R5GcQQoauXKrh6kQ8ip0"

mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(ACCESS_TOKEN)

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(" MQTT connected")
        client.subscribe("v1/devices/+/telemetry")
    else:
        print("MQTT connection failed", rc)

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        topic = msg.topic
        device_id = topic.split('/')[2]  
        alert_type = data.get("type")

        desk_id = 1 if device_id == "A1" else 2 if device_id == "A2" else None
        if not desk_id:
            return

        if alert_type == "motion":
            session = UserSession.query.filter_by(desk_id=desk_id, end_time=None).first()
            if session:
                session.end_time = datetime.utcnow()
                user = User.query.get(session.user_id)
                if user:
                    user.point = max(user.point - 100, 0)
                desk = Desk.query.get(desk_id)
                if desk:
                    desk.status = 'free'
                alert = Alert(alert_type="user_left_without_checkout", desk_id=desk_id, time=datetime.utcnow(), session_id=session.id)
                db.session.add(alert)
                db.session.commit()

        elif alert_type == "sound":
            for desk_id in [1, 2]:
                session = UserSession.query.filter_by(desk_id=desk_id, end_time=None).first()
                if session:
                    user = User.query.get(session.user_id)
                    if user:
                        user.point = max(user.point - 100, 0)
                    alert = Alert(alert_type="loud_voice", desk_id=desk_id, time=datetime.utcnow(), session_id=session.id)
                    db.session.add(alert)
            db.session.commit()

        elif "temperature" in data or "ppm" in data:
            for desk_id in [1, 2]:
                desk = Desk.query.get(desk_id)
                if desk:
                    desk.comment = f"Temp: {data.get('temperature')}°C, PPM: {data.get('ppm')}"
            db.session.commit()

    except Exception as e:
        print("MQTT Error:", e)

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(BROKER, PORT, 60)
mqtt_thread = threading.Thread(target=mqtt_client.loop_forever)
mqtt_thread.start()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def signup():
    data = request.json
    student_number = data.get('student_number')
    password = data.get('password')
    full_name = data.get('full_name', '')

    if not student_number or not password:
        return jsonify({'status': 'fail', 'message': 'Student number and password required'}), 400

    if User.query.filter_by(student_number=student_number).first():
        return jsonify({'status': 'fail', 'message': 'User already exists'}), 409

    password_hash = generate_password_hash(password)
    user = User(student_number=student_number, password_hash=password_hash, full_name=full_name, point=0)
    db.session.add(user)
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'User registered'})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    student_number = data.get('student_number')
    password = data.get('password')

    user = User.query.filter_by(student_number=student_number).first()
    if user and check_password_hash(user.password_hash, password):
        session['user_id'] = user.id
        return jsonify({
            'status': 'success',
            'user_id': user.id,
            'full_name': user.full_name,
            'student_number': user.student_number,
            'score': user.point
        })
    return jsonify({'status': 'fail', 'message': 'Invalid credentials'}), 401

@app.route('/checkin_qr', methods=['POST'])
def checkin_qr():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'status': 'fail', 'message': 'Not authenticated'}), 401

    file = request.files['file']
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    qr_data = read_qr(filepath) or read_qr_opencv(filepath)
    os.remove(filepath)
    if not qr_data:
        return jsonify({'status': 'fail', 'message': 'Invalid QR'}), 400

    try:
        zone, desk_id = None, None
        for part in qr_data.split(';'):
            if ':' in part:
                k, v = part.split(':')
                if k.strip() == 'zone': zone = v.strip()
                elif k.strip() == 'desk': desk_id = v.strip()

        desk_id = int(desk_id)
        user = User.query.get(user_id)
        desk = Desk.query.get(desk_id)
        if not user or not desk:
            return jsonify({'status': 'fail', 'message': 'User or Desk not found'}), 404

        session_obj = UserSession(user_id=user.id, desk_id=desk.id, start_time=datetime.utcnow())
        db.session.add(session_obj)
        desk.status = 'occupied'
        db.session.commit()

        mqtt_client.publish(f"v1/devices/{desk_id}/rpc/request/1", json.dumps({"method": "reserve"}))

        session['session_id'] = session_obj.id
        session['desk_id'] = desk.id

        return jsonify({'status': 'success', 'message': 'Checked in', 'session_id': session_obj.id})

    except Exception as e:
        return jsonify({'status': 'fail', 'message': str(e)}), 500

@app.route('/checkout', methods=['POST'])
def checkout():
    session_id = session.get("session_id")
    if not session_id:
        return jsonify({'status': 'fail', 'message': 'Not checked in'}), 400

    session_obj = UserSession.query.get(session_id)
    if session_obj:
        session_obj.end_time = datetime.utcnow()
        desk = Desk.query.get(session_obj.desk_id)
        if desk:
            desk.status = 'free'
            mqtt_client.publish(f"v1/devices/{desk.id}/rpc/request/1", json.dumps({"method": "release"}))

        user = User.query.get(session_obj.user_id)
        if user:
            user.point += 500

        db.session.commit()

    session.pop("session_id", None)
    session.pop("desk_id", None)

    return jsonify({'status': 'success', 'message': 'Checked out'})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)