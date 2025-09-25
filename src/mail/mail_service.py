import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any
import os
from dotenv import load_dotenv

from .template_loader import template_loader

load_dotenv()

class MailService:
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.sender_email = os.getenv("SENDER_EMAIL", "")
        self.sender_password = os.getenv("SENDER_PASSWORD", "")

    def send_payment_success_email(self, recipient_email: str, order_details: Dict[str, Any]) -> Dict[str, str]:
        """
        Gửi email thông báo thanh toán thành công

        Args:
            recipient_email: Email người nhận
            order_details: Thông tin đơn hàng

        Returns:
            Dict với trạng thái gửi email
        """
        try:
            # Tạo message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = recipient_email
            msg['Subject'] = "Thanh toán thành công - High5 Gen Book"

            # Render template
            body = template_loader.render_payment_success_email(order_details)

            msg.attach(MIMEText(body, 'html'))

            # Gửi email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            text = msg.as_string()
            server.sendmail(self.sender_email, recipient_email, text)
            server.quit()

            return {"status": "success", "message": "Email thanh toán thành công đã được gửi"}

        except Exception as e:
            return {"status": "error", "message": f"Lỗi gửi email: {str(e)}"}

    def send_ebook_url_email(self, recipient_email: str, ebook_details: Dict[str, Any]) -> Dict[str, str]:
        """
        Gửi email chứa URL ebook cho khách hàng

        Args:
            recipient_email: Email người nhận
            ebook_details: Thông tin ebook

        Returns:
            Dict với trạng thái gửi email
        """
        try:
            # Tạo message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = recipient_email
            msg['Subject'] = "Ebook của bạn đã sẵn sàng - High5 Gen Book"

            # Render template
            body = template_loader.render_ebook_delivery_email(ebook_details)

            msg.attach(MIMEText(body, 'html'))

            # Gửi email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            text = msg.as_string()
            server.sendmail(self.sender_email, recipient_email, text)
            server.quit()

            return {"status": "success", "message": "Email chứa URL ebook đã được gửi"}

        except Exception as e:
            return {"status": "error", "message": f"Lỗi gửi email: {str(e)}"}

# Instance của MailService
mail_service = MailService()
