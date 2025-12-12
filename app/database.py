from sqlmodel import create_engine, SQLModel, Session
from app.config import settings
from app.models import User, Blog, Category # Import tất cả các models để SQLModel biết cần tạo những bảng nào

# Chuỗi kết nối đến database (async)
# Với PostgreSQL, cần dùng thư viện asyncpg: postgresql+asyncpg://...
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL.replace("postgresql", "postgresql+psycopg2")
# Khởi tạo Engine
engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True) 

def create_db_and_tables():
    """
    Hàm này kiểm tra và tạo tất cả các bảng nếu chúng chưa tồn tại 
    dựa trên các Models kế thừa từ SQLModel đã được import.
    """
    print("Checking and creating database tables...")
    SQLModel.metadata.create_all(engine)
    print("Database tables checked/created successfully.")

def get_session():
    """
    Dependency cho FastAPI để cung cấp một database session.
    """
    with Session(engine) as session:
        yield session

# Khuyến nghị: Nếu muốn dùng async (tốt hơn cho FastAPI), bạn sẽ dùng:
# from sqlmodel.ext.asyncio.session import AsyncSession, AsyncEngine
# engine = create_async_engine(...)
# async def get_session():
#     async with AsyncSession(engine) as session:
#         yield session