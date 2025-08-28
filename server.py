import os
import sqlite3
import bcrypt
from flask import Flask, request, jsonify
from flask_httpauth import HTTPBasicAuth

app = Flask(__name__)
auth = HTTPBasicAuth()

DATABASE = "school.db"


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# ----------------- KHỞI TẠO DATABASE -----------------
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Bảng users
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            school_name TEXT NOT NULL
        )
    """)

    # Bảng học sinh
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            class_name TEXT NOT NULL,
            date_of_birth TEXT,
            gender TEXT,
            school_name TEXT NOT NULL
        )
    """)

    # Bảng loại vi phạm
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS violation_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            violation_name TEXT NOT NULL,
            points_deducted INTEGER NOT NULL,
            school_name TEXT NOT NULL
        )
    """)

    # Bảng ghi nhận vi phạm
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS violations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            violation_type TEXT NOT NULL,
            points_deducted INTEGER NOT NULL,
            violation_date TEXT NOT NULL,
            school_name TEXT NOT NULL,
            recorder_name TEXT NOT NULL,
            recorder_class TEXT NOT NULL,
            FOREIGN KEY (student_id) REFERENCES students (id)
        )
    """)

    conn.commit()
    conn.close()


# ----------------- AUTH -----------------
@auth.verify_password
def verify_password(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM users WHERE username=?", (username,))
    result = cursor.fetchone()
    conn.close()
    if result:
        stored_pw = result[0]
        if isinstance(stored_pw, str):  # nếu DB lưu text
            stored_pw = stored_pw.encode("utf-8")
        if bcrypt.checkpw(password.encode("utf-8"), stored_pw):
            return username
    return None


# ----------------- API -----------------
@app.route("/")
def index():
    return jsonify({"message": "✅ Server đang chạy thành công!"})


@app.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    school_name = data.get("school_name")

    hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password, school_name) VALUES (?, ?, ?)",
            (username, hashed_pw.decode("utf-8"), school_name),
        )
        conn.commit()
        conn.close()
        return jsonify({"message": "Đăng ký thành công"})
    except sqlite3.IntegrityError:
        return jsonify({"error": "Tên đăng nhập đã tồn tại"}), 400


# ----------------- START APP -----------------
if __name__ == "__main__":
    init_db()  # ✅ tạo DB khi khởi động
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
