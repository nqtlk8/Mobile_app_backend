from fastapi import APIRouter, Depends, Query, Path, HTTPException, status
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from typing import List, Any
import uuid
from datetime import datetime

from app.database import get_session
from app.models import Blog, User, Category
from app.schemas import (
    BlogListResponse, 
    UserDetailResponse, 
    BlogResponse, 
    UserResponse,
    CreateBlogBody,
    UpsertBlogBody,
    UpdateBlogBody,
    BlogDetailResponse,
    CategoryEnum,
    CategoryResponse
)
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
    Mỗi blog bao gồm thông tin tác giả (creator) và danh mục (category).
    """
    offset = (page - 1) * limit
    
    # 1. Truy vấn Blogs từ DB với LIMIT và OFFSET, eager load relationships
    statement = (
        select(Blog)
        .options(selectinload(Blog.creator), selectinload(Blog.category))
        .offset(offset)
        .limit(limit)
        .order_by(Blog.created_at.desc())  # Sắp xếp theo thời gian tạo mới nhất
    )
    blogs_model = db.exec(statement).all()

    # 2. Chuyển đổi List[Blog] Model sang List[BlogResponse] Schema
    blogs_response: List[BlogResponse] = []
    for blog in blogs_model:
        # Đảm bảo relationships đã được load
        if not blog.creator:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Không tìm thấy thông tin tác giả cho blog {blog.id}"
            )
        if not blog.category:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Không tìm thấy thông tin danh mục cho blog {blog.id}"
            )
        
        # Tạo UserResponse với thông tin creator
        creator_response = UserResponse(
            id=str(blog.creator.id),
            full_name=blog.creator.full_name,
            email=blog.creator.email,
            following=15,  # Cần tính toán hoặc giả lập
            follower=80    # Cần tính toán hoặc giả lập
        )
        
        # Tạo CategoryResponse object với id và name
        category_response = CategoryResponse(
            id=str(blog.category.id),
            name=blog.category.name
        )
        
        blogs_response.append(BlogResponse(
            id=str(blog.id),
            title=blog.title,
            content=blog.content,
            image_url=blog.image_url,
            category=category_response,  # Trả về CategoryResponse object
            created_at=blog.created_at,  # Pydantic tự động format ISO 8601
            updated_at=blog.updated_at,  # Pydantic tự động format ISO 8601
            creator=creator_response,
        ))

    # 3. Trả về phản hồi đã đóng gói theo định dạng BaseResponse<List<BlogResponse>>
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
    Trả về thông tin chi tiết (profile) của người dùng theo ID.
    Bao gồm thông tin cơ bản và số lượng following/follower.
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
        id=str(user_model.id),
        full_name=user_model.full_name,
        email=user_model.email,
        avatar_url=user_model.avatar_url,
        following=15,  # Cần tính toán hoặc giả lập
        follower=80,    # Cần tính toán hoặc giả lập
    )
    
    # 3. Trả về phản hồi đã đóng gói theo định dạng BaseResponse<UserResponse>
    return {
        "success": True,
        "message": "Lấy thông tin người dùng thành công.",
        "result": user_response,
    }


@router.post(
    "/api/blogs",
    response_model=BlogDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tạo blog mới"
)
async def create_blog(
    body: UpsertBlogBody,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
) -> dict[str, Any]:
    """
    Tạo một blog mới. Người dùng đăng nhập sẽ là creator của blog.
    Nhận category như một object CategoryResponse với id và name.
    """
    # 1. Tìm category theo id hoặc name từ body.category
    # Ưu tiên tìm theo id nếu có và hợp lệ, nếu không thì tìm theo name
    category = None
    if body.category.id and body.category.id.strip():
        category = db.get(Category, body.category.id)
    
    if not category and body.category.name:
        category = db.exec(
            select(Category).where(Category.name == body.category.name)
        ).first()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Danh mục không tồn tại. ID: {body.category.id}, Name: {body.category.name}"
        )
    
    # 2. Tạo blog mới
    new_blog = Blog(
        id=str(uuid.uuid4()),
        title=body.title,
        content=body.content,
        image_url=body.image_url,
        creator_id=str(current_user.id),
        category_id=str(category.id),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # 3. Lưu vào database
    db.add(new_blog)
    db.commit()
    db.refresh(new_blog)
    
    # 4. Load relationships để trả về đầy đủ thông tin
    db.refresh(new_blog, ["creator", "category"])
    
    # 5. Tạo response
    creator_response = UserResponse(
        id=str(new_blog.creator.id),
        full_name=new_blog.creator.full_name,
        email=new_blog.creator.email,
        following=15,  # Cần tính toán hoặc giả lập
        follower=80    # Cần tính toán hoặc giả lập
    )
    
    # Tạo CategoryResponse object
    category_response = CategoryResponse(
        id=str(new_blog.category.id),
        name=new_blog.category.name
    )
    
    blog_response = BlogResponse(
        id=str(new_blog.id),
        title=new_blog.title,
        content=new_blog.content,
        image_url=new_blog.image_url,
        category=category_response,  # CategoryResponse object
        created_at=new_blog.created_at,
        updated_at=new_blog.updated_at,
        creator=creator_response,
    )
    
    return {
        "success": True,
        "message": "Tạo blog thành công.",
        "result": blog_response,
    }


@router.put(
    "/api/blogs/{id}",
    response_model=BlogDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Cập nhật blog theo ID"
)
async def update_blog(
    id: str = Path(..., description="ID của blog cần cập nhật"),
    body: UpsertBlogBody = ...,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
) -> dict[str, Any]:
    """
    Cập nhật thông tin blog. Chỉ người tạo blog mới có quyền cập nhật.
    Nhận category như một object CategoryResponse với id và name.
    """
    # 1. Tìm blog theo ID và load relationships
    blog = db.exec(
        select(Blog)
        .options(selectinload(Blog.creator), selectinload(Blog.category))
        .where(Blog.id == id)
    ).first()
    
    if not blog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Blog không tồn tại."
        )
    
    # 2. Kiểm tra quyền: chỉ creator mới được cập nhật
    if str(blog.creator_id) != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền cập nhật blog này."
        )
    
    # 3. Tìm category theo id hoặc name từ body.category
    # Ưu tiên tìm theo id nếu có và hợp lệ, nếu không thì tìm theo name
    category = None
    if body.category.id and body.category.id.strip():
        category = db.get(Category, body.category.id)
    
    if not category and body.category.name:
        category = db.exec(
            select(Category).where(Category.name == body.category.name)
        ).first()
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Danh mục không tồn tại. ID: {body.category.id}, Name: {body.category.name}"
        )
    
    # 4. Cập nhật các trường từ body (tất cả đều required trong UpsertBlogBody)
    blog.title = body.title
    blog.content = body.content
    blog.image_url = body.image_url
    blog.category_id = str(category.id)
    
    # 5. Cập nhật updated_at
    blog.updated_at = datetime.utcnow()
    
    # 6. Refresh để load category mới
    db.refresh(blog, ["category"])
    
    # 7. Lưu vào database
    db.add(blog)
    db.commit()
    db.refresh(blog, ["creator", "category"])
    
    # 8. Tạo response
    creator_response = UserResponse(
        id=str(blog.creator.id),
        full_name=blog.creator.full_name,
        email=blog.creator.email,
        following=15,  # Cần tính toán hoặc giả lập
        follower=80    # Cần tính toán hoặc giả lập
    )
    
    # Tạo CategoryResponse object
    category_response = CategoryResponse(
        id=str(blog.category.id),
        name=blog.category.name
    )
    
    blog_response = BlogResponse(
        id=str(blog.id),
        title=blog.title,
        content=blog.content,
        image_url=blog.image_url,
        category=category_response,  # CategoryResponse object
        created_at=blog.created_at,
        updated_at=blog.updated_at,
        creator=creator_response,
    )
    
    return {
        "success": True,
        "message": "Cập nhật blog thành công.",
        "result": blog_response,
    }