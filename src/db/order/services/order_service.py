from sqlalchemy.orm import Session, desc
from typing import List, Optional, Dict, Any

from src.db.order.models.order_models import Order, Payment
from src.db.order.models.order_schemas import OrderCreate, OrderUpdate, PaymentCreate, PaymentUpdate

class OrderService:
    @staticmethod
    def get_order(db: Session, order_id: int) -> Optional[Order]:
        """Lấy order theo ID"""
        return db.query(Order).filter(Order.id == order_id).first()

    @staticmethod
    def get_orders_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Order]:
        """Lấy danh sách orders của một user"""
        return db.query(Order).filter(Order.user_id == user_id)\
            .order_by(desc(Order.created_at))\
            .offset(skip).limit(limit).all()

    @staticmethod
    def get_order_with_details(db: Session, order_id: int) -> Optional[Dict[str, Any]]:
        """Lấy order với đầy đủ thông tin chi tiết"""
        order = db.query(Order).filter(Order.id == order_id)\
            .options(
                db.joinedload(Order.payments)
            ).first()

        if not order:
            return None

        return {
            "order": order,
            "payments": order.payments
        }

    @staticmethod
    def create_order(db: Session, order: OrderCreate) -> Order:
        """Tạo order mới"""
        db_order = Order(**order.dict())
        db.add(db_order)
        db.commit()
        db.refresh(db_order)
        return db_order

    @staticmethod
    def update_order_status(db: Session, order_id: int, status: str) -> Optional[Order]:
        """Cập nhật trạng thái order"""
        order = db.query(Order).filter(Order.id == order_id).first()
        if order:
            order.status = status
            db.commit()
            db.refresh(order)
        return order

    @staticmethod
    def update_order(db: Session, order_id: int, order_update: OrderUpdate) -> Optional[Order]:
        """Cập nhật thông tin order"""
        db_order = db.query(Order).filter(Order.id == order_id).first()
        if not db_order:
            return None

        update_data = order_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_order, field, value)

        db.commit()
        db.refresh(db_order)
        return db_order


class PaymentService:
    @staticmethod
    def get_payment(db: Session, payment_id: int) -> Optional[Payment]:
        """Lấy payment theo ID"""
        return db.query(Payment).filter(Payment.id == payment_id).first()

    @staticmethod
    def get_payment_by_paypal_id(db: Session, paypal_payment_id: str) -> Optional[Payment]:
        """Lấy payment theo PayPal payment ID"""
        return db.query(Payment).filter(Payment.paypal_payment_id == paypal_payment_id).first()

    @staticmethod
    def get_payments_by_order(db: Session, order_id: int) -> List[Payment]:
        """Lấy tất cả payments của một order"""
        return db.query(Payment).filter(Payment.order_id == order_id)\
            .order_by(desc(Payment.created_at)).all()

    @staticmethod
    def create_payment(db: Session, payment: PaymentCreate) -> Payment:
        """Tạo payment mới"""
        db_payment = Payment(**payment.dict())
        db.add(db_payment)
        db.commit()
        db.refresh(db_payment)
        return db_payment

    @staticmethod
    def update_payment(db: Session, payment_id: int, payment_update: PaymentUpdate) -> Optional[Payment]:
        """Cập nhật payment"""
        db_payment = db.query(Payment).filter(Payment.id == payment_id).first()
        if not db_payment:
            return None

        update_data = payment_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_payment, field, value)

        db.commit()
        db.refresh(db_payment)
        return db_payment

    @staticmethod
    def get_payment_with_order(db: Session, payment_id: int) -> Optional[Dict[str, Any]]:
        """Lấy payment với thông tin order"""
        payment = db.query(Payment).filter(Payment.id == payment_id)\
            .options(db.joinedload(Payment.order)).first()

        if not payment:
            return None

        return {
            "payment": payment,
            "order": payment.order
        }
