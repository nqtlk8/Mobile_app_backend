from sqlmodel import SQLModel, Field, Relationship, Column
from typing import Optional, List
from datetime import datetime
from sqlalchemy import Enum as SQLAlchemyEnum
from app.schemas import CategoryEnum # <-- Import Enum từ file schemas

# --- Base Model (Để thêm trường thời gian tự động) ---

class TimestampModel(SQLModel):
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


# --- Category Model ---

class Category(TimestampModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True, index=True)
    
    # Định nghĩa cột 'name' sử dụng SQLAlchemyEnum để ràng buộc giá trị
    name: CategoryEnum = Field(
        sa_column=Column(
            SQLAlchemyEnum(
                CategoryEnum, 
                values_callable=lambda x: [e.value for e in x],
            ), 
            unique=True,
            nullable=False,
            index=True
        ),
    )
    
    # Quan hệ
    blogs: List["Blog"] = Relationship(back_populates="category")


# --- User Model ---

class User(TimestampModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True, index=True)
    email: str = Field(unique=True, index=True)
    password: str # Lưu trữ hash của mật khẩu
    full_name: str
    avatar_url: Optional[str] = None
    
    # Quan hệ
    blogs: List["Blog"] = Relationship(back_populates="creator")


# --- Blog Model ---

class Blog(TimestampModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True, index=True)
    title: str
    content: str
    image_url: str

    # Khóa ngoại
    creator_id: Optional[str] = Field(default=None, foreign_key="user.id")
    category_id: Optional[str] = Field(default=None, foreign_key="category.id")

    # Quan hệ
    creator: User = Relationship(back_populates="blogs")
    category: Category = Relationship(back_populates="blogs")