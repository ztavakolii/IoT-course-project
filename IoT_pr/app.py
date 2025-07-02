from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
from models import db, User, Desk, Session, Alert,Device,Zone
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from Qr_code_reader import read_qr
import os
from werkzeug.utils import secure_filename
import requests

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'SECRETE'
db.init_app(app)
CORS(app)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

pending_commands = {}

AUTHORIZED_DEVICES = {
    "A1": "abc123",
    "A2": "def456",
    "A": "ghi789"
}
desk_ip_map = {
    "A1": "http://192.168.75.106:80",
    "A2": "http://192.168.1.:80",
    "A": "http://192.168.75.222:80"
}

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
    user = User(student_number=student_number, password_hash=password_hash, full_name=full_name,point=0)
    db.session.add(user)
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'User registered'})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    student_number = data.get('student_number')
    password = data.get('password')

    if not student_number or not password:
        return jsonify({'status': 'fail', 'message': 'Student number and password required'}), 400

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
    else:
        return jsonify({'status': 'fail', 'message': 'Invalid credentials'}), 401

@app.route('/checkin_qr', methods=['POST'])
def checkin_qr():
    user_id = request.form.get('user_id')
    qr_data = None

    if 'qr_data' in request.form:
        qr_data = request.form['qr_data']
    elif 'file' in request.files:
        file = request.files['file']
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        qr_data = read_qr(filepath)
        os.remove(filepath)
    else:
        return jsonify({'status': 'fail', 'message': 'Missing file or qr_data'}), 400

    if not qr_data:
        return jsonify({'status': 'fail', 'message': 'QR code not detected'}), 400
    
    try:
        zone, desk_id = None, None
        parts = qr_data.split(';')
        for part in parts:
            key, value = part.split(':')
            if key.strip() == 'zone':
                zone = value.strip()
            elif key.strip() == 'desk':
                desk_id = value.strip()

        if not ((desk_id == "1" or desk_id == "2") and zone == "A"):
            return jsonify({'status': 'fail', 'message': 'Invalid QR format'}), 400

        user = User.query.get(user_id)



        if desk_id=="1":
            desk = Desk.query.get(int(1))
            desk_ip=desk_ip_map['A1']
            token=AUTHORIZED_DEVICES['A1']
        else:
            desk = Desk.query.get(int(2))
            desk_ip=desk_ip_map['A2']
            token=AUTHORIZED_DEVICES['A2']

        print(desk,user)
        if not user or not desk:
            return jsonify({'status': 'fail', 'message': 'User or Desk not found'}), 404

#        try:
#           requests.post(f"{desk_ip}/reserve", json={"token": token})

#        except Exception as e:
#            print(f"Failed to notify desk {desk_id}: {e}")
#            return jsonify({'status': 'fail', 'message': str(e)}), 500

        ses = Session(user_id=user.id, desk_id=desk.id, start_time=datetime.utcnow(),end_time=None)
        db.session.add(ses)
        desk.status = 'occupied'
        desk.last_present_time = datetime.utcnow()
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Checked in via QR', 'session_id': ses.id})


    except Exception as e:
        return jsonify({'status': 'fail', 'message': str(e)}), 500

@app.route('/checkout', methods=['POST'])
def checkout():
    data = request.json
    session_id = data.get('session_id')

    if not session_id:
        return jsonify({'status': 'fail', 'message': 'session_id required'}), 400

    session = Session.query.get(session_id)
    if not session:
        return jsonify({'status': 'fail', 'message': 'Session not found'}), 404

    if session.end_time is not None:
        return jsonify({'status': 'fail', 'message': 'Session already checked out'}), 400

    session.end_time = datetime.utcnow()

    desk = Desk.query.get(session.desk_id)
    if desk:        
        if session.desk_id==1:
            desk_ip=desk_ip_map['A1']
            token=AUTHORIZED_DEVICES['A1']
        else:
            desk_ip=desk_ip_map['A2']
            token=AUTHORIZED_DEVICES['A2']

        try:
            requests.post(f"{desk_ip}/release", json={"token": token})
            desk.status = 'free'
        except Exception as e:
            print(f"Failed to notify desk {desk.id}: {e}")

    user = User.query.get(session.user_id)
    if user:
        user.point = user.point + 500


    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Checked out'})

#@app.route('/violation', methods=['POST'])
#def add_violation():
#    data = request.json
#    user_id = data.get('user_id')
#    desk_id = data.get('desk_id')
#    violation_type = data.get('type')
#   zone_id = data.get('zone_id')
#    session_id = data.get('session_id')

#    if not user_id or not desk_id or not violation_type or not zone_id:
#       return jsonify({'status': 'fail', 'message': 'Missing parameters'}), 400
#
#    alert = Alert(
#        alert_type=violation_type,
#        desk_id=desk_id,
#        zone_id=zone_id,
#        session_id=session_id,
#        time=datetime.utcnow()
#    )
#   db.session.add(alert)
#   db.session.commit()
#    return jsonify({'status': 'success', 'message': 'Violation recorded'})

@app.route('/sensor-data', methods=['POST'])
def receive_sensor_data():
    try:
        data = request.json
        token = data.get("token")
        alert_type = data.get("type")

        if not token or not alert_type:
            return jsonify({'status': 'fail', 'message': 'Missing parameters'}), 400

        desk_id=0
        for id , tok in AUTHORIZED_DEVICES.items():
            if tok==token:
                desk_id=id

        if desk_id== 0:
            return jsonify({'status': 'fail', 'message': 'Unauthorized'}), 401

        if AUTHORIZED_DEVICES.get(desk_id) != token:
            return jsonify({'status': 'fail', 'message': 'Unauthorized'}), 401

        if alert_type == "motion":
            session = Session.query.filter_by(desk_id=desk_id, end_time=None).first()
            if session:
                session.end_time = datetime.utcnow()

                user = User.query.get(session.user_id)
                if user:
                    user.point = max(user.point - 100, 0)  
                desk = Desk.query.get(desk_id)
                if desk:
                    desk.status = 'free'

                    if desk_id == "1":
                        desk_ip = desk_ip_map['A1']
                        token = AUTHORIZED_DEVICES['A1']
                    else:
                        desk_ip = desk_ip_map['A2']
                        token = AUTHORIZED_DEVICES['A2']

                    try:
                        requests.post(f"{desk_ip}/release", json={"token": token})
                    except Exception as e:
                        print(f"Failed to notify desk {desk_id}: {e}")

                violation_alert = Alert(
                    alert_type="user_left_without_checkout",
                    desk_id=desk_id,
                    time=datetime.utcnow(),
                    session_id=session.id
                )
                db.session.add(violation_alert)
                        
                db.session.commit()
            
                return jsonify({'status': 'success', 'message': 'Alert recorded'})
            else:
                return jsonify({'status': 'fail', 'message': 'No active session'}), 400
        elif alert_type == "sound":
            for id in [1,2]:
                desk_id=id
                session = Session.query.filter_by(desk_id=desk_id, end_time=None).first()
                if session:
                    session.end_time = datetime.utcnow()

                    user = User.query.get(session.user_id)
                    if user:
                        user.point = max(user.point - 100, 0)  
                        violation_alert = Alert(
                            alert_type="loud_voice",
                            desk_id=desk_id,
                            time=datetime.utcnow(),
                            session_id=session.id
                        )
                        
                        db.session.add(violation_alert)
                    if desk_id==1:
                        ip=desk_ip_map['A1']
                        d_token=AUTHORIZED_DEVICES['A1']
                        d_id='A1'
                    else:
                        ip=desk_ip_map['A2']
                        d_token=AUTHORIZED_DEVICES['A2']
                        d_id='A2'

                    try:
                        requests.post(f"{ip}/buzz", json={"token": d_token})
                    except Exception as e:
                        print(f"Failed to buzz desk {d_id}: {e}")
            
                    db.session.commit()
                    return jsonify({'status': 'success', 'message': 'Alert recorded'})
                else:
                    return jsonify({'status': 'fail', 'message': 'No active session'}), 400

            else:
                temperature = data.get("temperature")
                ppm = data.get("ppm")
                for id in [1,2]:
                    desk_id=id      
                    desk = Desk.query.get(int(desk_id))
                    if desk:
                        db.session.commit()
                    return jsonify({'status': 'success', 'message': 'Environment data recorded'})

    except Exception as e:
        return jsonify({'status': 'fail', 'message': str(e)}), 500


@app.route('/desk-data')
def get_user_desk_data():
    user_id = session.get("user_id")
    if not user_id:
        print("user")
        return jsonify({"status": "fail", "message": "Unauthorized"}), 401
    print(user_id)
    active_session = Session.query.filter_by(user_id=user_id, end_time=None).first()
    if not active_session:
        print("sess")

        return jsonify([])
    print(active_session)

    desk = Desk.query.get(active_session.desk_id)
    if not desk:
        print("desk")

        return jsonify([])

    result = {
        "id": desk.id,
        "zone": desk.zone.name if desk.zone else "",
        "comment": desk.comment,
    }
    print(result)
    return jsonify(result)    

@app.route('/alerts/<int:user_id>', methods=['GET'])
def get_user_alerts(user_id):
    sessions = Session.query.filter_by(user_id=user_id).all()
    session_ids = [s.id for s in sessions]
    alerts = Alert.query.filter(Alert.session_id.in_(session_ids)).order_by(Alert.time.desc()).limit(3).all()

    alert_data = []
    for alert in alerts:
        msg = "صدای غیرمجاز شناسایی شد." if "sound" in alert.alert_type else "کاربر بدون خروج ترک کرد."
        alert_data.append({
            "type": alert.alert_type,
            "message": msg,
            "time": alert.time.isoformat()
        })

    return jsonify({"alerts": alert_data})



if __name__ == '__main__':
    with app.app_context():
        db.create_all()

app.run(host='0.0.0.0',port=5000,debug=True)
