#!/usr/bin/env python3
"""
Script test database connection và basic operations.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.db.services.database_connection import test_connection, SessionLocal
from src.db.services.crud import UserService, BookService
from src.db.models.schemas import UserCreate, BookCreate

def test_basic_operations():
    """Test các operations cơ bản"""
    db = SessionLocal()
    try:
        print("🧪 Testing basic database operations...")

        # Test tạo user
        test_user = UserCreate(
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            password="test123"
        )

        # Xóa user cũ nếu tồn tại
        existing = UserService.get_user_by_email(db, test_user.email)
        if existing:
            UserService.delete_user(db, existing.id)

        user = UserService.create_user(db, test_user)
        print(f"✅ Created user: {user.username} (ID: {user.id})")

        # Test tạo book
        test_book = BookCreate(
            title="Test Book",
            book_type="Test Type",
            character_name="Test Character",
            style="realistic",
            reference_image_url="https://example.com/test.jpg",
            user_id=user.id
        )

        book = BookService.create_book(db, test_book)
        print(f"✅ Created book: {book.title} (ID: {book.id})")

        # Test query
        retrieved_user = UserService.get_user(db, user.id)
        print(f"✅ Retrieved user: {retrieved_user.username}")

        retrieved_book = BookService.get_book(db, book.id)
        print(f"✅ Retrieved book: {retrieved_book.title}")

        # Cleanup
        BookService.delete_book(db, book.id)
        UserService.delete_user(db, user.id)
        print("✅ Cleanup completed")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        db.close()

def main():
    """Main test function"""
    print("🧪 Testing Database Module\n")

    # Test connection
    if not test_connection():
        print("❌ Database connection test failed")
        sys.exit(1)

    # Test operations
    if not test_basic_operations():
        print("❌ Basic operations test failed")
        sys.exit(1)

    print("\n🎉 All tests passed!")

if __name__ == "__main__":
    main()
