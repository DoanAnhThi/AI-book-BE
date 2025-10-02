import time
import asyncio
import json
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
class StoryRequest(BaseModel):
    story_id: str

class GenScriptRequest(BaseModel):
    category_id: str
    book_id: str
    stories: List[StoryRequest]
    gender: str  # For future use
    language: str  # For future use
    name: str  # Character name
    image_url: str  # Face image URL for swapping

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

# Pydantic models cho create_book endpoint
class CreateBookRequest(BaseModel):
    category_id: str
    book_id: str
    stories: List[StoryRequest]
    gender: str  # For future use
    language: str  # For future use
    name: str  # Character name
    image_url: str  # Face image URL for swapping

class CreateBookResponse(BaseModel):
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


@router.post("/create-book/")
async def create_book_endpoint(request: CreateBookRequest):
    """
    Tạo một cuốn sách PDF với nhiều trang từ các stories được chỉ định.

    Request body:
    - category_id: ID category
    - book_id: ID book
    - stories: Array của story objects với story_id
    - gender: Giới tính nhân vật (for future use)
    - language: Ngôn ngữ (for future use)
    - name: Tên nhân vật chính
    - image_url: URL ảnh face để swap vào characters

    Response: StreamingResponse với file PDF nhiều trang
    """
    start_time = time.time()

    try:
        # Load catalog metadata
        from pathlib import Path
        import yaml

        BASE_DIR = Path(__file__).resolve().parents[3]
        catalog_path = BASE_DIR / "assets" / "catalog_metadata.yaml"

        with catalog_path.open("r", encoding="utf-8") as f:
            catalog_data = yaml.safe_load(f)

        # Collect all pages to process
        all_pages = []
        for story_req in request.stories:
            story_id = story_req.story_id
            # Find all pages for this story (assuming 2 pages per story)
            for page_id in ["01", "02"]:
                try:
                    page_key = get_page_id(request.category_id, request.book_id, story_id, page_id)
                    all_pages.append(page_key)
                except HTTPException:
                    # Skip if page doesn't exist
                    continue

        if not all_pages:
            raise HTTPException(status_code=400, detail="No valid pages found for the specified stories")

        # Process all pages in parallel
        async def process_page(page_key):
            try:
                page_metadata = catalog_data["pages"].get(page_key)
                if not page_metadata:
                    return None, None

                # Load story content
                story_file_path = BASE_DIR / page_metadata["story_file"]
                with story_file_path.open("r", encoding="utf-8") as f:
                    story_data = json.load(f)

                page_content = story_data.get("page_content")
                if not page_content:
                    return None, None

                # Get character
                character_path = page_metadata["character"]
                # Send file path directly instead of URL for Replicate upload

                # Face swap
                face_swap_result = await swap_face(
                    face_image_url=request.image_url,
                    body_image_url=character_path  # Send file path for direct upload
                )

                if face_swap_result["success"]:
                    swapped_image_url = face_swap_result["swapped_image_url"]
                else:
                    # Fallback to original character URL
                    swapped_image_url = f"http://localhost:8000/{character_path}"

                # Remove background
                try:
                    processed_image_data = await remove_background(image_url=swapped_image_url)
                except:
                    processed_image_data = swapped_image_url

                return page_content, processed_image_data

            except Exception as e:
                print(f"Error processing page {page_key}: {e}")
                return None, None

        # Process all pages in parallel
        tasks = [process_page(page_key) for page_key in all_pages]
        results = await asyncio.gather(*tasks)

        # Collect valid results
        all_scripts = []
        all_image_urls = []

        for page_content, processed_image in results:
            if page_content and processed_image:
                all_scripts.append(page_content)
                all_image_urls.append(processed_image)

        if not all_scripts or not all_image_urls:
            raise HTTPException(status_code=400, detail="No valid pages processed")

        # Collect background local paths from catalog metadata
        background_urls = []
        for page_key in all_pages:
            page_metadata = catalog_data["pages"].get(page_key)
            if page_metadata:
                background_path = page_metadata["background"]
                # Use local file path for PDF generation (like the old create_page did)
                background_full_path = BASE_DIR / background_path
                if background_full_path.exists():
                    background_urls.append(str(background_full_path))
                else:
                    background_urls.append(None)  # Fallback
            else:
                background_urls.append(None)  # Fallback

        # Create PDF with all pages
        pdf_bytes = await create_pdf_book_bytes(
            image_urls=all_image_urls,
            scripts=all_scripts,
            background_urls=background_urls
        )

        processing_time = time.time() - start_time

        # Return PDF as streaming response
        def generate_pdf():
            yield pdf_bytes

        response = StreamingResponse(
            generate_pdf(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=book_{request.category_id}_{request.book_id}_{int(time.time())}.pdf",
                "X-Processing-Time": f"{processing_time:.2f}",
                "X-Page-Count": str(len(all_scripts)),
                "X-File-Size": str(len(pdf_bytes))
            }
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        raise HTTPException(
            status_code=500,
            detail=f"Book creation failed: {str(e)}"
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


    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Lỗi khi tải ảnh: {str(e)}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi server: {str(e)}")


