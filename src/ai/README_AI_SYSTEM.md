# 🤖 AI Services Module

Module này chứa tất cả các dịch vụ AI được sử dụng để tạo sách thiếu nhi cá nhân hóa, bao gồm tạo nội dung, hình ảnh minh họa, và xử lý PDF.

## 📁 Cấu trúc thư mục

```
src/ai/
├── api/
│   └── ai_routes.py              # FastAPI routes cho AI endpoints
└── services/
    ├── llm.py                    # AI text generation (OpenAI GPT-4o-mini)
    ├── gen_illustration_image.py # Tạo ảnh minh họa (Replicate API)
    ├── gen_cartoon_image.py      # Chuyển đổi ảnh thành cartoon (Replicate)
    ├── remove_background.py      # Xử lý remove background (rembg)
    └── gen_book.py               # Tạo PDF sách hoàn chỉnh (ReportLab)
```

## 🚀 Các AI Services

### 1. 📝 LLM Service (`llm.py`)

**Chức năng**: Tạo nội dung sách thiếu nhi cá nhân hóa sử dụng OpenAI GPT-4o-mini

**API sử dụng**: OpenAI GPT-4o-mini

**Input**:
- `type`: Loại sách (vd: "Khoa học viễn tưởng", "Phiêu lưu mạo hiểm")
- `name`: Tên nhân vật chính trong câu chuyện

**Output**: JSON object chứa:
- `title`: Tiêu đề sách hấp dẫn
- `content`: Object với 3 trang sách, mỗi trang có:
  - `page-content`: Nội dung câu chuyện (20-60 từ)
  - `page-prompt`: Prompt để tạo hình ảnh cho trang đó

**Ví dụ**:
```python
from src.ai.services.llm import gen_script

result = await gen_script("Khoa học viễn tưởng", "Lino")
print(result["script"]["title"])  # "Lino khám phá vũ trụ"
```

### 2. 🎨 Illustration Image Service (`gen_illustration_image.py`)

**Chức năng**: Tạo hình ảnh minh họa chất lượng cao cho sách thiếu nhi

**API sử dụng**: Replicate API với model Bytedance Seedream 4

**Input**:
- `prompt`: Mô tả chi tiết về ảnh cần tạo
- `image_url`: URL ảnh tham khảo (tùy chọn)
- `width/height`: Kích thước ảnh (mặc định: 2480x1754px - phù hợp A4 ngang)

**Output**: URL của ảnh đã tạo

**Tính năng đặc biệt**:
- Hỗ trợ image-to-image generation
- Tối ưu cho sách thiếu nhi với màu sắc tươi sáng
- Kích thước chuẩn cho in ấn A4

**Ví dụ**:
```python
from src.ai.services.gen_illustration_image import gen_illustration_image

image_url = await gen_illustration_image(
    prompt="Một cậu bé tò mò đang khám phá vũ trụ",
    image_url="https://example.com/child-photo.jpg"
)
```

### 3. 🎭 Cartoon Image Service (`gen_cartoon_image.py`)

**Chức năng**: Chuyển đổi ảnh chân thực thành phong cách cartoon 90s

**API sử dụng**: Replicate API

**Input**:
- `image_url`: URL ảnh đầu vào cần chuyển đổi

**Output**: URL của ảnh cartoon

**Phong cách**: Cartoon 90s với nét vẽ vui nhộn, đáng yêu

**Ví dụ**:
```python
from src.ai.services.gen_cartoon_image import gen_cartoon_image

cartoon_url = await gen_cartoon_image(
    image_url="https://example.com/child-photo.jpg"
)
```

### 4. 🖼️ Background Removal Service (`remove_background.py`)

**Chức năng**: Loại bỏ background khỏi ảnh để tạo hiệu ứng trong suốt

**Thư viện sử dụng**: rembg với ONNX Runtime

**Input**:
- `image_url`: URL ảnh đầu vào

**Output**: Base64 data URL của ảnh PNG trong suốt

**Tính năng**:
- Tự động detect và remove background
- Xuất ra định dạng PNG với transparency
- Hỗ trợ nhiều định dạng ảnh đầu vào

**Ví dụ**:
```python
from src.ai.services.remove_background import remove_background

processed_image = await remove_background(
    image_url="https://example.com/photo-with-bg.jpg"
)
```

### 5. 📄 PDF Generation Service (`gen_book.py`)

**Chức năng**: Tạo file PDF sách hoàn chỉnh từ nội dung và hình ảnh

**Thư viện sử dụng**: ReportLab

**Input**:
- `image_urls`: List URL ảnh cho từng trang
- `scripts`: List nội dung text cho từng trang

**Output**: PDF bytes data

**Tính năng đặc biệt**:
- **Custom Backgrounds**: Hỗ trợ background riêng cho mỗi trang
- **Modern Fonts**: Comic Neue, Patrick Hand cho sách trẻ em
- **Large Text**: Font size 18pt, dễ đọc cho trẻ
- **Bold Text Effect**: Chữ dày, rõ ràng với hiệu ứng shadow
- **Auto Text Color**: Tự động chọn màu chữ (đen/trắng) theo độ sáng background
- **Professional Layout**: Landscape A4 với spacing tối ưu

**Ví dụ**:
```python
from src.ai.services.gen_book import create_pdf_book_bytes

pdf_bytes = await create_pdf_book_bytes(
    image_urls=["url1.jpg", "url2.jpg", "url3.jpg"],
    scripts=["Trang 1 content...", "Trang 2 content...", "Trang 3 content..."]
)
```

## 🔧 Cấu hình

### Environment Variables

```bash
# OpenAI API Key (cần thiết)
OPENAI_API_KEY=your_openai_api_key_here

# Replicate API Token (cần thiết cho image generation)
REPLICATE_API_TOKEN=your_replicate_api_token_here
```

### Dependencies

```txt
openai>=1.0.0          # AI text generation
replicate>=0.25.0      # AI image generation
rembg>=2.0.0          # Background removal
onnxruntime           # ML inference cho rembg
reportlab>=4.0.0      # PDF generation
Pillow>=10.0.0        # Image processing
```

## 📊 Workflow AI Processing

### Realistic Book Generation:
1. **LLM Script Generation** → GPT-4o-mini tạo nội dung 3 trang
2. **Parallel Image Generation** → Tạo ảnh minh họa cho từng trang
3. **PDF Compilation** → Kết hợp text và hình thành PDF

### Cartoon Book Generation:
1. **LLM Script Generation** → Giống trên
2. **Cartoon Conversion** → Chuyển ảnh gốc thành cartoon
3. **Cartoon Illustrations** → Tạo ảnh minh họa cartoon cho từng trang
4. **PDF Compilation** → Tạo PDF với style cartoon

## 🎯 API Endpoints

### Base URL: `/api/v1`

#### `POST /gen-script/`
Tạo nội dung sách từ loại sách và tên nhân vật.

#### `POST /gen-illustration-image/`
Tạo hình ảnh minh họa từ prompt và ảnh tham khảo.

#### `POST /gen-cartoon-image/`
Chuyển đổi ảnh thành phong cách cartoon.

#### `POST /remove-background/`
Loại bỏ background khỏi ảnh.

#### `POST /create-pdf-book/`
Tạo PDF từ nội dung và danh sách ảnh có sẵn.

#### `POST /create-realistic-book/`
**Workflow hoàn chỉnh**: Tạo sách realistic từ đầu đến cuối.

#### `POST /create-cartoon-book/`
**Workflow hoàn chỉnh**: Tạo sách cartoon từ đầu đến cuối.

## ⚡ Performance & Optimization

- **Parallel Processing**: Image generation được thực hiện song song
- **Caching**: Có thể implement caching cho repeated requests
- **Error Handling**: Comprehensive error handling với fallback
- **Rate Limiting**: Tự động handle API rate limits
- **Memory Management**: Efficient memory usage cho large images

## 🧪 Testing

```python
# Test individual services
from src.ai.services.llm import gen_script
from src.ai.services.gen_illustration_image import gen_illustration_image

# Test LLM
result = await gen_script("Khoa học viễn tưởng", "Lino")
assert result["success"] == True

# Test Image Generation
image_url = await gen_illustration_image("test prompt")
assert image_url is not None
```

## 🚨 Error Handling

- **API Errors**: Automatic retry với exponential backoff
- **Invalid Input**: Comprehensive input validation
- **Network Issues**: Timeout và connection error handling
- **Fallback Mechanisms**: Graceful degradation khi service unavailable

## 🔧 Development Notes

- **Async/Await**: Tất cả functions đều là async để optimize performance
- **Type Hints**: Full type annotations cho better IDE support
- **Logging**: Comprehensive logging cho debugging và monitoring
- **Configuration**: Environment-based configuration cho flexibility

## 📈 Monitoring & Analytics

- **Processing Time**: Track thời gian xử lý của mỗi service
- **Success Rate**: Monitor tỷ lệ thành công của API calls
- **Usage Statistics**: Log usage patterns để optimize
- **Error Tracking**: Detailed error logging cho troubleshooting

---

**Module này cung cấp foundation AI cho việc tạo sách thiếu nhi cá nhân hóa, kết hợp sức mạnh của multiple AI services để tạo ra sản phẩm cuối cùng chất lượng cao.**
