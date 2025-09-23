from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from ..model import Books
from common_lib.database import get_session_book_service

router = APIRouter(
    prefix="/books",
    tags=["books"],
)

@router.post('/add', response_model= Books)
def add_book(book: Books ,session: Session = Depends(get_session_book_service)):
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


@router.put('/update/{bookID}', response_model=Books)
def update_book( bookID: int, book_data: Books, session: Session = Depends(get_session_book_service)):
    book = session.get(Books, bookID)

    if book is None:
        raise HTTPException(
            status_code=400, detail= 'No book found'
        )
    
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
        raise HTTPException(
            status_code=404, detail="Book not found"
        )
    
    session.delete(book)
    session.commit()

    return {f"Book with id {book_id} has been deleted"}
