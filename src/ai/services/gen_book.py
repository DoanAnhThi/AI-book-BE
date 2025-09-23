import os
import io
import base64
from typing import List, Optional

import requests
from PIL import Image
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph, Frame
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from .remove_background import remove_background




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


def _register_unicode_font(font_path: Optional[str]) -> str:
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


def _download_image_as_pil(url: str) -> Image.Image:
    # Check if it's a base64 data URL
    if url.startswith("data:image/"):
        # Extract base64 data from data URL
        # Format: data:image/png;base64,{base64_data}
        try:
            header, base64_data = url.split(",", 1)
            image_bytes = base64.b64decode(base64_data)
            image_stream = io.BytesIO(image_bytes)
            img = Image.open(image_stream)
        except Exception as e:
            raise ValueError(f"Failed to decode base64 image data: {e}")
    else:
        # Regular URL - download from web
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        image_stream = io.BytesIO(response.content)
        img = Image.open(image_stream)

    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")
    return img


def _analyze_background_brightness(bg_img: Image.Image, text_region_ratio: float = 0.3) -> float:
    """
    Analyze background brightness in the text region to determine appropriate text color.
    Returns average brightness (0-1), where > 0.5 is bright, < 0.5 is dark.
    """
    width, height = bg_img.size

    # Define text region (right half of the page where text will be placed)
    text_region_x = int(width * 0.5)  # Start from middle
    text_region_y = int(height * 0.1)  # Skip top margin
    text_region_width = int(width * 0.4)  # Text takes about 40% of width
    text_region_height = int(height * 0.8)  # Text takes about 80% of height

    # Crop to text region
    text_region = bg_img.crop((
        text_region_x,
        text_region_y,
        min(text_region_x + text_region_width, width),
        min(text_region_y + text_region_height, height)
    ))

    # Sample pixels (take every 10th pixel for performance)
    pixels = []
    for y in range(0, text_region.height, 10):
        for x in range(0, text_region.width, 10):
            pixels.append(text_region.getpixel((x, y)))

    if not pixels:
        return 0.5  # Default to medium brightness

    # Calculate average luminance using standard formula
    total_luminance = 0
    for r, g, b in pixels:
        # Standard luminance formula: 0.299*R + 0.587*G + 0.114*B
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
        total_luminance += luminance

    average_luminance = total_luminance / len(pixels)
    return average_luminance


def _get_optimal_text_colors(brightness: float) -> tuple:
    """
    Return optimal text and shadow colors based on background brightness.
    Returns (text_color_rgb, shadow_color_rgb) where each is (r, g, b) tuple with values 0-1.
    """
    if brightness > 0.5:
        # Bright background -> Dark text
        text_color = (0, 0, 0)  # Black text
        shadow_color = (0.3, 0.3, 0.3)  # Dark gray shadow
    else:
        # Dark background -> Light text
        text_color = (1, 1, 1)  # White text
        shadow_color = (0.7, 0.7, 0.7)  # Light gray shadow

    return text_color, shadow_color


def get_background_urls(num_pages: int) -> List[str]:
    """
    Load background images from assets/backgrounds/topic_01 and return file paths.
    Cycles through available backgrounds if there are more pages than backgrounds.

    Args:
        num_pages: Number of pages needed

    Returns:
        List of file paths for backgrounds
    """
    # Get the project root directory (parent of models directory)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    background_dir = os.path.join(project_root, "assets", "backgrounds", "topic_01")

    print(f"DEBUG: Current dir: {current_dir}")
    print(f"DEBUG: Project root: {project_root}")
    print(f"DEBUG: Background dir: {background_dir}")
    print(f"DEBUG: Background dir exists: {os.path.exists(background_dir)}")

    if not os.path.exists(background_dir):
        print(f"Warning: Background directory {background_dir} does not exist")
        return []

    # Get all image files
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp')
    background_files = [
        f for f in os.listdir(background_dir)
        if f.lower().endswith(image_extensions)
    ]

    if not background_files:
        print(f"Warning: No background images found in {background_dir}")
        return []

    # Sort files for consistent ordering
    background_files.sort()

    background_urls = []

    for i in range(num_pages):
        # Cycle through available backgrounds
        bg_file = background_files[i % len(background_files)]
        bg_path = os.path.join(background_dir, bg_file)

        # Just return the file path - PIL can handle file paths directly
        background_urls.append(bg_path)
        print(f"✓ Loaded background: {bg_file}")

    return background_urls


def _draw_background(c: canvas.Canvas, background_path: str, page_width: float, page_height: float) -> None:
    """
    Draw background image for the page, scaled to fit the full page.
    Background is drawn first so other elements appear on top.
    """
    try:
        # Open image directly from file path
        bg_img = Image.open(background_path)
        img_reader = ImageReader(bg_img)
        # Scale background to cover full page
        c.drawImage(img_reader, 0, 0, width=page_width, height=page_height, preserveAspectRatio=False, mask="auto")
        print(f"✓ Background loaded successfully: {background_path}")
    except Exception as e:
        # If background fails to load, just continue without background
        print(f"⚠ Warning: Could not load background image {background_path}: {e}")
        pass


def _draw_image_left_half(c: canvas.Canvas, pil_img: Image.Image, page_width: float, page_height: float, margin: float, gutter: float) -> None:
    left_x = margin
    left_y = margin
    left_width = page_width / 2 - margin - gutter / 2
    left_height = page_height - 2 * margin

    # Compute scaled size preserving aspect ratio
    img_w, img_h = pil_img.size
    scale = min(left_width / img_w, left_height / img_h)
    draw_w = img_w * scale
    draw_h = img_h * scale

    # Center inside left box
    draw_x = left_x + (left_width - draw_w) / 2
    draw_y = left_y + (left_height - draw_h) / 2

    img_reader = ImageReader(pil_img)
    c.drawImage(img_reader, draw_x, draw_y, width=draw_w, height=draw_h, preserveAspectRatio=True, mask="auto")


def _draw_bold_text(c: canvas.Canvas, text: str, x: float, y: float, font_name: str, font_size: float, max_width: float, text_color: tuple = (0, 0, 0), shadow_color: tuple = (0.3, 0.3, 0.3)) -> float:
    """
    Draw text with bold effect by drawing multiple slightly offset copies.
    Uses specified text and shadow colors for optimal contrast.
    Returns the y position after drawing.
    """
    # Split text into lines that fit within max_width
    lines = []
    words = text.split()
    current_line = ""

    for word in words:
        test_line = current_line + " " + word if current_line else word
        if c.stringWidth(test_line, font_name, font_size) <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)

    # Draw each line with bold effect
    line_height = font_size * 1.3  # Line spacing
    current_y = y

    for line in lines:
        # Create bold effect by drawing multiple copies with small offsets
        offsets = [
            (0.5, 0),    # Right
            (-0.5, 0),   # Left
            (0, 0.5),    # Up
            (0, -0.5),   # Down
            (0.3, 0.3),  # Diagonal
            (-0.3, 0.3), # Diagonal
            (0.3, -0.3), # Diagonal
            (-0.3, -0.3) # Diagonal
        ]

        # Draw shadow copies first with specified shadow color
        c.setFillColorRGB(*shadow_color)
        for offset_x, offset_y in offsets:
            c.drawString(x + offset_x, current_y + offset_y, line)

        # Draw main text on top with specified text color
        c.setFillColorRGB(*text_color)
        c.drawString(x, current_y, line)

        current_y -= line_height

    return current_y


def _draw_text_right_half(c: canvas.Canvas, text: str, font_name: str, page_width: float, page_height: float, margin: float, gutter: float, background_url: Optional[str] = None) -> None:
    right_x = page_width / 2 + gutter / 2
    right_y = margin
    right_width = page_width / 2 - margin - gutter / 2
    right_height = page_height - 2 * margin

    # Đảm bảo text là UTF-8
    try:
        text = text.encode('utf-8').decode('utf-8')
    except (UnicodeDecodeError, UnicodeEncodeError):
        # Fallback nếu có vấn đề encoding
        text = str(text)

    # Set font for bold text rendering
    c.setFont(font_name, 18)

    # Auto-detect optimal text colors based on background brightness
    text_color = (0, 0, 0)  # Default: black
    shadow_color = (0.3, 0.3, 0.3)  # Default: dark gray

    if background_url:
        try:
            # Load background image to analyze brightness
            bg_img = Image.open(background_url)
            brightness = _analyze_background_brightness(bg_img)
            text_color, shadow_color = _get_optimal_text_colors(brightness)
            print(f"✓ Auto-detected text colors for background: brightness={brightness:.2f}, text={text_color}, shadow={shadow_color}")
        except Exception as e:
            print(f"⚠ Could not analyze background for color detection: {e}")
            # Keep default colors

    # Draw text with bold effect and optimal colors
    text_x = right_x + 8  # Left padding
    text_y = right_y + right_height - 8 - 18  # Top padding + font size

    _draw_bold_text(c, text, text_x, text_y, font_name, 18, right_width - 16, text_color, shadow_color)  # 16 = left + right padding


def create_pdf_book(image_urls: List[str], scripts: List[str], output_filename: str = "generated_book.pdf", font_path: Optional[str] = None, background_urls: Optional[List[str]] = None) -> str:
    """
    Tạo file PDF với số trang tùy ý, mỗi trang gồm:
    - Background: hình ảnh nền (tùy chọn, mỗi trang có thể khác nhau)
    - Nửa bên trái: ảnh từ URL tương ứng
    - Nửa bên phải: script (văn bản) tương ứng với font hiện đại

    File PDF sẽ được lưu cùng cấp với file .py này.

    Args:
        image_urls: Danh sách URL ảnh.
        scripts: Danh sách đoạn script (chuỗi văn bản).
        output_filename: Tên file PDF đầu ra.
        font_path: (Tùy chọn) Đường dẫn tới font TTF hiện đại (Comic Neue, Patrick Hand, etc.)
        background_urls: (Tùy chọn) Danh sách URL background cho mỗi trang. Nếu ít hơn số trang, background cuối sẽ được lặp lại.

    Returns:
        Đường dẫn tuyệt đối tới file PDF đã tạo.
    """
    if len(image_urls) != len(scripts):
        raise ValueError("Số lượng ảnh và script phải bằng nhau.")
    if len(image_urls) == 0:
        raise ValueError("Phải có ít nhất một ảnh và một script.")

    # Chuẩn bị font hiện đại
    font_name = _register_unicode_font(font_path)

    # Thiết lập trang nằm ngang A4
    page_width, page_height = landscape(A4)
    margin = 36  # 0.5 inch
    gutter = 16  # khoảng cách giữa 2 nửa trang

    # Đường dẫn lưu file cùng cấp với file .py này
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(base_dir, output_filename)

    c = canvas.Canvas(output_path, pagesize=(page_width, page_height))

    for idx, (img_url, text) in enumerate(zip(image_urls, scripts), start=1):
        # Background (nếu có)
        bg_path = None
        if background_urls:
            bg_path = background_urls[min(idx-1, len(background_urls)-1)]  # Lặp lại background cuối nếu ít hơn số trang
            _draw_background(c, bg_path, page_width, page_height)

        # Ảnh bên trái
        pil_img = _download_image_as_pil(img_url)
        _draw_image_left_half(c, pil_img, page_width, page_height, margin, gutter)

        # Text bên phải với font hiện đại, size lớn và màu tự động theo background
        _draw_text_right_half(c, text, font_name, page_width, page_height, margin, gutter, bg_path)

        # Số trang (tuỳ chọn)
        c.setFont(font_name if font_name != "Helvetica" else "Helvetica", 10)
        c.setFillGray(0.3)
        c.drawRightString(page_width - margin, margin / 2, f"Trang {idx}")
        c.setFillGray(0)

        c.showPage()

    c.save()
    return output_path


async def create_pdf_book_bytes(image_urls: List[str], scripts: List[str], font_path: Optional[str] = None) -> bytes:
    """
    Tạo file PDF và trả về dưới dạng bytes để có thể trả về trực tiếp qua API.
    Background sẽ tự động được load từ thư mục assets/backgrounds/topic_01.
    Tự động remove background cho tất cả ảnh trước khi tạo PDF.

    Args:
        image_urls: Danh sách URL ảnh.
        scripts: Danh sách đoạn script (chuỗi văn bản).
        font_path: (Tùy chọn) Đường dẫn tới font TTF hiện đại (Comic Neue, Patrick Hand, etc.)

    Returns:
        Dữ liệu PDF dưới dạng bytes.
    """
    if len(image_urls) != len(scripts):
        raise ValueError("Số lượng ảnh và script phải bằng nhau.")
    if len(image_urls) == 0:
        raise ValueError("Phải có ít nhất một ảnh và một script.")

    # Xử lý remove background cho tất cả ảnh
    processed_image_urls = []
    for idx, img_url in enumerate(image_urls, start=1):
        try:
            print(f"Processing remove background for image {idx}/{len(image_urls)}")
            processed_data = await remove_background(image_url=img_url)

            if processed_data:
                processed_image_urls.append(processed_data)
                print(f"Successfully processed image {idx}")
            else:
                # Nếu không thể remove background, sử dụng ảnh gốc
                processed_image_urls.append(img_url)
                print(f"Failed to remove background for image {idx}, using original")

        except Exception as rb_error:
            print(f"Error removing background for image {idx}: {str(rb_error)}")
            # Sử dụng ảnh gốc nếu có lỗi
            processed_image_urls.append(img_url)

    # Load background images
    print(f"DEBUG: Loading backgrounds for {len(scripts)} pages...")
    background_urls = get_background_urls(len(scripts))
    print(f"DEBUG: Loaded {len(background_urls)} background URLs")

    # Chuẩn bị font hiện đại
    font_name = _register_unicode_font(font_path)

    # Thiết lập trang nằm ngang A4
    page_width, page_height = landscape(A4)
    margin = 36  # 0.5 inch
    gutter = 16  # khoảng cách giữa 2 nửa trang

    # Tạo PDF trong memory
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(page_width, page_height))

    for idx, (img_url, text) in enumerate(zip(processed_image_urls, scripts), start=1):
        # Background từ thư mục assets
        bg_path = background_urls[min(idx-1, len(background_urls)-1)] if background_urls else None
        if bg_path:
            _draw_background(c, bg_path, page_width, page_height)

        # Ảnh bên trái
        pil_img = _download_image_as_pil(img_url)
        _draw_image_left_half(c, pil_img, page_width, page_height, margin, gutter)

        # Text bên phải với font hiện đại, size lớn và màu tự động theo background
        _draw_text_right_half(c, text, font_name, page_width, page_height, margin, gutter, bg_path)

        # Số trang (tuỳ chọn)
        c.setFont(font_name if font_name != "Helvetica" else "Helvetica", 10)
        c.setFillGray(0.3)
        c.drawRightString(page_width - margin, margin / 2, f"Trang {idx}")
        c.setFillGray(0)

        c.showPage()

    c.save()
    buffer.seek(0)
    return buffer.getvalue()

