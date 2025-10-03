import time
import asyncio
import os
import base64
import requests
from pathlib import Path
from typing import Dict, Any
import replicate


# Get Replicate API token from environment variable
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
if not REPLICATE_API_TOKEN:
    raise ValueError("REPLICATE_API_TOKEN environment variable is not set")

# Initialize Replicate client with API token
client = replicate.Client(api_token=REPLICATE_API_TOKEN)


async def open_local_file_for_replicate(file_path: str):
    """
    Open a local file and return a file object that can be passed directly to Replicate API.
    This allows Replicate to upload the file directly without needing external hosting.

    Args:
        file_path: Local path to the image file

    Returns:
        File object that Replicate can use directly
    """
    try:
        # Convert relative path to absolute path
        if not file_path.startswith('/'):
            # Assume it's relative to the project root
            from pathlib import Path
            base_dir = Path(__file__).resolve().parents[3]  # Go up to project root
            full_path = base_dir / file_path
        else:
            full_path = Path(file_path)

        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {full_path}")

        print(f"DEBUG: Opening local file for Replicate: {full_path}")

        # Open file in binary mode for Replicate
        file_obj = open(full_path, 'rb')

        print(f"DEBUG: File opened successfully for Replicate")
        return file_obj

    except Exception as e:
        print(f"DEBUG: Failed to open local file for Replicate: {e}")
        # Fallback: return None and let Replicate handle it
        return None


async def swap_face(face_image_url: str, body_image_url: str) -> Dict[str, Any]:
    """
    Swap face from face_image_url onto body_image_url using Bytedance Seedream 4 model.

    Args:
        face_image_url: URL of the face image
        body_image_url: URL of the body image to place the face on

    Returns:
        Dict containing result URL and metadata
    """
    start_time = time.time()

    try:
        print(f"DEBUG swap_face: face_url={face_image_url[:50]}..., body_url={body_image_url[:50]}...")

        print(f"DEBUG swap_face: Using easel/advanced-face-swap model")

        # Prepare input parameters for easel/advanced-face-swap model
        # Based on working example from Replicate web interface

        # Handle target_image - can be URL or local file path
        if body_image_url.startswith('http://') or body_image_url.startswith('https://'):
            # This is a URL - Replicate can access it directly
            target_image = body_image_url
        else:
            # This is a local file path - open file and pass file object to Replicate
            target_image = await open_local_file_for_replicate(body_image_url)

        input_params = {
            "upscale": True,
            "detailer": False,
            "swap_image": face_image_url,  # Face to swap from - this is a URL
            "hair_source": "user",
            "user_gender": "a woman",
            "target_image": target_image,  # Body to swap onto - uploaded or external URL
            "user_b_gender": "a woman"
        }

        # Handle file objects properly - need to manage file lifecycle
        file_to_close = None
        if hasattr(target_image, 'read'):  # Check if it's a file object
            file_to_close = target_image

        try:
            # Run the Replicate model asynchronously using thread pool
            print(f"DEBUG swap_face: Calling Replicate API with input: {input_params}")
            loop = asyncio.get_event_loop()
            output = await loop.run_in_executor(None, client.run, "easel/advanced-face-swap", input_params)
            print(f"DEBUG swap_face: Replicate API call completed")
        except Exception as api_error:
            print(f"DEBUG swap_face: Replicate API call failed: {str(api_error)}")
            raise api_error
        finally:
            # Close file object if we opened one
            if file_to_close:
                try:
                    file_to_close.close()
                    print(f"DEBUG swap_face: Closed file object")
                except Exception as close_error:
                    print(f"DEBUG swap_face: Error closing file: {close_error}")

        processing_time = time.time() - start_time

        # Process the output
        def ensure_utf8_string(text):
            """Đảm bảo string là UTF-8"""
            if isinstance(text, str):
                try:
                    return text.encode('utf-8').decode('utf-8')
                except (UnicodeDecodeError, UnicodeEncodeError):
                    return str(text)
            return text

        print(f"DEBUG swap_face: output received, type={type(output)}")

        # Process the output - easel/advanced-face-swap returns a single output object
        if output:
            if hasattr(output, 'url'):
                # Call url() method if it's callable, otherwise access url attribute
                url = output.url() if callable(output.url) else output.url
                generated_url = ensure_utf8_string(url)
                print(f"DEBUG swap_face: Generated URL: {generated_url}")
            else:
                print(f"DEBUG swap_face: Output doesn't have url method/attribute: {output}")
                generated_url = ""
        else:
            print("DEBUG swap_face: No output received from model")
            generated_url = ""

        if generated_url:
            return {
                "swapped_image_url": generated_url,
                "success": True,
                "processing_time": processing_time,
                "model_used": "easel/advanced-face-swap",
                "face_image_url": face_image_url,
                "body_image_url": body_image_url
            }
        else:
            return {
                "swapped_image_url": "",
                "success": False,
                "processing_time": processing_time,
                "error": "No valid URL returned from model",
                "face_image_url": face_image_url,
                "body_image_url": body_image_url
            }

    except Exception as e:
        processing_time = time.time() - start_time
        print(f"DEBUG swap_face: Exception occurred: {str(e)}")
        return {
            "swapped_image_url": "",
            "success": False,
            "processing_time": processing_time,
            "error": f"Face swap failed: {str(e)}",
            "face_image_url": face_image_url,
            "body_image_url": body_image_url
        }
