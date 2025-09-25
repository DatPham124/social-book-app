from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jwt import PyJWTError
from sqlmodel import Session
from common_lib.database import get_session_user_service
from ..model import Role, User, Password_Update, User_role, UserCreate
from .. import auth
from dotenv import load_dotenv
import os
import re

load_dotenv()

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/register", response_model=User)
def register(user: UserCreate, session: Session = Depends(get_session_user_service)):

    if not user.email or not user.username or not user.password:
        raise HTTPException(status_code=400, detail="Không được để trống email, tên đăng nhập hoặc mật khẩu")
    
    email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    if not re.match(email_regex, user.email):
        raise HTTPException(status_code=400, detail="Email không hợp lệ")

    if len(user.password) < 6:
        raise HTTPException(status_code=400, detail="Mật khẩu phải có ít nhất 6 ký tự")


    user_email = session.query(User).filter(User.email == user.email).first()
    if user_email:
        raise HTTPException(status_code=400, detail="Email đã được đăng ký")
    
    user_name = session.query(User).filter(User.username == user.username).first()
    if user_name:
        raise HTTPException(status_code=400, detail="Tên người dùng đã được đăng ký")
    
    hashed_pw = auth.get_password_hash(user.password)

    new_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_pw
    )



    session.add(new_user)
    session.commit()
    session.refresh(new_user)


    role_user = session.query(Role).filter(Role.role_name == "user").first()

    if not role_user:
        raise HTTPException(status_code=500, detail="Default role 'user' not found")

    user_role = User_role(user_id=new_user.id, role_id=role_user.role_id)
    session.add(user_role)
    session.commit()
    session.refresh(user_role)

    return new_user


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
            data={"username": user.username, "roles": roles_name, "user_id": user.id},
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


@router.get("/me/", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(auth.get_current_active_user)],
):
    return current_user

@router.put("/me/password")
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
