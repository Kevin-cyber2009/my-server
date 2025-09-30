from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
import sqlite3
from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders
import os
from dotenv import load_dotenv
from utils.excel_handler import export_violation_report
import logging

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_email_scheduler(username, conn):
    """
    Lên lịch gửi email báo cáo hàng ngày.
    
    Args:
        username: Username của người dùng
        conn: Kết nối SQLite
    """
    jobstores = {
        'default': SQLAlchemyJobStore(url='sqlite:///jobs.db')  # Persistent job store
    }
    scheduler = BackgroundScheduler(jobstores=jobstores, timezone='Asia/Ho_Chi_Minh')
    cursor = conn.cursor()

    cursor.execute("SELECT email, report_hour, school_name FROM users WHERE username = ?", (username,))
    result = cursor.fetchone()
    if not result:
        logger.error(f"Không tìm thấy thông tin người dùng {username} trong local DB")
        return None

    email, report_hour, school_name = result

    def send_daily_report():
        """Tạo và gửi báo cáo vi phạm hàng ngày qua Gmail"""
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            excel_file = f"report_{school_name}_{today}_{datetime.now().strftime('%H%M%S')}.xlsx"
            success, error = export_violation_report(conn, school_name, today, today, excel_file)
            if not success:
                logger.error(f"Error generating report: {error}")
                return

            if not os.path.exists(excel_file):
                logger.error("Excel file not found after generation")
                return

            logger.info(f"Generating report for {school_name} on {today}")

            msg = MIMEMultipart()
            msg['From'] = os.getenv('GMAIL_USERNAME')
            msg['To'] = email
            msg['Subject'] = f'Báo Cáo Vi Phạm Hàng Ngày - {school_name} - {today}'
            msg.attach(MIMEText(f'<p>Xin chào,<br>Đây là báo cáo vi phạm ngày {today} của trường {school_name}.<br>Xin vui lòng xem file đính kèm.</p>', 'html'))

            with open(excel_file, 'rb') as f:
                attachment = MIMEBase('application', 'octet-stream')
                attachment.set_payload(f.read())
                encoders.encode_base64(attachment)
                attachment.add_header('Content-Disposition', f'attachment; filename={excel_file}')
                msg.attach(attachment)

            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(os.getenv('GMAIL_USERNAME'), os.getenv('GMAIL_PASSWORD'))
            server.sendmail(msg['From'], msg['To'], msg.as_string())
            server.quit()
            logger.info(f"Email sent to {email}")

            os.remove(excel_file)

        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")

    scheduler.add_job(send_daily_report, 'cron', hour=int(report_hour), minute=0, replace_existing=True)  # Replace if exists
    scheduler.start()
    logger.info("Scheduler started with daily job added")
    return scheduler

def start_email_scheduler(username, conn, email, report_hour, school_name):
    """Khởi động scheduler - insert user info nếu chưa có"""
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))
    gmail_username = os.getenv("GMAIL_USERNAME")
    gmail_password = os.getenv("GMAIL_PASSWORD")
    if not gmail_username or not gmail_password:
        logger.error("Gmail credentials not found in .env")
        return None

    cursor = conn.cursor()
    # Insert user info nếu chưa có
    cursor.execute("""
        INSERT OR REPLACE INTO users (username, email, report_hour, school_name)
        VALUES (?, ?, ?, ?)
    """, (username, email, report_hour, school_name))
    conn.commit()

    scheduler = setup_email_scheduler(username, conn)
    return scheduler