from sqlmodel import Session, select
from fastapi import APIRouter, Depends, HTTPException
from common_lib.database import get_session_review_service
from ..model import Comments


router = APIRouter(
    prefix="/reviews/{reviewID}/comments",
    tags=["comments"]
)


@router.post("/add", response_model=Comments)
def add_comment(comment: Comments, reviewID: int, userID: int, session: Session = Depends(get_session_review_service)):
    comment.review_id = reviewID
    comment.user_id = userID

    session.add(comment)
    session.commit()
    session.refresh(comment)
    return comment


@router.get("/", response_model=list[Comments])
def get_all_comments_by_review(reviewID: int, session: Session = Depends(get_session_review_service)):
    statement = select(Comments).where(Comments.review_id == reviewID)
    comments = session.exec(statement).all()

    if not comments:
        raise HTTPException(
            status_code=404,
            detail=f"No comments found for review with id {reviewID}"
        )

    return comments


@router.get("/getall", response_model=list[Comments])
def get_all_comments(session: Session = Depends(get_session_review_service)):
    statement = select(Comments)
    comments = session.exec(statement).all()

    if not comments:
        raise HTTPException(
            status_code=404,
            detail="No comments found"
        )

    return comments


@router.put("/update/{commentID}", response_model=Comments)
def update_comment(comment_data: Comments, commentID: int, session: Session = Depends(get_session_review_service)):
    comment = session.get(Comments, commentID)

    if comment is None:
        raise HTTPException(
            status_code=404,
            detail="comment not found"
        )

    if comment_data.content is not None:
        comment.content = comment_data.content

    session.add(comment)
    session.commit()
    session.refresh(comment)
    return comment


@router.delete("/delete/{commentID}")
def delete_comment(commentID: int, session: Session = Depends(get_session_review_service)):
    comment = session.get(Comments, commentID)

    if comment is None:
        raise HTTPException(
            status_code=404,
            detail="comment not found"
        )

    session.delete(comment)
    session.commit()

    return {"message": f"comment with id {commentID} has been deleted"}
