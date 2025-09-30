from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any
from .amazon_pay_service import amazon_pay_service

router = APIRouter()

class CreateCheckoutSessionRequest(BaseModel):
    amount: str = "11.99"
    currency: str = "USD"
    order_id: str = ""

@router.get("/config")
async def get_amazon_pay_config():
    """
    Lấy Amazon Pay configuration

    Returns:
        Amazon Pay config for client
    """
    try:
        result = amazon_pay_service.get_amazon_pay_config()

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get Amazon Pay config: {str(e)}")

@router.post("/create-checkout-session")
async def create_amazon_pay_checkout_session(request: CreateCheckoutSessionRequest):
    """
    Tạo Amazon Pay checkout session

    Args:
        request: Checkout session request data

    Returns:
        Checkout session info
    """
    try:
        order_data = {
            "amount": request.amount,
            "currency": request.currency,
            "order_id": request.order_id
        }

        result = amazon_pay_service.create_checkout_session(order_data)

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create Amazon Pay checkout session: {str(e)}")

@router.get("/success")
async def amazon_pay_success(sessionId: str = Query(None)):
    """
    Handle Amazon Pay success callback

    Args:
        sessionId: Checkout session ID

    Returns:
        Success response
    """
    try:
        if not sessionId:
            raise HTTPException(status_code=400, detail="Missing sessionId")

        result = amazon_pay_service.complete_checkout_session(sessionId)

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])

        return {
            "success": True,
            "message": "Amazon Pay payment completed successfully",
            "data": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Amazon Pay success handling failed: {str(e)}")

@router.get("/cancel")
async def amazon_pay_cancel(sessionId: str = Query(None)):
    """
    Handle Amazon Pay cancel callback

    Args:
        sessionId: Checkout session ID

    Returns:
        Cancel response
    """
    return {
        "success": False,
        "message": "Amazon Pay payment cancelled",
        "sessionId": sessionId
    }
