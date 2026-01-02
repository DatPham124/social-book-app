from sqlmodel import Session, func, select
from fastapi import APIRouter, Depends, HTTPException
from common_lib.database import get_session_review_service
from ..model import Likes


router = APIRouter(
    prefix="/reviews/{review_id}/likes",
    tags=["likes"]
)

@router.post("/add", response_model=Likes)
def add_like(like: Likes, userID: int, reviewID: int, session: Session = Depends(get_session_review_service)):
    like.user_id = userID
    like.review_id = reviewID

    session.add(like)
    session.commit()
    session.add(like)

    return like

@router.get("/")
def get_all_like_by_reviewID(reviewID: int, session: Session = Depends(get_session_review_service)):
    statement = select(func.count(Likes.id)).where(Likes.review_id == reviewID)
    like_count = session.exec(statement).one() # trả về tuple (count,)

    if not like_count:
        raise HTTPException(
            status_code=404,
            detail="No like found"
        )
    return like_count

@router.get("/getall", response_model=list[Likes])
def get_all_like(session: Session = Depends(get_session_review_service)):

    statement = select(Likes)
    like = session.exec(statement).all()

    if not like:
        raise HTTPException(
            status_code=404,
            detail="No like found"
        )
    return like

@router.delete("/delete")
def delete_like(like_id: int, session: Session = Depends(get_session_review_service)):
    like_to_delete = session.get(Likes, like_id)
    if not like_to_delete:
        raise HTTPException(
            status_code=404,
            detail="Like not found"
        )

    session.delete(like_to_delete)
    session.commit()

    return {f"like deleted"}

    
