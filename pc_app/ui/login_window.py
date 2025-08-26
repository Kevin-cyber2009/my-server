from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QComboBox, QMessageBox
from PySide6.QtCore import Qt
import sqlite3
import bcrypt
import os
from ui.main_window import MainWindow

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Đăng nhập / Đăng ký")
        self.resize(400, 500)
        self.setup_ui()
        self.is_login_mode = True
        self.setup_database()

    def setup_database(self):
        """Khởi tạo cơ sở dữ liệu SQLite"""
        if not os.path.exists("database"):
            os.makedirs("database")
        self.conn = sqlite3.connect("database/school.db")
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                email TEXT NOT NULL,
                report_hour INTEGER NOT NULL,
                school_name TEXT NOT NULL
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                student_id TEXT PRIMARY KEY,
                full_name TEXT NOT NULL,
                class_name TEXT NOT NULL,
                dob TEXT NOT NULL,
                gender TEXT NOT NULL,
                school_name TEXT NOT NULL
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS violations (
                violation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                violation_type TEXT NOT NULL,
                points_deducted INTEGER NOT NULL,
                violation_date TEXT NOT NULL,
                school_name TEXT NOT NULL,
                recorder_name TEXT NOT NULL,
                recorder_class TEXT NOT NULL,
                FOREIGN KEY (student_id) REFERENCES students(student_id)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS violation_types (
                violation_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
                violation_name TEXT NOT NULL,
                points_deducted INTEGER NOT NULL,
                school_name TEXT NOT NULL
            )
        """)
        self.conn.commit()

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
            # Kiểm tra đăng nhập
            self.cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
            result = self.cursor.fetchone()
            if result and bcrypt.checkpw(password.encode('utf-8'), result[0].encode('utf-8')):
                QMessageBox.information(self, "Thành công", "Đăng nhập thành công!")
                self.open_main_window(username)
            else:
                QMessageBox.critical(self, "Lỗi", "Tên đăng nhập hoặc mật khẩu không đúng!")
        else:
            # Đăng ký tài khoản mới
            email = self.email_input.text().strip()
            school = self.school_input.text().strip()
            report_hour = self.hour_combo.currentText().split(":")[0]

            if not email or not school:
                QMessageBox.warning(self, "Lỗi", "Vui lòng nhập đầy đủ thông tin!")
                return

            # Mã hóa mật khẩu
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            try:
                self.cursor.execute("""
                    INSERT INTO users (username, password, email, report_hour, school_name)
                    VALUES (?, ?, ?, ?, ?)
                """, (username, hashed_password, email, report_hour, school))
                self.conn.commit()
                QMessageBox.information(self, "Thành công", "Đăng ký thành công! Vui lòng đăng nhập.")
                self.toggle_mode()
            except sqlite3.IntegrityError:
                QMessageBox.critical(self, "Lỗi", "Tên đăng nhập đã tồn tại!")

    def open_main_window(self, username):
        """Mở cửa sổ chính sau khi đăng nhập"""
        self.main_window = MainWindow(username)
        self.main_window.show()
        self.close()

    def closeEvent(self, event):
        """Đóng kết nối cơ sở dữ liệu khi thoát"""
        self.conn.close()
        event.accept()