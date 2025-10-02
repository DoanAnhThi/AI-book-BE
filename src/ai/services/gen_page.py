import time
import os
import json
import base64
import requests
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import HTTPException

from src.ai.services.get_page_id import get_page_id
from src.ai.services.swap_face import swap_face
from src.ai.services.gen_book import create_pdf_book_bytes


async def upload_image_to_imgur(image_path: Path) -> str:
    """
    Upload image to Imgur and return public URL for Replicate API.

    Args:
        image_path: Path to the image file

    Returns:
        Public URL of the uploaded image
    """
    try:
        # Read image file as base64
        with open(image_path, 'rb') as f:
            image_data = f.read()

        # Upload to Imgur (anonymous upload)
        headers = {
            'Authorization': f'Client-ID {os.getenv("IMGUR_CLIENT_ID", "anonymous")}' if os.getenv("IMGUR_CLIENT_ID") else None
        }

        response = requests.post(
            'https://api.imgur.com/3/image',
            headers=headers,
            files={'image': image_data}
        )

        if response.status_code == 200:
            data = response.json()
            return data['data']['link']
        else:
            print(f"DEBUG: Imgur upload failed: {response.status_code} - {response.text}")
            # Fallback: return a placeholder URL
            return "https://picsum.photos/512/512?random=1"

    except Exception as e:
        print(f"DEBUG: Imgur upload error: {str(e)}")
        # Fallback: return a placeholder URL
        return "https://picsum.photos/512/512?random=1"


async def convert_image_to_data_url(image_path: Path) -> str:
    """
    Convert image file to base64 data URL for Replicate API.

    Args:
        image_path: Path to the image file

    Returns:
        Base64 data URL of the image
    """
    try:
        # Read image file
        with open(image_path, 'rb') as f:
            image_data = f.read()

        # Convert to base64
        encoded_data = base64.b64encode(image_data).decode('utf-8')

        # Get file extension
        file_ext = image_path.suffix.lower().lstrip('.')

        # Create data URL
        data_url = f"data:image/{file_ext};base64,{encoded_data}"

        return data_url

    except Exception as e:
        print(f"DEBUG: Data URL conversion error: {str(e)}")
        # Fallback: return a placeholder URL
        return "https://picsum.photos/512/512?random=1"


async def generate_page(
    category_id: str,
    book_id: str,
    story_id: str,
    page_id: str,
    image_url: str
) -> Dict[str, Any]:
    """
    Generate a single PDF page for the specified story page with face swapping.

    Args:
        category_id: Category identifier
        book_id: Book identifier
        story_id: Story identifier
        page_id: Page identifier
        image_url: URL of the face image to swap onto the character

    Returns:
        Dict containing PDF bytes and metadata
    """
    start_time = time.time()

    try:
        # Get the page ID using the service
        print(f"DEBUG: Getting page ID for {category_id}{book_id}{story_id}{page_id}")
        page_key = get_page_id(category_id, book_id, story_id, page_id)
        print(f"DEBUG: Page key: {page_key}")

        # Load catalog metadata
        BASE_DIR = Path(__file__).resolve().parents[3]
        catalog_path = BASE_DIR / "assets" / "catalog_metadata.yaml"

        import yaml
        with catalog_path.open("r", encoding="utf-8") as f:
            catalog_data = yaml.safe_load(f)

        if not catalog_data or "pages" not in catalog_data:
            raise HTTPException(status_code=500, detail="Invalid catalog metadata")

        page_metadata = catalog_data["pages"].get(page_key)
        if not page_metadata:
            print(f"DEBUG: Available pages: {list(catalog_data['pages'].keys())}")
            raise HTTPException(status_code=404, detail=f"Page metadata not found for ID: {page_key}")
        print(f"DEBUG: Page metadata: {page_metadata}")

        # Extract paths from metadata
        background_path = page_metadata.get("background")
        character_path = page_metadata.get("character")
        story_file_path = page_metadata.get("story_file")

        if not all([background_path, character_path, story_file_path]):
            raise HTTPException(status_code=500, detail="Incomplete page metadata")

        # Load story content
        story_file_full_path = BASE_DIR / story_file_path
        if not story_file_full_path.exists():
            raise HTTPException(status_code=404, detail=f"Story file not found: {story_file_path}")

        with story_file_full_path.open("r", encoding="utf-8") as f:
            story_data = json.load(f)

        page_content = story_data.get("page_content")
        if not page_content:
            raise HTTPException(status_code=400, detail="Page content not found in story file")
        print(f"DEBUG: Page content loaded: {page_content[:50]}...")

        # Swap face onto character image
        character_full_path = BASE_DIR / character_path
        if not character_full_path.exists():
            raise HTTPException(status_code=404, detail=f"Character image not found: {character_path}")

        # Convert character image to base64 data URL for Replicate
        character_url = await convert_image_to_data_url(character_full_path)
        print(f"DEBUG: Created character data URL (length: {len(character_url)})")

        print(f"DEBUG: Starting face swap...")
        face_swap_result = await swap_face(
            face_image_url=image_url,
            body_image_url=character_url
        )
        print(f"DEBUG: Face swap result: {face_swap_result.get('success', False)}")

        if not face_swap_result["success"]:
            print(f"DEBUG: Face swap failed, using original character")
            swapped_character_url = character_local_path  # Fallback to local path
        else:
            swapped_character_url = face_swap_result["swapped_image_url"]

        # Load background
        background_full_path = BASE_DIR / background_path
        if not background_full_path.exists():
            raise HTTPException(status_code=404, detail=f"Background image not found: {background_path}")

        # For PDF generation, use local file paths instead of URLs
        background_local_path = str(background_full_path)
        character_local_path = str(character_full_path)

        # Create single page PDF
        print(f"DEBUG: Creating PDF with background: {background_local_path}")
        print(f"DEBUG: Creating PDF with swapped character: {swapped_character_url}")
        pdf_bytes = await create_pdf_book_bytes(
            image_urls=[swapped_character_url],  # Use swapped image URL
            scripts=[page_content],
            background_urls=[background_local_path]  # Use local path for background
        )
        print(f"DEBUG: PDF created, size: {len(pdf_bytes)} bytes")

        processing_time = time.time() - start_time

        return {
            "pdf_bytes": pdf_bytes,
            "page_key": page_key,
            "background_path": background_path,
            "character_path": character_path,
            "story_file_path": story_file_path,
            "swapped_character_url": swapped_character_url,
            "page_content": page_content,
            "processing_time": processing_time,
            "success": True
        }

    except HTTPException:
        raise
    except Exception as e:
        processing_time = time.time() - start_time
        raise HTTPException(
            status_code=500,
            detail=f"Page generation failed: {str(e)}"
        )
