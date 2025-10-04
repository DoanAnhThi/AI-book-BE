from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import time
import os

# Import test service functions
from src.ai.services.create_cover import create_cover_test
from src.ai.services.create_interleafs import create_interleafs_test
from src.ai.services.create_content import create_main_content_test

# Pydantic models for test endpoints
class TestCoverRequest(BaseModel):
    category_id: str
    book_id: str
    name: str  # Character name
    image_url: str  # Face image URL (ignored in test mode)

class TestInterleafRequest(BaseModel):
    category_id: str
    book_id: str
    interleaf_count: int  # Number of interleafs to create
    name: str  # Character name
    image_url: str  # Face image URL (ignored in test mode)

class TestContentRequest(BaseModel):
    category_id: str
    book_id: str
    stories: List[dict]  # List of story objects with story_id
    name: str  # Character name
    image_url: str  # Face image URL (ignored in test mode)

router = APIRouter()

@router.get("/pdf")
async def get_pdf():
    """Trả về URL của file PDF demo"""
    pdf_path = "test/test_response/PDF/demo_01.pdf"

    # Kiểm tra file có tồn tại không
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="PDF file not found")

    # Trả về URL để FE có thể truy cập
    return {
        "url": "/test/test_response/PDF/demo_01.pdf",
        "filename": "demo_01.pdf",
        "type": "application/pdf"
    }

@router.get("/images")
async def get_image_paths():
    """Trả về URL các file hình ảnh"""
    return {
        "style_1": {
            "url": "/images/career.png",
            "type": "image/png"
        },
        "style_2": {
            "url": "/images/detactive.png",
            "type": "image/png"
        },
        "style_3": {
            "url": "/images/happy.png",
            "type": "image/png"
        }
    }


@router.post("/test-cover/")
async def test_cover_endpoint(request: TestCoverRequest):
    """
    Tạo cover của cuốn sách PDF (phiên bản test - không swapface).

    Request body:
    - category_id: ID category (2 chữ số)
    - book_id: ID book (2 chữ số)
    - name: Tên nhân vật chính
    - image_url: URL ảnh face (bị bỏ qua trong test mode)

    Response: StreamingResponse với file PDF cover
    """
    start_time = time.time()

    try:
        # Tạo cover PDF sử dụng test function (không swapface)
        pdf_bytes = await create_cover_test(
            category_id=request.category_id,
            book_id=request.book_id,
            name=request.name,
            image_url=request.image_url  # Ignored in test mode
        )

        processing_time = time.time() - start_time

        # Return PDF as streaming response
        def generate_pdf():
            yield pdf_bytes

        response = StreamingResponse(
            generate_pdf(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=test_cover_{request.category_id}_{request.book_id}_{int(time.time())}.pdf",
                "X-Processing-Time": f"{processing_time:.2f}",
                "X-File-Size": str(len(pdf_bytes)),
                "X-Test-Mode": "true"
            }
        )

        return response

    except Exception as e:
        processing_time = time.time() - start_time
        raise HTTPException(
            status_code=500,
            detail=f"Test cover creation failed: {str(e)}"
        )


@router.post("/test-interleaf/")
async def test_interleaf_endpoint(request: TestInterleafRequest):
    """
    Tạo các trang interleaf của cuốn sách PDF (phiên bản test - không swapface).

    Request body:
    - category_id: ID category (2 chữ số)
    - book_id: ID book (2 chữ số)
    - interleaf_count: Số lượng interleaf cần tạo
    - name: Tên nhân vật chính
    - image_url: URL ảnh face (bị bỏ qua trong test mode)

    Response: StreamingResponse với file PDF interleaf pages
    """
    start_time = time.time()

    try:
        # Tạo interleaf PDF sử dụng test function (không swapface)
        pdf_bytes = await create_interleafs_test(
            category_id=request.category_id,
            book_id=request.book_id,
            interleaf_count=request.interleaf_count,
            name=request.name,
            image_url=request.image_url  # Ignored in test mode
        )

        processing_time = time.time() - start_time

        # Return PDF as streaming response
        def generate_pdf():
            yield pdf_bytes

        response = StreamingResponse(
            generate_pdf(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=test_interleaf_{request.category_id}_{request.book_id}_{int(time.time())}.pdf",
                "X-Processing-Time": f"{processing_time:.2f}",
                "X-Page-Count": str(request.interleaf_count * 2),  # 2 pages per interleaf
                "X-File-Size": str(len(pdf_bytes)),
                "X-Test-Mode": "true"
            }
        )

        return response

    except Exception as e:
        processing_time = time.time() - start_time
        raise HTTPException(
            status_code=500,
            detail=f"Test interleaf creation failed: {str(e)}"
        )


@router.post("/test-content/")
async def test_content_endpoint(request: TestContentRequest):
    """
    Tạo nội dung chính của cuốn sách PDF với nhiều trang từ các stories được chỉ định (phiên bản test - không swapface).

    Request body:
    - category_id: ID category
    - book_id: ID book
    - stories: Array của story objects với story_id
    - name: Tên nhân vật chính
    - image_url: URL ảnh face (bị bỏ qua trong test mode)

    Response: StreamingResponse với file PDF nội dung nhiều trang
    """
    start_time = time.time()

    try:
        # Load catalog metadata
        from pathlib import Path
        import yaml
        import json

        BASE_DIR = Path(__file__).resolve().parents[2]
        catalog_path = BASE_DIR / "assets" / "interiors" / "pages_metadata.yaml"

        with catalog_path.open("r", encoding="utf-8") as f:
            catalog_data = yaml.safe_load(f)

        # Collect all pages to process
        all_pages = []
        for story_req in request.stories:
            story_id = story_req["story_id"]
            # Find all pages for this story (assuming 2 pages per story)
            for page_id in ["01", "02"]:
                try:
                    page_key = f"{request.category_id}{request.book_id}{story_id}({page_id})"
                    all_pages.append(page_key)
                except Exception:
                    # Skip if page doesn't exist
                    continue

        if not all_pages:
            raise HTTPException(status_code=400, detail="No valid pages found for the specified stories")

        # Process all pages in parallel (TEST MODE - no face swap)
        async def process_page_test(page_key):
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

                # Replace {character_name} placeholder with actual name from request
                page_content = page_content.replace("{character_name}", request.name).replace("{Name}", request.name)

                # Get character path directly (no face swap in test mode)
                character_path = page_metadata["character"]
                character_full_path = BASE_DIR / character_path

                # Convert to base64 data URL format for PDF generation
                from src.ai.services.create_content import _convert_image_to_transparent_base64
                processed_image_data = _convert_image_to_transparent_base64(str(character_full_path))

                return page_content, processed_image_data

            except Exception as e:
                print(f"Error processing page {page_key}: {e}")
                return None, None

        # Process all pages in parallel
        import asyncio
        tasks = [process_page_test(page_key) for page_key in all_pages]
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

        # Create main content PDF with all pages using test function
        pdf_bytes = await create_main_content_test(
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
                "Content-Disposition": f"attachment; filename=test_content_{request.category_id}_{request.book_id}_{int(time.time())}.pdf",
                "X-Processing-Time": f"{processing_time:.2f}",
                "X-Page-Count": str(len(all_scripts)),
                "X-File-Size": str(len(pdf_bytes)),
                "X-Test-Mode": "true"
            }
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        raise HTTPException(
            status_code=500,
            detail=f"Test content creation failed: {str(e)}"
        )
