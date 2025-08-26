from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QComboBox, QFileDialog, QMessageBox
from PySide6.QtCore import Qt
import sqlite3
import pandas as pd
from pyqtgraph import PlotWidget, BarGraphItem
from datetime import datetime, timedelta

class StatsWindow(QWidget):
    def __init__(self, username, conn):
        super().__init__()
        self.username = username
        self.conn = conn
        self.cursor = conn.cursor()
        self.setWindowTitle("Thống Kê Vi Phạm")
        self.resize(600, 500)
        self.setup_ui()

    def setup_ui(self):
        """Thiết lập giao diện high-tech"""
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(15)

        # Tiêu đề
        title_label = QLabel("Thống Kê Vi Phạm")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #00f5d4;")
        layout.addWidget(title_label)

        # Chọn loại thống kê
        self.stats_type_combo = QComboBox()
        self.stats_type_combo.addItems(["Theo Lớp", "Theo Loại Vi Phạm"])
        self.stats_type_combo.currentIndexChanged.connect(self.update_stats)
        layout.addWidget(QLabel("Loại thống kê"))
        layout.addWidget(self.stats_type_combo)

        # Biểu đồ
        self.plot_widget = PlotWidget()
        self.plot_widget.setBackground((26, 26, 46))  # Nền tối khớp với style.qss
        self.plot_widget.setStyleSheet("border: 1px solid #00f5d4;")
        layout.addWidget(self.plot_widget)

        # Nút xuất Excel
        self.export_button = QPushButton("Xuất Excel Tổng Kết Tuần")
        self.export_button.clicked.connect(self.export_excel)
        layout.addWidget(self.export_button)

        self.setLayout(layout)
        self.update_stats()  # Cập nhật biểu đồ khi mở cửa sổ

    def update_stats(self):
        """Cập nhật biểu đồ thống kê"""
        stats_type = self.stats_type_combo.currentText()
        self.cursor.execute("SELECT school_name FROM users WHERE username = ?", (self.username,))
        school_name = self.cursor.fetchone()[0]

        self.plot_widget.clear()
        if stats_type == "Theo Lớp":
            self.cursor.execute("""
                SELECT s.class_name, COUNT(v.violation_id) as violation_count
                FROM students s
                LEFT JOIN violations v ON s.student_id = v.student_id
                WHERE s.school_name = ?
                GROUP BY s.class_name
            """, (school_name,))
            data = self.cursor.fetchall()
            classes = [row[0] for row in data]
            counts = [row[1] for row in data]
            x = range(len(classes))
            bar = BarGraphItem(x=x, height=counts, width=0.4, brush=(0, 245, 212, 200))  # Màu neon #00f5d4
            self.plot_widget.addItem(bar)
            self.plot_widget.getPlotItem().setLabels(bottom=classes, left="Số vi phạm")
            self.plot_widget.getPlotItem().setTitle("Số Vi Phạm Theo Lớp")

        else:  # Theo Loại Vi Phạm
            self.cursor.execute("""
                SELECT violation_type, COUNT(violation_id) as violation_count
                FROM violations
                WHERE school_name = ?
                GROUP BY violation_type
            """, (school_name,))
            data = self.cursor.fetchall()
            violation_types = [row[0] for row in data]
            counts = [row[1] for row in data]
            x = range(len(violation_types))
            bar = BarGraphItem(x=x, height=counts, width=0.4, brush=(0, 245, 212, 200))
            self.plot_widget.addItem(bar)
            self.plot_widget.getPlotItem().setLabels(bottom=violation_types, left="Số vi phạm")
            self.plot_widget.getPlotItem().setTitle("Số Vi Phạm Theo Loại")

    def export_excel(self):
        """Xuất file Excel tổng kết điểm theo tuần"""
        try:
            # Lấy ngày đầu và cuối tuần hiện tại
            today = datetime.now()
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            start_date = start_of_week.strftime("%Y-%m-%d")
            end_date = end_of_week.strftime("%Y-%m-%d")

            # Lấy tên trường
            self.cursor.execute("SELECT school_name FROM users WHERE username = ?", (self.username,))
            school_name = self.cursor.fetchone()[0]

            # Lấy dữ liệu vi phạm trong tuần
            self.cursor.execute("""
                SELECT s.full_name, s.class_name, v.violation_type, v.points_deducted, v.violation_date
                FROM violations v
                JOIN students s ON v.student_id = s.student_id
                WHERE v.school_name = ? AND v.violation_date BETWEEN ? AND ?
            """, (school_name, start_date, end_date))
            data = self.cursor.fetchall()

            # Tạo DataFrame
            df = pd.DataFrame(data, columns=["Họ và Tên", "Lớp", "Loại vi phạm", "Điểm trừ", "Ngày vi phạm"])

            # Xuất file Excel
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Lưu File Excel", f"TongKetTuan_{start_date}_{end_date}.xlsx", "Excel Files (*.xlsx)"
            )
            if file_path:
                df.to_excel(file_path, index=False)
                QMessageBox.information(self, "Thành công", f"Đã xuất file Excel: {file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Có lỗi xảy ra: {str(e)}")

    def closeEvent(self, event):
        """Đóng cửa sổ"""
        event.accept()