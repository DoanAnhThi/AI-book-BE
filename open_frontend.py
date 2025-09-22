#!/usr/bin/env python3
"""
Script để mở frontend HTML trong browser
"""

import webbrowser
import os
import sys

def open_frontend():
    """Mở file frontend HTML trong browser mặc định"""

    html_path = os.path.join(os.path.dirname(__file__), "example", "frontend_example.html")

    if not os.path.exists(html_path):
        print(f"❌ Không tìm thấy file: {html_path}")
        return

    # Chuyển đổi path thành URL
    abs_path = os.path.abspath(html_path)
    url = f"file://{abs_path}"

    print(f"🌐 Đang mở frontend: {url}")

    try:
        # Mở trong browser mặc định
        webbrowser.open(url)
        print("✅ Frontend đã được mở trong browser!")
        print("\n📋 Hướng dẫn:")
        print("1. Đảm bảo server FastAPI đang chạy: uvicorn main:app --reload --host 0.0.0.0 --port 8000")
        print("2. Nhập loại sách, tên nhân vật và URL ảnh tham khảo")
        print("3. Click '🚀 Tạo sách hoàn chỉnh với AI' để tạo sách")

    except Exception as e:
        print(f"❌ Lỗi khi mở browser: {e}")
        print(f"📂 Bạn có thể mở file thủ công: {abs_path}")

if __name__ == "__main__":
    print("=" * 60)
    print("🎉 HIGH5 GEN BOOK - FRONTEND LAUNCHER")
    print("=" * 60)
    open_frontend()
