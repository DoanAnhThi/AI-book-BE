import time
import asyncio
import os
from typing import Dict, Any
import replicate


# Get Replicate API token from environment variable
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
if not REPLICATE_API_TOKEN:
    raise ValueError("REPLICATE_API_TOKEN environment variable is not set")

# Initialize Replicate client with API token
client = replicate.Client(api_token=REPLICATE_API_TOKEN)


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
        input_params = {
            "upscale": True,
            "detailer": False,
            "swap_image": face_image_url,  # Face to swap from - this is a URL
            "hair_source": "target",
            "user_gender": "a woman",
            "target_image": body_image_url,  # Body to swap onto - this needs to be uploaded
            "user_b_gender": "a woman"
        }

        # Run the Replicate model asynchronously using thread pool
        print(f"DEBUG swap_face: Calling Replicate API with input: {input_params}")
        try:
            loop = asyncio.get_event_loop()
            output = await loop.run_in_executor(None, client.run, "easel/advanced-face-swap", input_params)
            print(f"DEBUG swap_face: Replicate API call completed")
        except Exception as api_error:
            print(f"DEBUG swap_face: Replicate API call failed: {str(api_error)}")
            raise api_error

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
