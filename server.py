from flask import Flask, jsonify, request, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import datetime
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import os
import io
import bcrypt

app = Flask(__name__)
@app.route('/')
def index():
    return jsonify({'message': 'School Server API is running. Use /api/... for endpoints.'}), 200

# Cấu hình
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///school.db')  # PostgreSQL trên Render
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET', 'your-secret-key')  # Đặt trên Render
db = SQLAlchemy(app)
jwt = JWTManager(app)

# Scheduler cho gửi mail
scheduler = BackgroundScheduler()
scheduler.start()

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)  # Lưu bcrypt hash
    school_id = db.Column(db.String(50), db.ForeignKey('school.id'), nullable=False)

class School(db.Model):
    id = db.Column(db.String(50), primary_key=True)  # ID trường
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    send_hour = db.Column(db.Integer, nullable=False)  # Giờ gửi mail (0-23)

class Student(db.Model):
    id = db.Column(db.String(50), primary_key=True)  # ID từ QR
    school_id = db.Column(db.String(50), db.ForeignKey('school.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    class_name = db.Column(db.String(50), nullable=False)
    birthdate = db.Column(db.String(20), nullable=False)
    gender = db.Column(db.String(10), nullable=False)

class ViolationType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.String(50), db.ForeignKey('school.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    points_deducted = db.Column(db.Integer, nullable=False)

class Violation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.String(50), db.ForeignKey('school.id'), nullable=False)
    student_id = db.Column(db.String(50), db.ForeignKey('student.id'), nullable=False)
    violation_type = db.Column(db.String(100), nullable=False)
    points_deducted = db.Column(db.Integer, nullable=False)
    violation_date = db.Column(db.DateTime, nullable=False)
    recorder_name = db.Column(db.String(100), nullable=False)
    recorder_class = db.Column(db.String(50), nullable=False)

# Tạo DB
with app.app_context():
    db.create_all()

# Hàm gửi mail báo cáo
def send_report_email(school_id):
    school = School.query.get(school_id)
    if not school:
        return

    violations = Violation.query.filter_by(school_id=school_id).all()
    if not violations:
        return

    data = [{
        'Học sinh': v.student.name,
        'Lớp': v.student.class_name,
        'Ngày sinh': v.student.birthdate,
        'Giới tính': v.student.gender,
        'Vi phạm': v.violation_type,
        'Điểm trừ': v.points_deducted,
        'Ngày vi phạm': v.violation_date.strftime('%Y-%m-%d %H:%M'),
        'Người ghi': v.recorder_name,
        'Lớp người ghi': v.recorder_class
    } for v in violations]
    df = pd.DataFrame(data)
    excel_buffer = io.BytesIO()
    df.to_excel(excel_buffer, index=False)
    excel_buffer.seek(0)

    msg = MIMEMultipart()
    msg['From'] = 'your-email@gmail.com'  # Thay bằng email của bạn
    msg['To'] = school.email
    msg['Subject'] = f'Báo cáo vi phạm - {school.name}'
    msg.attach(MIMEText('Đính kèm báo cáo vi phạm.', 'plain'))

    attachment = MIMEBase('application', 'octet-stream')
    attachment.set_payload(excel_buffer.read())
    encoders.encode_base64(attachment)
    attachment.add_header('Content-Disposition', 'attachment; filename=report.xlsx')
    msg.attach(attachment)

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login('your-email@gmail.com', os.getenv('MAIL_PASSWORD'))  # App password
    server.sendmail(msg['From'], msg['To'], msg.as_string())
    server.quit()

# Đăng ký trường
@app.route('/api/register_school', methods=['POST'])
def register_school():
    data = request.json
    school_id = data.get('school_id')
    name = data.get('name')
    email = data.get('email')
    send_hour = data.get('send_hour')
    username = data.get('username')
    password = data.get('password')

    if not all([school_id, name, email, send_hour, username, password]):
        return jsonify({'error': 'Missing fields'}), 400

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    school = School(id=school_id, name=name, email=email, send_hour=send_hour)
    user = User(username=username, password=hashed_password, school_id=school_id)

    try:
        db.session.add(school)
        db.session.add(user)
        db.session.commit()

        scheduler.add_job(
            send_report_email,
            CronTrigger(hour=send_hour, minute=0),
            args=[school_id]
        )
        return jsonify({'message': 'School registered', 'school_id': school_id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

# Đăng nhập
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(username=username).first()
    if user and bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
        token = create_access_token(identity=user.school_id)
        return jsonify({'token': token}), 200
    return jsonify({'error': 'Invalid credentials'}), 401

# Lấy danh sách trường
@app.route('/api/schools', methods=['GET'])
def get_schools():
    schools = School.query.all()
    return jsonify([{'id': s.id, 'name': s.name} for s in schools]), 200

# Lấy quy định vi phạm
@app.route('/api/violation_types/<school_id>', methods=['GET'])
@jwt_required()
def get_violation_types(school_id):
    if get_jwt_identity() != school_id:
        return jsonify({'error': 'Unauthorized'}), 401
    violation_types = ViolationType.query.filter_by(school_id=school_id).all()
    return jsonify([{'name': v.name, 'points': v.points_deducted} for v in violation_types]), 200

# Upload quy định vi phạm
@app.route('/api/upload_violation_types', methods=['POST'])
@jwt_required()
def upload_violation_types():
    school_id = get_jwt_identity()
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename.endswith(('.csv', '.xlsx')):
        df = pd.read_csv(file) if file.filename.endswith('.csv') else pd.read_excel(file)
        required_cols = ['Tên vi phạm', 'Điểm trừ']
        if not all(col in df.columns for col in required_cols):
            return jsonify({'error': 'Invalid file format'}), 400

        ViolationType.query.filter_by(school_id=school_id).delete()
        for _, row in df.iterrows():
            rule = ViolationType(school_id=school_id, name=row['Tên vi phạm'], points_deducted=row['Điểm trừ'])
            db.session.add(rule)
        db.session.commit()
        return jsonify({'message': 'Violation types uploaded'}), 200
    return jsonify({'error': 'Unsupported file format'}), 400

# Ghi vi phạm
@app.route('/api/record_violation', methods=['POST'])
@jwt_required()
def record_violation():
    school_id = get_jwt_identity()
    data = request.json
    student_id = data.get('student_id')
    violation_type = data.get('violation_type')
    points_deducted = data.get('points_deducted')
    violation_date = data.get('violation_date') or datetime.now().isoformat()
    recorder_name = data.get('recorder_name')
    recorder_class = data.get('recorder_class')

    if not all([student_id, violation_type, points_deducted, recorder_name, recorder_class]):
        return jsonify({'error': 'Missing fields'}), 400

    violation = Violation(
        school_id=school_id, student_id=student_id, violation_type=violation_type,
        points_deducted=points_deducted, violation_date=datetime.fromisoformat(violation_date),
        recorder_name=recorder_name, recorder_class=recorder_class
    )
    db.session.add(violation)
    db.session.commit()
    return jsonify({'message': 'Violation recorded'}), 201

# Xuất báo cáo Excel
@app.route('/api/get_report/<school_id>', methods=['GET'])
@jwt_required()
def get_report(school_id):
    if get_jwt_identity() != school_id:
        return jsonify({'error': 'Unauthorized'}), 401

    violations = Violation.query.filter_by(school_id=school_id).all()
    data = [{
        'Học sinh': v.student.name,
        'Lớp': v.student.class_name,
        'Ngày sinh': v.student.birthdate,
        'Giới tính': v.student.gender,
        'Vi phạm': v.violation_type,
        'Điểm trừ': v.points_deducted,
        'Ngày vi phạm': v.violation_date.strftime('%Y-%m-%d %H:%M'),
        'Người ghi': v.recorder_name,
        'Lớp người ghi': v.recorder_class
    } for v in violations]
    df = pd.DataFrame(data)
    excel_buffer = io.BytesIO()
    df.to_excel(excel_buffer, index=False)
    excel_buffer.seek(0)
    return send_file(excel_buffer, as_attachment=True, download_name='report.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    print(f"DEBUG: DATABASE_URL={os.getenv('DATABASE_URL')}")
    print(f"DEBUG: JWT_SECRET={os.getenv('JWT_SECRET')}")
    print(f"DEBUG: MAIL_PASSWORD={os.getenv('MAIL_PASSWORD')}")