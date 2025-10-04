from fastapi import APIRouter, HTTPException
import os

router = APIRouter()

@router.get("/pdf")
async def get_pdf():
    """Trả về URL của file PDF demo"""
    pdf_path = "test/test_response/PDF/demo_01.pdf"

    # Kiểm tra file có tồn tại không
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="PDF file not found")

    # Trả về URL để FE có thể truy cập
    return {
        "url": "/test/test_response/PDF/demo_01.pdf",
        "filename": "demo_01.pdf",
        "type": "application/pdf"
    }

@router.get("/images")
async def get_image_paths():
    """Trả về URL các file hình ảnh"""
    return {
        "style_1": {
            "url": "/images/career.png",
            "type": "image/png"
        },
        "style_2": {
            "url": "/images/detactive.png",
            "type": "image/png"
        },
        "style_3": {
            "url": "/images/happy.png",
            "type": "image/png"
        }
    }
