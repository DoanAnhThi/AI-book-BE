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


async def gen_avatar(
    image_url: str,
    output_format: str = "jpeg"
) -> Optional[str]:
    """
    Generate a cartoon image using Replicate's Flux Kontext Pro model

    Args:
        image_url (str): URL of the input image to convert to cartoon
        output_format (str): Output format - "jpeg" (default: "jpeg")

    Returns:
        Optional[str]: URL of the generated cartoon image, or None if generation failed
    """
    try:
        # Fixed prompt for cartoon generation
        prompt = "Make this a 90s cartoon"

        # Đảm bảo prompt là UTF-8
        try:
            prompt = prompt.encode('utf-8').decode('utf-8')
        except (UnicodeDecodeError, UnicodeEncodeError):
            prompt = str(prompt)

        # Run the Replicate model asynchronously using thread pool
        loop = asyncio.get_event_loop()
        output = await loop.run_in_executor(
            None,
            client.run,
            "black-forest-labs/flux-kontext-pro",
            {
                "prompt": prompt,
                "input_image": image_url,
                "output_format": output_format
            }
        )

        # Return the URL of the generated image
        def ensure_utf8_string(text):
            """Đảm bảo string là UTF-8"""
            if isinstance(text, str):
                try:
                    return text.encode('utf-8').decode('utf-8')
                except (UnicodeDecodeError, UnicodeEncodeError):
                    return str(text)
            return text

        if isinstance(output, str):
            # Output is already a URL string
            return ensure_utf8_string(output)
        elif hasattr(output, 'url'):
            url = output.url() if callable(output.url) else output.url
            return ensure_utf8_string(url)
        elif output and isinstance(output, list) and len(output) > 0:
            # Try to get URL from list
            first_item = output[0]
            if isinstance(first_item, str):
                return ensure_utf8_string(first_item)
            elif hasattr(first_item, 'url'):
                url = first_item.url() if callable(first_item.url) else first_item.url
                return ensure_utf8_string(url)
        else:
            print("Warning: No output URL received from Replicate")
            return None

    except Exception as e:
        print(f"Error generating cartoon image: {str(e)}")
        return None
