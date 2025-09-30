from fastapi import APIRouter, HTTPException
from .apple_pay_service import apple_pay_service

router = APIRouter()

@router.get("/availability")
async def check_apple_pay_availability():
    """
    Kiểm tra Apple Pay availability

    Returns:
        Apple Pay availability info
    """
    try:
        result = apple_pay_service.check_apple_pay_availability()

        if not result["available"]:
            raise HTTPException(status_code=400, detail=result["message"])

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Apple Pay availability check failed: {str(e)}")

@router.post("/validate-merchant")
async def validate_apple_pay_merchant():
    """
    Validate Apple Pay merchant

    Returns:
        Merchant validation result
    """
    try:
        result = apple_pay_service.validate_merchant()

        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Apple Pay merchant validation failed: {str(e)}")
