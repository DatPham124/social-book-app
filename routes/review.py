from ..model import Reviews
from sqlmodel import Session, select
from fastapi import APIRouter, Depends, HTTPException
from common_lib.database import get_session_review_service


router = APIRouter(
    prefix="/review",
    tags=["review"]
)

@router.post("/add", response_model=Reviews)
def add_review(review: Reviews, session: Session = Depends(get_session_review_service)):
    session.add(review)
    session.commit()
    session.refresh(review)
    return review

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
