from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from src.db.common.database_connection import get_db
from src.db.order.services.order_service import OrderService, PaymentService
from src.db.order.models.order_schemas import Order, OrderCreate, OrderUpdate, Payment, PaymentCreate, PaymentUpdate

router = APIRouter()

# Order routes
@router.post("/orders/", response_model=Order, status_code=status.HTTP_201_CREATED)
async def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    """Tạo order mới"""
    return OrderService.create_order(db, order)

@router.get("/orders/", response_model=List[Order])
async def get_orders_by_user(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Lấy danh sách orders của một user"""
    return OrderService.get_orders_by_user(db, user_id, skip=skip, limit=limit)

@router.get("/orders/{order_id}", response_model=Order)
async def get_order(order_id: int, db: Session = Depends(get_db)):
    """Lấy thông tin order theo ID"""
    db_order = OrderService.get_order(db, order_id)
    if not db_order:
        raise HTTPException(status_code=404, detail="Order không tồn tại")
    return db_order

@router.get("/orders/{order_id}/details", response_model=Dict[str, Any])
async def get_order_with_details(order_id: int, db: Session = Depends(get_db)):
    """Lấy order với đầy đủ thông tin chi tiết"""
    order_details = OrderService.get_order_with_details(db, order_id)
    if not order_details:
        raise HTTPException(status_code=404, detail="Order không tồn tại")
    return order_details

@router.put("/orders/{order_id}", response_model=Order)
async def update_order(order_id: int, order_update: OrderUpdate, db: Session = Depends(get_db)):
    """Cập nhật thông tin order"""
    db_order = OrderService.update_order(db, order_id, order_update)
    if not db_order:
        raise HTTPException(status_code=404, detail="Order không tồn tại")
    return db_order

@router.put("/orders/{order_id}/status", response_model=Order)
async def update_order_status(order_id: int, status: str, db: Session = Depends(get_db)):
    """Cập nhật trạng thái order"""
    db_order = OrderService.update_order_status(db, order_id, status)
    if not db_order:
        raise HTTPException(status_code=404, detail="Order không tồn tại")
    return db_order

# Payment routes
@router.post("/payments/", response_model=Payment, status_code=status.HTTP_201_CREATED)
async def create_payment(payment: PaymentCreate, db: Session = Depends(get_db)):
    """Tạo payment mới"""
    return PaymentService.create_payment(db, payment)

@router.get("/payments/order/{order_id}", response_model=List[Payment])
async def get_payments_by_order(order_id: int, db: Session = Depends(get_db)):
    """Lấy tất cả payments của một order"""
    return PaymentService.get_payments_by_order(db, order_id)

@router.get("/payments/{payment_id}", response_model=Payment)
async def get_payment(payment_id: int, db: Session = Depends(get_db)):
    """Lấy thông tin payment theo ID"""
    db_payment = PaymentService.get_payment(db, payment_id)
    if not db_payment:
        raise HTTPException(status_code=404, detail="Payment không tồn tại")
    return db_payment

@router.get("/payments/paypal/id/{paypal_payment_id}", response_model=Payment)
async def get_payment_by_paypal_id(paypal_payment_id: str, db: Session = Depends(get_db)):
    """Lấy payment theo PayPal payment ID"""
    db_payment = PaymentService.get_payment_by_paypal_id(db, paypal_payment_id)
    if not db_payment:
        raise HTTPException(status_code=404, detail="Payment không tồn tại")
    return db_payment

@router.put("/payments/{payment_id}", response_model=Payment)
async def update_payment(payment_id: int, payment_update: PaymentUpdate, db: Session = Depends(get_db)):
    """Cập nhật payment"""
    db_payment = PaymentService.update_payment(db, payment_id, payment_update)
    if not db_payment:
        raise HTTPException(status_code=404, detail="Payment không tồn tại")
    return db_payment
