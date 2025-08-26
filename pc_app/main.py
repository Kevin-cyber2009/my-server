import sqlite3
import sys
import threading
from flask import Flask, jsonify, request
from flask_httpauth import HTTPBasicAuth
from datetime import datetime
import os
from PySide6.QtWidgets import QApplication
from ui.login_window import LoginWindow
import bcrypt

# ---------------- Flask Server ---------------- #
flask_app = Flask(__name__)
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

@flask_app.route('/api/schools', methods=['GET'])
def get_schools():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT school_name FROM users")
    schools = [row['school_name'] for row in cursor.fetchall()]
    conn.close()
    return jsonify(schools)

@flask_app.route('/api/violation_types/<school_name>', methods=['GET'])
@auth.login_required
def get_violation_types(school_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT violation_name, points_deducted FROM violation_types WHERE school_name = ?", (school_name,))
    violation_types = [{"name": row['violation_name'], "points": row['points_deducted']} for row in cursor.fetchall()]
    conn.close()
    return jsonify(violation_types)

@flask_app.route('/api/sync/db', methods=['GET'])
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

@flask_app.route('/api/sync/db', methods=['POST'])
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

# ---------------- Run Flask in background ---------------- #
def run_flask():
    port = int(os.environ.get("PORT", 5000))
    flask_app.run(host="0.0.0.0", port=port, debug=False)

# ---------------- Main Entry ---------------- #
if __name__ == "__main__":
    # Start Flask in separate thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    qt_app = QApplication(sys.argv)

    # Load stylesheet
    if os.path.exists("styles/style.qss"):
        with open("styles/style.qss", "r") as f:
            qt_app.setStyleSheet(f.read())

    # Show login window
    window = LoginWindow()
    window.show()

    sys.exit(qt_app.exec())