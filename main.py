import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from src.ai.api.ai_routes import router
from src.db.api.db_routes import router as db_router
from src.db.cart.api.cart_routes import router as cart_router
from src.db.order.api.order_routes import router as order_router
from src.mail.mail_routes import router as mail_router
from src.payments.paypal.payment_routes import router as payment_router
from src.payments.ApplePay.apple_pay_routes import router as apple_pay_router
from src.payments.GooglePay.google_pay_routes import router as google_pay_router
from src.payments.AmazonPay.amazon_pay_routes import router as amazon_pay_router
from src.db.common.database_connection import init_database
from test.route.test_routes import router as test_router

# Load environment variables
load_dotenv()

# Tạo instance của FastAPI
app = FastAPI(
    title="High5 Gen Book API",
    description="API tạo sách thiếu nhi cá nhân hóa với PostgreSQL database",
    version="1.0.0"
)

# Mount static files cho thư mục images
'''
FE request: GET /images/career.jpeg
           ↓
FastAPI thấy "/images" → gọi StaticFiles(directory="test/test_response/image")
           ↓
Tìm file: test/test_response/image/career.jpeg ✅
'''
app.mount("/images", StaticFiles(directory="test/test_response/image"), name="images")

# Mount static files cho thư mục assets (backgrounds, characters, stories)
app.mount("/assets", StaticFiles(directory="assets"), name="assets")

# CORS middleware để cho phép frontend truy cập
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Trong production nên chỉ định domain cụ thể
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database sẽ được init khi có request đầu tiên đến
# @app.on_event("startup")
# async def startup_event():
#     """Khởi tạo database khi ứng dụng khởi động"""
#     try:
#         # Run database init in thread pool to avoid blocking
#         import asyncio
#         from concurrent.futures import ThreadPoolExecutor
#         loop = asyncio.get_event_loop()
#         with ThreadPoolExecutor() as executor:
#             await loop.run_in_executor(executor, init_database)
#         print("✅ Database initialized successfully")
#     except Exception as e:
#         print(f"❌ Database initialization failed: {e}")
#         # Có thể raise exception để dừng ứng dụng nếu database không khởi tạo được
#         # raise e

# Health check route
@app.get("/health")
async def health():
    """Health check endpoint"""
    return "healthy"

# Root route
@app.get("/")
async def root():
    """Root endpoint trả về thông tin API"""
    return {
        "message": "Chào mừng đến với High5 Gen Book API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "AI": "/api/v1/",
            "Database": "/api/v1/db/",
            "Cart": "/api/v1/",
            "Order": "/api/v1/",
            "Mail": "/api/v1/",
            "Payments": "/api/v1/payments/",
            "Test": "/api/v1/test/"
        }
    }

# Include routers từ các modules
app.include_router(router, prefix="/api/v1", tags=["AI"])
app.include_router(db_router, prefix="/api/v1/db", tags=["Users"])
app.include_router(cart_router, prefix="/api/v1", tags=["Cart"])
app.include_router(order_router, prefix="/api/v1", tags=["Order"])
app.include_router(mail_router, prefix="/api/v1", tags=["Mail"])
app.include_router(payment_router, prefix="/api/v1/payments/paypal", tags=["Paypal"])
app.include_router(apple_pay_router, prefix="/api/v1/payments/apple-pay", tags=["Apple Pay"])
app.include_router(google_pay_router, prefix="/api/v1/payments/google-pay", tags=["Google Pay"])
app.include_router(amazon_pay_router, prefix="/api/v1/payments/amazon-pay", tags=["Amazon Pay"])
app.include_router(test_router, prefix="/api/v1/test", tags=["Test"])

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

