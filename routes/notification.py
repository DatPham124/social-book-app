from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List

from common_lib.database import get_session_user_service 
from ..model import Notification, NotificationStatus

router = APIRouter(prefix="/notifications", 
                   tags=["notifications"])



@router.post("/add", response_model=Notification)
def create_notification(notification: Notification, session: Session = Depends(get_session_user_service)):
    session.add(notification)
    session.commit()
    session.refresh(notification)
    return notification


@router.get("/user/{receiver_id}", response_model=List[Notification])
def get_notifications_by_user(receiver_id: int, session: Session = Depends(get_session_user_service)):
    notifications = session.exec(
        select(Notification)
        .where(Notification.receiver_id == receiver_id)
        .order_by(Notification.created_at.desc())
    ).all()
    return notifications


@router.get("/{notification_id}", response_model=Notification)
def get_notification(notification_id: int, session: Session = Depends(get_session_user_service)):
    notification = session.get(Notification, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Thông báo không tồn tại")
    return notification


@router.put("/{notification_id}/read", response_model=Notification)
def mark_as_read(notification_id: int, session: Session = Depends(get_session_user_service)):
    notification = session.get(Notification, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Thông báo không tồn tại")
    
    notification.status = NotificationStatus.READ
    session.add(notification)
    session.commit()
    session.refresh(notification)
    return notification


@router.delete("/{notification_id}")
def delete_notification(notification_id: int, session: Session = Depends(get_session_user_service)):
    notification = session.get(Notification, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Thông báo không tồn tại")
    
    session.delete(notification)
    session.commit()
    return {"message": "Xoá thông báo thành công"}
