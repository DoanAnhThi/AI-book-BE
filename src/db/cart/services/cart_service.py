from sqlalchemy.orm import Session, desc
from typing import List, Optional, Dict, Any

from src.db.cart.models.cart_models import Cart
from src.db.cart.models.cart_schemas import CartCreate, CartUpdate

class CartService:
    @staticmethod
    def get_cart_item(db: Session, cart_id: int) -> Optional[Cart]:
        """Lấy cart item theo ID"""
        return db.query(Cart).filter(Cart.id == cart_id).first()

    @staticmethod
    def get_user_cart(db: Session, user_id: int) -> List[Cart]:
        """Lấy tất cả cart items của một user"""
        return db.query(Cart).filter(Cart.user_id == user_id)\
            .order_by(desc(Cart.created_at)).all()

    @staticmethod
    def add_to_cart(db: Session, cart: CartCreate) -> Cart:
        """Thêm item vào cart"""
        db_cart = Cart(**cart.dict())
        db.add(db_cart)
        db.commit()
        db.refresh(db_cart)
        return db_cart

    @staticmethod
    def update_cart_item(db: Session, cart_id: int, cart_update: CartUpdate) -> Optional[Cart]:
        """Cập nhật cart item"""
        db_cart = db.query(Cart).filter(Cart.id == cart_id).first()
        if not db_cart:
            return None

        update_data = cart_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_cart, field, value)

        db.commit()
        db.refresh(db_cart)
        return db_cart

    @staticmethod
    def remove_from_cart(db: Session, cart_id: int) -> bool:
        """Xóa item khỏi cart"""
        db_cart = db.query(Cart).filter(Cart.id == cart_id).first()
        if not db_cart:
            return False

        db.delete(db_cart)
        db.commit()
        return True

    @staticmethod
    def clear_user_cart(db: Session, user_id: int) -> int:
        """Xóa tất cả items trong cart của user, trả về số lượng items đã xóa"""
        deleted_count = db.query(Cart).filter(Cart.user_id == user_id).delete()
        db.commit()
        return deleted_count

    @staticmethod
    def get_cart_total(db: Session, user_id: int) -> Dict[str, Any]:
        """Tính tổng giá trị cart của user"""
        from sqlalchemy import func

        result = db.query(
            func.count(Cart.id).label('total_items'),
            func.sum(Cart.price * Cart.quantity).label('total_amount'),
            Cart.currency
        ).filter(Cart.user_id == user_id).group_by(Cart.currency).first()

        if not result:
            return {
                "total_items": 0,
                "total_amount": 0,
                "currency": "USD"
            }

        return {
            "total_items": result.total_items,
            "total_amount": float(result.total_amount) if result.total_amount else 0,
            "currency": result.currency
        }
