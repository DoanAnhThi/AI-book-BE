from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal

# Cart schemas
class CartBase(BaseModel):
    book_request_data: str
    quantity: int = 1
    price: Decimal
    currency: str = "USD"

class CartCreate(CartBase):
    user_id: int

class CartUpdate(BaseModel):
    book_request_data: Optional[str] = None
    quantity: Optional[int] = None
    price: Optional[Decimal] = None
    currency: Optional[str] = None

class Cart(CartBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
