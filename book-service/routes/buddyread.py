import json
from fastapi import APIRouter, Depends, Form, HTTPException
from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime

from ..model import (
    BuddyRead, 
    BuddyReadMember, 
    BuddyReadComment, 
    BuddyReadInvitation,
    InviteStatus
)
from common_lib.database import get_session_book_service

router = APIRouter(prefix="/buddyreads", tags=["buddyreads"])

@router.post("/create")
def create_buddy_read(
    book_id: int = Form(...),
    user_id: int = Form(...),
    friend_ids_json: str = Form("[]"),
    session: Session = Depends(get_session_book_service)
):
    try:
        friend_ids = json.loads(friend_ids_json)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="friend_ids_json không hợp lệ")

    new_buddy_read = BuddyRead(
        book_id=book_id,
        created_by_user_id=user_id
    )
    session.add(new_buddy_read)
    session.commit()
    session.refresh(new_buddy_read)

    creator_member = BuddyReadMember(
        buddy_read_id=new_buddy_read.id,
        user_id=user_id
    )
    session.add(creator_member)
    
    for friend_id in friend_ids:
        if friend_id != user_id:
            invitation = BuddyReadInvitation(
                buddy_read_id=new_buddy_read.id,
                sender_id=user_id,
                receiver_id=friend_id,
                status=InviteStatus.PENDING
            )
            session.add(invitation)
            
    session.commit()
    session.refresh(new_buddy_read)
    return new_buddy_read

@router.post("/{buddy_read_id}/invite")
def invite_to_buddy_read(
    buddy_read_id: int,
    sender_id: int = Form(...),
    invitee_id: int = Form(...),
    session: Session = Depends(get_session_book_service)
):
    buddy_read = session.get(BuddyRead, buddy_read_id)
    if not buddy_read:
        raise HTTPException(status_code=404, detail="Không tìm thấy phòng đọc")
        
    if buddy_read.created_by_user_id != sender_id:
        raise HTTPException(status_code=403, detail="Chỉ người tạo phòng mới có quyền mời")
        
    existing_member = session.exec(
        select(BuddyReadMember).where(
            BuddyReadMember.buddy_read_id == buddy_read_id,
            BuddyReadMember.user_id == invitee_id
        )
    ).first()
    if existing_member:
        raise HTTPException(status_code=400, detail="Người dùng này đã ở trong phòng đọc")

    existing_invite = session.exec(
        select(BuddyReadInvitation).where(
            BuddyReadInvitation.buddy_read_id == buddy_read_id,
            BuddyReadInvitation.receiver_id == invitee_id,
            BuddyReadInvitation.status == InviteStatus.PENDING
        )
    ).first()
    if existing_invite:
        raise HTTPException(status_code=400, detail="Đã gửi lời mời đến người này")

    invitation = BuddyReadInvitation(
        buddy_read_id=buddy_read_id,
        sender_id=sender_id,
        receiver_id=invitee_id,
        status=InviteStatus.PENDING
    )
    session.add(invitation)
    session.commit()
    
    return {"message": "Đã gửi lời mời thành công"}

@router.get("/user/{user_id}", response_model=List[BuddyRead])
def get_my_buddy_reads(
    user_id: int, 
    session: Session = Depends(get_session_book_service)
):
    statement = (
        select(BuddyRead)
        .join(BuddyReadMember)
        .where(BuddyReadMember.user_id == user_id)
        .order_by(BuddyRead.created_at.desc())
    )
    buddy_reads = session.exec(statement).all()
    return buddy_reads

@router.get("/{buddy_read_id}", response_model=BuddyRead)
def get_buddy_read_details(
    buddy_read_id: int, 
    session: Session = Depends(get_session_book_service)
):
    buddy_read = session.get(BuddyRead, buddy_read_id)
    if not buddy_read:
        raise HTTPException(status_code=404, detail="Không tìm thấy phòng đọc")
    return buddy_read

@router.get("/{buddy_read_id}/comments", response_model=List[BuddyReadComment])
def get_buddy_read_comments(
    buddy_read_id: int, 
    session: Session = Depends(get_session_book_service)
):
    statement = (
        select(BuddyReadComment)
        .where(BuddyReadComment.buddy_read_id == buddy_read_id)
        .order_by(BuddyReadComment.created_at.asc())
    )
    comments = session.exec(statement).all()
    return comments

@router.post("/{buddy_read_id}/comments")
def post_buddy_read_comment(
    buddy_read_id: int,
    user_id: int = Form(...),
    content: str = Form(...),
    session: Session = Depends(get_session_book_service)
):
    comment = BuddyReadComment(
        buddy_read_id=buddy_read_id,
        user_id=user_id,
        content=content
    )
    session.add(comment)
    session.commit()
    session.refresh(comment)
    return comment

@router.get("/invitations/{user_id}", response_model=List[BuddyReadInvitation])
def get_my_buddy_read_invitations(
    user_id: int,
    session: Session = Depends(get_session_book_service)
):
    invitations = session.exec(
        select(BuddyReadInvitation).where(
            BuddyReadInvitation.receiver_id == user_id,
            BuddyReadInvitation.status == InviteStatus.PENDING
        )
    ).all()
    return invitations

@router.post("/invitations/{invitation_id}/accept")
def accept_buddy_read_invitation(
    invitation_id: int,
    session: Session = Depends(get_session_book_service)
):
    invitation = session.get(BuddyReadInvitation, invitation_id)
    if not invitation or invitation.status != InviteStatus.PENDING:
        raise HTTPException(status_code=404, detail="Không tìm thấy lời mời")

    existing_member = session.exec(
        select(BuddyReadMember).where(
            BuddyReadMember.buddy_read_id == invitation.buddy_read_id,
            BuddyReadMember.user_id == invitation.receiver_id
        )
    ).first()
    
    if not existing_member:
        member = BuddyReadMember(
            buddy_read_id=invitation.buddy_read_id,
            user_id=invitation.receiver_id,
            joined_at=datetime.utcnow()
        )
        session.add(member)
    
    invitation.status = InviteStatus.ACCEPTED
    session.add(invitation)
    session.commit()
    
    return {"message": "Đã chấp nhận lời mời"}

@router.delete("/invitations/{invitation_id}/decline")
def decline_buddy_read_invitation(
    invitation_id: int,
    session: Session = Depends(get_session_book_service)
):
    invitation = session.get(BuddyReadInvitation, invitation_id)
    if not invitation or invitation.status != InviteStatus.PENDING:
        raise HTTPException(status_code=404, detail="Không tìm thấy lời mời")

    invitation.status = InviteStatus.DECLINED
    session.add(invitation)
    session.commit()
    
    return {"message": "Đã từ chối lời mời"}

@router.get("/{buddy_read_id}/members", response_model=List[BuddyReadMember])
def get_buddy_read_members(
    buddy_read_id: int,
    session: Session = Depends(get_session_book_service)
):
    statement = (
        select(BuddyReadMember)
        .where(BuddyReadMember.buddy_read_id == buddy_read_id)
    )
    members = session.exec(statement).all()
    return members

@router.delete("/{buddy_read_id}")
def delete_buddy_read(
    buddy_read_id: int,
    user_id: int = Form(...),
    session: Session = Depends(get_session_book_service)
):
    buddy_read = session.get(BuddyRead, buddy_read_id)
    if not buddy_read:
        raise HTTPException(status_code=404, detail="Không tìm thấy phòng đọc")

    if buddy_read.created_by_user_id != user_id:
        raise HTTPException(status_code=403, detail="Chỉ người tạo mới có quyền xóa phòng")
    
    comments_stmt = select(BuddyReadComment).where(BuddyReadComment.buddy_read_id == buddy_read_id)
    comments_to_delete = session.exec(comments_stmt).all()
    for comment in comments_to_delete:
        session.delete(comment)
        
    members_stmt = select(BuddyReadMember).where(BuddyReadMember.buddy_read_id == buddy_read_id)
    members_to_delete = session.exec(members_stmt).all()
    for member in members_to_delete:
        session.delete(member)
        
    invites_stmt = select(BuddyReadInvitation).where(BuddyReadInvitation.buddy_read_id == buddy_read_id)
    invites_to_delete = session.exec(invites_stmt).all()
    for invite in invites_to_delete:
        session.delete(invite)
        
    session.delete(buddy_read)
    session.commit()
    
    return {"message": "Đã xóa phòng đọc thành công"}

@router.delete("/{buddy_read_id}/leave")
def leave_buddy_read(
    buddy_read_id: int,
    user_id: int = Form(...),
    session: Session = Depends(get_session_book_service)
):
    buddy_read = session.get(BuddyRead, buddy_read_id)
    if not buddy_read:
        raise HTTPException(status_code=404, detail="Không tìm thấy phòng đọc")
        
    if buddy_read.created_by_user_id == user_id:
        raise HTTPException(status_code=400, detail="Người tạo không thể rời, chỉ có thể xóa phòng")

    member_record = session.exec(
        select(BuddyReadMember).where(
            BuddyReadMember.buddy_read_id == buddy_read_id,
            BuddyReadMember.user_id == user_id
        )
    ).first()
    
    if not member_record:
        raise HTTPException(status_code=404, detail="Bạn không phải là thành viên của phòng này")

    session.delete(member_record)
    session.commit()
    
    return {"message": "Rời khỏi phòng đọc thành công"}

@router.delete("/{buddy_read_id}/members/{target_user_id}")
def remove_member_from_buddy_read(
    buddy_read_id: int,
    target_user_id: int,
    requester_id: int = Form(...), # ID người thực hiện (phải là Creator)
    session: Session = Depends(get_session_book_service)
):
    # 1. Kiểm tra Buddy Read tồn tại
    buddy_read = session.get(BuddyRead, buddy_read_id)
    if not buddy_read:
        raise HTTPException(status_code=404, detail="Không tìm thấy phòng đọc")

    # 2. Kiểm tra quyền hạn: Chỉ Creator mới được kick
    if buddy_read.created_by_user_id != requester_id:
        raise HTTPException(status_code=403, detail="Chỉ người tạo phòng mới có quyền xóa thành viên")

    # 3. Không cho phép Creator tự kick chính mình
    if target_user_id == buddy_read.created_by_user_id:
        raise HTTPException(status_code=400, detail="Không thể xóa chủ phòng")

    # 4. Tìm thành viên cần xóa
    member_record = session.exec(
        select(BuddyReadMember).where(
            BuddyReadMember.buddy_read_id == buddy_read_id,
            BuddyReadMember.user_id == target_user_id
        )
    ).first()

    if not member_record:
        raise HTTPException(status_code=404, detail="Thành viên không tồn tại trong phòng đọc")

    # 5. Xóa thành viên
    session.delete(member_record)
    session.commit()

    return {"message": "Đã xóa thành viên khỏi phòng đọc"}

