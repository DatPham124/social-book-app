# models.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from sqlmodel import SQLModel, Field
import uuid


class User(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True)
    email: str = Field(index=True, unique=True)
    username: str = Field(index=True, unique=True)
    hashed_password: str
    disabled: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Profile(SQLModel, table=True):
    user_id: uuid.UUID = Field(primary_key=True, foreign_key="user.id")  # quan hệ 1-1 với User
    full_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None

class Role(SQLModel, table=True):
    role_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    role_name: str


class User_role(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id")
    role_id:  uuid.UUID = Field(foreign_key="role.role_id")
    assigned_at: datetime = Field(default_factory=datetime.utcnow)

class Password_Update(BaseModel):
    old_password: str
    new_password: str
