from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    """Model cho người dùng"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(255))
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    books = relationship("Book", back_populates="user", cascade="all, delete-orphan")

class Book(Base):
    """Model cho sách được tạo"""
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    book_type = Column(String(100), nullable=False)  # Loại sách (Khoa học viễn tưởng, etc.)
    character_name = Column(String(255), nullable=False)  # Tên nhân vật chính
    style = Column(String(50), default="realistic")  # "realistic" hoặc "cartoon"
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reference_image_url = Column(Text)  # URL ảnh tham khảo gốc
    pdf_url = Column(Text)  # URL của file PDF đã tạo
    is_completed = Column(Boolean, default=False)
    processing_time = Column(Float)  # Thời gian xử lý (giây)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="books")
    pages = relationship("BookPage", back_populates="book", cascade="all, delete-orphan", order_by="BookPage.page_number")

class BookPage(Base):
    """Model cho từng trang của sách"""
    __tablename__ = "book_pages"

    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    page_number = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)  # Nội dung text của trang
    image_prompt = Column(Text)  # Prompt sử dụng để tạo ảnh
    generated_image_url = Column(Text)  # URL ảnh đã tạo
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    book = relationship("Book", back_populates="pages")

class GenerationLog(Base):
    """Model để log các lần tạo sách"""
    __tablename__ = "generation_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    operation_type = Column(String(100), nullable=False)  # "script_gen", "image_gen", "pdf_gen", etc.
    status = Column(String(50), default="success")  # "success", "error", "pending"
    input_data = Column(Text)  # JSON string chứa input parameters
    output_data = Column(Text)  # JSON string chứa kết quả hoặc error message
    processing_time = Column(Float)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User")
