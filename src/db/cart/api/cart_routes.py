from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from src.db.common.database_connection import get_db
from src.db.cart.services.cart_service import CartService
from src.db.cart.models.cart_schemas import Cart, CartCreate, CartUpdate

router = APIRouter()

@router.post("/cart/", response_model=Cart, status_code=status.HTTP_201_CREATED)
async def add_to_cart(cart: CartCreate, db: Session = Depends(get_db)):
    """Thêm item vào giỏ hàng"""
    return CartService.add_to_cart(db, cart)

@router.get("/cart/{user_id}", response_model=List[Cart])
async def get_user_cart(user_id: int, db: Session = Depends(get_db)):
    """Lấy giỏ hàng của user"""
    return CartService.get_user_cart(db, user_id)

@router.get("/cart/{user_id}/total", response_model=Dict[str, Any])
async def get_cart_total(user_id: int, db: Session = Depends(get_db)):
    """Lấy tổng giá trị giỏ hàng của user"""
    return CartService.get_cart_total(db, user_id)

@router.put("/cart/{cart_id}", response_model=Cart)
async def update_cart_item(cart_id: int, cart_update: CartUpdate, db: Session = Depends(get_db)):
    """Cập nhật item trong giỏ hàng"""
    db_cart = CartService.update_cart_item(db, cart_id, cart_update)
    if not db_cart:
        raise HTTPException(status_code=404, detail="Cart item không tồn tại")
    return db_cart

@router.delete("/cart/{cart_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_cart(cart_id: int, db: Session = Depends(get_db)):
    """Xóa item khỏi giỏ hàng"""
    success = CartService.remove_from_cart(db, cart_id)
    if not success:
        raise HTTPException(status_code=404, detail="Cart item không tồn tại")

@router.delete("/cart/user/{user_id}/clear", response_model=Dict[str, int])
async def clear_user_cart(user_id: int, db: Session = Depends(get_db)):
    """Xóa tất cả items trong giỏ hàng của user"""
    deleted_count = CartService.clear_user_cart(db, user_id)
    return {"deleted_items": deleted_count}
