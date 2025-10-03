import time
import io
from pathlib import Path
from typing import List
import yaml
from pypdf import PdfWriter, PdfReader
from .create_cover import create_cover
from .create_interleafs import create_interleafs
from .create_content import create_main_content
from .get_page_id import get_page_id


async def create_book(
    category_id: str,
    book_id: str,
    stories: List[dict],
    name: str,
    image_url: str,
    font_path: str = None
) -> bytes:
    """
    Tạo toàn bộ cuốn sách PDF bao gồm cover, content và interleafs.

    Logic:
    - 1 cover đầu tiên
    - Nội dung chính (content) từ các stories
    - Cứ mỗi 2 stories thì có 1 interleaf (2 trang)

    Args:
        category_id: ID category (2 chữ số)
        book_id: ID book (2 chữ số)
        stories: Danh sách story objects với story_id
        name: Tên nhân vật để thay thế vào content
        image_url: URL ảnh face để swap vào characters
        font_path: (Tùy chọn) Đường dẫn tới font TTF hiện đại

    Returns:
        Dữ liệu PDF của toàn bộ cuốn sách dưới dạng bytes
    """
    start_time = time.time()

    print(f"Creating complete book for category {category_id}, book {book_id}")
    print(f"Stories count: {len(stories)}")

    # Tạo cover
    print("Step 1: Creating cover...")
    try:
        cover_pdf = await create_cover(
            category_id=category_id,
            book_id=book_id,
            name=name,
            image_url=image_url
        )
        print("✓ Cover created successfully")
    except Exception as e:
        raise Exception(f"Failed to create cover: {str(e)}")

    # Tính số interleaf cần tạo (cứ 2 stories thì 1 interleaf)
    interleaf_count = len(stories) // 2
    print(f"Step 2: Will create {interleaf_count} interleaf(s) for {len(stories)} stories")

    # Tạo content PDF (tương tự logic từ create-content endpoint)
    print("Step 3: Creating content pages...")
    try:
        # Load catalog metadata
        import os
        catalog_path = Path("/app/assets/interiors/pages_metadata.yaml")

        with catalog_path.open("r", encoding="utf-8") as f:
            catalog_data = yaml.safe_load(f)

        # Collect all pages to process
        all_pages = []
        for story_req in stories:
            story_id = story_req["story_id"]
            # Find all pages for this story (assuming 2 pages per story)
            for page_id in ["01", "02"]:
                try:
                    page_key = get_page_id(category_id, book_id, story_id, page_id)
                    all_pages.append(page_key)
                except Exception:
                    # Skip if page doesn't exist
                    continue

        if not all_pages:
            raise Exception("No valid pages found for the specified stories")

        # Process pages similar to create-content endpoint
        all_scripts = []
        all_image_urls = []

        # Import required services
        from .swap_face import swap_face
        from .remove_background import remove_background

        for page_key in all_pages:
            try:
                page_metadata = catalog_data["pages"].get(page_key)
                if not page_metadata:
                    continue

                # Load story content
                story_file_path = base_dir / page_metadata["story_file"]
                with story_file_path.open("r", encoding="utf-8") as f:
                    import json
                    story_data = json.load(f)

                page_content = story_data.get("page_content")
                if not page_content:
                    continue

                # Get character
                character_path = page_metadata["character"]

                # Face swap
                face_swap_result = await swap_face(
                    face_image_url=image_url,
                    body_image_url=character_path
                )

                if face_swap_result["success"]:
                    swapped_image_url = face_swap_result["swapped_image_url"]
                else:
                    swapped_image_url = f"http://localhost:8000/{character_path}"

                # Remove background
                try:
                    processed_image_data = await remove_background(image_url=swapped_image_url)
                except:
                    processed_image_data = swapped_image_url

                all_scripts.append(page_content)
                all_image_urls.append(processed_image_data)

            except Exception as e:
                print(f"Error processing page {page_key}: {e}")
                continue

        if not all_scripts or not all_image_urls:
            raise Exception("No valid pages processed")

        # Collect background local paths
        background_urls = []
        for page_key in all_pages:
            page_metadata = catalog_data["pages"].get(page_key)
            if page_metadata:
                background_path = page_metadata["background"]
                background_full_path = base_dir / background_path
                if background_full_path.exists():
                    background_urls.append(str(background_full_path))
                else:
                    background_urls.append(None)
            else:
                background_urls.append(None)

        # Create main content PDF
        content_pdf = await create_main_content(
            image_urls=all_image_urls,
            scripts=all_scripts,
            background_urls=background_urls,
            font_path=font_path
        )
        print("✓ Content pages created successfully")

    except Exception as e:
        raise Exception(f"Failed to create content: {str(e)}")

    # Tạo interleafs nếu cần
    interleaf_pdf = None
    if interleaf_count > 0:
        print(f"Step 4: Creating {interleaf_count} interleaf(s)...")
        try:
            interleaf_pdf = await create_interleafs(
                category_id=category_id,
                book_id=book_id,
                interleaf_count=interleaf_count,
                name=name,
                image_url=image_url
            )
            print("✓ Interleaf pages created successfully")
        except Exception as e:
            print(f"Warning: Failed to create interleafs: {str(e)}, continuing without interleafs")
            interleaf_pdf = None

    # Merge tất cả PDFs theo thứ tự: cover + content + interleafs
    print("Step 5: Merging all PDFs...")
    try:
        writer = PdfWriter()

        # Add cover
        cover_stream = io.BytesIO(cover_pdf)
        cover_reader = PdfReader(cover_stream)
        for page in cover_reader.pages:
            writer.add_page(page)

        # Add content
        content_stream = io.BytesIO(content_pdf)
        content_reader = PdfReader(content_stream)
        for page in content_reader.pages:
            writer.add_page(page)

        # Add interleafs if available
        if interleaf_pdf:
            interleaf_stream = io.BytesIO(interleaf_pdf)
            interleaf_reader = PdfReader(interleaf_stream)
            for page in interleaf_reader.pages:
                writer.add_page(page)

        # Create final merged PDF
        merged_buffer = io.BytesIO()
        writer.write(merged_buffer)

        merged_buffer.seek(0)
        final_pdf = merged_buffer.getvalue()

        processing_time = time.time() - start_time
        print(f"✓ Complete book created successfully in {processing_time:.2f} seconds")
        print(f"  - Cover: 1 page")
        print(f"  - Content: {len(all_scripts)} pages")
        print(f"  - Interleafs: {interleaf_count * 2 if interleaf_pdf else 0} pages")
        print(f"  - Total: {1 + len(all_scripts) + (interleaf_count * 2 if interleaf_pdf else 0)} pages")

        return final_pdf

    except Exception as e:
        raise Exception(f"Failed to merge PDFs: {str(e)}")
