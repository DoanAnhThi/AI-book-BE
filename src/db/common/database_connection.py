from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database settings
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://username:password@localhost:5432/gen_book_db")

# SQLAlchemy setup
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Test connections before using them
    pool_recycle=300,    # Recycle connections after 5 minutes
    echo=False           # Set to True for SQL query logging in development
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """
    Dependency để inject database session vào FastAPI routes
    Sử dụng trong routes với: db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """
    Tạo tất cả tables trong database
    Gọi hàm này khi khởi tạo ứng dụng lần đầu
    """
    Base.metadata.create_all(bind=engine)

def drop_tables():
    """
    Xóa tất cả tables (chỉ dùng trong development/testing)
    """
    Base.metadata.drop_all(bind=engine)

def init_database():
    """
    Khởi tạo database - tạo tables nếu chưa tồn tại
    """
    try:
        create_tables()
        print("Database tables created successfully")
    except Exception as e:
        print(f"Error creating database tables: {e}")
        raise
