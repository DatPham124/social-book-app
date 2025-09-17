from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from common_lib.database import get_session_user_service
from ..model import Friends, User
from ..auth import get_current_active_user
import uuid

router = APIRouter(
    prefix="/friends",
    tags=["friends"]
)

@router.post("/add", response_model=Friends)
def add_friend(friend: Friends, friend_id: int, session: Session = Depends(get_session_user_service), current_user: User = Depends(get_current_active_user)):
    
    user_id = current_user.id
    friend.user_id = user_id
    friend.friend_id = friend_id    

    if user_id == friend_id:
        raise HTTPException(
            status_code=400,
            detail="You cannot add yourself as a friend"
        )

    session.add(friend)
    session.commit()
    session.refresh(friend) 

    return friend

@router.get("/{user_id}", response_model=list[Friends])
def get_all_friends_by_userID(session: Session = Depends(get_session_user_service), current_user: User = Depends(get_current_active_user)):
    user_id = current_user.id
    
    statement = select(Friends).where(Friends.user_id == user_id)
    friends = session.exec(statement).all()

    if not friends:
        raise HTTPException(
            status_code=404,
            detail=f"No friends found for user with id {user_id}"
        )

    return friends

@router.delete("/delete/{friend_id}")
def delete_friend(friend_id: int, session: Session = Depends(get_session_user_service), current_user: User = Depends(get_current_active_user)):
    user_id = current_user.id

    statement = select(Friends).where(
        Friends.user_id == user_id,
        Friends.friend_id == friend_id
    )
    friend_to_delete = session.exec(statement).first()

    if not friend_to_delete:
        raise HTTPException(
            status_code=404,
            detail="Friend relationship not found"
        )

    session.delete(friend_to_delete)
    session.commit()

    return {"detail": f"Friend with ID {friend_id} deleted successfully"}