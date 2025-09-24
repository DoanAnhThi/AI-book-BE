from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, Dict, Any
from decimal import Decimal

from src.db.order.models.order_models import Order, Payment
from src.db.user.models.user_models import User
# Note: Book model không tồn tại trong cấu trúc hiện tại
from src.db.order.models.order_schemas import (
    OrderCreate, OrderUpdate, PaymentCreate, PaymentUpdate,
    CheckoutRequest, CheckoutResponse, PayPalExecuteResponse
)
from .paypal_service import paypal_service
import json

class PaymentService:
    """Service xử lý business logic cho thanh toán"""

    @staticmethod
    def create_order(
        request: CheckoutRequest,
        user_id: int,
        db: Session
    ) -> Order:
        """
        Tạo đơn hàng mới

        Args:
            request: Checkout request data
            user_id: User ID
            db: Database session

        Returns:
            Order object
        """
        # Tính tổng tiền (ví dụ: $11.99 cho sách)
        total_amount = Decimal("11.99")

        order_data = OrderCreate(
            user_id=user_id,
            total_amount=total_amount,
            currency="USD",
            full_name=request.full_name,
            email=request.email,
            address=request.address,
            city=request.city,
            zip_code=request.zip_code,
            country=request.country,
            payment_method=request.payment_method
        )

        order = Order(**order_data.dict())
        db.add(order)
        db.commit()
        db.refresh(order)

        return order

    @staticmethod
    def get_order_by_id(order_id: int, db: Session) -> Optional[Order]:
        """Lấy đơn hàng theo ID"""
        return db.query(Order).filter(Order.id == order_id).first()

    @staticmethod
    def update_order_status(
        order_id: int,
        status: str,
        db: Session
    ) -> Optional[Order]:
        """Cập nhật trạng thái đơn hàng"""
        order = db.query(Order).filter(Order.id == order_id).first()
        if order:
            order.status = status
            db.commit()
            db.refresh(order)
        return order

    @staticmethod
    def create_payment_record(
        order_id: int,
        paypal_payment_id: str,
        amount: Decimal,
        status: str,
        paypal_response: Optional[Dict] = None,
        db: Session = None
    ) -> Payment:
        """
        Tạo bản ghi thanh toán

        Args:
            order_id: Order ID
            paypal_payment_id: PayPal payment ID
            amount: Payment amount
            status: Payment status
            paypal_response: PayPal response data
            db: Database session

        Returns:
            Payment object
        """
        payment_data = PaymentCreate(
            order_id=order_id,
            paypal_payment_id=paypal_payment_id,
            amount=amount,
            currency="USD",
            status=status,
            payment_method="paypal",
            paypal_response=json.dumps(paypal_response) if paypal_response else None
        )

        payment = Payment(**payment_data.dict())
        db.add(payment)
        db.commit()
        db.refresh(payment)

        return payment

    @staticmethod
    def update_payment_record(
        payment_id: int,
        updates: PaymentUpdate,
        db: Session
    ) -> Optional[Payment]:
        """Cập nhật bản ghi thanh toán"""
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        if payment:
            for field, value in updates.dict(exclude_unset=True).items():
                setattr(payment, field, value)
            db.commit()
            db.refresh(payment)
        return payment

    @staticmethod
    def process_paypal_checkout(
        request: CheckoutRequest,
        user_id: int,
        base_url: str,
        db: Session
    ) -> CheckoutResponse:
        """
        Xử lý checkout với PayPal

        Args:
            request: Checkout request
            user_id: User ID
            base_url: Base URL cho redirect
            db: Database session

        Returns:
            CheckoutResponse
        """
        try:
            # Tạo đơn hàng
            order = PaymentService.create_order(request, user_id, db)

            # Tạo URL redirect
            success_url = f"{base_url}/api/v1/payments/paypal/success"
            cancel_url = f"{base_url}/api/v1/payments/paypal/cancel"

            # Tạo payment PayPal
            paypal_result = paypal_service.create_payment(
                order=order,
                success_url=success_url,
                cancel_url=cancel_url,
                db=db
            )

            if paypal_result["success"]:
                # Tạo bản ghi payment trong DB
                payment = PaymentService.create_payment_record(
                    order_id=order.id,
                    paypal_payment_id=paypal_result["payment_id"],
                    amount=order.total_amount,
                    status="created",
                    paypal_response={"payment": str(paypal_result["payment"])},
                    db=db
                )

                return CheckoutResponse(
                    order=order,
                    paypal_approval_url=paypal_result["approval_url"],
                    message="Payment created successfully",
                    success=True
                )
            else:
                # Cập nhật trạng thái đơn hàng thành failed
                PaymentService.update_order_status(order.id, "failed", db)

                return CheckoutResponse(
                    order=order,
                    message=f"Failed to create PayPal payment: {paypal_result.get('message', 'Unknown error')}",
                    success=False
                )

        except SQLAlchemyError as e:
            db.rollback()
            return CheckoutResponse(
                order=None,
                message=f"Database error: {str(e)}",
                success=False
            )
        except Exception as e:
            return CheckoutResponse(
                order=None,
                message=f"Unexpected error: {str(e)}",
                success=False
            )

    @staticmethod
    def process_paypal_success(
        payment_id: str,
        payer_id: str,
        db: Session
    ) -> PayPalExecuteResponse:
        """
        Xử lý thanh toán thành công từ PayPal

        Args:
            payment_id: PayPal payment ID
            payer_id: PayPal payer ID
            db: Database session

        Returns:
            PayPalExecuteResponse
        """
        try:
            # Thực hiện thanh toán PayPal
            paypal_result = paypal_service.execute_payment(
                payment_id=payment_id,
                payer_id=payer_id,
                db=db
            )

            if paypal_result["success"]:
                # Tìm payment record trong DB
                payment = db.query(Payment).filter(
                    Payment.paypal_payment_id == payment_id
                ).first()

                if payment:
                    # Cập nhật payment record
                    updates = PaymentUpdate(
                        paypal_payer_id=payer_id,
                        paypal_transaction_id=paypal_result.get("transaction_id"),
                        status="approved",
                        paypal_response=json.dumps({"payment": str(paypal_result["payment"])})
                    )
                    PaymentService.update_payment_record(payment.id, updates, db)

                    # Cập nhật trạng thái đơn hàng
                    PaymentService.update_order_status(payment.order_id, "paid", db)

                    # Tải lại order với thông tin mới
                    order = PaymentService.get_order_by_id(payment.order_id, db)

                    return PayPalExecuteResponse(
                        payment=payment,
                        order=order,
                        message="Payment completed successfully",
                        success=True
                    )
                else:
                    return PayPalExecuteResponse(
                        payment=None,
                        order=None,
                        message="Payment record not found in database",
                        success=False
                    )
            else:
                return PayPalExecuteResponse(
                    payment=None,
                    order=None,
                    message=f"PayPal execution failed: {paypal_result.get('message', 'Unknown error')}",
                    success=False
                )

        except Exception as e:
            return PayPalExecuteResponse(
                payment=None,
                order=None,
                message=f"Unexpected error: {str(e)}",
                success=False
            )

    @staticmethod
    def process_paypal_cancel(payment_id: str, db: Session) -> Dict[str, Any]:
        """
        Xử lý hủy thanh toán từ PayPal

        Args:
            payment_id: PayPal payment ID
            db: Database session

        Returns:
            Dict với kết quả xử lý
        """
        try:
            # Tìm payment record trong DB
            payment = db.query(Payment).filter(
                Payment.paypal_payment_id == payment_id
            ).first()

            if payment:
                # Cập nhật trạng thái payment và order
                PaymentService.update_payment_record(
                    payment.id,
                    PaymentUpdate(status="cancelled"),
                    db
                )
                PaymentService.update_order_status(payment.order_id, "cancelled", db)

                return {
                    "success": True,
                    "message": "Payment cancelled successfully"
                }
            else:
                return {
                    "success": False,
                    "message": "Payment record not found"
                }

        except Exception as e:
            return {
                "success": False,
                "message": f"Error processing cancellation: {str(e)}"
            }

# Singleton instance
payment_service = PaymentService()
