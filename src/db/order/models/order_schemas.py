from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from decimal import Decimal

# Order schemas
class OrderBase(BaseModel):
    total_amount: Decimal
    currency: str = "USD"
    full_name: str
    email: EmailStr
    address: str
    city: str
    zip_code: str
    country: str
    payment_method: str = "paypal"

class OrderCreate(OrderBase):
    user_id: int

class OrderUpdate(BaseModel):
    book_id: Optional[int] = None
    status: Optional[str] = None
    total_amount: Optional[Decimal] = None
    currency: Optional[str] = None
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    city: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    payment_method: Optional[str] = None

class Order(OrderBase):
    id: int
    user_id: int
    book_id: Optional[int] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Payment schemas
class PaymentBase(BaseModel):
    paypal_payment_id: Optional[str] = None
    paypal_payer_id: Optional[str] = None
    paypal_transaction_id: Optional[str] = None
    amount: Decimal
    currency: str = "USD"
    status: str
    payment_method: str = "paypal"
    paypal_response: Optional[str] = None

class PaymentCreate(PaymentBase):
    order_id: int

class PaymentUpdate(BaseModel):
    paypal_payment_id: Optional[str] = None
    paypal_payer_id: Optional[str] = None
    paypal_transaction_id: Optional[str] = None
    status: Optional[str] = None
    paypal_response: Optional[str] = None

class Payment(PaymentBase):
    id: int
    order_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PaymentWithOrder(Payment):
    order: Order

# Checkout request/response schemas
class CheckoutRequest(BaseModel):
    email: EmailStr
    full_name: str
    address: str
    city: str
    zip_code: str
    country: str
    payment_method: str = "paypal"

class CheckoutResponse(BaseModel):
    order: Order
    paypal_approval_url: Optional[str] = None
    message: str
    success: bool

class PayPalExecuteRequest(BaseModel):
    payment_id: str
    payer_id: str

class PayPalExecuteResponse(BaseModel):
    payment: Payment
    order: Order
    message: str
    success: bool
