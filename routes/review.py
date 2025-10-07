from sqlalchemy import func
from ..model import Reviews
from sqlmodel import Session, select
from fastapi import APIRouter, Depends, HTTPException
from common_lib.database import get_session_review_service


router = APIRouter(
    prefix="/review",
    tags=["review"]
)

@router.post("/add", response_model=Reviews)
def add_review(user_id: int, book_id: int, rating: float, content: str , session: Session = Depends(get_session_review_service)):
    
    review_data = Reviews(user_id=user_id, book_id=book_id, rating=rating, content=content)
    session.add(review_data)
    session.commit()
    session.refresh(review_data)
    return review_data

@router.get("/{bookID}", response_model=list[Reviews])
def get_all_review_by_bookID(bookID: int, session: Session = Depends(get_session_review_service)):
    statement = select(Reviews).where(Reviews.book_id == bookID)
    review_by_bookID = session.exec(statement).all()

    if not review_by_bookID:
        raise HTTPException(
            status_code=404,
            detail=f"Review for book with id {bookID} not found"
        )

    return review_by_bookID

@router.get("/", response_model=list[Reviews])
def get_all_review(session: Session = Depends(get_session_review_service)):
    statement = select(Reviews)
    reviews = session.exec(statement).all()

    return reviews

@router.put("/update/{reviewID}", response_model=Reviews)
def update_review(review_data: Reviews, reviewID: int, session: Session = Depends(get_session_review_service)):
    review = session.get(Reviews, reviewID)

    if review is None:
        raise HTTPException(
            status_code=404,
            detail="review not found"
        )
    
    review_field = ["rating", "content"]

    for field in review_field:
        value = getattr(review_data, field)
        if value is not None:
            setattr(review, field, value)

    session.add(review)
    session.commit()
    session.refresh(review)
    return review

@router.delete("/delete/{reviewID}")
def delete_review(reviewID: int, session: Session = Depends(get_session_review_service)):
    review = session.get(Reviews, reviewID)

    if review is None:
        raise HTTPException(
            status_code=404,
            detail="review not found"
        )

    session.delete(review)
    session.commit()

    return {"message": f"review with id {reviewID} has been deleted"}

@router.get("/{book_id}/average-rating")
def get_average_rating(book_id: int, session: Session = Depends(get_session_review_service)):
    result = session.exec(
        select(func.avg(Reviews.rating)).where(Reviews.book_id == book_id)
    ).one_or_none()
    avg_rating = result if result is not None else 0
    return {"book_id": book_id, "average_rating": round(avg_rating, 2)}    

@router.get("/{book_id}/review-count")
def get_review_count(book_id: int, session: Session = Depends(get_session_review_service)):
    count = session.exec(
        select(func.count()).where(Reviews.book_id == book_id)
    ).one()
    return {"review_count": count}
