# app/main.py

from fastapi import FastAPI
from app.database import create_db_and_tables
from app.routers import auth, blog # Import các routers

# Khởi tạo ứng dụng
app = FastAPI(
    title="Blog API cho Android App",
    description="API được xây dựng dựa trên các yêu cầu của client Kotlin/Retrofit",
    version="1.0.0"
)

# Gắn các Routers
app.include_router(auth.router)
app.include_router(blog.router)

@app.on_event("startup")
def on_startup():
    """
    Đảm bảo DB được khởi tạo và tạo bảng (nếu chưa có) khi app khởi động.
    """
    # Hàm này đã được định nghĩa trong app/db.py
    create_db_and_tables() 

# Nếu bạn đang chạy ứng dụng: uvicorn app.main:app --reload