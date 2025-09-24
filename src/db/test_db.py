#!/usr/bin/env python3
"""
Script test database connection và basic operations.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.db.common.database_connection import test_connection, SessionLocal
from src.db.user.services.user_service import UserService
from src.db.user.models.user_schemas import UserCreate

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

        # Test query
        retrieved_user = UserService.get_user(db, user.id)
        print(f"✅ Retrieved user: {retrieved_user.username}")

        # Test update user
        from src.db.user.models.user_schemas import UserUpdate
        update_data = UserUpdate(full_name="Updated Test User")
        updated_user = UserService.update_user(db, user.id, update_data)
        print(f"✅ Updated user: {updated_user.full_name}")

        # Cleanup
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
