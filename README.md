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

#### 1. Clone repository
```bash
git clone <repository-url>
cd gen-book
```

#### 2. Chạy với Docker Compose
```bash
# Cách 1: Sử dụng script tự động (khuyến nghị)
./run_docker.sh

# Cách 2: Chạy thủ công
docker-compose up --build
```

#### 3. Truy cập ứng dụng
- API sẽ chạy tại: `http://localhost:8000` hoặc `http://127.0.0.1:8000`
- Mở file `example/frontend_example.html` trong browser để xem giao diện demo

#### 4. Dừng ứng dụng
```bash
docker-compose down
```

#### 5. Lệnh hữu ích khác
```bash
# Xem logs
docker-compose logs -f

# Restart ứng dụng
docker-compose restart

# Xây dựng lại image
docker-compose build --no-cache
```

### Phương pháp 2: Chạy trực tiếp với Python

#### 1. Clone repository
```bash
git clone <repository-url>
cd gen-book
```

#### 2. Tạo virtual environment (khuyến nghị)
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# hoặc
venv\Scripts\activate     # Windows
```

#### 3. Cài đặt dependencies
```bash
pip install -r requirements.txt
```

#### 4. Chạy server
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 5. Mở giao diện
```bash
python open_frontend.py
```

Hoặc mở file `example/frontend_example.html` trực tiếp trong browser.

## 📖 API Documentation

Server sẽ chạy tại `http://localhost:8000`

### Endpoints chính

#### `POST /create-realistic-book/`
Tạo sách hoàn chỉnh với phong cách realistic.

**Request Body:**
```json
{
  "type": "Khoa học viễn tưởng - Lino khám phá vũ trụ",
  "name": "Lino",
  "image": "https://example.com/reference-image.jpg"
}
```

**Response:** File PDF trực tiếp (StreamingResponse)

#### `POST /create-cartoon-book/`
Tạo sách hoàn chỉnh với phong cách cartoon 90s.

**Request Body:** Giống endpoint trên

#### `POST /gen-script/`
Chỉ tạo nội dung sách (không có hình ảnh).

#### `POST /gen-illustration-image/`
Tạo hình ảnh minh họa từ prompt và ảnh tham khảo.

#### `POST /gen-cartoon-image/`
Chuyển đổi ảnh thành phong cách cartoon.

#### `POST /create-pdf-book/`
Tạo PDF từ nội dung và danh sách URL ảnh có sẵn, hỗ trợ background tùy chỉnh.

**Request Body:**
```json
{
  "scripts": ["Trang 1 content...", "Trang 2 content..."],
  "image_urls": ["https://example.com/image1.jpg", "https://example.com/image2.jpg"],
  "background_urls": ["https://example.com/bg1.jpg", "https://example.com/bg2.jpg"]  // Tùy chọn
}
```

**Features:**
- 🎨 **Custom Backgrounds**: Thêm background riêng cho mỗi trang
- 🔤 **Modern Fonts**: Comic Neue, Patrick Hand cho sách trẻ em
- 📝 **Large Text**: Font size 18pt, dễ đọc cho trẻ
- 🖊️ **Bold Text Effect**: Chữ dày, rõ ràng với hiệu ứng shadow
- 🎯 **Auto Text Color**: Tự động chọn màu chữ (đen/trắng) theo độ sáng background
- 📄 **Professional Layout**: Landscape A4 với spacing tối ưu

## 🛠️ Kiến trúc hệ thống

```
📁 gen-book/
├── 📄 main.py                 # FastAPI application chính
├── 📄 requirements.txt        # Dependencies Python
├── 📄 Dockerfile             # Docker image configuration
├── 📄 docker-compose.yml     # Docker Compose configuration
├── 📄 .dockerignore          # Docker ignore patterns
├── 📄 run_docker.sh          # Script tự động chạy với Docker
├── 📄 open_frontend.py       # Script mở giao diện demo
├── 📁 assets/
│   └── 📁 backgrounds/       # Thư mục chứa ảnh background
├── 📁 models/
│   ├── 📄 llm.py             # Xử lý AI text generation (OpenAI)
│   ├── 📄 gen_illustration_image.py  # Tạo ảnh minh họa (Replicate)
│   ├── 📄 gen_cartoon_image.py      # Tạo ảnh cartoon (Replicate)
│   ├── 📄 remove_background.py      # Xử lý remove background
│   └── 📄 gen_book.py        # Tạo PDF sách (ReportLab)
├── 📁 example/
│   └── 📄 frontend_example.html     # Giao diện demo HTML
├── 📄 .gitignore            # Git ignore patterns
└── 📄 run_docker.sh         # Script chạy Docker (không được track bởi git)
```

## 🧠 Công nghệ sử dụng

- **Backend**: FastAPI (Python web framework)
- **AI Text**: OpenAI GPT-4o-mini
- **AI Images**: Replicate API (Stability AI models)
- **PDF Generation**: ReportLab
- **Image Processing**: Pillow (PIL)
- **Frontend Demo**: HTML5 + JavaScript (Vanilla)

## 🔧 Cấu hình

### API Keys
- **OpenAI API Key**: Đã được cấu hình sẵn trong `models/llm.py`
- **Replicate API Token**: Cần thiết lập biến môi trường `REPLICATE_API_TOKEN`

### Models AI sử dụng
- **Text Generation**: `gpt-4o-mini`
- **Image Generation**: `stability-ai/sdxl` (qua Replicate)
- **Cartoon Style**: Custom prompt "Make this a 90s cartoon"

## 📊 Workflow chi tiết

### Realistic Book Generation:
1. **Script Generation** → GPT-4o-mini tạo nội dung 3 trang
2. **Image Generation** → Tạo ảnh minh họa cho từng trang
3. **PDF Creation** → Kết hợp text và hình thành PDF

### Cartoon Book Generation:
1. **Script Generation** → Giống trên
2. **Base Cartoon Conversion** → Chuyển ảnh gốc thành cartoon
3. **Cartoon Illustrations** → Tạo ảnh minh họa cartoon cho từng trang
4. **PDF Creation** → Tạo PDF với style cartoon

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
