from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# User schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

class User(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Book schemas
class BookBase(BaseModel):
    title: str
    book_type: str
    character_name: str
    style: str = "realistic"
    reference_image_url: Optional[str] = None
    pdf_url: Optional[str] = None
    is_completed: bool = False
    processing_time: Optional[float] = None

class BookCreate(BookBase):
    user_id: int

class BookUpdate(BaseModel):
    title: Optional[str] = None
    book_type: Optional[str] = None
    character_name: Optional[str] = None
    style: Optional[str] = None
    reference_image_url: Optional[str] = None
    pdf_url: Optional[str] = None
    is_completed: Optional[bool] = None
    processing_time: Optional[float] = None

class Book(BookBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class BookWithUser(Book):
    user: User

# BookPage schemas
class BookPageBase(BaseModel):
    page_number: int
    content: str
    image_prompt: Optional[str] = None
    generated_image_url: Optional[str] = None

class BookPageCreate(BookPageBase):
    book_id: int

class BookPageUpdate(BaseModel):
    page_number: Optional[int] = None
    content: Optional[str] = None
    image_prompt: Optional[str] = None
    generated_image_url: Optional[str] = None

class BookPage(BookPageBase):
    id: int
    book_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# GenerationLog schemas
class GenerationLogBase(BaseModel):
    operation_type: str
    status: str = "success"
    input_data: Optional[str] = None
    output_data: Optional[str] = None
    processing_time: Optional[float] = None
    error_message: Optional[str] = None

class GenerationLogCreate(GenerationLogBase):
    user_id: Optional[int] = None

class GenerationLog(GenerationLogBase):
    id: int
    user_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Response schemas
class BookDetail(Book):
    pages: List[BookPage] = []
    user: User

# Request/Response cho API endpoints
class CreateBookRequest(BaseModel):
    title: str
    book_type: str
    character_name: str
    style: str = "realistic"
    reference_image_url: str

class CreateBookResponse(BaseModel):
    book: Book
    message: str
    success: bool

class GetBooksResponse(BaseModel):
    books: List[Book]
    total: int
    page: int
    per_page: int

class GenerationStats(BaseModel):
    total_books: int
    total_users: int
    total_pages: int
    avg_processing_time: Optional[float] = None
