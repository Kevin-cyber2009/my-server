from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QLabel, QComboBox, QMessageBox
from PySide6.QtCore import Qt

class SettingsWindow(QWidget):
    def __init__(self, username, conn):
        super().__init__()
        self.username = username
        self.conn = conn
        self.cursor = conn.cursor()
        self.setWindowTitle("Cài Đặt")
        self.resize(400, 400)
        self.setup_ui()
        self.load_user_data()

    def setup_ui(self):
        """Thiết lập giao diện high-tech"""
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)

        # Tiêu đề
        title_label = QLabel("Cài Đặt Thông Tin")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #00f5d4;")
        layout.addWidget(title_label)

        # Trường tên trường
        self.school_input = QLineEdit()
        self.school_input.setPlaceholderText("Tên trường")
        layout.addWidget(QLabel("Tên trường"))
        layout.addWidget(self.school_input)

        # Trường email
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email nhận báo cáo")
        layout.addWidget(QLabel("Email"))
        layout.addWidget(self.email_input)

        # Giờ gửi báo cáo
        self.hour_combo = QComboBox()
        self.hour_combo.addItems([f"{h:02d}:00" for h in range(24)])
        layout.addWidget(QLabel("Giờ gửi báo cáo hàng ngày"))
        layout.addWidget(self.hour_combo)

        # Nút lưu thay đổi
        self.save_button = QPushButton("Lưu Thay Đổi")
        self.save_button.clicked.connect(self.save_settings)
        layout.addWidget(self.save_button)

        self.setLayout(layout)

    def load_user_data(self):
        """Tải thông tin người dùng từ SQLite"""
        self.cursor.execute("SELECT school_name, email, report_hour FROM users WHERE username = ?", (self.username,))
        result = self.cursor.fetchone()
        if result:
            self.school_input.setText(result[0])
            self.email_input.setText(result[1])
            self.hour_combo.setCurrentText(f"{result[2]:02d}:00")

    def save_settings(self):
        """Lưu thay đổi vào SQLite"""
        school_name = self.school_input.text().strip()
        email = self.email_input.text().strip()
        report_hour = self.hour_combo.currentText().split(":")[0]

        if not school_name or not email:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập đầy đủ thông tin!")
            return

        try:
            self.cursor.execute("""
                UPDATE users SET school_name = ?, email = ?, report_hour = ?
                WHERE username = ?
            """, (school_name, email, report_hour, self.username))
            self.conn.commit()
            QMessageBox.information(self, "Thành công", "Cập nhật cài đặt thành công!")
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Có lỗi xảy ra: {str(e)}")

    def closeEvent(self, event):
        """Đóng cửa sổ"""
        event.accept()