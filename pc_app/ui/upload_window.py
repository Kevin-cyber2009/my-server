from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog, QMessageBox
from PySide6.QtCore import Qt
import requests
from requests.exceptions import RequestException
import os
class UploadWindow(QWidget):
    def __init__(self, username, token):
        super().__init__()
        self.username = username
        self.token = token  # Nhận token từ MainWindow
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
            self, "Chọn File Excel", "", "Excel Files (*.csv *.xlsx *.xls)"
        )
        if file_path:
            if not file_path.lower().endswith(('.csv', '.xlsx', '.xls')):
                QMessageBox.warning(self, "Lỗi", "Vui lòng chọn file .csv hoặc .xlsx!")
                return
            self.excel_file = file_path
            self.upload_button.setEnabled(True)
            QMessageBox.information(self, "Thành công", f"Đã chọn file: {file_path}")

    def upload_rules(self):
        try:
            filename = os.path.basename(self.excel_file)
            mimetype = 'text/csv' if filename.endswith('.csv') else 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            with open(self.excel_file, 'rb') as file:
                files = {'file': (filename, file, mimetype)}
                headers = {"Authorization": f"Bearer {self.token}"}
                print(f"Sending file: {filename}, size: {os.path.getsize(self.excel_file)} bytes, mimetype: {mimetype}")  # Debug
                response = requests.post(
                    "https://my-server-fvfu.onrender.com/api/upload_violation_types",
                    files=files,
                    headers=headers,
                    timeout=30
                )
                print(f"Response status: {response.status_code}, text: {response.text}")  # Debug response
                response.raise_for_status()
                result = response.json()
                if 'message' in result:
                    QMessageBox.information(self, "Thành công", result['message'])
                else:
                    QMessageBox.warning(self, "Cảnh báo", "Upload thành công nhưng có thông báo: " + str(result))
        except RequestException as e:
            error_msg = f"Lỗi upload: {str(e)} (Mã lỗi: {e.response.status_code if e.response else 'No response'})"
            if e.response:
                try:
                    error_detail = e.response.json().get('error', 'No detail')
                except:
                    error_detail = e.response.text
                error_msg += f"\nChi tiết từ server: {error_detail}"
            QMessageBox.critical(self, "Lỗi", error_msg)
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Có lỗi xảy ra: {str(e)}")

    def closeEvent(self, event):
        """Đóng cửa sổ"""
        event.accept()