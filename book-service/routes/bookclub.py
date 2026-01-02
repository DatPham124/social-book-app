from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, File
from sqlmodel import Session, func, select, delete
from datetime import datetime
from typing import List, Optional
import requests, os
from dotenv import load_dotenv

from ..model import (
    BookClub,
    BookClubInvitation,
    BookClubMeeting,
    BookClubMember,
    BookClubBook,
    BookClubDiscussion,
    BookClubComment,
    InviteStatus,
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
    is_public: bool = Form(True), 
    file: UploadFile = File(None),
    session: Session = Depends(get_session_book_service),
):
    club = BookClub(
        name=name,
        description=description,
        creator_id=creator_id,
        is_public=is_public, 
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

@router.get("/search", response_model=List[BookClub])
def search_book_clubs(
    q: str,
    session: Session = Depends(get_session_book_service)
):

    search_term = f"%{q.lower()}%"
    
    clubs = session.exec(
        select(BookClub)
        .where(
            BookClub.name.ilike(search_term), 
            BookClub.is_public == True
        )
        .limit(20) 
    ).all()
    
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
    is_public: bool = Form(True), 
    file: UploadFile = File(None),
    user_id: int = Form(...),
    session: Session = Depends(get_session_book_service),
):
    club = session.get(BookClub, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu lạc bộ")
    
    if club.creator_id != user_id:
        raise HTTPException(status_code=403, detail="Chỉ người tạo club mới có quyền này")

    club.name = name
    club.description = description
    club.rules = rules
    club.is_public = is_public 

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
def delete_bookclub(
    club_id: int, 
    user_id: int, 
    session: Session = Depends(get_session_book_service)
):
    club = session.get(BookClub, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu lạc bộ")
    
    if club.creator_id != user_id:
        raise HTTPException(status_code=403, detail="Chỉ người tạo club mới có quyền này")
    
    if club.avatar_url:
        try:
            filename = os.path.basename(club.avatar_url)
            requests.delete(f"{FILE_SERVER_API}/upload/club/{filename}")
        except Exception:
            pass
            
    
    session.exec(delete(BookClubInvitation).where(BookClubInvitation.club_id == club_id))

    session.exec(delete(BookClubMember).where(BookClubMember.club_id == club_id))

    session.exec(delete(BookClubMeeting).where(BookClubMeeting.club_id == club_id))

    discussions = session.exec(select(BookClubDiscussion).where(BookClubDiscussion.club_id == club_id)).all()
    for disc in discussions:
        session.exec(delete(BookClubComment).where(BookClubComment.discussion_id == disc.id))
        session.delete(disc)
    

    session.delete(club)
    session.commit()
    
    return {"message": "Đã xóa câu lạc bộ"}


@router.post("/{club_id}/join")
def join_bookclub(
    club_id: int, 
    user_id: int = Form(...), 
    session: Session = Depends(get_session_book_service)
):
    club = session.get(BookClub, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu lạc bộ")
        
    existing = session.exec(
        select(BookClubMember).where(
            BookClubMember.club_id == club_id, 
            BookClubMember.user_id == user_id
        )
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Đã tham gia")
        
    if club.is_public:
        member = BookClubMember(
            club_id=club_id, 
            user_id=user_id, 
            joined_at=datetime.utcnow()
        )
        session.add(member)
        session.commit()
        return {"message": "Tham gia thành công", "status": "joined"}
    else:
        existing_request = session.exec(
            select(BookClubInvitation).where(
                BookClubInvitation.club_id == club_id,
                BookClubInvitation.sender_id == user_id, 
                BookClubInvitation.type == "request",
                BookClubInvitation.status == InviteStatus.PENDING
            )
        ).first()
        if existing_request:
            raise HTTPException(status_code=400, detail="Đã gửi yêu cầu tham gia")
        
        invitation = BookClubInvitation(
            club_id=club_id,
            sender_id=user_id, 
            receiver_id=club.creator_id, 
            status=InviteStatus.PENDING,
            type="request" 
        )
        session.add(invitation)
        session.commit()
        return {"message": "Đã gửi yêu cầu tham gia, vui lòng chờ duyệt", "status": "pending"}


@router.delete("/{club_id}/leave")
def leave_bookclub(
    club_id: int, 
    user_id: int = Form(...), 
    session: Session = Depends(get_session_book_service)
):
    member = session.exec(
        select(BookClubMember).where(
            BookClubMember.club_id == club_id, 
            BookClubMember.user_id == user_id
        )
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Chưa tham gia")
    
    club = session.get(BookClub, club_id)
    if club and club.creator_id == user_id:
        raise HTTPException(status_code=400, detail="Người tạo không thể rời, chỉ có thể xóa câu lạc bộ")
        
    session.delete(member)
    session.commit()
    return {"message": "Đã rời câu lạc bộ"}


@router.post("/{club_id}/discussion")
def create_discussion(
    club_id: int,
    user_id: int = Form(...),
    title: str = Form(...),
    content: str = Form(...),
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
    user_id: int = Form(...),
    content: str = Form(...),
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


class DiscussionWithCount(BookClubDiscussion):
    comment_count: int

@router.get("/{club_id}/discussions", response_model=List[DiscussionWithCount])
def list_discussions(club_id: int, session: Session = Depends(get_session_book_service)):
    
    statement = (
        select(
            BookClubDiscussion, 
            func.count(BookClubComment.id).label("comment_count")
        )
        .join(
            BookClubComment, 
            BookClubDiscussion.id == BookClubComment.discussion_id, 
            isouter=True 
        )
        .where(BookClubDiscussion.club_id == club_id)
        .group_by(BookClubDiscussion.id) 
        .order_by(BookClubDiscussion.created_at.desc())
    ) 
    
    results = session.exec(statement).all()

    discussions_with_count = []
    for discussion, count in results:
        discussion_data = discussion.model_dump() 
        discussion_data["comment_count"] = count
        discussions_with_count.append(DiscussionWithCount(**discussion_data))
    
    return discussions_with_count

    
@router.get("/discussion/{discussion_id}")
def get_discussion_details(
    discussion_id: int, 
    session: Session = Depends(get_session_book_service)
):
    discussion = session.get(BookClubDiscussion, discussion_id)
    if not discussion:
        raise HTTPException(status_code=404, detail="Không tìm thấy bài thảo luận")
    
    return discussion

@router.get("/discussion/{discussion_id}/comments", response_model=List[BookClubComment])
def get_discussion_comments(
    discussion_id: int, 
    session: Session = Depends(get_session_book_service)
):
    comments = session.exec(
        select(BookClubComment)
        .where(BookClubComment.discussion_id == discussion_id)
        .order_by(BookClubComment.created_at.asc())
    ).all()
    
    return comments

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
        club.avatar_url = data.get("filename", "") 

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

# Trong file bookclub.py

@router.post("/{club_id}/meetings")
def create_meeting(
    club_id: int,
    title: str = Form(...),
    date: datetime = Form(...),
    book_id: Optional[int] = Form(None),
    user_id: int = Form(...),
    agenda: str = Form(""), # <--- 1. THÊM DÒNG NÀY (Mặc định là rỗng)
    session: Session = Depends(get_session_book_service)
):
    club = session.get(BookClub, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu lạc bộ")
    if club.creator_id != user_id:
        raise HTTPException(status_code=403, detail="Chỉ người tạo club mới có quyền này")

    # Kiểm tra thời gian (Optional - nếu bạn muốn giữ logic chặn ở backend)
    if date < datetime.utcnow():
         raise HTTPException(status_code=400, detail="Thời gian họp không hợp lệ")

    meeting = BookClubMeeting(
        club_id=club_id, 
        title=title, 
        date=date, 
        book_id=book_id,
        agenda=agenda # <--- 2. LƯU AGENDA VÀO DATABASE
    )
    session.add(meeting)
    session.commit()
    session.refresh(meeting) 
    return meeting


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
    response_data = meeting.model_dump()
    response_data["creator_id"] = creator_id
    return response_data


@router.put("/meeting/{meeting_id}/agenda")
def update_meeting_agenda(
    meeting_id: int,
    agenda: str = Form(""),
    user_id: int = Form(...), 
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
    if creator_id != user_id:
        raise HTTPException(status_code=403, detail="Chỉ người tạo club mới có quyền này")

    meeting.agenda = agenda
    session.add(meeting)
    session.commit()
    session.refresh(meeting)
    return meeting


@router.post("/{club_id}/invite")
def invite_to_bookclub(
    club_id: int,
    creator_id: int = Form(...), 
    invitee_id: int = Form(...), 
    session: Session = Depends(get_session_book_service),
):
    club = session.get(BookClub, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu lạc bộ")

    if club.creator_id != creator_id:
        raise HTTPException(status_code=403, detail="Chỉ người tạo club mới có quyền mời")

    existing_member = session.exec(
        select(BookClubMember).where(
            BookClubMember.club_id == club_id, 
            BookClubMember.user_id == invitee_id
        )
    ).first()
    if existing_member:
        raise HTTPException(status_code=400, detail="Người dùng này đã ở trong câu lạc bộ")

    existing_invite = session.exec(
        select(BookClubInvitation).where(
            BookClubInvitation.club_id == club_id,
            BookClubInvitation.receiver_id == invitee_id,
            BookClubInvitation.status == InviteStatus.PENDING
        )
    ).first()
    if existing_invite:
        raise HTTPException(status_code=400, detail="Đã gửi lời mời đến người này")

    invitation = BookClubInvitation(
        club_id=club_id,
        sender_id=creator_id,
        receiver_id=invitee_id,
        status=InviteStatus.PENDING,
        type="invite" 
    )
    session.add(invitation)
    session.commit()
    return {"message": "Đã gửi lời mời thành công"}

@router.get("/invitations/{user_id}", response_model=List[BookClubInvitation])
def get_my_invitations(
    user_id: int,
    session: Session = Depends(get_session_book_service)
):
    invitations = session.exec(
        select(BookClubInvitation).where(
            BookClubInvitation.receiver_id == user_id,
            BookClubInvitation.status == InviteStatus.PENDING,
            BookClubInvitation.type == "invite" 
        )
    ).all()
    return invitations


@router.post("/invitations/{invitation_id}/accept")
def accept_invitation(
    invitation_id: int,
    session: Session = Depends(get_session_book_service)
):
    invitation = session.get(BookClubInvitation, invitation_id)
    if not invitation or invitation.status != InviteStatus.PENDING:
        raise HTTPException(status_code=404, detail="Không tìm thấy lời mời")

    member = BookClubMember(
        club_id=invitation.club_id,
        user_id=invitation.receiver_id,
        joined_at=datetime.utcnow()
    )
    session.add(member)
    
    invitation.status = InviteStatus.ACCEPTED
    session.add(invitation)
    session.commit()
    return {"message": "Đã chấp nhận lời mời và tham gia câu lạc bộ"}


@router.delete("/invitations/{invitation_id}/decline")
def decline_invitation(
    invitation_id: int,
    session: Session = Depends(get_session_book_service)
):
    invitation = session.get(BookClubInvitation, invitation_id)
    if not invitation or invitation.status != InviteStatus.PENDING:
        raise HTTPException(status_code=404, detail="Không tìm thấy lời mời")
    
    invitation.status = InviteStatus.DECLINED
    session.add(invitation)
    session.commit()
    return {"message": "Đã từ chối lời mời"}

@router.get("/{club_id}/join-requests", response_model=List[BookClubInvitation])
def get_join_requests(
    club_id: int,
    user_id: int, 
    session: Session = Depends(get_session_book_service)
):
    club = session.get(BookClub, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu lạc bộ")
    if club.creator_id != user_id:
        raise HTTPException(status_code=403, detail="Chỉ Host mới có quyền xem")

    requests = session.exec(
        select(BookClubInvitation).where(
            BookClubInvitation.club_id == club_id,
            BookClubInvitation.status == InviteStatus.PENDING,
            BookClubInvitation.type == "request" 
        )
    ).all()
    return requests

@router.post("/request/{request_id}/accept")
def accept_join_request(
    request_id: int,
    user_id: int = Form(...), 
    session: Session = Depends(get_session_book_service)
):
    invitation = session.get(BookClubInvitation, request_id)
    if not invitation or invitation.status != InviteStatus.PENDING or invitation.type != "request":
        raise HTTPException(status_code=404, detail="Không tìm thấy yêu cầu")

    club = session.get(BookClub, invitation.club_id)
    if not club or club.creator_id != user_id:
        raise HTTPException(status_code=403, detail="Chỉ Host mới có quyền duyệt")

    member = BookClubMember(
        club_id=invitation.club_id,
        user_id=invitation.sender_id, 
        joined_at=datetime.utcnow()
    )
    session.add(member)
    
    invitation.status = InviteStatus.ACCEPTED
    session.add(invitation)
    session.commit()
    
    return {"message": "Đã chấp thuận yêu cầu"}

@router.delete("/request/{request_id}/decline")
def decline_join_request(
    request_id: int,
    user_id: int = Form(...), 
    session: Session = Depends(get_session_book_service)
):
    invitation = session.get(BookClubInvitation, request_id)
    if not invitation or invitation.status != InviteStatus.PENDING or invitation.type != "request":
        raise HTTPException(status_code=404, detail="Không tìm thấy yêu cầu")

    club = session.get(BookClub, invitation.club_id)
    if not club or club.creator_id != user_id:
        raise HTTPException(status_code=403, detail="Chỉ Host mới có quyền duyệt")

    invitation.status = InviteStatus.DECLINED
    session.add(invitation)
    session.commit()
    
    return {"message": "Đã từ chối yêu cầu"}

@router.get("/{club_id}/member-count")
def get_member_count(
    club_id: int, 
    session: Session = Depends(get_session_book_service)
):
    statement = select(func.count(BookClubMember.id)).where(BookClubMember.club_id == club_id)
    count = session.exec(statement).one()
    return {"club_id": club_id, "member_count": count}


@router.get("/{club_id}/members")
def get_club_members(
    club_id: int, 
    session: Session = Depends(get_session_book_service)
):
    statement = select(BookClubMember).where(BookClubMember.club_id == club_id)
    members = session.exec(statement).all()
    return members

# Thêm vào bookclub.py

@router.delete("/{club_id}/members/{target_user_id}")
def remove_member_from_club(
    club_id: int,
    target_user_id: int,
    requester_id: int = Form(...), # ID của người thực hiện (phải là Host)
    session: Session = Depends(get_session_book_service)
):
    # 1. Kiểm tra CLB tồn tại
    club = session.get(BookClub, club_id)
    if not club:
        raise HTTPException(status_code=404, detail="Không tìm thấy câu lạc bộ")

    # 2. Kiểm tra quyền hạn: Chỉ Host mới được kick
    if club.creator_id != requester_id:
        raise HTTPException(status_code=403, detail="Chỉ Host mới có quyền xóa thành viên")

    # 3. Không cho phép Host tự kick chính mình (Host phải dùng chức năng xóa CLB)
    if target_user_id == club.creator_id:
        raise HTTPException(status_code=400, detail="Không thể xóa Host khỏi câu lạc bộ")

    # 4. Tìm thành viên cần xóa
    member_record = session.exec(
        select(BookClubMember).where(
            BookClubMember.club_id == club_id,
            BookClubMember.user_id == target_user_id
        )
    ).first()

    if not member_record:
        raise HTTPException(status_code=404, detail="Thành viên không tồn tại trong câu lạc bộ")

    # 5. Xóa thành viên
    session.delete(member_record)
    session.commit()

    return {"message": "Đã xóa thành viên khỏi câu lạc bộ"}