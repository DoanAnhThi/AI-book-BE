import requests
import io
import base64
from rembg import remove
from PIL import Image
from typing import Optional


async def remove_background(image_url: str) -> Optional[str]:
    """
    Remove background from an image URL and return as base64 data URL

    Args:
        image_url (str): URL of the input image

    Returns:
        Optional[str]: Base64 data URL of the processed image, or None if processing failed
    """
    # Kiểm tra xem ảnh đã là base64 data URL chưa
    if image_url.startswith("data:image/"):
        print(f"Image is already processed (base64 data URL), skipping remove background")
        return image_url

    try:
        print(f"Starting remove background for URL: {image_url}")

        # Step 1: Download image from URL
        print("Step 1: Downloading image...")
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        print(f"Downloaded image, size: {len(response.content)} bytes")

        # Step 2: Open image from bytes
        print("Step 2: Opening image...")
        input_img = Image.open(io.BytesIO(response.content))
        print(f"Image opened successfully, format: {input_img.format}, size: {input_img.size}")

        # Step 3: Remove background
        print("Step 3: Removing background...")
        output_img = remove(input_img)
        print("Background removed successfully")

        # Step 4: Convert to bytes
        print("Step 4: Converting to PNG bytes...")
        output_buffer = io.BytesIO()
        output_img.save(output_buffer, format='PNG')
        output_bytes = output_buffer.getvalue()
        print(f"Converted to PNG, size: {len(output_bytes)} bytes")

        # Convert to base64 data URL for direct viewing
        base64_data = base64.b64encode(output_bytes).decode('utf-8')
        data_url = f"data:image/png;base64,{base64_data}"
        print("Converted to base64 data URL successfully")

        return data_url

    except requests.exceptions.RequestException as e:
        print(f"Network error: {str(e)}")
        return None
    except Image.UnidentifiedImageError as e:
        print(f"Image format error: {str(e)}")
        return None
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None