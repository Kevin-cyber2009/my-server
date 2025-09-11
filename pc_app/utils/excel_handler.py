import pandas as pd
import sqlite3
from unidecode import unidecode  # Nếu lỗi import, pip install unidecode

def read_student_excel(file_path, school_name):
    """
    Đọc file Excel/CSV danh sách học sinh và lưu vào SQLite.
    
    Args:
        file_path: Đường dẫn file Excel/CSV
        school_name: Tên trường (optional)
    Returns:
        list: Danh sách học sinh (dicts) nếu thành công, None nếu lỗi
    """
    try:
        # Đọc file với encoding UTF-8-sig cho CSV (handle BOM và tiếng Việt tốt hơn cp1252)
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path, encoding='utf-8-sig')  # Sửa từ 'cp1252'
            print(f"CSV read success. Columns: {df.columns.tolist()}")  # Debug
            print(f"First row: {df.iloc[0].to_dict()}")  # Debug data, check có # không
        else:
            df = pd.read_excel(file_path, engine='openpyxl')
            print(f"Excel read success. Columns: {df.columns.tolist()}")  # Debug
        
        # Normalize columns (skip nếu unidecode error)
        try:
            df.columns = [unidecode(col).lower().replace(' ', '_') for col in df.columns.str.strip()]
        except:
            df.columns = [col.lower().replace(' ', '_') for col in df.columns.str.strip()]  # Fallback không unidecode
        
        expected_columns = ["stt", "ho_va_ten", "lop", "ngay_thang_nam_sinh", "gioi_tinh"]
        print(f"Normalized columns: {df.columns.tolist()}")  # Debug
        if not all(col in df.columns for col in expected_columns):
            missing = [col for col in expected_columns if col not in df.columns]
            return None, f"File không đúng định dạng! Thiếu cột: {missing}. Cột hiện tại: {df.columns.tolist()}"
        
        conn = sqlite3.connect("database/school.db")
        cursor = conn.cursor()
        
        # Tạo table nếu chưa tồn tại
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS students (
                student_id TEXT PRIMARY KEY,
                full_name TEXT NOT NULL,
                class_name TEXT NOT NULL,
                dob TEXT NOT NULL,
                gender TEXT NOT NULL,
                school_name TEXT
            )
        """)
        print("Table created or exists.")  # Debug
        
        students_data = []
        for idx, row in df.iterrows():
            stt = row["stt"]
            full_name = str(row["ho_va_ten"]).replace('#', '')  # Escape # nếu có trong data
            class_name = str(row["lop"]).replace('#', '')
            dob = str(row["ngay_thang_nam_sinh"]).replace('#', '')
            gender = str(row["gioi_tinh"]).replace('#', '')
            
            student_data = {
                "STT": stt,
                "Họ và Tên": full_name,
                "Lớp": class_name,
                "Ngày tháng năm sinh": dob,
                "Giới tính": gender
            }
            student_id = f"{stt}"  # Chỉ dùng STT
            print(f"Inserting: student_id={student_id}, full_name={full_name}")  # Debug trước INSERT
            cursor.execute("""
                INSERT OR REPLACE INTO students (student_id, full_name, class_name, dob, gender, school_name)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (student_id, full_name, class_name, dob, gender, school_name if school_name else None))
            students_data.append(student_data)

        conn.commit()
        conn.close()
        print(f"Inserted {len(students_data)} students.")  # Debug
        return students_data, None
    except Exception as e:
        print(f"Exception in read_student_excel: {str(e)}")  # Debug console
        return None, f"Có lỗi khi đọc/insert file: {str(e)}"

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