# 🎉 High5 Gen Book - AI Book Generator

[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green.svg)](https://fastapi.tiangolo.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-blue.svg)](https://openai.com/)
[![Replicate](https://img.shields.io/badge/Replicate-API-orange.svg)](https://replicate.com/)
[![Python](https://img.shields.io/badge/Python-3.13+-yellow.svg)](https://www.python.org/)

Tạo sách thiếu nhi cá nhân hóa với AI chỉ với 1 cú click! 🚀

## 📋 Mô tả dự án

High5 Gen Book là một ứng dụng web AI tiên tiến giúp tạo ra những cuốn sách thiếu nhi cá nhân hóa hoàn chỉnh chỉ trong vài phút. Ứng dụng kết hợp sức mạnh của trí tuệ nhân tạo để:

- ✍️ **Tạo nội dung sách** phù hợp với chủ đề và nhân vật được chỉ định
- 🎨 **Tạo hình ảnh minh họa** chất lượng cao cho từng trang
- 🎭 **Chuyển đổi ảnh thành phong cách cartoon** 90s
- 📄 **Xuất PDF sách hoàn chỉnh** với layout chuyên nghiệp

## ✨ Tính năng chính

### 🔄 Quy trình tự động hoàn chỉnh
1. **Nhập thông tin**: Loại sách, tên nhân vật, ảnh tham khảo
2. **AI tạo nội dung**: GPT-4o-mini tạo câu chuyện 3 trang phù hợp lứa tuổi
3. **AI tạo hình ảnh**: Tạo hình minh họa cá nhân hóa cho từng trang
4. **Xuất PDF**: Tạo file PDF sách hoàn chỉnh có thể tải về

### 🎯 Các loại sách hỗ trợ
- Khoa học viễn tưởng
- Phiêu lưu mạo hiểm
- Thế giới động vật
- Khoa học tự nhiên
- Truyện cổ tích
- Và nhiều chủ đề khác...

### 🎨 Phong cách hình ảnh
- **Realistic**: Hình ảnh minh họa chân thực, màu sắc tươi sáng
- **Cartoon**: Phong cách hoạt hình 90s vui nhộn, đáng yêu

## 🚀 Cài đặt và chạy

### Yêu cầu hệ thống
- Python 3.13+
- pip (đã có sẵn với Python)
- Kết nối internet (cho API calls)

### Phương pháp 1: Chạy với Docker (Khuyến nghị) 🐳

#### Yêu cầu
- Docker và Docker Compose đã được cài đặt
- PostgreSQL database (có thể chạy trong Docker)

### Phương pháp 2: Chạy native với Python

#### Yêu cầu
- Python 3.13+
- PostgreSQL database server

#### Các bước cài đặt

1. **Clone repository và cài đặt dependencies**
   ```bash
   git clone <repository-url>
   cd gen-book
   pip install -r requirements.txt
   ```

2. **Cấu hình Database**

   Tạo file `.env`:
   ```bash
   cp database_env_example.txt .env
   ```

   Chỉnh sửa file `.env` với thông tin database:
   ```env
   DATABASE_URL=postgresql://username:password@localhost:5432/gen_book_db
   ```

   Tạo database trong PostgreSQL:
   ```sql
   CREATE DATABASE gen_book_db;
   CREATE USER genbook_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE gen_book_db TO genbook_user;
   ```

3. **Khởi tạo Database**
   ```bash
   python src/db/init_db.py
   ```

4. **Chạy ứng dụng**
   ```bash
   python main.py
   ```

### Phương pháp 1: Chạy với Docker (Khuyến nghị) 🐳

#### Yêu cầu
- Docker và Docker Compose đã được cài đặt

#### 1. Clone repository
```bash
git clone <repository-url>
cd gen-book
```

#### 2. Cấu hình Database (cho Docker)
Chỉnh sửa file `docker-compose.yml` để cấu hình PostgreSQL:
```yaml
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: gen_book_db
      POSTGRES_USER: genbook_user
      POSTGRES_PASSWORD: your_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

#### 3. Chạy với Docker Compose
```bash
# Cách 1: Sử dụng script tự động (khuyến nghị)
./run_docker.sh

# Cách 2: Chạy thủ công
docker-compose up --build -d
```

#### 4. Khởi tạo Database
```bash
# Chạy script khởi tạo database trong container
docker-compose exec app python src/db/init_db.py
```

#### 5. Truy cập ứng dụng
- API sẽ chạy tại: `http://localhost:8000` hoặc `http://127.0.0.1:8000`
- Mở file `example/frontend_example.html` trong browser để xem giao diện demo

#### 6. Dừng ứng dụng
```bash
docker-compose down
```

#### 7. Lệnh hữu ích khác
```bash
# Xem logs
docker-compose logs -f

# Restart ứng dụng
docker-compose restart

# Xây dựng lại image
docker-compose build --no-cache

# Truy cập database container
docker-compose exec db psql -U genbook_user -d gen_book_db
```

#### Testing Database
```bash
# Test database connection
docker-compose exec app python src/db/test_db.py
```

## 📖 API Documentation

Server sẽ chạy tại `http://localhost:8000`

### Database Endpoints (mới)

Base URL: `/api/v1/db`

#### Users
- `POST /users/` - Tạo user mới
- `GET /users/` - Lấy danh sách users
- `POST /auth/login` - Đăng nhập

#### Books
- `POST /books/` - Tạo sách mới
- `GET /books/` - Lấy danh sách sách
- `GET /books/{book_id}` - Lấy chi tiết sách

#### Statistics
- `GET /stats/generation/` - Thống kê tổng quan
- `GET /health/` - Health check database

### AI Endpoints

Xem chi tiết tại [`src/ai/README.md`](./src/ai/README.md)

#### Endpoints chính
- `POST /create-realistic-book/` - Tạo sách hoàn chỉnh phong cách realistic
- `POST /create-cartoon-book/` - Tạo sách hoàn chỉnh phong cách cartoon
- `POST /gen-script/` - Tạo nội dung sách
- `POST /gen-illustration-image/` - Tạo hình ảnh minh họa
- `POST /gen-cartoon-image/` - Chuyển đổi ảnh thành cartoon
- `POST /create-pdf-book/` - Tạo PDF với custom backgrounds

## 🛠️ Kiến trúc hệ thống

```
📁 gen-book/
├── 📄 main.py                 # FastAPI application chính
├── 📄 requirements.txt        # Dependencies Python
├── 📄 database_env_example.txt # Database configuration template
├── 📄 Dockerfile             # Docker image configuration
├── 📄 docker-compose.yml     # Docker Compose configuration
├── 📄 .dockerignore          # Docker ignore patterns
├── 📄 run_docker.sh          # Script tự động chạy với Docker
├── 📄 open_frontend.py       # Script mở giao diện demo
├── 📁 src/
│   ├── 📁 ai/
│   │   ├── 📁 api/
│   │   │   └── 📄 ai_routes.py    # AI endpoints
│   │   └── 📁 services/
│   │       ├── 📄 llm.py         # AI text generation (OpenAI)
│   │       ├── 📄 gen_illustration_image.py  # Tạo ảnh minh họa
│   │       ├── 📄 gen_avatar.py      # Tạo ảnh cartoon
│   │       ├── 📄 remove_background.py      # Xử lý remove background
│   │       └── 📄 create_pages.py    # Tạo PDF sách (ReportLab)
│   └── 📁 db/
│       ├── 📁 api/
│       │   └── 📄 db_routes.py   # Database endpoints
│       ├── 📁 models/
│       │   ├── 📄 database.py    # SQLAlchemy models
│       │   └── 📄 schemas.py     # Pydantic schemas
│       └── 📁 services/
│           ├── 📄 crud.py        # Database CRUD operations
│           ├── 📄 database_connection.py  # DB connection management
│           ├── 📄 init_db.py     # Database initialization
│           └── 📄 test_db.py     # Database testing
├── 📁 assets/
│   └── 📁 backgrounds/       # Thư mục chứa ảnh background
├── 📁 example/
│   └── 📄 frontend_example.html     # Giao diện demo HTML
├── 📄 .gitignore            # Git ignore patterns
└── 📄 run_docker.sh         # Script chạy Docker (không được track bởi git)
```

## 🧠 Công nghệ sử dụng

- **Backend**: FastAPI (Python web framework)
- **Database**: PostgreSQL với SQLAlchemy ORM
- **Authentication**: PassLib với bcrypt
- **Frontend Demo**: HTML5 + JavaScript (Vanilla)

### AI & Image Processing
Xem chi tiết tại [`src/ai/README.md`](./src/ai/README.md)

### Database Operations
Xem chi tiết tại [`src/db/README.md`](./src/db/README.md)

## 🔧 Cấu hình

### Environment Variables
Tạo file `.env` từ template `database_env_example.txt`:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/gen_book_db
```

### API Keys & Models
- **Database**: Xem [`src/db/README.md`](./src/db/README.md)
- **AI Services**: Xem [`src/ai/README.md`](./src/ai/README.md)

## 📊 Workflow chi tiết

Xem chi tiết workflow AI processing tại [`src/ai/README.md`](./src/ai/README.md)

### Tổng quan quy trình:
1. **User Authentication** → Đăng nhập/đăng ký (tùy chọn)
2. **AI Content Generation** → Tạo nội dung và hình ảnh
3. **Database Logging** → Lưu trữ thông tin và log hoạt động
4. **PDF Compilation** → Xuất file sách hoàn chỉnh

## 🎯 Mục tiêu sử dụng

- Tạo quà tặng cá nhân hóa cho trẻ em
- Công cụ giáo dục và giải trí
- Phát triển kỹ năng đọc viết cho trẻ
- Sản xuất nội dung sách số

## 🤝 Đóng góp

1. Fork repository
2. Tạo feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Tạo Pull Request

## 📄 License

Dự án này sử dụng cho mục đích giáo dục và thương mại. Vui lòng liên hệ tác giả để biết thêm chi tiết về license.

## 👨‍💻 Tác giả

**High5 Team** - *AI-powered book generation for children*

## 🙏 Lời cảm ơn

- OpenAI và Replicate vì các API AI mạnh mẽ
- FastAPI community vì framework tuyệt vời
- ReportLab vì thư viện PDF chuyên nghiệp

---

**🎉 Chúc bạn tạo ra những cuốn sách tuyệt vời cho các em nhỏ!**
