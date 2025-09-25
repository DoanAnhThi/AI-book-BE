import os
from typing import Dict, Any
from datetime import datetime

class EmailTemplateLoader:
    """Utility class để load và render email templates"""

    def __init__(self, template_dir: str = None):
        if template_dir is None:
            # Mặc định là thư mục templates trong cùng thư mục với file này
            current_dir = os.path.dirname(os.path.abspath(__file__))
            template_dir = os.path.join(current_dir, 'templates')

        self.template_dir = template_dir

    def load_template(self, template_name: str) -> str:
        """
        Load nội dung template HTML

        Args:
            template_name: Tên file template (vd: 'payment_success.html')

        Returns:
            Nội dung HTML của template

        Raises:
            FileNotFoundError: Nếu template không tồn tại
        """
        template_path = os.path.join(self.template_dir, template_name)

        if not os.path.exists(template_path):
            raise FileNotFoundError(f"Template '{template_name}' không tồn tại tại {template_path}")

        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()

    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Render template với context data

        Args:
            template_name: Tên file template
            context: Dictionary chứa dữ liệu để render

        Returns:
            HTML đã được render
        """
        template_content = self.load_template(template_name)

        # Thay thế các biến trong template
        rendered = template_content
        for key, value in context.items():
            placeholder = f"{{{{ {key} }}}}"
            rendered = rendered.replace(placeholder, str(value))

        return rendered

    def render_payment_success_email(self, order_details: Dict[str, Any]) -> str:
        """
        Render template email thanh toán thành công

        Args:
            order_details: Thông tin đơn hàng

        Returns:
            HTML email đã render
        """
        context = {
            'order_id': order_details.get('order_id', 'N/A'),
            'total_amount': f"{order_details.get('total_amount', 0):,.0f}",
            'status': order_details.get('status', 'Đã thanh toán'),
            'order_date': datetime.now().strftime('%d/%m/%Y %H:%M')
        }

        return self.render_template('payment_success.html', context)

    def render_ebook_delivery_email(self, ebook_details: Dict[str, Any]) -> str:
        """
        Render template email gửi link ebook

        Args:
            ebook_details: Thông tin ebook

        Returns:
            HTML email đã render
        """
        context = {
            'book_title': ebook_details.get('book_title', 'N/A'),
            'order_id': ebook_details.get('order_id', 'N/A'),
            'ebook_url': ebook_details.get('ebook_url', '#'),
            'created_at': datetime.now().strftime('%d/%m/%Y %H:%M')
        }

        return self.render_template('ebook_delivery.html', context)

# Instance mặc định
template_loader = EmailTemplateLoader()
