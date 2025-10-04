import os
import io
import base64
import json
import time
from pathlib import Path
from typing import Optional, Dict, Any

import requests
from PIL import Image
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph, Frame
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# from .swap_face import swap_face  # Import moved inside functions that need it


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
    # Handle base64 data URL
    if source.startswith("data:image/"):
        try:
            _, base64_data = source.split(",", 1)
            image_bytes = base64.b64decode(base64_data)
            return Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            raise ValueError(f"Failed to decode base64 image data: {e}")

    # Try local filesystem paths first
    possible_paths = [Path(source), Path("/app") / source]
    for path in possible_paths:
        if path.exists():
            return Image.open(path)

    # Fallback to HTTP(S) URL
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


def _draw_title_center(c: canvas.Canvas, title: str, font_name: str, page_width: float, page_height: float, bg_path: Optional[str] = None):
    """Draw title text in the center of the page."""
    # Analyze background brightness for text color
    if bg_path:
        try:
            bg_img = Image.open(bg_path)
            brightness = _analyze_background_brightness(bg_img, text_region_ratio=0.5)  # Check center region
            text_color = "black" if brightness > 0.5 else "white"
        except Exception:
            text_color = "black"
    else:
        text_color = "black"

    # Set font and size for title (larger and bolder)
    title_font_size = 48
    c.setFont(font_name if font_name != "Helvetica" else "Helvetica-Bold", title_font_size)

    # Set text color
    if text_color == "white":
        c.setFillColorRGB(1, 1, 1)  # White
    else:
        c.setFillColorRGB(0, 0, 0)  # Black

    # Center the title
    title_width = c.stringWidth(title, font_name if font_name != "Helvetica" else "Helvetica-Bold", title_font_size)
    x = (page_width - title_width) / 2
    y = page_height / 2 - title_font_size / 2  # Center vertically

    c.drawString(x, y, title)


async def create_cover(
    category_id: str,
    book_id: str,
    name: str,
    image_url: str,
    font_path: Optional[str] = None
) -> bytes:
    """
    Tạo cover của cuốn sách dưới dạng PDF bytes.

    Args:
        category_id: ID category (2 chữ số)
        book_id: ID book (2 chữ số)
        name: Tên nhân vật để thay thế vào title
        image_url: URL ảnh face để swap vào character
        font_path: (Tùy chọn) Đường dẫn tới font TTF hiện đại

    Returns:
        Dữ liệu PDF của cover dưới dạng bytes
    """
    start_time = time.time()

    # Tạo cover ID (4 chữ số: category + book)
    cover_id = f"{category_id}{book_id}"

    print(f"Creating cover for ID: {cover_id}")

    # Load cover metadata
    covers_metadata_path = Path("/app/assets/covers/covers_metadata.yaml")

    # Nếu chưa có metadata, tạo mặc định
    if not covers_metadata_path.exists():
        print(f"Warning: Cover metadata not found at {covers_metadata_path}, using default paths")

        # Default paths for cover assets
        background_path = Path(f"/app/assets/covers/backgrounds/background_{cover_id}.png")
        character_path = Path(f"/app/assets/covers/characters/character_{cover_id}.png")
        title_file_path = Path(f"/app/assets/covers/titles/title_{cover_id}.json")
    else:
        # Load from metadata (nếu có)
        import yaml
        with covers_metadata_path.open("r", encoding="utf-8") as f:
            covers_data = yaml.safe_load(f)

        cover_metadata = covers_data.get("covers", {}).get(cover_id)
        if not cover_metadata:
            raise ValueError(f"Cover metadata not found for ID: {cover_id}")

        background_path = Path(f"/app/{cover_metadata['background']}")
        character_path = cover_metadata['character']  # Use relative path like create_content
        title_file_path = Path(f"/app/{cover_metadata['title_file']}")

    # Validate file paths
    if not background_path.exists():
        raise FileNotFoundError(f"Background file not found: {background_path}")
    character_full_path = Path(f"/app/{character_path}")
    if not character_full_path.exists():
        raise FileNotFoundError(f"Character file not found: {character_full_path}")
    if not title_file_path.exists():
        raise FileNotFoundError(f"Title file not found: {title_file_path}")

    # Load title content
    with title_file_path.open("r", encoding="utf-8") as f:
        title_data = json.load(f)

    title_template = title_data.get("title", "Book Title")
    # Replace {character_name} placeholder with actual name
    title = title_template.replace("{character_name}", name).replace("{character_name}", name)

    print(f"Loaded title: {title}")

    # Face swap character (sử dụng file path trực tiếp như create_content)
    print("Performing face swap...")
    from .swap_face import swap_face
    face_swap_result = await swap_face(
        face_image_url=image_url,
        body_image_url=str(character_path)  # Sử dụng file path trực tiếp
    )

    if face_swap_result["success"]:
        swapped_character_url = face_swap_result["swapped_image_url"]
        print("Face swap successful")
    else:
        print(f"Face swap failed: {face_swap_result.get('error', 'Unknown error')}")
        swapped_character_url = str(character_path)

    character_image_url = _convert_image_to_transparent_base64(swapped_character_url)

    # Chuẩn bị font hiện đại
    font_name = _register_unicode_font(font_path)

    # Thiết lập trang nằm ngang A4
    page_width, page_height = landscape(A4)
    margin = 36  # 0.5 inch

    # Tạo PDF trong memory
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(page_width, page_height))

    # Draw background
    _draw_background(c, str(background_path), page_width, page_height)

    # Draw character (centered)
    try:
        pil_character = _download_image_as_pil(character_image_url)
        # For cover, place character in center-left area
        char_max_width = page_width * 0.4  # 40% of page width
        char_max_height = page_height - 2 * margin

        # Resize character
        char_ratio = pil_character.width / pil_character.height
        if char_ratio > char_max_width / char_max_height:
            new_width = char_max_width
            new_height = char_max_width / char_ratio
        else:
            new_height = char_max_height
            new_width = char_max_height * char_ratio

        # Position character on left side
        x = margin + (page_width * 0.4 - new_width) / 2
        y = margin + (char_max_height - new_height) / 2

        c.drawImage(ImageReader(pil_character), x, y, width=new_width, height=new_height, mask='auto')
    except Exception as e:
        print(f"Warning: Could not draw character: {e}")

    # Draw title (centered on right side)
    title_font_size = 48
    c.setFont(font_name if font_name != "Helvetica" else "Helvetica-Bold", title_font_size)

    # Simple title positioning - center right area
    title_x = page_width * 0.6  # Start at 60% of page width
    title_y = page_height / 2 - title_font_size / 2

    # Word wrap title if too long
    max_title_width = page_width * 0.35  # 35% of page width for title
    title_lines = []
    current_line = ""
    words = title.split()

    for word in words:
        test_line = current_line + " " + word if current_line else word
        if c.stringWidth(test_line, font_name if font_name != "Helvetica" else "Helvetica-Bold", title_font_size) > max_title_width:
            if current_line:
                title_lines.append(current_line)
            current_line = word
        else:
            current_line = test_line

    if current_line:
        title_lines.append(current_line)

    # Draw title lines
    line_height = title_font_size * 1.2
    start_y = page_height / 2 + (len(title_lines) - 1) * line_height / 2

    for i, line in enumerate(title_lines):
        line_width = c.stringWidth(line, font_name if font_name != "Helvetica" else "Helvetica-Bold", title_font_size)
        x = title_x + (max_title_width - line_width) / 2  # Center within title area
        y = start_y - i * line_height
        c.drawString(x, y, line)

    c.save()
    buffer.seek(0)

    processing_time = time.time() - start_time
    print(f"Cover creation completed in {processing_time:.2f} seconds")

    return buffer.getvalue()


async def create_cover_test(
    category_id: str,
    book_id: str,
    name: str,
    image_url: str,
    font_path: Optional[str] = None
) -> bytes:
    """
    Tạo cover của cuốn sách dưới dạng PDF bytes (phiên bản test - không swapface).

    Args:
        category_id: ID category (2 chữ số)
        book_id: ID book (2 chữ số)
        name: Tên nhân vật để thay thế vào title
        image_url: URL ảnh face (bị bỏ qua trong phiên bản test)
        font_path: (Tùy chọn) Đường dẫn tới font TTF hiện đại

    Returns:
        Dữ liệu PDF của cover dưới dạng bytes
    """
    start_time = time.time()

    # Tạo cover ID (4 chữ số: category + book)
    cover_id = f"{category_id}{book_id}"

    print(f"Creating cover (TEST MODE - no swapface) for ID: {cover_id}")

    # Load cover metadata
    covers_metadata_path = Path("/app/assets/covers/covers_metadata.yaml")

    # Nếu chưa có metadata, tạo mặc định
    if not covers_metadata_path.exists():
        print(f"Warning: Cover metadata not found at {covers_metadata_path}, using default paths")

        # Default paths for cover assets
        background_path = Path(f"/app/assets/covers/backgrounds/background_{cover_id}.png")
        character_path = Path(f"/app/assets/covers/characters/character_{cover_id}.png")
        title_file_path = Path(f"/app/assets/covers/titles/title_{cover_id}.json")
    else:
        # Load from metadata (nếu có)
        import yaml
        with covers_metadata_path.open("r", encoding="utf-8") as f:
            covers_data = yaml.safe_load(f)

        cover_metadata = covers_data.get("covers", {}).get(cover_id)
        if not cover_metadata:
            raise ValueError(f"Cover metadata not found for ID: {cover_id}")

        background_path = Path(f"/app/{cover_metadata['background']}")
        character_path = cover_metadata['character']  # Use relative path like create_content
        title_file_path = Path(f"/app/{cover_metadata['title_file']}")

    # Validate file paths
    if not background_path.exists():
        raise FileNotFoundError(f"Background file not found: {background_path}")
    character_full_path = Path(f"/app/{character_path}")
    if not character_full_path.exists():
        raise FileNotFoundError(f"Character file not found: {character_full_path}")
    if not title_file_path.exists():
        raise FileNotFoundError(f"Title file not found: {title_file_path}")

    # Load title content
    with title_file_path.open("r", encoding="utf-8") as f:
        title_data = json.load(f)

    title_template = title_data.get("title", "Book Title")
    # Replace {character_name} placeholder with actual name
    title = title_template.replace("{character_name}", name).replace("{Name}", name)

    print(f"Loaded title: {title}")

    # SKIP FACE SWAP - use original character image directly
    print("TEST MODE: Skipping face swap, using original character image")
    character_image_url = _convert_image_to_transparent_base64(str(character_path))

    # Chuẩn bị font hiện đại
    font_name = _register_unicode_font(font_path)

    # Thiết lập trang nằm ngang A4
    page_width, page_height = landscape(A4)
    margin = 36  # 0.5 inch

    # Tạo PDF trong memory
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(page_width, page_height))

    # Draw background
    _draw_background(c, str(background_path), page_width, page_height)

    # Draw character (centered)
    try:
        pil_character = _download_image_as_pil(character_image_url)
        # For cover, place character in center-left area
        char_max_width = page_width * 0.4  # 40% of page width
        char_max_height = page_height - 2 * margin

        # Resize character
        char_ratio = pil_character.width / pil_character.height
        if char_ratio > char_max_width / char_max_height:
            new_width = char_max_width
            new_height = char_max_width / char_ratio
        else:
            new_height = char_max_height
            new_width = char_max_height * char_ratio

        # Position character on left side
        x = margin + (page_width * 0.4 - new_width) / 2
        y = margin + (char_max_height - new_height) / 2

        c.drawImage(ImageReader(pil_character), x, y, width=new_width, height=new_height, mask='auto')
    except Exception as e:
        print(f"Warning: Could not draw character: {e}")

    # Draw title (centered on right side)
    title_font_size = 48
    c.setFont(font_name if font_name != "Helvetica" else "Helvetica-Bold", title_font_size)

    # Simple title positioning - center right area
    title_x = page_width * 0.6  # Start at 60% of page width
    title_y = page_height / 2 - title_font_size / 2

    # Word wrap title if too long
    max_title_width = page_width * 0.35  # 35% of page width for title
    title_lines = []
    current_line = ""
    words = title.split()

    for word in words:
        test_line = current_line + " " + word if current_line else word
        if c.stringWidth(test_line, font_name if font_name != "Helvetica" else "Helvetica-Bold", title_font_size) > max_title_width:
            if current_line:
                title_lines.append(current_line)
            current_line = word
        else:
            current_line = test_line

    if current_line:
        title_lines.append(current_line)

    # Draw title lines
    line_height = title_font_size * 1.2
    start_y = page_height / 2 + (len(title_lines) - 1) * line_height / 2

    for i, line in enumerate(title_lines):
        line_width = c.stringWidth(line, font_name if font_name != "Helvetica" else "Helvetica-Bold", title_font_size)
        x = title_x + (max_title_width - line_width) / 2  # Center within title area
        y = start_y - i * line_height
        c.drawString(x, y, line)

    c.save()
    buffer.seek(0)

    processing_time = time.time() - start_time
    print(f"Cover creation (TEST MODE) completed in {processing_time:.2f} seconds")

    return buffer.getvalue()
