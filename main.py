import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.ai.api.ai_routes import router
from src.db.api.db_routes import router as db_router
from src.payments.paypal.payment_routes import router as payment_router
from src.db.common.database_connection import init_database

# Tạo instance của FastAPI
app = FastAPI(
    title="High5 Gen Book API",
    description="API tạo sách thiếu nhi cá nhân hóa với PostgreSQL database",
    version="1.0.0"
)

# CORS middleware để cho phép frontend truy cập
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Trong production nên chỉ định domain cụ thể
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Khởi tạo database khi ứng dụng start
@app.on_event("startup")
async def startup_event():
    """Khởi tạo database khi ứng dụng khởi động"""
    try:
        init_database()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        # Có thể raise exception để dừng ứng dụng nếu database không khởi tạo được
        # raise e

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
            "Payments": "/api/v1/payments/"
        }
    }

# Include routers từ các modules
app.include_router(router, prefix="/api/v1", tags=["AI"])
app.include_router(db_router, prefix="/api/v1/db", tags=["Database"])
app.include_router(payment_router, prefix="/api/v1/payments", tags=["Payments"])

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

