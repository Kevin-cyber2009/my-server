from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QMessageBox
from PySide6.QtCore import Qt
import sqlite3
from utils.excel_handler import read_rules_excel

class UploadWindow(QWidget):
    def __init__(self, username, conn):
        super().__init__()
        self.username = username
        self.conn = conn
        self.cursor = conn.cursor()
        self.setWindowTitle("Upload Nội Quy Vi Phạm")
        self.resize(400, 300)
        self.setup_ui()

    def setup_ui(self):
        """Thiết lập giao diện high-tech"""
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)

        # Tiêu đề
        title_label = QLabel("Upload File Excel Nội Quy")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #00f5d4;")
        layout.addWidget(title_label)

        # Nút chọn file Excel
        self.select_button = QPushButton("Chọn File Excel Nội Quy")
        self.select_button.clicked.connect(self.select_excel_file)
        layout.addWidget(self.select_button)

        # Nút đẩy file
        self.upload_button = QPushButton("Upload Nội Quy")
        self.upload_button.clicked.connect(self.upload_rules)
        self.upload_button.setEnabled(False)
        layout.addWidget(self.upload_button)

        self.setLayout(layout)

    def select_excel_file(self):
        """Mở hộp thoại chọn file Excel"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Chọn File Excel", "", "Excel Files (*.xlsx *.xls)"
        )
        if file_path:
            self.excel_file = file_path
            self.upload_button.setEnabled(True)
            QMessageBox.information(self, "Thành công", f"Đã chọn file: {file_path}")

    def upload_rules(self):
        """Đọc file Excel và lưu nội quy vào SQLite"""
        try:
            # Lấy tên trường
            self.cursor.execute("SELECT school_name FROM users WHERE username = ?", (self.username,))
            school_name = self.cursor.fetchone()[0]

            # Đọc và lưu nội quy
            success, error = read_rules_excel(self.excel_file, school_name)
            if success:
                QMessageBox.information(self, "Thành công", "Đã upload nội quy thành công!")
            else:
                QMessageBox.critical(self, "Lỗi", error)

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Có lỗi xảy ra: {str(e)}")

    def closeEvent(self, event):
        """Đóng cửa sổ"""
        event.accept()