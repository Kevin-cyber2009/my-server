from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QComboBox, QMessageBox
from PySide6.QtCore import Qt
import requests
from requests.exceptions import RequestException
import os
from ui.main_window import MainWindow
from utils.email_scheduler import start_email_scheduler  # Import để gọi sau login

SERVER_URL = "https://my-server-fvfu.onrender.com"  # URL server Render

class LoginWindow(QWidget):
    def __init__(self, conn):
        super().__init__()
        self.conn = conn  # Truyền conn từ main để dùng local DB
        self.setWindowTitle("Đăng nhập / Đăng ký")
        self.resize(400, 500)
        self.setup_ui()
        self.is_login_mode = True

    def setup_ui(self):
        """Thiết lập giao diện high-tech"""
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)

        # Tiêu đề
        title_label = QLabel("HỆ THỐNG QUẢN LÝ THI ĐUA")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #00f5d4;")
        layout.addWidget(title_label)

        # Trường nhập liệu
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Tên đăng nhập")
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Mật khẩu")
        self.password_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_input)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email (cho báo cáo)")
        self.email_input.setVisible(False)  # Ẩn trong chế độ đăng nhập
        layout.addWidget(self.email_input)

        self.school_input = QLineEdit()
        self.school_input.setPlaceholderText("Tên trường")
        self.school_input.setVisible(False)  # Ẩn trong chế độ đăng nhập
        layout.addWidget(self.school_input)

        self.hour_combo = QComboBox()
        self.hour_combo.addItems([f"{h:02d}:00" for h in range(24)])
        self.hour_combo.setVisible(False)  # Ẩn trong chế độ đăng nhập
        layout.addWidget(QLabel("Giờ gửi báo cáo hàng ngày"))
        layout.addWidget(self.hour_combo)

        # Nút đăng nhập/đăng ký
        self.submit_button = QPushButton("Đăng nhập")
        self.submit_button.clicked.connect(self.handle_submit)
        layout.addWidget(self.submit_button)

        # Nút chuyển đổi chế độ
        self.toggle_button = QPushButton("Chuyển sang Đăng ký")
        self.toggle_button.clicked.connect(self.toggle_mode)
        layout.addWidget(self.toggle_button)

        self.setLayout(layout)

    def toggle_mode(self):
        """Chuyển đổi giữa đăng nhập và đăng ký"""
        self.is_login_mode = not self.is_login_mode
        if self.is_login_mode:
            self.submit_button.setText("Đăng nhập")
            self.toggle_button.setText("Chuyển sang Đăng ký")
            self.email_input.setVisible(False)
            self.school_input.setVisible(False)
            self.hour_combo.setVisible(False)
        else:
            self.submit_button.setText("Đăng ký")
            self.toggle_button.setText("Chuyển sang Đăng nhập")
            self.email_input.setVisible(True)
            self.school_input.setVisible(True)
            self.hour_combo.setVisible(True)

    def handle_submit(self):
        """Xử lý đăng nhập hoặc đăng ký"""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập đầy đủ thông tin!")
            return

        if self.is_login_mode:
            # Đăng nhập qua server
            response = self.login(username, password)
            if 'token' in response:
                QMessageBox.information(self, "Thành công", "Đăng nhập thành công!")
                self.open_main_window(username, response['token'])
            else:
                QMessageBox.critical(self, "Lỗi", response.get('error', "Đăng nhập thất bại!"))
        else:
            # Đăng ký qua server
            email = self.email_input.text().strip()
            school = self.school_input.text().strip()
            report_hour = self.hour_combo.currentText().split(":")[0]

            if not email or not school:
                QMessageBox.warning(self, "Lỗi", "Vui lòng nhập đầy đủ thông tin!")
                return

            school_data = {
                "school_id": school.lower().replace(" ", ""),
                "name": school,
                "email": email,
                "send_hour": int(report_hour),
                "username": username,
                "password": password
            }
            response = self.register_school(school_data)
            if 'message' in response:
                QMessageBox.information(self, "Thành công", "Đăng ký thành công! Vui lòng đăng nhập.")
                self.toggle_mode()
            else:
                QMessageBox.critical(self, "Lỗi", response.get('error', "Đăng ký thất bại!"))

    def register_school(self, school_data):
        try:
            response = requests.post(f"{SERVER_URL}/api/register_school", json=school_data)
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            return {"error": str(e)}

    def login(self, username, password):
        try:
            response = requests.post(f"{SERVER_URL}/api/login", json={"username": username, "password": password})
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            return {"error": str(e)}

    def open_main_window(self, username, token):
        """Mở cửa sổ chính sau khi đăng nhập"""
        # Insert user info vào local DB trước khi mở main_window
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                email TEXT NOT NULL,
                report_hour INTEGER NOT NULL,
                school_name TEXT NOT NULL
            )
        """)
        # Lấy info từ server hoặc input (giả định từ register/login response, hoặc query lại nếu cần)
        # Ví dụ: Giả định response có email, report_hour, school_name - thay bằng data thực tế
        cursor.execute("SELECT email, send_hour, name FROM schools WHERE id = (SELECT school_id FROM users WHERE username = ?)", (username,))
        school_result = cursor.fetchone()
        if school_result:
            email, report_hour, school_name = school_result
            cursor.execute("""
                INSERT OR REPLACE INTO users (username, email, report_hour, school_name)
                VALUES (?, ?, ?, ?)
            """, (username, email, report_hour, school_name))
            self.conn.commit()

        self.main_window = MainWindow(username, token, self.conn)  # Truyền conn cho main_window nếu cần
        self.main_window.show()
        self.close()