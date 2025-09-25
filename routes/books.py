from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, and_, or_, select
from ..model import Books, UserBookStatus
from common_lib.database import get_session_book_service

router = APIRouter(
    prefix="/books",
    tags=["books"],
)

# -----------------------
# BOOK CRUD
# -----------------------

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
    return book


@router.put('/update/{book_id}', response_model=Books)
def update_book(book_id: int, book_data: Books, session: Session = Depends(get_session_book_service)):
    book = session.get(Books, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail='No book found')
    
    update_fields = ["title", "description", "cover_url", "published_date", "language", "authorID"]
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
    valid_status = ["to_read", "currently_reading", "read", "DNF"]
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
    limit: int = Query(10, le=50),  # mỗi lần load tối đa 50 sách
    session: Session = Depends(get_session_book_service)
):

    subquery = select(UserBookStatus.book_id).where(UserBookStatus.user_id == user_id)

    statement = (
        select(Books)
        .where(Books.id.not_in(subquery))  # chưa có trạng thái
        .offset(offset)
        .limit(limit)
    )

    books = session.exec(statement).all()

    results = [
        {
            "id": book.id,
            "title": book.title,
            "description": book.description,
            "cover_url": book.cover_url,
            "published_date": book.published_date,
            "language": book.language,
            "authorID": book.authorID,
            "categoryID": book.categoryID,
            "status": "to_read"
        }
        for book in books
    ]
    return results
