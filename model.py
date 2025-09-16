from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class Books(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True) #Truoc khi insert chua co id, do id la tu sinh nen de Optional va default:none
    title: str = Field(index=True, nullable=False)
    description: Optional[str] = None
    cover_url: Optional[str] = None
    published_date: Optional[datetime] = None
    language: Optional[str] = None
    authorID: Optional[int] = Field(foreign_key="authors.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Authors(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    bio: Optional[str] = None
    birth_date: Optional[datetime] = None


class Category(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
