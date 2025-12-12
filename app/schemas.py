from pydantic import BaseModel, Field
from typing import Generic, TypeVar, List, Optional
from datetime import datetime
from enum import Enum

# --- 1. ENUM (Kiểu liệt kê) ---

class CategoryEnum(str, Enum):
    """ Tương ứng với Kotlin enum class CategoryResponse (chỉ tên danh mục) """
    BUSINESS = "business"
    TECHNOLOGY = "technology"
    FASHION = "fashion"
    TRAVEL = "travel"
    FOOD = "food"
    EDUCATION = "education"

# --- 2. Cấu trúc Phản hồi Chung (BaseResponse) ---

T = TypeVar('T')

class BaseResponse(BaseModel, Generic[T]):
    """ Cấu trúc phản hồi chung tương ứng với BaseResponse<T> bên Kotlin. """
    success: bool = Field(..., description="Trạng thái thành công của yêu cầu (true/false)")
    message: str = Field(..., description="Thông báo đi kèm")
    result: Optional[T] = Field(None, description="Dữ liệu chính của phản hồi (data)")

    class Config:
        # Cho phép sử dụng các tên trường (field names) như trong Kotlin
        alias_generator = lambda field_name: {'data': 'result'}.get(field_name, field_name)
        allow_population_by_field_name = True

# --- 3. Schemas Đầu vào (Input Bodies) ---

class LoginUserBody(BaseModel):
    email: str
    password: str

class RegisterUserBody(BaseModel):
    email: str
    password: str = Field(..., min_length=1, description="Mật khẩu người dùng")
    confirmation_password: str = Field(..., min_length=1, description="Xác nhận mật khẩu")
    full_name: str

    class Config:
        # Mapping fields (ví dụ: confirmation_password thay vì confirmationPassword)
        fields = {
            "confirmation_password": "confirmation_password",
            "full_name": "full_name",
        }

# --- 4. Schemas Đầu ra (Output Responses) ---

class UserResponse(BaseModel):
    id: str
    full_name: str
    email: str
    avatar_url: Optional[str] = None
    following: int = Field(0, description="Số người user này đang theo dõi")
    follower: int = Field(0, description="Số người theo dõi user này")

    class Config:
        fields = {
            "full_name": "full_name",
            "avatar_url": "avatar_url",
        }

class CategoryResponse(BaseModel):
    """ Schema phản hồi Category """
    id: str
    name: CategoryEnum # <-- Sử dụng Enum đã định nghĩa

class BlogResponse(BaseModel):
    id: str
    title: str
    content: str
    image_url: str
    category: CategoryResponse
    created_at: datetime
    updated_at: datetime
    creator: UserResponse

    class Config:
        fields = {
            "image_url": "image_url",
            "created_at": "created_at",
            "updated_at": "updated_at",
        }

class LoginUserResponse(BaseModel):
    id: str
    token: str

# --- 5. API Response Wrappers (Sử dụng cho response_model trong routers) ---

LoginResponse = BaseResponse[LoginUserResponse]
RegisterResponse = BaseResponse[dict] # BaseResponse<Any>
BlogListResponse = BaseResponse[List[BlogResponse]]
UserDetailResponse = BaseResponse[UserResponse]