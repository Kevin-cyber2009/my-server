import requests
from requests.exceptions import RequestException
import sys
from PySide6.QtWidgets import QApplication
from ui.login_window import LoginWindow
import os
import sqlite3

SERVER_URL = "https://my-server-fvfu.onrender.com"  # URL server Render

def register_school(school_data):
    try:
        response = requests.post(f"{SERVER_URL}/api/register_school", json=school_data)
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        print(f"Lỗi đăng ký trường: {e}")
        return {"error": str(e)}

def login(username, password):
    try:
        response = requests.post(f"{SERVER_URL}/api/login", json={"username": username, "password": password})
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        print(f"Lỗi đăng nhập: {e}")
        return {"error": str(e)}

def get_schools():
    try:
        response = requests.get(f"{SERVER_URL}/api/schools")
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        print(f"Lỗi lấy danh sách trường: {e}")
        return []

def get_violation_types(school_name, token):
    try:
        response = requests.get(f"{SERVER_URL}/api/violation_types/{school_name}", headers={"Authorization": f"Bearer {token}"})
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        print(f"Lỗi lấy nội quy: {e}")
        return []

def sync_db(token):
    try:
        response = requests.get(f"{SERVER_URL}/api/sync/db", headers={"Authorization": f"Bearer {token}"})
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        print(f"Lỗi sync DB: {e}")
        return {}

def update_db(violations, token):
    try:
        response = requests.post(f"{SERVER_URL}/api/sync/db", json={"violations": violations}, headers={"Authorization": f"Bearer {token}"})
        response.raise_for_status()
        return response.json()
    except RequestException as e:
        print(f"Lỗi update DB: {e}")
        return {"error": str(e)}

# ---------------- Main Entry ---------------- #
if __name__ == "__main__":
    qt_app = QApplication(sys.argv)

    # Load stylesheet
    if os.path.exists("styles/style.qss"):
        with open("styles/style.qss", "r") as f:
            qt_app.setStyleSheet(f.read())

    # Tạo local DB connection
    conn = sqlite3.connect("database/school.db")

    # Show login window
    window = LoginWindow(conn)
    window.show()

    sys.exit(qt_app.exec())