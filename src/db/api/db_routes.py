from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from src.db.services.database_connection import get_db
from src.db.services.crud import UserService, BookService, BookPageService, GenerationLogService
from src.db.models.schemas import (
    User, UserCreate, UserUpdate, CreateBookRequest, CreateBookResponse,
    Book, BookWithUser, BookUpdate, BookPage, BookPageCreate, BookPageUpdate,
    GenerationLog, GenerationLogCreate, GenerationStats, GetBooksResponse
)

router = APIRouter()

# User routes
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

# Book routes
@router.post("/books/", response_model=CreateBookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(book_request: CreateBookRequest, db: Session = Depends(get_db)):
    """Tạo sách mới"""
    # Kiểm tra user tồn tại
    user = UserService.get_user(db, book_request.user_id if hasattr(book_request, 'user_id') else 1)
    if not user:
        raise HTTPException(status_code=404, detail="User không tồn tại")

    # Tạo book
    book_create = BookCreate(
        title=book_request.title,
        book_type=book_request.book_type,
        character_name=book_request.character_name,
        style=book_request.style,
        reference_image_url=book_request.reference_image_url,
        user_id=user.id
    )

    book = BookService.create_book(db, book_create)

    return CreateBookResponse(
        book=book,
        message="Sách đã được tạo thành công",
        success=True
    )

@router.get("/books/", response_model=GetBooksResponse)
async def get_books(
    user_id: Optional[int] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Lấy danh sách sách"""
    if user_id:
        books = BookService.get_books_by_user(db, user_id, skip=skip, limit=limit)
        total = len(BookService.get_books_by_user(db, user_id))  # Có thể tối ưu bằng count query
    else:
        books = BookService.get_books(db, skip=skip, limit=limit)
        total = len(BookService.get_books(db))  # Có thể tối ưu bằng count query

    return GetBooksResponse(
        books=books,
        total=total,
        page=skip // limit + 1,
        per_page=limit
    )

@router.get("/books/{book_id}", response_model=BookWithUser)
async def get_book(book_id: int, db: Session = Depends(get_db)):
    """Lấy thông tin sách theo ID"""
    db_book = BookService.get_book_with_pages(db, book_id)
    if not db_book:
        raise HTTPException(status_code=404, detail="Sách không tồn tại")
    return db_book

@router.put("/books/{book_id}", response_model=Book)
async def update_book(book_id: int, book_update: BookUpdate, db: Session = Depends(get_db)):
    """Cập nhật thông tin sách"""
    db_book = BookService.update_book(db, book_id, book_update)
    if not db_book:
        raise HTTPException(status_code=404, detail="Sách không tồn tại")
    return db_book

@router.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_id: int, db: Session = Depends(get_db)):
    """Xóa sách"""
    success = BookService.delete_book(db, book_id)
    if not success:
        raise HTTPException(status_code=404, detail="Sách không tồn tại")

# BookPage routes
@router.post("/books/{book_id}/pages/", response_model=BookPage, status_code=status.HTTP_201_CREATED)
async def create_book_page(book_id: int, page: BookPageCreate, db: Session = Depends(get_db)):
    """Thêm trang mới vào sách"""
    # Kiểm tra sách tồn tại
    book = BookService.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Sách không tồn tại")

    # Đảm bảo page thuộc về book đúng
    if page.book_id != book_id:
        raise HTTPException(status_code=400, detail="book_id không khớp")

    return BookPageService.create_page(db, page)

@router.post("/books/{book_id}/pages/batch/", response_model=List[BookPage], status_code=status.HTTP_201_CREATED)
async def create_book_pages_batch(book_id: int, pages: List[BookPageCreate], db: Session = Depends(get_db)):
    """Thêm nhiều trang cùng lúc vào sách"""
    # Kiểm tra sách tồn tại
    book = BookService.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Sách không tồn tại")

    # Đảm bảo tất cả pages thuộc về book đúng
    for page in pages:
        if page.book_id != book_id:
            raise HTTPException(status_code=400, detail="book_id không khớp")

    return BookPageService.create_pages_batch(db, pages)

@router.get("/books/{book_id}/pages/", response_model=List[BookPage])
async def get_book_pages(book_id: int, db: Session = Depends(get_db)):
    """Lấy tất cả trang của một sách"""
    # Kiểm tra sách tồn tại
    book = BookService.get_book(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Sách không tồn tại")

    return BookPageService.get_pages_by_book(db, book_id)

@router.put("/pages/{page_id}", response_model=BookPage)
async def update_book_page(page_id: int, page_update: BookPageUpdate, db: Session = Depends(get_db)):
    """Cập nhật thông tin trang"""
    db_page = BookPageService.update_page(db, page_id, page_update)
    if not db_page:
        raise HTTPException(status_code=404, detail="Trang không tồn tại")
    return db_page

@router.delete("/pages/{page_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book_page(page_id: int, db: Session = Depends(get_db)):
    """Xóa trang"""
    success = BookPageService.delete_page(db, page_id)
    if not success:
        raise HTTPException(status_code=404, detail="Trang không tồn tại")

# Statistics and Analytics routes
@router.get("/stats/generation/", response_model=GenerationStats)
async def get_generation_stats(days: int = Query(30, ge=1, le=365), db: Session = Depends(get_db)):
    """Lấy thống kê generation trong khoảng thời gian"""
    book_stats = BookService.get_books_stats(db)
    gen_stats = GenerationLogService.get_generation_stats(db, days)

    return GenerationStats(
        total_books=book_stats["total_books"],
        total_users=len(UserService.get_users(db)),
        total_pages=db.query(BookPage).count(),
        avg_processing_time=book_stats["avg_processing_time"]
    )

@router.get("/stats/books/")
async def get_book_stats(db: Session = Depends(get_db)):
    """Lấy thống kê chi tiết về sách"""
    stats = BookService.get_books_stats(db)
    return stats

# GenerationLog routes (chủ yếu cho admin/debugging)
@router.get("/logs/", response_model=List[GenerationLog])
async def get_generation_logs(
    user_id: Optional[int] = None,
    operation_type: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Lấy danh sách generation logs"""
    if user_id:
        logs = GenerationLogService.get_logs_by_user(db, user_id, skip=skip, limit=limit)
    elif operation_type:
        logs = GenerationLogService.get_logs_by_operation(db, operation_type, skip=skip, limit=limit)
    else:
        # Có thể thêm method để lấy tất cả logs nếu cần
        logs = []

    return logs

@router.post("/logs/", response_model=GenerationLog, status_code=status.HTTP_201_CREATED)
async def create_generation_log(log: GenerationLogCreate, db: Session = Depends(get_db)):
    """Tạo generation log mới (thường dùng internal)"""
    return GenerationLogService.create_log(db, log)

# Health check
@router.get("/health/")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Test database connection
        db.execute("SELECT 1")
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database connection failed: {str(e)}")
