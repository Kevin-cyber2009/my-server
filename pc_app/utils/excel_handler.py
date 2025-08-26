import pandas as pd
import sqlite3
from datetime import datetime, timedelta

def read_student_excel(file_path, school_name):
    """
    Đọc file Excel danh sách học sinh và lưu vào SQLite.
    
    Args:
        file_path: Đường dẫn file Excel
        school_name: Tên trường
    Returns:
        list: Danh sách học sinh (dicts) nếu thành công, None nếu lỗi
    """
    try:
        df = pd.read_excel(file_path)
        expected_columns = ["STT", "Họ và Tên", "Lớp", "Ngày tháng năm sinh", "Giới tính"]
        if not all(col in df.columns for col in expected_columns):
            return None, "File Excel không đúng định dạng! Cần các cột: STT, Họ và Tên, Lớp, Ngày tháng năm sinh, Giới tính"

        conn = sqlite3.connect("database/school.db")
        cursor = conn.cursor()
        students_data = []

        for _, row in df.iterrows():
            stt = row["STT"]
            student_data = {
                "STT": stt,
                "Họ và Tên": str(row["Họ và Tên"]),
                "Lớp": str(row["Lớp"]),
                "Ngày tháng năm sinh": str(row["Ngày tháng năm sinh"]),
                "Giới tính": str(row["Giới tính"])
            }
            student_id = f"{school_name}_{stt}"
            cursor.execute("""
                INSERT OR REPLACE INTO students (student_id, full_name, class_name, dob, gender, school_name)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (student_id, student_data["Họ và Tên"], student_data["Lớp"],
                  student_data["Ngày tháng năm sinh"], student_data["Giới tính"], school_name))
            students_data.append(student_data)

        conn.commit()
        conn.close()
        return students_data, None
    except Exception as e:
        return None, f"Có lỗi khi đọc file Excel: {str(e)}"

def read_rules_excel(file_path, school_name):
    """
    Đọc file Excel danh sách nội quy vi phạm và lưu vào SQLite.
    
    Args:
        file_path: Đường dẫn file Excel
        school_name: Tên trường
    Returns:
        bool: True nếu thành công, False nếu lỗi
        str: Thông báo lỗi nếu có
    """
    try:
        df = pd.read_excel(file_path)
        expected_columns = ["Loại vi phạm", "Điểm trừ"]
        if not all(col in df.columns for col in expected_columns):
            return False, "File Excel không đúng định dạng! Cần các cột: Loại vi phạm, Điểm trừ"

        conn = sqlite3.connect("database/school.db")
        cursor = conn.cursor()

        # Xóa nội quy cũ của trường để tránh trùng lặp
        cursor.execute("DELETE FROM violation_types WHERE school_name = ?", (school_name,))

        for _, row in df.iterrows():
            violation_name = str(row["Loại vi phạm"])
            points_deducted = int(row["Điểm trừ"])
            cursor.execute("""
                INSERT INTO violation_types (violation_name, points_deducted, school_name)
                VALUES (?, ?, ?)
            """, (violation_name, points_deducted, school_name))

        conn.commit()
        conn.close()
        return True, None
    except Exception as e:
        return False, f"Có lỗi khi đọc file Excel: {str(e)}"

def export_violation_report(conn, school_name, start_date, end_date, output_file):
    """
    Xuất báo cáo vi phạm dưới dạng Excel với cột mới.
    
    Args:
        conn: Kết nối SQLite
        school_name: Tên trường
        start_date: Ngày bắt đầu (YYYY-MM-DD)
        end_date: Ngày kết thúc (YYYY-MM-DD)
        output_file: Đường dẫn file Excel đầu ra
    Returns:
        bool: True nếu thành công, False nếu lỗi
        str: Thông báo lỗi nếu có
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT v.violation_id AS STT, v.recorder_name AS 'Người ghi nhận', v.recorder_class AS 'Lớp ghi nhận',
                   s.full_name AS 'Học sinh vi phạm', s.class_name AS 'Lớp học sinh vi phạm', v.violation_type AS 'Lỗi vi phạm',
                   v.violation_date AS 'Thời gian ghi nhận'
            FROM violations v
            JOIN students s ON v.student_id = s.student_id
            WHERE v.school_name = ? AND v.violation_date BETWEEN ? AND ?
        """, (school_name, start_date, end_date))
        data = cursor.fetchall()

        df = pd.DataFrame(data, columns=["STT", "Người ghi nhận", "Lớp ghi nhận", "Học sinh vi phạm", "Lớp học sinh vi phạm", "Lỗi vi phạm", "Thời gian ghi nhận"])
        df.to_excel(output_file, index=False)
        return True, None
    except Exception as e:
        return False, f"Có lỗi khi xuất file Excel: {str(e)}"