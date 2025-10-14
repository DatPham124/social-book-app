from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy import select
from sqlmodel import Session
from common_lib.database import get_session_user_service
from ..model import Profile, User
from .. import auth
from dotenv import load_dotenv
import os
import requests  

load_dotenv()

FILE_SERVER_API = os.getenv("FILE_SERVER_API")
router = APIRouter(
    prefix="/users",
    tags=["profiles"])

@router.post("/profile/add")
def create_profile(
    profile: Profile,
    session: Session = Depends(get_session_user_service),
    current_user: User = Depends(auth.get_current_active_user)
):
    existing_profile = session.get(Profile, current_user.id)
    if existing_profile:
        raise HTTPException(status_code=400, detail="Profile already exists for this user")

    profile.user_id = current_user.id
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile


@router.put("/profile/update")
def update_profile(
    profile_data: Profile,
    session: Session = Depends(get_session_user_service),
    current_user: User = Depends(auth.get_current_active_user)
):
    profile = session.get(Profile, current_user.id)
    if profile is None:
        raise HTTPException(status_code=400, detail="Can't get profile")
    
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
def get_profile(
    session: Session = Depends(get_session_user_service),
    current_user: User = Depends(auth.get_current_active_user)
):
    profile = session.get(Profile, current_user.id)
    if profile is None:
        raise HTTPException(status_code=400, detail="Profile is not found")
    return profile


@router.get("/profile/{user_id}")
def get_profile_by_id(
    user_id: int,
    session: Session = Depends(get_session_user_service)
):
    statement = (
        select(User, Profile)
        .join(Profile, Profile.user_id == User.id, isouter=True)
        .where(User.id == user_id)
    )

    result = session.exec(statement).first()  
    if not result:
        raise HTTPException(status_code=404, detail="Không tìm thấy người dùng")

    user, profile = result  

    return {
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": profile.full_name if profile else None,
        "bio": profile.bio if profile else None,
        "avatar_url": profile.avatar_url if profile else None,
        "created_at": user.created_at,
    }


@router.put("/me/avatar")
def update_avatar(
    session: Session = Depends(get_session_user_service),
    current_user: User = Depends(auth.get_current_active_user),
    file: UploadFile = File(...)
):
    try:
        response = requests.post(
    f"{FILE_SERVER_API}/upload/avatar",
    files={"file": (file.filename, file.file, file.content_type)}
)

        response.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi upload ảnh: {e}")

    result = response.json()
    filename = result.get("filename") 

    profile = session.get(Profile, current_user.id)
    if not profile:
        profile = Profile(user_id=current_user.id)

    profile.avatar_url = filename 
    session.add(profile)
    session.commit()
    session.refresh(profile)

    return {"avatar_url": filename}
