from typing import List, Optional, Literal
from pydantic import BaseModel
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlmodel import Session, select

from ..model import BookQuote, BookQuoteLike
from common_lib.database import get_session_book_service

router = APIRouter(tags=["quotes"])

# DTOs
class QuoteCreateRequest(BaseModel):
    book_id: int
    content: str

class QuoteResponse(BaseModel):
    id: int
    content: str
    user_id: int
    user_name: str
    like_count: int
    is_liked: bool
    created_at: datetime

# 1. API Lấy danh sách (Đã nâng cấp Pagination + Sorting)
@router.get("/books/{book_id}/quotes", response_model=List[QuoteResponse])
def get_quotes(
    book_id: int, 
    current_user_id: Optional[int] = None,
    page: int = Query(1, ge=1),      # Trang số mấy (mặc định 1)
    limit: int = Query(5, ge=1, le=50), # Số lượng mỗi lần tải (mặc định 5)
    sort_by: Literal["newest", "top"] = "top", # Chế độ sắp xếp
    session: Session = Depends(get_session_book_service)
):
    offset = (page - 1) * limit
    
    # Tạo query cơ bản
    statement = select(BookQuote).where(BookQuote.book_id == book_id)
    
    # Xử lý Sắp xếp
    if sort_by == "top":
        # Ưu tiên like nhiều nhất, nếu bằng nhau thì mới nhất lên trước
        statement = statement.order_by(BookQuote.like_count.desc(), BookQuote.created_at.desc())
    else:
        # Mới nhất
        statement = statement.order_by(BookQuote.created_at.desc())
        
    # Áp dụng phân trang
    statement = statement.offset(offset).limit(limit)
    
    quotes = session.exec(statement).all()
    
    results = []
    for quote in quotes:
        # Kiểm tra đã like chưa (Logic cũ)
        liked_by_me = False
        if current_user_id:
            for like_record in quote.likes:
                if like_record.user_id == current_user_id:
                    liked_by_me = True
                    break
        
        results.append(QuoteResponse(
            id=quote.id,
            content=quote.content,
            user_id=quote.user_id,
            user_name=f"User {quote.user_id}", 
            like_count=quote.like_count, # Lấy trực tiếp từ cột mới
            is_liked=liked_by_me,
            created_at=quote.created_at
        ))
        
    return results

# 2. Tạo Quote (Giữ nguyên)
@router.post("/quotes")
def create_quote(
    request: QuoteCreateRequest,
    current_user_id: int = Body(..., embed=True),
    session: Session = Depends(get_session_book_service)
):
    new_quote = BookQuote(
        book_id=request.book_id,
        content=request.content,
        user_id=current_user_id
    )
    session.add(new_quote)
    session.commit()
    session.refresh(new_quote)
    
    return {
        "id": new_quote.id,
        "content": new_quote.content,
        "like_count": 0,
        "is_liked": False,
        "created_at": new_quote.created_at
    }

# 3. Toggle Like (Cập nhật để tăng/giảm like_count)
@router.post("/quotes/{quote_id}/like")
def toggle_like(
    quote_id: int,
    current_user_id: int = Body(..., embed=True),
    session: Session = Depends(get_session_book_service)
):
    quote = session.get(BookQuote, quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")

    statement = select(BookQuoteLike).where(
        BookQuoteLike.quote_id == quote_id,
        BookQuoteLike.user_id == current_user_id
    )
    existing_like = session.exec(statement).first()
    
    if existing_like:
        # UNLIKE: Xóa record like và Giảm count
        session.delete(existing_like)
        quote.like_count = max(0, quote.like_count - 1) # Tránh âm
        session.add(quote)
        session.commit()
        return {"message": "Unliked", "status": False}
    else:
        # LIKE: Thêm record like và Tăng count
        new_like = BookQuoteLike(quote_id=quote_id, user_id=current_user_id)
        session.add(new_like)
        quote.like_count += 1
        session.add(quote)
        session.commit()
        return {"message": "Liked", "status": True}