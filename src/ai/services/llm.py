import time
import asyncio
import os
from openai import OpenAI


# === HÀM XỬ LÝ AI SCRIPT GENERATION VỚI OPENAI ===


async def gen_script(type: str, name: str):
    """
    Hàm tạo nội dung sách thiếu nhi cá nhân hóa dựa trên loại được yêu cầu
    Sử dụng OpenAI để tạo câu chuyện phù hợp với lứa tuổi trẻ em
    """
    start_time = time.time()

    # Get OpenAI API key from environment variable
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")

    # Khởi tạo OpenAI model
    model = OpenAI(api_key=openai_api_key)

    try:
        # Create prompt with simple JSON format
        prompt = f"""
          Create a personalized children's book with theme: {type}.

          Please return JSON with the following format:

          {{
            "title": "attractive book title",
            "content": {{
              "page 1": {{
                "page-content": "story content for page 1 (20-60 words)",
                "page-prompt": "prompt to generate image for page 1"
              }},
              "page 2": {{
                "page-content": "story content for page 2 (20-60 words)",
                "page-prompt": "prompt to generate image for page 2"
              }},
              "page 3": {{
                "page-content": "story content for page 3 (20-60 words)",
                "page-prompt": "prompt to generate image for page 3"
              }}
            }}
          }}

          Requirements:
          1. Attractive book title suitable for theme: {type}
          2. Create content for the first 3 pages of the story
          3. Each page should have both story content and image prompt
          4. Fun, educational style, appropriate for 4-year-old children
          5. The main character is {character_name}, who explores the world of {type} in fun and imaginative ways
          6. Each "page-prompt" must describe {character_name}, the {type}-related setting, and style: "cute, colorful, children's book illustration"
          7. Ensure {character_name} appears consistently across all prompts
          8. Each "page-prompt" must describe {character_name}'s clear action (running, jumping, swimming, exploring, etc.) instead of only standing still.
          9. Include camera angle/viewpoint in each "page-prompt" using these common AI art keywords:
             - front view / front-facing → chụp chính diện
             - back view / rear view / from behind → chụp từ phía sau
             - side view / profile view → chụp ngang, nghiêng
             - 3/4 view (three-quarter view) → góc nghiêng 45°
             - top view / bird's eye view → chụp từ trên xuống
             - low angle / from below → chụp từ dưới lên
          10. IMPORTANT: Use different camera angles for consecutive pages to create visual variety (e.g., page 1: front view, page 2: side view, page 3: 3/4 view)

          """

        # Đơn giản hóa response format
        response_format = {"type": "json_object"}

        # Gọi OpenAI API
        response = model.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format=response_format,
            max_tokens=2000,
            temperature=0.8,  # Tăng creativity cho câu chuyện thiếu nhi
        )

        # Parse JSON response với xử lý encoding UTF-8
        import json

        response_content = response.choices[0].message.content

        # Đảm bảo response content là UTF-8
        if isinstance(response_content, str):
            try:
                response_content = response_content.encode("utf-8").decode("utf-8")
            except (UnicodeDecodeError, UnicodeEncodeError):
                pass

        book_content = json.loads(response_content)

        processing_time = time.time() - start_time

        return {
            "script": book_content,
            "script_type": type,
            "processing_time": processing_time,
            "model_used": "gpt-4o-mini",
            "success": True,
        }

    except Exception as e:
        processing_time = time.time() - start_time
        return {
            "error": str(e),
            "script_type": type,
            "processing_time": processing_time,
            "success": False,
        }
