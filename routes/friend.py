from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, or_
from common_lib.database import get_session_user_service
from ..model import Friends, User
from ..auth import get_current_active_user

router = APIRouter(
    prefix="/friends",
    tags=["friends"],
    dependencies=[Depends(get_current_active_user)]
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

@router.get("/{user_id}/{status}", response_model=list[Friends])
def get_all_friends_by_userID_and_status(status: str, session: Session = Depends(get_session_user_service), current_user: User = Depends(get_current_active_user)):
    user_id = current_user.id
    
    statement = select(Friends).where(or_(
        Friends.user_id == user_id,
        Friends.friend_id == user_id
    ),
    Friends.status == status
    )
    friends = session.exec(statement).all()

    if not friends:
        raise HTTPException(
            status_code=404,
            detail=f"No friends found for user with id {user_id}"
        )

    return friends


@router.get("/{user_id}", response_model=list[Friends])
def get_all_friends_by_userID(session: Session = Depends(get_session_user_service), current_user: User = Depends(get_current_active_user)):
    user_id = current_user.id
    
    statement = select(Friends).where(or_(
        Friends.user_id == user_id,
        Friends.friend_id == user_id
    ),
    )
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

@router.put("/update/{friend_id}", response_model=Friends)
def update_friend_status(friend_id: int, status: str, session: Session = Depends(get_session_user_service), current_user: User = Depends(get_current_active_user)):
    friend_to_update = session.get(Friends, friend_id)

    if not friend_to_update:
        raise HTTPException(
            status_code=404,
            detail="Friend relationship not found"
        )

    if status not in ["pending", "accepted", "rejected"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid status value"
        )

    friend_to_update.status = status
    session.add(friend_to_update)
    session.commit()
    session.refresh(friend_to_update)

    return friend_to_update


