from PySide6.QtWidgets import QMainWindow, QWidget, QGridLayout, QPushButton, QLabel
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from ui.settings_window import SettingsWindow
from ui.qr_window import QRWindow
from ui.upload_window import UploadWindow
from ui.stats_window import StatsWindow
import sqlite3
from utils.email_scheduler import start_email_scheduler
import logging  # Thêm import logging

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)  # Định nghĩa logger

class MainWindow(QMainWindow):
    def __init__(self, username, token, conn, email=None):
        super().__init__()
        self.username = username
        self.token = token
        self.conn = conn
        self.email = email
        self.setWindowTitle("Hệ Thống Quản Lý Thi Đua")
        self.resize(600, 400)
        self.setup_ui()
        self.setup_database()
        # Xóa start_email_scheduler ở đây để tránh duplicate - gọi chỉ ở login_window

    def setup_database(self):
        """Kết nối cơ sở dữ liệu SQLite"""
        self.cursor = self.conn.cursor()

    def setup_ui(self):
        """Thiết lập giao diện chính với 4 chức năng"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QGridLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(20)

        # Tiêu đề
        title_label = QLabel(f"Chào mừng, {self.username}")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #00f5d4;")
        layout.addWidget(title_label, 0, 0, 1, 2)

        # Nút chức năng
        button_size = QSize(150, 150)

        # Nút Cài đặt
        settings_button = QPushButton("Cài đặt")
        settings_button.setIcon(QIcon("resources/settings.png"))
        settings_button.setIconSize(QSize(64, 64))
        settings_button.setFixedSize(button_size)
        settings_button.clicked.connect(self.open_settings)
        layout.addWidget(settings_button, 1, 0)

        # Nút Tạo QR
        qr_button = QPushButton("Tạo QR")
        qr_button.setIcon(QIcon("resources/qr_code.png"))
        qr_button.setIconSize(QSize(64, 64))
        qr_button.setFixedSize(button_size)
        qr_button.clicked.connect(self.open_qr)
        layout.addWidget(qr_button, 1, 1)

        # Nút Upload Nội Quy
        upload_button = QPushButton("Upload Nội Quy")
        upload_button.setIcon(QIcon("resources/upload.png"))
        upload_button.setIconSize(QSize(64, 64))
        upload_button.setFixedSize(button_size)
        upload_button.clicked.connect(self.open_upload_window)
        layout.addWidget(upload_button, 2, 0)

        # Nút Thống kê
        stats_button = QPushButton("Thống Kê")
        stats_button.setIcon(QIcon("resources/stats.png"))
        stats_button.setIconSize(QSize(64, 64))
        stats_button.setFixedSize(button_size)
        stats_button.clicked.connect(self.open_stats)
        layout.addWidget(stats_button, 2, 1)

        central_widget.setLayout(layout)

    def open_settings(self):
        """Mở cửa sổ cài đặt"""
        self.settings_window = SettingsWindow(self.username, self.conn)
        self.settings_window.show()

    def open_qr(self):
        """Mở cửa sổ tạo QR"""
        self.qr_window = QRWindow(self.username, self.conn)
        self.qr_window.show()

    def open_upload_window(self):
        self.upload_window = UploadWindow(self.username, self.token)
        self.upload_window.show()

    def open_stats(self):
        """Mở cửa sổ thống kê"""
        self.stats_window = StatsWindow(self.username, self.conn)
        self.stats_window.show()

    def closeEvent(self, event):
        """Đóng kết nối cơ sở dữ liệu khi thoát"""
        self.conn.close()
        event.accept()