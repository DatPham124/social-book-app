from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jwt import PyJWTError
from sqlmodel import Session
from common_lib.database import get_session_user_service
from ..model import Role, User, Password_Update, User_role
from .. import auth
from dotenv import load_dotenv
import os

load_dotenv()

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/register", response_model=User)
def register(user: User, session: Session = Depends(get_session_user_service)):
    # hash mật khẩu trước khi lưu
    plain_password = user.hashed_password
    user.hashed_password = auth.get_password_hash(plain_password)

    session.add(user)
    session.commit()
    session.refresh(user)

    # tìm role mặc định "user"
    role_user = session.query(Role).filter(Role.role_name == "user").first()
    if not role_user:
        raise HTTPException(status_code=500, detail="Default role 'user' not found")

    # gán role cho user vừa tạo
    user_role = User_role(user_id=user.id, role_id=role_user.role_id)
    session.add(user_role)
    session.commit()
    session.refresh(user_role)

    return user


@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Session = Depends(get_session_user_service)
):
    user = auth.authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        roles_name = auth.get_role(user.id, session)
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = auth.create_access_token(
            data={"sub": user.username, "roles": roles_name},
            expires_delta=access_token_expires
        )
    except PyJWTError as e: 
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token generation failed: {str(e)}"
        )
    except Exception as e:  
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )

    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/users/me/", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(auth.get_current_active_user)],
):
    return current_user

@router.put("/users/me/password")
def update_password(
    password_data: Password_Update,
    session: Session = Depends(get_session_user_service),
    current_user: User = Depends(auth.get_current_active_user)
):
    if not auth.verify_password(password_data.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Old password is incorrect")

    new_hashed_password = auth.get_password_hash(password_data.new_password)
    current_user.hashed_password = new_hashed_password

    session.add(current_user)
    session.commit()
    session.refresh(current_user)

    return {"msg": "Password updated successfully"}
