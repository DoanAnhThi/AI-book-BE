import time
import requests
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from src.ai.services.llm import gen_script  # Import hàm từ services
from src.ai.services.gen_illustration_image import gen_illustration_image  # Import hàm xử lý image
from src.ai.services.gen_avatar import gen_avatar  # Import hàm tạo cartoon image
from src.ai.services.gen_book import create_pdf_book_bytes
from src.ai.services.remove_background import remove_background  # Import hàm remove background cho endpoint riêng
from src.ai.services.get_page_id import get_page_id  # Import hàm get_page_id từ services
from src.ai.services.swap_face import swap_face  # Import hàm swap_face từ services
from src.ai.services.gen_page import generate_page  # Import hàm generate_page từ services

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

# Pydantic models cho gen_avatar endpoint
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


class PageIdRequest(BaseModel):
    category_id: str
    book_id: str
    story_id: str
    page_id: str


class PageIdResponse(BaseModel):
    id: str

# Pydantic models cho swap_face endpoint
class SwapFaceRequest(BaseModel):
    face_image_url: str  # URL của ảnh face để swap
    body_image_url: str  # URL của ảnh body để đặt face vào

class SwapFaceResponse(BaseModel):
    swapped_image_url: str
    success: bool
    processing_time: float
    model_used: str
    error: Optional[str] = None

# Pydantic models cho create_page endpoint
class CreatePageRequest(BaseModel):
    category_id: str
    book_id: str
    story_id: str
    page_id: str
    image_url: str  # URL của ảnh face để swap vào character

class CreatePageResponse(BaseModel):
    page_key: str
    background_path: str
    character_path: str
    story_file_path: str
    swapped_character_url: str
    page_content: str
    processing_time: float
    success: bool

# Tạo APIRouter instance
router = APIRouter()

# Route get page ID
@router.post("/get-page-id/", response_model=PageIdResponse)
async def get_page_id_endpoint(request: PageIdRequest) -> PageIdResponse:
    page_id = get_page_id(
        category_id=request.category_id,
        book_id=request.book_id,
        story_id=request.story_id,
        page_id=request.page_id,
    )

    return PageIdResponse(id=page_id)


@router.post("/swap-face/", response_model=SwapFaceResponse)
async def swap_face_endpoint(request: SwapFaceRequest) -> SwapFaceResponse:
    """
    Endpoint swap face từ face_image_url lên body_image_url.
    Sử dụng AI model để thực hiện face swapping.

    Request body:
    - face_image_url: URL ảnh face cần swap
    - body_image_url: URL ảnh body để đặt face vào

    Response: SwapFaceResponse với URL ảnh đã swap và metadata
    """
    result = await swap_face(
        face_image_url=request.face_image_url,
        body_image_url=request.body_image_url
    )

    return SwapFaceResponse(
        swapped_image_url=result.get("swapped_image_url", ""),
        success=result.get("success", False),
        processing_time=result.get("processing_time", 0.0),
        model_used=result.get("model_used", "unknown"),
        error=result.get("error")
    )


@router.post("/create-page/")
async def create_page_endpoint(request: CreatePageRequest):
    """
    Tạo một trang PDF đơn với background, character đã swap face và page content.

    Request body:
    - category_id: ID category
    - book_id: ID book
    - story_id: ID story
    - page_id: ID page
    - image_url: URL ảnh face để swap vào character

    Response: StreamingResponse với file PDF trang đơn
    """
    start_time = time.time()

    try:
        # Generate the page
        result = await generate_page(
            category_id=request.category_id,
            book_id=request.book_id,
            story_id=request.story_id,
            page_id=request.page_id,
            image_url=request.image_url
        )

        processing_time = time.time() - start_time

        # Return PDF as streaming response
        def generate_pdf():
            yield result["pdf_bytes"]

        response = StreamingResponse(
            generate_pdf(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=page_{result['page_key']}.pdf",
                "X-Processing-Time": f"{processing_time:.2f}",
                "X-Page-Key": result["page_key"],
                "X-File-Size": str(len(result["pdf_bytes"]))
            }
        )

        return response

    except Exception as e:
        processing_time = time.time() - start_time
        raise HTTPException(
            status_code=500,
            detail=f"Page creation failed: {str(e)}"
        )


# Route tạo nội dung sách thiếu nhi cá nhân hóa
@router.post("/gen-script/", response_model=GenScriptResponse)
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
@router.post("/gen-illustration-image/", response_model=GenImagesResponse)
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
@router.post("/gen-cartoon-image/", response_model=GenCartoonImageResponse)
async def create_cartoon_image(request: GenCartoonImageRequest):
    """
    Endpoint tạo ảnh cartoon từ URL ảnh đầu vào
    Sử dụng prompt cố định: "Make this a 90s cartoon"
    """
    start_time = time.time()

    try:
        # Gọi hàm gen_avatar từ models với image_url
        generated_url = await gen_avatar(
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
@router.post("/remove-background/", response_model=RemoveBackgroundResponse)
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
@router.post("/create-pdf-book/")
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


