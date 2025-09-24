import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any
import os
from dotenv import load_dotenv

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

            # Nội dung email
            body = f"""
            <html>
            <body>
                <h2>Chúc mừng! Thanh toán thành công</h2>
                <p>Cảm ơn bạn đã mua sách từ High5 Gen Book.</p>

                <h3>Thông tin đơn hàng:</h3>
                <ul>
                    <li><strong>Mã đơn hàng:</strong> {order_details.get('order_id', 'N/A')}</li>
                    <li><strong>Tổng tiền:</strong> {order_details.get('total_amount', 0)} VND</li>
                    <li><strong>Trạng thái:</strong> {order_details.get('status', 'Đã thanh toán')}</li>
                </ul>

                <p>Chúng tôi sẽ gửi ebook cho bạn trong thời gian sớm nhất.</p>

                <p>Trân trọng,<br>Đội ngũ High5 Gen Book</p>
            </body>
            </html>
            """

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

            # Nội dung email
            body = f"""
            <html>
            <body>
                <h2>Ebook của bạn đã sẵn sàng!</h2>
                <p>Chúc mừng! Ebook cá nhân hóa của bạn đã được tạo thành công.</p>

                <h3>Thông tin ebook:</h3>
                <ul>
                    <li><strong>Tên sách:</strong> {ebook_details.get('book_title', 'N/A')}</li>
                    <li><strong>Mã đơn hàng:</strong> {ebook_details.get('order_id', 'N/A')}</li>
                </ul>

                <p><strong>Link tải ebook:</strong></p>
                <p><a href="{ebook_details.get('ebook_url', '#')}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Tải Ebook</a></p>

                <p><em>Lưu ý: Link này sẽ hết hạn sau 30 ngày.</em></p>

                <p>Cảm ơn bạn đã sử dụng dịch vụ của High5 Gen Book!</p>

                <p>Trân trọng,<br>Đội ngũ High5 Gen Book</p>
            </body>
            </html>
            """

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
