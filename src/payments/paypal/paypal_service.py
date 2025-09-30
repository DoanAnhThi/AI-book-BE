import paypalrestsdk
import json
import os
from typing import Optional, Dict, Any
from decimal import Decimal
from urllib.parse import urljoin

from src.db.order.models.order_schemas import Order, CheckoutRequest
from src.db.common.database_connection import get_db
from sqlalchemy.orm import Session

class PayPalService:
    """Service xử lý thanh toán PayPal"""

    def __init__(self):
        # Cấu hình PayPal SDK
        paypalrestsdk.configure({
            "mode": os.getenv("PAYPAL_MODE", "sandbox"),  # "sandbox" hoặc "live"
            "client_id": os.getenv("PAYPAL_CLIENT_ID", ""),
            "client_secret": os.getenv("PAYPAL_CLIENT_SECRET", "")
        })

    def create_payment(
        self,
        order: Order,
        success_url: str,
        cancel_url: str,
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Tạo payment PayPal

        Args:
            order: Order object
            success_url: URL khi thanh toán thành công
            cancel_url: URL khi hủy thanh toán
            db: Database session

        Returns:
            Dict chứa thông tin payment PayPal
        """
        try:
            # Tạo payment object
            payment = paypalrestsdk.Payment({
                "intent": "sale",
                "payer": {
                    "payment_method": "paypal"
                },
                "redirect_urls": {
                    "return_url": success_url,
                    "cancel_url": cancel_url
                },
                "transactions": [{
                    "item_list": {
                        "items": [{
                            "name": "AI Generated Children's Book",
                            "sku": f"book_{order.id}",
                            "price": str(order.total_amount),
                            "currency": order.currency,
                            "quantity": 1
                        }]
                    },
                    "amount": {
                        "total": str(order.total_amount),
                        "currency": order.currency
                    },
                    "description": f"Order #{order.id} - {order.full_name}"
                }]
            })

            # Tạo payment
            if payment.create():
                return {
                    "success": True,
                    "payment_id": payment.id,
                    "approval_url": self._get_approval_url(payment),
                    "payment": payment
                }
            else:
                return {
                    "success": False,
                    "error": payment.error,
                    "message": "Failed to create PayPal payment"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Exception occurred while creating PayPal payment"
            }

    def execute_payment(
        self,
        payment_id: str,
        payer_id: str,
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Thực hiện thanh toán PayPal

        Args:
            payment_id: PayPal payment ID
            payer_id: PayPal payer ID
            db: Database session

        Returns:
            Dict chứa kết quả thanh toán
        """
        try:
            # Lấy payment object
            payment = paypalrestsdk.Payment.find(payment_id)

            if not payment:
                return {
                    "success": False,
                    "message": "Payment not found"
                }

            # Check payment state - nếu đã approved/completed thì không cần execute lại
            if payment.state in ['approved', 'completed']:
                # Lấy transaction ID từ related resources
                transaction_id = None
                if hasattr(payment, 'transactions') and payment.transactions:
                    transaction = payment.transactions[0]
                    if hasattr(transaction, 'related_resources') and transaction.related_resources:
                        sale = transaction.related_resources[0].sale
                        if sale:
                            transaction_id = sale.id

                return {
                    "success": True,
                    "payment": payment,
                    "transaction_id": transaction_id,
                    "message": f"Payment already {payment.state}"
                }

            # Thực hiện thanh toán nếu chưa completed
            if payment.execute({"payer_id": payer_id}):
                return {
                    "success": True,
                    "payment": payment,
                    "transaction_id": self._get_transaction_id(payment)
                }
            else:
                return {
                    "success": False,
                    "error": payment.error,
                    "message": "Failed to execute PayPal payment"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Exception occurred while executing PayPal payment"
            }

    def refund_payment(
        self,
        transaction_id: str,
        amount: Optional[Decimal] = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Hoàn tiền thanh toán

        Args:
            transaction_id: PayPal transaction ID
            amount: Số tiền hoàn (optional, nếu không có thì hoàn toàn bộ)
            db: Database session

        Returns:
            Dict chứa kết quả hoàn tiền
        """
        try:
            # Tìm sale transaction
            sale = paypalrestsdk.Sale.find(transaction_id)

            if not sale:
                return {
                    "success": False,
                    "message": "Sale transaction not found"
                }

            # Tạo refund
            refund_data = {}
            if amount:
                refund_data["amount"] = {
                    "total": str(amount),
                    "currency": sale.amount.currency
                }

            refund = sale.refund(refund_data)

            if refund.success():
                return {
                    "success": True,
                    "refund": refund,
                    "refund_id": refund.id
                }
            else:
                return {
                    "success": False,
                    "error": refund.error,
                    "message": "Failed to refund payment"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Exception occurred while refunding payment"
            }

    def verify_webhook_signature(
        self,
        webhook_body: str,
        signature: str,
        webhook_id: str
    ) -> bool:
        """
        Xác minh webhook signature từ PayPal

        Args:
            webhook_body: Raw webhook body
            signature: Webhook signature header
            webhook_id: PayPal webhook ID

        Returns:
            True nếu signature hợp lệ
        """
        try:
            # Tạo webhook event object
            webhook_event = paypalrestsdk.WebhookEvent({
                "body": webhook_body,
                "signature": signature,
                "webhook_id": webhook_id
            })

            return webhook_event.verify()

        except Exception as e:
            print(f"Webhook verification error: {e}")
            return False

    def _get_approval_url(self, payment: paypalrestsdk.Payment) -> Optional[str]:
        """Lấy approval URL từ payment object"""
        for link in payment.links:
            if link.rel == "approval_url":
                return link.href
        return None

    def _get_transaction_id(self, payment: paypalrestsdk.Payment) -> Optional[str]:
        """Lấy transaction ID từ payment object"""
        if payment.transactions and len(payment.transactions) > 0:
            transaction = payment.transactions[0]
            if transaction.related_resources and len(transaction.related_resources) > 0:
                sale = transaction.related_resources[0].sale
                if sale:
                    return sale.id
        return None

    def create_paypal_order(self, order: Order, db: Session = None) -> Dict[str, Any]:
        """
        Tạo PayPal order cho client-side payment

        Args:
            order: Order object
            db: Database session

        Returns:
            Dict chứa thông tin PayPal order
        """
        try:
            import requests
            import base64
            import json

            # PayPal API credentials
            client_id = os.getenv('PAYPAL_CLIENT_ID')
            client_secret = os.getenv('PAYPAL_CLIENT_SECRET')
            mode = os.getenv('PAYPAL_MODE', 'sandbox')

            # PayPal API base URL
            base_url = 'https://api.sandbox.paypal.com' if mode == 'sandbox' else 'https://api.paypal.com'

            # Get access token
            auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
            headers = {
                'Authorization': f'Basic {auth}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }

            token_response = requests.post(f'{base_url}/v1/oauth2/token',
                                         data='grant_type=client_credentials',
                                         headers=headers)

            if token_response.status_code != 200:
                return {
                    "success": False,
                    "error": token_response.text,
                    "message": "Failed to get PayPal access token"
                }

            access_token = token_response.json()['access_token']

            # Create order
            order_headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            order_data = {
                "intent": "CAPTURE",
                "purchase_units": [{
                    "reference_id": f"order_{order.id}",
                    "amount": {
                        "currency_code": order.currency,
                        "value": str(order.total_amount)
                    },
                    "description": f"Order #{order.id} - {order.full_name}"
                }]
            }

            order_response = requests.post(f'{base_url}/v2/checkout/orders',
                                         json=order_data,
                                         headers=order_headers)

            if order_response.status_code == 201:
                paypal_order = order_response.json()
                return {
                    "success": True,
                    "paypal_order_id": paypal_order['id'],
                    "order": paypal_order
                }
            else:
                return {
                    "success": False,
                    "error": order_response.text,
                    "message": f"Failed to create PayPal order: {order_response.status_code}"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Exception occurred while creating PayPal order: {str(e)}"
            }

    def capture_paypal_payment(self, paypal_order_id: str, db: Session = None) -> Dict[str, Any]:
        """
        Capture PayPal payment sau khi user approve

        Args:
            paypal_order_id: PayPal order ID
            db: Database session

        Returns:
            Dict chứa kết quả capture
        """
        try:
            import requests
            import base64

            # PayPal API credentials
            client_id = os.getenv('PAYPAL_CLIENT_ID')
            client_secret = os.getenv('PAYPAL_CLIENT_SECRET')
            mode = os.getenv('PAYPAL_MODE', 'sandbox')

            # PayPal API base URL
            base_url = 'https://api.sandbox.paypal.com' if mode == 'sandbox' else 'https://api.paypal.com'

            # Get access token
            auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
            headers = {
                'Authorization': f'Basic {auth}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }

            token_response = requests.post(f'{base_url}/v1/oauth2/token',
                                         data='grant_type=client_credentials',
                                         headers=headers)

            if token_response.status_code != 200:
                return {
                    "success": False,
                    "error": token_response.text,
                    "message": "Failed to get PayPal access token"
                }

            access_token = token_response.json()['access_token']

            # Capture order
            capture_headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            capture_response = requests.post(f'{base_url}/v2/checkout/orders/{paypal_order_id}/capture',
                                           headers=capture_headers)

            if capture_response.status_code == 201:
                capture_data = capture_response.json()

                # Extract transaction ID
                transaction_id = None
                if 'purchase_units' in capture_data and capture_data['purchase_units']:
                    purchase_unit = capture_data['purchase_units'][0]
                    if 'payments' in purchase_unit and 'captures' in purchase_unit['payments']:
                        captures = purchase_unit['payments']['captures']
                        if captures and len(captures) > 0:
                            transaction_id = captures[0]['id']

                return {
                    "success": True,
                    "capture": capture_data,
                    "transaction_id": transaction_id
                }
            else:
                return {
                    "success": False,
                    "error": capture_response.text,
                    "message": f"Failed to capture PayPal payment: {capture_response.status_code}"
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Exception occurred while capturing PayPal payment: {str(e)}"
            }

# Singleton instance
paypal_service = PayPalService()
