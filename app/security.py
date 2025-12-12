from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, select

from app.config import settings
from app.database import get_session
from app.models import User

# Cấu hình password hashing
# Sử dụng bcrypt_sha256 làm scheme chính để tránh giới hạn 72 bytes
# bcrypt_sha256 sẽ hash password bằng SHA256 trước, sau đó mới pass vào bcrypt
# Vẫn hỗ trợ bcrypt để tương thích với password cũ (nếu có)
# Tắt bug detection để tránh lỗi khi khởi tạo
pwd_context = CryptContext(
    schemes=["bcrypt_sha256", "bcrypt"], 
    deprecated="auto",
    bcrypt__ident="2b"  # Sử dụng bcrypt version 2b
)

# HTTPBearer để lấy token từ header Authorization
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Xác thực mật khẩu plain text với mật khẩu đã được hash.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash mật khẩu bằng bcrypt_sha256.
    bcrypt_sha256 sẽ hash password bằng SHA256 trước, sau đó mới pass vào bcrypt,
    điều này giải quyết giới hạn 72 bytes của bcrypt.
    """
    # Đảm bảo password là string
    if not isinstance(password, str):
        raise ValueError(f"Password phải là string, nhận được: {type(password)}")
    
    # Đảm bảo password không rỗng
    if not password:
        raise ValueError("Password không được rỗng")
    
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Tạo JWT access token.
    
    Args:
        data: Dictionary chứa thông tin để encode vào token (thường là user_id)
        expires_delta: Thời gian hết hạn tùy chỉnh. Nếu None, dùng giá trị mặc định từ config.
    
    Returns:
        JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Giải mã JWT token và trả về payload.
    
    Args:
        token: JWT token string
    
    Returns:
        Dictionary chứa payload nếu thành công, None nếu lỗi
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_session)
) -> User:
    """
    Dependency function để lấy user hiện tại từ JWT token.
    
    Hàm này:
    1. Lấy token từ header Authorization: Bearer <token>
    2. Giải mã token để lấy user_id
    3. Tìm user trong database
    4. Trả về user nếu thành công, ném HTTPException nếu lỗi
    
    Args:
        credentials: HTTPAuthorizationCredentials từ HTTPBearer dependency
        db: Database session
    
    Returns:
        User object
    
    Raises:
        HTTPException: 401 Unauthorized nếu token không hợp lệ hoặc user không tồn tại
    """
    token = credentials.credentials
    
    # Giải mã token
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ hoặc đã hết hạn.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Lấy user_id từ payload (thường là key "sub" trong JWT)
    user_id: Optional[str] = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token không hợp lệ.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Tìm user trong database
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Người dùng không tồn tại.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

