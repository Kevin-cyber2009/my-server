from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QMessageBox
from PySide6.QtCore import Qt
import sqlite3
from utils.excel_handler import read_student_excel
from utils.qr_generator import generate_qr_codes

class QRWindow(QWidget):
    def __init__(self, username, conn):
        super().__init__()
        self.username = username
        self.conn = conn
        self.cursor = conn.cursor()
        self.setWindowTitle("Tạo Mã QR")
        self.resize(400, 300)
        self.setup_ui()

    def setup_ui(self):
        """Thiết lập giao diện high-tech"""
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)

        # Tiêu đề
        title_label = QLabel("Tạo Mã QR Cho Học Sinh")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #00f5d4;")
        layout.addWidget(title_label)

        # Nút chọn file Excel
        self.select_button = QPushButton("Chọn File Excel Danh Sách Học Sinh")
        self.select_button.clicked.connect(self.select_excel_file)
        layout.addWidget(self.select_button)

        # Nút tạo mã QR
        self.generate_button = QPushButton("Tạo Mã QR")
        self.generate_button.clicked.connect(self.generate_qr_codes)
        self.generate_button.setEnabled(False)
        layout.addWidget(self.generate_button)

        self.setLayout(layout)

    def select_excel_file(self):
        """Mở hộp thoại chọn file Excel"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Chọn File Excel", "", "Excel Files (*.xlsx *.xls)"
        )
        if file_path:
            self.excel_file = file_path
            self.generate_button.setEnabled(True)
            QMessageBox.information(self, "Thành công", f"Đã chọn file: {file_path}")

    def generate_qr_codes(self):
        """Tạo mã QR từ file Excel và lưu vào thư mục"""
        try:
            # Lấy tên trường từ bảng users
            self.cursor.execute("SELECT school_name FROM users WHERE username = ?", (self.username,))
            school_name = self.cursor.fetchone()[0]

            # Đọc file Excel
            students_data, error = read_student_excel(self.excel_file, school_name)
            if error:
                QMessageBox.critical(self, "Lỗi", error)
                return

            # Tạo mã QR
            if generate_qr_codes(students_data, school_name):
                QMessageBox.information(self, "Thành công", f"Đã tạo mã QR và lưu vào qr_codes/{school_name}")
            else:
                QMessageBox.critical(self, "Lỗi", "Có lỗi khi tạo mã QR!")

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Có lỗi xảy ra: {str(e)}")

    def closeEvent(self, event):
        """Đóng cửa sổ"""
        event.accept()