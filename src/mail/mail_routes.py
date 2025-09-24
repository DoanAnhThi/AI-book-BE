from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
from pydantic import BaseModel, EmailStr

from src.mail.mail_service import mail_service

router = APIRouter()

class PaymentSuccessRequest(BaseModel):
    recipient_email: EmailStr
    order_id: str
    total_amount: float
    status: str = "Đã thanh toán"

class EbookUrlRequest(BaseModel):
    recipient_email: EmailStr
    order_id: str
    book_title: str
    ebook_url: str

@router.post("/mail/payment-success", response_model=Dict[str, str])
async def send_payment_success_email(request: PaymentSuccessRequest):
    """
    Gửi email thông báo thanh toán thành công

    - **recipient_email**: Email người nhận
    - **order_id**: Mã đơn hàng
    - **total_amount**: Tổng tiền
    - **status**: Trạng thái đơn hàng (mặc định: "Đã thanh toán")
    """
    order_details = {
        "order_id": request.order_id,
        "total_amount": request.total_amount,
        "status": request.status
    }

    result = mail_service.send_payment_success_email(request.recipient_email, order_details)

    if result["status"] == "error":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result["message"]
        )

    return result

@router.post("/mail/send-ebook", response_model=Dict[str, str])
async def send_ebook_url_email(request: EbookUrlRequest):
    """
    Gửi email chứa URL ebook cho khách hàng

    - **recipient_email**: Email người nhận
    - **order_id**: Mã đơn hàng
    - **book_title**: Tên sách
    - **ebook_url**: URL để tải ebook
    """
    ebook_details = {
        "order_id": request.order_id,
        "book_title": request.book_title,
        "ebook_url": request.ebook_url
    }

    result = mail_service.send_ebook_url_email(request.recipient_email, ebook_details)

    if result["status"] == "error":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result["message"]
        )

    return result
