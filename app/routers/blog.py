from fastapi import APIRouter, Depends, Query, Path, HTTPException, status
from sqlmodel import Session, select
from typing import List, Any

from app.database import get_session
from app.models import Blog, User, Category
from app.schemas import BlogListResponse, UserDetailResponse, BlogResponse, UserResponse, CategoryResponse
from app.security import get_current_user

router = APIRouter(tags=["Blogs", "Users"])


@router.get(
    "/api/blogs",
    response_model=BlogListResponse,
    status_code=status.HTTP_200_OK,
    summary="Lấy danh sách Blogs theo phân trang"
)
async def get_blogs(
    limit: int = Query(20, description="Số lượng bài viết trên mỗi trang"),
    page: int = Query(1, description="Số trang hiện tại"),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user) # Yêu cầu xác thực
) -> dict[str, Any]:
    """
    Trả về danh sách các bài blog, hỗ trợ phân trang (limit và page).
    """
    offset = (page - 1) * limit
    
    # 1. Truy vấn Blogs từ DB với LIMIT và OFFSET
    blogs_model = db.exec(
        select(Blog).offset(offset).limit(limit)
    ).all()

    # 2. Chuyển đổi List[Blog] Model sang List[BlogResponse] Schema
    blogs_response: List[BlogResponse] = []
    for blog in blogs_model:
        # Giả lập tạo các response lồng nhau
        creator_response = UserResponse(
            id=blog.creator.id, full_name=blog.creator.full_name, email=blog.creator.email, following=0, follower=0
        )
        category_response = CategoryResponse(id=blog.category.id, name=blog.category.name)
        
        blogs_response.append(BlogResponse(
            id=blog.id,
            title=blog.title,
            content=blog.content,
            image_url=blog.image_url,
            category=category_response,
            created_at=blog.created_at,
            updated_at=blog.updated_at,
            creator=creator_response,
        ))

    # 3. Trả về phản hồi đã đóng gói
    return {
        "success": True,
        "message": f"Lấy thành công {len(blogs_response)} bài blog.",
        "result": blogs_response,
    }


@router.get(
    "/api/users/{id}/profiles",
    response_model=UserDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Lấy thông tin chi tiết người dùng theo ID"
)
async def get_user_by_id(
    id: str = Path(..., description="ID của người dùng cần lấy profile"),
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user) # Yêu cầu xác thực
) -> dict[str, Any]:
    """
    Trả về thông tin chi tiết (profile) của người dùng.
    """
    # 1. Truy vấn User từ DB theo ID
    user_model = db.get(User, id)

    if not user_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Người dùng không tồn tại."
        )

    # 2. Chuyển đổi User Model sang UserResponse Schema
    user_response = UserResponse(
        id=user_model.id,
        full_name=user_model.full_name,
        email=user_model.email,
        avatar_url=user_model.avatar_url,
        following=15, # Giả lập
        follower=80, # Giả lập
    )
    
    # 3. Trả về phản hồi đã đóng gói
    return {
        "success": True,
        "message": "Lấy thông tin người dùng thành công.",
        "result": user_response,
    }