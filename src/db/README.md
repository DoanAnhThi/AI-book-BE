# Database Module cho Gen Book

Module này cung cấp PostgreSQL database integration cho dự án Gen Book, bao gồm user management, book storage và logging.

## Cấu trúc thư mục

```
src/db/
├── api/
│   └── db_routes.py          # FastAPI routes cho database operations
├── models/
│   ├── database.py           # SQLAlchemy models
│   └── schemas.py            # Pydantic schemas
├── services/
│   ├── crud.py               # CRUD operations
│   └── database_connection.py # Database connection & session management
├── init_db.py                # Script khởi tạo database
└── README.md                 # Tài liệu này
```

## Cài đặt và Setup

### 1. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 2. Cấu hình Database

Tạo file `.env` trong thư mục gốc của project:

```bash
cp database_env_example.txt .env
```

Chỉnh sửa file `.env` với thông tin database của bạn:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/gen_book_db
```

### 3. Tạo PostgreSQL Database

```sql
-- Tạo database trong PostgreSQL
CREATE DATABASE gen_book_db;

-- Tạo user (tùy chọn)
CREATE USER genbook_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE gen_book_db TO genbook_user;
```

### 4. Khởi tạo Database

Chạy script khởi tạo để tạo tables và dữ liệu mẫu:

```bash
python src/db/init_db.py
```

## Models

### User
- Quản lý thông tin người dùng
- Hỗ trợ authentication cơ bản

### Book
- Lưu trữ thông tin sách đã tạo
- Liên kết với user và các trang

### BookPage
- Lưu trữ từng trang của sách
- Bao gồm content và generated images

### GenerationLog
- Log các hoạt động tạo sách
- Theo dõi performance và errors

## API Endpoints

Base URL: `/api/v1/db`

### Users
- `POST /users/` - Tạo user mới
- `GET /users/` - Lấy danh sách users
- `GET /users/{user_id}` - Lấy user theo ID
- `PUT /users/{user_id}` - Cập nhật user
- `DELETE /users/{user_id}` - Xóa user
- `POST /auth/login` - Đăng nhập

### Books
- `POST /books/` - Tạo sách mới
- `GET /books/` - Lấy danh sách sách
- `GET /books/{book_id}` - Lấy sách theo ID
- `PUT /books/{book_id}` - Cập nhật sách
- `DELETE /books/{book_id}` - Xóa sách

### Book Pages
- `POST /books/{book_id}/pages/` - Thêm trang mới
- `POST /books/{book_id}/pages/batch/` - Thêm nhiều trang
- `GET /books/{book_id}/pages/` - Lấy tất cả trang của sách
- `PUT /pages/{page_id}` - Cập nhật trang
- `DELETE /pages/{page_id}` - Xóa trang

### Statistics
- `GET /stats/generation/` - Thống kê generation
- `GET /stats/books/` - Thống kê sách
- `GET /logs/` - Lấy generation logs

### Health Check
- `GET /health/` - Kiểm tra kết nối database

## Sử dụng trong Code

### Dependency Injection

```python
from src.db.services.database_connection import get_db

@app.get("/example/")
async def example_endpoint(db: Session = Depends(get_db)):
    # Sử dụng db session
    pass
```

### CRUD Operations

```python
from src.db.services.crud import UserService, BookService

# Tạo user
user = UserService.create_user(db, user_data)

# Lấy sách của user
books = BookService.get_books_by_user(db, user_id)

# Log operation
GenerationLogService.log_operation(
    db, "script_gen", "success",
    user_id=user_id, processing_time=1.5
)
```

## Development

### Chạy ứng dụng

```bash
python main.py
```

API documentation sẽ có tại: http://localhost:8000/docs

### Testing

```python
# Test database connection
python -c "from src.db.services.database_connection import test_connection; test_connection()"
```

### Migration (sử dụng Alembic nếu cần)

```bash
# Khởi tạo alembic
alembic init alembic

# Tạo migration
alembic revision --autogenerate -m "Add new table"

# Chạy migration
alembic upgrade head
```

## Security Notes

- Password được hash bằng bcrypt
- Sử dụng environment variables cho sensitive data
- CORS được cấu hình (cần điều chỉnh cho production)
- Authentication hiện tại đơn giản, có thể nâng cấp lên JWT

## Performance

- Sử dụng connection pooling
- Batch operations cho việc tạo nhiều pages
- Indexing trên các trường thường query
- Pagination cho các list endpoints
