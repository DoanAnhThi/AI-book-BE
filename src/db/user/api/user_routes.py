from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List

from src.db.common.database_connection import get_db
from src.db.user.services.user_service import UserService
from src.db.user.models.user_schemas import User, UserCreate, UserUpdate

router = APIRouter()

@router.post("/users/", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Tạo user mới"""
    # Kiểm tra email đã tồn tại
    db_user = UserService.get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email đã được đăng ký")

    # Kiểm tra username đã tồn tại
    db_user = UserService.get_user_by_username(db, user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username đã được sử dụng")

    return UserService.create_user(db, user)

@router.get("/users/", response_model=List[User])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Lấy danh sách users"""
    users = UserService.get_users(db, skip=skip, limit=limit)
    return users

@router.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    """Lấy thông tin user theo ID"""
    db_user = UserService.get_user(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User không tồn tại")
    return db_user

@router.put("/users/{user_id}", response_model=User)
async def update_user(user_id: int, user_update: UserUpdate, db: Session = Depends(get_db)):
    """Cập nhật thông tin user"""
    db_user = UserService.update_user(db, user_id, user_update)
    if not db_user:
        raise HTTPException(status_code=404, detail="User không tồn tại")
    return db_user

@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Xóa user"""
    success = UserService.delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User không tồn tại")

# Authentication endpoint (đơn giản, không dùng JWT)
@router.post("/auth/login")
async def login(username: str, password: str, db: Session = Depends(get_db)):
    """Đăng nhập và trả về thông tin user"""
    user = UserService.authenticate_user(db, username, password)
    if not user:
        raise HTTPException(status_code=401, detail="Tên đăng nhập hoặc mật khẩu không đúng")
    return {"user": user, "message": "Đăng nhập thành công"}
