from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, func, and_, case
from pydantic import BaseModel
from datetime import datetime, date

# Import các model cần thiết
# Đảm bảo import đúng đường dẫn model
from ..model import UserBookStatus, Books, BookClubMember, BookStatus, Category, BookCategoryLink, Authors

from common_lib.database import get_session_book_service

router = APIRouter(
    prefix="/stats",
    tags=["statistics"],
)

# --- Pydantic Models cho Response ---

class ShelfCounts(BaseModel):
    to_read: int = 0
    currently_reading: int = 0
    read: int = 0
    dnf: int = 0

class KpiStatsResponse(BaseModel):
    total_read: int
    total_pages: int
    avg_time_to_finish: float
    read_this_year: int
    favorites_count: int
    clubs_count: int
    shelf_counts: ShelfCounts

class MonthlyReadResponse(BaseModel):
    labels: List[str]
    data: List[int]

class PageDistResponse(BaseModel):
    short: int = 0  # < 300
    medium: int = 0 # 300-499
    long: int = 0   # 500+

class TopItem(BaseModel):
    name: str
    count: int

# --- Helper Function ---

def get_read_records(session: Session, user_id: int):
    """Helper: Lấy tất cả bản ghi 'read' của user."""
    return session.exec(
        select(UserBookStatus).where(
            UserBookStatus.user_id == user_id,
            UserBookStatus.status == BookStatus.read
        )
    ).all()

# --- Endpoints ---

@router.get("/kpis/{user_id}", response_model=KpiStatsResponse)
def get_user_kpis(
    user_id: int,
    session: Session = Depends(get_session_book_service)
):
    # 1. Lấy tất cả bản ghi 'read'
    read_records = get_read_records(session, user_id)
    
    # 2. Tính Tổng sách đã đọc
    total_read = len(read_records)

    # 3. Tính Sách đọc trong năm nay
    current_year = datetime.utcnow().year
    read_this_year = 0
    total_days = 0
    completed_books_with_dates = 0
    
    # Lấy ID các sách đã đọc
    read_book_ids = [record.book_id for record in read_records]

    # 4. Tính Tổng số trang đã đọc
    total_pages = 0
    if read_book_ids:
        total_pages = session.exec(
            select(func.sum(Books.page_count))
            .where(Books.id.in_(read_book_ids))
        ).one_or_none() or 0

    # 5. Tính Thời gian đọc trung bình (từ records)
    for record in read_records:
        # Tính sách đọc năm nay
        if record.updated_at and record.updated_at.year == current_year:
            read_this_year += 1
        
        # Tính thời gian đọc TB
        if record.start_date and record.finish_date:
            # Đảm bảo cả hai đều là 'date', không phải 'datetime'
            start_date_obj = record.start_date
            finish_date_obj = record.finish_date
            
            if isinstance(start_date_obj, datetime):
                start_date_obj = start_date_obj.date()
            if isinstance(finish_date_obj, datetime):
                finish_date_obj = finish_date_obj.date()

            if start_date_obj and finish_date_obj:
                days_diff = (finish_date_obj - start_date_obj).days
                if days_diff >= 0: # Chỉ tính nếu ngày hợp lệ
                    total_days += days_diff
                    completed_books_with_dates += 1

    avg_time_to_finish = (total_days / completed_books_with_dates) if completed_books_with_dates > 0 else 0.0

    # 6. Đếm số sách yêu thích
    favorites_count = session.exec(
        select(func.count(UserBookStatus.id))
        .where(
            UserBookStatus.user_id == user_id,
            UserBookStatus.is_favorite == True
        )
    ).one_or_none() or 0

    # 7. Đếm số CLB đã tham gia
    clubs_count = session.exec(
        select(func.count(BookClubMember.id))
        .where(BookClubMember.user_id == user_id)
    ).one_or_none() or 0

    # 8. Đếm phân bổ các kệ sách
    shelf_counts_query = session.exec(
        select(UserBookStatus.status, func.count(UserBookStatus.id))
        .where(UserBookStatus.user_id == user_id)
        .group_by(UserBookStatus.status)
    ).all()
    
    shelf_counts = ShelfCounts()
    for status, count in shelf_counts_query:
        if status == BookStatus.to_read:
            shelf_counts.to_read = count
        elif status == BookStatus.currently_reading:
            shelf_counts.currently_reading = count
        elif status == BookStatus.read:
            shelf_counts.read = count
        elif status == BookStatus.did_not_finish:
            shelf_counts.dnf = count

    return KpiStatsResponse(
        total_read=total_read,
        total_pages=total_pages,
        avg_time_to_finish=avg_time_to_finish,
        read_this_year=read_this_year,
        favorites_count=favorites_count,
        clubs_count=clubs_count,
        shelf_counts=shelf_counts
    )

@router.get("/read-by-month/{user_id}", response_model=MonthlyReadResponse)
def get_read_by_month(
    user_id: int,
    year: int = Query(default_factory=lambda: datetime.utcnow().year),
    session: Session = Depends(get_session_book_service)
):
    stmt = (
        select(
            func.extract('month', UserBookStatus.updated_at).label('month'),
            func.count(UserBookStatus.id).label('count')
        )
        .where(
            UserBookStatus.user_id == user_id,
            UserBookStatus.status == BookStatus.read,
            func.extract('year', UserBookStatus.updated_at) == year
        )
        .group_by(func.extract('month', UserBookStatus.updated_at))
    )
    
    results = session.exec(stmt).all() # Kết quả: [(1, 5), (3, 2), (11, 8)]
    
    # Khởi tạo 12 tháng với 0
    monthly_counts = [0] * 12 
    
    for month, count in results:
        if 1 <= month <= 12:
            monthly_counts[int(month) - 1] = count # month 1 là index 0

    return MonthlyReadResponse(
        labels=['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8', 'T9', 'T10', 'T11', 'T12'],
        data=monthly_counts
    )

@router.get("/page-distribution/{user_id}", response_model=PageDistResponse)
def get_page_distribution(
    user_id: int,
    session: Session = Depends(get_session_book_service)
):
    # Lấy ID các sách đã đọc
    read_records = get_read_records(session, user_id)
    read_book_ids = [record.book_id for record in read_records]

    if not read_book_ids:
        return PageDistResponse()

    # Phân nhóm bằng CASE WHEN trong SQL
    stmt = (
        select(
            func.sum(case((Books.page_count < 300, 1), else_=0)).label('short'),
            func.sum(case((and_(Books.page_count >= 300, Books.page_count < 500), 1), else_=0)).label('medium'),
            func.sum(case((Books.page_count >= 500, 1), else_=0)).label('long')
        )
        .where(Books.id.in_(read_book_ids))
    )
    
    result = session.exec(stmt).one_or_none()

    if not result:
        return PageDistResponse()

    return PageDistResponse(
        short=result[0] or 0,
        medium=result[1] or 0,
        long=result[2] or 0
    )

@router.get("/top-categories/{user_id}", response_model=List[TopItem])
def get_top_categories(
    user_id: int,
    limit: int = 5,
    session: Session = Depends(get_session_book_service)
):
    stmt = (
        select(
            Category.name,
            func.count(Category.id).label('count')
        )
        .join(BookCategoryLink, Category.id == BookCategoryLink.category_id)
        .join(UserBookStatus, BookCategoryLink.book_id == UserBookStatus.book_id)
        .where(
            UserBookStatus.user_id == user_id,
            UserBookStatus.status == BookStatus.read
        )
        .group_by(Category.name)
        .order_by(func.count(Category.id).desc())
        .limit(limit)
    )
    
    results = session.exec(stmt).all()
    return [TopItem(name=name, count=count) for name, count in results]

@router.get("/top-authors/{user_id}", response_model=List[TopItem])
def get_top_authors(
    user_id: int,
    limit: int = 5,
    session: Session = Depends(get_session_book_service)
):
    stmt = (
        select(
            Authors.name,
            func.count(Authors.id).label('count')
        )
        # SỬA LỖI Ở ĐÂY: Thêm .select_from() để chỉ định bảng bắt đầu
        .select_from(UserBookStatus)
        # Bắt đầu từ UserBookStatus
        .join(Books, UserBookStatus.book_id == Books.id)
        .join(Authors, Books.authorID == Authors.id) # authorID là FK
        .where(
            UserBookStatus.user_id == user_id,
            UserBookStatus.status == BookStatus.read,
            Authors.name != None # Bỏ qua tác giả không tên
        )
        .group_by(Authors.name)
        .order_by(func.count(Authors.id).desc())
        .limit(limit)
    )
    
    results = session.exec(stmt).all()
    return [TopItem(name=name, count=count) for name, count in results]