import time
import asyncio
import os
from openai import OpenAI
import json
import replicate
from typing import Optional, Dict, Any

# Get Replicate API token from environment variable
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")
if not REPLICATE_API_TOKEN:
    raise ValueError("REPLICATE_API_TOKEN environment variable is not set")

# Initialize Replicate client with API token
client = replicate.Client(api_token=REPLICATE_API_TOKEN)


async def gen_illustration_image(
    prompt: str,
    image_url: str = "",
    output_format: str = "png",
    aspect_ratio: str = "match_input_image",
    size: str = "custom",
    width: int = 2480,
    height: int = 1754,
    max_images: int = 1,
    sequential_image_generation: str = "disabled"
) -> Optional[str]:
    """
    Generate an image using Replicate's Bytedance Seedream 4 model

    Args:
        prompt (str): Text description for image generation
        image_url (str): URL of the reference image for image-to-image generation
        output_format (str): Output format (ignored by current model)
        aspect_ratio (str): Aspect ratio of the generated image (default: "match_input_image")
        size (str): Image resolution: "1K", "2K", "4K", or "custom" (default: "custom" - optimized for A4 horizontal)
        width (int): Custom image width when size="custom" (default: 2480px - suitable for A4 horizontal background)
        height (int): Custom image height when size="custom" (default: 1754px - suitable for A4 horizontal background)
        max_images (int): Maximum number of images to generate (default: 1, range: 1-15)
        sequential_image_generation (str): "disabled" or "auto" (default: "disabled")

    Returns:
        Optional[str]: URL of the generated image, or None if generation failed
    """
    try:
        # Đảm bảo prompt là UTF-8
        try:
            prompt = prompt.encode('utf-8').decode('utf-8')
        except (UnicodeDecodeError, UnicodeEncodeError):
            prompt = str(prompt)

        # Prepare input parameters
        input_params = {
            "prompt": prompt,
            "size": size,
            "max_images": max_images,
            "aspect_ratio": aspect_ratio,
            "sequential_image_generation": sequential_image_generation
        }

        # Add custom dimensions if size is "custom"
        if size == "custom":
            input_params["width"] = width
            input_params["height"] = height

        # Add image_input if image_url is provided
        if image_url and image_url.strip():
            input_params["image_input"] = [image_url]

        # Run the Replicate model asynchronously using thread pool
        loop = asyncio.get_event_loop()
        output = await loop.run_in_executor(None, client.run, "bytedance/seedream-4", input_params)

        # Return the URL of the generated image
        def ensure_utf8_string(text):
            """Đảm bảo string là UTF-8"""
            if isinstance(text, str):
                try:
                    return text.encode('utf-8').decode('utf-8')
                except (UnicodeDecodeError, UnicodeEncodeError):
                    return str(text)
            return text

        if output and isinstance(output, list) and len(output) > 0:
            # Get URL from the first output item
            first_item = output[0]
            if hasattr(first_item, 'url'):
                url = first_item.url() if callable(first_item.url) else first_item.url
                return ensure_utf8_string(url)
            elif isinstance(first_item, str):
                return ensure_utf8_string(first_item)
        else:
            print("Warning: No output URL received from Replicate")
            return None

    except Exception as e:
        print(f"Error generating image: {str(e)}")
        return None
