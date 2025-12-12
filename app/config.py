from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # Lấy chuỗi kết nối từ biến môi trường
    # Mặc định sử dụng chuỗi kết nối trong docker-compose nếu không tìm thấy biến
    DATABASE_URL: str = Field(
        default="postgresql://user_blog:secret@db:5432/blog_db", 
        description="Chuỗi kết nối đến PostgreSQL"
    )
    
    # JWT Configuration
    SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production-use-env-variable",
        description="Secret key để ký JWT tokens"
    )
    ALGORITHM: str = Field(
        default="HS256",
        description="Thuật toán mã hóa JWT"
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        description="Thời gian hết hạn của access token (phút)"
    )

    # Cấu hình để load biến môi trường từ file .env
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

# Khởi tạo đối tượng settings
settings = Settings()