from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from .google_pay_service import google_pay_service

router = APIRouter()

class GooglePayPaymentRequest(BaseModel):
    payment_data: Dict[str, Any]

@router.get("/config")
async def get_google_pay_config():
    """
    Lấy Google Pay configuration

    Returns:
        Google Pay config for client
    """
    try:
        result = google_pay_service.get_google_pay_config()

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get Google Pay config: {str(e)}")

@router.post("/process-payment")
async def process_google_pay_payment(request: GooglePayPaymentRequest):
    """
    Xử lý Google Pay payment

    Args:
        request: Google Pay payment data

    Returns:
        Payment processing result
    """
    try:
        result = google_pay_service.process_google_pay_payment(request.payment_data)

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process Google Pay payment: {str(e)}")
