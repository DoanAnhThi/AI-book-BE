import time
import os
import json
from typing import List, Optional, Dict, Any

from openai import OpenAI


async def gen_prompt(
    scripts: List[str],
    topic: Optional[str] = None,
    main_character: Optional[str] = None,
    illustration_style: str = "cute, colorful, children's book illustration"
) -> Dict[str, Any]:
    """
    Generate illustration prompts for each script page using OpenAI.

    Args:
        scripts: List of story snippets, one per page.
        topic: Optional topic of the book to guide prompt tone.
        main_character: Optional main character name to ensure consistency.
        illustration_style: Preferred illustration style keywords.

    Returns:
        Dict with keys: "page_prompts" (List[str]), "processing_time", "model_used", "success".
    """

    start_time = time.time()

    if not scripts:
        return {
            "page_prompts": [],
            "processing_time": 0.0,
            "model_used": None,
            "success": False,
            "error": "Scripts list cannot be empty."
        }

    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")

    client = OpenAI(api_key=openai_api_key)

    # Compose instruction for the model
    topic_clause = f" about the topic '{topic}'" if topic else ""
    character_clause = (
        f" featuring the main character '{main_character}'" if main_character else ""
    )

    numbered_scripts = "\n".join(
        [f"Page {idx + 1}: {scripts[idx]}" for idx in range(len(scripts))]
    )

    system_prompt = (
        "You are an expert children's book illustrator prompt engineer. "
        "Create vivid, imaginative prompts for text-to-image models."
    )

    user_prompt = f"""
    For each page script below{topic_clause}{character_clause}, craft a detailed image prompt.

    Requirements:
    1. Keep prompts concise (<= 120 tokens) but descriptive.
    2. Clearly describe the main character (consistent appearance across pages).
    3. Mention actions, emotions, and setting details from the script.
    4. Include camera angle or shot type for variety.
    5. Use the illustration style keywords: {illustration_style}.
    6. Return JSON with structure:
       {{
         "page_prompts": [
            "prompt for page 1",
            "prompt for page 2",
            ...
         ]
       }}
    7. The number of prompts must equal the number of scripts provided.

    Page scripts:
    {numbered_scripts}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=1200,
        )

        content = response.choices[0].message.content

        if isinstance(content, str):
            try:
                content = content.encode("utf-8").decode("utf-8")
            except (UnicodeEncodeError, UnicodeDecodeError):
                pass

        payload = json.loads(content)
        prompts = payload.get("page_prompts", [])

        # Ensure alignment length
        if len(prompts) != len(scripts):
            # Pad or trim to match script count
            prompts = (prompts + scripts)[: len(scripts)]

        processing_time = time.time() - start_time

        return {
            "page_prompts": prompts,
            "processing_time": processing_time,
            "model_used": "gpt-4o-mini",
            "success": True,
        }

    except Exception as exc:  # noqa: BLE001 - broad except for API errors
        processing_time = time.time() - start_time
        return {
            "page_prompts": [],
            "processing_time": processing_time,
            "model_used": "gpt-4o-mini",
            "success": False,
            "error": str(exc),
        }

