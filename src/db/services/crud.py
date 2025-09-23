from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
from typing import List, Optional, Dict, Any
import json
from datetime import datetime, timedelta

from src.db.models.database import User, Book, BookPage, GenerationLog
from src.db.models.schemas import (
    UserCreate, UserUpdate, BookCreate, BookUpdate,
    BookPageCreate, BookPageUpdate, GenerationLogCreate
)

# User CRUD operations
class UserService:
    @staticmethod
    def get_user(db: Session, user_id: int) -> Optional[User]:
        """Lấy user theo ID"""
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """Lấy user theo email"""
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """Lấy user theo username"""
        return db.query(User).filter(User.username == username).first()

    @staticmethod
    def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        """Lấy danh sách users với pagination"""
        return db.query(User).offset(skip).limit(limit).all()

    @staticmethod
    def create_user(db: Session, user: UserCreate) -> User:
        """Tạo user mới"""
        from passlib.context import CryptContext

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hashed_password = pwd_context.hash(user.password)

        db_user = User(
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            hashed_password=hashed_password,
            is_active=user.is_active,
            is_superuser=user.is_superuser
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def update_user(db: Session, user_id: int, user_update: UserUpdate) -> Optional[User]:
        """Cập nhật thông tin user"""
        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            return None

        update_data = user_update.dict(exclude_unset=True)
        if "password" in update_data:
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            update_data["hashed_password"] = pwd_context.hash(update_data.pop("password"))

        for field, value in update_data.items():
            setattr(db_user, field, value)

        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def delete_user(db: Session, user_id: int) -> bool:
        """Xóa user"""
        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            return False

        db.delete(db_user)
        db.commit()
        return True

    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        """Xác thực user với username và password"""
        user = db.query(User).filter(
            and_(User.username == username, User.is_active == True)
        ).first()

        if not user:
            return None

        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        if not pwd_context.verify(password, user.hashed_password):
            return None

        return user

# Book CRUD operations
class BookService:
    @staticmethod
    def get_book(db: Session, book_id: int) -> Optional[Book]:
        """Lấy book theo ID"""
        return db.query(Book).filter(Book.id == book_id).first()

    @staticmethod
    def get_books_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[Book]:
        """Lấy danh sách books của một user"""
        return db.query(Book).filter(Book.user_id == user_id)\
            .order_by(desc(Book.created_at))\
            .offset(skip).limit(limit).all()

    @staticmethod
    def get_books(db: Session, skip: int = 0, limit: int = 100) -> List[Book]:
        """Lấy tất cả books với pagination"""
        return db.query(Book).order_by(desc(Book.created_at))\
            .offset(skip).limit(limit).all()

    @staticmethod
    def create_book(db: Session, book: BookCreate) -> Book:
        """Tạo book mới"""
        db_book = Book(**book.dict())
        db.add(db_book)
        db.commit()
        db.refresh(db_book)
        return db_book

    @staticmethod
    def update_book(db: Session, book_id: int, book_update: BookUpdate) -> Optional[Book]:
        """Cập nhật thông tin book"""
        db_book = db.query(Book).filter(Book.id == book_id).first()
        if not db_book:
            return None

        update_data = book_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_book, field, value)

        db.commit()
        db.refresh(db_book)
        return db_book

    @staticmethod
    def delete_book(db: Session, book_id: int) -> bool:
        """Xóa book"""
        db_book = db.query(Book).filter(Book.id == book_id).first()
        if not db_book:
            return False

        db.delete(db_book)
        db.commit()
        return True

    @staticmethod
    def get_book_with_pages(db: Session, book_id: int) -> Optional[Book]:
        """Lấy book cùng với tất cả pages"""
        return db.query(Book).filter(Book.id == book_id)\
            .options(db.joinedload(Book.pages))\
            .first()

    @staticmethod
    def get_books_stats(db: Session) -> Dict[str, Any]:
        """Lấy thống kê về books"""
        total_books = db.query(func.count(Book.id)).scalar()
        completed_books = db.query(func.count(Book.id)).filter(Book.is_completed == True).scalar()
        avg_processing_time = db.query(func.avg(Book.processing_time)).filter(Book.processing_time.isnot(None)).scalar()

        return {
            "total_books": total_books,
            "completed_books": completed_books,
            "avg_processing_time": avg_processing_time
        }

# BookPage CRUD operations
class BookPageService:
    @staticmethod
    def get_page(db: Session, page_id: int) -> Optional[BookPage]:
        """Lấy page theo ID"""
        return db.query(BookPage).filter(BookPage.id == page_id).first()

    @staticmethod
    def get_pages_by_book(db: Session, book_id: int) -> List[BookPage]:
        """Lấy tất cả pages của một book"""
        return db.query(BookPage).filter(BookPage.book_id == book_id)\
            .order_by(BookPage.page_number).all()

    @staticmethod
    def create_page(db: Session, page: BookPageCreate) -> BookPage:
        """Tạo page mới"""
        db_page = BookPage(**page.dict())
        db.add(db_page)
        db.commit()
        db.refresh(db_page)
        return db_page

    @staticmethod
    def create_pages_batch(db: Session, pages: List[BookPageCreate]) -> List[BookPage]:
        """Tạo nhiều pages cùng lúc"""
        db_pages = [BookPage(**page.dict()) for page in pages]
        db.add_all(db_pages)
        db.commit()
        for page in db_pages:
            db.refresh(page)
        return db_pages

    @staticmethod
    def update_page(db: Session, page_id: int, page_update: BookPageUpdate) -> Optional[BookPage]:
        """Cập nhật thông tin page"""
        db_page = db.query(BookPage).filter(BookPage.id == page_id).first()
        if not db_page:
            return None

        update_data = page_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_page, field, value)

        db.commit()
        db.refresh(db_page)
        return db_page

    @staticmethod
    def delete_page(db: Session, page_id: int) -> bool:
        """Xóa page"""
        db_page = db.query(BookPage).filter(BookPage.id == page_id).first()
        if not db_page:
            return False

        db.delete(db_page)
        db.commit()
        return True

# GenerationLog CRUD operations
class GenerationLogService:
    @staticmethod
    def get_log(db: Session, log_id: int) -> Optional[GenerationLog]:
        """Lấy log theo ID"""
        return db.query(GenerationLog).filter(GenerationLog.id == log_id).first()

    @staticmethod
    def get_logs_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[GenerationLog]:
        """Lấy logs của một user"""
        return db.query(GenerationLog).filter(GenerationLog.user_id == user_id)\
            .order_by(desc(GenerationLog.created_at))\
            .offset(skip).limit(limit).all()

    @staticmethod
    def get_logs_by_operation(db: Session, operation_type: str, skip: int = 0, limit: int = 100) -> List[GenerationLog]:
        """Lấy logs theo loại operation"""
        return db.query(GenerationLog).filter(GenerationLog.operation_type == operation_type)\
            .order_by(desc(GenerationLog.created_at))\
            .offset(skip).limit(limit).all()

    @staticmethod
    def create_log(db: Session, log: GenerationLogCreate) -> GenerationLog:
        """Tạo log mới"""
        db_log = GenerationLog(**log.dict())
        db.add(db_log)
        db.commit()
        db.refresh(db_log)
        return db_log

    @staticmethod
    def log_operation(db: Session, operation_type: str, status: str = "success",
                     user_id: Optional[int] = None, input_data: Optional[Dict] = None,
                     output_data: Optional[Dict] = None, processing_time: Optional[float] = None,
                     error_message: Optional[str] = None) -> GenerationLog:
        """Helper method để log một operation"""
        log_data = {
            "operation_type": operation_type,
            "status": status,
            "user_id": user_id,
            "input_data": json.dumps(input_data) if input_data else None,
            "output_data": json.dumps(output_data) if output_data else None,
            "processing_time": processing_time,
            "error_message": error_message
        }

        log_create = GenerationLogCreate(**log_data)
        return GenerationLogService.create_log(db, log_create)

    @staticmethod
    def get_generation_stats(db: Session, days: int = 30) -> Dict[str, Any]:
        """Lấy thống kê generation trong khoảng thời gian"""
        since_date = datetime.utcnow() - timedelta(days=days)

        total_logs = db.query(func.count(GenerationLog.id))\
            .filter(GenerationLog.created_at >= since_date).scalar()

        success_logs = db.query(func.count(GenerationLog.id))\
            .filter(and_(GenerationLog.created_at >= since_date, GenerationLog.status == "success")).scalar()

        error_logs = db.query(func.count(GenerationLog.id))\
            .filter(and_(GenerationLog.created_at >= since_date, GenerationLog.status == "error")).scalar()

        avg_processing_time = db.query(func.avg(GenerationLog.processing_time))\
            .filter(and_(GenerationLog.created_at >= since_date, GenerationLog.processing_time.isnot(None))).scalar()

        return {
            "total_operations": total_logs,
            "successful_operations": success_logs,
            "failed_operations": error_logs,
            "success_rate": (success_logs / total_logs * 100) if total_logs > 0 else 0,
            "avg_processing_time": avg_processing_time,
            "period_days": days
        }
