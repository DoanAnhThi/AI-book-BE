from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional
import json

from src.db.common.database_connection import get_db
from src.db.order.models.order_models import Payment
from src.db.order.models.order_schemas import (
    CheckoutRequest, CheckoutResponse,
    PayPalExecuteRequest, PayPalExecuteResponse,
    CreateOrderRequest, CreateOrderResponse,
    CreatePayPalOrderRequest, CreatePayPalOrderResponse,
    CapturePaymentRequest, CapturePaymentResponse
)
from .payment_service import payment_service
from .paypal_service import paypal_service

router = APIRouter()

@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    request: CheckoutRequest,
    user_id: int = 1,  # Trong thực tế sẽ lấy từ authentication
    db: Session = Depends(get_db)
):
    """
    Tạo checkout session với PayPal

    Args:
        request: Checkout request data
        user_id: User ID (tạm thời hardcode, sau này dùng auth)
        db: Database session

    Returns:
        CheckoutResponse với PayPal approval URL
    """
    try:
        # Lấy base URL từ request
        base_url = "http://localhost:8000"  # Trong production nên dùng environment variable

        result = payment_service.process_paypal_checkout(
            request=request,
            user_id=user_id,
            base_url=base_url,
            db=db
        )

        if not result.success:
            raise HTTPException(status_code=400, detail=result.message)

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Checkout failed: {str(e)}")

@router.get("/success")
async def paypal_success(
    paymentId: str = Query(None, alias="paymentId"),
    PayerID: str = Query(None, alias="PayerID"),
    db: Session = Depends(get_db)
):
    """
    Xử lý khi thanh toán PayPal thành công

    Args:
        paymentId: PayPal payment ID
        PayerID: PayPal payer ID
        db: Database session

    Returns:
        Redirect to success page hoặc JSON response
    """
    if not paymentId or not PayerID:
        raise HTTPException(status_code=400, detail="Missing paymentId or PayerID")

    try:
        result = payment_service.process_paypal_success(
            payment_id=paymentId,
            payer_id=PayerID,
            db=db
        )

        if result.success:
            # Trả về JSON response với thông tin đơn hàng
            return {
                "success": True,
                "message": "Payment completed successfully",
                "order": result.order,
                "payment": result.payment
            }
        else:
            # Redirect về trang lỗi
            error_url = f"http://localhost:3000/checkout/error?message={result.message}"
            return RedirectResponse(url=error_url)

    except Exception as e:
        error_url = f"http://localhost:3000/checkout/error?message={str(e)}"
        return RedirectResponse(url=error_url)

@router.get("/cancel")
async def paypal_cancel(
    token: str = Query(None),  # PayPal token (có thể là payment ID)
    db: Session = Depends(get_db)
):
    """
    Xử lý khi người dùng hủy thanh toán PayPal

    Args:
        token: PayPal token
        db: Database session

    Returns:
        Redirect to cancel page
    """
    try:
        if token:
            payment_service.process_paypal_cancel(token, db)

        # Redirect về trang checkout hoặc cancel page
        cancel_url = "http://localhost:3000/checkout?cancelled=true"
        return RedirectResponse(url=cancel_url)

    except Exception as e:
        cancel_url = f"http://localhost:3000/checkout?error={str(e)}"
        return RedirectResponse(url=cancel_url)

@router.post("/webhook")
async def paypal_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Xử lý PayPal webhook notifications

    Args:
        request: Webhook request từ PayPal
        db: Database session

    Returns:
        Webhook response
    """
    try:
        # Lấy webhook data
        body = await request.body()
        webhook_body = body.decode('utf-8')

        # Lấy headers
        signature = request.headers.get('paypal-transmission-signature')
        cert_url = request.headers.get('paypal-cert-url')
        transmission_id = request.headers.get('paypal-transmission-id')
        timestamp = request.headers.get('paypal-transmission-time')
        webhook_id = request.headers.get('paypal-webhook-id')

        # Parse webhook data
        webhook_data = json.loads(webhook_body)

        # Xử lý các loại event khác nhau
        event_type = webhook_data.get('event_type')

        if event_type == 'PAYMENT.SALE.COMPLETED':
            # Thanh toán hoàn tất
            sale_id = webhook_data.get('resource', {}).get('id')
            payment_id = webhook_data.get('resource', {}).get('parent_payment')

            # Tìm và cập nhật payment record
            payment = db.query(Payment).filter(
                Payment.paypal_transaction_id == sale_id
            ).first()

            if payment:
                payment.status = 'completed'
                db.commit()

        elif event_type == 'PAYMENT.SALE.DENIED':
            # Thanh toán bị từ chối
            sale_id = webhook_data.get('resource', {}).get('id')

            payment = db.query(Payment).filter(
                Payment.paypal_transaction_id == sale_id
            ).first()

            if payment:
                payment.status = 'denied'
                # Cập nhật order status
                payment_service.update_order_status(payment.order_id, 'failed', db)

        elif event_type == 'PAYMENT.SALE.REFUNDED':
            # Hoàn tiền
            sale_id = webhook_data.get('resource', {}).get('id')

            payment = db.query(Payment).filter(
                Payment.paypal_transaction_id == sale_id
            ).first()

            if payment:
                payment.status = 'refunded'
                payment_service.update_order_status(payment.order_id, 'refunded', db)

        # Trả về 200 OK để xác nhận đã nhận webhook
        return {"status": "ok"}

    except Exception as e:
        # Log lỗi nhưng vẫn trả về 200 để PayPal không retry
        print(f"Webhook processing error: {e}")
        return {"status": "error", "message": str(e)}

@router.post("/execute", response_model=PayPalExecuteResponse)
async def execute_payment(
    request: PayPalExecuteRequest,
    db: Session = Depends(get_db)
):
    """
    Thực hiện thanh toán PayPal (alternative endpoint)

    Args:
        request: Execute request với payment_id và payer_id
        db: Database session

    Returns:
        Execute response
    """
    try:
        result = payment_service.process_paypal_success(
            payment_id=request.payment_id,
            payer_id=request.payer_id,
            db=db
        )

        if not result.success:
            raise HTTPException(status_code=400, detail=result.message)

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Payment execution failed: {str(e)}")

@router.get("/orders/{order_id}")
async def get_order_details(
    order_id: int,
    db: Session = Depends(get_db)
):
    """
    Lấy chi tiết đơn hàng

    Args:
        order_id: Order ID
        db: Database session

    Returns:
        Order details
    """
    try:
        from src.db.order.services.order_service import OrderService

        order = OrderService.get_order_with_details(db, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        return order

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get order details: {str(e)}")

# Client-side PayPal endpoints
@router.post("/create-order", response_model=CreateOrderResponse)
async def create_order(
    request: CreateOrderRequest,
    user_id: int = 1,  # Trong thực tế sẽ lấy từ authentication
    db: Session = Depends(get_db)
):
    """
    Tạo order trong database (cho client-side PayPal flow)

    Args:
        request: Create order request data
        user_id: User ID (tạm thời hardcode, sau này dùng auth)
        db: Database session

    Returns:
        CreateOrderResponse với order_id
    """
    try:
        order = payment_service.create_order(
            CheckoutRequest(**request.dict()),
            user_id,
            db
        )

        return CreateOrderResponse(
            order_id=order.id,
            message="Order created successfully",
            success=True
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create order: {str(e)}")

@router.post("/create-paypal-order", response_model=CreatePayPalOrderResponse)
async def create_paypal_order(
    request: CreatePayPalOrderRequest,
    db: Session = Depends(get_db)
):
    """
    Tạo PayPal order cho client-side payment

    Args:
        request: Create PayPal order request
        db: Database session

    Returns:
        CreatePayPalOrderResponse với paypal_order_id
    """
    try:
        # Lấy order từ database
        order = payment_service.get_order_by_id(request.order_id, db)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        # Tạo PayPal order sử dụng PayPal SDK
        paypal_result = paypal_service.create_paypal_order(order, db)

        if paypal_result["success"]:
            # Tạo payment record trong DB
            payment = payment_service.create_payment_record(
                order_id=order.id,
                paypal_payment_id=paypal_result["paypal_order_id"],
                amount=order.total_amount,
                status="created",
                paypal_response={"order": str(paypal_result["order"])},
                db=db
            )

            return CreatePayPalOrderResponse(
                paypal_order_id=paypal_result["paypal_order_id"],
                message="PayPal order created successfully",
                success=True
            )
        else:
            raise HTTPException(status_code=400, detail=paypal_result.get("message", "Failed to create PayPal order"))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create PayPal order: {str(e)}")

@router.post("/capture-payment", response_model=CapturePaymentResponse)
async def capture_payment(
    request: CapturePaymentRequest,
    db: Session = Depends(get_db)
):
    """
    Capture payment sau khi user approve (client-side flow)

    Args:
        request: Capture payment request
        db: Database session

    Returns:
        CapturePaymentResponse
    """
    try:
        # Capture payment với PayPal
        paypal_result = paypal_service.capture_paypal_payment(
            paypal_order_id=request.order_id,
            db=db
        )

        if paypal_result["success"]:
            # Tìm payment record trong DB
            payment = db.query(Payment).filter(
                Payment.paypal_payment_id == request.order_id
            ).first()

            if payment:
                # Update payment record
                payment.paypal_payer_id = request.payer_id
                payment.paypal_transaction_id = paypal_result.get("transaction_id")
                payment.status = "approved"
                payment.paypal_response = json.dumps({"capture": str(paypal_result["capture"])})
                db.commit()

                # Update order status
                payment_service.update_order_status(payment.order_id, "paid", db)

                return CapturePaymentResponse(
                    order_id=payment.order_id,
                    payment_id=payment.id,
                    transaction_id=paypal_result.get("transaction_id"),
                    message="Payment captured successfully",
                    success=True
                )
            else:
                raise HTTPException(status_code=404, detail="Payment record not found")
        else:
            raise HTTPException(status_code=400, detail=paypal_result.get("message", "Failed to capture payment"))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to capture payment: {str(e)}")

@router.get("/client-config")
async def get_paypal_client_config():
    """
    Trả về PayPal client configuration cho frontend

    Returns:
        Dict chứa client_id
    """
    try:
        import os
        client_id = os.getenv("PAYPAL_CLIENT_ID", "")

        if not client_id:
            raise HTTPException(status_code=500, detail="PayPal client ID not configured")

        return {
            "client_id": client_id,
            "environment": "sandbox" if os.getenv("PAYPAL_MODE", "sandbox") == "sandbox" else "production"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get PayPal config: {str(e)}")
