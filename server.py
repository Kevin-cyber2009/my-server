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
import logging

# Cấu hình logging
logging.basicConfig(level=logging.DEBUG)  # Đổi thành DEBUG để thấy chi tiết
logger = logging.getLogger(__name__)

app = Flask(__name__)
@app.route('/')
def index():
    return jsonify({'message': 'School Server API is running. Use /api/... for endpoints.'}), 200

# Cấu hình
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///school.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET', 'your-secret-key')
db = SQLAlchemy(app)
jwt = JWTManager(app)

# Scheduler cho gửi mail
scheduler = BackgroundScheduler()
scheduler.start()

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    school_id = db.Column(db.String(50), db.ForeignKey('school.id'), nullable=False)

class School(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    send_hour = db.Column(db.Integer, nullable=False)

class Student(db.Model):
    id = db.Column(db.String(50), primary_key=True)
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

with app.app_context():
    db.create_all()

# Hàm gửi mail báo cáo
def send_report_email(school_id):
    school = School.query.get(school_id)
    if not school:
        logger.error(f"School {school_id} not found for email")
        return

    violations = Violation.query.filter_by(school_id=school_id).all()
    if not violations:
        logger.info(f"No violations found for school {school_id}")
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
    msg['From'] = 'trananhkhoidq@gmail.com'
    msg['To'] = school.email
    msg['Subject'] = f'Báo cáo vi phạm - {school.name}'
    msg.attach(MIMEText('Đính kèm báo cáo vi phạm.', 'plain'))

    attachment = MIMEBase('application', 'octet-stream')
    attachment.set_payload(excel_buffer.read())
    encoders.encode_base64(attachment)
    attachment.add_header('Content-Disposition', 'attachment; filename=report.xlsx')
    msg.attach(attachment)

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login('trananhkhoidq@gmail.com', os.getenv('MAIL_PASSWORD'))
        server.sendmail(msg['From'], msg['To'], msg.as_string())
        server.quit()
        logger.info(f"Email sent successfully to {school.email}")
    except Exception as e:
        logger.error(f"Failed to send email to {school.email}: {str(e)}")

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
        scheduler.add_job(send_report_email, CronTrigger(hour=send_hour, minute=0), args=[school_id])
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
@app.route('/api/violation_types/<school_name>', methods=['GET'])
@jwt_required()
def get_violation_types(school_name):
    school = School.query.filter_by(name=school_name).first()
    if not school or get_jwt_identity() != school.id:
        return jsonify({'error': 'Unauthorized'}), 401
    violation_types = ViolationType.query.filter_by(school_id=school.id).all()
    return jsonify([{'name': v.name, 'points': v.points_deducted} for v in violation_types]), 200

# Upload quy định vi phạm
# Endpoint upload_violation_types
@app.route('/api/upload_violation_types', methods=['POST'])
@jwt_required()
def upload_violation_types():
    school_id = get_jwt_identity()
    logger.debug(f"Upload request from school_id: {school_id}")
    if 'file' not in request.files:
        logger.error("No file in request")
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    filename = file.filename
    if not filename:
        logger.error("File has no filename")
        return jsonify({'error': 'File must have a filename'}), 400
    logger.debug(f"Uploaded file: {filename}, size: {file.content_length if hasattr(file, 'content_length') else 'Unknown'}")
    if filename.endswith(('.csv', '.xlsx')):
        try:
            file.seek(0)
            if filename.endswith('.csv'):
                # Đọc nội dung để debug
                file_content = file.read().decode('utf-8-sig')
                logger.debug(f"File content: {file_content}")
                # Tự detect separator (comma, tab, space)
                df = pd.read_csv(io.StringIO(file_content), encoding='utf-8-sig', sep=None, engine='python')
            else:
                df = pd.read_excel(file)
            df.columns = df.columns.str.strip()
            logger.debug(f"DataFrame columns: {df.columns.tolist()}")
            logger.debug(f"DataFrame head: {df.head().to_dict()}")

            required_cols = ['Loai vi pham', 'Diem tru']
            if not all(col in df.columns for col in required_cols):
                missing = [col for col in required_cols if col not in df.columns]
                logger.error(f"Missing columns: {missing}")
                return jsonify({'error': f'Invalid file format: Missing columns {missing}'}), 422
            if df.empty or not all(df[col].notna().any() for col in required_cols):
                logger.error("File empty or missing data")
                return jsonify({'error': 'File is empty or missing data in required columns'}), 422
            if not pd.api.types.is_numeric_dtype(df['Diem tru']):
                logger.error(f"'Diem tru' not numeric, dtype: {df['Diem tru'].dtype}")
                return jsonify({'error': 'Column "Diem tru" must contain numeric values'}), 422

            ViolationType.query.filter_by(school_id=school_id).delete()
            for _, row in df.iterrows():
                name = str(row['Loai vi pham']).strip()
                points = int(row['Diem tru'])
                logger.debug(f"Adding rule: {name} with points {points}")
                rule = ViolationType(school_id=school_id, name=name, points_deducted=points)
                db.session.add(rule)
            db.session.commit()
            logger.info(f"Violation types uploaded for school_id: {school_id}")
            return jsonify({'message': 'Violation types uploaded'}), 200
        except pd.errors.ParserError as e:
            logger.error(f"Parsing error: {str(e)}, content: {file_content if 'file_content' in locals() else 'N/A'}")
            return jsonify({'error': f'Parsing error: {str(e)} (Check CSV encoding, line endings, or format)'}), 422
        except ValueError as e:
            logger.error(f"Value error: {str(e)}")
            return jsonify({'error': f'Value error: {str(e)} (Ensure "Diem tru" is numeric)'}), 422
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return jsonify({'error': f'Unexpected error: {str(e)}'}), 500
    logger.error(f"Unsupported file format: {filename}")
    return jsonify({'error': 'Unsupported file format (must be .csv or .xlsx)'}), 400

# Thêm học sinh
@app.route('/api/add_student', methods=['POST'])
@jwt_required()
def add_student():
    school_id = get_jwt_identity()
    data = request.json
    name = data.get('name')
    class_name = data.get('class')
    birthdate = data.get('dob')
    gender = data.get('gender')

    if not all([name, class_name, birthdate, gender]):
        return jsonify({'error': 'Missing fields'}), 400

    student_id = f"{school_id}_{hash(name) % 1000000}".replace('-', '0')
    existing_student = Student.query.get(student_id)
    if existing_student:
        return jsonify({'error': 'Student ID already exists'}), 409

    new_student = Student(
        id=student_id,
        school_id=school_id,
        name=name,
        class_name=class_name,
        birthdate=birthdate,
        gender=gender
    )
    try:
        db.session.add(new_student)
        db.session.commit()
        return jsonify({'message': 'Student added successfully', 'student_id': student_id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

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

    student = Student.query.get(student_id)
    if not student:
        return jsonify({'error': 'Student not found'}), 404

    violation = ViolationType.query.filter_by(school_id=school_id, name=violation_type).first()
    if not violation:
        return jsonify({'error': 'Violation type not found'}), 404

    try:
        violation_date_obj = datetime.fromisoformat(violation_date)
        new_violation = Violation(
            school_id=school_id,
            student_id=student_id,
            violation_type=violation_type,
            points_deducted=points_deducted,
            violation_date=violation_date_obj,
            recorder_name=recorder_name,
            recorder_class=recorder_class
        )
        db.session.add(new_violation)
        db.session.commit()
        return jsonify({'message': 'Violation recorded'}), 201
    except ValueError as e:
        return jsonify({'error': 'Invalid date format'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Xuất báo cáo Excel
@app.route('/api/get_report/<school_id>', methods=['GET'])
@jwt_required()
def get_report(school_id):
    if get_jwt_identity() != school_id:
        return jsonify({'error': 'Unauthorized'}), 401

    violations = Violation.query.filter_by(school_id=school_id).all()
    if not violations:
        return jsonify({'message': 'No violations found'}), 200

    data = []
    for v in violations:
        if v.student:
            data.append({
                'Học sinh': v.student.name or 'N/A',
                'Lớp': v.student.class_name or 'N/A',
                'Ngày sinh': v.student.birthdate or 'N/A',
                'Giới tính': v.student.gender or 'N/A',
                'Vi phạm': v.violation_type,
                'Điểm trừ': v.points_deducted,
                'Ngày vi phạm': v.violation_date.strftime('%Y-%m-%d %H:%M'),
                'Người ghi': v.recorder_name,
                'Lớp người ghi': v.recorder_class
            })
        else:
            data.append({
                'Học sinh': 'N/A',
                'Lớp': 'N/A',
                'Ngày sinh': 'N/A',
                'Giới tính': 'N/A',
                'Vi phạm': v.violation_type,
                'Điểm trừ': v.points_deducted,
                'Ngày vi phạm': v.violation_date.strftime('%Y-%m-%d %H:%M'),
                'Người ghi': v.recorder_name,
                'Lớp người ghi': v.recorder_class
            })
    df = pd.DataFrame(data)
    excel_buffer = io.BytesIO()
    df.to_excel(excel_buffer, index=False)
    excel_buffer.seek(0)
    return send_file(excel_buffer, as_attachment=True, download_name='report.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

# Endpoint sync từ app Android
@app.route('/api/sync/db', methods=['POST'])
@jwt_required()
def update_db():
    school_id = get_jwt_identity()
    data = request.json
    if not data or 'violations' not in data:
        return jsonify({"error": "No violations data"}), 400

    try:
        for violation in data['violations']:
            student_id = violation.get('student_id')
            student = Student.query.get(student_id)
            if not student:
                return jsonify({'error': f'Student {student_id} not found'}), 404

            violation_date = datetime.strptime(violation['violation_date'], '%Y-%m-%d')
            new_violation = Violation(
                school_id=school_id,
                student_id=student_id,
                violation_type=violation['violation_type'],
                points_deducted=violation['points_deducted'],
                violation_date=violation_date,
                recorder_name=violation['recorder_name'],
                recorder_class=violation['recorder_class']
            )
            db.session.add(new_violation)
        db.session.commit()
        return jsonify({"message": "Data updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=True)  # Thêm debug=True cho local log chi tiết
    logger.info("Server started successfully with configured environment variables")