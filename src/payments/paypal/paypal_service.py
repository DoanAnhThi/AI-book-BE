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

            # Thực hiện thanh toán
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

# Singleton instance
paypal_service = PayPalService()
