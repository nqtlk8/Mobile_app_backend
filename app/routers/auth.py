from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import Any

from app.database import get_session
from app.models import User
from app.schemas import (
    LoginUserBody, RegisterUserBody, 
    LoginResponse, RegisterResponse, 
    LoginUserResponse
)
from app.security import (
    create_access_token
)

router = APIRouter(tags=["Auth"])

@router.post(
    "/api/auth/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Đăng nhập người dùng"
)
async def login(
    body: LoginUserBody, 
    db: Session = Depends(get_session)
) -> dict[str, Any]:
    """
    Xử lý đăng nhập, trả về token và thông tin người dùng.
    """
    # 1. Lấy user từ DB dựa trên email
    user = db.exec(select(User).where(User.email == body.email)).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không đúng."
        )

    # 2. Xử lý xác thực mật khẩu (demo: so sánh plain text)
    if body.password != user.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không đúng."
        )

    # 3. Tạo JWT Token
    access_token = create_access_token(data={"sub": user.id})

    # 4. Trả về phản hồi đã đóng gói
    return {
        "success": True,
        "message": "Đăng nhập thành công.",
        "result": LoginUserResponse(id=user.id, token=access_token),
    }

@router.post(
    "/api/auth/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Đăng ký người dùng mới"
)
async def register(
    body: RegisterUserBody, 
    db: Session = Depends(get_session)
) -> dict[str, Any]:
    """
    Xử lý đăng ký người dùng mới.
    """
    # 1. Kiểm tra mật khẩu xác nhận
    if body.password != body.confirmation_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mật khẩu xác nhận không khớp."
        )
        
    # 2. Kiểm tra email đã tồn tại chưa
    existing_user = db.exec(select(User).where(User.email == body.email)).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email đã được đăng ký."
        )

    # 3. Tạo User Model mới với mật khẩu plain text (demo only - không hash)
    new_user = User(
        id=f"user_{body.email.split('@')[0]}", # Giả lập UUID
        email=body.email,
        password=body.password, # Lưu plain text cho demo
        full_name=body.full_name,
    )

    # 4. Lưu vào DB
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 5. Trả về phản hồi thành công (BaseResponse<Any> -> BaseResponse<dict>)
    return {
        "success": True,
        "message": "Đăng ký thành công.",
        "result": {"user_id": new_user.id},
    }