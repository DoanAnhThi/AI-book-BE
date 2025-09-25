from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime

from src.db.common.database_connection import Base

class Order(Base):
    """Model cho đơn hàng"""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    book_id = Column(Integer)  # Có thể null nếu chưa tạo book
    total_amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD")
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    address = Column(Text, nullable=False)
    city = Column(String(100), nullable=False)
    zip_code = Column(String(20), nullable=False)
    country = Column(String(100), nullable=False)
    payment_method = Column(String(50), default="paypal")
    status = Column(String(50), default="pending")  # pending, paid, shipped, delivered, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    payments = relationship("Payment", back_populates="order", cascade="all, delete-orphan")


class Payment(Base):
    """Model cho thanh toán"""
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    paypal_payment_id = Column(String(100), unique=True)
    paypal_payer_id = Column(String(100))
    paypal_transaction_id = Column(String(100))
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD")
    status = Column(String(50), nullable=False)  # created, approved, failed, cancelled, completed
    payment_method = Column(String(50), default="paypal")
    paypal_response = Column(Text)  # JSON response từ PayPal
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    order = relationship("Order", back_populates="payments")
