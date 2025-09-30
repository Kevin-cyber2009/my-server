from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QTableWidget, QTableWidgetItem, QMessageBox  # Thêm QMessageBox
from PySide6.QtCore import Qt
import sqlite3
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import logging

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StatsWindow(QWidget):
    def __init__(self, username, conn):
        super().__init__()
        self.username = username
        self.conn = conn
        self.cursor = conn.cursor()
        self.setup_database()  # Tạo table nếu chưa có
        self.setWindowTitle("Thống Kê Vi Phạm")
        self.resize(800, 600)
        self.setup_ui()

    def setup_database(self):
        """Tạo table students và violations nếu chưa có"""
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                student_id TEXT PRIMARY KEY,
                full_name TEXT NOT NULL,
                class_name TEXT NOT NULL,
                dob TEXT NOT NULL,
                gender TEXT NOT NULL,
                school_name TEXT
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS violations (
                violation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT,
                violation_type TEXT,
                violation_date TEXT,
                recorder_name TEXT,
                recorder_class TEXT,
                school_name TEXT
            )
        """)
        self.conn.commit()

    def setup_ui(self):
        """Thiết lập giao diện thống kê"""
        layout = QVBoxLayout()

        # Tiêu đề
        title_label = QLabel("Thống Kê Vi Phạm Học Sinh")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #00f5d4;")
        layout.addWidget(title_label)

        # Bảng thống kê
        self.stats_table = QTableWidget()
        self.stats_table.setRowCount(0)
        self.stats_table.setColumnCount(4)
        self.stats_table.setHorizontalHeaderLabels(["Học sinh", "Lớp", "Số vi phạm", "Loại vi phạm"])
        self.stats_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.stats_table)

        # Biểu đồ
        self.figure = Figure(figsize=(8, 5))
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        # Nút cập nhật
        update_button = QPushButton("Cập Nhật Thống Kê")
        update_button.clicked.connect(self.update_stats)
        layout.addWidget(update_button)

        self.setLayout(layout)
        self.update_stats()  # Cập nhật biểu đồ khi mở cửa sổ

    def update_stats(self):
        """Cập nhật thống kê từ DB"""
        try:
            # Query thống kê vi phạm theo học sinh
            self.cursor.execute("""
                SELECT s.full_name, s.class_name, COUNT(v.violation_id) as count, GROUP_CONCAT(v.violation_type) as types
                FROM students s
                LEFT JOIN violations v ON s.student_id = v.student_id
                GROUP BY s.student_id
                ORDER BY count DESC
            """)
            data = self.cursor.fetchall()

            if not data:
                logger.warning("No data in students table - upload student file first")
                self.stats_table.setRowCount(0)
                self.figure.clear()
                ax = self.figure.add_subplot(111)
                ax.text(0.5, 0.5, 'No data available - Upload student file first', ha='center', va='center')
                self.canvas.draw()
                return

            # Cập nhật bảng
            self.stats_table.setRowCount(len(data))
            for row, (full_name, class_name, count, types) in enumerate(data):
                self.stats_table.setItem(row, 0, QTableWidgetItem(full_name))
                self.stats_table.setItem(row, 1, QTableWidgetItem(class_name))
                self.stats_table.setItem(row, 2, QTableWidgetItem(str(count)))
                self.stats_table.setItem(row, 3, QTableWidgetItem(types or "None"))

            # Cập nhật biểu đồ
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            names = [row[0] for row in data[:10]]  # Top 10
            counts = [row[2] for row in data[:10]]
            ax.bar(names, counts)
            ax.set_xlabel('Học sinh')
            ax.set_ylabel('Số vi phạm')
            ax.set_title('Top 10 Học sinh vi phạm nhiều nhất')
            plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
            self.canvas.draw()

        except Exception as e:
            logger.error(f"Error updating stats: {str(e)}")
            QMessageBox.critical(self, "Lỗi", f"Lỗi cập nhật thống kê: {str(e)}")