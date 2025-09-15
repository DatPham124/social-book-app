import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from common_lib.database import get_session_user_service
from ..model import Profile, User
from .. import auth

router = APIRouter(prefix="/users", tags=["profiles"], dependencies=[Depends(auth.get_current_active_user)])

@router.post ("/profile/add")
def create_profile(profile: Profile, 
                   session:Session = Depends(get_session_user_service),
                   current_user: User = Depends(auth.get_current_active_user)):
    
    existing_profile = session.get(Profile, current_user.id)

    if existing_profile:
        raise HTTPException(
            status_code=400, detail="Profile aleready exists for this user"
        )

    profile.user_id = current_user.id

    session.add(profile)
    session.commit()
    session.refresh(profile)

    return profile

@router.put("/profile/update")
def update_profile(profile_data: Profile, 
                   session:Session = Depends(get_session_user_service),
                   current_user: User = Depends(auth.get_current_active_user)):
    
    profile = session.get(Profile, current_user.id)

    if profile is None:
        raise HTTPException(
            status_code=400, detail="Can't get profile"
        )
    
    if profile_data.full_name is not None:
        profile.full_name = profile_data.full_name
    if profile_data.bio is not None:
        profile.bio = profile_data.bio
    if profile_data.avatar_url is not None:
        profile.avatar_url = profile_data.avatar_url

    session.add(profile)
    session.commit()
    session.refresh(profile)

    return profile

@router.get("/profile", response_model=Profile)
def get_profile(session:Session = Depends(get_session_user_service),
                   current_user: User = Depends(auth.get_current_active_user)):
    
    profile = session.get(Profile, current_user.id)

    if profile is None:
        raise HTTPException(
            status_code=400, detail="Profile is not found"
        )
    
    return profile

@router.get("/profile/{user_id}", response_model=Profile)
def get_profile(user_id, session: Session = Depends(get_session_user_service)):
    user_uuid = uuid.UUID(user_id)
    profile = session.get(Profile, user_uuid)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile