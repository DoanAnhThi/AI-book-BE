import time
import io
import os
import json
import base64
import binascii
import requests
import asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from src.ai.services.llm import gen_script  # Import hàm từ services
from src.ai.services.llm_gen_prompt import gen_prompt
from src.ai.services.gen_illustration_image import gen_illustration_image  # Import hàm xử lý image
from src.ai.services.gen_cartoon_image import gen_cartoon_image  # Import hàm tạo cartoon image
from src.ai.services.gen_book import create_pdf_book_bytes, get_background_urls
from src.ai.services.merge_PDF_book import merge_pdf_books
from src.ai.services.remove_background import remove_background  # Import hàm remove background cho endpoint riêng
# Pydantic models cho multi-book endpoint
class BookInput(BaseModel):
    story: str
    image: str
    main_character: str


class MultiBookRequest(BaseModel):
    books: List[BookInput]


class GenPromptRequest(BaseModel):
    scripts: List[str]
    story: Optional[str] = None
    main_character: Optional[str] = None
    illustration_style: Optional[str] = None


class GenPromptResponse(BaseModel):
    page_prompts: List[str]
    processing_time: float
    model_used: Optional[str]
    success: bool
    error: Optional[str] = None


class MergePdfRequest(BaseModel):
    pdfs: List[str]
    output_filename: Optional[str] = None


class MergePdfResponse(BaseModel):
    merged_pdf_base64: str
    success: bool
    message: str

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

# Tạo APIRouter instance
router = APIRouter()

# Route cơ bản
@router.get("/")
async def read_root():
    return {"message": "Chào mừng đến với High5 Gen Book!"}

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


# Route tổng hợp tạo sách hoàn chỉnh từ type và image
@router.post("/create-realistic-book/")
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
@router.post("/create-cartoon-book/")
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


# Route tạo prompt từ scripts
@router.post("/gen-prompt/", response_model=GenPromptResponse)
async def generate_prompts(request: GenPromptRequest):
    """
    Endpoint tạo illustration prompts từ danh sách scripts.

    Request body:
    - scripts: Danh sách nội dung trang
    - story: Chủ đề sách (tùy chọn)
    - main_character: Tên nhân vật chính (tùy chọn)
    - illustration_style: Phong cách vẽ (tùy chọn)

    Response: GenPromptResponse với danh sách prompts
    """
    start_time = time.time()

    try:
        result = await gen_prompt(
            scripts=request.scripts,
            story=request.story,
            main_character=request.main_character,
            illustration_style=request.illustration_style
        )

        processing_time = time.time() - start_time

        return GenPromptResponse(
            page_prompts=result["page_prompts"],
            processing_time=result["processing_time"],
            model_used=result["model_used"],
            success=result["success"],
            error=result.get("error")
        )

    except Exception as e:
        processing_time = time.time() - start_time
        return GenPromptResponse(
            page_prompts=[],
            processing_time=processing_time,
            model_used=None,
            success=False,
            error=str(e)
        )


# Route merge PDFs
@router.post("/merge-pdf/", response_model=MergePdfResponse)
async def merge_pdfs_endpoint(request: MergePdfRequest):
    """
    Endpoint merge nhiều PDF thành một PDF duy nhất.

    Request body:
    - pdfs: Danh sách base64 strings của các PDF
    - output_filename: Tên file output (tùy chọn)

    Response: MergePdfResponse với base64 của PDF đã merge
    """
    start_time = time.time()

    try:
        # Decode base64 PDFs to bytes
        pdf_bytes_list = []
        for pdf_base64 in request.pdfs:
            try:
                pdf_bytes = base64.b64decode(pdf_base64)
                pdf_bytes_list.append(pdf_bytes)
            except (ValueError, binascii.Error) as decode_error:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid base64 PDF data: {str(decode_error)}"
                )

        # Merge PDFs
        merged_bytes = await merge_pdf_books(pdf_bytes_list, request.output_filename)

        # Encode merged PDF to base64
        merged_base64 = base64.b64encode(merged_bytes).decode('utf-8')

        processing_time = time.time() - start_time

        return MergePdfResponse(
            merged_pdf_base64=merged_base64,
            success=True,
            message=f"Merged {len(pdf_bytes_list)} PDFs successfully in {processing_time:.2f}s"
        )

    except HTTPException:
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        return MergePdfResponse(
            merged_pdf_base64="",
            success=False,
            message=f"Error merging PDFs: {str(e)}"
        )


# Route tạo multi-book từ payload có sẵn
@router.post("/multi-book/")
async def generate_multi_book(request: MultiBookRequest):
    """
    Endpoint tạo nhiều cuốn sách từ payload có sẵn, sau đó merge thành một PDF tổng.
    Script được load từ file assets/scripts/{story}.json, background từ assets/backgrounds/{story}/.

    Request body:
    - books: Danh sách các book với story, image, main_character
      (script được load tự động từ file theo story, style đã có sẵn trong script)

    Response: StreamingResponse với file PDF tổng đã merge
    """
    start_time = time.time()
    all_pdf_bytes = []

    try:
        # Validate all stories and scripts before processing
        print("🚀 Starting multi-book generation...")
        print(f"📋 Processing {len(request.books)} book(s)")
        print("🔍 Validating stories and scripts...")

        for book_idx, book in enumerate(request.books, start=1):
            print(f"  📂 Checking book {book_idx}: story='{book.story}', character='{book.main_character}'")
            try:
                # Validate background directory exists
                print(f"    🎨 Checking background directory for story '{book.story}'...")
                from src.ai.services.gen_book import _resolve_background_directory
                background_dir = _resolve_background_directory(book.story, allow_fallback=False)
                print(f"    ✅ Background directory found: {os.path.basename(background_dir)}")

                # Validate script file exists
                print(f"    📖 Checking script file for story '{book.story}'...")
                from src.ai.services.gen_book import load_script_from_file
                script_data = load_script_from_file(book.story, book.main_character)  # Test load
                print(f"    ✅ Script file loaded: {len(script_data['pages'])} pages")

                print(f"✓ Book {book_idx} validation completed")
            except ValueError as validation_error:
                print(f"❌ Validation failed for book {book_idx}: {str(validation_error)}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid configuration for book {book_idx}: {str(validation_error)}"
                )

        print("✅ All validations passed, starting processing...")

        for book_idx, book in enumerate(request.books, start=1):
            print(f"\n📖 Processing book {book_idx}/{len(request.books)}: story='{book.story}', character='{book.main_character}'")
            book_start_time = time.time()

            # Bước 1: Load script từ file và tạo prompts
            print(f"  🔄 Step 1/3: Loading script from file and preparing prompts...")
            try:
                from src.ai.services.gen_book import load_script_from_file
                script_data = load_script_from_file(book.story, book.main_character)
                scripts = [page['page_content'] for page in script_data['pages']]
                page_prompts = [page['page_prompt'] for page in script_data['pages']]
                print(f"  ✅ Script loaded: {len(scripts)} pages with prompts ready")
            except ValueError as script_error:
                print(f"  ❌ Failed to load script for book {book_idx}: {script_error}")
                continue

            # Bước 2: Tạo illustrations song song
            print(f"  🎨 Step 2/3: Generating {len(page_prompts)} illustrations...")
            illustration_start = time.time()

            illustration_tasks = []
            for idx, prompt in enumerate(page_prompts):
                print(f"    📸 Starting illustration {idx + 1}/{len(page_prompts)}...")
                illustration_tasks.append(gen_illustration_image(
                    prompt=prompt,
                    image_url=book.image
                ))

            image_urls = await asyncio.gather(*illustration_tasks, return_exceptions=True)
            illustration_time = time.time() - illustration_start

            # Xử lý exceptions
            success_count = 0
            for i, result in enumerate(image_urls):
                if isinstance(result, Exception):
                    print(f"    ⚠️ Illustration {i + 1} failed: {str(result)[:100]}...")
                    image_urls[i] = book.image
                else:
                    success_count += 1

            print(f"  ✅ Illustrations completed: {success_count}/{len(image_urls)} successful ({illustration_time:.1f}s)")

            # Bước 3: Tạo PDF cho cuốn sách này
            print(f"  📄 Step 3/3: Creating PDF for book {book_idx}...")
            pdf_start = time.time()

            pdf_bytes = await create_pdf_book_bytes(
                image_urls=image_urls,
                scripts=scripts,  # Use loaded scripts from file
                story=book.story,  # Required parameter - will validate background exists
                allow_fallback=False  # No fallback for multi-book - each story must exist
            )

            pdf_time = time.time() - pdf_start
            all_pdf_bytes.append(pdf_bytes)
            book_time = time.time() - book_start_time
            print(f"  ✅ PDF created: {len(pdf_bytes)} bytes ({pdf_time:.1f}s)")
            print(f"  🎉 Book {book_idx} completed in {book_time:.1f}s")

        if not all_pdf_bytes:
            raise HTTPException(
                status_code=500,
                detail="Không thể tạo được cuốn sách nào"
            )

        # Bước 4: Merge tất cả PDFs
        print(f"\n🔗 Step 4: Merging {len(all_pdf_bytes)} PDFs into final book...")
        merge_start = time.time()

        merged_bytes = await merge_pdf_books(all_pdf_bytes)

        merge_time = time.time() - merge_start
        processing_time = time.time() - start_time

        print(f"✅ PDF merge completed: {len(merged_bytes)} bytes ({merge_time:.1f}s)")
        print(f"🎊 Multi-book generation completed in {processing_time:.1f}s total")

        # Trả về file PDF tổng
        def generate_pdf():
            yield merged_bytes

        response = StreamingResponse(
            generate_pdf(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=multi_book_{int(time.time())}.pdf",
                "X-Processing-Time": f"{processing_time:.2f}",
                "X-Book-Count": str(len(request.books)),
                "X-File-Size": str(len(merged_bytes)),
                "X-Total-Pages": "unknown"  # Có thể tính sau nếu cần
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
            detail=f"Lỗi khi tạo multi-book: {error_msg}"
        )
