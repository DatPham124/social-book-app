from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, func
from sqlalchemy import and_, or_, extract, distinct
from typing import List, Optional
from pydantic import BaseModel

# Import các model bạn cần từ file model.py
from ..model import Books, Category, BookCategoryLink, UserBookStatus
from common_lib.database import get_session_book_service

router = APIRouter(
    prefix="/filter",
    tags=["filter"],
)

# 1. Định nghĩa model cho bộ lọc (JSON body)
class FilterBody(BaseModel):
    genres_include: Optional[List[str]] = None
    genres_exclude: Optional[List[str]] = None
    page_min: Optional[int] = None
    page_max: Optional[int] = None
    year_min: Optional[int] = None
    year_max: Optional[int] = None
    user_id_to_exclude_books: Optional[int] = None

# 2. Định nghĩa model cho dữ liệu trả về (để thêm categories)
# (Frontend của bạn cần 'categories' là một danh sách string)
class BookWithDetails(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    cover_url: Optional[str] = None
    published_date: Optional[date] = None
    language: Optional[str] = None
    page_count: Optional[int] = None  
    authorID: Optional[int] = None
    created_at: date
    categories: List[str] = [] # <-- Quan trọng

# 3. API Lọc Nâng cao
@router.post("/books", response_model=List[BookWithDetails])
def filter_books(
    filters: FilterBody,
    session: Session = Depends(get_session_book_service)
):
    # Dùng distinct() để tránh lặp sách khi JOIN thể loại
    statement = select(Books).distinct() 
    
    # 1. Lọc Sách đã đọc (Exclude)
    if filters.user_id_to_exclude_books:
        subquery = (
            select(UserBookStatus.book_id)
            .where(UserBookStatus.user_id == filters.user_id_to_exclude_books)
        )
        statement = statement.where(Books.id.not_in(subquery))

    # 2. Lọc Thể loại (Include)
    if filters.genres_include:
        # JOIN và lọc
        statement = statement.join(
            BookCategoryLink, BookCategoryLink.book_id == Books.id
        ).join(Category).where(
            Category.name.in_(filters.genres_include)
        )
        
    # 3. Lọc Thể loại (Exclude)
    if filters.genres_exclude:
        # Dùng subquery để tìm các sách CÓ thể loại bị cấm
        exclude_subquery = (
            select(BookCategoryLink.book_id)
            .join(Category)
            .where(Category.name.in_(filters.genres_exclude))
        )
        # Lọc ra các sách KHÔNG CÓ ID trong danh sách cấm
        statement = statement.where(Books.id.not_in(exclude_subquery))

    # 4. Lọc Số trang (Pages)
    if filters.page_min is not None:
        statement = statement.where(Books.page_count >= filters.page_min)
    if filters.page_max is not None:
        statement = statement.where(Books.page_count <= filters.page_max)

    # 5. Lọc Năm (Year)
    if filters.year_min is not None:
        # Dùng 'extract' của SQLAlchemy để lấy 'năm' từ 'date'
        statement = statement.where(extract('year', Books.published_date) >= filters.year_min)
    if filters.year_max is not None:
        statement = statement.where(extract('year', Books.published_date) <= filters.year_max)

    # Giới hạn kết quả
    statement = statement.limit(50)
    
    books = session.exec(statement).all()
    
    # 6. Gộp categories vào (Frontend đang mong đợi 'categories' là List[str])
    results_with_categories = []
    for book in books:
        # Lấy category names (giống hệt API 'explore' của bạn)
        category_names = [cat.name for cat in book.categories] if book.categories else []
        
        # Tạo đối tượng trả về
        book_data = BookWithDetails(
            id=book.id,
            title=book.title,
            description=book.description,
            cover_url=book.cover_url,
            published_date=book.published_date,
            language=book.language,
            page_count=book.page_count,
            authorID=book.authorID,
            created_at=book.created_at,
            categories=category_names # Gán danh sách tên thể loại
        )
        results_with_categories.append(book_data)

    return results_with_categories

