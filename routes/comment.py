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
