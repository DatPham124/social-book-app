# main.py
from datetime import timedelta
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import SQLModel, Session

from .config import ACCESS_TOKEN_EXPIRE_MINUTES
from .database import engine, get_session
from .model import User
from . import auth
app = FastAPI()

# Khởi tạo DB khi chạy app
@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

@app.post("/users/register", response_model=User)
def register(user: User, session: Session = Depends(get_session)):
    plain_password = user.hashed_password
    user.hashed_password = auth.get_password_hash(plain_password)

    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@app.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Session = Depends(get_session)
):
    user = auth.authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me/", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(auth.get_current_active_user)],
):
    return current_user
