import time
import io
import asyncio
from pathlib import Path
from typing import List, Tuple
import yaml
from pypdf import PdfWriter, PdfReader
from .create_cover import create_cover
from .create_interleafs import create_interleafs
from .create_content import create_main_content
from .get_page_id import get_page_id


async def _process_story_pages(
    story_req: dict,
    category_id: str,
    book_id: str,
    name: str,
    image_url: str,
    catalog_data: dict,
    base_dir: Path
) -> Tuple[List[str], List[str], List[str]]:
    """
    Xử lý song song các trang trong một story.
    Returns: (scripts, image_urls, background_urls)
    """
    story_id = story_req["story_id"]
    tasks = []

    # Import required services
    from .swap_face import swap_face

    async def process_single_page(page_id: str):
        try:
            page_key = get_page_id(category_id, book_id, story_id, page_id)
            page_metadata = catalog_data["pages"].get(page_key)
            if not page_metadata:
                return None, None, None

            # Load story content
            story_file_path = base_dir / page_metadata["story_file"]
            with story_file_path.open("r", encoding="utf-8") as f:
                import json
                story_data = json.load(f)

            page_content = story_data.get("page_content")
            if not page_content:
                return None, None, None

            # Replace {character_name} placeholder with actual name from request
            page_content = page_content.replace("{character_name}", name).replace("{Name}", name)

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
                swapped_image_url = character_path

            # Skip remove_background to preserve original props (balloon, basket, etc.)
            processed_image_data = swapped_image_url

            # Collect background local path
            background_path = page_metadata["background"]
            background_full_path = base_dir / background_path
            background_url = str(background_full_path) if background_full_path.exists() else None

            return page_content, processed_image_data, background_url

        except Exception as e:
            print(f"Error processing page {page_id} for story {story_id}: {e}")
            return None, None, None

    # Tạo tasks cho 2 pages của story (01, 02)
    for page_id in ["01", "02"]:
        tasks.append(process_single_page(page_id))

    # Chạy song song 2 pages
    results = await asyncio.gather(*tasks, return_exceptions=True)

    scripts = []
    image_urls = []
    background_urls = []

    for result in results:
        if isinstance(result, Exception):
            print(f"Exception in page processing: {result}")
            continue
        if result and all(result):  # Check if all values are not None
            scripts.append(result[0])
            image_urls.append(result[1])
            background_urls.append(result[2])

    return scripts, image_urls, background_urls


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

    Logic mới:
    - 1 cover đầu tiên
    - Story 1 (2 trang)
    - Story 2 (2 trang)
    - Interleaf 1 (2 trang) ← xen vào sau mỗi 2 story
    - Story 3 (2 trang)
    - Story 4 (2 trang)
    - Interleaf 2 (2 trang) ← xen vào sau mỗi 2 story

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
    base_dir = Path("/app")

    print(f"Creating complete book for category {category_id}, book {book_id}")
    print(f"Stories count: {len(stories)}")

    # Tính số interleaf cần tạo (cứ 2 stories thì 1 interleaf)
    interleaf_count = len(stories) // 2
    print(f"Step 1: Will create {interleaf_count} interleaf(s) for {len(stories)} stories")

    # CHẠY SONG SONG: Tạo cover và chuẩn bị content data
    print("Step 2: Creating cover and preparing content (parallel)...")

    async def create_cover_task():
        try:
            return await create_cover(
                category_id=category_id,
                book_id=book_id,
                name=name,
                image_url=image_url
            )
        except Exception as e:
            raise Exception(f"Failed to create cover: {str(e)}")

    async def prepare_content_task():
        try:
            # Load catalog metadata
            catalog_path = Path("/app/assets/interiors/pages_metadata.yaml")
            with catalog_path.open("r", encoding="utf-8") as f:
                catalog_data = yaml.safe_load(f)

            # Xử lý song song tất cả stories
            print(f"  - Processing {len(stories)} stories in parallel...")
            story_tasks = [
                _process_story_pages(story_req, category_id, book_id, name, image_url, catalog_data, base_dir)
                for story_req in stories
            ]

            story_results = await asyncio.gather(*story_tasks, return_exceptions=True)

            # Collect tất cả data từ các stories
            all_scripts = []
            all_image_urls = []
            all_background_urls = []

            for i, result in enumerate(story_results):
                if isinstance(result, Exception):
                    print(f"Exception in story {stories[i]['story_id']}: {result}")
                    continue

                story_scripts, story_images, story_backgrounds = result
                all_scripts.extend(story_scripts)
                all_image_urls.extend(story_images)
                all_background_urls.extend(story_backgrounds)

            if not all_scripts or not all_image_urls:
                raise Exception("No valid pages processed")

            print(f"  - Collected {len(all_scripts)} pages from {len(stories)} stories")

            # Create main content PDF
            content_pdf = await create_main_content(
                image_urls=all_image_urls,
                scripts=all_scripts,
                background_urls=all_background_urls,
                font_path=font_path
            )

            return content_pdf, all_scripts

        except Exception as e:
            raise Exception(f"Failed to prepare content: {str(e)}")

    # Chạy song song cover và content preparation
    cover_task = create_cover_task()
    content_task = prepare_content_task()

    cover_pdf, (content_pdf, all_scripts) = await asyncio.gather(cover_task, content_task)

    print("✓ Cover and content preparation completed successfully")

    # Tạo interleafs nếu cần (chạy song song với merge nếu có thể)
    interleaf_pdfs = []
    if interleaf_count > 0:
        print(f"Step 3: Creating {interleaf_count} interleaf(s)...")
        try:
            # Create all interleafs
            all_interleafs_pdf = await create_interleafs(
                category_id=category_id,
                book_id=book_id,
                interleaf_count=interleaf_count,
                name=name,
                image_url=image_url
            )

            if all_interleafs_pdf:
                # Split interleaf PDF into individual interleaf PDFs (each 2 pages)
                interleaf_stream = io.BytesIO(all_interleafs_pdf)
                interleaf_reader = PdfReader(interleaf_stream)

                # Each interleaf has 2 pages
                for i in range(0, len(interleaf_reader.pages), 2):
                    writer = PdfWriter()
                    writer.add_page(interleaf_reader.pages[i])
                    if i + 1 < len(interleaf_reader.pages):
                        writer.add_page(interleaf_reader.pages[i + 1])

                    buffer = io.BytesIO()
                    writer.write(buffer)
                    buffer.seek(0)
                    interleaf_pdfs.append(buffer.getvalue())

            print("✓ Interleaf pages created successfully")
        except Exception as e:
            print(f"Warning: Failed to create interleafs: {str(e)}, continuing without interleafs")
            interleaf_pdfs = []

    # Merge tất cả PDFs theo thứ tự xen kẽ: cover + (content 4 pages + interleaf 2 pages) * n
    print("Step 4: Merging all PDFs in interleaved order...")
    try:
        writer = PdfWriter()

        # Add cover
        cover_stream = io.BytesIO(cover_pdf)
        cover_reader = PdfReader(cover_stream)
        for page in cover_reader.pages:
            writer.add_page(page)

        # Split content into chunks of 4 pages (2 stories = 4 pages each)
        content_stream = io.BytesIO(content_pdf)
        content_reader = PdfReader(content_stream)
        content_pages = content_reader.pages

        # Process content in chunks of 4 pages, interleaving with interleafs
        interleaf_index = 0
        for i in range(0, len(content_pages), 4):  # 4 pages per story group (2 stories × 2 pages)
            # Add 4 content pages (2 stories)
            for j in range(4):
                if i + j < len(content_pages):
                    writer.add_page(content_pages[i + j])

            # Add interleaf after every 2 stories (if available)
            if interleaf_index < len(interleaf_pdfs):
                interleaf_stream = io.BytesIO(interleaf_pdfs[interleaf_index])
                interleaf_reader = PdfReader(interleaf_stream)
                for page in interleaf_reader.pages:
                    writer.add_page(page)
                interleaf_index += 1

        # Create final merged PDF
        merged_buffer = io.BytesIO()
        writer.write(merged_buffer)

        merged_buffer.seek(0)
        final_pdf = merged_buffer.getvalue()

        processing_time = time.time() - start_time
        print(f"✓ Complete book created successfully in {processing_time:.2f} seconds")
        print(f"  - Cover: 1 page")
        print(f"  - Content: {len(content_pages)} pages")
        print(f"  - Interleafs: {len(interleaf_pdfs) * 2} pages")
        print(f"  - Total: {1 + len(content_pages) + (len(interleaf_pdfs) * 2)} pages")
        print(f"  - Parallel processing: Stories processed concurrently, pages within each story processed concurrently")

        return final_pdf

    except Exception as e:
        raise Exception(f"Failed to merge PDFs: {str(e)}")
