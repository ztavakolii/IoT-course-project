from flask import Flask, request, jsonify,render_template
from flask_cors import CORS
from models import db, User, Desk, Session, Alert, Device, Zone
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from Qr_code_reader import read_qr
import os 
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
CORS(app)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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
    user = User(student_number=student_number, password_hash=password_hash, full_name=full_name)
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
        return jsonify({
            'status': 'success',
            'user_id': user.id,
            'full_name': user.full_name,
            'student_number': user.student_number
        })
    else:
        return jsonify({'status': 'fail', 'message': 'Invalid credentials'}), 401

@app.route('/checkin_qr', methods=['POST'])
def checkin_qr():
    if 'file' not in request.files or 'user_id' not in request.form:
        return jsonify({'status': 'fail', 'message': 'Missing file or user_id'}), 400

    file = request.files['file']
    user_id = request.form['user_id']
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    qr_data = read_qr(filepath)
    os.remove(filepath)

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
        print(desk_id,zone)

        if not ((desk_id=="1" or desk_id =="2") and zone=="A"):
            return jsonify({'status': 'fail', 'message': 'Invalid QR format'}), 400

        user = User.query.get(user_id)
        desk = Desk.query.get(desk_id)

        if not user or not desk:
            return jsonify({'status': 'fail', 'message': 'User or Desk not found'}), 404

        session = Session(user_id=user.id, desk_id=desk.id, start_time=datetime.utcnow())
        db.session.add(session)
        desk.status = 'occupied'
        desk.last_present_time = datetime.utcnow()
        db.session.commit()

        return jsonify({'status': 'success', 'message': 'Checked in via QR', 'session_id': session.id})
    
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
        desk.status = 'free'

    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Checked out'})

@app.route('/violation', methods=['POST'])
def add_violation():
    data = request.json
    user_id = data.get('user_id')
    desk_id = data.get('desk_id')
    violation_type = data.get('type')
    zone_id = data.get('zone_id')
    session_id = data.get('session_id')  

    if not user_id or not desk_id or not violation_type or not zone_id:
        return jsonify({'status': 'fail', 'message': 'Missing parameters'}), 400

    alert = Alert(
        alert_type=violation_type,
        desk_id=desk_id,
        zone_id=zone_id,
        session_id=session_id,
        time=datetime.utcnow()
    )
    db.session.add(alert)
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Violation recorded'})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
