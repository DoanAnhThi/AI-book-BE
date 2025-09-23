#!/usr/bin/env python3
"""
Script để khởi tạo PostgreSQL database cho Gen Book project.
Chạy script này để tạo tables và dữ liệu mẫu.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.db.services.database_connection import init_database, engine
from src.db.services.crud import UserService, BookService
from src.db.models.schemas import UserCreate, BookCreate
from sqlalchemy.orm import Session
from sqlalchemy import text

def create_sample_data():
    """Tạo dữ liệu mẫu để test"""
    from src.db.services.database_connection import SessionLocal

    db = SessionLocal()
    try:
        # Tạo user mẫu
        sample_user = UserCreate(
            email="admin@example.com",
            username="admin",
            full_name="Administrator",
            password="admin123",
            is_superuser=True
        )

        existing_user = UserService.get_user_by_email(db, sample_user.email)
        if not existing_user:
            user = UserService.create_user(db, sample_user)
            print(f"Created sample user: {user.username}")

            # Tạo book mẫu
            sample_book = BookCreate(
                title="Sách Thiếu Nhi Mẫu",
                book_type="Khoa học viễn tưởng",
                character_name="Chú Bé Tò Mò",
                style="realistic",
                reference_image_url="https://example.com/sample_image.jpg",
                user_id=user.id
            )

            book = BookService.create_book(db, sample_book)
            print(f"Created sample book: {book.title}")
        else:
            print("Sample user already exists")

    finally:
        db.close()

def test_connection():
    """Test kết nối database"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✓ Database connection successful")
            return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False

def main():
    """Main function"""
    print("Initializing PostgreSQL database for Gen Book...")

    # Test connection trước
    if not test_connection():
        print("Please check your DATABASE_URL in .env file")
        sys.exit(1)

    # Khởi tạo tables
    try:
        init_database()
        print("✓ Database tables created successfully")
    except Exception as e:
        print(f"✗ Failed to create database tables: {e}")
        sys.exit(1)

    # Tạo dữ liệu mẫu
    try:
        create_sample_data()
        print("✓ Sample data created successfully")
    except Exception as e:
        print(f"✗ Failed to create sample data: {e}")
        sys.exit(1)

    print("\n🎉 Database initialization completed!")
    print("You can now run the application with: python main.py")

if __name__ == "__main__":
    main()
