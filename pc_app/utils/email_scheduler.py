from apscheduler.schedulers.background import BackgroundScheduler
import sqlite3
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
import base64
import os
from dotenv import load_dotenv
from utils.excel_handler import export_violation_report

def setup_email_scheduler(username, conn, sendgrid_api_key):
    """
    Lên lịch gửi email báo cáo hàng ngày.
    
    Args:
        username: Username của người dùng
        conn: Kết nối SQLite
        sendgrid_api_key: Khóa API của SendGrid
    """
    scheduler = BackgroundScheduler()
    cursor = conn.cursor()

    cursor.execute("SELECT email, report_hour, school_name FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    if not result:
        print(f"Không tìm thấy thông tin người dùng {username}")
        return

    email, report_hour, school_name = result
    report_time = f"{report_hour}:00"

    def send_daily_report():
        """Tạo và gửi báo cáo vi phạm hàng ngày"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            excel_file = f"report_{today}.xlsx"
            success, error = export_violation_report(conn, school_name, today, today, excel_file)
            if not success:
                print(f"Error generating report: {error}")
                return

            message = Mail(
                from_email='no-reply@schoolviolation.com',
                to_emails=email,
                subject=f'Báo Cáo Vi Phạm Hàng Ngày - {school_name} - {today}',
                html_content=f'<p>Xin chào,<br>Đây là báo cáo vi phạm ngày {today} của trường {school_name}.<br>Xin vui lòng xem file đính kèm.</p>'
            )

            with open(excel_file, 'rb') as f:
                data = f.read()
                encoded = base64.b64encode(data).decode()
            attachment = Attachment(
                FileContent(encoded),
                FileName(excel_file),
                FileType('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                Disposition('attachment')
            )
            message.attachment = attachment

            sg = SendGridAPIClient(sendgrid_api_key)
            response = sg.send(message)
            print(f"Email sent to {email} with status code {response.status_code}")

            os.remove(excel_file)

        except Exception as e:
            print(f"Error sending email: {str(e)}")

    scheduler.add_job(send_daily_report, 'cron', hour=int(report_hour), minute=0)
    scheduler.start()

def start_email_scheduler(username, conn):
    """Khởi động scheduler với SendGrid API key từ .env"""
    load_dotenv()
    sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
    if not sendgrid_api_key:
        print("SendGrid API key not found in .env")
        return
    setup_email_scheduler(username, conn, sendgrid_api_key)