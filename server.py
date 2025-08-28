from flask import Flask, jsonify, request
from flask_httpauth import HTTPBasicAuth
from datetime import datetime
import sqlite3, bcrypt, os

app = Flask(__name__)
auth = HTTPBasicAuth()

def get_db_connection():
    conn = sqlite3.connect('school.db')
    conn.row_factory = sqlite3.Row
    return conn

@auth.verify_password
def verify_password(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()
    if result and bcrypt.checkpw(password.encode('utf-8'), result[0].encode('utf-8')):
        return username
    return None

@app.route('/api/schools', methods=['GET'])
def get_schools():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT school_name FROM users")
    schools = [row['school_name'] for row in cursor.fetchall()]
    conn.close()
    return jsonify(schools)

@app.route('/api/violation_types/<school_name>', methods=['GET'])
@auth.login_required
def get_violation_types(school_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT violation_name, points_deducted FROM violation_types WHERE school_name = ?", (school_name,))
    violation_types = [{"name": row['violation_name'], "points": row['points_deducted']} for row in cursor.fetchall()]
    conn.close()
    return jsonify(violation_types)

@app.route('/api/sync/db', methods=['GET'])
def sync_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM students")
    students = [dict(row) for row in cursor.fetchall()]

    cursor.execute("SELECT * FROM violations")
    violations = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return jsonify({
        "students": students,
        "violations": violations,
        "last_updated": datetime.now().isoformat()
    })

@app.route('/api/sync/db', methods=['POST'])
@auth.login_required
def update_db():
    data = request.get_json()
    if not data or 'violations' not in data:
        return jsonify({"error": "No violations data"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    for violation in data['violations']:
        cursor.execute("""
            INSERT INTO violations (student_id, violation_type, points_deducted, violation_date, school_name, recorder_name, recorder_class)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            violation['student_id'],
            violation['violation_type'],
            violation['points_deducted'],
            violation['violation_date'],
            violation['school_name'],
            violation['recorder_name'],
            violation['recorder_class']
        ))

    conn.commit()
    conn.close()

    return jsonify({"message": "Data updated successfully"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
