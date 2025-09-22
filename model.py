from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from sqlalchemy import Enum, UniqueConstraint
from sqlmodel import SQLModel, Field


class User(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True, index=True)  
    email: str = Field(index=True, unique=True, nullable =False)
    username: str = Field(index=True, unique=True, nullable =False)
    hashed_password: str
    disabled: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    email: str
    username: str
    password: str  


class Profile(SQLModel, table=True):
    user_id: int = Field(primary_key=True, foreign_key="user.id")  
    full_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None


class Role(SQLModel, table=True):
    role_id: int = Field(default=None, primary_key=True)  
    role_name: str


class User_role(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    role_id: int = Field(foreign_key="role.role_id")
    assigned_at: datetime = Field(default_factory=datetime.utcnow)


class Password_Update(BaseModel):
    old_password: str
    new_password: str

class FriendRequest(str, Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"   

class Friends(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("user_id", "friend_id"),)

    id: int = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    friend_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = Field(default=FriendRequest.pending)  # pending, accepted, rejected
