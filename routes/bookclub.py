from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, File
from sqlmodel import Session, select
from datetime import datetime
from typing import List, Optional
import requests, os
from dotenv import load_dotenv

from ..model import (
    BookClub,
    BookClubMeeting,
    BookClubMember,
    BookClubBook,
    BookClubDiscussion,
    BookClubComment,
)
from common_lib.database import get_session_book_service

load_dotenv()
router = APIRouter(prefix="/bookclubs", tags=["bookclubs"])

FILE_SERVER_API = os.getenv("FILE_SERVER_API")



@router.post("/create")
def create_bookclub(
    name: str = Form(...),
    creator_id: int = Form(...),
    description: str = Form(""),
    file: UploadFile = File(None),
    session: Session = Depends(get_session_book_service),
):
    club = BookClub(
        name=name,
        description=description,
        creator_id=creator_id,
        created_at=datetime.utcnow(),
    )
    session.add(club)
    session.commit()
    session.refresh(club)

    if file:
        try:
            files = {"file": (file.filename, file.file, file.content_type)}

            res = requests.post(f"{FILE_SERVER_API}/upload/club", files=files)
            res.raise_for_status()

            upload_data = res.json()
            club.avatar_url = upload_data.get("filename", "")

            session.add(club)
            session.commit()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Lỗi upload ảnh: {e}")

    member = BookClubMember(
        club_id=club.id,
        user_id=creator_id,
        role="host",
        joined_at=datetime.utcnow(),
    )
    session.add(member)
    session.commit()

    return {"message": "Tạo câu lạc bộ thành công", "club": club}


@router.get("/")
def list_bookclubs(session: Session = Depends(get_session_book_service)):
    return session.exec(select(BookClub)).all()

@router.get("/created_by/{user_id}")
def get_created_bookclubs(
    user_id: int, session: Session = Depends(get_session_book_service)
):
    clubs = session.exec(
        select(BookClub).where(BookClub.creator_id == user_id)
    ).all()
    return clubs


@router.get("/joined_by/{user_id}")
def get_joined_bookclubs(
    user_id: int, session: Session = Depends(get_session_book_service)
):
    stmt = (
        select(BookClub)
        .join(BookClubMember, BookClubMember.club_id == BookClub.id)
        .where(BookClubMember.user_id == user_id)
    )
    clubs = session.exec(stmt).all()
    return clubs



@router.get("/{club_id}")
def get_bookclub(club_id: int, session: Session = Depends(get_session_book_service)):
    club = session.get(BookClub, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu lạc bộ")
    return club


@router.put("/{club_id}")
def update_bookclub(
    club_id: int,
    name: str = Form(...),
    description: str = Form(""),
    rules: str = Form(""),  
    file: UploadFile = File(None),
    session: Session = Depends(get_session_book_service),
):
    club = session.get(BookClub, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu lạc bộ")

    club.name = name
    club.description = description
    club.rules = rules

    if file:
        if club.avatar_url:
            try:
                requests.delete(f"{FILE_SERVER_API}/upload/club/{club.avatar_url}")
            except Exception as e:
                print(f"Lỗi khi xóa ảnh cũ: {e}")

        try:
            files = {"file": (file.filename, file.file, file.content_type)}
            res = requests.post(f"{FILE_SERVER_API}/upload/club", files=files)
            res.raise_for_status()

            upload_data = res.json()
            club.avatar_url = upload_data.get("filename", "") 
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Lỗi upload ảnh mới: {e}")

    session.add(club)
    session.commit()
    session.refresh(club)

    return {"message": "Cập nhật câu lạc bộ thành công", "club": club}




@router.delete("/{club_id}")
def delete_bookclub(club_id: int, session: Session = Depends(get_session_book_service)):
    club = session.get(BookClub, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu lạc bộ")

    # Nếu có ảnh thì xóa khỏi file server
    if club.avatar_url:
        try:
            filename = os.path.basename(club.avatar_url)
            requests.delete(f"{FILE_SERVER_API}/upload/club/{filename}")
        except Exception:
            pass

    session.delete(club)
    session.commit()
    return {"message": "Đã xóa câu lạc bộ"}


@router.post("/{club_id}/join")
def join_bookclub(club_id: int, user_id: int, session: Session = Depends(get_session_book_service)):
    existing = session.exec(
        select(BookClubMember).where(
            BookClubMember.club_id == club_id, BookClubMember.user_id == user_id
        )
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Đã tham gia")
    member = BookClubMember(club_id=club_id, user_id=user_id, joined_at=datetime.utcnow())
    session.add(member)
    session.commit()
    return {"message": "Tham gia thành công"}


@router.delete("/{club_id}/leave")
def leave_bookclub(club_id: int, user_id: int, session: Session = Depends(get_session_book_service)):
    member = session.exec(
        select(BookClubMember).where(
            BookClubMember.club_id == club_id, BookClubMember.user_id == user_id
        )
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Chưa tham gia")
    session.delete(member)
    session.commit()
    return {"message": "Đã rời câu lạc bộ"}


@router.post("/{club_id}/add_book")
def add_book(club_id: int, book_id: int, session: Session = Depends(get_session_book_service)):
    club_book = BookClubBook(club_id=club_id, book_id=book_id, status="reading")
    session.add(club_book)
    session.commit()
    return {"message": "Đã thêm sách"}


@router.post("/{club_id}/discussion")
def create_discussion(
    club_id: int,
    user_id: int,
    title: str,
    content: str,
    session: Session = Depends(get_session_book_service),
):
    discussion = BookClubDiscussion(
        club_id=club_id,
        user_id=user_id,
        title=title,
        content=content,
        created_at=datetime.utcnow(),
    )
    session.add(discussion)
    session.commit()
    session.refresh(discussion)
    return discussion


@router.post("/discussion/{discussion_id}/comment")
def add_comment(
    discussion_id: int,
    user_id: int,
    content: str,
    session: Session = Depends(get_session_book_service),
):
    comment = BookClubComment(
        discussion_id=discussion_id,
        user_id=user_id,
        content=content,
        created_at=datetime.utcnow(),
    )
    session.add(comment)
    session.commit()
    session.refresh(comment)
    return comment


@router.get("/{club_id}/discussions")
def list_discussions(club_id: int, session: Session = Depends(get_session_book_service)):
    return session.exec(
        select(BookClubDiscussion).where(BookClubDiscussion.club_id == club_id)
    ).all()

@router.post("/{club_id}/upload_image")
def upload_club_image(
    club_id: int,
    file: UploadFile = File(...),
    session: Session = Depends(get_session_book_service),
):
    club = session.get(BookClub, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu lạc bộ")

    try:
        files = {"file": (file.filename, file.file, file.content_type)}
        res = requests.post(f"{FILE_SERVER_API}/upload/club", files=files)
        res.raise_for_status()
        data = res.json()
        club.avatar_url = data.get("url")

        session.add(club)
        session.commit()
        session.refresh(club)

        return {"message": "Tải ảnh thành công", "avatar_url": club.avatar_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi upload ảnh: {e}")

@router.get("/{club_id}/meetings")
def list_meetings(club_id: int, session: Session = Depends(get_session_book_service)):
    return session.exec(
        select(BookClubMeeting).where(BookClubMeeting.club_id == club_id)
    ).all()

@router.post("/{club_id}/meetings")
def create_meeting(
    club_id: int,
    title: str = Form(...),
    date: datetime = Form(...),
    book_id: Optional[int] = Form(None),
    session: Session = Depends(get_session_book_service)
):
    meeting = BookClubMeeting(club_id=club_id, title=title, date=date, book_id=book_id)
    session.add(meeting)
    session.commit()
    session.refresh(meeting) 
    return meeting



from pydantic import BaseModel
class MeetingDetailsResponse(BookClubMeeting):
    creator_id: int | None = None

@router.get("/meeting/{meeting_id}", response_model=MeetingDetailsResponse)
def get_meeting_details(
    meeting_id: int, 
    session: Session = Depends(get_session_book_service)
):
    statement = (
        select(BookClubMeeting, BookClub.creator_id)
        .join(BookClub, BookClubMeeting.club_id == BookClub.id)
        .where(BookClubMeeting.id == meeting_id)
    )
    
    result = session.exec(statement).first()
    
    if not result:
        raise HTTPException(status_code=404, detail="Không tìm thấy cuộc họp")

    meeting, creator_id = result
    
    response_data = meeting.dict()
    response_data["creator_id"] = creator_id
    
    
    return response_data


@router.put("/meeting/{meeting_id}/agenda")
def update_meeting_agenda(
    meeting_id: int,
    agenda: str = Form(""),
    session: Session = Depends(get_session_book_service)
):
    meeting = session.get(BookClubMeeting, meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Không tìm thấy cuộc họp")

    meeting.agenda = agenda
    session.add(meeting)
    session.commit()
    session.refresh(meeting)
    return meeting