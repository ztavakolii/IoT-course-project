from flask import Flask, request, jsonify, render_template, session
from flask_cors import CORS
from models import db, User, Desk, Session, Alert,Device,Zone
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from Qr_code_reader import read_qr,read_qr_opencv
import os
from werkzeug.utils import secure_filename
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

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
    user_id = session.get('user_id')
    if not user_id :
        return jsonify({'status': 'fail', 'message': 'Invalid or missing user_id'}), 400

    user = User.query.get(int(user_id))
    if not user:
        return jsonify({'status': 'fail', 'message': 'User not found'}), 404

    # Handle QR data or file upload
    qr_data = None
    if 'qr_data' in request.form:
        qr_data = request.form['qr_data']
    elif 'file' in request.files:
        file = request.files['file']
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        try:
            file.save(filepath)
            qr_data = read_qr(filepath)
            if not qr_data:
                qr_data=read_qr_opencv(filepath)
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)
    else:
        return jsonify({'status': 'fail', 'message': 'Missing file or qr_data'}), 400

    if not qr_data:
        return jsonify({'status': 'fail', 'message': 'QR code not detected'}), 400

    # Parse QR data
    try:
        zone, desk_id = None, None
        parts = qr_data.split(';')
        for part in parts:
            if ':' not in part:
                continue
            key, value = part.split(':', 1)
            key, value = key.strip(), value.strip()
            if key == 'zone':
                zone = value
            elif key == 'desk':
                desk_id = value

        if not zone or not desk_id:
            return jsonify({'status': 'fail', 'message': 'Invalid QR format: missing zone or desk'}), 400
        print("desk:")
        print(desk_id)
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

        try:
            requests.post(f"{desk_ip}/reserve", json={"token": token})

        except Exception as e:
           print(f"Failed to notify desk {desk_id}: {e}")
           return jsonify({'status': 'fail', 'message': str(e)}), 500
           
        ses = Session(user_id=user.id, desk_id=desk.id, start_time=datetime.now(ZoneInfo("Asia/Tehran")),end_time=None)
        db.session.add(ses)
        desk.status = 'occupied'
        db.session.commit()
        session["desk_id"] = desk.id
        session["session_id"] = ses.id
        print("check:")
        print(desk.id)
        return jsonify({'status': 'success', 'message': 'Checked in via QR', 'session_id': ses.id})

    except Exception as e:
        return jsonify({'status': 'fail', 'message': str(e)}), 500
        

@app.route('/checkout', methods=['POST'])
def checkout():
    session_id = session.get("session_id")  
    if not session_id:
        return jsonify({'status': 'fail', 'message': 'session_id required'}), 400

    ses = Session.query.get(session_id)
    if not ses:
        return jsonify({'status': 'fail', 'message': 'Session not found'}), 404


    ses.end_time = datetime.now(ZoneInfo("Asia/Tehran"))
    print(ses.end_time)
    desk = Desk.query.get(ses.desk_id)
    if desk:        
        if ses.desk_id==1:
            desk_ip=desk_ip_map['A1']
            token=AUTHORIZED_DEVICES['A1']
        else:
            desk_ip=desk_ip_map['A2']
            token=AUTHORIZED_DEVICES['A2']

        try:
           requests.post(f"{desk_ip}/release", json={"token": token})
        except Exception as e:
           print(f"Failed to notify desk {desk.id}: {e}")
    desk.status = 'free'
    user = User.query.get(ses.user_id)
    if user:
        user.point = user.point + 500


    db.session.commit()
    session.pop("desk_id", None)
    session.pop("session_id", None)

    return jsonify({'status': 'success', 'message': 'Checked out'})
@app.route('/sensor-data', methods=['POST'])
def receive_sensor_data():
    try:
        data = request.json
        desk_id=data.get("desk_id")
        token = data.get("token")
        alert_type = data.get("type")

        if  not desk_id or not token or not alert_type:
            return jsonify({'status': 'fail', 'message': 'Missing parameters'}), 400

        if AUTHORIZED_DEVICES.get(desk_id) != token:
            return jsonify({'status': 'fail', 'message': 'Unauthorized'}), 401
        if desk_id == "A1":
            id=1
        elif desk_id=="A2":
            id=2
        if alert_type == "motion":
            sess = Session.query.filter_by(desk_id=id, end_time=None).first()
            if sess:
                sess.end_time = datetime.now(ZoneInfo("Asia/Tehran"))
                print(sess.user_id)
                user = User.query.get(sess.user_id)
                if user:
                    user.point = max(user.point - 100, 0)  
                desk = Desk.query.get(id)
                if desk:
                    desk.status = 'free'

                    if id == 1:
                        desk_ip = desk_ip_map['A1']
                        token = AUTHORIZED_DEVICES['A1']
                    else:
                        desk_ip = desk_ip_map['A2']
                        token = AUTHORIZED_DEVICES['A2']

                    # try:
                    #     requests.post(f"{desk_ip}/release", json={"token": token})
                    # except Exception as e:
                    #     print(f"Failed to notify desk {desk_id}: {e}")

                violation_alert = Alert(
                    alert_type="user_left_without_checkout",
                    desk_id=desk.id,
                    time=datetime.now(ZoneInfo("Asia/Tehran")),
                    session_id=sess.id
                )
                db.session.add(violation_alert)
                        
                db.session.commit()
                session.pop("desk_id", None)
                session.pop("session_id", None)
                return jsonify({'status': 'success', 'message': 'Alert recorded'})
            else:
                return jsonify({'status': 'fail', 'message': 'No active session'}), 400

        elif alert_type == "sound":
            temp = 0
            alerts = []
            for id in [1, 2]:
                desk_id = id
                session = Session.query.filter_by(desk_id=desk_id, end_time=None).first()
                if not session:
                    print(f"No active session for desk_id {desk_id}")
                    continue
                user = User.query.get(session.user_id)
                print(session.user_id)

                if not user:
                    print(f"No user found for session.user_id {session.user_id}")
                    continue
                user.point = max(user.point - 100, 0)
                violation_alert = Alert(
                    alert_type="loud_voice",
                    desk_id=desk_id,
                    time=datetime.now(ZoneInfo("Asia/Tehran")),
                    session_id=session.id
                )
                alerts.append(violation_alert)
                temp = 1
                print(f"Alert created: {violation_alert}")
                if int(desk_id) == 1:
                    ip = desk_ip_map['A1']
                    d_token = AUTHORIZED_DEVICES['A1']
                    d_id = 'A1'
                else:
                    ip = desk_ip_map['A2']
                    d_token = AUTHORIZED_DEVICES['A2']
                    d_id = 'A2'            
                try:
                    requests.post(f"{ip}/sound_alert", json={"token": d_token})
                except Exception as e:
                    print(f"Failed to buzz desk {d_id}: {e}")
            
            if alerts:
                    try:
                        for alert in alerts:
                            db.session.add(alert)
                        db.session.commit()
                        print("All alerts committed")
                        return jsonify({'status': 'success', 'message': 'Alert recorded'})
                    except Exception as e:
                        db.session.rollback()
                        print(f"Failed to commit alerts: {e}")
                        return jsonify({'status': 'fail', 'message': f'Database error: {str(e)}'}), 500
            else:
                    return jsonify({'status': 'fail', 'message': 'No active session'}), 400
                        
        else:
            temp=0
            temperature = data.get("temperature")
            ppm = data.get("ppm")
            for id in [1,2]:
                desk = Desk.query.get(int(id))
                if desk:
                    desk.comment = f"Temperature: {temperature}°C, PPM: {ppm}"
                    db.session.commit()
                    temp=1
            if temp:        
                return jsonify({'status': 'success', 'message': 'Environment data recorded'})
            else:        
                return jsonify({'status': 'fail', 'message':'error'}), 500


    except Exception as e:
        return jsonify({'status': 'fail', 'message': str(e)}), 500


@app.route('/desk-data')
def get_user_desk_data():
    user_id = session.get("user_id")
    if not user_id:
        print("user")
        return jsonify({"status": "fail", "message": "Unauthorized"}), 401
    print(user_id)
    active_session = Session.query.get(session.get("session_id"))
    if not active_session:
        print("sess")

        return jsonify([])
    print(active_session)
    desk = Desk.query.get(session.get("desk_id"))
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

@app.route('/alerts', methods=['GET'])
def get_user_alerts():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"status": "fail", "message": "Unauthorized"}), 401
    print(user_id)

    sessions = Session.query.filter_by(user_id=user_id).all()
    session_ids = [s.id for s in sessions]
    alerts = Alert.query.filter(Alert.session_id.in_(session_ids)).order_by(Alert.time.desc()).all()
    alert_data = []
    for alert in alerts:
        msg = "صدای بلند در ناحیه شناسایی شد." if "loud_voice" in alert.alert_type else "کاربر بدون خروج ترک کرد."
        alert_data.append({
            "type": alert.alert_type,
            "message": msg,
            "time": alert.time.isoformat()
        })
    return jsonify({"alerts": alert_data})

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()  # This clears all session data
    return jsonify({"message": "Logged out"})

@app.route('/me', methods=['GET'])
def get_current_user():
    user_id = session.get("user_id")
    print(F'user{session.get("user_id")}')

    if not user_id:
        return jsonify({"logged_in": False})

    user = User.query.get(user_id)
    session_id = session.get("session_id") 
    print(F'session_id{session.get("session_id")}')
 
    if not session_id:
        return jsonify({
            "logged_in": True,
            "full_name": user.full_name,
            "student_number": user.student_number,
            "score": user.point,
            "desk_id": None 
        })
    print(F'desk{session.get("desk_id")}')
    return jsonify({
        "logged_in": True,
        "full_name": user.full_name,
        "student_number": user.student_number,
        "score": user.point,
        "desk_id": session.get("desk_id")  
    })
    



if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    # from app import app, db
    # from models import Zone, Desk, Device

    # with app.app_context():
    #     db.drop_all()
    #     db.create_all()

    #     temp_sensor = Device(kind='Temperature', zone_id=None, status='online')
    #     sound_sensor = Device(kind='Sound', zone_id=None, status='online')
    #     pollution_sensor = Device(kind='Air Pollution', zone_id=None, status='online')

    #     db.session.add_all([temp_sensor, sound_sensor, pollution_sensor])
    #     db.session.commit()  

    #     zone_a = Zone(
    #         name='A',
    #         temperature_sensor_id=temp_sensor.id,
    #         sound_sensor_id=sound_sensor.id,
    #         pollution_sensor_id=pollution_sensor.id
    #     )
    #     db.session.add(zone_a)
    #     db.session.commit()

    #     desk1 = Desk(id=1, zone_id=zone_a.id, status='free', comment='Desk 1')
    #     desk2 = Desk(id=2, zone_id=zone_a.id, status='free', comment='Desk 2')
    #     db.session.add_all([desk1, desk2])
    #     db.session.commit()

    #     motion1 = Device(kind='Motion', zone_id=zone_a.id, desk_id=desk1.id, status='online')
    #     motion2 = Device(kind='Motion', zone_id=zone_a.id, desk_id=desk2.id, status='online')
    #     db.session.add_all([motion1, motion2])
    #     db.session.commit()

    #     print("Data seeded successfully!")


app.run(host='0.0.0.0',port=5000,debug=True)
