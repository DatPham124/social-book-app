from ..model import Authors
from sqlmodel import Session, select
from fastapi import APIRouter, Depends, HTTPException
from common_lib.database import get_session_book_service


router = APIRouter(
    prefix="/author",
    tags=["author"]
)

@router.post("/add")
def add_author(author: Authors, session: Session = Depends(get_session_book_service)):
    session.add(author)
    session.commit()
    session.refresh(author)
    return {"Author add complete"}

@router.get("/", response_model=list[Authors])
def get_all(session: Session = Depends(get_session_book_service)):
    statement = select(Authors)
    authors = session.exec(statement).all()

    if authors is None:
        raise HTTPException(
            status_code=404,
            detail="No authors"
        )
    
    return authors

@router.get("/{author_id}", response_model=Authors)
def get_all(author_id: int, session: Session = Depends(get_session_book_service)):
    author =  session.get(Authors, author_id)

    if author is None:
        raise HTTPException(
            status_code=404,
            detail="No authors"
        )
    
    return author

@router.put("/update/{author_id}", response_model=Authors)
def update_author(author_id: int, author_data: Authors, session: Session = Depends(get_session_book_service)):
    author = session.get(Authors, author_id)

    if author is None:
        raise HTTPException(
            status_code=404,
            detail="author not found"
        )
    
    author_field = ["name", "bio", "birth_date"]

    for field in author_field:
        value = getattr(author_data, field)

        if value is not None:
            setattr(author, field, value)

    session.add(author)
    session.commit()
    session.refresh(author)

    return author

@router.delete('/delete/{author_id}')
def delete_author(author_id: int, session: Session = Depends(get_session_book_service)):
    author  = session.get(Authors, author_id)

    if author is None:
        raise HTTPException(
            status_code=404,
            detail="author not found"
        )
    
    session.delete(author)
    session.commit()

    return {f"Author with id: {author_id} has been deleted"}