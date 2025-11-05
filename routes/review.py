from typing import List
from pydantic import BaseModel
from sqlalchemy import func
from ..model import Reviews
from sqlmodel import Session, select
from fastapi import APIRouter, Depends, HTTPException, Query
from common_lib.database import get_session_review_service


router = APIRouter(
    prefix="/review",
    tags=["review"]
)

@router.get("/", response_model=list[Reviews])
def get_all_review(session: Session = Depends(get_session_review_service)):
    statement = select(Reviews)
    reviews = session.exec(statement).all()
    return reviews

@router.post("/add", response_model=Reviews)
def add_review(user_id: int, book_id: int, rating: float, content: str , session: Session = Depends(get_session_review_service)):
    
    review_data = Reviews(user_id=user_id, book_id=book_id, rating=rating, content=content)
    session.add(review_data)
    session.commit()
    session.refresh(review_data)
    return review_data

@router.get("/feed/recent", response_model=List[Reviews])
def get_recent_reviews_feed(
    session: Session = Depends(get_session_review_service),
    limit: int = Query(50) 
):
    statement = (
        select(Reviews)
        .order_by(Reviews.created_at.desc())
        .limit(limit)
    )
    reviews = session.exec(statement).all()
    return reviews

@router.get("/book/{bookID}", response_model=list[Reviews])
def get_all_review_by_bookID(bookID: int, session: Session = Depends(get_session_review_service)):
    statement = select(Reviews).where(Reviews.book_id == bookID)
    review_by_bookID = session.exec(statement).all()
    if not review_by_bookID:
        raise HTTPException(
            status_code=404,
            detail=f"Review for book with id {bookID} not found"
        )
    return review_by_bookID

@router.get("/user/{user_id}", response_model=List[Reviews])
def get_all_reviews_by_user(
    user_id: int, 
    session: Session = Depends(get_session_review_service)
):
    statement = (
        select(Reviews)
        .where(Reviews.user_id == user_id)
        .order_by(Reviews.created_at.desc()) 
    )
    reviews = session.exec(statement).all()
    if not reviews:
        raise HTTPException(
            status_code=404,
            detail="Không tìm thấy đánh giá nào cho người dùng này"
        )
    return reviews


class ReviewDistribution(BaseModel):
    one_star: int = 0
    two_star: int = 0
    three_star: int = 0
    four_star: int = 0
    five_star: int = 0

class UserStatsResponse(BaseModel):
    total_reviews: int
    distribution: ReviewDistribution

# --- HÀM ĐÃ ĐƯỢC SỬA LỖI (SỬ DỤNG func.round) ---
@router.get("/stats/user-distribution/{user_id}", response_model=UserStatsResponse)
def get_user_review_distribution(
    user_id: int,
    session: Session = Depends(get_session_review_service)
):
    
    # 1. SỬA CÂU LỆNH SELECT
    #    Chúng ta sẽ 'round' (làm tròn) rating TRƯỚC KHI 'group by'
    statement = (
        select(
            func.round(Reviews.rating).label("rounded_rating"), 
            func.count(Reviews.id).label("count")
        )
        .where(Reviews.user_id == user_id)
        .group_by("rounded_rating") # Group by theo tên đã làm tròn
    )
    
    results = session.exec(statement).all() 

    total_reviews = 0
    distribution_dict = {
        "one_star": 0, "two_star": 0, "three_star": 0, "four_star": 0, "five_star": 0
    }
    
    # 2. SỬA LẠI MAP
    rating_map = {
        0.0: None, # Bỏ qua 0 sao
        1.0: "one_star",
        2.0: "two_star",
        3.0: "three_star",
        4.0: "four_star",
        5.0: "five_star"
    }

    for rounded_rating, count in results:
        if rounded_rating is None: 
            continue
            
        total_reviews += count
        
        # 3. SỬA LOGIC LẤY KEY
        rating_key = rating_map.get(float(rounded_rating))
        
        if rating_key:
            distribution_dict[rating_key] = count
            
    return UserStatsResponse(
        total_reviews=total_reviews,
        distribution=ReviewDistribution(**distribution_dict)
    )

# --- CÁC ROUTE ĐỘNG (DYNAMIC) ---

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
            status_code=44,
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


@router.get("/{bookId}/{userId}")
def get_review_by_userid(bookId: int, userId: int, session: Session = Depends(get_session_review_service)):
    statement = select(Reviews).where(Reviews.user_id == userId, Reviews.book_id == bookId)
    result = session.exec(statement).first()
    return result

@router.get("/{reviewId}", response_model=Reviews)
def get_review_by_reviewId(reviewId: int , session: Session = Depends(get_session_review_service)):
    statement = select(Reviews).where(Reviews.id == reviewId)
    reviews = session.exec(statement).first()
    if not reviews:
        raise HTTPException(status_code=404, detail="Review not found")
    return reviews