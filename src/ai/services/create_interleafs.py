import os
import io
import base64
import json
import time
from pathlib import Path
from typing import List, Optional, Dict, Any

import requests
from PIL import Image
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph, Frame
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from .swap_face import swap_face


def _find_usable_font_path(preferred_path: Optional[str] = None) -> Optional[str]:
    """
    Try to find a modern/kids-style TTF font to render text.
    Prefers Comic Neue, Patrick Hand, or other fun fonts for children's books.
    Falls back to system fonts that support Unicode.
    """
    candidate_paths = [
        preferred_path,
        # Kids/fun fonts
        "/usr/share/fonts/truetype/comic-neue/ComicNeue-Regular.ttf",
        "/usr/share/fonts/comic-neue/ComicNeue-Regular.ttf",
        "/usr/share/fonts/truetype/patrick-hand/PatrickHand-Regular.ttf",
        "/usr/share/fonts/patrick-hand/PatrickHand-Regular.ttf",
        "/Library/Fonts/ComicNeue-Regular.ttf",
        "/System/Library/Fonts/ComicNeue-Regular.ttf",
        "/Library/Fonts/PatrickHand-Regular.ttf",
        "/System/Library/Fonts/PatrickHand-Regular.ttf",
        # Modern system fonts
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/Library/Fonts/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for path in candidate_paths:
        if path and os.path.isfile(path):
            return path
    return None


def _register_unicode_font(font_path: Optional[str] = None) -> str:
    """
    Register a TTF font (if available) to support Unicode text. Returns font name to use.
    Falls back to Helvetica if no TTF is available (may not render Vietnamese correctly).
    """
    resolved_path = _find_usable_font_path(font_path)
    if resolved_path:
        font_name = "EmbeddedUnicode"
        if font_name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(font_name, resolved_path))
        return font_name
    return "Helvetica"


def _download_image_as_pil(source: str) -> Image.Image:
    if source.startswith("data:image/"):
        try:
            _, base64_data = source.split(",", 1)
            image_bytes = base64.b64decode(base64_data)
            return Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            raise ValueError(f"Failed to decode base64 image data: {e}")

    possible_paths = [Path(source), Path("/app") / source]
    for path in possible_paths:
        if path.exists():
            return Image.open(path)

    response = requests.get(source, timeout=30)
    response.raise_for_status()
    img = Image.open(io.BytesIO(response.content))

    if img.mode == "P":
        if "transparency" in img.info:
            img = img.convert("RGBA")
        else:
            img = img.convert("RGB")
    elif img.mode == "LA":
        img = img.convert("RGBA")
    elif img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")
    return img


def _image_to_base64_png(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode('utf-8')}"


def _convert_image_to_transparent_base64(source: str) -> str:
    image = _download_image_as_pil(source)
    if image.mode != "RGBA":
        image = image.convert("RGBA")

    cleaned_pixels = []
    for pixel in image.getdata():
        if isinstance(pixel, int):
            pixel = (pixel, pixel, pixel, 255)
        elif len(pixel) == 3:
            pixel = (*pixel, 255)

        r, g, b, a = pixel
        if a > 0 and r < 10 and g < 10 and b < 10:
            cleaned_pixels.append((r, g, b, 0))
        else:
            cleaned_pixels.append((r, g, b, a))

    image.putdata(cleaned_pixels)
    return _image_to_base64_png(image)


def _analyze_background_brightness(bg_img: Image.Image, text_region_ratio: float = 0.3) -> float:
    """
    Analyze background brightness in the text region to determine appropriate text color.
    Returns average brightness (0-1), where > 0.5 is bright, < 0.5 is dark.
    """
    width, height = bg_img.size

    # Define text region (right half of the page where text will be placed)
    text_region_width = int(width * text_region_ratio)
    text_region_x = width - text_region_width  # Right side of page

    # Crop to text region
    text_region = bg_img.crop((text_region_x, 0, width, height))

    # Convert to grayscale and calculate average brightness
    gray_region = text_region.convert("L")
    histogram = gray_region.histogram()

    # Calculate weighted average brightness
    total_pixels = sum(histogram)
    if total_pixels == 0:
        return 0.5  # Default to middle brightness

    brightness_sum = sum(i * count for i, count in enumerate(histogram))
    average_brightness = brightness_sum / (total_pixels * 255.0)  # Normalize to 0-1

    return average_brightness


def _draw_background(c: canvas.Canvas, bg_path: str, page_width: float, page_height: float):
    """Draw background image on the canvas."""
    try:
        bg_img = Image.open(bg_path)
        # Resize to fit page while maintaining aspect ratio
        bg_img.thumbnail((page_width, page_height), Image.Resampling.LANCZOS)

        # Center the background
        bg_width, bg_height = bg_img.size
        x = (page_width - bg_width) / 2
        y = (page_height - bg_height) / 2

        c.drawImage(ImageReader(bg_img), x, y, width=bg_width, height=bg_height, mask='auto')
    except Exception as e:
        print(f"Warning: Could not load background {bg_path}: {e}")


def _draw_image_left_half(c: canvas.Canvas, pil_img: Image.Image, page_width: float, page_height: float, margin: float, gutter: float):
    """Draw character image on the left half of the page."""
    left_half_width = (page_width - gutter) / 2 - margin
    img_max_width = left_half_width
    img_max_height = page_height - 2 * margin

    # Resize image to fit left half while maintaining aspect ratio
    img_ratio = pil_img.width / pil_img.height
    if img_ratio > img_max_width / img_max_height:
        # Image is wider relative to available space
        new_width = img_max_width
        new_height = img_max_width / img_ratio
    else:
        # Image is taller relative to available space
        new_height = img_max_height
        new_width = img_max_height * img_ratio

    # Center in left half
    x = margin + (left_half_width - new_width) / 2
    y = margin + (img_max_height - new_height) / 2

    if pil_img.mode == "RGBA":
        buffer = io.BytesIO()
        pil_img.save(buffer, format="PNG")
        buffer.seek(0)
        image_reader = ImageReader(buffer)
    else:
        image_reader = ImageReader(pil_img)

    c.drawImage(image_reader, x, y, width=new_width, height=new_height, mask='auto')


def _draw_text_right_half(c: canvas.Canvas, text: str, font_name: str, page_width: float, page_height: float, margin: float, gutter: float, bg_path: Optional[str] = None):
    """Draw text on the right half of the page with automatic color based on background."""
    # Analyze background brightness for text color
    if bg_path:
        try:
            bg_img = Image.open(bg_path)
            brightness = _analyze_background_brightness(bg_img)
            text_color = "black" if brightness > 0.5 else "white"
        except Exception:
            text_color = "black"
    else:
        text_color = "black"

    # Set text color
    if text_color == "white":
        c.setFillColorRGB(1, 1, 1)  # White
    else:
        c.setFillColorRGB(0, 0, 0)  # Black

    # Calculate right half dimensions
    left_half_width = (page_width - gutter) / 2
    right_half_x = left_half_width + gutter
    right_half_width = page_width - right_half_x - margin

    # Create text frame for right half
    text_frame_width = right_half_width
    text_frame_height = page_height - 2 * margin
    text_frame_x = right_half_x
    text_frame_y = margin

    # Create paragraph style for story text
    styles = getSampleStyleSheet()
    story_style = ParagraphStyle(
        'StoryStyle',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=24,  # Larger font for interleaf
        leading=28,   # Line spacing
        spaceAfter=12,
        alignment=0,  # Left align
        textColor=text_color,
    )

    # Create frame and paragraph
    frame = Frame(text_frame_x, text_frame_y, text_frame_width, text_frame_height, showBoundary=0)
    paragraph = Paragraph(text, story_style)
    frame.addFromList([paragraph], c)


async def create_interleafs(
    category_id: str,
    book_id: str,
    interleaf_count: int,
    name: str,
    image_url: str,
    font_path: Optional[str] = None
) -> bytes:
    """
    Tạo các trang interleaf dưới dạng PDF bytes.
    Mỗi interleaf có 2 trang.

    Args:
        category_id: ID category (2 chữ số)
        book_id: ID book (2 chữ số)
        interleaf_count: Số lượng interleaf cần tạo
        name: Tên nhân vật để thay thế vào quotes
        image_url: URL ảnh face để swap vào characters
        font_path: (Tùy chọn) Đường dẫn tới font TTF hiện đại

    Returns:
        Dữ liệu PDF của tất cả interleaf pages dưới dạng bytes
    """
    start_time = time.time()

    print(f"Creating {interleaf_count} interleaf(s) for category {category_id}, book {book_id}")

    # Load interleaf metadata
    interleaf_metadata_path = Path("/app/assets/interleafs/interleaf_metadata.yaml")

    # Nếu chưa có metadata, tạo mặc định
    if not interleaf_metadata_path.exists():
        print(f"Warning: Interleaf metadata not found at {interleaf_metadata_path}, using default paths")
        # Sẽ xử lý trong vòng lặp dưới đây
        has_metadata = False
    else:
        import yaml
        with interleaf_metadata_path.open("r", encoding="utf-8") as f:
            interleaf_data = yaml.safe_load(f)
        has_metadata = True

    # Collect all interleaf pages to process
    all_interleaf_pages = []

    for interleaf_idx in range(1, interleaf_count + 1):
        interleaf_order = f"{interleaf_idx:02d}"

        for page_num in ["01", "02"]:
            # New format: XXYY(AA) where XX=category_id, YY=interleaf_order, AA=page_num
            interleaf_id = f"{category_id}{interleaf_order}({page_num})"

            if has_metadata:
                page_metadata = interleaf_data.get("pages", {}).get(interleaf_id)
                if not page_metadata:
                    print(f"Warning: Interleaf metadata not found for ID: {interleaf_id}, skipping")
                    continue

                background_path = Path(f"/app/{page_metadata['background']}")
                character_path = page_metadata['character']  # Use relative path like create_content
                quote_file_path = Path(f"/app/{page_metadata['quote_file']}")
            else:
                # Default paths - use new format
                background_path = Path(f"/app/assets/interleafs/backgrounds/background_{interleaf_id}.png")
                character_path = f"assets/interleafs/characters/character_{interleaf_id}.png"  # Use relative path
                quote_file_path = Path(f"/app/assets/interleafs/quotes/quote_{interleaf_id}.json")

            # Validate file paths
            if not background_path.exists():
                print(f"Warning: Background file not found: {background_path}, skipping page {interleaf_id}")
                continue
            character_full_path = Path(f"/app/{character_path}")
            if not character_full_path.exists():
                print(f"Warning: Character file not found: {character_full_path}, skipping page {interleaf_id}")
                continue
            if not quote_file_path.exists():
                print(f"Warning: Quote file not found: {quote_file_path}, skipping page {interleaf_id}")
                continue

            # Load quote content
            try:
                with quote_file_path.open("r", encoding="utf-8") as f:
                    quote_data = json.load(f)

                quote_content = quote_data.get("quote", "")
                if not quote_content:
                    print(f"Warning: Empty quote content for {interleaf_id}, skipping")
                    continue

                # Replace placeholders
                quote_content = quote_content.replace("{character_name}", name).replace("{character_name}", name)

                all_interleaf_pages.append({
                    "interleaf_id": interleaf_id,
                    "background_path": background_path,
                    "character_path": character_path,
                    "quote_content": quote_content
                })

            except Exception as e:
                print(f"Error loading quote for {interleaf_id}: {e}, skipping")
                continue

    if not all_interleaf_pages:
        raise ValueError("No valid interleaf pages found")

    print(f"Processing {len(all_interleaf_pages)} interleaf pages")

    # Process all pages
    processed_pages = []

    for page_data in all_interleaf_pages:
        interleaf_id = page_data["interleaf_id"]
        background_path = page_data["background_path"]
        character_path = page_data["character_path"]
        quote_content = page_data["quote_content"]

        print(f"Processing interleaf page: {interleaf_id}")

        # Face swap character
        face_swap_result = await swap_face(
            face_image_url=image_url,
            body_image_url=str(character_path)
        )

        if face_swap_result["success"]:
            swapped_character_url = face_swap_result["swapped_image_url"]
        else:
            print(f"Face swap failed for {interleaf_id}: {face_swap_result.get('error', 'Unknown error')}")
            swapped_character_url = str(character_path)

        character_image_url = _convert_image_to_transparent_base64(swapped_character_url)

        processed_pages.append({
            "background_path": background_path,
            "character_image_url": character_image_url,
            "quote_content": quote_content
        })

    # Chuẩn bị font hiện đại
    font_name = _register_unicode_font(font_path)

    # Thiết lập trang nằm ngang A4
    page_width, page_height = landscape(A4)
    margin = 36  # 0.5 inch
    gutter = 16  # khoảng cách giữa 2 nửa trang

    # Tạo PDF trong memory
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(page_width, page_height))

    for idx, page_data in enumerate(processed_pages, start=1):
        background_path = page_data["background_path"]
        character_image_url = page_data["character_image_url"]
        quote_content = page_data["quote_content"]

        # Background
        _draw_background(c, str(background_path), page_width, page_height)

        # Character bên trái
        try:
            pil_character = _download_image_as_pil(character_image_url)
            _draw_image_left_half(c, pil_character, page_width, page_height, margin, gutter)
        except Exception as e:
            print(f"Warning: Could not draw character for page {idx}: {e}")

        # Quote bên phải
        _draw_text_right_half(c, quote_content, font_name, page_width, page_height, margin, gutter, str(background_path))

        # Page number
        c.setFont(font_name if font_name != "Helvetica" else "Helvetica", 10)
        c.setFillGray(0.3)
        c.drawRightString(page_width - margin, margin / 2, f"Interleaf {idx}")
        c.setFillGray(0)

        c.showPage()

    c.save()
    buffer.seek(0)

    processing_time = time.time() - start_time
    print(f"Interleaf creation completed in {processing_time:.2f} seconds")

    return buffer.getvalue()
