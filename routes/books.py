from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, and_, or_, select
from ..model import Books, Category, ReadingProgress, UserBookStatus, BookCategoryLink
from common_lib.database import get_session_book_service

router = APIRouter(
    prefix="/books",
    tags=["books"],
)

@router.post('/add', response_model=Books)
def add_book(book: Books, session: Session = Depends(get_session_book_service)):
    session.add(book)
    session.commit()
    session.refresh(book)
    return book


@router.get("/", response_model=list[Books])
def get_all_books(session: Session = Depends(get_session_book_service)):
    statement = select(Books)
    books = session.exec(statement).all()
    return books


@router.get("/{book_id}", response_model=Books)
def get_book_by_id(book_id: int, session: Session = Depends(get_session_book_service)):
    book = session.get(Books, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # lấy categories
    stmt = (
        select(Category)
        .join(BookCategoryLink, BookCategoryLink.category_id == Category.id)
        .where(BookCategoryLink.book_id == book.id)
    )
    categories = session.exec(stmt).all()

    return book

@router.put('/update/{book_id}', response_model=Books)
def update_book(book_id: int, book_data: Books, session: Session = Depends(get_session_book_service)):
    book = session.get(Books, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail='No book found')
    
    update_fields = ["title", "description", "cover_url", "published_date", "language", "authorID", "page_count"]
    for field in update_fields:
        value = getattr(book_data, field)
        if value is not None:
            setattr(book, field, value)

    session.add(book)
    session.commit()
    session.refresh(book)
    return book


@router.delete('/delete/{book_id}')
def delete_book_by_id(book_id: int, session: Session = Depends(get_session_book_service)):  
    book = session.get(Books, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    
    session.delete(book)
    session.commit()
    return {"message": f"Book with id {book_id} has been deleted"}


# -----------------------
# BOOK STATUS
# -----------------------

@router.get('/status/all', response_model=list[UserBookStatus])
def get_all_status_books(session: Session = Depends(get_session_book_service)):
    statement = select(UserBookStatus)
    status = session.exec(statement).all()
    return status


@router.post('/status/add')
def add_book_status(status_change: str, book_id: int, user_id: int, session: Session = Depends(get_session_book_service)):
    valid_status = ["to_read", "currently_reading", "read", "dnf"]
    if status_change not in valid_status:
        raise HTTPException(status_code=400, detail="Trạng thái không hợp lệ")

    new_status = UserBookStatus(
        user_id=user_id,
        book_id=book_id,
        status=status_change
    )
    session.add(new_status)
    session.commit()
    session.refresh(new_status)
    return {"message": "Book status added successfully"}

@router.get('/status/book/{user_id}', response_model=list[UserBookStatus])
def get_book_by_status_and_userID(
    status: str,
    user_id: int,  
    session: Session = Depends(get_session_book_service)
):
    valid_status = ["to_read", "currently_reading", "read", "dnf"]
    if status not in valid_status:
        raise HTTPException(
            status_code=400,
            detail=f"Trạng thái không hợp lệ. Hợp lệ: {', '.join(valid_status)}"
        )

    statement = select(UserBookStatus).where(
        and_(
            UserBookStatus.status == status,
            UserBookStatus.user_id == user_id
        )
    )
    results = session.exec(statement).all()

    if not results:
        raise HTTPException(
            status_code=404,
            detail=f"Không tìm thấy sách với trạng thái '{status}' cho user_id={user_id}"
        )

    return results


@router.put('/{book_id}/status')
def update_user_book_status(
    book_id: int,
    user_id: int,
    status: str,
    session: Session = Depends(get_session_book_service)
):
    valid_status = ["to_read", "currently_reading", "read", "dnf"]
    if status not in valid_status:
        raise HTTPException(status_code=400, detail="Trạng thái không hợp lệ")

    # Kiểm tra xem bản ghi có tồn tại chưa
    statement = select(UserBookStatus).where(
        and_(
            UserBookStatus.book_id == book_id,
            UserBookStatus.user_id == user_id
        )
    )
    book_status = session.exec(statement).first()

    if not book_status:
        book_status = UserBookStatus(
            user_id=user_id,
            book_id=book_id,
            status=status
        )
        session.add(book_status)
    else:
        book_status.status = status
        session.add(book_status)

    session.commit()
    session.refresh(book_status)

    return {"message": "✅ Book status updated", "status": book_status.status}

@router.get("/explore/{user_id}")
def get_explore_books(
    user_id: int,
    offset: int = Query(0, ge=0),
    limit: int = Query(10, le=50),
    session: Session = Depends(get_session_book_service)
):
    subquery = select(UserBookStatus.book_id).where(UserBookStatus.user_id == user_id)

    statement = (
        select(Books)
        .where(Books.id.not_in(subquery))
        .offset(offset)
        .limit(limit)
    )

    books = session.exec(statement).all()

    results = []
    for book in books:
        # Lấy category names
        category_names = [cat.name for cat in book.categories] if book.categories else []
        
        results.append({
            "id": book.id,
            "title": book.title,
            "description": book.description,
            "cover_url": book.cover_url,
            "published_date": book.published_date,
            "language": book.language,
            "authorID": book.authorID,
            "categories": category_names,  # Trả về mảng categories
            "status": "to_read"
        })
    
    return results


@router.get("/{book_id}/categories", response_model=List[Category])
def get_book_categories(book_id: int, session: Session = Depends(get_session_book_service)):
    book = session.get(Books, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    return book.categories

# Thêm vào routes books.py

@router.get("/reading-progress/{user_id}/{book_id}")
def get_reading_progress(
    user_id: int,
    book_id: int,
    session: Session = Depends(get_session_book_service)
):
    statement = select(ReadingProgress).where(
        and_(
            ReadingProgress.user_id == user_id,
            ReadingProgress.book_id == book_id
        )
    )
    progress = session.exec(statement).first()
    
    if not progress:
        # Nếu chưa có tiến độ, trả về mặc định
        book = session.get(Books, book_id)
        return {
            "user_id": user_id,
            "book_id": book_id,
            "current_page": 0,
            "total_pages": book.page_count if book else 0
        }
    
    return progress

@router.put("/reading-progress/{user_id}/{book_id}")
def update_reading_progress(
    user_id: int,
    book_id: int,
    current_page_from_user: int,
    session: Session = Depends(get_session_book_service)
):
    
       # Lấy sách từ DB
    book = session.get(Books, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Kiểm tra số trang
    if current_page_from_user > book.page_count:
        raise HTTPException(status_code=400, detail="Số trang vượt quá số trang thực tế")

    statement = select(ReadingProgress).where(
        and_(
            ReadingProgress.user_id == user_id,
            ReadingProgress.book_id == book_id
        )
    )
    progress = session.exec(statement).first()

    if not progress:
        progress = ReadingProgress(
            user_id=user_id,
            book_id=book_id,
            current_page=current_page_from_user    
        )
    else:
        progress.current_page = current_page_from_user
        
    session.add(progress)
    session.commit()
    session.refresh(progress)
    
    return progress

