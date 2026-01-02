from fastapi import APIRouter, Depends, HTTPException, Body
from sqlmodel import Session, select, func
from sqlalchemy import extract, desc
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from ..model import AnnualChallenge, UserBookStatus, Books, BookStatus
from common_lib.database import get_session_book_service

router = APIRouter(
    prefix="/challenges",
    tags=["challenges"],
)

class ChallengeRequest(BaseModel):
    user_id: int
    year: int
    goal_count: int

class ChallengeResponse(BaseModel):
    has_joined: bool
    goal: int = 0
    progress: int = 0
    percentage: int = 0
    read_books: List[Books] = []

@router.post("/annual")
def set_annual_challenge(
    req: ChallengeRequest,
    session: Session = Depends(get_session_book_service)
):
    # 1. Kiểm tra xem đã có thử thách cho năm này chưa
    statement = select(AnnualChallenge).where(
        AnnualChallenge.user_id == req.user_id,
        AnnualChallenge.year == req.year
    )
    challenge = session.exec(statement).first()

    if challenge:
        # Nếu có rồi -> Cập nhật mục tiêu
        challenge.goal_count = req.goal_count
    else:
        # Nếu chưa -> Tạo mới
        challenge = AnnualChallenge(
            user_id=req.user_id,
            year=req.year,
            goal_count=req.goal_count
        )
        session.add(challenge)
    
    session.commit()
    session.refresh(challenge)
    return {"message": "Đã lưu mục tiêu thử thách!", "goal": challenge.goal_count}

@router.get("/annual/{user_id}/{year}", response_model=ChallengeResponse)
def get_annual_challenge_progress(
    user_id: int,
    year: int,
    session: Session = Depends(get_session_book_service)
):
    # 1. Lấy thông tin Thử thách (Mục tiêu)
    chal_stmt = select(AnnualChallenge).where(
        AnnualChallenge.user_id == user_id,
        AnnualChallenge.year == year
    )
    challenge = session.exec(chal_stmt).first()

    if not challenge:
        # Người dùng chưa tham gia
        return ChallengeResponse(has_joined=False)

    # 2. TÍNH TOÁN TIẾN ĐỘ (Logic Nâng cao)
    # Đếm số sách có status='read' và updated_at trong năm đó
    # (Giả định updated_at là thời điểm hoàn thành sách)
    
    # Lấy danh sách sách đã đọc để hiển thị
    books_stmt = (
        select(Books)
        .join(UserBookStatus, Books.id == UserBookStatus.book_id)
        .where(
            UserBookStatus.user_id == user_id,
            UserBookStatus.status == BookStatus.read,
            extract('year', UserBookStatus.updated_at) == year
        )
        .order_by(UserBookStatus.updated_at.desc())
    )
    read_books = session.exec(books_stmt).all()
    
    progress = len(read_books)
    
    # Tính phần trăm
    percentage = 0
    if challenge.goal_count > 0:
        percentage = int((progress / challenge.goal_count) * 100)
        if percentage > 100: percentage = 100

    return ChallengeResponse(
        has_joined=True,
        goal=challenge.goal_count,
        progress=progress,
        percentage=percentage,
        read_books=read_books
    )