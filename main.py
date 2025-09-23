import time
import io
import os
import base64
import requests
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from models.llm import gen_script  # Import hàm từ models
from models.gen_illustration_image import gen_illustration_image  # Import hàm xử lý image
from models.gen_cartoon_image import gen_cartoon_image  # Import hàm tạo cartoon image
from models.gen_book import create_pdf_book_bytes  # Import hàm tạo PDF (tự động remove background)
from models.remove_background import remove_background  # Import hàm remove background cho endpoint riêng

# Pydantic models cho gen_script endpoint
class GenScriptRequest(BaseModel):
    type: str   # Book type (Khoa học viễn tưởng, etc.)
    name: str   # Character name for the story

class GenScriptResponse(BaseModel):
    script: dict
    script_type: str
    processing_time: float
    model_used: str
    success: bool

# Pydantic models cho gen_illustration_image endpoint
class GenImagesRequest(BaseModel):
    prompt: str  # Prompt tạo ảnh
    image_url: str  # URL ảnh tham khảo

class GenImagesResponse(BaseModel):
    generated_image_url: str
    success: bool
    processing_time: float
    message: str

# Pydantic models cho gen_cartoon_image endpoint
class GenCartoonImageRequest(BaseModel):
    image_url: str  # URL ảnh đầu vào để chuyển thành cartoon

class GenCartoonImageResponse(BaseModel):
    generated_image_url: str
    success: bool
    processing_time: float
    message: str

# Pydantic models cho create_pdf_book endpoint
class CreatePDFBookRequest(BaseModel):
    scripts: List[str]  # Danh sách các đoạn script cho từng trang
    image_urls: List[str]  # Danh sách URL ảnh cho từng trang
    background_urls: List[str] = []  # Danh sách URL background cho từng trang (tùy chọn)

# Pydantic models cho remove_background endpoint
class RemoveBackgroundRequest(BaseModel):
    image_url: str  # URL ảnh đầu vào để remove background

class RemoveBackgroundResponse(BaseModel):
    processed_image_data: str  # Base64 data URL của ảnh đã remove background
    success: bool
    processing_time: float
    message: str

# Pydantic models cho book_generation endpoint
class BookGenerationRequest(BaseModel):
    type: str   # Book type (Khoa học viễn tưởng, etc.)
    name: str   # Character name for the story
    image: str  # URL ảnh tham khảo để tạo hình ảnh cho sách


# Tạo instance của FastAPI
app = FastAPI(
    title="High5 Gen Book API",
    description="API tạo sách thiếu nhi cá nhân hóa",
    version="1.0.0"
)

# CORS middleware để cho phép frontend truy cập
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Trong production nên chỉ định domain cụ thể
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Route cơ bản
@app.get("/")
async def read_root():
    return {"message": "Chào mừng đến với High5 Gen Book!"}

# Route tạo nội dung sách thiếu nhi cá nhân hóa
@app.post("/gen-script/", response_model=GenScriptResponse)
async def create_script(request: GenScriptRequest):
    """
    Endpoint tạo nội dung sách thiếu nhi cá nhân hóa
    Nhận type (loại sách như "Khoa học viễn tưởng") và name (tên nhân vật chính), tạo câu chuyện 3 trang đầu tiên
    """
    # Gọi hàm gen_script từ models với type và name
    result = await gen_script(type=request.type, name=request.name)

    # Trả về kết quả với validation từ Pydantic
    return GenScriptResponse(
        script=result.get("script", {}),
        script_type=result["script_type"],
        processing_time=result["processing_time"],
        model_used=result.get("model_used", "unknown"),
        success=result["success"]
    )

# Route tạo hình ảnh từ nội dung sách
@app.post("/gen-illustration-image/", response_model=GenImagesResponse)
async def create_images(request: GenImagesRequest):
    """
    Endpoint tạo hình ảnh từ prompt và ảnh tham khảo
    Nhận prompt (mô tả ảnh cần tạo) và image_url (URL ảnh tham khảo)
    """
    start_time = time.time()

    try:
        # Gọi hàm gen_illustration_image từ models với prompt và image_url
        generated_url = await gen_illustration_image(
            prompt=request.prompt,
            image_url=request.image_url
        )

        processing_time = time.time() - start_time

        if generated_url:
            return GenImagesResponse(
                generated_image_url=generated_url,
                success=True,
                processing_time=processing_time,
                message="Tạo ảnh thành công!"
            )
        else:
            return GenImagesResponse(
                generated_image_url="",
                success=False,
                processing_time=processing_time,
                message="Không thể tạo ảnh. Vui lòng thử lại."
            )

    except Exception as e:
        processing_time = time.time() - start_time
        return GenImagesResponse(
            generated_image_url="",
            success=False,
            processing_time=processing_time,
            message=f"Lỗi khi tạo ảnh: {str(e)}"
        )

# Route tạo ảnh cartoon từ ảnh đầu vào
@app.post("/gen-cartoon-image/", response_model=GenCartoonImageResponse)
async def create_cartoon_image(request: GenCartoonImageRequest):
    """
    Endpoint tạo ảnh cartoon từ URL ảnh đầu vào
    Sử dụng prompt cố định: "Make this a 90s cartoon"
    """
    start_time = time.time()

    try:
        # Gọi hàm gen_cartoon_image từ models với image_url
        generated_url = await gen_cartoon_image(
            image_url=request.image_url
        )

        processing_time = time.time() - start_time

        if generated_url:
            return GenCartoonImageResponse(
                generated_image_url=generated_url,
                success=True,
                processing_time=processing_time,
                message="Tạo ảnh cartoon thành công!"
            )
        else:
            return GenCartoonImageResponse(
                generated_image_url="",
                success=False,
                processing_time=processing_time,
                message="Không thể tạo ảnh cartoon. Vui lòng thử lại."
            )

    except Exception as e:
        processing_time = time.time() - start_time
        return GenCartoonImageResponse(
            generated_image_url="",
            success=False,
            processing_time=processing_time,
            message=f"Lỗi khi tạo ảnh cartoon: {str(e)}"
        )

# Route remove background từ ảnh
@app.post("/remove-background/", response_model=RemoveBackgroundResponse)
async def remove_image_background(request: RemoveBackgroundRequest):
    """
    Endpoint remove background từ ảnh đầu vào
    Nhận URL ảnh và trả về base64 data URL của ảnh đã remove background
    """
    start_time = time.time()

    try:
        # Gọi hàm remove_background từ models với image_url
        processed_image_data = await remove_background(image_url=request.image_url)

        processing_time = time.time() - start_time

        if processed_image_data:
            return RemoveBackgroundResponse(
                processed_image_data=processed_image_data,
                success=True,
                processing_time=processing_time,
                message="Remove background thành công!"
            )
        else:
            return RemoveBackgroundResponse(
                processed_image_data="",
                success=False,
                processing_time=processing_time,
                message="Không thể remove background. Vui lòng thử lại với ảnh khác."
            )

    except Exception as e:
        processing_time = time.time() - start_time
        return RemoveBackgroundResponse(
            processed_image_data="",
            success=False,
            processing_time=processing_time,
            message=f"Lỗi khi remove background: {str(e)}"
        )

# Route tạo file PDF và trả về trực tiếp (không lưu)
@app.post("/create-pdf-book/")
async def create_pdf_book_direct_endpoint(request: CreatePDFBookRequest):
    """
    Tạo PDF sách từ scripts và image URLs, trả về trực tiếp không lưu file.

    Request body:
    - scripts: Danh sách text cho từng trang (đã escape \\n cho xuống dòng)
    - image_urls: Danh sách URL ảnh tương ứng
    - background_urls: Danh sách URL background cho từng trang (tùy chọn)

    Response: StreamingResponse với file PDF
    """
    start_time = time.time()

    try:
        # Kiểm tra số lượng scripts và image_urls có khớp nhau không
        if len(request.scripts) != len(request.image_urls):
            raise HTTPException(
                status_code=400,
                detail=f"Số lượng scripts ({len(request.scripts)}) và image URLs ({len(request.image_urls)}) phải bằng nhau."
            )

        if len(request.scripts) == 0:
            raise HTTPException(
                status_code=400,
                detail="Phải có ít nhất một script và một image URL."
            )

        # Tạo PDF dưới dạng bytes với background tự động (tự động remove background)
        pdf_bytes = await create_pdf_book_bytes(
            image_urls=request.image_urls,
            scripts=request.scripts
        )

        processing_time = time.time() - start_time

        # Trả về file PDF trực tiếp với StreamingResponse
        def generate_pdf():
            yield pdf_bytes

        response = StreamingResponse(
            generate_pdf(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=generated_book_{int(time.time())}.pdf",
                "X-Processing-Time": f"{processing_time:.2f}",
                "X-Page-Count": str(len(request.scripts)),
                "X-File-Size": str(len(pdf_bytes))
            }
        )

        return response

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Lỗi khi tải ảnh: {str(e)}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")


# Route tổng hợp tạo sách hoàn chỉnh từ type và image
@app.post("/create-realistic-book/")
async def generate_realistic_book(request: BookGenerationRequest):
    """
    Endpoint tổng hợp tạo sách hoàn chỉnh từ type, name và ảnh tham khảo.
    Kết hợp gen-script, gen-images và create-pdf-book thành một endpoint duy nhất.

    Request body:
    - type: Loại sách (vd: "Khoa học viễn tưởng")
    - name: Tên nhân vật chính trong câu chuyện
    - image: URL ảnh tham khảo để tạo hình ảnh

    Response: StreamingResponse với file PDF hoàn chỉnh
    """
    start_time = time.time()

    try:
        # Bước 1: Tạo script từ type và name
        print(f"Generating script for type: {request.type} with character: {request.name}")
        script_result = await gen_script(type=request.type, name=request.name)

        if not script_result.get("success", False):
            error_detail = script_result.get('error', 'Unknown error')
            if isinstance(error_detail, str):
                error_detail = error_detail.encode('utf-8').decode('utf-8')
            raise HTTPException(
                status_code=400,
                detail=f"Không thể tạo script: {error_detail}"
            )

        script_data = script_result.get("script", {})
        content = script_data.get("content", {})

        if not content:
            raise HTTPException(
                status_code=400,
                detail="Không có nội dung trong script được tạo"
            )

        # Bước 2: Tạo hình ảnh cho từng trang
        scripts = []
        page_generation_data = []  # Danh sách dữ liệu để tạo ảnh parallel

        # Chuẩn bị dữ liệu cho tất cả các trang
        for page_key, page_data in content.items():
            page_content = page_data.get("page-content", "")
            page_prompt = page_data.get("page-prompt", "")

            if not page_content or not page_prompt:
                print(f"Skipping page {page_key} - missing content or prompt")
                continue

            # Đảm bảo encoding UTF-8 cho text
            try:
                page_content = page_content.encode('utf-8').decode('utf-8')
                page_prompt = page_prompt.encode('utf-8').decode('utf-8')
            except (UnicodeDecodeError, UnicodeEncodeError):
                # Fallback nếu có vấn đề encoding
                pass

            scripts.append(page_content)
            page_generation_data.append((page_key, page_prompt))

        # Function helper để tạo ảnh cho một trang
        async def generate_single_image(page_key: str, page_prompt: str, image_url: str):
            try:
                print(f"Generating image for page {page_key}")
                generated_url = await gen_illustration_image(
                    prompt=page_prompt,
                    image_url=image_url
                )

                if generated_url:
                    print(f"Generated image for page {page_key}: {generated_url}")
                    return generated_url
                else:
                    print(f"Using original image for page {page_key}")
                    return image_url

            except Exception as img_error:
                print(f"Error generating image for page {page_key}: {str(img_error)}")
                return image_url

        # Tạo danh sách các coroutine tasks để thực thi parallel
        page_tasks = [
            generate_single_image(page_key, page_prompt, request.image)
            for page_key, page_prompt in page_generation_data
        ]

        # Thực hiện tất cả tasks parallel và chờ kết quả
        print(f"Starting parallel generation of {len(page_tasks)} images")
        image_urls = await asyncio.gather(*page_tasks, return_exceptions=True)

        # Xử lý kết quả, thay thế exception bằng fallback image
        for i, result in enumerate(image_urls):
            if isinstance(result, Exception):
                print(f"Exception in parallel task {i}: {str(result)}")
                image_urls[i] = request.image
            # Nếu result là URL hợp lệ thì giữ nguyên

        # Bước 3: Kiểm tra dữ liệu
        if len(scripts) != len(image_urls):
            raise HTTPException(
                status_code=500,
                detail=f"Số lượng scripts ({len(scripts)}) và image URLs ({len(image_urls)}) không khớp"
            )

        if len(scripts) == 0:
            raise HTTPException(
                status_code=400,
                detail="Không có nội dung nào được tạo"
            )

        # Bước 4: Tạo PDF với background tự động (tự động remove background)
        print(f"Creating PDF with {len(scripts)} pages")
        pdf_bytes = await create_pdf_book_bytes(
            image_urls=image_urls,
            scripts=scripts
        )

        processing_time = time.time() - start_time

        # Trả về file PDF trực tiếp
        def generate_pdf():
            yield pdf_bytes

        response = StreamingResponse(
            generate_pdf(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=generated_book_{int(time.time())}.pdf",
                "X-Processing-Time": f"{processing_time:.2f}",
                "X-Page-Count": str(len(scripts)),
                "X-File-Size": str(len(pdf_bytes)),
                # HTTP headers must be latin-1. Send book type as Base64 to preserve Unicode
                "X-Book-Type-Base64": base64.b64encode(request.type.encode("utf-8")).decode("ascii")
            }
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = str(e).encode('utf-8').decode('utf-8')
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi tạo sách hoàn chỉnh: {error_msg}"
        )


# Route tổng hợp tạo sách cartoon hoàn chỉnh từ type và image
@app.post("/create-cartoon-book/")
async def generate_cartoon_book(request: BookGenerationRequest):
    """
    Endpoint tổng hợp tạo sách cartoon hoàn chỉnh từ type, name và ảnh tham khảo.
    Đầu tiên chuyển đổi ảnh gốc thành cartoon, sau đó tạo sách với style cartoon.

    Request body:
    - type: Loại sách (vd: "Khoa học viễn tưởng")
    - name: Tên nhân vật chính trong câu chuyện
    - image: URL ảnh tham khảo để tạo hình ảnh cartoon

    Response: StreamingResponse với file PDF hoàn chỉnh (style cartoon)
    """
    start_time = time.time()

    try:
        # Bước 1: Tạo script từ type và name
        print(f"Generating script for cartoon book - type: {request.type} with character: {request.name}")
        script_result = await gen_script(type=request.type, name=request.name)

        if not script_result.get("success", False):
            error_detail = script_result.get('error', 'Unknown error')
            if isinstance(error_detail, str):
                error_detail = error_detail.encode('utf-8').decode('utf-8')
            raise HTTPException(
                status_code=400,
                detail=f"Không thể tạo script: {error_detail}"
            )

        script_data = script_result.get("script", {})
        content = script_data.get("content", {})

        if not content:
            raise HTTPException(
                status_code=400,
                detail="Không có nội dung trong script được tạo"
            )

        # Bước 2: Chuyển đổi ảnh gốc thành cartoon
        print(f"Converting original image to cartoon: {request.image}")
        cartoon_image_url = await gen_cartoon_image(
            image_url=request.image
        )

        if not cartoon_image_url:
            raise HTTPException(
                status_code=400,
                detail="Không thể tạo ảnh cartoon từ ảnh gốc. Vui lòng thử lại với ảnh khác."
            )

        print(f"Generated cartoon image: {cartoon_image_url}")

        # Bước 3: Tạo hình ảnh cho từng trang sử dụng ảnh cartoon làm tham khảo
        scripts = []
        page_generation_data = []  # Danh sách dữ liệu để tạo ảnh parallel

        # Chuẩn bị dữ liệu cho tất cả các trang
        for page_key, page_data in content.items():
            page_content = page_data.get("page-content", "")
            page_prompt = page_data.get("page-prompt", "")

            if not page_content or not page_prompt:
                print(f"Skipping page {page_key} - missing content or prompt")
                continue

            # Đảm bảo encoding UTF-8 cho text
            try:
                page_content = page_content.encode('utf-8').decode('utf-8')
                page_prompt = page_prompt.encode('utf-8').decode('utf-8')
            except (UnicodeDecodeError, UnicodeEncodeError):
                # Fallback nếu có vấn đề encoding
                pass

            scripts.append(page_content)
            page_generation_data.append((page_key, page_prompt))

        # Function helper để tạo ảnh cho một trang
        async def generate_single_image(page_key: str, page_prompt: str, cartoon_image_url: str):
            try:
                print(f"Generating cartoon illustration for page {page_key}")
                generated_url = await gen_illustration_image(
                    prompt=page_prompt,
                    image_url=cartoon_image_url
                )

                if generated_url:
                    print(f"Generated cartoon illustration for page {page_key}: {generated_url}")
                    return generated_url
                else:
                    print(f"Using cartoon base image for page {page_key}")
                    return cartoon_image_url

            except Exception as img_error:
                print(f"Error generating cartoon illustration for page {page_key}: {str(img_error)}")
                return cartoon_image_url

        # Tạo danh sách các coroutine tasks để thực thi parallel
        page_tasks = [
            generate_single_image(page_key, page_prompt, cartoon_image_url)
            for page_key, page_prompt in page_generation_data
        ]

        # Thực hiện tất cả tasks parallel và chờ kết quả
        print(f"Starting parallel generation of {len(page_tasks)} cartoon illustrations")
        image_urls = await asyncio.gather(*page_tasks, return_exceptions=True)

        # Xử lý kết quả, thay thế exception bằng fallback image
        for i, result in enumerate(image_urls):
            if isinstance(result, Exception):
                print(f"Exception in parallel task {i}: {str(result)}")
                image_urls[i] = cartoon_image_url
            # Nếu result là URL hợp lệ thì giữ nguyên

        # Bước 4: Kiểm tra dữ liệu
        if len(scripts) != len(image_urls):
            raise HTTPException(
                status_code=500,
                detail=f"Số lượng scripts ({len(scripts)}) và image URLs ({len(image_urls)}) không khớp"
            )

        if len(scripts) == 0:
            raise HTTPException(
                status_code=400,
                detail="Không có nội dung nào được tạo"
            )

        # Bước 5: Tạo PDF cartoon với background tự động (tự động remove background)
        print(f"Creating cartoon PDF with {len(scripts)} pages")
        pdf_bytes = await create_pdf_book_bytes(
            image_urls=image_urls,
            scripts=scripts
        )

        processing_time = time.time() - start_time

        # Trả về file PDF trực tiếp
        def generate_pdf():
            yield pdf_bytes

        response = StreamingResponse(
            generate_pdf(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=cartoon_book_{int(time.time())}.pdf",
                "X-Processing-Time": f"{processing_time:.2f}",
                "X-Page-Count": str(len(scripts)),
                "X-File-Size": str(len(pdf_bytes)),
                "X-Book-Style": "cartoon",
                # HTTP headers must be latin-1. Send book type as Base64 to preserve Unicode
                "X-Book-Type-Base64": base64.b64encode(request.type.encode("utf-8")).decode("ascii")
            }
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = str(e).encode('utf-8').decode('utf-8')
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi khi tạo sách cartoon: {error_msg}"
        )

