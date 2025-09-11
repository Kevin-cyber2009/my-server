import qrcode
import os
import json

def generate_qr_codes(students_data, school_name):
    """
    Tạo mã QR cho danh sách học sinh và lưu vào thư mục.
    
    Args:
        students_data: List of dicts containing student info (STT, Họ và Tên, Lớp, Ngày tháng năm sinh, Giới tính)
        school_name: Name of the school (optional)
    Returns:
        bool: True if successful, False if an error occurs
    """
    try:
        # Tạo thư mục gốc nếu chưa tồn tại
        output_dir = os.path.abspath("qr_codes")  # Folder chung
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Duyệt qua từng học sinh
        for index, student in enumerate(students_data):
            stt = student.get("STT", "unknown")
            # Chuẩn hóa dữ liệu học sinh
            student_data = {
                "full_name": str(student.get("Họ và Tên", "Unknown")).strip(),
                "class_name": str(student.get("Lớp", "Unknown")).strip(),
                "dob": str(student.get("Ngày tháng năm sinh", "2000-01-01")).split()[0],
                "gender": str(student.get("Giới tính", "Unknown")).strip()
            }

            # Tạo chuỗi JSON sạch
            qr_data = json.dumps(student_data, ensure_ascii=False, separators=(',', ':'))

            qr = qrcode.QRCode(
                version=2,  # Tăng version để hỗ trợ dữ liệu lớn hơn
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=15,
                border=6
            )
            qr.add_data(qr_data)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="black", back_color="white")

            # Tạo thư mục cho lớp
            class_dir = os.path.join(output_dir, student_data["class_name"])
            if not os.path.exists(class_dir):
                os.makedirs(class_dir)

            # Lưu file QR với tên duy nhất
            qr_file_path = os.path.join(class_dir, f"{stt}.png")
            qr_img.save(qr_file_path)
            print(f"Đã tạo QR cho {student_data['full_name']} tại {qr_file_path}")

        return True
    except Exception as e:
        print(f"Error generating QR codes: {str(e)}")
        return False