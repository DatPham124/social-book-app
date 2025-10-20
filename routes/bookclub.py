from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from datetime import datetime

from ..model import (
    BookClub, BookClubMember, BookClubBook,
    BookClubDiscussion, BookClubComment
)
from common_lib.database import get_session_book_service

router = APIRouter(prefix="/bookclub", tags=["BookClub"])


@router.post("/create", response_model=BookClub)
def create_bookclub(
    name: str,
    creator_id: int,
    description: str = "",
    is_public: bool = True,
    session: Session = Depends(get_session_book_service)
):
    new_club = BookClub(
        name=name,
        description=description,
        creator_id=creator_id,
        is_public=is_public,
        created_at=datetime.utcnow()
    )
    session.add(new_club)
    session.commit()
    session.refresh(new_club)

    member = BookClubMember(
        club_id=new_club.id,
        user_id=creator_id,
        role="host",
        joined_at=datetime.utcnow()
    )
    session.add(member)
    session.commit()

    return new_club


@router.get("/", response_model=List[BookClub])
def list_bookclubs(session: Session = Depends(get_session_book_service)):
    return session.exec(select(BookClub)).all()


@router.get("/{club_id}", response_model=BookClub)
def get_bookclub(club_id: int, session: Session = Depends(get_session_book_service)):
    club = session.get(BookClub, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Câu lạc bộ không tồn tại")
    return club


@router.post("/{club_id}/join")
def join_bookclub(
    club_id: int,
    user_id: int,
    session: Session = Depends(get_session_book_service)
):
    club = session.get(BookClub, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu lạc bộ")

    existing = session.exec(
        select(BookClubMember)
        .where(BookClubMember.club_id == club_id, BookClubMember.user_id == user_id)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bạn đã tham gia câu lạc bộ này")

    new_member = BookClubMember(
        club_id=club_id,
        user_id=user_id,
        joined_at=datetime.utcnow()
    )
    session.add(new_member)
    session.commit()
    return {"message": "Đã tham gia câu lạc bộ thành công"}


@router.post("/{club_id}/add_book")
def add_book_to_club(
    club_id: int,
    book_id: int,
    user_id: int,
    session: Session = Depends(get_session_book_service)
):
    club = session.get(BookClub, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Câu lạc bộ không tồn tại")

    if club.creator_id != user_id:
        raise HTTPException(status_code=403, detail="Chỉ chủ câu lạc bộ mới được thêm sách")

    existing = session.exec(
        select(BookClubBook).where(BookClubBook.club_id == club_id, BookClubBook.book_id == book_id)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Sách đã tồn tại trong câu lạc bộ")

    club_book = BookClubBook(club_id=club_id, book_id=book_id, status="reading")
    session.add(club_book)
    session.commit()
    return {"message": "Đã thêm sách vào câu lạc bộ"}


@router.post("/{club_id}/discussion", response_model=BookClubDiscussion)
def create_discussion(
    club_id: int,
    user_id: int,
    title: str,
    content: str,
    session: Session = Depends(get_session_book_service)
):
    club = session.get(BookClub, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu lạc bộ")

    new_discussion = BookClubDiscussion(
        club_id=club_id,
        user_id=user_id,
        title=title,
        content=content,
        created_at=datetime.utcnow()
    )
    session.add(new_discussion)
    session.commit()
    session.refresh(new_discussion)
    return new_discussion


@router.post("/discussion/{discussion_id}/comment", response_model=BookClubComment)
def comment_discussion(
    discussion_id: int,
    user_id: int,
    content: str,
    session: Session = Depends(get_session_book_service)
):
    discussion = session.get(BookClubDiscussion, discussion_id)
    if not discussion:
        raise HTTPException(status_code=404, detail="Bài thảo luận không tồn tại")

    new_comment = BookClubComment(
        discussion_id=discussion_id,
        user_id=user_id,
        content=content,
        created_at=datetime.utcnow()
    )
    session.add(new_comment)
    session.commit()
    session.refresh(new_comment)
    return new_comment


@router.get("/{club_id}/discussions", response_model=List[BookClubDiscussion])
def list_discussions(club_id: int, session: Session = Depends(get_session_book_service)):
    return session.exec(
        select(BookClubDiscussion).where(BookClubDiscussion.club_id == club_id)
    ).all()


@router.delete("/{club_id}/leave")
def leave_bookclub(
    club_id: int,
    user_id: int,
    session: Session = Depends(get_session_book_service)
):
    member = session.exec(
        select(BookClubMember)
        .where(BookClubMember.club_id == club_id, BookClubMember.user_id == user_id)
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Bạn chưa tham gia câu lạc bộ này")

    session.delete(member)
    session.commit()
    return {"message": "Đã rời câu lạc bộ"}
